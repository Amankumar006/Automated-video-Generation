"""
The Model Verse — Tier 1 Deterministic Computer Vision (CV) Gatekeeper Engine
Executes local, zero-API-cost deterministic image heuristics in <50ms per frame:
1. Farnebäck Dense Optical Flow Motion Jitter & SSIM Strobing Detector
2. WCAG AAA Linear Relative Luminance & Pixel Contrast Ratio Analyzer
3. Axis-Aligned Bounding Box (AABB) & Text Overlap Collision Solver
4. Universal 9:16 Mobile Safe-Zone Binary Mask Exclusion Checker
"""

import time
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import cv2
from pydantic import BaseModel, Field

from pipeline.vsg.schema import BoundingBoxPx


# =============================================================================
# DATA STRUCTURES & VERDICTS
# =============================================================================

class GatekeeperVerdict(str):
    PASS = "PASS"
    FAIL = "FAIL"


class GatekeeperViolation(BaseModel):
    rule: str
    verdict: str = GatekeeperVerdict.FAIL
    message: str
    target_id: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


class Tier1AuditReport(BaseModel):
    verdict: str = GatekeeperVerdict.PASS
    frame_index: int = 0
    latency_ms: float = 0.0
    violations: List[GatekeeperViolation] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.verdict == GatekeeperVerdict.PASS and len(self.violations) == 0


# =============================================================================
# 1. OPTICAL FLOW MOTION JITTER & STROBING DETECTOR
# =============================================================================

class FarnebackMotionAnalyzer:
    """
    Computes dense optical flow fields across consecutive frames to detect
    high-frequency motion jitter, acceleration spikes, and strobing SSIM drops.
    """

    def __init__(
        self,
        max_acceleration_variance: float = 15.0,
        max_ssim_drop: float = 0.22,
        flow_spike_ratio_limit: float = 3.8
    ):
        self.max_acceleration_variance = max_acceleration_variance
        self.max_ssim_drop = max_ssim_drop
        self.flow_spike_ratio_limit = flow_spike_ratio_limit

    def compute_ssim(self, img1_gray: np.ndarray, img2_gray: np.ndarray) -> float:
        """Computes structural similarity (SSIM) between two grayscale frames."""
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2

        # Fast downsample to 135x240 for sub-5ms SSIM evaluation
        h, w = img1_gray.shape[:2]
        if w > 135:
            img1_gray = cv2.resize(img1_gray, (135, int(h * 135 / w)), interpolation=cv2.INTER_AREA)
            img2_gray = cv2.resize(img2_gray, (135, int(h * 135 / w)), interpolation=cv2.INTER_AREA)

        img1 = img1_gray.astype(np.float64)
        img2 = img2_gray.astype(np.float64)

        mu1 = cv2.GaussianBlur(img1, (7, 7), 1.5)
        mu2 = cv2.GaussianBlur(img2, (7, 7), 1.5)

        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2

        sigma1_sq = cv2.GaussianBlur(img1 ** 2, (7, 7), 1.5) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(img2 ** 2, (7, 7), 1.5) - mu2_sq
        sigma12 = cv2.GaussianBlur(img1 * img2, (7, 7), 1.5) - mu1_mu2

        ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / (
            (mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2)
        )
        return float(np.mean(ssim_map))

    def analyze(
        self,
        prev_gray: np.ndarray,
        curr_gray: np.ndarray,
        prev_flow: Optional[np.ndarray] = None,
        is_scene_cut: bool = False
    ) -> Tuple[bool, List[GatekeeperViolation], Dict[str, Any], np.ndarray]:
        violations: List[GatekeeperViolation] = []

        # 1. Downscale for ultra-fast <20ms flow kernel (216x384 resolution)
        scale = 0.2
        h, w = curr_gray.shape[:2]
        small_prev = cv2.resize(prev_gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA) if (w > 216 or h > 384) else prev_gray
        small_curr = cv2.resize(curr_gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA) if (w > 216 or h > 384) else curr_gray

        # 2. Gunnar Farnebäck dense flow
        flow = cv2.calcOpticalFlowFarneback(
            small_prev, small_curr, None,
            pyr_scale=0.5, levels=2, winsize=9,
            iterations=2, poly_n=5, poly_sigma=1.1, flags=0
        )

        mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        flow_mean = float(np.mean(mag))
        flow_median = float(np.median(mag))
        flow_variance = float(np.var(mag))

        # 3. Acceleration & Jerk detection (if prev_flow supplied)
        accel_variance = 0.0
        if prev_flow is not None and prev_flow.shape == flow.shape:
            accel = flow - prev_flow
            accel_mag = np.sqrt(accel[..., 0] ** 2 + accel[..., 1] ** 2)
            accel_variance = float(np.var(accel_mag))

            if accel_variance > self.max_acceleration_variance:
                violations.append(GatekeeperViolation(
                    rule="FLOW_MOTION_JITTER",
                    message=f"Erratic motion acceleration variance ({accel_variance:.2f} px/f^2) exceeds threshold ({self.max_acceleration_variance})",
                    metrics={"accel_variance": accel_variance, "limit": self.max_acceleration_variance}
                ))

        # 4. Global Strobing SSIM Check
        ssim_val = 1.0
        if not is_scene_cut:
            ssim_val = self.compute_ssim(small_prev, small_curr)
            ssim_drop = 1.0 - ssim_val
            if ssim_drop > self.max_ssim_drop:
                violations.append(GatekeeperViolation(
                    rule="GLOBAL_STROBING_DETECTED",
                    message=f"Severe SSIM drop ({ssim_drop:.3f}) across consecutive frames without scene wipe (limit: {self.max_ssim_drop})",
                    metrics={"ssim": ssim_val, "ssim_drop": ssim_drop}
                ))

        metrics = {
            "flow_mean": flow_mean,
            "flow_median": flow_median,
            "flow_variance": flow_variance,
            "accel_variance": accel_variance,
            "ssim": ssim_val
        }

        return len(violations) == 0, violations, metrics, flow


