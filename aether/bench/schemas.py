"""AetherBench Data Schemas.

Defines Pydantic models and schemas for cinematic benchmark scenarios,
character descriptors, camera kinematics, physical constraints, hard gates,
and evaluation metrics for Project Aether v2.
"""

from __future__ import annotations

import math
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ComplexityLevel(IntEnum):
    """Complexity classification level (0-5) defined in Pillar 3."""
    LEVEL_0_TEXT_ONLY = 0           # Pure text prompt: cutaways, cloudscapes, abstract
    LEVEL_1_REF_CONDITIONED = 1     # Reference conditioned: establishing shots, static portraits
    LEVEL_2_KEYFRAMES = 2           # Keyframe conditioned: simple camera pans, character actions
    LEVEL_3_2D_TRAJECTORY = 3       # 2D pose/trajectory: talking heads, walking to camera
    LEVEL_4_3D_BLOCKING = 4         # 3D geometric blocking: multi-character, crane moves, handoffs
    LEVEL_5_DETERMINISTIC_SIM = 5   # Deterministic simulation: complex collisions, fluids, stunts


class PhysicsDifficulty(str, Enum):
    """Subjective physics difficulty level."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class PhysicsChallengeType(str, Enum):
    """Specific physical phenomenon stress-tested in the scenario."""
    FLUID_DYNAMICS = "FLUID_DYNAMICS"
    GLASS_REFRACTION = "GLASS_REFRACTION"
    SPECULAR_REFLECTION = "SPECULAR_REFLECTION"
    RIGID_BODY_COLLISION = "RIGID_BODY_COLLISION"
    SOFT_BODY_DEFORMATION = "SOFT_BODY_DEFORMATION"
    CLOTH_SIMULATION = "CLOTH_SIMULATION"
    SMOKE_VOLUMETRICS = "SMOKE_VOLUMETRICS"
    PARTICLE_EMISSION = "PARTICLE_EMISSION"
    RAPID_SHADOW_INVERSION = "RAPID_SHADOW_INVERSION"
    HIGH_VELOCITY_IMPACT = "HIGH_VELOCITY_IMPACT"


class CameraMovementType(str, Enum):
    """Kinematic camera trajectory type."""
    STATIC = "STATIC"
    PAN = "PAN"
    TILT = "TILT"
    ROLL = "ROLL"
    DOLLY_IN = "DOLLY_IN"
    DOLLY_OUT = "DOLLY_OUT"
    TRUCK = "TRUCK"
    PEDESTAL = "PEDESTAL"
    CRANE = "CRANE"
    WHIP_PAN = "WHIP_PAN"
    ORBIT = "ORBIT"
    TRACKING = "TRACKING"
    HANDHELD = "HANDHELD"
    DUTCH_ANGLE = "DUTCH_ANGLE"


class StressTestCategory(str, Enum):
    """Cinematic stress-test domain."""
    MULTI_CHARACTER_INTERACTION = "MULTI_CHARACTER_INTERACTION"
    HAND_OBJECT_HANDOFF = "HAND_OBJECT_HANDOFF"
    RAPID_CAMERA_MOVEMENT = "RAPID_CAMERA_MOVEMENT"
    GLASS_REFLECTION_OPTICS = "GLASS_REFLECTION_OPTICS"
    TEMPORAL_CONTINUITY = "TEMPORAL_CONTINUITY"
    FLUID_COLLISION_PHYSICS = "FLUID_COLLISION_PHYSICS"
    RAPID_LIGHTING_TRANSITION = "RAPID_LIGHTING_TRANSITION"
    ANATOMICAL_STRESS = "ANATOMICAL_STRESS"


class GateStatus(str, Enum):
    """Status evaluation for a quality gate."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


class HardGateType(str, Enum):
    """Pillar 5 binary quality gates."""
    ANATOMICAL_INTEGRITY = "ANATOMICAL_INTEGRITY"
    CHARACTER_IDENTITY = "CHARACTER_IDENTITY"
    PROP_CONTINUITY = "PROP_CONTINUITY"
    LIP_SYNC_ALIGNMENT = "LIP_SYNC_ALIGNMENT"


