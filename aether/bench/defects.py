"""AetherBench Synthetic Defect Ground-Truth Dataset (WBS 1.1.3).

Provides standardized synthetic defect ground-truth datasets for calibrating
the Critic Council (Phase 4), verifying defect localization, evaluating temporal
bounding box detection, and benchmarking surgical repair planning (Phase 6).
"""

from __future__ import annotations

from enum import Enum
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aether.bench.schemas import (
    AetherScenario,
    DefectAnnotation,
    HardGateType,
    RepairStrategy,
)


class DefectCategory(str, Enum):
    """Broad classification of cinematic generation defects."""
    ANATOMICAL_INTEGRITY = "ANATOMICAL_INTEGRITY"
    CHARACTER_IDENTITY = "CHARACTER_IDENTITY"
    PROP_CONTINUITY = "PROP_CONTINUITY"
    LIP_SYNC_ALIGNMENT = "LIP_SYNC_ALIGNMENT"
    TEMPORAL_CONTINUITY = "TEMPORAL_CONTINUITY"
    OPTICAL_REFLECTION = "OPTICAL_REFLECTION"


class DefectSeverity(str, Enum):
    """Defect impact severity rating."""
    FATAL = "FATAL"     # Causes hard gate failure or immediate shot rejection
    MAJOR = "MAJOR"     # Noticeable visual artifact requiring surgical repair
    MINOR = "MINOR"     # Subtle micro-glitch or acceptable perceptual flaw


class GroundTruthDefect(BaseModel):
    """Standardized ground-truth defect annotation with spatial-temporal coordinates."""
    model_config = ConfigDict(extra="forbid")

    defect_id: str = Field(..., description="Unique defect ID e.g. 'GT-DEF-ANAT-001'")
    scenario_id: str = Field(..., description="Target benchmark scenario ID")
    category: DefectCategory = Field(..., description="Defect classification category")
    defect_class: str = Field(..., description="Specific defect type e.g. 'fused_fingers', 'face_drift'")
    start_frame: int = Field(..., ge=0, description="First corrupted frame index (inclusive)")
    end_frame: int = Field(..., ge=0, description="Last corrupted frame index (inclusive)")
    timestamp_sec: float = Field(..., ge=0.0, description="Timestamp of defect onset in seconds")
    bounding_box: Tuple[float, float, float, float] = Field(
        ..., description="Normalized spatial coordinates [x1, y1, x2, y2] (0.0 to 1.0)"
    )
    severity: DefectSeverity = Field(DefectSeverity.FATAL, description="Defect severity rating")
    description: str = Field(..., description="Detailed technical description of the artifact")
    expected_repair_strategy: RepairStrategy = Field(..., description="Ground-truth recommended repair tactic")
    ground_truth_label: str = Field("TRUE_POSITIVE_DEFECT", description="Supervised benchmark evaluation label")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic extension metadata")

    @field_validator("bounding_box")
    @classmethod
    def validate_bbox(cls, v: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        if len(v) != 4:
            raise ValueError("bounding_box must have 4 coordinates [x1, y1, x2, y2]")
        x1, y1, x2, y2 = v
        if not (0.0 <= x1 <= x2 <= 1.0 and 0.0 <= y1 <= y2 <= 1.0):
            raise ValueError(f"bounding_box coordinates must satisfy 0 <= x1 <= x2 <= 1 and 0 <= y1 <= y2 <= 1, got {v}")
        return v

    @model_validator(mode="after")
    def validate_temporal_span(self) -> GroundTruthDefect:
        if self.start_frame > self.end_frame:
            raise ValueError(
                f"start_frame ({self.start_frame}) cannot exceed end_frame ({self.end_frame})"
            )
        if not math.isfinite(self.timestamp_sec):
            raise ValueError("timestamp_sec must be a finite number")
        return self

    def to_defect_annotation(self) -> DefectAnnotation:
        """Convert ground-truth defect into a Critic Council DefectAnnotation model."""
        # Map DefectCategory to HardGateType if direct match
        gate_mapping = {
            DefectCategory.ANATOMICAL_INTEGRITY: HardGateType.ANATOMICAL_INTEGRITY,
            DefectCategory.CHARACTER_IDENTITY: HardGateType.CHARACTER_IDENTITY,
            DefectCategory.PROP_CONTINUITY: HardGateType.PROP_CONTINUITY,
            DefectCategory.LIP_SYNC_ALIGNMENT: HardGateType.LIP_SYNC_ALIGNMENT,
        }
        gate = gate_mapping.get(self.category, HardGateType.ANATOMICAL_INTEGRITY)

        return DefectAnnotation(
            defect_id=self.defect_id,
            gate=gate,
            description=self.description,
            start_frame=self.start_frame,
            end_frame=self.end_frame,
            timestamp_sec=self.timestamp_sec,
            bounding_box=self.bounding_box,
            severity=self.severity.value,
        )


class SyntheticDefectDataset(BaseModel):
    """Collection and catalog of verified ground-truth synthetic defects."""
    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field("aetherbench-gt-defects-v2", description="Dataset version ID")
    version: str = Field("2.0.0", description="Dataset semantic version")
    description: str = Field(
        "Standardized ground-truth defect catalog for Project Aether Critic Council evaluation",
        description="Dataset summary",
    )
    defects: List[GroundTruthDefect] = Field(default_factory=list, description="Annotated defect entries")

    def count(self) -> int:
        """Return total number of defect entries."""
        return len(self.defects)

    def get_by_id(self, defect_id: str) -> Optional[GroundTruthDefect]:
        """Look up a defect by ID."""
        for d in self.defects:
            if d.defect_id == defect_id:
                return d
        return None

    def filter_by_scenario(self, scenario_id: str) -> List[GroundTruthDefect]:
        """Return all defects targeting a specific scenario ID."""
        return [d for d in self.defects if d.scenario_id == scenario_id]

    def filter_by_category(self, category: DefectCategory) -> List[GroundTruthDefect]:
        """Return all defects belonging to a specific category."""
        return [d for d in self.defects if d.category == category]

    def filter_by_severity(self, severity: DefectSeverity) -> List[GroundTruthDefect]:
        """Return all defects with the specified severity."""
        return [d for d in self.defects if d.severity == severity]

    def summary(self) -> Dict[str, Any]:
        """Compute summary statistics for the dataset."""
        cat_counts: Dict[str, int] = {}
        sev_counts: Dict[str, int] = {}
        repair_counts: Dict[str, int] = {}
        scenarios: set[str] = set()

        for d in self.defects:
            cat_counts[d.category.value] = cat_counts.get(d.category.value, 0) + 1
            sev_counts[d.severity.value] = sev_counts.get(d.severity.value, 0) + 1
            repair_counts[d.expected_repair_strategy.value] = repair_counts.get(d.expected_repair_strategy.value, 0) + 1
            scenarios.add(d.scenario_id)

        return {
            "total_defects": len(self.defects),
            "target_scenarios_count": len(scenarios),
            "categories": cat_counts,
            "severities": sev_counts,
            "repair_strategies": repair_counts,
        }

    def export_to_json(self, file_path: Union[str, Path]) -> int:
        """Export dataset to JSON file. Returns count exported."""
        path = Path(file_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))
        return len(self.defects)

    @classmethod
    def import_from_json(cls, file_path: Union[str, Path]) -> SyntheticDefectDataset:
        """Load defect dataset from JSON file."""
        path = Path(file_path).resolve()
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return cls.model_validate(raw)


