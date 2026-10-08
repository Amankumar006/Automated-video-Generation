"""Project Aether Critic Council Schemas.

Defines Pydantic V2 schemas for the multi-critic verification engine, binary hard gates,
defect severity ratings, failure objects, and aggregated council evaluation reports
for Project Aether v2 (Pillar 5 / WBS 1.5).
"""

from __future__ import annotations

from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CriticType(str, Enum):
    """Specialized critic agent modalities defined in Pillar 5."""
    VISUAL = "VISUAL"
    TEMPORAL = "TEMPORAL"
    CONTINUITY = "CONTINUITY"
    PERFORMANCE = "PERFORMANCE"
    PHYSICS = "PHYSICS"
    AUDIO = "AUDIO"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, val: Any) -> CriticType:
        if isinstance(val, cls):
            return val
        s = val.value if hasattr(val, "value") else str(val)
        if "." in s:
            s = s.split(".")[-1]
        s = s.upper().strip()
        return cls(s)


class DefectSeverity(str, Enum):
    """Defect impact and triage severity classification."""
    NEGLIGIBLE = "NEGLIGIBLE"   # Imperceptible perceptual variance, ignored
    MINOR = "MINOR"             # Subtle micro-glitch within acceptable tolerance
    MODERATE = "MODERATE"       # Noticeable defect reducing aesthetic quality
    SEVERE = "SEVERE"           # Serious flaw causing hard gate failure / regional repair
    FATAL = "FATAL"             # Catastrophic failure mandating complete shot rejection

    def __str__(self) -> str:
        return self.value

    @property
    def is_hard_gate_breaker(self) -> bool:
        """True if severity trips a binary hard gate failure."""
        return self in (DefectSeverity.SEVERE, DefectSeverity.FATAL)

    @property
    def rank(self) -> int:
        """Numerical rank for sorting (lower value = higher priority)."""
        ranks = {
            DefectSeverity.FATAL: 1,
            DefectSeverity.SEVERE: 2,
            DefectSeverity.MODERATE: 3,
            DefectSeverity.MINOR: 4,
            DefectSeverity.NEGLIGIBLE: 5,
        }
        return ranks.get(self, 6)

    @classmethod
    def from_str(cls, val: Any) -> DefectSeverity:
        if isinstance(val, cls):
            return val
        s = val.value if hasattr(val, "value") else str(val)
        if "." in s:
            s = s.split(".")[-1]
        s = s.upper().strip()
        return cls(s)


class HardGateType(str, Enum):
    """Binary PASS/FAIL quality gates enforced before soft aesthetic scoring."""
    ANATOMICAL_INTEGRITY = "ANATOMICAL_INTEGRITY"
    CHARACTER_IDENTITY = "CHARACTER_IDENTITY"
    PROP_CONTINUITY = "PROP_CONTINUITY"
    LIP_SYNC_ALIGNMENT = "LIP_SYNC_ALIGNMENT"
    PHYSICAL_TRAJECTORY = "PHYSICAL_TRAJECTORY"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, val: Any) -> HardGateType:
        if isinstance(val, cls):
            return val
        s = val.value if hasattr(val, "value") else str(val)
        if "." in s:
            s = s.split(".")[-1]
        s = s.upper().strip()
        return cls(s)


class RepairRecommendation(str, Enum):
    """Downstream surgical repair tactic recommendations (Pillar 6 / WBS 1.7)."""
    REGIONAL_INPAINTING = "REGIONAL_INPAINTING"
    AUDIO_REMASTER = "AUDIO_REMASTER"
    SPATIAL_PREVIS_RERUN = "SPATIAL_PREVIS_RERUN"
    FULL_REGEN = "FULL_REGEN"
    NO_REPAIR_NEEDED = "NO_REPAIR_NEEDED"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, val: Any) -> RepairRecommendation:
        if isinstance(val, cls):
            return val
        s = val.value if hasattr(val, "value") else str(val)
        if "." in s:
            s = s.split(".")[-1]
        s = s.upper().strip()
        return cls(s)


class CouncilStatus(str, Enum):
    """Overall evaluation verdict for candidate video evaluation."""
    ACCEPTED = "ACCEPTED"
    REJECTED_FOR_REPAIR = "REJECTED_FOR_REPAIR"

    def __str__(self) -> str:
        return self.value


