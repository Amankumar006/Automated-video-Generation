"""Aether World Model Schemas.

Defines Pydantic V2 schemas for persistent cinematic scene states, character rosters,
prop tracking, camera kinematics, environment parameters, scene actions, state deltas,
and frozen shot snapshots for Project Aether v2 (Pillar 2 / WBS 1.3).
"""

from __future__ import annotations

import math
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class HandAttachment(str, Enum):
    """Hand attachment slot for props held by characters."""
    LEFT = "left"
    RIGHT = "right"
    NONE = "none"
    BOTH = "both"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, val: Any) -> HandAttachment:
        if isinstance(val, HandAttachment):
            return val
        s = val.value if hasattr(val, "value") else str(val)
        if "." in s:
            s = s.split(".")[-1]
        s = s.lower().strip()
        return cls(s)


class PhysicalState(str, Enum):
    """Common physical states of props and surfaces."""
    PRISTINE = "pristine"
    WET = "wet"
    BROKEN = "broken"
    DAMAGED = "damaged"
    EMPTY = "empty"
    BURNING = "burning"
    DIRTY = "dirty"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, val: Any) -> PhysicalState:
        if isinstance(val, PhysicalState):
            return val
        s = val.value if hasattr(val, "value") else str(val)
        if "." in s:
            s = s.split(".")[-1]
        s = s.lower().strip()
        return cls(s)


class ActionType(str, Enum):
    """Supported scene action types for deterministic state mutation."""
    PROP_TRANSFER = "PROP_TRANSFER"
    PROP_MUTATION = "PROP_MUTATION"
    PROP_SPAWNED = "PROP_SPAWNED"
    PROP_CONSUMED = "PROP_CONSUMED"
    PROP_DESTROYED = "PROP_DESTROYED"
    WARDROBE_MUTATION = "WARDROBE_MUTATION"
    WARDROBE_REPAIR = "WARDROBE_REPAIR"
    WARDROBE_CHANGE = "WARDROBE_CHANGE"
    CHARACTER_MOVE = "CHARACTER_MOVE"
    ENVIRONMENT_CHANGE = "ENVIRONMENT_CHANGE"
    INJURY_MUTATION = "INJURY_MUTATION"
    INJURY_ADDED = "INJURY_ADDED"
    HEALING = "HEALING"
    MEDICAL_TREATMENT = "MEDICAL_TREATMENT"
    EMOTION_CHANGE = "EMOTION_CHANGE"
    CAMERA_MOVE = "CAMERA_MOVE"
    CUSTOM = "CUSTOM"

    def __str__(self) -> str:
        return self.value