def generate_ground_truth_defect_dataset(
    scenarios: Optional[List[AetherScenario]] = None,
) -> SyntheticDefectDataset:
    """Generate standardized ground-truth defect catalog mapped across benchmark scenarios.

    Covers all core defect failure modes:
    - Anatomical deformations (fused digits, joint dislocations, hyper-rotations)
    - Identity morphing (jaw drift, eye shape shift, wardrobe color popping)
    - Prop continuity errors (prop drop, hand clipping, phantom vanish)
    - Lip-sync offsets (audio lag, silent viseme movement)
    - Temporal continuity failures (shutter flicker, optical flow jitter tear)
    - Reflection & optical failures (missing specular bounce, inverted refraction)
    """
    defects: List[GroundTruthDefect] = [
        # 1. Anatomical integrity defects
        GroundTruthDefect(
            defect_id="GT-DEF-ANAT-001",
            scenario_id="BENCH-MC-001",
            category=DefectCategory.ANATOMICAL_INTEGRITY,
            defect_class="fused_digits",
            start_frame=36,
            end_frame=52,
            timestamp_sec=1.5,
            bounding_box=(0.42, 0.58, 0.56, 0.72),
            severity=DefectSeverity.FATAL,
            description="Maya's left hand displays 6 fused digits on table surface during zoom-in",
            expected_repair_strategy=RepairStrategy.TEMPORAL_INPAINTING,
            metadata={"affected_joint": "hand_left_phalanges", "defect_area_norm": 0.0196},
        ),
        GroundTruthDefect(
            defect_id="GT-DEF-ANAT-002",
            scenario_id="BENCH-AN-001",
            category=DefectCategory.ANATOMICAL_INTEGRITY,
            defect_class="elbow_joint_inversion",
            start_frame=48,
            end_frame=72,
            timestamp_sec=2.0,
            bounding_box=(0.35, 0.28, 0.65, 0.68),
            severity=DefectSeverity.FATAL,
            description="Fighter Beta's right elbow articulates past 180 degrees unnaturally during hip throw",
            expected_repair_strategy=RepairStrategy.SPATIAL_PREVIS_FALLBACK,
            metadata={"affected_joint": "arm_right_cubital", "defect_area_norm": 0.12},
        ),
        GroundTruthDefect(
            defect_id="GT-DEF-ANAT-003",
            scenario_id="BENCH-TC-001",
            category=DefectCategory.ANATOMICAL_INTEGRITY,
            defect_class="neck_torsion_morph",
            start_frame=120,
            end_frame=144,
            timestamp_sec=5.0,
            bounding_box=(0.40, 0.18, 0.58, 0.42),
            severity=DefectSeverity.MAJOR,
            description="Cervical spine exhibits unnatural 30-degree elongation under rapid strobe pulse",
            expected_repair_strategy=RepairStrategy.TEMPORAL_INPAINTING,
            metadata={"affected_joint": "spine_cervical", "defect_area_norm": 0.0432},
        ),

        # 2. Character identity preservation defects
        GroundTruthDefect(
            defect_id="GT-DEF-IDENT-001",
            scenario_id="BENCH-MC-001",
            category=DefectCategory.CHARACTER_IDENTITY,
            defect_class="facial_jaw_morph",
            start_frame=60,
            end_frame=96,
            timestamp_sec=2.5,
            bounding_box=(0.38, 0.20, 0.52, 0.45),
            severity=DefectSeverity.FATAL,
            description="Detective Thorne's jawline expands and nose bridge shifts width across camera pan",
            expected_repair_strategy=RepairStrategy.TEMPORAL_INPAINTING,
            metadata={"drift_metric_cosine": 0.71, "threshold": 0.90},
        ),
        GroundTruthDefect(
            defect_id="GT-DEF-IDENT-002",
            scenario_id="BENCH-TC-001",
            category=DefectCategory.CHARACTER_IDENTITY,
            defect_class="wardrobe_state_healing",
            start_frame=144,
            end_frame=180,
            timestamp_sec=6.0,
            bounding_box=(0.32, 0.35, 0.52, 0.65),
            severity=DefectSeverity.FATAL,
            description="Torn left sleeve spontaneously self-heals into pristine intact black leather",
            expected_repair_strategy=RepairStrategy.TEMPORAL_INPAINTING,
            metadata={"target_wardrobe_id": "leather_004", "state_expected": "left_sleeve_torn"},
        ),
        GroundTruthDefect(
            defect_id="GT-DEF-IDENT-003",
            scenario_id="BENCH-TC-001",
            category=DefectCategory.CHARACTER_IDENTITY,
            defect_class="injury_erasure",
            start_frame=192,
            end_frame=216,
            timestamp_sec=8.0,
            bounding_box=(0.44, 0.22, 0.54, 0.38),
            severity=DefectSeverity.MAJOR,
            description="Dried blood mark on right cheek vanishes during lighting angle change",
            expected_repair_strategy=RepairStrategy.TEMPORAL_INPAINTING,
            metadata={"expected_injury": "blood_cheek_right"},
        ),

        # 3. Prop continuity defects
        GroundTruthDefect(
            defect_id="GT-DEF-PROP-001",
            scenario_id="BENCH-HO-001",
            category=DefectCategory.PROP_CONTINUITY,
            defect_class="prop_teleportation_drop",
            start_frame=48,
            end_frame=72,
            timestamp_sec=2.0,
            bounding_box=(0.42, 0.45, 0.62, 0.68),
            severity=DefectSeverity.FATAL,
            description="Cryogenic vial vanishes from Maya's fingers 3 frames before Thorne makes grip contact",
            expected_repair_strategy=RepairStrategy.KEYFRAME_INTERPOLATION,
            metadata={"prop_id": "cryo_vial_x9", "expected_window": [1.8, 3.2]},
        ),
        GroundTruthDefect(
            defect_id="GT-DEF-PROP-002",
            scenario_id="BENCH-HO-001",
            category=DefectCategory.PROP_CONTINUITY,
            defect_class="mesh_penetration_clipping",
            start_frame=65,
            end_frame=84,
            timestamp_sec=2.7,
            bounding_box=(0.46, 0.48, 0.58, 0.65),
            severity=DefectSeverity.MAJOR,
            description="Vial cylinder clips through Thorne's palm mesh during transfer grip phase",
            expected_repair_strategy=RepairStrategy.KEYFRAME_INTERPOLATION,
            metadata={"prop_id": "cryo_vial_x9"},
        ),
        GroundTruthDefect(
            defect_id="GT-DEF-PROP-003",
            scenario_id="BENCH-TC-001",
            category=DefectCategory.PROP_CONTINUITY,
            defect_class="static_prop_disappearance",
            start_frame=80,
            end_frame=108,
            timestamp_sec=3.3,
            bounding_box=(0.55, 0.48, 0.70, 0.75),
            severity=DefectSeverity.FATAL,
            description="Flashlight held in right hand flickers into nonexistence across strobe cycle",
            expected_repair_strategy=RepairStrategy.TEMPORAL_INPAINTING,
            metadata={"prop_id": "flashlight_torch"},
        ),

        # 4. Lip-sync alignment defects
        GroundTruthDefect(
            defect_id="GT-DEF-LIP-001",
            scenario_id="BENCH-MC-001",
            category=DefectCategory.LIP_SYNC_ALIGNMENT,
            defect_class="phoneme_audio_lead",
            start_frame=24,
            end_frame=60,
            timestamp_sec=1.0,
            bounding_box=(0.42, 0.32, 0.54, 0.44),
            severity=DefectSeverity.FATAL,
            description="Detective Thorne's spoken dialogue leads mouth shape opening by 110ms",
            expected_repair_strategy=RepairStrategy.AUDIO_ONLY_REMASTER,
            metadata={"offset_ms": 110.0, "tolerance_ms": 40.0},
        ),
        GroundTruthDefect(
            defect_id="GT-DEF-LIP-002",
            scenario_id="BENCH-MC-001",
            category=DefectCategory.LIP_SYNC_ALIGNMENT,
            defect_class="static_mouth_speaking",
            start_frame=72,
            end_frame=96,
            timestamp_sec=3.0,
            bounding_box=(0.43, 0.33, 0.53, 0.43),
            severity=DefectSeverity.FATAL,
            description="Dialogue track active while speaker's lips remain closed in static viseme",
            expected_repair_strategy=RepairStrategy.AUDIO_ONLY_REMASTER,
            metadata={"offset_ms": 250.0},
        ),

        # 5. Temporal continuity defects
        GroundTruthDefect(
            defect_id="GT-DEF-TEMP-001",
            scenario_id="BENCH-RC-001",
            category=DefectCategory.TEMPORAL_CONTINUITY,
            defect_class="optical_flow_jitter_spike",
            start_frame=36,
            end_frame=48,
            timestamp_sec=1.5,
            bounding_box=(0.10, 0.10, 0.90, 0.90),
            severity=DefectSeverity.FATAL,
            description="High-velocity whip pan experiences abrupt frame shear and optical acceleration tear",
            expected_repair_strategy=RepairStrategy.TEMPORAL_INPAINTING,
            metadata={"measured_jitter": 0.28, "threshold": 0.18},
        ),
        GroundTruthDefect(
            defect_id="GT-DEF-TEMP-002",
            scenario_id="BENCH-TC-001",
            category=DefectCategory.TEMPORAL_CONTINUITY,
            defect_class="high_frequency_luminance_flicker",
            start_frame=160,
            end_frame=184,
            timestamp_sec=6.6,
            bounding_box=(0.0, 0.0, 1.0, 1.0),
            severity=DefectSeverity.MAJOR,
            description="Background walls flicker uncontrollably at 12 Hz outside configured 2.5 Hz strobe",
            expected_repair_strategy=RepairStrategy.TEMPORAL_INPAINTING,
            metadata={"flicker_ratio": 0.18, "threshold": 0.10},
        ),

        # 6. Optical & reflection defects
        GroundTruthDefect(
            defect_id="GT-DEF-OPT-001",
            scenario_id="BENCH-GR-001",
            category=DefectCategory.OPTICAL_REFLECTION,
            defect_class="missing_specular_bounce",
            start_frame=24,
            end_frame=72,
            timestamp_sec=1.0,
            bounding_box=(0.20, 0.30, 0.80, 0.85),
            severity=DefectSeverity.MAJOR,
            description="Wet glass storefront displays zero reflection of prominent magenta neon sign",
            expected_repair_strategy=RepairStrategy.KEYFRAME_INTERPOLATION,
            metadata={"expected_specular_intensity": 0.95},
        ),
        GroundTruthDefect(
            defect_id="GT-DEF-OPT-002",
            scenario_id="BENCH-LT-001",
            category=DefectCategory.OPTICAL_REFLECTION,
            defect_class="shadow_vector_inversion_jump",
            start_frame=40,
            end_frame=55,
            timestamp_sec=1.8,
            bounding_box=(0.30, 0.50, 0.70, 0.95),
            severity=DefectSeverity.MAJOR,
            description="Cast shadow jumps instantaneously 180 degrees instead of rotating smoothly with beacon",
            expected_repair_strategy=RepairStrategy.KEYFRAME_INTERPOLATION,
            metadata={"shadow_sharpness": 0.85},
        ),
    ]

    return SyntheticDefectDataset(defects=defects)
