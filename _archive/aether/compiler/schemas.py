"""Project Aether Compiler Schemas.

Defines Pydantic V2 schemas for complexity levels, shot requirements,
spatial representation packages, and compiled model payloads for Project Aether v2
(Pillar 3 & Pillar 4 / WBS 1.4).
"""

from __future__ import annotations

import json
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aether.state.schemas import SceneSnapshot

# Canonical alias for immutable frozen shot slice of world state (Pillar 2 / Pillar 3)
ShotSlice = SceneSnapshot


class ComplexityLevel(IntEnum):
    """Complexity classification levels (0 through 5) defined in Pillar 3.

    - Level 0 (PROMPT_ONLY): Pure text prompt for atmospheric cutaways, cloudscapes, abstract concepts.
    - Level 1 (REFERENCE_IMAGE): Single reference image for static portraits, establishing shots.
    - Level 2 (KEYFRAMES_INTERPOLATION): First/last keyframes for simple pans, straightforward character actions.
    - Level 3 (TWOD_TRAJECTORY_POSE): 2D pose/trajectory for talking heads, walking toward camera, gestural dialogue.
    - Level 4 (THREED_BLOCKING): 3D geometric blocking for multi-character staging, crane moves, hand-object handoffs.
    - Level 5 (FULL_PHYSICAL_SIMULATION): Deterministic physics simulation for complex collisions, fluids, stunts.
    """
    PROMPT_ONLY = 0
    REFERENCE_IMAGE = 1
    KEYFRAMES_INTERPOLATION = 2
    TWOD_TRAJECTORY_POSE = 3
    THREED_BLOCKING = 4
    FULL_PHYSICAL_SIMULATION = 5

    @property
    def label(self) -> str:
        """Human-readable level title."""
        labels = {
            0: "Level 0: Prompt-Only",
            1: "Level 1: Reference Image Conditioned",
            2: "Level 2: Keyframes Interpolation",
            3: "Level 3: 2D Trajectory & Pose",
            4: "Level 4: 3D Geometric Blocking",
            5: "Level 5: Full Physical Simulation",
        }
        return labels.get(self.value, f"Level {self.value}")

    @property
    def description(self) -> str:
        """Detailed architectural description of this complexity tier."""
        descriptions = {
            0: "Atmospheric cutaways, cloudscapes, vistas, and abstract concepts with no actor interaction.",
            1: "Static portraits and establishing frames anchored by photorealistic image conditioning.",
            2: "Straightforward camera pans, zooms, and simple actions bounded by start and end keyframes.",
            3: "Talking heads, walking towards camera, and gestural dialogue requiring pose and lip-sync alignment.",
            4: "Multi-character blocking, camera crane moves, and hand-object handoffs requiring 3D spatial previs.",
            5: "Complex physical collisions, fluid dynamics, grapples, and stunts requiring deterministic simulation.",
        }
        return descriptions.get(self.value, "")

    @classmethod
    def from_val(cls, val: Any) -> ComplexityLevel:
        """Convert int, float, string, or enum into a valid ComplexityLevel instance."""
        if isinstance(val, ComplexityLevel):
            return val
        if isinstance(val, (int, float)):
            int_val = int(val)
            if float(val) == float(int_val) and 0 <= int_val <= 5:
                return cls(int_val)
            raise ValueError(f"Numeric complexity level must be an integer between 0 and 5, got {val}")

        s = str(val).strip().upper()
        # Direct lookup by name
        if hasattr(cls, s):
            return getattr(cls, s)

        # Check float string e.g. '2.0'
        try:
            f_val = float(s)
            if f_val.is_integer() and 0 <= int(f_val) <= 5:
                return cls(int(f_val))
        except ValueError:
            pass

        # Check explicit semantic keywords FIRST before numeric parsing
        mapping = {
            "FULL_PHYSICAL_SIMULATION": cls.FULL_PHYSICAL_SIMULATION,
            "PHYSICAL_SIMULATION": cls.FULL_PHYSICAL_SIMULATION,
            "SIMULATION": cls.FULL_PHYSICAL_SIMULATION,
            "THREED_BLOCKING": cls.THREED_BLOCKING,
            "3D_BLOCKING": cls.THREED_BLOCKING,
            "3D": cls.THREED_BLOCKING,
            "BLOCKING": cls.THREED_BLOCKING,
            "TWOD_TRAJECTORY_POSE": cls.TWOD_TRAJECTORY_POSE,
            "2D_TRAJECTORY": cls.TWOD_TRAJECTORY_POSE,
            "2D_POSE": cls.TWOD_TRAJECTORY_POSE,
            "2D": cls.TWOD_TRAJECTORY_POSE,
            "POSE": cls.TWOD_TRAJECTORY_POSE,
            "TRAJECTORY": cls.TWOD_TRAJECTORY_POSE,
            "KEYFRAMES_INTERPOLATION": cls.KEYFRAMES_INTERPOLATION,
            "KEYFRAMES": cls.KEYFRAMES_INTERPOLATION,
            "INTERPOLATION": cls.KEYFRAMES_INTERPOLATION,
            "REFERENCE_IMAGE": cls.REFERENCE_IMAGE,
            "REF_CONDITIONED": cls.REFERENCE_IMAGE,
            "REFERENCE": cls.REFERENCE_IMAGE,
            "PROMPT_ONLY": cls.PROMPT_ONLY,
            "TEXT_ONLY": cls.PROMPT_ONLY,
            "PROMPT": cls.PROMPT_ONLY,
        }
        for k, v in mapping.items():
            if k in s:
                return v

        # Level pattern e.g. "LEVEL_0", "LEVEL 4", "L2", or just a digit "3"
        import re
        match = re.search(r'(?:LEVEL[_\s]*|L|^)(\d)(?:\.0)?$', s)
        if match:
            int_val = int(match.group(1))
            if 0 <= int_val <= 5:
                return cls(int_val)

        if len(s) <= 2 and s.isdigit():
            int_val = int(s)
            if 0 <= int_val <= 5:
                return cls(int_val)

        raise ValueError(f"Cannot parse '{val}' into a valid ComplexityLevel (must be 0-5)")