class WardrobeItemState(BaseModel):
    """Specific wardrobe garment tracking persistent physical and damage states."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str = Field("garment", description="Unique wardrobe garment identifier e.g. 'leather_004'")
    name: Optional[str] = Field(None, description="Descriptive garment name")
    type: Optional[str] = Field(None, description="Garment type e.g. 'jacket', 'trousers', 'boots'")
    state: str = Field("pristine", description="Persistent physical damage state e.g. 'left_sleeve_torn'")
    color: Optional[str] = Field(None, description="Garment color e.g. '#2b2b2b' or 'black'")
    damage_level: float = Field(0.0, ge=0.0, le=1.0, description="Normalized damage metric [0.0 = pristine, 1.0 = destroyed]")


class CharacterState(BaseModel):
    """Persistent cinematic state for a character within a scene."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    character_id: str = Field(..., description="Unique character identifier e.g. 'maya'")
    name: Optional[str] = Field(None, description="Display name e.g. 'Maya Lin'")
    position: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0], description="3D coordinates [x, y, z] in meters")
    facing_angle: float = Field(0.0, ge=0.0, le=360.0, description="Rotation angle in degrees [0.0, 360.0]")
    eyeline_vector: List[float] = Field(default_factory=lambda: [0.0, 0.0, 1.0], description="3D eyeline unit vector [dx, dy, dz]")
    emotional_state: str = Field("neutral", description="Emotional affect / micro-expression e.g. 'hyper-vigilant'")
    wardrobe: Dict[str, WardrobeItemState] = Field(default_factory=dict, description="Wardrobe mapping by slot e.g. 'jacket'")
    injuries: List[str] = Field(default_factory=list, description="List of physical wounds e.g. ['blood_cheek_right']")
    held_props: Dict[str, str] = Field(default_factory=dict, description="Props held by hand slot e.g. {'right': 'spectrometer_01'}")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary custom character metadata")

    @model_validator(mode="before")
    @classmethod
    def _normalize_character_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            if "id" in d and "character_id" not in d:
                d["character_id"] = d["id"]
            if "emotion" in d and "emotional_state" not in d:
                d["emotional_state"] = d["emotion"]
            if "micro_expression" in d and "emotional_state" not in d:
                d["emotional_state"] = d["micro_expression"]
            if "physical_injuries" in d and "injuries" not in d:
                d["injuries"] = d["physical_injuries"]
            elif "marks" in d and "injuries" not in d:
                d["injuries"] = d["marks"]
            if "wardrobe" in d and isinstance(d["wardrobe"], dict):
                normalized_wardrobe = {}
                for slot, val in d["wardrobe"].items():
                    if isinstance(val, WardrobeItemState):
                        normalized_wardrobe[slot] = val
                    elif isinstance(val, dict):
                        w_dict = dict(val)
                        if "id" not in w_dict:
                            w_dict["id"] = slot
                        normalized_wardrobe[slot] = WardrobeItemState(**w_dict)
                    elif isinstance(val, str):
                        normalized_wardrobe[slot] = WardrobeItemState(id=slot, state=val)
                    else:
                        normalized_wardrobe[slot] = val
                d["wardrobe"] = normalized_wardrobe
            return d
        return data

    @field_validator("position")
    @classmethod
    def _validate_position(cls, v: List[float]) -> List[float]:
        if len(v) != 3:
            raise ValueError(f"position must be a 3-element [x, y, z] list, got {len(v)}")
        if not all(math.isfinite(c) for c in v):
            raise ValueError("position coordinates must be finite real numbers")
        return [float(c) for c in v]

    @field_validator("eyeline_vector")
    @classmethod
    def _validate_eyeline(cls, v: List[float]) -> List[float]:
        if len(v) != 3:
            raise ValueError(f"eyeline_vector must be a 3-element [dx, dy, dz] list, got {len(v)}")
        if not all(math.isfinite(c) for c in v):
            raise ValueError("eyeline_vector components must be finite real numbers")
        mag = math.sqrt(sum(c * c for c in v))
        if mag == 0.0:
            raise ValueError("eyeline_vector cannot be a zero vector")
        return [float(c) for c in v]

    @property
    def id(self) -> str:
        """Alias for character_id."""
        return self.character_id

    @property
    def micro_expression(self) -> str:
        """Alias for emotional_state."""
        return self.emotional_state

    @property
    def physical_injuries(self) -> List[str]:
        """Alias for injuries."""
        return self.injuries

    @property
    def marks(self) -> List[str]:
        """Alias for injuries."""
        return self.injuries

    def normalized_eyeline(self) -> List[float]:
        """Returns unit-length normalized eyeline vector."""
        mag = math.sqrt(sum(c * c for c in self.eyeline_vector))
        return [c / mag for c in self.eyeline_vector]

    def distance_to(self, other: Union[List[float], CharacterState]) -> float:
        """Calculates Euclidean distance to target position or character."""
        other_pos = other.position if isinstance(other, CharacterState) else other
        return math.sqrt(
            (self.position[0] - other_pos[0]) ** 2
            + (self.position[1] - other_pos[1]) ** 2
            + (self.position[2] - other_pos[2]) ** 2
        )