class RepairStrategy(str, Enum):
    """Pillar 6 surgical repair intervention strategies."""
    TEMPORAL_INPAINTING = "TEMPORAL_INPAINTING"
    AUDIO_ONLY_REMASTER = "AUDIO_ONLY_REMASTER"
    SPATIAL_PREVIS_FALLBACK = "SPATIAL_PREVIS_FALLBACK"
    KEYFRAME_INTERPOLATION = "KEYFRAME_INTERPOLATION"
    FULL_REGENERATION = "FULL_REGENERATION"


class SurfaceProperties(BaseModel):
    """Physical surface conditions for the ground and materials."""
    model_config = ConfigDict(extra="forbid")

    wetness: float = Field(0.0, ge=0.0, le=1.0, description="Surface liquid wetness factor (0.0 to 1.0)")
    reflections: bool = Field(False, description="Whether specular ground reflections are expected")
    roughness: float = Field(0.5, ge=0.0, le=1.0, description="Microfacet roughness")
    specular_intensity: float = Field(0.5, ge=0.0, le=1.0, description="Reflective gloss level")


class EnvironmentLighting(BaseModel):
    """Cinematic environmental lighting parameters."""
    model_config = ConfigDict(extra="forbid")

    ambient_description: str = Field(..., description="Semantic lighting description e.g. emergency_red_pulsing")
    color_temperature_k: Optional[int] = Field(None, ge=1000, le=20000, description="Color temp in Kelvin")
    strobe_frequency_hz: float = Field(0.0, ge=0.0, description="Lighting flicker/strobe rate in Hertz")
    key_light_direction: Optional[List[float]] = Field(None, description="Normalized 3D vector [dx, dy, dz]")
    contrast_ratio: float = Field(2.0, ge=1.0, description="Lighting key-to-fill contrast ratio")
    shadow_sharpness: float = Field(0.8, ge=0.0, le=1.0, description="Shadow penumbra sharpness")

    @field_validator("key_light_direction")
    @classmethod
    def validate_light_direction(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        if v is not None:
            if len(v) != 3:
                raise ValueError("key_light_direction must be a 3-element [dx, dy, dz] list")
            if not all(math.isfinite(c) for c in v):
                raise ValueError("key_light_direction components must be finite numbers")
            mag = math.sqrt(sum(c * c for c in v))
            if mag == 0:
                raise ValueError("key_light_direction vector cannot be a zero vector")
        return v


class SceneVariables(BaseModel):
    """Macro scene environment variables."""
    model_config = ConfigDict(extra="forbid")

    location: str = Field(..., description="Unique scene environment location name")
    time_of_day: str = Field(..., description="Timestamp or time descriptor, e.g. '23:42' or 'golden_hour'")
    environment: EnvironmentLighting = Field(..., description="Lighting setup")
    particulates: Optional[str] = Field(None, description="Volumetric particulates e.g. 'steam_leak', 'dense_fog'")
    surface: SurfaceProperties = Field(default_factory=SurfaceProperties, description="Ground surface material properties")
    weather: Optional[str] = Field("clear", description="Macro weather condition")
    audio_ambience: Optional[str] = Field(None, description="Acoustic background tone descriptor")


class WardrobeGarment(BaseModel):
    """Specific wardrobe garment with damage or persistent state tracking."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique wardrobe item identifier e.g. 'leather_004'")
    type: str = Field(..., description="Garment classification e.g. 'jacket', 'trousers', 'boots'")
    state: str = Field("pristine", description="Persistent physical state e.g. 'left_sleeve_torn'")
    color: Optional[str] = Field(None, description="Hex code or descriptive color")


class CharacterDescriptor(BaseModel):
    """Character identity, spatial position, and state tracking."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique character ID e.g. 'maya'")
    name: str = Field(..., description="Display name e.g. 'Maya Lin'")
    position: List[float] = Field(..., description="3D coordinate position in meters [x, y, z]")
    facing_angle: float = Field(..., ge=0.0, le=360.0, description="Rotation angle in degrees [0, 360]")
    eyeline_vector: List[float] = Field(..., description="Eyeline orientation unit vector [dx, dy, dz]")
    wardrobe: Dict[str, WardrobeGarment] = Field(default_factory=dict, description="Garment mapping by slot")
    injuries: List[str] = Field(default_factory=list, description="List of physical wounds e.g. ['blood_cheek_right']")
    props: Dict[str, str] = Field(default_factory=dict, description="Props currently held e.g. {'right_hand': 'vial'}")
    emotional_state: str = Field("neutral", description="Emotional affect e.g. 'hyper-vigilant'")
    action_description: str = Field("", description="High-level action performed in the scene")

    @field_validator("position")
    @classmethod
    def validate_position(cls, v: List[float]) -> List[float]:
        if len(v) != 3:
            raise ValueError("position must be a 3-element [x, y, z] coordinate list")
        if not all(math.isfinite(c) for c in v):
            raise ValueError("position coordinates must be finite numbers")
        return v

    @field_validator("eyeline_vector")
    @classmethod
    def validate_eyeline(cls, v: List[float]) -> List[float]:
        if len(v) != 3:
            raise ValueError("eyeline_vector must be a 3-element [dx, dy, dz] list")
        if not all(math.isfinite(c) for c in v):
            raise ValueError("eyeline_vector components must be finite numbers")
        mag = math.sqrt(sum(c * c for c in v))
        if mag == 0:
            raise ValueError("eyeline_vector cannot be zero vector")
        return v