# Convenience aliases for ComplexityLevel
ComplexityLevel.LEVEL_0 = ComplexityLevel.PROMPT_ONLY
ComplexityLevel.LEVEL_1 = ComplexityLevel.REFERENCE_IMAGE
ComplexityLevel.LEVEL_2 = ComplexityLevel.KEYFRAMES_INTERPOLATION
ComplexityLevel.LEVEL_3 = ComplexityLevel.TWOD_TRAJECTORY_POSE
ComplexityLevel.LEVEL_4 = ComplexityLevel.THREED_BLOCKING
ComplexityLevel.LEVEL_5 = ComplexityLevel.FULL_PHYSICAL_SIMULATION
ComplexityLevel.LEVEL_0_TEXT_ONLY = ComplexityLevel.PROMPT_ONLY
ComplexityLevel.LEVEL_1_REF_CONDITIONED = ComplexityLevel.REFERENCE_IMAGE
ComplexityLevel.LEVEL_2_KEYFRAMES = ComplexityLevel.KEYFRAMES_INTERPOLATION
ComplexityLevel.LEVEL_3_2D_TRAJECTORY = ComplexityLevel.TWOD_TRAJECTORY_POSE
ComplexityLevel.LEVEL_4_3D_BLOCKING = ComplexityLevel.THREED_BLOCKING
ComplexityLevel.LEVEL_5_DETERMINISTIC_SIM = ComplexityLevel.FULL_PHYSICAL_SIMULATION


class ProviderTarget(str, Enum):
    """Supported generative video provider targets."""
    VEO_3_1 = "veo_3_1"
    KLING_3_0 = "kling_3_0"
    RUNWAY_GEN_4_5 = "runway_gen_4_5"
    COGVIDEOX_COMFYUI = "cogvideox_comfyui"

    @classmethod
    def from_val(cls, val: Any) -> ProviderTarget:
        """Parse provider target from string or enum."""
        if isinstance(val, ProviderTarget):
            return val
        s = str(val).lower().strip()
        for member in cls:
            if s == member.value or s == member.name.lower():
                return member
        # Fuzzy matches
        if "veo" in s:
            return cls.VEO_3_1
        if "kling" in s:
            return cls.KLING_3_0
        if "runway" in s or "gen-4" in s or "gen4" in s:
            return cls.RUNWAY_GEN_4_5
        if "cogvideo" in s or "comfy" in s or "hunyuan" in s:
            return cls.COGVIDEOX_COMFYUI
        raise ValueError(f"Unknown video provider target: '{val}'")