# =============================================================================
# 2. WCAG AAA RELATIVE LUMINANCE & CONTRAST ANALYZER
# =============================================================================

class WCAGContrastAnalyzer:
    """
    Evaluates photometric linear luminance according to ITU-R BT.709
    and enforces WCAG AAA contrast ratios (>= 7.0:1 for body/math, >= 4.5:1 for headlines).
    """

    @staticmethod
    def srgb_to_linear(srgb: np.ndarray) -> np.ndarray:
        """Vectorized conversion of non-linear 8-bit sRGB to linear photometric luminance."""
        c = srgb.astype(np.float64) / 255.0
        linear = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
        return linear

    @classmethod
    def compute_relative_luminance(cls, bgr_color: Union[np.ndarray, Tuple[int, int, int]]) -> float:
        """Computes relative luminance L from a BGR pixel or patch."""
        if isinstance(bgr_color, (list, tuple)):
            bgr = np.array(bgr_color, dtype=np.uint8)
        else:
            bgr = bgr_color

        if bgr.ndim == 1:
            b, g, r = bgr[0], bgr[1], bgr[2]
            rgb = np.array([r, g, b], dtype=np.uint8)
            lin = cls.srgb_to_linear(rgb)
            return float(0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2])
        else:
            # Patch mean
            mean_bgr = np.mean(bgr, axis=(0, 1))
            rgb = np.array([mean_bgr[2], mean_bgr[1], mean_bgr[0]], dtype=np.uint8)
            lin = cls.srgb_to_linear(rgb)
            return float(0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2])

    @classmethod
    def calculate_contrast_ratio(cls, lum1: float, lum2: float) -> float:
        """Calculates contrast ratio CR = (L1 + 0.05) / (L2 + 0.05)."""
        l_high = max(lum1, lum2)
        l_low = min(lum1, lum2)
        return float((l_high + 0.05) / (l_low + 0.05))

    def evaluate_bounding_box(
        self,
        frame_bgr: np.ndarray,
        box: BoundingBoxPx,
        node_id: str,
        is_headline: bool = False
    ) -> Tuple[bool, Optional[GatekeeperViolation], float]:
        """
        Extracts foreground glyph clusters vs background envelope and validates contrast.
        """
        h_frame, w_frame = frame_bgr.shape[:2]
        x1 = max(0, int(box.x_min_px))
        y1 = max(0, int(box.y_min_px))
        x2 = min(w_frame, int(box.x_max_px))
        y2 = min(h_frame, int(box.y_max_px))

        if x2 <= x1 or y2 <= y1:
            return True, None, 21.0

        patch = frame_bgr[y1:y2, x1:x2]
        gray_patch = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)

        # Separate foreground (bright glyphs) from background (dark surface) using Otsu
        _, mask = cv2.threshold(gray_patch, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        fg_pixels = patch[mask == 255]
        bg_pixels = patch[mask == 0]

        if len(fg_pixels) < 10 or len(bg_pixels) < 10:
            return True, None, 21.0

        fg_lum = self.compute_relative_luminance(np.mean(fg_pixels, axis=0))
        bg_lum = self.compute_relative_luminance(np.mean(bg_pixels, axis=0))

        cr = self.calculate_contrast_ratio(fg_lum, bg_lum)
        threshold = 4.5 if is_headline else 7.0

        if cr < threshold:
            violation = GatekeeperViolation(
                rule="WCAG_CONTRAST_VIOLATION",
                message=f"Node '{node_id}' contrast ratio {cr:.2f}:1 is below WCAG {'AA (4.5:1)' if is_headline else 'AAA (7.0:1)'}",
                target_id=node_id,
                metrics={"contrast_ratio": cr, "threshold": threshold, "fg_lum": fg_lum, "bg_lum": bg_lum}
            )
            return False, violation, cr

        return True, None, cr


# =============================================================================
# 3. SPATIAL COLLISION & AABB SOLVER
# =============================================================================

class AABBCollisionSolver:
    """
    Evaluates spatial collisions between visual bounding boxes with zero tolerance (IoU = 0.0).
    """

    @staticmethod
    def audit_collisions(
        boxes: List[Tuple[str, BoundingBoxPx]]
    ) -> Tuple[bool, List[GatekeeperViolation]]:
        violations: List[GatekeeperViolation] = []

        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                id_a, box_a = boxes[i]
                id_b, box_b = boxes[j]

                if box_a.intersects(box_b):
                    iou = box_a.intersection_iou(box_b)
                    violations.append(GatekeeperViolation(
                        rule="AABB_SPATIAL_COLLISION",
                        message=f"Collision detected between nodes '{id_a}' and '{id_b}' (IoU: {iou:.3f})",
                        target_id=f"{id_a} vs {id_b}",
                        metrics={"node_a": id_a, "node_b": id_b, "iou": iou}
                    ))

        return len(violations) == 0, violations


# =============================================================================
# 4. MOBILE 9:16 SAFE-ZONE BINARY EXCLUSION MASK AUDITOR
# =============================================================================

class MobileSafeZoneAuditor:
    """
    Applies an 8-bit binary exclusion mask on 1080x1920 canvas:
    - Top exclusion: Y in [0, 220]
    - Bottom exclusion: Y in [1420, 1920]
    - Right rail exclusion: X in [920, 1080] between Y in [220, 1420]
    - Left margin exclusion: X in [0, 120]
    """

    def __init__(self, width: int = 1080, height: int = 1920):
        self.width = width
        self.height = height
        self.mask = np.zeros((height, width), dtype=np.uint8)

        # 1. Top exclusion corridor (Status bar, title, audio pill)
        self.mask[0:220, :] = 1

        # 2. Bottom exclusion corridor (Channel avatar, title, subscribe pill, nav)
        self.mask[1420:1920, :] = 1

        # 3. Right engagement rail (Like, Comment, Share icon column)
        self.mask[220:1420, 920:1080] = 1

        # 4. Left margin padding
        self.mask[220:1420, 0:120] = 1

    def audit_box(self, box: BoundingBoxPx, target_id: str) -> Tuple[bool, Optional[GatekeeperViolation], float]:
        x1 = max(0, int(round(box.x_min_px)))
        y1 = max(0, int(round(box.y_min_px)))
        x2 = min(self.width, int(round(box.x_max_px)))
        y2 = min(self.height, int(round(box.y_max_px)))

        if x2 <= x1 or y2 <= y1:
            return True, None, 0.0

        sub_mask = self.mask[y1:y2, x1:x2]
        violation_pixels = int(np.sum(sub_mask))

        if violation_pixels > 0:
            violation = GatekeeperViolation(
                rule="SAFE_ZONE_BREACH",
                message=f"Node '{target_id}' overlaps mobile exclusion mask ({violation_pixels} intersecting pixels)",
                target_id=target_id,
                metrics={
                    "violation_pixels": violation_pixels,
                    "box": [box.x_min_px, box.y_min_px, box.x_max_px, box.y_max_px]
                }
            )
            return False, violation, float(violation_pixels)

        return True, None, 0.0


# =============================================================================
# MASTER TIER 1 GATEKEEPER ENGINE
# =============================================================================

class Tier1CVGatekeeper:
    """Master Tier 1 Deterministic CV Gatekeeper coordinating all 4 heuristics."""

    def __init__(self):
        self.motion_analyzer = FarnebackMotionAnalyzer()
        self.contrast_analyzer = WCAGContrastAnalyzer()
        self.collision_solver = AABBCollisionSolver()
        self.safe_zone_auditor = MobileSafeZoneAuditor()

    def evaluate_frame(
        self,
        frame_bgr: np.ndarray,
        frame_index: int = 0,
        prev_frame_bgr: Optional[np.ndarray] = None,
        prev_flow: Optional[np.ndarray] = None,
        node_boxes: Optional[List[Tuple[str, BoundingBoxPx, bool]]] = None,
        is_scene_cut: bool = False
    ) -> Tuple[Tier1AuditReport, Optional[np.ndarray]]:
        """
        Executes all 4 deterministic CV heuristics on a rendered frame buffer.
        Guaranteed execution time < 50ms on modern CPU.
        """
        t0 = time.perf_counter()
        violations: List[GatekeeperViolation] = []
        metrics: Dict[str, Any] = {}
        curr_flow: Optional[np.ndarray] = None

        # 1. Optical Flow & Strobing (if previous frame provided)
        if prev_frame_bgr is not None:
            # Ultra-fast downsample prior to grayscale conversion
            h, w = frame_bgr.shape[:2]
            small_prev_bgr = cv2.resize(prev_frame_bgr, (216, 384), interpolation=cv2.INTER_AREA) if (w > 216 or h > 384) else prev_frame_bgr
            small_curr_bgr = cv2.resize(frame_bgr, (216, 384), interpolation=cv2.INTER_AREA) if (w > 216 or h > 384) else frame_bgr
            prev_gray = cv2.cvtColor(small_prev_bgr, cv2.COLOR_BGR2GRAY)
            curr_gray = cv2.cvtColor(small_curr_bgr, cv2.COLOR_BGR2GRAY)

            passed_motion, motion_violations, motion_metrics, curr_flow = self.motion_analyzer.analyze(
                prev_gray, curr_gray, prev_flow=prev_flow, is_scene_cut=is_scene_cut
            )
            violations.extend(motion_violations)
            metrics.update(motion_metrics)

        # 2. Node Bounding Box Heuristics (Collisions, Safe-Zone, Contrast)
        if node_boxes:
            boxes_only = [(nid, box) for nid, box, _ in node_boxes]

            # 2a. AABB Collision Solver
            passed_collisions, collision_violations = self.collision_solver.audit_collisions(boxes_only)
            violations.extend(collision_violations)

            # 2b. Safe Zone & Contrast Checks per Node
            contrast_scores = {}
            for nid, box, is_headline in node_boxes:
                # Safe Zone Audit
                passed_safe, safe_violation, _ = self.safe_zone_auditor.audit_box(box, nid)
                if not passed_safe and safe_violation:
                    violations.append(safe_violation)

                # WCAG Contrast Ratio Audit
                passed_cr, cr_violation, cr_val = self.contrast_analyzer.evaluate_bounding_box(
                    frame_bgr, box, nid, is_headline=is_headline
                )
                contrast_scores[nid] = cr_val
                if not passed_cr and cr_violation:
                    violations.append(cr_violation)

            metrics["contrast_ratios"] = contrast_scores

        latency_ms = (time.perf_counter() - t0) * 1000.0

        verdict = GatekeeperVerdict.PASS if len(violations) == 0 else GatekeeperVerdict.FAIL

        report = Tier1AuditReport(
            verdict=verdict,
            frame_index=frame_index,
            latency_ms=round(latency_ms, 2),
            violations=violations,
            metrics=metrics
        )

        return report, curr_flow