class CriticFailureObject(BaseModel):
    """Structured defect report produced by individual critics or CV analyzers."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    failure_type: str = Field(..., description="Defect taxonomy code e.g. 'extra_limbs', 'micro_flicker', 'prop_mismatch'")
    severity: DefectSeverity = Field(DefectSeverity.SEVERE, description="Impact severity classification")
    frame_bounds: Tuple[int, int] = Field((0, 0), description="Temporal frame span [start_frame, end_frame] inclusive")
    bounding_box: Tuple[float, float, float, float] = Field(
        (0.0, 0.0, 1.0, 1.0),
        description="Normalized spatial bounding box [x1, y1, x2, y2] (0.0 to 1.0)",
    )
    target_entity_id: Optional[str] = Field(None, description="Affected character or prop identifier")
    observed_state: str = Field("", description="Empirical defect observation or detected anomaly telemetry")
    expected_state: Optional[str] = Field(None, description="Canonical world state or cinematic expectation")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Detection confidence score")
    recommended_repair: RepairRecommendation = Field(
        RepairRecommendation.FULL_REGEN,
        description="Recommended surgical repair strategy",
    )
    critic_type: Optional[CriticType] = Field(None, description="Critic agent responsible for detection")
    hard_gate: Optional[HardGateType] = Field(None, description="Hard gate violated if applicable")
    description: Optional[str] = Field(None, description="Human-readable defect narrative")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic extension telemetry")

    @model_validator(mode="before")
    @classmethod
    def _normalize_failure_object(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            # Aliases for failure_type
            for fk in ("defect_type", "type", "failure_name", "defect_class", "defect_id"):
                if fk in d and "failure_type" not in d:
                    d["failure_type"] = str(d[fk])
                    break

            # Frame bounds aliases
            if "frame_bounds" not in d:
                start = d.get("start_frame", 0)
                end = d.get("end_frame", start)
                d["frame_bounds"] = (int(start), int(end))
            elif isinstance(d["frame_bounds"], (list, tuple)):
                bounds = list(d["frame_bounds"])
                if len(bounds) == 2:
                    d["frame_bounds"] = (int(bounds[0]), int(bounds[1]))

            # Bounding box aliases
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

            # Entity ID aliases
            for ek in ("entity_id", "character_id", "prop_id", "actor_id"):
                if ek in d and "target_entity_id" not in d:
                    d["target_entity_id"] = str(d[ek])
                    break

            # Repair recommendation aliases
            for rk in ("repair_recommendation", "recommended_repair_strategy", "repair_strategy", "strategy"):
                if rk in d and "recommended_repair" not in d:
                    d["recommended_repair"] = d[rk]
                    break

            # Severity normalization
            if "severity" in d and isinstance(d["severity"], str):
                d["severity"] = DefectSeverity.from_str(d["severity"])

            # Recommended repair normalization
            if "recommended_repair" in d and isinstance(d["recommended_repair"], str):
                d["recommended_repair"] = RepairRecommendation.from_str(d["recommended_repair"])

            # Critic type normalization
            if "critic_type" in d and isinstance(d["critic_type"], str):
                d["critic_type"] = CriticType.from_str(d["critic_type"])

            # Hard gate normalization
            if "hard_gate" in d and isinstance(d["hard_gate"], str):
                d["hard_gate"] = HardGateType.from_str(d["hard_gate"])

            return d
        return data

    @field_validator("bounding_box")
    @classmethod
    def _validate_bounding_box(cls, v: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        if len(v) != 4:
            raise ValueError(f"bounding_box must have 4 coordinates [x1, y1, x2, y2], got {len(v)}")
        x1, y1, x2, y2 = v
        # Clamp minor numerical floats if slightly outside [0.0, 1.0]
        x1 = max(0.0, min(1.0, float(x1)))
        y1 = max(0.0, min(1.0, float(y1)))
        x2 = max(0.0, min(1.0, float(x2)))
        y2 = max(0.0, min(1.0, float(y2)))
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
    def start_frame(self) -> int:
        """Alias for starting frame index."""
        return self.frame_bounds[0]

    @property
    def end_frame(self) -> int:
        """Alias for ending frame index."""
        return self.frame_bounds[1]

    @property
    def bbox(self) -> Tuple[float, float, float, float]:
        """Alias for normalized spatial bounding box."""
        return self.bounding_box

    @property
    def x1(self) -> float:
        """Normalized bounding box left coordinate."""
        return self.bounding_box[0]

    @property
    def y1(self) -> float:
        """Normalized bounding box top coordinate."""
        return self.bounding_box[1]

    @property
    def x2(self) -> float:
        """Normalized bounding box right coordinate."""
        return self.bounding_box[2]

    @property
    def y2(self) -> float:
        """Normalized bounding box bottom coordinate."""
        return self.bounding_box[3]

    @property
    def recommended_repair_strategy(self) -> RepairRecommendation:
        """Alias for recommended_repair strategy."""
        return self.recommended_repair

    @property
    def is_hard_gate_breaker(self) -> bool:
        """True if defect severity forces hard gate rejection."""
        return self.severity.is_hard_gate_breaker


class CriticAuditResult(BaseModel):
    """Specific audit report generated by an individual critic agent."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    critic_type: CriticType = Field(..., description="Modality of evaluating critic")
    passed: bool = Field(True, description="Whether candidate satisfies this critic's standards")
    score: float = Field(10.0, ge=0.0, le=10.0, description="Normalized fidelity or aesthetic score (0.0 to 10.0)")
    failures: List[CriticFailureObject] = Field(default_factory=list, description="Defects identified by this critic")
    hard_gate_verdicts: Dict[HardGateType, bool] = Field(
        default_factory=dict,
        description="Binary verdicts on evaluated hard gates",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Critic telemetry and metrics")

    @property
    def has_fatal_or_severe(self) -> bool:
        """True if any failure is SEVERE or FATAL."""
        return any(f.is_hard_gate_breaker for f in self.failures)

    @property
    def failure_count(self) -> int:
        """Total defect count."""
        return len(self.failures)

    @property
    def fatal_count(self) -> int:
        """Total fatal defect count."""
        return sum(1 for f in self.failures if f.severity == DefectSeverity.FATAL)

    @property
    def severe_count(self) -> int:
        """Total severe defect count."""
        return sum(1 for f in self.failures if f.severity == DefectSeverity.SEVERE)


class RepairActionDirective(BaseModel):
    """Prioritized, actionable intervention instruction for surgical repair."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    priority: int = Field(1, ge=1, description="Execution priority rank (1 = highest)")
    repair_type: RepairRecommendation = Field(..., description="Target repair technique")
    target_entity_id: Optional[str] = Field(None, description="Affected character or prop ID")
    frame_bounds: Tuple[int, int] = Field((0, 0), description="Temporal frame span [start_frame, end_frame]")
    bounding_box: Tuple[float, float, float, float] = Field(
        (0.0, 0.0, 1.0, 1.0),
        description="Normalized spatial bounding box [x1, y1, x2, y2]",
    )
    defect_type: str = Field(..., description="Underlying defect code")
    severity: DefectSeverity = Field(..., description="Defect severity")
    action_description: str = Field(..., description="Actionable repair instruction")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Technique-specific repair parameters")


class CouncilEvaluationReport(BaseModel):
    """Aggregated evaluation report produced by the Master Critic Council."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    hard_gate_verdicts: Dict[HardGateType, bool] = Field(
        default_factory=dict,
        description="Binary PASS/FAIL status for each evaluated hard gate",
    )
    all_hard_gates_passed: bool = Field(True, description="True iff every evaluated hard gate passed")
    soft_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Soft aesthetic scores (Cinematography, Atmosphere, Performance, Pacing)",
    )
    overall_score: float = Field(10.0, ge=0.0, le=10.0, description="Overall aggregated score (0.0 to 10.0)")
    status: CouncilStatus = Field(CouncilStatus.ACCEPTED, description="ACCEPTED vs REJECTED_FOR_REPAIR")
    audit_results: Dict[CriticType, CriticAuditResult] = Field(
        default_factory=dict,
        description="Detailed audit report from each critic modality",
    )
    failures: List[CriticFailureObject] = Field(
        default_factory=list,
        description="Consolidated and prioritized defect list",
    )
    prioritized_repair_plan: List[RepairActionDirective] = Field(
        default_factory=list,
        description="Actionable repair directives ordered by severity and priority",
    )
    shot_id: Optional[str] = Field(None, description="Evaluated shot identifier")
    summary: str = Field("", description="Executive summary narrative of evaluation outcome")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Telemetry extension metadata")

    @property
    def is_accepted(self) -> bool:
        """True if shot passed all hard gates and met quality threshold."""
        return self.status == CouncilStatus.ACCEPTED

    @property
    def failed_hard_gates(self) -> List[HardGateType]:
        """List of hard gates that failed."""
        return [gate for gate, passed in self.hard_gate_verdicts.items() if not passed]

    def get_failures_by_severity(self, severity: DefectSeverity) -> List[CriticFailureObject]:
        """Filter failures by severity tier."""
        return [f for f in self.failures if f.severity == severity]