class CameraParameters(BaseModel):
    """Cinematic camera sensor, lens, and movement parameters."""
    model_config = ConfigDict(extra="forbid")

    lens_mm: float = Field(..., gt=0.0, description="Focal length in millimeters e.g. 35.0, 50.0")
    sensor_format: str = Field("full_frame", description="Sensor format e.g. 'full_frame', 'super35', 'imax'")
    aperture_fstop: float = Field(2.8, gt=0.0, description="Lens aperture f-number")
    shutter_angle_deg: float = Field(180.0, gt=0.0, le=360.0, description="Motion blur shutter angle in degrees")
    movement_type: CameraMovementType = Field(..., description="Type of camera movement")
    start_position: List[float] = Field(..., description="Camera initial 3D position [x, y, z]")
    end_position: List[float] = Field(..., description="Camera terminal 3D position [x, y, z]")
    velocity_mps: float = Field(0.0, ge=0.0, description="Camera translation velocity in meters/second")
    eyeline_vector: Optional[List[float]] = Field(None, description="Camera optical axis vector")
    focus_distance_m: float = Field(2.5, gt=0.0, description="Initial focal plane distance in meters")
    rack_focus: bool = Field(False, description="Whether rack focus transition occurs")
    rack_focus_target_m: Optional[float] = Field(None, gt=0.0, description="Terminal focus distance if racking")

    @field_validator("start_position", "end_position")
    @classmethod
    def validate_camera_coords(cls, v: List[float]) -> List[float]:
        if len(v) != 3:
            raise ValueError("Camera position must be a 3-element [x, y, z] list")
        if not all(math.isfinite(c) for c in v):
            raise ValueError("Camera position coordinates must be finite numbers")
        return v

    @field_validator("eyeline_vector")
    @classmethod
    def validate_camera_eyeline(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        if v is not None:
            if len(v) != 3:
                raise ValueError("Camera eyeline_vector must be a 3-element [dx, dy, dz] list")
            if not all(math.isfinite(c) for c in v):
                raise ValueError("Camera eyeline_vector components must be finite numbers")
            mag = math.sqrt(sum(c * c for c in v))
            if mag == 0:
                raise ValueError("Camera eyeline_vector cannot be a zero vector")
        return v

    @model_validator(mode="after")
    def validate_rack_focus_consistency(self) -> CameraParameters:
        if self.rack_focus and self.rack_focus_target_m is None:
            raise ValueError("rack_focus_target_m must be provided when rack_focus is True")
        return self


class PhysicsProfile(BaseModel):
    """Physics simulation challenge parameters and constraints."""
    model_config = ConfigDict(extra="forbid")

    difficulty: PhysicsDifficulty = Field(..., description="Physics simulation difficulty rating")
    challenges: List[PhysicsChallengeType] = Field(..., min_length=1, description="List of physical challenges tested")
    gravity_vector: List[float] = Field(default_factory=lambda: [0.0, -9.81, 0.0], description="Gravity vector [gx, gy, gz]")
    fluid_viscosity: Optional[float] = Field(None, ge=0.0, description="Dynamic viscosity in Pa·s if fluid is present")
    collision_elasticity: Optional[float] = Field(None, ge=0.0, le=1.0, description="Coefficient of restitution")
    optical_refraction_index: Optional[float] = Field(None, ge=1.0, description="Index of refraction (e.g. 1.52 for glass)")
    simulation_tolerance: float = Field(0.05, ge=0.0, le=1.0, description="Allowed physical trajectory error tolerance")

    @field_validator("gravity_vector")
    @classmethod
    def validate_gravity(cls, v: List[float]) -> List[float]:
        if len(v) != 3:
            raise ValueError("gravity_vector must be a 3-element list")
        return v


class HardGateConstraints(BaseModel):
    """Tier 1 binary pass/fail continuity and integrity constraints."""
    model_config = ConfigDict(extra="forbid")

    anatomical_integrity: bool = Field(True, description="Strict ban on fused limbs, extra fingers, or joint popping")
    max_limb_deformation_tolerance: float = Field(0.05, ge=0.0, le=0.5, description="Maximum permitted skeletal distortion")
    character_identity_preservation: bool = Field(True, description="Character facial and anatomical identity invariance")
    min_face_embedding_cosine: float = Field(0.85, ge=0.0, le=1.0, description="Minimum face embedding cosine similarity")
    prop_continuity: bool = Field(True, description="Enforce strict prop persistence and handoff rules")
    handoff_prop_id: Optional[str] = Field(None, description="Specific prop ID involved in handoff if applicable")
    handoff_source_character: Optional[str] = Field(None, description="Character giving the prop")
    handoff_target_character: Optional[str] = Field(None, description="Character receiving the prop")
    handoff_window_start_sec: Optional[float] = Field(None, ge=0.0, description="Start timestamp of transfer window")
    handoff_window_end_sec: Optional[float] = Field(None, ge=0.0, description="End timestamp of transfer window")
    lip_sync_alignment: bool = Field(True, description="Audio-to-visual phoneme sync enforcement")
    max_phoneme_offset_ms: float = Field(40.0, ge=0.0, description="Max allowed lip sync latency in milliseconds")

    @model_validator(mode="after")
    def validate_handoff_window(self) -> HardGateConstraints:
        if self.handoff_window_start_sec is not None and self.handoff_window_end_sec is not None:
            if self.handoff_window_start_sec >= self.handoff_window_end_sec:
                raise ValueError("handoff_window_start_sec must be strictly less than handoff_window_end_sec")
        return self


class TemporalContinuityConstraints(BaseModel):
    """Temporal and optical consistency thresholds."""
    model_config = ConfigDict(extra="forbid")

    max_optical_flow_jitter: float = Field(0.15, ge=0.0, description="Max frame-to-frame optical flow acceleration jitter")
    min_ssim_frame_to_frame: float = Field(0.80, ge=0.0, le=1.0, description="Minimum pairwise SSIM across adjacent frames")
    max_flicker_ratio: float = Field(0.08, ge=0.0, le=1.0, description="Max permissible high-frequency luminance flicker")
    line_of_action_180_deg_enforced: bool = Field(True, description="Cinema 180-degree line-of-action rule compliance")
    allow_motion_blur: bool = Field(True, description="Permit velocity-proportional cinematic shutter blur")


class SoftScoringSpec(BaseModel):
    """Tier 2 soft aesthetic and cinematography criteria."""
    model_config = ConfigDict(extra="forbid")

    min_cinematography: float = Field(8.0, ge=0.0, le=10.0, description="Minimum cinematography score (0-10)")
    min_visual_aesthetic: float = Field(8.0, ge=0.0, le=10.0, description="Minimum visual aesthetic score (0-10)")
    min_narrative_pacing: float = Field(8.0, ge=0.0, le=10.0, description="Minimum narrative pacing score (0-10)")
    min_aggregate_score: float = Field(8.0, ge=0.0, le=10.0, description="Minimum weighted aggregate score to PASS")
    cinematography_weight: float = Field(0.35, ge=0.0, le=1.0)
    aesthetic_weight: float = Field(0.40, ge=0.0, le=1.0)
    pacing_weight: float = Field(0.25, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_weights(self) -> SoftScoringSpec:
        total = self.cinematography_weight + self.aesthetic_weight + self.pacing_weight
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Soft score weights must sum to 1.0, got {total:.3f}")
        return self


class AetherScenario(BaseModel):
    """Master benchmark scenario definition for AetherBench."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique scenario benchmark identifier e.g. 'BENCH-MC-001'")
    title: str = Field(..., description="Human-readable scenario title")
    description: str = Field(..., description="Detailed narrative and cinematic scenario description")
    category: StressTestCategory = Field(..., description="Benchmark stress test category")
    complexity_level: ComplexityLevel = Field(..., description="Required generation complexity level (0-5)")
    duration_seconds: float = Field(..., gt=0.0, description="Total shot duration in seconds")
    target_fps: int = Field(24, ge=1, le=120, description="Target frame rate (default 24 fps)")
    resolution: Tuple[int, int] = Field((1920, 1080), description="Target width and height in pixels")
    scene_variables: SceneVariables = Field(..., description="Macro scene variables")
    characters: List[CharacterDescriptor] = Field(default_factory=list, description="Characters involved in shot")
    camera: CameraParameters = Field(..., description="Camera lens and kinematic trajectory")
    physics_profile: PhysicsProfile = Field(..., description="Physics simulation profile")
    hard_gate_constraints: HardGateConstraints = Field(default_factory=HardGateConstraints)
    temporal_constraints: TemporalContinuityConstraints = Field(default_factory=TemporalContinuityConstraints)
    soft_scoring_spec: SoftScoringSpec = Field(default_factory=SoftScoringSpec)
    tags: List[str] = Field(default_factory=list, description="Descriptive metadata tags")
    expected_repair_strategy_on_failure: Optional[RepairStrategy] = Field(
        None, description="Prescribed repair tactic if scenario fails generation"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary extension metadata")

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, v: Tuple[int, int]) -> Tuple[int, int]:
        if len(v) != 2:
            raise ValueError("resolution must be a 2-element (width, height) tuple")
        w, h = v
        if w <= 0 or h <= 0:
            raise ValueError(f"resolution width and height must be strictly positive integers, got ({w}, {h})")
        return v

    @field_validator("id")
    @classmethod
    def validate_scenario_id(cls, v: str) -> str:
        v_clean = v.strip()
        if not v_clean:
            raise ValueError("Scenario ID cannot be empty or whitespace")
        return v_clean

    @field_validator("characters")
    @classmethod
    def validate_unique_characters(cls, chars: List[CharacterDescriptor]) -> List[CharacterDescriptor]:
        ids = [c.id for c in chars]
        if len(ids) != len(set(ids)):
            raise ValueError("Characters in scenario must possess unique IDs")
        return chars

    @model_validator(mode="after")
    def validate_handoff_characters_exist(self) -> AetherScenario:
        hg = self.hard_gate_constraints
        char_ids = {c.id for c in self.characters}
        if hg.handoff_source_character and hg.handoff_source_character not in char_ids:
            raise ValueError(f"handoff_source_character '{hg.handoff_source_character}' not found in characters")
        if hg.handoff_target_character and hg.handoff_target_character not in char_ids:
            raise ValueError(f"handoff_target_character '{hg.handoff_target_character}' not found in characters")
        if (
            hg.handoff_source_character
            and hg.handoff_target_character
            and hg.handoff_source_character == hg.handoff_target_character
        ):
            raise ValueError(
                f"handoff_source_character and handoff_target_character must be distinct, got '{hg.handoff_source_character}' for both"
            )
        if hg.handoff_window_start_sec is not None and hg.handoff_window_start_sec > self.duration_seconds:
            raise ValueError(
                f"handoff_window_start_sec ({hg.handoff_window_start_sec}) exceeds scenario duration ({self.duration_seconds})"
            )
        if hg.handoff_window_end_sec and hg.handoff_window_end_sec > self.duration_seconds:
            raise ValueError(
                f"handoff_window_end_sec ({hg.handoff_window_end_sec}) exceeds scenario duration ({self.duration_seconds})"
            )
        return self


class DefectAnnotation(BaseModel):
    """Localized spatial and temporal defect identified by Critic Council."""
    model_config = ConfigDict(extra="forbid")

    defect_id: str = Field(..., description="Unique defect identifier")
    gate: HardGateType = Field(..., description="Violated hard gate")
    description: str = Field(..., description="Detailed description of anomaly")
    start_frame: Optional[int] = Field(None, ge=0)
    end_frame: Optional[int] = Field(None, ge=0)
    timestamp_sec: Optional[float] = Field(None, ge=0.0)
    bounding_box: Optional[Tuple[float, float, float, float]] = Field(
        None, description="Normalized coordinates [x1, y1, x2, y2] where 0.0 <= c <= 1.0"
    )
    severity: str = Field("FATAL", description="Severity level: 'FATAL', 'MAJOR', 'MINOR'")

    @field_validator("bounding_box")
    @classmethod
    def validate_bbox(cls, v: Optional[Tuple[float, float, float, float]]) -> Optional[Tuple[float, float, float, float]]:
        if v is not None:
            if len(v) != 4:
                raise ValueError("bounding_box must have 4 coordinates [x1, y1, x2, y2]")
            x1, y1, x2, y2 = v
            if not (0.0 <= x1 <= x2 <= 1.0 and 0.0 <= y1 <= y2 <= 1.0):
                raise ValueError("bounding_box coordinates must satisfy 0 <= x1 <= x2 <= 1 and 0 <= y1 <= y2 <= 1")
        return v

    @model_validator(mode="after")
    def validate_frame_order(self) -> DefectAnnotation:
        if self.start_frame is not None and self.end_frame is not None:
            if self.start_frame > self.end_frame:
                raise ValueError(
                    f"start_frame ({self.start_frame}) cannot be greater than end_frame ({self.end_frame})"
                )
        return self


class CandidateEvaluationInput(BaseModel):
    """Model generation candidate output data for evaluation against a scenario."""
    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., description="Scenario ID under test")
    model_id: str = Field(..., description="Target model ID e.g. 'google_veo_3.1'")
    candidate_id: str = Field(..., description="Candidate execution ID")
    generation_latency_sec: float = Field(0.0, ge=0.0)
    estimated_cost_usd: float = Field(0.0, ge=0.0)
    anatomical_score: float = Field(1.0, ge=0.0, le=1.0, description="1.0 = perfect anatomical integrity")
    face_similarity_cosine: float = Field(1.0, ge=0.0, le=1.0, description="Observed face embedding cosine similarity")
    prop_handoff_success: bool = Field(True, description="Whether prop transfer succeeded seamlessly")
    lip_sync_offset_ms: float = Field(0.0, ge=-5000.0, le=5000.0, description="Audio-video phoneme offset in milliseconds")
    optical_flow_jitter: float = Field(0.02, ge=0.0, description="Measured optical flow velocity variance")
    min_observed_ssim: float = Field(0.92, ge=0.0, le=1.0, description="Lowest observed frame-to-frame SSIM")
    observed_flicker_ratio: float = Field(0.01, ge=0.0, le=1.0, description="Observed high-frequency luminance flicker")
    line_of_action_preserved: bool = Field(True, description="Whether 180-degree line-of-action was maintained")
    soft_cinematography: float = Field(9.0, ge=0.0, le=10.0)
    soft_aesthetic: float = Field(9.0, ge=0.0, le=10.0)
    soft_pacing: float = Field(9.0, ge=0.0, le=10.0)
    synthetic_defects: List[DefectAnnotation] = Field(default_factory=list)
    raw_frames_count: Optional[int] = Field(None, ge=1)

    @model_validator(mode="after")
    def validate_finite_scores(self) -> CandidateEvaluationInput:
        for field_name in (
            "generation_latency_sec",
            "estimated_cost_usd",
            "anatomical_score",
            "face_similarity_cosine",
            "lip_sync_offset_ms",
            "optical_flow_jitter",
            "min_observed_ssim",
            "observed_flicker_ratio",
            "soft_cinematography",
            "soft_aesthetic",
            "soft_pacing",
        ):
            val = getattr(self, field_name)
            if not math.isfinite(val):
                raise ValueError(f"{field_name} must be a finite number, got {val}")
        return self


class GateEvaluationResult(BaseModel):
    """Result for an individual quality gate."""
    model_config = ConfigDict(extra="forbid")

    gate: HardGateType
    status: GateStatus
    score: float
    threshold: float
    message: str
    defect_count: int = 0


class ScenarioEvaluationReport(BaseModel):
    """Comprehensive evaluation report for a candidate scenario execution."""
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    model_id: str
    candidate_id: str
    passed: bool
    hard_gates_passed: bool
    temporal_passed: bool
    gate_results: Dict[str, GateEvaluationResult]
    temporal_metrics: Dict[str, Any] = Field(default_factory=dict, description="Detailed temporal continuity diagnostics")
    soft_scores: Dict[str, float]
    aggregate_soft_score: float
    defects: List[DefectAnnotation]
    recommended_repairs: List[RepairStrategy]
    execution_timestamp: str
    summary: str