class PropState(BaseModel):
    """Persistent state of a physical object or prop in the scene."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    prop_id: str = Field(..., description="Unique prop identifier e.g. 'spectrometer_device_01'")
    name: str = Field(..., description="Display name e.g. 'Spectrometer Device'")
    world_coordinates: Optional[List[float]] = Field(None, description="3D world position [x, y, z] when not held")
    owner_id: Optional[str] = Field(None, description="Character ID currently holding or owning this prop")
    hand_attachment: HandAttachment = Field(HandAttachment.NONE, description="Hand slot attachment: left, right, none, both")
    physical_state: str = Field("pristine", description="Physical condition e.g. 'wet', 'broken', 'pristine', 'empty'")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional custom prop parameters")

    @model_validator(mode="before")
    @classmethod
    def _normalize_prop_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            if "id" in d and "prop_id" not in d:
                d["prop_id"] = d["id"]
            for hk in ("holder_id", "holder_character_id", "owner_character_id", "character_id"):
                if hk in d and "owner_id" not in d:
                    d["owner_id"] = d[hk]
                    break
            if "position" in d and "world_coordinates" not in d:
                d["world_coordinates"] = d["position"]
            if "world_position" in d and "world_coordinates" not in d:
                d["world_coordinates"] = d["world_position"]
            if "hand" in d and "hand_attachment" not in d:
                d["hand_attachment"] = d["hand"]
            if isinstance(d.get("hand_attachment"), str):
                d["hand_attachment"] = d["hand_attachment"].lower()
            return d
        return data

    @field_validator("world_coordinates")
    @classmethod
    def _validate_world_coordinates(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        if v is not None:
            if len(v) != 3:
                raise ValueError(f"world_coordinates must be a 3-element [x, y, z] list, got {len(v)}")
            if not all(math.isfinite(c) for c in v):
                raise ValueError("world_coordinates components must be finite real numbers")
            return [float(c) for c in v]
        return v

    @property
    def id(self) -> str:
        """Alias for prop_id."""
        return self.prop_id

    @property
    def holder_id(self) -> Optional[str]:
        """Alias for owner_id."""
        return self.owner_id

    @property
    def owner_character_id(self) -> Optional[str]:
        """Alias for owner_id."""
        return self.owner_id

    @property
    def holder_character_id(self) -> Optional[str]:
        """Alias for owner_id."""
        return self.owner_id

    @property
    def world_position(self) -> Optional[List[float]]:
        """Alias for world_coordinates."""
        return self.world_coordinates

    @property
    def position(self) -> Optional[List[float]]:
        """Alias for world_coordinates."""
        return self.world_coordinates

    @property
    def is_held(self) -> bool:
        """True if currently held by a character."""
        return bool(self.owner_id is not None and self.hand_attachment != HandAttachment.NONE)


class CameraState(BaseModel):
    """Cinematic camera sensor, lens optics, and spatial positioning."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    lens_focal_length_mm: float = Field(35.0, gt=0.0, description="Focal length in millimeters (e.g. 24, 35, 50, 85)")
    aperture: float = Field(2.8, gt=0.0, description="Lens aperture f-stop value e.g. 1.8, 2.8, 4.0")
    position: List[float] = Field(default_factory=lambda: [0.0, 1.5, -3.0], description="3D camera location [x, y, z]")
    focus_distance: float = Field(3.0, gt=0.0, description="Subject focus plane distance in meters")
    previous_eyeline_vector: Optional[List[float]] = Field(None, description="Previous frame camera eyeline vector")
    eyeline_vector: Optional[List[float]] = Field(None, description="Current camera optical orientation vector")
    previous_lens_mm: Optional[float] = Field(None, description="Previous frame lens focal length in mm")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Camera rigs, stabilization, sensor info")

    @model_validator(mode="before")
    @classmethod
    def _normalize_camera_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            if "previous_lens_mm" in d and d["previous_lens_mm"] is not None:
                d["previous_lens_mm"] = float(d["previous_lens_mm"])
            for k in ("focal_length_mm", "focal_length", "lens_mm"):
                if k in d and "lens_focal_length_mm" not in d:
                    d["lens_focal_length_mm"] = float(d[k])
                    break
            if "lens_focal_length_mm" not in d and "previous_lens_mm" in d and d.get("previous_lens_mm") is not None:
                d["lens_focal_length_mm"] = float(d["previous_lens_mm"])
            return d
        return data

    @field_validator("position")
    @classmethod
    def _validate_position(cls, v: List[float]) -> List[float]:
        if len(v) != 3:
            raise ValueError(f"position must be a 3-element [x, y, z] list, got {len(v)}")
        if not all(math.isfinite(c) for c in v):
            raise ValueError("position coordinates must be finite real numbers")
        return [float(c) for c in v]

    @field_validator("previous_eyeline_vector", "eyeline_vector")
    @classmethod
    def _validate_eyeline(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        if v is not None:
            if len(v) != 3:
                raise ValueError(f"eyeline vector must be a 3-element list, got {len(v)}")
            if not all(math.isfinite(c) for c in v):
                raise ValueError("eyeline vector components must be finite real numbers")
            mag = math.sqrt(sum(c * c for c in v))
            if mag == 0.0:
                raise ValueError("eyeline vector cannot be zero vector")
            return [float(c) for c in v]
        return v

    @property
    def focal_length_mm(self) -> float:
        """Alias for lens_focal_length_mm."""
        return self.lens_focal_length_mm

    @property
    def focal_length(self) -> float:
        """Alias for lens_focal_length_mm."""
        return self.lens_focal_length_mm

    @property
    def lens_mm(self) -> float:
        """Alias for lens_focal_length_mm."""
        return self.lens_focal_length_mm


class EnvironmentState(BaseModel):
    """Environmental atmospheric parameters, lighting vectors, and surface moisture."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    weather: str = Field("clear", description="Atmospheric weather e.g. 'clear', 'rain', 'overcast'")
    particulates: Optional[str] = Field(None, description="Volumetric particles e.g. 'steam_leak', 'dense_fog'")
    wetness: float = Field(0.0, ge=0.0, le=1.0, description="Surface liquid wetness factor (0.0 to 1.0)")
    lighting: str = Field("neutral", description="Lighting descriptor e.g. 'emergency_red_pulsing'")
    global_lighting_vectors: List[List[float]] = Field(default_factory=list, description="Global 3D light direction vectors")
    reflections: bool = Field(False, description="Ground reflection status")
    ambient_description: Optional[str] = Field(None, description="Semantic ambient audio or lighting notes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary custom environment data")

    @model_validator(mode="before")
    @classmethod
    def _normalize_env_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            if "floor" in d and isinstance(d["floor"], dict):
                floor = d["floor"]
                if "wetness" in floor:
                    d["wetness"] = floor["wetness"]
                if "reflections" in floor:
                    d["reflections"] = floor["reflections"]
            if "global_lighting_vector" in d and "global_lighting_vectors" not in d:
                vec = d["global_lighting_vector"]
                if isinstance(vec, list) and len(vec) == 3 and isinstance(vec[0], (int, float)):
                    d["global_lighting_vectors"] = [vec]
                else:
                    d["global_lighting_vectors"] = vec
            return d
        return data

    @property
    def global_lighting_vector(self) -> Optional[List[float]]:
        """Alias for primary global lighting vector."""
        if self.global_lighting_vectors:
            return self.global_lighting_vectors[0]
        return None


class SceneState(BaseModel):
    """Immutable or persistent snapshot of a complete cinematic scene state."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    scene_id: str = Field(..., description="Unique scene identifier e.g. 'SC_014'")
    location: str = Field(..., description="Location identifier e.g. 'abandoned_cleanroom'")
    timestamp: str = Field("00:00", description="Timecode or time-of-day descriptor e.g. '23:42' or 'golden_hour'")
    environment: EnvironmentState = Field(default_factory=EnvironmentState, description="Atmospheric and lighting parameters")
    character_roster: Dict[str, CharacterState] = Field(default_factory=dict, description="Active characters in the scene")
    prop_roster: Dict[str, PropState] = Field(default_factory=dict, description="Active props in the scene")
    active_camera: Optional[CameraState] = Field(None, description="Active camera parameters")
    sequence_index: int = Field(0, ge=0, description="Sequential shot or frame sequence index")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom scene metadata")

    @model_validator(mode="before")
    @classmethod
    def _normalize_scene_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            if "id" in d and "scene_id" not in d:
                d["scene_id"] = d["id"]
            if "time_of_day" in d and "timestamp" not in d:
                d["timestamp"] = d["time_of_day"]
            if "time" in d and "timestamp" not in d:
                d["timestamp"] = d["time"]
            if "characters" in d and "character_roster" not in d:
                d["character_roster"] = d["characters"]
            if "props" in d and "prop_roster" not in d:
                d["prop_roster"] = d["props"]
            if "camera" in d and "active_camera" not in d:
                d["active_camera"] = d["camera"]

            # Normalize character_roster list or dict
            if "character_roster" in d and isinstance(d["character_roster"], list):
                d["character_roster"] = {
                    (c.character_id if hasattr(c, "character_id") else c.get("character_id") or c.get("id")): c
                    for c in d["character_roster"]
                }
            if "character_roster" in d and isinstance(d["character_roster"], dict):
                norm_chars = {}
                for cid, cval in d["character_roster"].items():
                    if isinstance(cval, CharacterState):
                        norm_chars[cid] = cval
                    elif isinstance(cval, dict):
                        cd = dict(cval)
                        if "character_id" not in cd and "id" not in cd:
                            cd["character_id"] = cid
                        norm_chars[cid] = CharacterState(**cd)
                    else:
                        norm_chars[cid] = cval
                d["character_roster"] = norm_chars

            # Normalize prop_roster list or dict
            if "prop_roster" in d and isinstance(d["prop_roster"], list):
                d["prop_roster"] = {
                    (p.prop_id if hasattr(p, "prop_id") else p.get("prop_id") or p.get("id")): p
                    for p in d["prop_roster"]
                }
            if "prop_roster" in d and isinstance(d["prop_roster"], dict):
                norm_props = {}
                for pid, pval in d["prop_roster"].items():
                    if isinstance(pval, PropState):
                        norm_props[pid] = pval
                    elif isinstance(pval, dict):
                        pd = dict(pval)
                        if "prop_id" not in pd and "id" not in pd:
                            pd["prop_id"] = pid
                        if "name" not in pd:
                            pd["name"] = pid
                        norm_props[pid] = PropState(**pd)
                    else:
                        norm_props[pid] = pval
                d["prop_roster"] = norm_props

            return d
        return data

    @property
    def id(self) -> str:
        """Alias for scene_id."""
        return self.scene_id

    @property
    def time_of_day(self) -> str:
        """Alias for timestamp."""
        return self.timestamp

    @property
    def characters(self) -> Dict[str, CharacterState]:
        """Alias for character_roster."""
        return self.character_roster

    @characters.setter
    def characters(self, val: Dict[str, CharacterState]) -> None:
        self.character_roster = val

    @property
    def props(self) -> Dict[str, PropState]:
        """Alias for prop_roster."""
        return self.prop_roster

    @props.setter
    def props(self, val: Dict[str, PropState]) -> None:
        self.prop_roster = val

    @property
    def camera(self) -> Optional[CameraState]:
        """Alias for active_camera."""
        return self.active_camera

    @camera.setter
    def camera(self, val: Optional[CameraState]) -> None:
        self.active_camera = val

    def get_character(self, character_id: str) -> Optional[CharacterState]:
        """Fetch character by ID."""
        return self.character_roster.get(character_id)

    def get_prop(self, prop_id: str) -> Optional[PropState]:
        """Fetch prop by ID."""
        return self.prop_roster.get(prop_id)

    def add_character(self, character: CharacterState) -> None:
        """Add or update character in the roster."""
        self.character_roster[character.character_id] = character

    def add_prop(self, prop: PropState) -> None:
        """Add or update prop in the roster."""
        self.prop_roster[prop.prop_id] = prop


class SceneAction(BaseModel):
    """Discrete cinematic action mutating the persistent world model."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    action_id: str = Field(default_factory=lambda: f"ACT_{uuid.uuid4().hex[:8]}", description="Unique action identifier e.g. 'ACT_019'")
    action_type: Union[ActionType, str] = Field(..., description="Action classification e.g. PROP_TRANSFER")
    actor_id: Optional[str] = Field(None, description="Primary actor ID initiating the action")
    target_id: Optional[str] = Field(None, description="Target entity ID (recipient character, prop, or zone)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Contextual parameters for mutation")
    elapsed_seconds: float = Field(0.0, ge=0.0, description="Time elapsed during this action in seconds")

    @model_validator(mode="before")
    @classmethod
    def _normalize_action_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            if "id" in d and "action_id" not in d:
                d["action_id"] = d["id"]
            if "type" in d and "action_type" not in d:
                d["action_type"] = d["type"]
            if "duration" in d and "elapsed_seconds" not in d:
                d["elapsed_seconds"] = float(d["duration"])
            return d
        return data

    @property
    def id(self) -> str:
        """Alias for action_id."""
        return self.action_id

    @property
    def type(self) -> str:
        """Alias for action_type."""
        return str(self.action_type)

    @property
    def duration(self) -> float:
        """Alias for elapsed_seconds."""
        return self.elapsed_seconds


class CharacterDelta(BaseModel):
    """Granular delta in character state between two consecutive shots."""
    character_id: str
    position_delta: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    distance_moved: float = 0.0
    velocity_mps: float = 0.0
    facing_angle_delta: float = 0.0
    eyeline_angle_delta_deg: float = 0.0
    emotional_transition: Optional[Tuple[str, str]] = None
    wardrobe_changes: Dict[str, Tuple[str, str]] = Field(default_factory=dict)
    injuries_added: List[str] = Field(default_factory=list)
    injuries_removed: List[str] = Field(default_factory=list)


class PropDelta(BaseModel):
    """Granular delta in prop state between two consecutive shots."""
    prop_id: str
    ownership_transition: Optional[Tuple[Optional[str], Optional[str]]] = None
    hand_transition: Optional[Tuple[Optional[str], Optional[str]]] = None
    physical_state_transition: Optional[Tuple[Optional[str], Optional[str]]] = None
    position_delta: Optional[List[float]] = None
    distance_moved: Optional[float] = None


class CameraDelta(BaseModel):
    """Granular delta in camera state between two consecutive shots."""
    position_delta: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    distance_moved: float = 0.0
    focal_length_delta: float = 0.0
    aperture_delta: float = 0.0
    focus_distance_delta: float = 0.0


class EnvironmentDelta(BaseModel):
    """Granular delta in environment parameters between two consecutive shots."""
    weather_transition: Optional[Tuple[str, str]] = None
    wetness_delta: float = 0.0
    particulates_transition: Optional[Tuple[Optional[str], Optional[str]]] = None
    lighting_transition: Optional[Tuple[str, str]] = None


class StateDelta(BaseModel):
    """Complete granular differential record between Shot A and Shot B."""
    shot_a_id: str
    shot_b_id: str
    elapsed_seconds: float = 0.0
    character_deltas: Dict[str, CharacterDelta] = Field(default_factory=dict)
    prop_deltas: Dict[str, PropDelta] = Field(default_factory=dict)
    environment_delta: Optional[EnvironmentDelta] = None
    camera_delta: Optional[CameraDelta] = None
    actions_applied: List[SceneAction] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        """True if any physical, character, prop, camera, or environmental differences exist."""
        for cd in self.character_deltas.values():
            if (
                cd.distance_moved > 0.001
                or abs(cd.facing_angle_delta) > 0.1
                or abs(cd.eyeline_angle_delta_deg) > 0.1
                or cd.emotional_transition is not None
                or len(cd.wardrobe_changes) > 0
                or len(cd.injuries_added) > 0
                or len(cd.injuries_removed) > 0
            ):
                return True
        for pd in self.prop_deltas.values():
            if (
                pd.ownership_transition is not None
                or pd.hand_transition is not None
                or pd.physical_state_transition is not None
                or (pd.distance_moved is not None and pd.distance_moved > 0.001)
            ):
                return True
        if self.camera_delta and (
            self.camera_delta.distance_moved > 0.001
            or abs(self.camera_delta.focal_length_delta) > 0.01
            or abs(self.camera_delta.aperture_delta) > 0.01
            or abs(self.camera_delta.focus_distance_delta) > 0.01
        ):
            return True
        if self.environment_delta and (
            abs(self.environment_delta.wetness_delta) > 0.001
            or self.environment_delta.weather_transition is not None
            or self.environment_delta.particulates_transition is not None
            or self.environment_delta.lighting_transition is not None
        ):
            return True
        return False

    @property
    def characters_entered(self) -> List[str]:
        """IDs of characters present in Shot B but not in Shot A."""
        return [
            cid for cid, cd in self.character_deltas.items()
            if cd.emotional_transition and cd.emotional_transition[0] == "none"
        ]

    @property
    def characters_exited(self) -> List[str]:
        """IDs of characters present in Shot A but absent in Shot B."""
        return [
            cid for cid, cd in self.character_deltas.items()
            if cd.emotional_transition and cd.emotional_transition[1] == "exited"
        ]

    @property
    def props_spawned(self) -> List[str]:
        """IDs of props newly introduced in Shot B."""
        return [
            pid for pid, pd in self.prop_deltas.items()
            if pd.physical_state_transition and pd.physical_state_transition[0] == "none"
        ]

    @property
    def props_consumed(self) -> List[str]:
        """IDs of props removed or consumed in Shot B."""
        return [
            pid for pid, pd in self.prop_deltas.items()
            if pd.physical_state_transition and pd.physical_state_transition[1] == "removed"
        ]


class SceneSnapshot(BaseModel):
    """Immutable frozen slice of world state at a specific shot milestone."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    shot_id: str = Field(..., description="Shot identifier associated with this frozen state")
    sequence_index: int = Field(0, description="Chronological sequence position")
    timestamp: float = Field(0.0, description="Timeline timestamp in seconds")
    state: SceneState = Field(..., description="Deep-frozen scene state")
    parent_snapshot_id: Optional[str] = Field(None, description="Previous snapshot in the timeline branch")
    actions_applied: List[SceneAction] = Field(default_factory=list, description="Actions applied leading to this state")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata attached to the shot slice")

    @model_validator(mode="before")
    @classmethod
    def _normalize_snapshot_ids(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            if "snapshot_id" not in d and "shot_id" in d:
                d["snapshot_id"] = d["shot_id"]
            if "shot_id" not in d and "snapshot_id" in d:
                d["shot_id"] = d["snapshot_id"]
            return d
        return data
