"""Project Aether Temporal Mask Generation Engine.

Implements spatio-temporal inpainting mask synthesis, spatial Gaussian/cosine feathering,
temporal padding ramps, protected region shielding, and boundary seam metric
analysis to address RSK-004 (Temporal Inpainting Boundary Seams).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from aether.council.schemas import CriticFailureObject
from aether.repair.schemas import (
    ProtectedRegion,
    ProtectedRegionType,
    RepairBoundaryMask,
)


class TemporalMaskEngine:
    """Spatio-temporal mask generation and edge feathering engine (Pillar 6 / WBS 1.7.2).

    Eliminates edge boundary seams and temporal strobing (RSK-004) by applying:
    1. Contextual spatial bounding box expansion around raw defect coordinates.
    2. Continuous distance-based spatial feathering (Gaussian or smooth cosine falloff).
    3. Temporal ramp-in and ramp-out frame padding weights.
    4. Explicit protection masks for clean background, faces, and camera motion trajectories.
    5. Quantitative boundary seam metric calculation for council verification.
    """

    def __init__(
        self,
        default_feather_radius_px: float = 16.0,
        default_temporal_pad_frames: int = 4,
        default_box_expansion_ratio: float = 0.12,
        default_resolution: Tuple[int, int] = (1080, 1920),  # (H, W)
    ) -> None:
        self.default_feather_radius_px = default_feather_radius_px
        self.default_temporal_pad_frames = default_temporal_pad_frames
        self.default_box_expansion_ratio = default_box_expansion_ratio
        self.default_resolution = default_resolution

    def expand_bounding_box(
        self,
        bbox: Tuple[float, float, float, float],
        expansion_ratio: float = 0.12,
    ) -> Tuple[float, float, float, float]:
        """Expands normalized bounding box [x1, y1, x2, y2] by a margin ratio.

        Prevents tight defect cropping and provides necessary spatial context for
        inpaint models to stitch seamless latent representations.
        """
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1

        dx = max(width * expansion_ratio, 0.02 if width <= 0.0 else width * expansion_ratio)
        dy = max(height * expansion_ratio, 0.02 if height <= 0.0 else height * expansion_ratio)

        exp_x1 = max(0.0, x1 - dx)
        exp_y1 = max(0.0, y1 - dy)
        exp_x2 = min(1.0, x2 + dx)
        exp_y2 = min(1.0, y2 + dy)

        return (exp_x1, exp_y1, exp_x2, exp_y2)

    def create_boundary_mask(
        self,
        failure: CriticFailureObject,
        feather_radius_px: Optional[float] = None,
        temporal_pad_frames: Optional[int] = None,
        box_expansion_ratio: Optional[float] = None,
        protected_regions: Optional[List[Union[ProtectedRegion, Dict[str, Any]]]] = None,
    ) -> RepairBoundaryMask:
        """Constructs a `RepairBoundaryMask` specification from a `CriticFailureObject`."""
        expansion = (
            box_expansion_ratio
            if box_expansion_ratio is not None
            else self.default_box_expansion_ratio
        )
        feather = (
            feather_radius_px
            if feather_radius_px is not None
            else self.default_feather_radius_px
        )
        pad = (
            temporal_pad_frames
            if temporal_pad_frames is not None
            else self.default_temporal_pad_frames
        )

        expanded_box = self.expand_bounding_box(failure.bounding_box, expansion_ratio=expansion)

        clean_protected: List[ProtectedRegion] = []
        if protected_regions:
            for p in protected_regions:
                if isinstance(p, ProtectedRegion):
                    clean_protected.append(p)
                elif isinstance(p, dict):
                    clean_protected.append(ProtectedRegion.model_validate(p))

        return RepairBoundaryMask(
            bounding_box=expanded_box,
            frame_bounds=failure.frame_bounds,
            feather_radius_px=feather,
            temporal_pad_frames=pad,
            box_expansion_ratio=expansion,
            protected_regions=clean_protected,
        )

    def generate_spatial_mask(
        self,
        bbox: Tuple[float, float, float, float],
        resolution: Optional[Tuple[int, int]] = None,
        feather_radius_px: Optional[float] = None,
        falloff: str = "cosine",
    ) -> np.ndarray:
        """Synthesizes a 2D spatial inpainting mask with distance-based edge feathering.

        Args:
            bbox: Normalized [x1, y1, x2, y2]
            resolution: (Height, Width) in pixels
            feather_radius_px: Radius of feather falloff in pixels
            falloff: 'cosine', 'gaussian', or 'linear'

        Returns:
            np.ndarray: 2D array of shape (H, W) with float32 values in [0.0, 1.0].
                        1.0 = inner defect core to inpaint,
                        0.0 = untouched background,
                        (0, 1) = feathered transition band.
        """
        H, W = resolution or self.default_resolution
        R = float(
            feather_radius_px
            if feather_radius_px is not None
            else self.default_feather_radius_px
        )

        x1_px = int(round(bbox[0] * W))
        y1_px = int(round(bbox[1] * H))
        x2_px = int(round(bbox[2] * W))
        y2_px = int(round(bbox[3] * H))

        # Clamp pixel coordinates
        x1_px = max(0, min(W - 1, x1_px))
        x2_px = max(0, min(W, x2_px))
        y1_px = max(0, min(H - 1, y1_px))
        y2_px = max(0, min(H, y2_px))

        if x1_px >= x2_px or y1_px >= y2_px:
            return np.zeros((H, W), dtype=np.float32)

        if R <= 0.0:
            mask = np.zeros((H, W), dtype=np.float32)
            mask[y1_px:y2_px, x1_px:x2_px] = 1.0
            return mask

        # Vectorized Euclidean distance from bounding box core
        x_coords = np.arange(W, dtype=np.float32)
        y_coords = np.arange(H, dtype=np.float32)

        dx = np.maximum(0.0, np.maximum(x1_px - x_coords, x_coords - x2_px))[None, :]
        dy = np.maximum(0.0, np.maximum(y1_px - y_coords, y_coords - y2_px))[:, None]

        dist = np.sqrt(dx ** 2 + dy ** 2)

        # Inner core (dist == 0) has weight 1.0; outside R has weight 0.0
        u = np.clip(dist / R, 0.0, 1.0)

        if falloff == "gaussian":
            # Normalized Gaussian falloff reaching ~0 at dist=R
            sigma = 0.4
            mask = np.exp(-0.5 * (u / sigma) ** 2)
            mask[dist >= R] = 0.0
        elif falloff == "linear":
            mask = 1.0 - u
        else:
            # Smooth cosine falloff (default)
            mask = 0.5 * (1.0 + np.cos(np.pi * u))
            mask[dist >= R] = 0.0

        # Exact 1.0 inside inner core
        mask[dist == 0.0] = 1.0
        return mask.astype(np.float32)

    def compute_temporal_weights(
        self,
        total_frames: int,
        start_frame: int,
        end_frame: int,
        pad_frames: int = 4,
    ) -> np.ndarray:
        """Calculates temporal ramp-in and ramp-out frame weights to eliminate strobing.

        Args:
            total_frames: Total number of frames in shot
            start_frame: Defect beginning frame index
            end_frame: Defect ending frame index
            pad_frames: Number of transition buffer frames before/after defect

        Returns:
            np.ndarray: 1D array of shape (total_frames,) with weights in [0.0, 1.0].
        """
        weights = np.zeros(total_frames, dtype=np.float32)
        start = max(0, min(total_frames - 1, start_frame))
        end = max(0, min(total_frames - 1, end_frame))
        if start > end:
            start, end = end, start

        # Core defect frame span has full inpainting weight 1.0
        weights[start : end + 1] = 1.0

        if pad_frames > 0:
            # Smooth cosine ramp-in
            for i in range(1, pad_frames + 1):
                f_in = start - i
                if 0 <= f_in < total_frames:
                    u = 1.0 - (i / (pad_frames + 1.0))
                    weights[f_in] = float(0.5 * (1.0 - math.cos(math.pi * u)))

            # Smooth cosine ramp-out
            for i in range(1, pad_frames + 1):
                f_out = end + i
                if 0 <= f_out < total_frames:
                    u = 1.0 - (i / (pad_frames + 1.0))
                    weights[f_out] = float(0.5 * (1.0 - math.cos(math.pi * u)))

        return weights

    def apply_protection_to_mask(
        self,
        mask: np.ndarray,
        protected_regions: List[ProtectedRegion],
        resolution: Optional[Tuple[int, int]] = None,
        frame_idx: Optional[int] = None,
    ) -> np.ndarray:
        """Shields protected areas (clean background, actors, camera trajectories).

        Corresponds to Pillar 6 specification: inpaint masks must strictly preserve
        stable background pixels and unaffected actor features.
        """
        if not protected_regions:
            return mask

        H, W = resolution or self.default_resolution
        protected_mask = np.zeros((H, W), dtype=np.float32)

        for pr in protected_regions:
            # Check frame bound validity if applicable
            if frame_idx is not None and pr.frame_bounds is not None:
                start, end = pr.frame_bounds
                if not (start <= frame_idx <= end):
                    continue

            if pr.bounding_box is not None:
                bx1 = int(round(pr.bounding_box[0] * W))
                by1 = int(round(pr.bounding_box[1] * H))
                bx2 = int(round(pr.bounding_box[2] * W))
                by2 = int(round(pr.bounding_box[3] * H))

                bx1 = max(0, min(W - 1, bx1))
                bx2 = max(0, min(W, bx2))
                by1 = max(0, min(H - 1, by1))
                by2 = max(0, min(H, by2))

                if bx1 < bx2 and by1 < by2:
                    protected_mask[by1:by2, bx1:bx2] = np.maximum(
                        protected_mask[by1:by2, bx1:bx2],
                        float(pr.protection_strength),
                    )

        # Attenuate inpainting mask where protected regions exist
        shielded = mask * (1.0 - protected_mask)
        return np.clip(shielded, 0.0, 1.0).astype(np.float32)

    def generate_spatio_temporal_mask(
        self,
        boundary_mask: RepairBoundaryMask,
        total_frames: int,
        resolution: Optional[Tuple[int, int]] = None,
        falloff: str = "cosine",
    ) -> np.ndarray:
        """Synthesizes complete 3D spatio-temporal inpainting mask tensor.

        Returns:
            np.ndarray: 3D float32 tensor of shape (total_frames, H, W).
        """
        H, W = resolution or self.default_resolution
        spatial_mask = self.generate_spatial_mask(
            bbox=boundary_mask.bounding_box,
            resolution=(H, W),
            feather_radius_px=boundary_mask.feather_radius_px,
            falloff=falloff,
        )

        temporal_weights = self.compute_temporal_weights(
            total_frames=total_frames,
            start_frame=boundary_mask.start_frame,
            end_frame=boundary_mask.end_frame,
            pad_frames=boundary_mask.temporal_pad_frames,
        )

        tensor_3d = np.zeros((total_frames, H, W), dtype=np.float32)
        for t in range(total_frames):
            tw = temporal_weights[t]
            if tw > 0.0:
                frame_mask = spatial_mask * tw
                if boundary_mask.protected_regions:
                    frame_mask = self.apply_protection_to_mask(
                        frame_mask,
                        boundary_mask.protected_regions,
                        resolution=(H, W),
                        frame_idx=t,
                    )
                tensor_3d[t] = frame_mask

        return tensor_3d

    def compute_boundary_seam_metric(
        self,
        mask: np.ndarray,
        frame: Optional[np.ndarray] = None,
    ) -> float:
        """Calculates edge feather variance and boundary seam metric (RSK-004).

        A raw binary unfeathered mask produces a sharp step transition with high
        discontinuity variance (> 0.20).
        A properly feathered mask produces a continuous gradient falloff with very
        low edge feather variance (<= 0.05).

        Returns:
            float: Seam continuity metric (lower is smoother; <= 0.05 is acceptable).
        """
        # Collapse 3D tensor to 2D representative slice if necessary
        frame_2d: Optional[np.ndarray] = None
        if mask.ndim == 3:
            # Pick the peak frame (highest active area)
            sums = mask.sum(axis=(1, 2))
            peak_idx = int(np.argmax(sums))
            if sums[peak_idx] == 0:
                return 0.0
            m_2d = mask[peak_idx]

            if frame is not None:
                if frame.ndim == 4 and frame.shape[0] == mask.shape[0]:
                    frame_2d = frame[peak_idx].mean(axis=-1).astype(np.float32)
                elif frame.ndim == 3 and frame.shape[0] == mask.shape[0]:
                    frame_2d = frame[peak_idx].astype(np.float32)
                elif frame.ndim == 3 and frame.shape[:2] == m_2d.shape:
                    frame_2d = frame.mean(axis=-1).astype(np.float32)
                elif frame.ndim == 2 and frame.shape == m_2d.shape:
                    frame_2d = frame.astype(np.float32)
        elif mask.ndim == 2:
            m_2d = mask
            if frame is not None:
                if frame.ndim == 3 and frame.shape[:2] == m_2d.shape:
                    frame_2d = frame.mean(axis=-1).astype(np.float32)
                elif frame.ndim == 2 and frame.shape == m_2d.shape:
                    frame_2d = frame.astype(np.float32)
        else:
            return 0.0

        if np.all(m_2d == 0.0):
            return 0.0

        # Identify boundary transition band where 0.01 < mask < 0.99
        feather_band = (m_2d > 0.01) & (m_2d < 0.99)
        band_count = np.count_nonzero(feather_band)

        if band_count == 0:
            # Binary step edge without feathering! High seam variance penalty
            # Compute step gradient magnitude along binary perimeter
            grad_y, grad_x = np.gradient(m_2d)
            edge_grad = np.sqrt(grad_y ** 2 + grad_x ** 2)
            edge_pixels = edge_grad > 0.1
            if np.count_nonzero(edge_pixels) > 0:
                step_discontinuity = float(np.var(edge_grad[edge_pixels]) + 0.25)
                return min(1.0, step_discontinuity)
            return 0.0

        # Compute gradient variance across transition feather band
        grad_y, grad_x = np.gradient(m_2d)
        grad_mag = np.sqrt(grad_y ** 2 + grad_x ** 2)

        band_gradients = grad_mag[feather_band]
        gradient_variance = float(np.var(band_gradients))

        # If a frame is supplied, evaluate blend boundary color variance
        if frame_2d is not None and frame_2d.shape == m_2d.shape:
            f_norm = (frame_2d / 255.0) if float(np.max(frame_2d)) > 1.01 else frame_2d
            f_grad_y, f_grad_x = np.gradient(f_norm)
            f_grad_mag = np.sqrt(f_grad_y ** 2 + f_grad_x ** 2)
            color_var = float(np.var(f_grad_mag[feather_band]))
            return float(min(1.0, gradient_variance * 0.7 + color_var * 0.3))

        return float(min(1.0, gradient_variance))
