"""Project Aether Computer Vision Temporal & Artifact Analyzer.

Deterministic CV analyzer implementing optical flow motion variance, frame-to-frame SSIM,
and pixel differential metrics to detect micro-flickering, transient 1-4 frame morphing/strobing,
and unphysical motion acceleration spikes that multimodal LLMs miss (Risk RSK-002 / WBS 1.5.2).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union
import numpy as np

try:
    import cv2  # type: ignore
    HAS_OPENCV = True
except ImportError:  # pragma: no cover
    cv2 = None
    HAS_OPENCV = False

from aether.council.schemas import (
    CriticFailureObject,
    CriticType,
    DefectSeverity,
    RepairRecommendation,
)


class CVTemporalAnalyzer:
    """Deterministic CV engine evaluating frame sequences for temporal artifacts."""

    def __init__(
        self,
        flicker_amplitude_threshold: float = 0.04,
        ssim_drop_threshold: float = 0.18,
        ssim_absolute_min: float = 0.72,
        motion_spike_multiplier: float = 3.5,
        motion_variance_threshold: float = 12.0,
        max_morph_span_frames: int = 4,
    ) -> None:
        self.flicker_amplitude_threshold = flicker_amplitude_threshold
        self.ssim_drop_threshold = ssim_drop_threshold
        self.ssim_absolute_min = ssim_absolute_min
        self.motion_spike_multiplier = motion_spike_multiplier
        self.motion_variance_threshold = motion_variance_threshold
        self.max_morph_span_frames = max_morph_span_frames

    # -----------------------------------------------------------------------
    # Frame Normalization & Preprocessing
    # -----------------------------------------------------------------------

    @staticmethod
    def normalize_frames(
        frames: Union[np.ndarray, Sequence[np.ndarray]],
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Convert input frames to (N, H, W) float32 in [0.0, 1.0] and uint8 in [0, 255]."""
        if isinstance(frames, (list, tuple)):
            if len(frames) == 0:
                empty_f = np.zeros((0, 0, 0), dtype=np.float32)
                empty_u = np.zeros((0, 0, 0), dtype=np.uint8)
                return empty_f, empty_u
            arr = np.stack(frames, axis=0)
        else:
            arr = np.asarray(frames)

        if arr.ndim == 2:
            arr = arr[np.newaxis, ...]  # (1, H, W)
        elif arr.ndim == 3 and arr.shape[-1] in (1, 3):
            arr = arr[np.newaxis, ...]

        if arr.ndim != 3 and arr.ndim != 4:
            raise ValueError(f"Expected 3D or 4D frame tensor, got shape {arr.shape}")

        # Grayscale conversion if multi-channel
        if arr.ndim == 4:
            if arr.shape[-1] == 3:
                # RGB / BGR luminance weights
                gray = (
                    0.2989 * arr[..., 0].astype(np.float32)
                    + 0.5870 * arr[..., 1].astype(np.float32)
                    + 0.1140 * arr[..., 2].astype(np.float32)
                )
            elif arr.shape[-1] == 1:
                gray = arr[..., 0].astype(np.float32)
            else:
                gray = arr[..., 0].astype(np.float32)
        else:
            gray = arr.astype(np.float32)

        # Scale float values to [0.0, 1.0] and uint8 to [0, 255]
        if np.issubdtype(arr.dtype, np.integer) or arr.dtype == np.uint8:
            gray_float = np.clip(gray / 255.0, 0.0, 1.0).astype(np.float32)
            gray_uint8 = np.clip(gray, 0, 255).astype(np.uint8)
        else:
            max_val = float(np.max(gray)) if gray.size > 0 else 0.0
            if max_val > 1.01:
                gray_float = np.clip(gray / 255.0, 0.0, 1.0).astype(np.float32)
                gray_uint8 = np.clip(gray, 0, 255).astype(np.uint8)
            else:
                gray_float = np.clip(gray, 0.0, 1.0).astype(np.float32)
                gray_uint8 = np.clip(gray * 255.0, 0, 255).astype(np.uint8)

        return gray_float, gray_uint8

    # -----------------------------------------------------------------------
    # Core Mathematical CV Metrics
    # -----------------------------------------------------------------------

    @staticmethod
    def compute_frame_differentials(gray_float: np.ndarray) -> np.ndarray:
        """Compute mean absolute pixel difference between consecutive frames.

        Returns array of shape (N-1,) in [0.0, 1.0].
        """
        n = gray_float.shape[0]
        if n < 2:
            return np.zeros(0, dtype=np.float32)
        diffs = np.mean(np.abs(gray_float[1:] - gray_float[:-1]), axis=(1, 2))
        return diffs.astype(np.float32)

    @staticmethod
    def compute_ssim_sequence(gray_float: np.ndarray) -> np.ndarray:
        """Compute exact Structural Similarity (SSIM) between consecutive frames.

        Returns array of shape (N-1,) in [-1.0, 1.0].
        """
        n = gray_float.shape[0]
        if n < 2:
            return np.zeros(0, dtype=np.float32)

        c1 = 0.0001
        c2 = 0.0009
        ssims = []

        for i in range(n - 1):
            im1 = gray_float[i]
            im2 = gray_float[i + 1]

            mu1 = float(np.mean(im1))
            mu2 = float(np.mean(im2))
            var1 = float(np.var(im1))
            var2 = float(np.var(im2))
            cov = float(np.mean((im1 - mu1) * (im2 - mu2)))

            num = (2.0 * mu1 * mu2 + c1) * (2.0 * cov + c2)
            den = (mu1**2 + mu2**2 + c1) * (var1 + var2 + c2)
            val = num / den if den != 0.0 else 0.0
            ssims.append(float(val))

        return np.array(ssims, dtype=np.float32)

    @staticmethod
    def compute_optical_flow(
        gray_uint8: np.ndarray,
        gray_float: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Compute frame-to-frame optical flow displacement magnitude and variance.

        Uses OpenCV Farneback if available, with pure NumPy gradient fallback.
        Returns:
            magnitudes: Array of shape (N-1,) representing mean flow magnitude
            variances: Array of shape (N-1,) representing flow vector variance
        """
        n = gray_uint8.shape[0]
        if n < 2:
            return np.zeros(0, dtype=np.float32), np.zeros(0, dtype=np.float32)

        magnitudes = []
        variances = []

        for i in range(n - 1):
            flow_mag = None
            if HAS_OPENCV:
                f1 = gray_uint8[i]
                f2 = gray_uint8[i + 1]
                if min(f1.shape[0], f1.shape[1]) >= 16:
                    try:
                        flow = cv2.calcOpticalFlowFarneback(
                            f1,
                            f2,
                            None,
                            pyr_scale=0.5,
                            levels=3,
                            winsize=15,
                            iterations=3,
                            poly_n=5,
                            poly_sigma=1.2,
                            flags=0,
                        )
                        u = flow[..., 0]
                        v = flow[..., 1]
                        flow_mag = np.sqrt(u**2 + v**2)
                    except Exception:  # pragma: no cover
                        flow_mag = None

            # Fallback to pure NumPy spatial-temporal gradient optical flow
            if flow_mag is None:
                gf = gray_float if gray_float is not None else (gray_uint8.astype(np.float32) / 255.0)
                im1 = gf[i]
                im2 = gf[i + 1]
                # Spatial gradients
                gx = np.gradient(im1, axis=1)
                gy = np.gradient(im1, axis=0)
                gt = im2 - im1
                denom = gx**2 + gy**2 + 0.001
                u = -gt * gx / denom
                v = -gt * gy / denom
                flow_mag = np.clip(np.sqrt(u**2 + v**2), 0.0, 100.0)

            mag_mean = float(np.mean(flow_mag))
            mag_var = float(np.var(flow_mag))
            magnitudes.append(mag_mean)
            variances.append(mag_var)

        return np.array(magnitudes, dtype=np.float32), np.array(variances, dtype=np.float32)

    # -----------------------------------------------------------------------
    # Spatial Bounding Box Localization Utilities
    # -----------------------------------------------------------------------

    @staticmethod
    def _localize_spatial_bounding_box(
        diff_map: np.ndarray,
        threshold_quantile: float = 0.85,
        padding: float = 0.05,
    ) -> Tuple[float, float, float, float]:
        """Calculates normalized [x1, y1, x2, y2] bounding box for localized delta region."""
        h, w = diff_map.shape[:2]
        if h == 0 or w == 0:
            return (0.0, 0.0, 1.0, 1.0)

        max_diff = float(np.max(diff_map))
        if max_diff <= 1e-4:
            return (0.0, 0.0, 1.0, 1.0)

        # Contrast cutoff: isolate high delta anomaly pixels from subtle background motion
        cutoff = max(0.08, max_diff * 0.35)
        active_y, active_x = np.where(diff_map > cutoff)
        if len(active_x) == 0 or len(active_y) == 0:
            cutoff = float(np.quantile(diff_map, threshold_quantile))
            active_y, active_x = np.where(diff_map > cutoff)
            if len(active_x) == 0 or len(active_y) == 0:
                return (0.0, 0.0, 1.0, 1.0)

        # If active pixels cover majority of frame, defect is global
        area_coverage = len(active_x) / (h * w)
        if area_coverage > 0.55:
            return (0.0, 0.0, 1.0, 1.0)

        x1 = max(0.0, float(np.min(active_x)) / w - padding)
        y1 = max(0.0, float(np.min(active_y)) / h - padding)
        x2 = min(1.0, float(np.max(active_x)) / w + padding)
        y2 = min(1.0, float(np.max(active_y)) / h + padding)

        return (round(x1, 3), round(y1, 3), round(x2, 3), round(y2, 3))

    # -----------------------------------------------------------------------
    # Defect Detectors
    # -----------------------------------------------------------------------

    def detect_micro_flicker(
        self,
        gray_float: np.ndarray,
    ) -> List[CriticFailureObject]:
        """Detect high-frequency temporal luminance oscillation and rapid 1-3 frame strobing."""
        n = gray_float.shape[0]
        if n < 3:
            return []

        failures: List[CriticFailureObject] = []
        covered_frames: Set[int] = set()

        # 1. Global mean luminance across time
        luminance = np.mean(gray_float, axis=(1, 2))
        deltas = np.diff(luminance)  # length N-1

        i = 0
        while i < len(deltas) - 1:
            d1 = float(deltas[i])
            d2 = float(deltas[i + 1])

            # Condition 1: Direct sign reversal with noticeable amplitude
            is_sign_flip = (d1 * d2 < 0) and (
                (abs(d1) >= self.flicker_amplitude_threshold and abs(d2) >= self.flicker_amplitude_threshold * 0.4)
                or (abs(d2) >= self.flicker_amplitude_threshold and abs(d1) >= self.flicker_amplitude_threshold * 0.4)
            )

            # Condition 2: Single-frame flash (frame i+1 sharply deviates then reverts)
            is_flash = False
            if i + 2 < len(luminance):
                base_diff = abs(float(luminance[i + 2] - luminance[i]))
                pulse_diff = abs(float(luminance[i + 1] - luminance[i]))
                if pulse_diff >= self.flicker_amplitude_threshold * 1.5 and base_diff < pulse_diff * 0.4:
                    is_flash = True

            if is_sign_flip or is_flash:
                start_frame = max(0, i)
                # Expand span if oscillation continues
                end_frame = min(n - 1, i + 2)
                curr_ptr = i + 1
                while curr_ptr < len(deltas) - 1:
                    dn1 = float(deltas[curr_ptr])
                    dn2 = float(deltas[curr_ptr + 1])
                    if dn1 * dn2 < 0 and (abs(dn1) >= self.flicker_amplitude_threshold or abs(dn2) >= self.flicker_amplitude_threshold):
                        end_frame = min(n - 1, curr_ptr + 2)
                        curr_ptr += 1
                    else:
                        break

                max_amp = float(np.max(np.abs(deltas[start_frame:end_frame])))
                severity = DefectSeverity.SEVERE if max_amp > 0.10 else DefectSeverity.MODERATE

                # Spatial localization: difference map between flickered frames
                flickered_frame = gray_float[min(start_frame + 1, n - 1)]
                clean_ref = gray_float[start_frame]
                diff_map = np.abs(flickered_frame - clean_ref)
                bbox = self._localize_spatial_bounding_box(diff_map)

                repair = (
                    RepairRecommendation.FULL_REGEN
                    if (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) > 0.6
                    else RepairRecommendation.REGIONAL_INPAINTING
                )

                failures.append(
                    CriticFailureObject(
                        failure_type="micro_flicker",
                        severity=severity,
                        frame_bounds=(start_frame, end_frame),
                        bounding_box=bbox,
                        observed_state=(
                            f"High-frequency temporal luminance oscillation detected (delta amplitude {max_amp:.3f}) "
                            f"across frames {start_frame}-{end_frame}"
                        ),
                        expected_state="Continuous monotonic or smooth luminance gradient across frames",
                        confidence=0.92,
                        recommended_repair=repair,
                        critic_type=CriticType.TEMPORAL,
                        description="Micro-flickering luminance strobe breaching temporal tolerance threshold",
                        metadata={"amplitude": max_amp, "span_frames": end_frame - start_frame + 1, "mode": "global"},
                    )
                )
                for f_idx in range(start_frame, end_frame + 1):
                    covered_frames.add(f_idx)
                i = end_frame
            else:
                i += 1

        # 2. Localized spatial grid block check (detects localized strobing that global mean misses)
        H, W = gray_float.shape[1], gray_float.shape[2]
        grid_size = 4
        if H >= 16 and W >= 16:
            bh, bw = H // grid_size, W // grid_size
            cropped = gray_float[:, :grid_size * bh, :grid_size * bw]
            blocks = cropped.reshape(n, grid_size, bh, grid_size, bw).transpose(0, 1, 3, 2, 4)
            block_lum = blocks.mean(axis=(3, 4))  # (N, grid_size, grid_size)
            block_deltas = np.diff(block_lum, axis=0)  # (N-1, grid_size, grid_size)

            t = 0
            while t < len(block_deltas) - 1:
                if t in covered_frames or (t + 1) in covered_frames:
                    t += 1
                    continue

                bd1 = block_deltas[t]
                bd2 = block_deltas[t + 1]
                sign_flips = (bd1 * bd2 < -1e-5) & (
                    (np.abs(bd1) >= self.flicker_amplitude_threshold) & (np.abs(bd2) >= self.flicker_amplitude_threshold * 0.4)
                )

                flash_mask = np.zeros((grid_size, grid_size), dtype=bool)
                if t + 2 < len(block_lum):
                    b_base = np.abs(block_lum[t + 2] - block_lum[t])
                    b_pulse = np.abs(block_lum[t + 1] - block_lum[t])
                    flash_mask = (b_pulse >= self.flicker_amplitude_threshold * 1.5) & (b_base < b_pulse * 0.4)

                active_mask = sign_flips | flash_mask
                if np.any(active_mask):
                    start_frame = t
                    end_frame = min(n - 1, t + 2)
                    max_amp = float(np.max(np.abs(block_deltas[t : end_frame, active_mask])))
                    severity = DefectSeverity.SEVERE if max_amp > 0.12 else DefectSeverity.MODERATE

                    by_idx, bx_idx = np.where(active_mask)
                    x1 = max(0.0, float(np.min(bx_idx)) / grid_size - 0.05)
                    y1 = max(0.0, float(np.min(by_idx)) / grid_size - 0.05)
                    x2 = min(1.0, float(np.max(bx_idx) + 1) / grid_size + 0.05)
                    y2 = min(1.0, float(np.max(by_idx) + 1) / grid_size + 0.05)
                    bbox = (round(x1, 3), round(y1, 3), round(x2, 3), round(y2, 3))

                    failures.append(
                        CriticFailureObject(
                            failure_type="micro_flicker",
                            severity=severity,
                            frame_bounds=(start_frame, end_frame),
                            bounding_box=bbox,
                            observed_state=(
                                f"Localized temporal luminance oscillation detected (amplitude {max_amp:.3f}) "
                                f"across frames {start_frame}-{end_frame}"
                            ),
                            expected_state="Continuous monotonic or smooth luminance gradient across frames",
                            confidence=0.91,
                            recommended_repair=RepairRecommendation.REGIONAL_INPAINTING,
                            critic_type=CriticType.TEMPORAL,
                            description="Localized micro-flickering luminance strobe breaching temporal tolerance threshold",
                            metadata={"amplitude": max_amp, "span_frames": end_frame - start_frame + 1, "mode": "localized"},
                        )
                    )
                    for f_idx in range(start_frame, end_frame + 1):
                        covered_frames.add(f_idx)
                    t = end_frame
                else:
                    t += 1

        return failures

    def detect_morphing(
        self,
        gray_float: np.ndarray,
        ssim_sequence: np.ndarray,
    ) -> List[CriticFailureObject]:
        """Detect transient 1-4 frame structural collapse / morphing artifacts (RSK-002)."""
        n = gray_float.shape[0]
        if n < 3 or len(ssim_sequence) == 0:
            return []

        baseline_ssim = float(np.median(ssim_sequence))
        failures: List[CriticFailureObject] = []
        i = 0

        while i < len(ssim_sequence):
            curr_ssim = float(ssim_sequence[i])
            ssim_drop = baseline_ssim - curr_ssim

            # Breach occurs when SSIM drops sharply below absolute threshold or baseline
            if curr_ssim < self.ssim_absolute_min or ssim_drop >= self.ssim_drop_threshold:
                start_frame = i
                # Track how many consecutive frames remain depressed
                end_frame = i + 1
                k = i + 1
                while k < len(ssim_sequence) and (k - i) <= self.max_morph_span_frames:
                    k_ssim = float(ssim_sequence[k])
                    if k_ssim < self.ssim_absolute_min or (baseline_ssim - k_ssim) >= self.ssim_drop_threshold:
                        end_frame = k + 1
                        k += 1
                    else:
                        break

                span = end_frame - start_frame
                # Check if it was a transient morph (1 to 4 frames) or permanent scene cut
                is_transient = span <= self.max_morph_span_frames

                min_ssim = float(np.min(ssim_sequence[start_frame:min(end_frame, len(ssim_sequence))]))
                severity = DefectSeverity.FATAL if (min_ssim < 0.55 or ssim_drop > 0.35) else DefectSeverity.SEVERE

                # Spatial localization: compare morphed frame against start_frame
                morphed_span = gray_float[min(start_frame + 1, n - 1) : min(end_frame + 1, n)]
                clean_ref = gray_float[start_frame]
                if len(morphed_span) > 0:
                    diff_map = np.max(np.abs(morphed_span - clean_ref), axis=0)
                else:
                    diff_map = np.abs(gray_float[min(start_frame + 1, n - 1)] - clean_ref)
                bbox = self._localize_spatial_bounding_box(diff_map)

                bbox_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                repair = (
                    RepairRecommendation.REGIONAL_INPAINTING
                    if bbox_area < 0.55
                    else RepairRecommendation.FULL_REGEN
                )

                failures.append(
                    CriticFailureObject(
                        failure_type="morphing_artifact",
                        severity=severity,
                        frame_bounds=(start_frame, end_frame),
                        bounding_box=bbox,
                        observed_state=(
                            f"Transient {span}-frame structural collapse/morphing artifact detected "
                            f"(SSIM dipped to {min_ssim:.3f}, delta {baseline_ssim - min_ssim:.3f})"
                        ),
                        expected_state="Continuous topological and structural geometry preservation across frames",
                        confidence=0.96,
                        recommended_repair=repair,
                        critic_type=CriticType.TEMPORAL,
                        description=(
                            f"Transient {span}-frame structural morphing/geometry deformation across frames "
                            f"{start_frame}-{end_frame}"
                        ),
                        metadata={"min_ssim": min_ssim, "baseline_ssim": baseline_ssim, "span": span, "is_transient": is_transient},
                    )
                )
                i = end_frame
            else:
                i += 1

        return failures

    def detect_motion_spikes(
        self,
        gray_uint8: np.ndarray,
        flow_magnitudes: np.ndarray,
        flow_variances: np.ndarray,
        gray_float: Optional[np.ndarray] = None,
    ) -> List[CriticFailureObject]:
        """Detect unphysical erratic optical flow motion displacement jumps and variance spikes."""
        n = gray_uint8.shape[0]
        if n < 3 or len(flow_magnitudes) == 0:
            return []

        baseline_mag = float(np.median(flow_magnitudes))
        baseline_var = float(np.median(flow_variances))

        failures: List[CriticFailureObject] = []
        i = 0

        while i < len(flow_magnitudes):
            curr_mag = float(flow_magnitudes[i])
            curr_var = float(flow_variances[i])

            # Relative motion jump condition
            mag_ratio = curr_mag / (baseline_mag + 0.05)
            var_ratio = curr_var / (baseline_var + 0.1)

            is_mag_spike = mag_ratio >= self.motion_spike_multiplier and curr_mag > 1.5
            is_var_spike = curr_var >= self.motion_variance_threshold or (var_ratio >= 4.0 and curr_var > 5.0)

            if is_mag_spike or is_var_spike:
                start_frame = i
                end_frame = min(n - 1, i + 1)
                max_mag = curr_mag
                max_var = curr_var
                max_ratio = mag_ratio

                # Spatial localization: compute difference map between spike frames
                if gray_float is not None:
                    diff_map = np.abs(gray_float[end_frame] - gray_float[start_frame])
                else:
                    diff_map = np.abs(gray_uint8[end_frame].astype(np.float32) - gray_uint8[start_frame].astype(np.float32)) / 255.0
                bbox = self._localize_spatial_bounding_box(diff_map)

                severity = DefectSeverity.SEVERE if (max_ratio > 5.0 or max_var > 20.0) else DefectSeverity.MODERATE
                bbox_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                repair = (
                    RepairRecommendation.REGIONAL_INPAINTING
                    if bbox_area < 0.45
                    else RepairRecommendation.SPATIAL_PREVIS_RERUN
                )

                failures.append(
                    CriticFailureObject(
                        failure_type="erratic_motion_spike",
                        severity=severity,
                        frame_bounds=(start_frame, end_frame),
                        bounding_box=bbox,
                        observed_state=(
                            f"Unphysical motion displacement spike (optical flow magnitude {max_mag:.2f}, "
                            f"variance {max_var:.2f}, ratio {max_ratio:.1f}x baseline)"
                        ),
                        expected_state="Continuous kinematic velocity trajectory adhering to Newtonian inertia",
                        confidence=0.89,
                        recommended_repair=repair,
                        critic_type=CriticType.TEMPORAL,
                        description="Erratic motion vector spike breaching physical velocity continuity",
                        metadata={"flow_magnitude": max_mag, "flow_variance": max_var, "mag_ratio": max_ratio},
                    )
                )
                i += 1
            else:
                i += 1

        return failures

    # -----------------------------------------------------------------------
    # Main Analysis Entrypoint
    # -----------------------------------------------------------------------

    def analyze_frames(
        self,
        frames: Union[np.ndarray, Sequence[np.ndarray]],
        telemetry: Optional[Dict[str, Any]] = None,
    ) -> List[CriticFailureObject]:
        """Execute full deterministic CV inspection pipeline across candidate frames."""
        gray_float, gray_uint8 = self.normalize_frames(frames)
        n = gray_float.shape[0]
        if n < 2:
            return []

        # 1. Compute frame metrics
        ssim_seq = self.compute_ssim_sequence(gray_float)
        flow_mag, flow_var = self.compute_optical_flow(gray_uint8, gray_float)

        # 2. Execute defect detectors
        failures: List[CriticFailureObject] = []
        failures.extend(self.detect_micro_flicker(gray_float))
        failures.extend(self.detect_morphing(gray_float, ssim_seq))
        failures.extend(self.detect_motion_spikes(gray_uint8, flow_mag, flow_var, gray_float))

        # Sort failures chronologically and by severity
        failures.sort(key=lambda f: (f.start_frame, f.severity.rank))
        return failures

    # -----------------------------------------------------------------------
    # Synthetic Sequence Generator Utilities for Testing & Calibration
    # -----------------------------------------------------------------------

    @staticmethod
    def generate_clean_sequence(
        num_frames: int = 16,
        height: int = 64,
        width: int = 64,
    ) -> np.ndarray:
        """Generates synthetic clean video sequence with smooth constant motion."""
        frames = []
        for t in range(num_frames):
            y, x = np.mgrid[0:height, 0:width]
            # Smoothly panning horizontal gradient
            im = 0.5 + 0.3 * np.sin((x + t * 0.8) / 8.0) * np.cos(y / 10.0)
            frames.append(np.clip(im, 0.0, 1.0).astype(np.float32))
        return np.stack(frames, axis=0)

    @staticmethod
    def inject_flicker(
        frames: np.ndarray,
        start_frame: int = 4,
        end_frame: int = 7,
        amplitude: float = 0.25,
    ) -> np.ndarray:
        """Injects high-frequency alternating luminance oscillation across frame window."""
        corrupted = frames.copy()
        for idx in range(start_frame, min(end_frame + 1, len(corrupted))):
            sign = 1.0 if (idx % 2 == 0) else -1.0
            corrupted[idx] = np.clip(corrupted[idx] + sign * amplitude, 0.0, 1.0)
        return corrupted

    @staticmethod
    def inject_morph(
        frames: np.ndarray,
        start_frame: int = 6,
        end_frame: int = 8,
        bbox: Tuple[float, float, float, float] = (0.2, 0.2, 0.6, 0.6),
    ) -> np.ndarray:
        """Injects localized 1-3 frame structural distortion/morphing artifact."""
        corrupted = frames.copy()
        h, w = corrupted.shape[1:3]
        x1, y1 = int(bbox[0] * w), int(bbox[1] * h)
        x2, y2 = int(bbox[2] * w), int(bbox[3] * h)

        for idx in range(start_frame, min(end_frame + 1, len(corrupted))):
            noise = np.random.RandomState(42 + idx).uniform(0.0, 1.0, (y2 - y1, x2 - x1))
            corrupted[idx, y1:y2, x1:x2] = noise.astype(np.float32)
        return corrupted

    @staticmethod
    def inject_motion_spike(
        frames: np.ndarray,
        spike_frame: int = 5,
        displacement: Tuple[int, int] = (16, 16),
    ) -> np.ndarray:
        """Injects sudden violent spatial translation jump at spike_frame."""
        corrupted = frames.copy()
        if 0 <= spike_frame < len(corrupted):
            dy, dx = displacement
            corrupted[spike_frame] = np.roll(corrupted[spike_frame], shift=(dy, dx), axis=(0, 1))
        return corrupted
