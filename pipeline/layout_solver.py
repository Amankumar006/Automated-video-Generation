"""
The Model Verse — Deterministic Geometric Layout & Collision Solver (Phase 6)
Implements:
1. Bijective coordinate transforms between Normalized [0, 1000] and Manim 9:16 Canvas.
2. Analytical AABB collision detection & Minimum Translation Vector (MTV) repulsion.
3. Strict 9:16 mobile safe-zone corridor enforcement (X in [-3.2, 3.2], Y in [-4.0, 5.5]).
4. Position-Based Dynamics (PBD) multi-body relaxation with inverse mass weighting.
5. Visual Repair Diagnostic Ledger for automated self-healing verification.
"""

import time
from enum import Enum
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
from pydantic import BaseModel, Field

# =============================================================================
# CONSTANTS & SAFE-ZONE GEOMETRY (9:16 Vertical Platform Standard)
# =============================================================================

MANIM_FRAME_WIDTH = 9.0
MANIM_FRAME_HEIGHT = 16.0

# Sacred Safe Zone corridor in Manim Units:
# Top header badge lives at Y in [5.8, 6.4]
# Bottom subtitles and YouTube Shorts player deck live at Y in [-8.0, -4.0]
SAFE_X_MIN = -3.20
SAFE_X_MAX = 3.20
SAFE_Y_MIN = -4.00
SAFE_Y_MAX = 5.50

DEFAULT_PADDING_X = 0.25
DEFAULT_PADDING_Y = 0.20


# =============================================================================
# SCHEMAS FOR DIAGNOSTIC LEDGER & VISUAL PATCHES
# =============================================================================

class ViolationType(str, Enum):
    AABB_COLLISION = "aabb_collision"
    SAFE_ZONE_BREACH = "safe_zone_breach"
    SCALE_UNDERFLOW = "scale_underflow"
    OCCLUSION = "occlusion"


class RepairActionType(str, Enum):
    TRANSLATE = "translate"
    RESCALE = "rescale"
    TRANSLATE_AND_RESCALE = "translate_and_rescale"
    NO_ACTION = "no_action"


class BoundingBox2D(BaseModel):
    # Normalized [ymin, xmin, ymax, xmax] in 0..1000 integer range
    gemini_box: List[int] = Field(default_factory=lambda: [0, 0, 0, 0])
    # Manim coordinates [xmin, ymin, xmax, ymax]
    manim_box: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    center: List[float] = Field(default_factory=lambda: [0.0, 0.0])
    dimensions: List[float] = Field(default_factory=lambda: [0.0, 0.0])


class SpatialViolation(BaseModel):
    violation_id: str
    violation_type: ViolationType
    primary_entity_id: str
    secondary_entity_id: Optional[str] = None
    penetration_depth: List[float] = Field(default_factory=lambda: [0.0, 0.0])
    iou_score: float = 0.0
    breached_boundary: Optional[str] = None  # "top", "bottom", "left", "right"
    severity: float = 0.5


class VisualPatchProposal(BaseModel):
    """Declarative patch applied to a specific beat and entity."""
    beat_id: int
    entity_id: str
    action_type: RepairActionType = RepairActionType.TRANSLATE
    dx: float = 0.0
    dy: float = 0.0
    scale_multiplier: float = 1.0
    rationale: str = ""
    applied_patch_code: str = ""


class DiagnosticLedgerEntry(BaseModel):
    entry_id: str
    beat_id: int
    iteration: int = 1
    violations_found: List[SpatialViolation] = Field(default_factory=list)
    prescribed_patches: List[VisualPatchProposal] = Field(default_factory=list)
    solver_time_ms: float = 0.0
    resolved: bool = True


# =============================================================================
# COORDINATE CONVERTER
# =============================================================================

