"""Project Aether Surgical Repair Engine Schemas.

Defines Pydantic V2 schemas for surgical repair actions, boundary masks,
repair tasks, execution plans, and result telemetry for Project Aether v2
(Pillar 6 / WBS 1.7).
"""

from __future__ import annotations

from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aether.council.schemas import DefectSeverity, RepairRecommendation


class RepairActionType(str, Enum):
    """Categorical intervention actions for surgical repair (Pillar 6 / WBS 1.7)."""
    REGIONAL_TEMPORAL_INPAINTING = "REGIONAL_TEMPORAL_INPAINTING"
    AUDIO_REMASTER_VOICE = "AUDIO_REMASTER_VOICE"
    AUDIO_REMASTER_FOLEY = "AUDIO_REMASTER_FOLEY"
    SPATIAL_PREVIS_REBLOCK = "SPATIAL_PREVIS_REBLOCK"
    FULL_SHOT_REGENERATION = "FULL_SHOT_REGENERATION"
    NO_OP = "NO_OP"

    # Support prompt typo alias if accessed directly
    REGIONAL_TEMONTAL_INPAINTING = "REGIONAL_TEMPORAL_INPAINTING"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, val: Any) -> RepairActionType:
        if isinstance(val, cls):
            return val
        s = val.value if hasattr(val, "value") else str(val)
        if "." in s:
            s = s.split(".")[-1]
        s = s.upper().strip()
        if "TEMONTAL" in s or "INPAINT" in s:
            return cls.REGIONAL_TEMPORAL_INPAINTING
        if "VOICE" in s or ("AUDIO" in s and "FOLEY" not in s):
            return cls.AUDIO_REMASTER_VOICE
        if "FOLEY" in s:
            return cls.AUDIO_REMASTER_FOLEY
        if "PREVIS" in s or "REBLOCK" in s:
            return cls.SPATIAL_PREVIS_REBLOCK
        if "FULL" in s or "REGEN" in s:
            return cls.FULL_SHOT_REGENERATION
        if "NO_OP" in s or "NO_REPAIR" in s:
            return cls.NO_OP
        return cls(s)


class ProtectedRegionType(str, Enum):
    """Types of image/scene elements strictly shielded from inpainting corruption."""
    BACKGROUND = "BACKGROUND"
    FACE = "FACE"
    CAMERA_MOTION = "CAMERA_MOTION"
    STATIC_ELEMENT = "STATIC_ELEMENT"
    OTHER = "OTHER"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, val: Any) -> ProtectedRegionType:
        if isinstance(val, cls):
            return val
        s = val.value if hasattr(val, "value") else str(val)
        if "." in s:
            s = s.split(".")[-1]
        s = s.upper().strip()
        return cls(s)