class ComputeTier(str, Enum):
    """Compute tier classification for rendering and compilation workflows."""
    STANDARD = "standard"
    PREMIUM = "premium"
    CLOUD_SERVERLESS = "cloud_serverless"
    DEDICATED_A100 = "dedicated_a100"
    DEDICATED_H100 = "dedicated_h100"

    @classmethod
    def from_val(cls, val: Any) -> ComputeTier:
        """Parse ComputeTier from string or enum."""
        if isinstance(val, ComputeTier):
            return val
        s = str(val).lower().strip()
        for member in cls:
            if s == member.value or s == member.name.lower():
                return member
        if "h100" in s:
            return cls.DEDICATED_H100
        if "a100" in s:
            return cls.DEDICATED_A100
        if "serverless" in s or "cloud" in s:
            return cls.CLOUD_SERVERLESS
        if "premium" in s:
            return cls.PREMIUM
        if "standard" in s:
            return cls.STANDARD
        raise ValueError(f"Unknown compute tier: '{val}'")


class AudioRequirement(BaseModel):
    """Audio specification for shot compilation."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    dialogue: bool = Field(False, description="Whether shot requires synchronous character dialogue")
    dialogue_transcript: Optional[str] = Field(None, description="Spoken dialogue line or phonetic text")
    dialogue_audio_uri: Optional[str] = Field(None, description="Pre-rendered speech audio file URI")
    foley: bool = Field(False, description="Whether shot requires specific synchronized foley effects")
    foley_cues: List[str] = Field(default_factory=list, description="Descriptive foley sound events e.g. ['footsteps', 'gunshot']")
    score: bool = Field(False, description="Whether musical score accompaniment is required")
    score_mood: Optional[str] = Field(None, description="Musical atmosphere descriptor e.g. 'tense orchestral drone'")
    native_audio_requested: bool = Field(False, description="Whether to request native model audio synthesis (e.g. Veo 3.1)")

    @model_validator(mode="before")
    @classmethod
    def _normalize_audio_fields(cls, data: Any) -> Any:
        if isinstance(data, bool):
            return {"native_audio_requested": data}
        if isinstance(data, str):
            return {"score": True, "score_mood": data}
        if data is None:
            return {}
        if isinstance(data, dict):
            d = dict(data)
            if "has_dialogue" in d and "dialogue" not in d:
                d["dialogue"] = bool(d["has_dialogue"])
            if "transcript" in d and "dialogue_transcript" not in d:
                d["dialogue_transcript"] = str(d["transcript"])
            if "audio_uri" in d and "dialogue_audio_uri" not in d:
                d["dialogue_audio_uri"] = str(d["audio_uri"])
            if "has_foley" in d and "foley" not in d:
                d["foley"] = bool(d["has_foley"])
            if "has_score" in d and "score" not in d:
                d["score"] = bool(d["has_score"])
            if "score_genre" in d and "score_mood" not in d:
                d["score_mood"] = str(d["score_genre"])
            if d.get("dialogue_transcript") and "dialogue" not in d:
                d["dialogue"] = True
            return d
        return data


class ShotRequirement(BaseModel):
    """Comprehensive requirement specification for compiling an individual cinematic shot."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    shot_id: str = Field("SHOT_001", description="Unique shot identifier e.g. 'SHOT_001'")
    target_duration: float = Field(5.0, gt=0.0, description="Target duration in seconds")
    aspect_ratio: str = Field("16:9", description="Target aspect ratio e.g. '16:9', '9:16', '2.39:1'")
    resolution: str = Field("1080p", description="Target render resolution e.g. '720p', '1080p', '4k'")
    audio: AudioRequirement = Field(default_factory=AudioRequirement, description="Dialogue, foley, and score requirements")
    character_ids_involved: List[str] = Field(default_factory=list, description="IDs of characters actively featured")
    prop_interaction_flags: Dict[str, bool] = Field(default_factory=dict, description="Flags for prop interaction e.g. {'has_handoff': True}")
    emotional_beat: Optional[str] = Field(None, description="Narrative emotional beat e.g. 'tense standoff', 'sorrowful realization'")
    target_focal_intent: Optional[str] = Field(None, description="Cinematic focal intent e.g. 'shallow depth of field on Maya's eyes'")
    camera_movement: Optional[str] = Field(None, description="Camera kinematic motion e.g. 'pan_right', 'crane_up', 'dolly_in'")
    camera_velocity_mps: float = Field(0.0, ge=0.0, description="Estimated camera velocity in meters per second")
    physical_challenges: List[str] = Field(default_factory=list, description="Physical phenomena present: ['fluids', 'collisions', 'grapple']")
    continuity_critical: bool = Field(False, description="Whether strict temporal continuity across cuts must be enforced")
    first_frame_uri: Optional[str] = Field(None, description="Starting keyframe URI for image-to-video / interpolation")
    last_frame_uri: Optional[str] = Field(None, description="Ending keyframe URI for bidirectional interpolation")
    enable_teacache: bool = Field(True, description="Enable Timestep Embedding Aware Cache DiT acceleration")
    enable_pab: bool = Field(True, description="Enable Pyramid Attention Broadcast DiT layer acceleration")
    sampling_steps: int = Field(8, ge=1, description="Few-step distilled flow sampling steps (default 8)")
    enable_speculative_draft: bool = Field(False, description="Enable 480p low-latency speculative draft gating")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom parameters, provider overrides, or director notes")

    @model_validator(mode="before")
    @classmethod
    def _normalize_shot_requirement(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            # Cost & efficiency flags aliases
            if "teacache" in d and "enable_teacache" not in d:
                d["enable_teacache"] = bool(d["teacache"])
            if "pab" in d and "enable_pab" not in d:
                d["enable_pab"] = bool(d["pab"])
            if "steps" in d and "sampling_steps" not in d:
                d["sampling_steps"] = int(d["steps"])
            elif "num_steps" in d and "sampling_steps" not in d:
                d["sampling_steps"] = int(d["num_steps"])
            if "speculative" in d and "enable_speculative_draft" not in d:
                d["enable_speculative_draft"] = bool(d["speculative"])
            elif "speculative_draft" in d and "enable_speculative_draft" not in d:
                d["enable_speculative_draft"] = bool(d["speculative_draft"])

            # Duration aliases
            if "duration" in d and "target_duration" not in d:
                d["target_duration"] = float(d["duration"])
            if "duration_seconds" in d and "target_duration" not in d:
                d["target_duration"] = float(d["duration_seconds"])

            # Character list aliases
            for ck in ("characters", "character_ids", "characters_involved", "actors"):
                if ck in d and "character_ids_involved" not in d:
                    chars = d[ck]
                    if isinstance(chars, str):
                        chars = [chars]
                    d["character_ids_involved"] = list(chars)
                    break

            # Focal intent alias
            for fk in ("focal_intent", "focal_point", "focus_intent"):
                if fk in d and "target_focal_intent" not in d:
                    d["target_focal_intent"] = d[fk]
                    break

            # First and last frame aliases
            if "first_frame" in d and "first_frame_uri" not in d:
                d["first_frame_uri"] = str(d["first_frame"])
            if "last_frame" in d and "last_frame_uri" not in d:
                d["last_frame_uri"] = str(d["last_frame"])

            # Prop interaction flags alias
            if "prop_interaction" in d:
                pi = d["prop_interaction"]
                if isinstance(pi, bool):
                    d.setdefault("prop_interaction_flags", {})["active"] = pi
                elif isinstance(pi, dict):
                    d["prop_interaction_flags"] = pi
            if "has_handoff" in d:
                d.setdefault("prop_interaction_flags", {})["has_handoff"] = bool(d["has_handoff"])

            # Audio requirements normalization
            if "audio_requirements" in d and "audio" not in d:
                d["audio"] = d["audio_requirements"]
            if "audio" in d:
                if isinstance(d["audio"], bool):
                    d["audio"] = AudioRequirement(native_audio_requested=d["audio"])
                elif isinstance(d["audio"], str):
                    d["audio"] = AudioRequirement(score=True, score_mood=d["audio"])
                elif isinstance(d["audio"], dict):
                    d["audio"] = AudioRequirement(**d["audio"])
                elif d["audio"] is None:
                    d["audio"] = AudioRequirement()
            elif "audio" not in d:
                # Infer from root fields if passed directly
                audio_kwargs = {}
                if "dialogue" in d:
                    audio_kwargs["dialogue"] = bool(d["dialogue"])
                elif "has_dialogue" in d:
                    audio_kwargs["dialogue"] = bool(d["has_dialogue"])
                if "dialogue_transcript" in d:
                    audio_kwargs["dialogue_transcript"] = d["dialogue_transcript"]
                elif "transcript" in d:
                    audio_kwargs["dialogue_transcript"] = d["transcript"]
                if "dialogue_audio_uri" in d:
                    audio_kwargs["dialogue_audio_uri"] = d["dialogue_audio_uri"]
                elif "audio_uri" in d:
                    audio_kwargs["dialogue_audio_uri"] = d["audio_uri"]
                if "foley" in d:
                    audio_kwargs["foley"] = bool(d["foley"])
                elif "has_foley" in d:
                    audio_kwargs["foley"] = bool(d["has_foley"])
                if "score" in d:
                    audio_kwargs["score"] = bool(d["score"])
                elif "has_score" in d:
                    audio_kwargs["score"] = bool(d["has_score"])
                if audio_kwargs:
                    d["audio"] = AudioRequirement(**audio_kwargs)

            return d
        return data

    @property
    def duration(self) -> float:
        """Alias for target_duration."""
        return self.target_duration

    @property
    def characters_involved(self) -> List[str]:
        """Alias for character_ids_involved."""
        return self.character_ids_involved

    @property
    def characters(self) -> List[str]:
        """Alias for character_ids_involved."""
        return self.character_ids_involved

    @property
    def character_ids(self) -> List[str]:
        """Alias for character_ids_involved."""
        return self.character_ids_involved

    @property
    def focal_intent(self) -> Optional[str]:
        """Alias for target_focal_intent."""
        return self.target_focal_intent

    @property
    def prop_interaction(self) -> Dict[str, bool]:
        """Alias for prop_interaction_flags."""
        return self.prop_interaction_flags

    @property
    def audio_requirements(self) -> AudioRequirement:
        """Alias for audio."""
        return self.audio

    @property
    def first_frame(self) -> Optional[str]:
        """Alias for first_frame_uri."""
        return self.first_frame_uri

    @property
    def last_frame(self) -> Optional[str]:
        """Alias for last_frame_uri."""
        return self.last_frame_uri

    @property
    def has_prop_handoff(self) -> bool:
        """True if any prop handoff or transfer flag is enabled."""
        return bool(
            self.prop_interaction_flags.get("has_handoff")
            or self.prop_interaction_flags.get("handoff")
            or self.prop_interaction_flags.get("transfer")
            or self.prop_interaction_flags.get("pickup")
            or self.prop_interaction_flags.get("drop")
            or self.prop_interaction_flags.get("interaction")
            or self.prop_interaction_flags.get("active")
        )

    @property
    def has_dialogue(self) -> bool:
        """True if dialogue delivery is required."""
        return bool(self.audio.dialogue or self.audio.dialogue_transcript)


class SpatialRepresentationPackage(BaseModel):
    """Collection of deterministic spatial and geometric rendering passes.

    Produced by Headless 3D engines (Unreal Engine 5 / Blender) to guide
    generative video models via ControlNet, keyframe interpolation, or motion vectors.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    clay_render_uri: Optional[str] = Field(None, description="URI to low-poly RGB clay render pass")
    photoreal_ref_uri: Optional[str] = Field(None, description="URI to high-fidelity reference render or keyframe")
    first_frame_uri: Optional[str] = Field(None, description="Starting keyframe render URI")
    last_frame_uri: Optional[str] = Field(None, description="Ending keyframe render URI")
    depth_map_uri: Optional[str] = Field(None, description="URI to normalized 16-bit depth map pass")
    surface_normals_uri: Optional[str] = Field(None, description="URI to world-space surface normals pass")
    segmentation_masks: Dict[str, str] = Field(default_factory=dict, description="Mapping of actor/prop IDs to mask URIs")
    motion_vectors_uri: Optional[str] = Field(None, description="URI to optical flow / motion vector tensor pass")
    camera_trajectory_path: Optional[str] = Field(None, description="URI or path to 3D camera trajectory curve (FBX/JSON)")
    skeleton_pose_metadata: Dict[str, Any] = Field(default_factory=dict, description="2D/3D skeleton rig joint keypoints")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Pass render metadata, bounding boxes, or camera matrices")

    @model_validator(mode="before")
    @classmethod
    def _normalize_spatial_package(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            # Pass aliases
            if "clay_render" in d and "clay_render_uri" not in d:
                d["clay_render_uri"] = d["clay_render"]
            if "photoreal_ref" in d and "photoreal_ref_uri" not in d:
                d["photoreal_ref_uri"] = d["photoreal_ref"]
            if "first_frame" in d and "first_frame_uri" not in d:
                d["first_frame_uri"] = d["first_frame"]
            if "last_frame" in d and "last_frame_uri" not in d:
                d["last_frame_uri"] = d["last_frame"]
            if "depth_map" in d and "depth_map_uri" not in d:
                d["depth_map_uri"] = d["depth_map"]
            if "surface_normals" in d and "surface_normals_uri" not in d:
                d["surface_normals_uri"] = d["surface_normals"]
            if "motion_vectors" in d and "motion_vectors_uri" not in d:
                d["motion_vectors_uri"] = d["motion_vectors"]
            if "optical_flow" in d and "motion_vectors_uri" not in d:
                d["motion_vectors_uri"] = d["optical_flow"]
            if "optical_flow_uri" in d and "motion_vectors_uri" not in d:
                d["motion_vectors_uri"] = d["optical_flow_uri"]
            if "camera_trajectory" in d and "camera_trajectory_path" not in d:
                d["camera_trajectory_path"] = d["camera_trajectory"]
            if "skeleton_poses" in d and "skeleton_pose_metadata" not in d:
                d["skeleton_pose_metadata"] = d["skeleton_poses"]
            # Masks alias if passed as list
            if "segmentation_masks" in d and isinstance(d["segmentation_masks"], list):
                d["segmentation_masks"] = {f"mask_{i}": uri for i, uri in enumerate(d["segmentation_masks"])}
            return d
        return data

    @property
    def optical_flow_uri(self) -> Optional[str]:
        """Alias for motion_vectors_uri."""
        return self.motion_vectors_uri

    @property
    def optical_flow(self) -> Optional[str]:
        """Alias for motion_vectors_uri."""
        return self.motion_vectors_uri

    @property
    def motion_vectors(self) -> Optional[str]:
        """Alias for motion_vectors_uri."""
        return self.motion_vectors_uri

    @property
    def clay_render(self) -> Optional[str]:
        """Alias for clay_render_uri."""
        return self.clay_render_uri

    @property
    def photoreal_ref(self) -> Optional[str]:
        """Alias for photoreal_ref_uri."""
        return self.photoreal_ref_uri

    @property
    def first_frame(self) -> Optional[str]:
        """Alias for first_frame_uri."""
        return self.first_frame_uri

    @property
    def last_frame(self) -> Optional[str]:
        """Alias for last_frame_uri."""
        return self.last_frame_uri

    @property
    def depth_map(self) -> Optional[str]:
        """Alias for depth_map_uri."""
        return self.depth_map_uri

    @property
    def surface_normals(self) -> Optional[str]:
        """Alias for surface_normals_uri."""
        return self.surface_normals_uri

    @property
    def camera_trajectory(self) -> Optional[str]:
        """Alias for camera_trajectory_path."""
        return self.camera_trajectory_path

    @property
    def skeleton_poses(self) -> Dict[str, Any]:
        """Alias for skeleton_pose_metadata."""
        return self.skeleton_pose_metadata

    @property
    def has_clay_render(self) -> bool:
        """True if clay render pass is available."""
        return bool(self.clay_render_uri)

    @property
    def has_photoreal_ref(self) -> bool:
        """True if photoreal reference image is available."""
        return bool(self.photoreal_ref_uri)

    @property
    def has_first_frame(self) -> bool:
        """True if first frame is available."""
        return bool(self.first_frame_uri)

    @property
    def has_last_frame(self) -> bool:
        """True if last frame is available."""
        return bool(self.last_frame_uri)

    @property
    def has_depth(self) -> bool:
        """True if depth map pass is available."""
        return bool(self.depth_map_uri)

    @property
    def has_normals(self) -> bool:
        """True if surface normals pass is available."""
        return bool(self.surface_normals_uri)

    @property
    def has_motion_vectors(self) -> bool:
        """True if motion vectors or optical flow are available."""
        return bool(self.motion_vectors_uri)

    @property
    def has_camera_trajectory(self) -> bool:
        """True if 3D camera trajectory path is populated."""
        return bool(self.camera_trajectory_path)

    @property
    def has_skeleton_poses(self) -> bool:
        """True if skeleton pose keypoints are populated."""
        return bool(self.skeleton_pose_metadata)

    @property
    def has_segmentation_masks(self) -> bool:
        """True if any actor/prop segmentation masks exist."""
        return bool(self.segmentation_masks)

    @property
    def is_empty(self) -> bool:
        """True if no spatial passes are populated."""
        return not (
            self.clay_render_uri
            or self.photoreal_ref_uri
            or self.first_frame_uri
            or self.last_frame_uri
            or self.depth_map_uri
            or self.surface_normals_uri
            or self.segmentation_masks
            or self.motion_vectors_uri
            or self.camera_trajectory_path
            or self.skeleton_pose_metadata
        )


class ComplexityPlan(BaseModel):
    """Structured rationale and representation package recommendations from ComplexityPlanner."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    shot_id: str = Field("SHOT_001", description="Shot identifier evaluated")
    complexity_level: ComplexityLevel = Field(..., description="Minimum necessary complexity classification (0 to 5)")
    rationale: List[str] = Field(default_factory=list, description="Granular analytical reasons triggering this classification")
    recommended_representations: List[str] = Field(default_factory=list, description="Spatial representation package passes advised")
    recommended_provider: ProviderTarget = Field(..., description="Default optimal generative video provider target")
    factors_detected: Dict[str, Any] = Field(default_factory=dict, description="Metrics evaluated (actor count, velocity, physics)")

    @property
    def rationale_summary(self) -> str:
        """Condensed single-string explanation of the complexity determination."""
        return " | ".join(self.rationale)


class CompiledModelPayload(BaseModel):
    """Fully translated, provider-ready generation payload.

    Ingested by downstream model client wrappers (Google Veo, Kling, Runway, ComfyUI).
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    shot_id: str = Field("SHOT_001", description="Shot identifier for tracking")
    provider_target: ProviderTarget = Field(..., description="Target model API family")
    prompt: str = Field(..., description="Compiled positive cinematic prompt incorporating scene parameters")
    negative_prompt: Optional[str] = Field(None, description="Compiled negative prompt to suppress artifacts")
    reference_images: List[str] = Field(default_factory=list, description="All relevant reference image URIs")
    first_frame_uri: Optional[str] = Field(None, description="Starting keyframe URI for image-to-video / interpolation")
    last_frame_uri: Optional[str] = Field(None, description="Ending keyframe URI for bidirectional interpolation")
    camera_motion_parameters: Dict[str, Any] = Field(default_factory=dict, description="Kinematic camera trajectory parameters")
    provider_config: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific API payload parameters")
    required_compute_tier: ComputeTier = Field(ComputeTier.STANDARD, description="Estimated hardware execution tier")
    duration_seconds: float = Field(5.0, description="Shot duration in seconds")
    aspect_ratio: str = Field("16:9", description="Video aspect ratio")
    resolution: str = Field("1080p", description="Video resolution")
    complexity_level: Optional[ComplexityLevel] = Field(None, description="Assigned complexity level")
    enable_teacache: bool = Field(True, description="Enable Timestep Embedding Aware Cache DiT acceleration")
    enable_pab: bool = Field(True, description="Enable Pyramid Attention Broadcast DiT layer acceleration")
    sampling_steps: int = Field(8, ge=1, description="Few-step distilled flow sampling steps (default 8)")
    enable_speculative_draft: bool = Field(False, description="Enable 480p low-latency speculative draft gating")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Compiler debug logs and metadata")

    @model_validator(mode="before")
    @classmethod
    def _normalize_compiled_payload(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            if "teacache" in d and "enable_teacache" not in d:
                d["enable_teacache"] = bool(d["teacache"])
            if "pab" in d and "enable_pab" not in d:
                d["enable_pab"] = bool(d["pab"])
            if "steps" in d and "sampling_steps" not in d:
                d["sampling_steps"] = int(d["steps"])
            if "speculative" in d and "enable_speculative_draft" not in d:
                d["enable_speculative_draft"] = bool(d["speculative"])
            elif "speculative_draft" in d and "enable_speculative_draft" not in d:
                d["enable_speculative_draft"] = bool(d["speculative_draft"])
            if "positive_prompt" in d and "prompt" not in d:
                d["prompt"] = d["positive_prompt"]
            if "provider" in d and "provider_target" not in d:
                d["provider_target"] = ProviderTarget.from_val(d["provider"])
            elif "provider_target" in d and not isinstance(d["provider_target"], ProviderTarget):
                d["provider_target"] = ProviderTarget.from_val(d["provider_target"])
            if "camera_motion" in d and "camera_motion_parameters" not in d:
                d["camera_motion_parameters"] = d["camera_motion"]
            if "compute_tier" in d and "required_compute_tier" not in d:
                d["required_compute_tier"] = ComputeTier.from_val(d["compute_tier"])
            elif "required_compute_tier" in d and not isinstance(d["required_compute_tier"], ComputeTier):
                d["required_compute_tier"] = ComputeTier.from_val(d["required_compute_tier"])
            if "duration" in d and "duration_seconds" not in d:
                d["duration_seconds"] = float(d["duration"])
            if "first_frame" in d and "first_frame_uri" not in d:
                d["first_frame_uri"] = d["first_frame"]
            if "last_frame" in d and "last_frame_uri" not in d:
                d["last_frame_uri"] = d["last_frame"]
            if "complexity_level" in d and d["complexity_level"] is not None and not isinstance(d["complexity_level"], ComplexityLevel):
                d["complexity_level"] = ComplexityLevel.from_val(d["complexity_level"])
            return d
        return data

    @property
    def positive_prompt(self) -> str:
        """Alias for prompt."""
        return self.prompt

    @property
    def camera_motion(self) -> Dict[str, Any]:
        """Alias for camera_motion_parameters."""
        return self.camera_motion_parameters

    @property
    def compute_tier(self) -> ComputeTier:
        """Alias for required_compute_tier."""
        return self.required_compute_tier

    @property
    def provider(self) -> ProviderTarget:
        """Alias for provider_target."""
        return self.provider_target

    @property
    def first_frame(self) -> Optional[str]:
        """Alias for first_frame_uri."""
        return self.first_frame_uri

    @property
    def last_frame(self) -> Optional[str]:
        """Alias for last_frame_uri."""
        return self.last_frame_uri

    def to_api_payload(self) -> Dict[str, Any]:
        """Convert the compiled payload into a direct dictionary format for provider clients."""
        return {
            "shot_id": self.shot_id,
            "provider": self.provider_target.value,
            "prompt": self.prompt,
            "positive_prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "first_frame": self.first_frame_uri,
            "last_frame": self.last_frame_uri,
            "reference_images": self.reference_images,
            "duration": self.duration_seconds,
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "camera_motion": self.camera_motion_parameters,
            "provider_config": self.provider_config,
            "compute_tier": self.required_compute_tier.value,
            "complexity_level": self.complexity_level.value if self.complexity_level is not None else None,
            "enable_teacache": self.enable_teacache,
            "enable_pab": self.enable_pab,
            "sampling_steps": self.sampling_steps,
            "enable_speculative_draft": self.enable_speculative_draft,
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize payload to formatted JSON."""
        return json.dumps(self.to_api_payload(), indent=indent)