def gemini_box_to_manim(box_2d: List[int]) -> BoundingBox2D:
    """
    Converts Gemini normalized bounding box [ymin, xmin, ymax, xmax] (0..1000)
    to Manim coordinates (X in [-4.5, 4.5], Y in [-8.0, 8.0], origin at center).
    """
    ymin, xmin, ymax, xmax = box_2d
    
    # X mapping: u = x/1000 -> X_manim = (u - 0.5) * 9.0
    x_min_m = round((xmin / 1000.0 - 0.5) * MANIM_FRAME_WIDTH, 4)
    x_max_m = round((xmax / 1000.0 - 0.5) * MANIM_FRAME_WIDTH, 4)
    
    # Y mapping: v = y/1000 (downwards) -> Y_manim = (0.5 - v) * 16.0 (upwards)
    y_max_m = round((0.5 - ymin / 1000.0) * MANIM_FRAME_HEIGHT, 4)
    y_min_m = round((0.5 - ymax / 1000.0) * MANIM_FRAME_HEIGHT, 4)
    
    width_m = round(x_max_m - x_min_m, 4)
    height_m = round(y_max_m - y_min_m, 4)
    cx_m = round((x_min_m + x_max_m) / 2.0, 4)
    cy_m = round((y_min_m + y_max_m) / 2.0, 4)
    
    return BoundingBox2D(
        gemini_box=box_2d,
        manim_box=[x_min_m, y_min_m, x_max_m, y_max_m],
        center=[cx_m, cy_m],
        dimensions=[width_m, height_m]
    )


# =============================================================================
# DETERMINISTIC SPATIAL REPULSION SOLVER (Position-Based Dynamics)
# =============================================================================

class PhysicalEntity:
    def __init__(
        self,
        entity_id: str,
        center: Tuple[float, float],
        dim: Tuple[float, float],
        inv_mass: float = 1.0,
        scale: float = 1.0
    ):
        self.entity_id = entity_id
        self.pos = np.array(center, dtype=np.float64)
        self.initial_pos = np.array(center, dtype=np.float64)
        self.dim = np.array(dim, dtype=np.float64)
        self.inv_mass = inv_mass  # 0.0 = fixed/pinned, 0.2 = heavy, 1.0 = mobile
        self.scale = scale

    @property
    def xmin(self) -> float:
        return self.pos[0] - (self.dim[0] * self.scale) / 2.0

    @property
    def xmax(self) -> float:
        return self.pos[0] + (self.dim[0] * self.scale) / 2.0

    @property
    def ymin(self) -> float:
        return self.pos[1] - (self.dim[1] * self.scale) / 2.0

    @property
    def ymax(self) -> float:
        return self.pos[1] + (self.dim[1] * self.scale) / 2.0


