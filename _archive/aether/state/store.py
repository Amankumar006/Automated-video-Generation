"""Aether World State Store.

Provides JSON persistence, serialization, state ledger export, and query APIs
for prop possession history, character movement paths, and wardrobe state progression.
(Project Aether v2 - Pillar 2 / WBS 1.3).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field

from aether.state.graph import AetherWorldModel
from aether.state.schemas import (
    HandAttachment,
    PropState,
    SceneAction,
    SceneSnapshot,
    SceneState,
)


class PropPossessionRecord(BaseModel):
    """Chronological record of prop ownership and spatial location at a shot milestone."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    shot_id: str
    sequence_index: int
    timestamp: float
    prop_id: str
    owner_id: Optional[str] = None
    hand_attachment: str = "none"
    world_coordinates: Optional[List[float]] = None
    physical_state: str = "pristine"
    is_held: bool = False


class CharacterMovementPoint(BaseModel):
    """Kinematic waypoint for a character across the cinematic timeline."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    shot_id: str
    sequence_index: int
    timestamp: float
    character_id: str
    position: List[float]
    facing_angle: float
    eyeline_vector: List[float]
    distance_from_previous: float = 0.0
    velocity_from_previous: float = 0.0


class WardrobeRecord(BaseModel):
    """Snapshot record of garment damage state at a shot milestone."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    shot_id: str
    sequence_index: int
    timestamp: float
    character_id: str
    garment_slot: str
    garment_id: str
    state: str
    color: Optional[str] = None
    damage_level: float = 0.0