class ProtectedRegion(BaseModel):
    """Specification of an image or spatial region shielded during inpainting."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    region_type: ProtectedRegionType = Field(ProtectedRegionType.BACKGROUND, description="Category of protected area")
    bounding_box: Optional[Tuple[float, float, float, float]] = Field(
        None,
        description="Normalized bounding box [x1, y1, x2, y2] to protect",
    )
    frame_bounds: Optional[Tuple[int, int]] = Field(None, description="Temporal frame span [start_frame, end_frame]")
    protection_strength: float = Field(1.0, ge=0.0, le=1.0, description="Protection weight (1.0 = strictly untouched)")
    description: Optional[str] = Field(None, description="Reason or context for region protection")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Region metadata, e.g. camera trajectory path or entity telemetry")

    @model_validator(mode="before")
    @classmethod
    def _normalize_protected_region(cls, data: Any) -> Any:
        if isinstance(data, (str, ProtectedRegionType)):
            return {"region_type": ProtectedRegionType.from_str(data)}
        if isinstance(data, dict):
            d = dict(data)
            if "region_type" in d and isinstance(d["region_type"], (str, ProtectedRegionType)):
                d["region_type"] = ProtectedRegionType.from_str(d["region_type"])
            for bk in ("bbox", "box", "bounds"):
                if bk in d and "bounding_box" not in d:
                    d["bounding_box"] = d[bk]
                    break
            if isinstance(d.get("bounding_box"), (list, tuple)):
                b = list(d["bounding_box"])
                if len(b) == 4:
                    d["bounding_box"] = (float(b[0]), float(b[1]), float(b[2]), float(b[3]))
            if isinstance(d.get("frame_bounds"), (list, tuple)):
                fb = list(d["frame_bounds"])
                if len(fb) == 2:
                    d["frame_bounds"] = (int(fb[0]), int(fb[1]))
            return d
        return data


class RepairBoundaryMask(BaseModel):
    """Spatio-temporal boundary mask specification for regional inpainting (RSK-004)."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    bounding_box: Tuple[float, float, float, float] = Field(
        (0.0, 0.0, 1.0, 1.0),
        description="Normalized spatial bounding box [x1, y1, x2, y2] in range [0.0, 1.0]",
    )
    frame_bounds: Tuple[int, int] = Field(
        (0, 0),
        description="Temporal frame range [start_frame, end_frame] inclusive",
    )
    feather_radius_px: float = Field(
        16.0,
        ge=0.0,
        description="Spatial edge feather radius in pixels for Gaussian/linear falloff",
    )
    temporal_pad_frames: int = Field(
        4,
        ge=0,
        description="Temporal ramp-in and ramp-out frame padding to eliminate strobing (RSK-004)",
    )
    protected_regions: List[ProtectedRegion] = Field(
        default_factory=list,
        description="Shielded regions (background, faces, camera motion vectors)",
    )
    box_expansion_ratio: float = Field(
        0.1,
        ge=0.0,
        description="Fractional expansion margin applied around raw defect bounding box",
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_boundary_mask(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            for bk in ("bbox", "box", "spatial_bbox", "bounds"):
                if bk in d and "bounding_box" not in d:
                    d["bounding_box"] = d[bk]
                    break
            if "bounding_box" not in d and all(k in d for k in ("x1", "y1", "x2", "y2")):
                d["bounding_box"] = (float(d["x1"]), float(d["y1"]), float(d["x2"]), float(d["y2"]))
            elif isinstance(d.get("bounding_box"), (list, tuple)):
                box = list(d["bounding_box"])
                if len(box) == 4:
                    d["bounding_box"] = (float(box[0]), float(box[1]), float(box[2]), float(box[3]))

            if "frame_bounds" not in d:
                start = d.get("start_frame", 0)
                end = d.get("end_frame", start)
                d["frame_bounds"] = (int(start), int(end))
            elif isinstance(d.get("frame_bounds"), (list, tuple)):
                bounds = list(d["frame_bounds"])
                if len(bounds) == 2:
                    d["frame_bounds"] = (int(bounds[0]), int(bounds[1]))

            if "protected_regions" in d and isinstance(d["protected_regions"], (list, tuple)):
                norm_regions = []
                for pr in d["protected_regions"]:
                    if isinstance(pr, (str, ProtectedRegionType)):
                        norm_regions.append({"region_type": ProtectedRegionType.from_str(pr)})
                    else:
                        norm_regions.append(pr)
                d["protected_regions"] = norm_regions

            return d
        return data

    @field_validator("bounding_box")
    @classmethod
    def _validate_bounding_box(cls, v: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        if len(v) != 4:
            raise ValueError(f"bounding_box must have 4 coordinates [x1, y1, x2, y2], got {len(v)}")
        x1, y1, x2, y2 = [max(0.0, min(1.0, float(coord))) for coord in v]
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        return (x1, y1, x2, y2)

    @field_validator("frame_bounds")
    @classmethod
    def _validate_frame_bounds(cls, v: Tuple[int, int]) -> Tuple[int, int]:
        if len(v) != 2:
            raise ValueError(f"frame_bounds must have 2 integers [start_frame, end_frame], got {len(v)}")
        start, end = int(v[0]), int(v[1])
        if start < 0 or end < 0:
            raise ValueError(f"frame indices cannot be negative, got ({start}, {end})")
        if start > end:
            start, end = end, start
        return (start, end)

    @property
    def x1(self) -> float:
        return self.bounding_box[0]

    @property
    def y1(self) -> float:
        return self.bounding_box[1]

    @property
    def x2(self) -> float:
        return self.bounding_box[2]

    @property
    def y2(self) -> float:
        return self.bounding_box[3]

    @property
    def start_frame(self) -> int:
        return self.frame_bounds[0]

    @property
    def end_frame(self) -> int:
        return self.frame_bounds[1]

    @property
    def duration_frames(self) -> int:
        return self.frame_bounds[1] - self.frame_bounds[0] + 1

    @property
    def padded_start_frame(self) -> int:
        return max(0, self.start_frame - self.temporal_pad_frames)

    @property
    def padded_end_frame(self) -> int:
        return self.end_frame + self.temporal_pad_frames

    @property
    def area(self) -> float:
        """Normalized spatial area of the bounding box."""
        return (self.x2 - self.x1) * (self.y2 - self.y1)


class ComputeTier(str, Enum):
    """Compute tier hierarchy required to execute a repair task or plan."""
    TIER_0_NOOP = "TIER_0_NOOP"
    TIER_1_AUDIO = "TIER_1_AUDIO"
    TIER_2_REGIONAL_INPAINT = "TIER_2_REGIONAL_INPAINT"
    TIER_3_PREVIS_REBLOCK = "TIER_3_PREVIS_REBLOCK"
    TIER_4_FULL_REGEN = "TIER_4_FULL_REGEN"

    def __str__(self) -> str:
        return self.value

    @property
    def cost_rank(self) -> int:
        ranks = {
            ComputeTier.TIER_0_NOOP: 0,
            ComputeTier.TIER_1_AUDIO: 1,
            ComputeTier.TIER_2_REGIONAL_INPAINT: 2,
            ComputeTier.TIER_3_PREVIS_REBLOCK: 3,
            ComputeTier.TIER_4_FULL_REGEN: 4,
        }
        return ranks.get(self, 5)


class SurgicalRepairTask(BaseModel):
    """An individual actionable repair task scheduled by the RepairPlanner."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    task_id: str = Field(..., description="Unique repair task identifier")
    action_type: RepairActionType = Field(..., description="Technique required for repair")
    target_defect_id: Optional[str] = Field(None, description="Underlying defect taxonomy or failure identifier")
    defect_severity: DefectSeverity = Field(DefectSeverity.MODERATE, description="Defect severity rating")
    priority: int = Field(1, ge=1, description="Execution priority (1 = highest priority)")
    repair_boundary_mask: Optional[RepairBoundaryMask] = Field(
        None,
        description="Spatio-temporal boundary mask for localized inpainting",
    )
    replacement_prompt: Optional[str] = Field(
        None,
        description="Positive replacement prompt guidance for inpainting or regen",
    )
    negative_prompt_modifier: Optional[str] = Field(
        None,
        description="Negative prompt modifier suppressing artifacts or deformations",
    )
    audio_retargeting_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Audio retargeting parameters (latency shift ms, phoneme alignment, volume)",
    )
    fallback_strategy: Optional[RepairActionType] = Field(
        None,
        description="Escalation fallback action if this surgical repair fails",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extension telemetry and renderer settings")

    @model_validator(mode="before")
    @classmethod
    def _normalize_task(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            if "action_type" in d and isinstance(d["action_type"], str):
                d["action_type"] = RepairActionType.from_str(d["action_type"])
            if "defect_severity" in d and isinstance(d["defect_severity"], str):
                d["defect_severity"] = DefectSeverity.from_str(d["defect_severity"])
            if "fallback_strategy" in d and isinstance(d["fallback_strategy"], str):
                d["fallback_strategy"] = RepairActionType.from_str(d["fallback_strategy"])
            return d
        return data

    @property
    def is_inpainting(self) -> bool:
        return self.action_type == RepairActionType.REGIONAL_TEMPORAL_INPAINTING

    @property
    def is_audio(self) -> bool:
        return self.action_type in (RepairActionType.AUDIO_REMASTER_VOICE, RepairActionType.AUDIO_REMASTER_FOLEY)

    @property
    def is_previs(self) -> bool:
        return self.action_type == RepairActionType.SPATIAL_PREVIS_REBLOCK

    @property
    def is_full_regen(self) -> bool:
        return self.action_type == RepairActionType.FULL_SHOT_REGENERATION


class RepairPlan(BaseModel):
    """Complete, prioritized repair plan generated for a rejected shot."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    plan_id: str = Field(..., description="Unique plan identifier")
    original_shot_id: str = Field(..., description="Original shot ID being repaired")
    total_tasks_count: int = Field(0, ge=0, description="Total count of scheduled repair tasks")
    ordered_tasks_list: List[SurgicalRepairTask] = Field(
        default_factory=list,
        description="Ordered list of non-redundant repair tasks sorted by execution priority",
    )
    estimated_compute_tier: Union[ComputeTier, str] = Field(
        ComputeTier.TIER_0_NOOP,
        description="Highest compute tier required by tasks in this plan",
    )
    expected_latency: float = Field(0.0, ge=0.0, description="Expected wall-clock latency in seconds")
    is_feasible: bool = Field(True, description="True if plan is deterministically executable")
    summary: str = Field("", description="Executive rationale for repair decisions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic extension telemetry")

    @model_validator(mode="before")
    @classmethod
    def _normalize_plan(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            # Support alias 'tasks' for 'ordered_tasks_list'
            if "tasks" in d and "ordered_tasks_list" not in d:
                d["ordered_tasks_list"] = d["tasks"]
            if "ordered_tasks_list" in d and isinstance(d["ordered_tasks_list"], list):
                d["total_tasks_count"] = len(d["ordered_tasks_list"])
            return d
        return data

    @property
    def tasks(self) -> List[SurgicalRepairTask]:
        """Alias for ordered_tasks_list."""
        return self.ordered_tasks_list

    @property
    def has_full_regen(self) -> bool:
        return any(t.is_full_regen for t in self.ordered_tasks_list)

    @property
    def has_inpainting(self) -> bool:
        return any(t.is_inpainting for t in self.ordered_tasks_list)

    @property
    def has_audio_repair(self) -> bool:
        return any(t.is_audio for t in self.ordered_tasks_list)

    @property
    def is_empty(self) -> bool:
        return len(self.ordered_tasks_list) == 0


class RepairExecutionResult(BaseModel):
    """Telemetry report produced following execution of a surgical repair task."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    task_id: str = Field(..., description="Executed repair task identifier")
    success_status: bool = Field(True, description="Whether repair operation succeeded")
    repaired_asset_uri: Optional[str] = Field(None, description="URI of repaired video or audio asset")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Repaired frame sequences, renderer metadata, and diagnostic stats",
    )
    boundary_seam_metric: float = Field(
        0.0,
        ge=0.0,
        description="Edge feather variance / seam continuity metric (RSK-004)",
    )
    latency: float = Field(0.0, ge=0.0, description="Execution latency in seconds")
    verified_by_council_flag: bool = Field(
        False,
        description="Whether the repair has been verified and approved by the Critic Council",
    )
    error_message: Optional[str] = Field(None, description="Diagnostic error details if failed")

    @model_validator(mode="before")
    @classmethod
    def _normalize_result(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            if "success" in d and "success_status" not in d:
                d["success_status"] = bool(d["success"])
            return d
        return data

    @property
    def success(self) -> bool:
        return self.success_status

    @property
    def is_seamless(self) -> bool:
        """True if seam metric is within acceptable threshold (variance <= 0.05)."""
        return self.boundary_seam_metric <= 0.05