class DeterministicLayoutSolver:
    """
    Solves spatial overlaps and safe-zone clipping using Position-Based Dynamics (PBD)
    and Minimum Translation Vectors (MTV). Computes exact mathematical delta vectors.
    """

    def __init__(
        self,
        safe_x: Tuple[float, float] = (SAFE_X_MIN, SAFE_X_MAX),
        safe_y: Tuple[float, float] = (SAFE_Y_MIN, SAFE_Y_MAX),
        padding: Tuple[float, float] = (DEFAULT_PADDING_X, DEFAULT_PADDING_Y)
    ):
        self.safe_x = safe_x
        self.safe_y = safe_y
        self.padding = np.array(padding, dtype=np.float64)

    def detect_violations(self, bodies: List[PhysicalEntity]) -> List[SpatialViolation]:
        """Identifies all pairwise collisions and safe-zone violations."""
        violations = []
        n = len(bodies)

        # 1. Pairwise AABB Intersections
        for i in range(n):
            for j in range(i + 1, n):
                b1, b2 = bodies[i], bodies[j]
                req_dist = (b1.dim * b1.scale + b2.dim * b2.scale) / 2.0 + self.padding
                delta = b1.pos - b2.pos
                pen = req_dist - np.abs(delta)

                if pen[0] > 0.0 and pen[1] > 0.0:
                    # Overlap detected
                    overlap_x = max(0.0, min(b1.xmax, b2.xmax) - max(b1.xmin, b2.xmin))
                    overlap_y = max(0.0, min(b1.ymax, b2.ymax) - max(b1.ymin, b2.ymin))
                    inter_area = overlap_x * overlap_y
                    area1 = (b1.dim[0] * b1.scale) * (b1.dim[1] * b1.scale)
                    area2 = (b2.dim[0] * b2.scale) * (b2.dim[1] * b2.scale)
                    union_area = max(1e-5, area1 + area2 - inter_area)
                    iou = round(inter_area / union_area, 4)

                    violations.append(SpatialViolation(
                        violation_id=f"viol_coll_{b1.entity_id}_{b2.entity_id}",
                        violation_type=ViolationType.AABB_COLLISION,
                        primary_entity_id=b1.entity_id,
                        secondary_entity_id=b2.entity_id,
                        penetration_depth=[round(float(pen[0]), 4), round(float(pen[1]), 4)],
                        iou_score=iou,
                        severity=round(min(1.0, iou * 2.0 + 0.3), 3)
                    ))

        # 2. Safe-Zone Breaches
        for b in bodies:
            if b.inv_mass == 0.0:
                continue  # Pinned items are assumed pre-configured

            half_w = (b.dim[0] * b.scale) / 2.0
            half_h = (b.dim[1] * b.scale) / 2.0

            # Check boundaries
            if b.xmin < self.safe_x[0]:
                violations.append(SpatialViolation(
                    violation_id=f"viol_safe_left_{b.entity_id}",
                    violation_type=ViolationType.SAFE_ZONE_BREACH,
                    primary_entity_id=b.entity_id,
                    penetration_depth=[round(self.safe_x[0] - b.xmin, 4), 0.0],
                    breached_boundary="left",
                    severity=0.75
                ))
            if b.xmax > self.safe_x[1]:
                violations.append(SpatialViolation(
                    violation_id=f"viol_safe_right_{b.entity_id}",
                    violation_type=ViolationType.SAFE_ZONE_BREACH,
                    primary_entity_id=b.entity_id,
                    penetration_depth=[round(b.xmax - self.safe_x[1], 4), 0.0],
                    breached_boundary="right",
                    severity=0.75
                ))
            if b.ymin < self.safe_y[0]:
                violations.append(SpatialViolation(
                    violation_id=f"viol_safe_bottom_{b.entity_id}",
                    violation_type=ViolationType.SAFE_ZONE_BREACH,
                    primary_entity_id=b.entity_id,
                    penetration_depth=[0.0, round(self.safe_y[0] - b.ymin, 4)],
                    breached_boundary="bottom",
                    severity=0.85
                ))
            if b.ymax > self.safe_y[1]:
                violations.append(SpatialViolation(
                    violation_id=f"viol_safe_top_{b.entity_id}",
                    violation_type=ViolationType.SAFE_ZONE_BREACH,
                    primary_entity_id=b.entity_id,
                    penetration_depth=[0.0, round(b.ymax - self.safe_y[1], 4)],
                    breached_boundary="top",
                    severity=0.85
                ))

        return violations

    def solve(
        self,
        bodies: List[PhysicalEntity],
        beat_id: int = 1,
        max_iters: int = 20,
        tol: float = 1e-3
    ) -> DiagnosticLedgerEntry:
        """
        Relaxes positions and scales to satisfy all collision and boundary invariants.
        Returns a complete DiagnosticLedgerEntry with prescribed patches.
        """
        t_start = time.perf_counter()
        initial_violations = self.detect_violations(bodies)
        
        if not initial_violations:
            t_elapsed = (time.perf_counter() - t_start) * 1000.0
            return DiagnosticLedgerEntry(
                entry_id=f"diag_beat_{beat_id}_iter0",
                beat_id=beat_id,
                violations_found=[],
                prescribed_patches=[],
                solver_time_ms=round(t_elapsed, 2),
                resolved=True
            )

        n = len(bodies)
        safe_w_avail = self.safe_x[1] - self.safe_x[0]
        safe_h_avail = self.safe_y[1] - self.safe_y[0]

        for iteration in range(max_iters):
            max_pen = 0.0
            displacements = [np.zeros(2, dtype=np.float64) for _ in range(n)]

            # 1. Pairwise Repulsion via Minimum Translation Vector
            for i in range(n):
                for j in range(i + 1, n):
                    b1, b2 = bodies[i], bodies[j]
                    total_inv = b1.inv_mass + b2.inv_mass
                    if total_inv == 0.0:
                        continue

                    req_dist = (b1.dim * b1.scale + b2.dim * b2.scale) / 2.0 + self.padding
                    delta = b1.pos - b2.pos
                    pen = req_dist - np.abs(delta)

                    if pen[0] > 0.0 and pen[1] > 0.0:
                        overlap_mag = min(pen[0], pen[1])
                        max_pen = max(max_pen, overlap_mag)

                        # Minimum Translation Vector along least resistance
                        if pen[0] < pen[1]:
                            sgn = 1.0 if delta[0] >= 0 else -1.0
                            mtv = np.array([sgn * pen[0], 0.0])
                        else:
                            sgn = 1.0 if delta[1] >= 0 else -1.0
                            mtv = np.array([0.0, sgn * pen[1]])

                        displacements[i] += (b1.inv_mass / total_inv) * mtv
                        displacements[j] -= (b2.inv_mass / total_inv) * mtv

            # Apply displacements
            for i in range(n):
                bodies[i].pos += displacements[i]

            # 2. Safe-Zone Projection & Dimension Clamping
            for i in range(n):
                b = bodies[i]
                if b.inv_mass == 0.0:
                    continue

                half_w = (b.dim[0] * b.scale) / 2.0
                half_h = (b.dim[1] * b.scale) / 2.0

                # Rescale if entity exceeds safe corridor
                if (half_w * 2.0) > safe_w_avail or (half_h * 2.0) > safe_h_avail:
                    scale_x = safe_w_avail / b.dim[0] * 0.92
                    scale_y = safe_h_avail / b.dim[1] * 0.92
                    b.scale = max(0.65, min(b.scale, scale_x, scale_y))
                    half_w = (b.dim[0] * b.scale) / 2.0
                    half_h = (b.dim[1] * b.scale) / 2.0

                # Clamp center to maintain all edges inside boundary
                b.pos[0] = np.clip(b.pos[0], self.safe_x[0] + half_w, self.safe_x[1] - half_w)
                b.pos[1] = np.clip(b.pos[1], self.safe_y[0] + half_h, self.safe_y[1] - half_h)

            if max_pen < tol:
                break

        t_elapsed = (time.perf_counter() - t_start) * 1000.0
        remaining_violations = self.detect_violations(bodies)

        # Build Patch Proposals
        patches = []
        for b in bodies:
            dx = round(float(b.pos[0] - b.initial_pos[0]), 3)
            dy = round(float(b.pos[1] - b.initial_pos[1]), 3)
            scale_m = round(float(b.scale), 3)

            if abs(dx) > 0.05 or abs(dy) > 0.05 or abs(scale_m - 1.0) > 0.03:
                act_type = RepairActionType.TRANSLATE
                if abs(scale_m - 1.0) > 0.03 and (abs(dx) > 0.05 or abs(dy) > 0.05):
                    act_type = RepairActionType.TRANSLATE_AND_RESCALE
                elif abs(scale_m - 1.0) > 0.03:
                    act_type = RepairActionType.RESCALE

                patch_code = f"{b.entity_id}.shift(RIGHT * {dx} + UP * {dy})"
                if scale_m != 1.0:
                    patch_code += f".scale({scale_m})"

                patches.append(VisualPatchProposal(
                    beat_id=beat_id,
                    entity_id=b.entity_id,
                    action_type=act_type,
                    dx=dx,
                    dy=dy,
                    scale_multiplier=scale_m,
                    rationale=f"Resolved collision/safe-zone violation for {b.entity_id}",
                    applied_patch_code=patch_code
                ))

        return DiagnosticLedgerEntry(
            entry_id=f"diag_beat_{beat_id}_iter1",
            beat_id=beat_id,
            violations_found=initial_violations,
            prescribed_patches=patches,
            solver_time_ms=round(t_elapsed, 2),
            resolved=len(remaining_violations) == 0
        )


layout_solver = DeterministicLayoutSolver()