class InjuryRecord(BaseModel):
    """Record of character physical injuries at a shot milestone."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    shot_id: str
    sequence_index: int
    timestamp: float
    character_id: str
    injuries: List[str]


class WorldStateStore:
    """Serialization, JSON persistence, ledger generation, and history query engine."""

    @classmethod
    def to_json(cls, world_model: AetherWorldModel, indent: int = 2) -> str:
        """Serializes complete AetherWorldModel instance to a formatted JSON string."""
        data = {
            "version": "2.0",
            "active_state": world_model.active_state.model_dump(),
            "shots": {sid: snap.model_dump() for sid, snap in world_model.shots.items()},
            "branches": world_model.branches,
            "current_branch": world_model.current_branch,
            "action_history": [a.model_dump() for a in world_model.action_history],
            "timeline_clock": world_model._timeline_clock,
        }
        return json.dumps(data, indent=indent, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> AetherWorldModel:
        """Reconstructs an AetherWorldModel instance from serialized JSON."""
        data = json.loads(json_str)
        active_state = SceneState.model_validate(data["active_state"])
        model = AetherWorldModel(initial_state=active_state)

        # Restore snapshots
        shots_data = data.get("shots", {})
        for sid, snap_dict in shots_data.items():
            snap = SceneSnapshot.model_validate(snap_dict)
            model._shots[sid] = snap
            model._snapshots[snap.snapshot_id] = snap

        # Restore branches
        model._branches = data.get("branches", {"main": []})
        model._current_branch = data.get("current_branch", "main")

        # Restore action history
        actions_data = data.get("action_history", [])
        model._action_history = [SceneAction.model_validate(ad) for ad in actions_data]
        model._timeline_clock = float(data.get("timeline_clock", 0.0))

        return model

    @classmethod
    def save(cls, world_model: AetherWorldModel, file_path: Union[str, Path]) -> Path:
        """Saves world model to a JSON file on disk."""
        path = Path(file_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        content = cls.to_json(world_model)
        path.write_text(content, encoding="utf-8")
        return path

    @classmethod
    def save_to_file(cls, world_model: AetherWorldModel, file_path: Union[str, Path]) -> Path:
        """Alias for save."""
        return cls.save(world_model, file_path)

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> AetherWorldModel:
        """Loads world model from a JSON file on disk."""
        path = Path(file_path).resolve()
        content = path.read_text(encoding="utf-8")
        return cls.from_json(content)

    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> AetherWorldModel:
        """Alias for load."""
        return cls.load(file_path)

    @classmethod
    def query_prop_possession_history(
        cls,
        world_model: AetherWorldModel,
        prop_id: str,
        branch_name: Optional[str] = None,
    ) -> List[PropPossessionRecord]:
        """Queries the sequential history of prop ownership, hands, and positions."""
        timeline = world_model.get_timeline(branch_name)
        records: List[PropPossessionRecord] = []

        for snap in timeline:
            prop = snap.state.prop_roster.get(prop_id)
            if prop:
                records.append(
                    PropPossessionRecord(
                        shot_id=snap.shot_id,
                        sequence_index=snap.sequence_index,
                        timestamp=snap.timestamp,
                        prop_id=prop_id,
                        owner_id=prop.owner_id,
                        hand_attachment=str(prop.hand_attachment.value if isinstance(prop.hand_attachment, HandAttachment) else prop.hand_attachment),
                        world_coordinates=prop.world_coordinates,
                        physical_state=prop.physical_state,
                        is_held=prop.is_held,
                    )
                )

        return records

    @classmethod
    def query_character_movement_path(
        cls,
        world_model: AetherWorldModel,
        character_id: str,
        branch_name: Optional[str] = None,
    ) -> List[CharacterMovementPoint]:
        """Queries 3D trajectory waypoints and velocities for a character across shots."""
        timeline = world_model.get_timeline(branch_name)
        points: List[CharacterMovementPoint] = []
        prev_pos: Optional[List[float]] = None
        prev_time: Optional[float] = None

        for snap in timeline:
            char = snap.state.character_roster.get(character_id)
            if char:
                pos = char.position
                dist = 0.0
                vel = 0.0
                if prev_pos is not None and prev_time is not None:
                    dist = math.sqrt(sum((pos[i] - prev_pos[i]) ** 2 for i in range(3)))
                    dt = snap.timestamp - prev_time
                    vel = (dist / dt) if dt > 0.0 else 0.0

                points.append(
                    CharacterMovementPoint(
                        shot_id=snap.shot_id,
                        sequence_index=snap.sequence_index,
                        timestamp=snap.timestamp,
                        character_id=character_id,
                        position=pos,
                        facing_angle=char.facing_angle,
                        eyeline_vector=char.eyeline_vector,
                        distance_from_previous=dist,
                        velocity_from_previous=vel,
                    )
                )
                prev_pos = pos
                prev_time = snap.timestamp

        return points

    @classmethod
    def query_wardrobe_history(
        cls,
        world_model: AetherWorldModel,
        character_id: str,
        garment_slot: Optional[str] = None,
        branch_name: Optional[str] = None,
    ) -> List[WardrobeRecord]:
        """Queries chronological garment state transitions for a character."""
        timeline = world_model.get_timeline(branch_name)
        records: List[WardrobeRecord] = []

        for snap in timeline:
            char = snap.state.character_roster.get(character_id)
            if char:
                for slot, garment in char.wardrobe.items():
                    if garment_slot is None or slot == garment_slot:
                        records.append(
                            WardrobeRecord(
                                shot_id=snap.shot_id,
                                sequence_index=snap.sequence_index,
                                timestamp=snap.timestamp,
                                character_id=character_id,
                                garment_slot=slot,
                                garment_id=garment.id,
                                state=garment.state,
                                color=garment.color,
                                damage_level=garment.damage_level,
                            )
                        )

        return records

    @classmethod
    def query_injuries_history(
        cls,
        world_model: AetherWorldModel,
        character_id: str,
        branch_name: Optional[str] = None,
    ) -> List[InjuryRecord]:
        """Queries injury list progression for a character."""
        timeline = world_model.get_timeline(branch_name)
        records: List[InjuryRecord] = []

        for snap in timeline:
            char = snap.state.character_roster.get(character_id)
            if char:
                records.append(
                    InjuryRecord(
                        shot_id=snap.shot_id,
                        sequence_index=snap.sequence_index,
                        timestamp=snap.timestamp,
                        character_id=character_id,
                        injuries=list(char.injuries),
                    )
                )

        return records

    @classmethod
    def query_shot_by_id(
        cls,
        world_model: AetherWorldModel,
        shot_id: str,
    ) -> Optional[SceneSnapshot]:
        """Fetches frozen snapshot slice by shot ID."""
        return world_model.get_snapshot(shot_id)

    @classmethod
    def export_state_ledger(
        cls,
        world_model: AetherWorldModel,
        branch_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Exports a production state ledger summarizing characters, props, shots, and timeline."""
        timeline = world_model.get_timeline(branch_name)

        all_chars: Dict[str, Dict[str, Any]] = {}
        all_props: Dict[str, Dict[str, Any]] = {}

        shot_summaries = []
        for snap in timeline:
            st = snap.state
            cam = st.active_camera
            shot_summaries.append({
                "shot_id": snap.shot_id,
                "sequence_index": snap.sequence_index,
                "timestamp": snap.timestamp,
                "location": st.location,
                "characters": list(st.character_roster.keys()),
                "props": list(st.prop_roster.keys()),
                "camera_lens_mm": cam.lens_focal_length_mm if cam else None,
                "actions_applied": len(snap.actions_applied),
            })

            for cid, char in st.character_roster.items():
                all_chars[cid] = {
                    "name": char.name,
                    "final_position": char.position,
                    "final_emotion": char.emotional_state,
                    "final_wardrobe": {s: g.state for s, g in char.wardrobe.items()},
                    "final_injuries": char.injuries,
                }

            for pid, prop in st.prop_roster.items():
                all_props[pid] = {
                    "name": prop.name,
                    "final_owner": prop.owner_id,
                    "final_hand": str(prop.hand_attachment.value if isinstance(prop.hand_attachment, HandAttachment) else prop.hand_attachment),
                    "final_physical_state": prop.physical_state,
                    "world_coordinates": prop.world_coordinates,
                }

        return {
            "ledger_version": "2.0",
            "active_branch": branch_name or world_model.current_branch,
            "total_shots": len(timeline),
            "total_duration_seconds": timeline[-1].timestamp if timeline else 0.0,
            "characters_summary": all_chars,
            "props_summary": all_props,
            "timeline_shots": shot_summaries,
            "actions_count": len(world_model.action_history),
        }
