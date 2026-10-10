"""Aether World Model (Scene State Graph Engine).

Provides the central AetherWorldModel class managing the active cinematic scene state,
applying sequential mutations via SceneActions, freezing immutable shot slices,
calculating granular StateDeltas, and supporting timeline branching and rollbacks
for Project Aether v2 (Pillar 2 / WBS 1.3).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple, Union

from aether.state.schemas import (
    ActionType,
    CameraDelta,
    CameraState,
    CharacterDelta,
    CharacterState,
    EnvironmentDelta,
    EnvironmentState,
    HandAttachment,
    PhysicalState,
    PropDelta,
    PropState,
    SceneAction,
    SceneSnapshot,
    SceneState,
    StateDelta,
    WardrobeItemState,
)


def _get_action_type(action: SceneAction) -> str:
    """Extract normalized uppercase string from ActionType enum or string."""
    at = action.action_type
    if isinstance(at, ActionType):
        return at.value.upper()
    s = str(at)
    if "." in s:
        s = s.split(".")[-1]
    return s.upper()


class AetherWorldModel:
    """Central world state engine managing active scene state and multi-shot continuity."""

    def __init__(self, initial_state: Optional[SceneState] = None) -> None:
        if initial_state is not None:
            self._active_state: SceneState = initial_state.model_copy(deep=True)
        else:
            self._active_state = SceneState(
                scene_id="SC_INIT",
                location="stage",
                timestamp="00:00",
            )

        self._shots: Dict[str, SceneSnapshot] = {}
        self._snapshots: Dict[str, SceneSnapshot] = {}
        self._branches: Dict[str, List[str]] = {"main": []}
        self._current_branch: str = "main"
        self._action_history: List[SceneAction] = []
        self._pending_actions: List[SceneAction] = []
        self._timeline_clock: float = 0.0

    @property
    def active_state(self) -> SceneState:
        """Returns the current active scene state."""
        return self._active_state

    @property
    def current_state(self) -> SceneState:
        """Alias for active_state."""
        return self._active_state

    @property
    def shots(self) -> Dict[str, SceneSnapshot]:
        """Dictionary of frozen shot snapshots indexed by shot_id."""
        return self._shots

    @property
    def snapshots(self) -> Dict[str, SceneSnapshot]:
        """Dictionary of frozen snapshots indexed by snapshot_id."""
        return self._snapshots

    @property
    def branches(self) -> Dict[str, List[str]]:
        """Dictionary of timeline branch names to ordered shot_ids."""
        return self._branches

    @property
    def current_branch(self) -> str:
        """Name of the currently active branch."""
        return self._current_branch

    @property
    def action_history(self) -> List[SceneAction]:
        """Chronological list of all actions applied across the timeline."""
        return self._action_history

    @property
    def character_roster(self) -> Dict[str, CharacterState]:
        """Active characters mapped by character_id."""
        return self._active_state.character_roster

    @property
    def characters(self) -> Dict[str, CharacterState]:
        """Alias for character_roster."""
        return self._active_state.character_roster

    @property
    def prop_roster(self) -> Dict[str, PropState]:
        """Active props mapped by prop_id."""
        return self._active_state.prop_roster

    @property
    def props(self) -> Dict[str, PropState]:
        """Alias for prop_roster."""
        return self._active_state.prop_roster

    @property
    def active_camera(self) -> Optional[CameraState]:
        """Active camera configuration."""
        return self._active_state.active_camera

    @property
    def camera(self) -> Optional[CameraState]:
        """Alias for active_camera."""
        return self._active_state.active_camera

    def set_active_state(self, state: SceneState) -> None:
        """Explicitly sets the active scene state via deep copy."""
        self._active_state = state.model_copy(deep=True)

    def apply_action(self, action: SceneAction) -> SceneState:
        """Applies a discrete action mutation to the active world state."""
        action_type_str = _get_action_type(action)

        if action_type_str == ActionType.CHARACTER_MOVE.value:
            self._apply_character_move(action)
        elif action_type_str in (
            ActionType.PROP_TRANSFER.value,
            "PROP_HANDOFF",
            "PROP_PICKUP",
            "PROP_DROP",
        ):
            self._apply_prop_transfer(action)
        elif action_type_str in (
            ActionType.PROP_SPAWNED.value,
            "PROP_INTRODUCED",
            "PROP_CREATED",
        ):
            self._apply_prop_spawned(action)
        elif action_type_str in (
            ActionType.PROP_CONSUMED.value,
            ActionType.PROP_DESTROYED.value,
            "PROP_REMOVED",
            "PROP_DESPAWN",
        ):
            self._apply_prop_consumed(action)
        elif action_type_str in (
            ActionType.WARDROBE_MUTATION.value,
            ActionType.WARDROBE_CHANGE.value,
        ):
            self._apply_wardrobe_mutation(action)
        elif action_type_str == ActionType.WARDROBE_REPAIR.value:
            self._apply_wardrobe_repair(action)
        elif action_type_str == ActionType.ENVIRONMENT_CHANGE.value:
            self._apply_environment_change(action)
        elif action_type_str in (ActionType.INJURY_MUTATION.value, ActionType.INJURY_ADDED.value):
            self._apply_injury_mutation(action)
        elif action_type_str in (
            ActionType.HEALING.value,
            ActionType.MEDICAL_TREATMENT.value,
            "INJURY_REMOVED",
        ):
            self._apply_injury_healing(action)
        elif action_type_str == ActionType.EMOTION_CHANGE.value:
            self._apply_emotion_change(action)
        elif action_type_str == ActionType.PROP_MUTATION.value:
            self._apply_prop_mutation(action)
        elif action_type_str == ActionType.CAMERA_MOVE.value:
            self._apply_camera_move(action)
        else:
            # Custom or generic action
            self._timeline_clock += action.elapsed_seconds

        self._action_history.append(action)
        self._pending_actions.append(action)
        return self._active_state

    def apply_actions(self, actions: List[SceneAction]) -> SceneState:
        """Sequentially applies a sequence of scene actions."""
        for action in actions:
            self.apply_action(action)
        return self._active_state

    def _apply_character_move(self, action: SceneAction) -> None:
        actor_id = action.actor_id or action.target_id
        if not actor_id:
            return
        char = self._active_state.character_roster.get(actor_id)
        if char:
            if "position" in action.metadata:
                char.position = [float(x) for x in action.metadata["position"]]
            elif "new_position" in action.metadata:
                char.position = [float(x) for x in action.metadata["new_position"]]
            if "facing_angle" in action.metadata:
                char.facing_angle = float(action.metadata["facing_angle"])
            if "eyeline_vector" in action.metadata:
                char.eyeline_vector = [float(x) for x in action.metadata["eyeline_vector"]]
        self._timeline_clock += action.elapsed_seconds

    def _apply_prop_transfer(self, action: SceneAction) -> None:
        prop_id = (
            action.metadata.get("prop_id")
            or action.metadata.get("prop")
            or action.metadata.get("item")
        )
        if not prop_id:
            if action.target_id and action.target_id in self._active_state.prop_roster:
                prop_id = action.target_id
            elif action.actor_id and action.actor_id in self._active_state.prop_roster:
                prop_id = action.actor_id

        if not prop_id:
            return
        prop = self._active_state.prop_roster.get(prop_id)
        if not prop:
            return

        recipient = (
            action.metadata.get("new_owner")
            or action.metadata.get("recipient")
            or action.metadata.get("to")
        )
        if not recipient and action.target_id and action.target_id != prop_id:
            recipient = action.target_id

        hand_val = (
            action.metadata.get("hand")
            or action.metadata.get("to_hand")
            or action.metadata.get("hand_attachment")
        )
        is_drop = (
            action.metadata.get("drop", False)
            or recipient in (None, "none", "world", "floor")
        )

        if is_drop:
            # Disconnect from previous holder
            old_owner = prop.owner_id
            if old_owner and old_owner in self._active_state.character_roster:
                old_char = self._active_state.character_roster[old_owner]
                old_char.held_props = {k: v for k, v in old_char.held_props.items() if v != prop_id}
            prop.owner_id = None
            prop.hand_attachment = HandAttachment.NONE
            if "world_coordinates" in action.metadata:
                prop.world_coordinates = [float(x) for x in action.metadata["world_coordinates"]]
            elif "position" in action.metadata:
                prop.world_coordinates = [float(x) for x in action.metadata["position"]]
            elif old_owner and old_owner in self._active_state.character_roster:
                prop.world_coordinates = list(self._active_state.character_roster[old_owner].position)
            else:
                prop.world_coordinates = [0.0, 0.0, 0.0]
        else:
            # Clear from previous owner
            old_owner = prop.owner_id
            if old_owner and old_owner in self._active_state.character_roster:
                old_char = self._active_state.character_roster[old_owner]
                old_char.held_props = {k: v for k, v in old_char.held_props.items() if v != prop_id}

            hand_att = HandAttachment.from_str(hand_val) if hand_val else HandAttachment.RIGHT
            prop.owner_id = recipient
            prop.hand_attachment = hand_att
            prop.world_coordinates = None

            if recipient in self._active_state.character_roster:
                r_char = self._active_state.character_roster[recipient]
                slot_key = str(hand_att.value)
                # Unseat any displaced prop currently in this hand slot
                if slot_key in r_char.held_props:
                    displaced_pid = r_char.held_props[slot_key]
                    if displaced_pid in self._active_state.prop_roster and displaced_pid != prop_id:
                        displaced_prop = self._active_state.prop_roster[displaced_pid]
                        displaced_prop.owner_id = None
                        displaced_prop.hand_attachment = HandAttachment.NONE
                        displaced_prop.world_coordinates = list(r_char.position)
                r_char.held_props[slot_key] = prop_id

        if "physical_state" in action.metadata:
            prop.physical_state = str(action.metadata["physical_state"])

        self._timeline_clock += action.elapsed_seconds

    def _apply_prop_spawned(self, action: SceneAction) -> None:
        prop_id = (
            action.metadata.get("prop_id")
            or action.metadata.get("prop")
            or action.metadata.get("item")
            or action.target_id
        )
        if not prop_id:
            return
        name = action.metadata.get("name") or prop_id.replace("_", " ").title()
        owner_id = action.metadata.get("owner_id") or action.metadata.get("recipient")
        hand = action.metadata.get("hand") or action.metadata.get("hand_attachment")
        hand_att = HandAttachment.from_str(hand) if hand else (HandAttachment.RIGHT if owner_id else HandAttachment.NONE)
        coords = action.metadata.get("world_coordinates") or action.metadata.get("position")
        if coords is not None:
            coords = [float(x) for x in coords]
        phys_state = str(action.metadata.get("physical_state", "pristine"))

        prop = PropState(
            prop_id=prop_id,
            name=name,
            owner_id=owner_id,
            hand_attachment=hand_att,
            world_coordinates=coords if not owner_id else None,
            physical_state=phys_state,
            metadata=action.metadata.get("prop_metadata", {}),
        )
        self._active_state.prop_roster[prop_id] = prop
        if owner_id and owner_id in self._active_state.character_roster:
            self._active_state.character_roster[owner_id].held_props[str(hand_att.value)] = prop_id

        self._timeline_clock += action.elapsed_seconds

    def _apply_prop_consumed(self, action: SceneAction) -> None:
        prop_id = (
            action.metadata.get("prop_id")
            or action.metadata.get("prop")
            or action.metadata.get("item")
            or action.target_id
            or action.actor_id
        )
        if not prop_id:
            return
        if prop_id in self._active_state.prop_roster:
            prop = self._active_state.prop_roster.pop(prop_id)
            if prop.owner_id and prop.owner_id in self._active_state.character_roster:
                char = self._active_state.character_roster[prop.owner_id]
                char.held_props = {k: v for k, v in char.held_props.items() if v != prop_id}
        self._timeline_clock += action.elapsed_seconds

    def _apply_wardrobe_mutation(self, action: SceneAction) -> None:
        actor_id = action.actor_id or action.target_id
        if not actor_id:
            return
        char = self._active_state.character_roster.get(actor_id)
        if not char:
            return

        slot = action.metadata.get("slot") or action.metadata.get("garment_id") or "garment"
        new_state = action.metadata.get("state") or action.metadata.get("new_state", "damaged")
        color = action.metadata.get("color")
        damage_level = action.metadata.get("damage_level")

        if slot in char.wardrobe:
            char.wardrobe[slot].state = new_state
            if color is not None:
                char.wardrobe[slot].color = color
            if damage_level is not None:
                char.wardrobe[slot].damage_level = float(damage_level)
        else:
            char.wardrobe[slot] = WardrobeItemState(
                id=slot,
                type=slot,
                state=new_state,
                color=color,
                damage_level=float(damage_level) if damage_level is not None else 0.5,
            )

        self._timeline_clock += action.elapsed_seconds

    def _apply_wardrobe_repair(self, action: SceneAction) -> None:
        actor_id = action.actor_id or action.target_id
        if not actor_id:
            return
        char = self._active_state.character_roster.get(actor_id)
        if not char:
            return
        slot = action.metadata.get("slot") or action.metadata.get("garment_id")
        target_state = action.metadata.get("state", "pristine")
        damage_level = float(action.metadata.get("damage_level", 0.0))

        if slot and slot in char.wardrobe:
            char.wardrobe[slot].state = target_state
            char.wardrobe[slot].damage_level = damage_level
        elif not slot or slot in ("all", "outfit"):
            for garment in char.wardrobe.values():
                garment.state = target_state
                garment.damage_level = damage_level

        self._timeline_clock += action.elapsed_seconds

    def _apply_environment_change(self, action: SceneAction) -> None:
        env = self._active_state.environment
        if "weather" in action.metadata:
            env.weather = str(action.metadata["weather"])
        if "wetness" in action.metadata:
            env.wetness = float(action.metadata["wetness"])
        if "particulates" in action.metadata:
            env.particulates = action.metadata["particulates"]
        if "lighting" in action.metadata:
            env.lighting = str(action.metadata["lighting"])
        if "reflections" in action.metadata:
            env.reflections = bool(action.metadata["reflections"])
        if "global_lighting_vectors" in action.metadata:
            env.global_lighting_vectors = action.metadata["global_lighting_vectors"]
        elif "global_lighting_vector" in action.metadata:
            vec = action.metadata["global_lighting_vector"]
            env.global_lighting_vectors = [vec] if isinstance(vec[0], (int, float)) else vec

        self._timeline_clock += action.elapsed_seconds

    def _apply_injury_mutation(self, action: SceneAction) -> None:
        actor_id = action.actor_id or action.target_id
        if not actor_id:
            return
        char = self._active_state.character_roster.get(actor_id)
        injury = action.metadata.get("injury") or action.metadata.get("injury_id")
        if char and injury and injury not in char.injuries:
            char.injuries.append(injury)
        self._timeline_clock += action.elapsed_seconds

    def _apply_injury_healing(self, action: SceneAction) -> None:
        actor_id = action.actor_id or action.target_id
        if not actor_id:
            return
        char = self._active_state.character_roster.get(actor_id)
        if not char:
            return
        injury = action.metadata.get("injury") or action.metadata.get("injury_id")
        if injury:
            if injury in char.injuries:
                char.injuries.remove(injury)
        else:
            char.injuries.clear()
        self._timeline_clock += action.elapsed_seconds

    def _apply_emotion_change(self, action: SceneAction) -> None:
        actor_id = action.actor_id or action.target_id
        if not actor_id:
            return
        char = self._active_state.character_roster.get(actor_id)
        emotion = action.metadata.get("emotional_state") or action.metadata.get("emotion")
        if char and emotion:
            char.emotional_state = emotion
        self._timeline_clock += action.elapsed_seconds

    def _apply_prop_mutation(self, action: SceneAction) -> None:
        prop_id = action.target_id or action.metadata.get("prop_id") or action.actor_id
        if not prop_id:
            return
        prop = self._active_state.prop_roster.get(prop_id)
        new_state = action.metadata.get("physical_state") or action.metadata.get("state")
        if prop and new_state:
            prop.physical_state = new_state
        self._timeline_clock += action.elapsed_seconds

    def _apply_camera_move(self, action: SceneAction) -> None:
        if self._active_state.active_camera is None:
            self._active_state.active_camera = CameraState()
        cam = self._active_state.active_camera

        if "position" in action.metadata:
            cam.position = [float(x) for x in action.metadata["position"]]
        for k in ("lens_focal_length_mm", "focal_length_mm", "lens_mm"):
            if k in action.metadata:
                cam.previous_lens_mm = cam.lens_focal_length_mm
                cam.lens_focal_length_mm = float(action.metadata[k])
                break
        if "aperture" in action.metadata:
            cam.aperture = float(action.metadata["aperture"])
        if "focus_distance" in action.metadata:
            cam.focus_distance = float(action.metadata["focus_distance"])
        if "eyeline_vector" in action.metadata:
            cam.previous_eyeline_vector = cam.eyeline_vector
            cam.eyeline_vector = [float(x) for x in action.metadata["eyeline_vector"]]

        self._timeline_clock += action.elapsed_seconds

    def freeze_shot(self, shot_id: str, metadata: Optional[Dict[str, Any]] = None) -> SceneSnapshot:
        """Freezes an immutable snapshot slice of the current active world state for a shot."""
        if shot_id in self._shots:
            raise ValueError(f"Shot '{shot_id}' has already been frozen in world model")

        snapshot_id = f"snap_{shot_id}"
        parent_id = None
        current_branch_shots = self._branches[self._current_branch]
        if current_branch_shots:
            last_shot_id = current_branch_shots[-1]
            parent_id = self._shots[last_shot_id].snapshot_id

        frozen_state = self._active_state.model_copy(deep=True)
        frozen_state.sequence_index = len(current_branch_shots)

        snapshot = SceneSnapshot(
            snapshot_id=snapshot_id,
            shot_id=shot_id,
            sequence_index=len(current_branch_shots),
            timestamp=self._timeline_clock,
            state=frozen_state,
            parent_snapshot_id=parent_id,
            actions_applied=list(self._pending_actions),
            metadata=metadata or {},
        )

        self._shots[shot_id] = snapshot
        self._snapshots[snapshot_id] = snapshot
        self._branches[self._current_branch].append(shot_id)
        self._pending_actions.clear()
        return snapshot

    def compute_delta(self, shot_a_id: str, shot_b_id: str) -> StateDelta:
        """Calculates granular StateDelta between two frozen shot snapshots."""
        if shot_a_id not in self._shots:
            raise KeyError(f"Shot '{shot_a_id}' not found in frozen snapshots")
        if shot_b_id not in self._shots:
            raise KeyError(f"Shot '{shot_b_id}' not found in frozen snapshots")

        snap_a = self._shots[shot_a_id]
        snap_b = self._shots[shot_b_id]
        elapsed = max(0.0, snap_b.timestamp - snap_a.timestamp)
        return self.compute_delta_between_states(
            state_a=snap_a.state,
            state_b=snap_b.state,
            elapsed_seconds=elapsed,
            actions_applied=snap_b.actions_applied,
            shot_a_id=shot_a_id,
            shot_b_id=shot_b_id,
        )

    @staticmethod
    def compute_delta_between_states(
        state_a: SceneState,
        state_b: SceneState,
        elapsed_seconds: float = 0.0,
        actions_applied: Optional[List[SceneAction]] = None,
        shot_a_id: str = "shot_a",
        shot_b_id: str = "shot_b",
    ) -> StateDelta:
        """Computes granular differential metrics between any two SceneStates."""
        char_deltas: Dict[str, CharacterDelta] = {}
        all_char_ids = set(state_a.character_roster.keys()) | set(state_b.character_roster.keys())

        for cid in all_char_ids:
            ca = state_a.character_roster.get(cid)
            cb = state_b.character_roster.get(cid)
            if ca and cb:
                pos_delta = [cb.position[i] - ca.position[i] for i in range(3)]
                dist = math.sqrt(sum(c * c for c in pos_delta))
                vel = dist / elapsed_seconds if elapsed_seconds > 0.0 else 0.0
                facing_delta = cb.facing_angle - ca.facing_angle

                # Eyeline deviation angle
                mag_a = math.sqrt(sum(c * c for c in ca.eyeline_vector))
                mag_b = math.sqrt(sum(c * c for c in cb.eyeline_vector))
                dot = sum(ca.eyeline_vector[i] * cb.eyeline_vector[i] for i in range(3))
                denom = mag_a * mag_b
                cos_val = max(-1.0, min(1.0, dot / denom if denom > 0 else 1.0))
                eyeline_deg = math.degrees(math.acos(cos_val))

                emotion_trans = (
                    (ca.emotional_state, cb.emotional_state)
                    if ca.emotional_state != cb.emotional_state
                    else None
                )

                wardrobe_changes: Dict[str, Tuple[str, str]] = {}
                all_slots = set(ca.wardrobe.keys()) | set(cb.wardrobe.keys())
                for slot in all_slots:
                    wa = ca.wardrobe.get(slot)
                    wb = cb.wardrobe.get(slot)
                    sa = wa.state if wa else "missing"
                    sb = wb.state if wb else "missing"
                    if sa != sb:
                        wardrobe_changes[slot] = (sa, sb)

                inj_added = [i for i in cb.injuries if i not in ca.injuries]
                inj_removed = [i for i in ca.injuries if i not in cb.injuries]

                char_deltas[cid] = CharacterDelta(
                    character_id=cid,
                    position_delta=pos_delta,
                    distance_moved=dist,
                    velocity_mps=vel,
                    facing_angle_delta=facing_delta,
                    eyeline_angle_delta_deg=eyeline_deg,
                    emotional_transition=emotion_trans,
                    wardrobe_changes=wardrobe_changes,
                    injuries_added=inj_added,
                    injuries_removed=inj_removed,
                )
            elif cb and not ca:
                char_deltas[cid] = CharacterDelta(
                    character_id=cid,
                    position_delta=list(cb.position),
                    distance_moved=0.0,
                    velocity_mps=0.0,
                    emotional_transition=("none", cb.emotional_state),
                    wardrobe_changes={s: ("none", w.state) for s, w in cb.wardrobe.items()},
                    injuries_added=list(cb.injuries),
                    injuries_removed=[],
                )
            elif ca and not cb:
                char_deltas[cid] = CharacterDelta(
                    character_id=cid,
                    position_delta=[-ca.position[i] for i in range(3)],
                    distance_moved=0.0,
                    velocity_mps=0.0,
                    emotional_transition=(ca.emotional_state, "exited"),
                    wardrobe_changes={s: (w.state, "exited") for s, w in ca.wardrobe.items()},
                    injuries_added=[],
                    injuries_removed=list(ca.injuries),
                )

        # Prop deltas
        prop_deltas: Dict[str, PropDelta] = {}
        all_prop_ids = set(state_a.prop_roster.keys()) | set(state_b.prop_roster.keys())

        for pid in all_prop_ids:
            pa = state_a.prop_roster.get(pid)
            pb = state_b.prop_roster.get(pid)
            if pa and pb:
                owner_trans = (
                    (pa.owner_id, pb.owner_id)
                    if pa.owner_id != pb.owner_id
                    else None
                )
                hand_a = str(pa.hand_attachment.value if hasattr(pa.hand_attachment, "value") else pa.hand_attachment)
                hand_b = str(pb.hand_attachment.value if hasattr(pb.hand_attachment, "value") else pb.hand_attachment)
                hand_trans = (
                    (hand_a, hand_b)
                    if hand_a != hand_b
                    else None
                )
                phys_trans = (
                    (pa.physical_state, pb.physical_state)
                    if pa.physical_state != pb.physical_state
                    else None
                )
                p_delta, p_dist = None, None
                if pa.world_coordinates and pb.world_coordinates:
                    p_delta = [pb.world_coordinates[i] - pa.world_coordinates[i] for i in range(3)]
                    p_dist = math.sqrt(sum(c * c for c in p_delta))

                if owner_trans or hand_trans or phys_trans or (p_dist and p_dist > 0.001):
                    prop_deltas[pid] = PropDelta(
                        prop_id=pid,
                        ownership_transition=owner_trans,
                        hand_transition=hand_trans,
                        physical_state_transition=phys_trans,
                        position_delta=p_delta,
                        distance_moved=p_dist,
                    )
            elif pb and not pa:
                prop_deltas[pid] = PropDelta(
                    prop_id=pid,
                    ownership_transition=(None, pb.owner_id),
                    hand_transition=(None, str(pb.hand_attachment.value if hasattr(pb.hand_attachment, "value") else pb.hand_attachment)),
                    physical_state_transition=("none", pb.physical_state),
                    position_delta=pb.world_coordinates,
                    distance_moved=0.0,
                )
            elif pa and not pb:
                prop_deltas[pid] = PropDelta(
                    prop_id=pid,
                    ownership_transition=(pa.owner_id, None),
                    hand_transition=(str(pa.hand_attachment.value if hasattr(pa.hand_attachment, "value") else pa.hand_attachment), None),
                    physical_state_transition=(pa.physical_state, "removed"),
                    position_delta=None,
                    distance_moved=0.0,
                )

        # Environment delta
        env_delta = None
        ea = state_a.environment
        eb = state_b.environment
        if ea and eb:
            env_delta = EnvironmentDelta(
                weather_transition=(ea.weather, eb.weather) if ea.weather != eb.weather else None,
                wetness_delta=eb.wetness - ea.wetness,
                particulates_transition=(
                    (ea.particulates, eb.particulates)
                    if ea.particulates != eb.particulates
                    else None
                ),
                lighting_transition=(
                    (ea.lighting, eb.lighting)
                    if ea.lighting != eb.lighting
                    else None
                ),
            )

        # Camera delta
        cam_delta = None
        ca = state_a.active_camera
        cb = state_b.active_camera
        if ca and cb:
            c_pos_delta = [cb.position[i] - ca.position[i] for i in range(3)]
            c_dist = math.sqrt(sum(c * c for c in c_pos_delta))
            cam_delta = CameraDelta(
                position_delta=c_pos_delta,
                distance_moved=c_dist,
                focal_length_delta=cb.lens_focal_length_mm - ca.lens_focal_length_mm,
                aperture_delta=cb.aperture - ca.aperture,
                focus_distance_delta=cb.focus_distance - ca.focus_distance,
            )
        elif cb and not ca:
            cam_delta = CameraDelta(
                position_delta=list(cb.position),
                distance_moved=0.0,
                focal_length_delta=cb.lens_focal_length_mm,
                aperture_delta=cb.aperture,
                focus_distance_delta=cb.focus_distance,
            )

        return StateDelta(
            shot_a_id=shot_a_id,
            shot_b_id=shot_b_id,
            elapsed_seconds=elapsed_seconds,
            character_deltas=char_deltas,
            prop_deltas=prop_deltas,
            environment_delta=env_delta,
            camera_delta=cam_delta,
            actions_applied=actions_applied or [],
        )

    def create_branch(self, branch_name: str, from_shot_id: Optional[str] = None) -> str:
        """Forks the timeline into a named branch, optionally starting from a historic shot."""
        if from_shot_id is not None:
            if from_shot_id not in self._shots:
                raise KeyError(f"Shot '{from_shot_id}' not found in frozen snapshots")
            snap = self._shots[from_shot_id]
            self._active_state = snap.state.model_copy(deep=True)
            self._timeline_clock = snap.timestamp
            current_shots = self._branches.get(self._current_branch, [])
            if from_shot_id in current_shots:
                idx = current_shots.index(from_shot_id)
                self._branches[branch_name] = list(current_shots[: idx + 1])
            else:
                found = False
                for b_shots in self._branches.values():
                    if from_shot_id in b_shots:
                        idx = b_shots.index(from_shot_id)
                        self._branches[branch_name] = list(b_shots[: idx + 1])
                        found = True
                        break
                if not found:
                    self._branches[branch_name] = [from_shot_id]
        else:
            self._branches[branch_name] = list(self._branches.get(self._current_branch, []))

        self._current_branch = branch_name
        self._pending_actions.clear()
        return branch_name

    def checkout_branch(self, branch_name: str) -> SceneState:
        """Switches the active branch and sets the active state to the branch's latest snapshot."""
        if branch_name not in self._branches:
            raise KeyError(f"Branch '{branch_name}' does not exist")
        self._current_branch = branch_name
        branch_shots = self._branches[branch_name]
        if branch_shots:
            last_shot_id = branch_shots[-1]
            last_snap = self._shots[last_shot_id]
            self._active_state = last_snap.state.model_copy(deep=True)
            self._timeline_clock = last_snap.timestamp
        self._pending_actions.clear()
        return self._active_state

    def rollback_to_shot(self, shot_id: str) -> SceneState:
        """Rolls back active scene state to a historic shot milestone."""
        if shot_id not in self._shots:
            raise KeyError(f"Shot '{shot_id}' not found in snapshots")
        snap = self._shots[shot_id]
        self._active_state = snap.state.model_copy(deep=True)
        self._timeline_clock = snap.timestamp
        self._pending_actions.clear()

        # Truncate current branch to this shot
        current_shots = self._branches[self._current_branch]
        if shot_id in current_shots:
            idx = current_shots.index(shot_id)
            self._branches[self._current_branch] = list(current_shots[: idx + 1])
        else:
            for b_name, b_shots in self._branches.items():
                if shot_id in b_shots:
                    idx = b_shots.index(shot_id)
                    self._branches[b_name] = list(b_shots[: idx + 1])
                    break

        return self._active_state

    def rollback_to(self, shot_id: str) -> SceneState:
        """Alias for rollback_to_shot."""
        return self.rollback_to_shot(shot_id)

    def list_branches(self) -> List[str]:
        """Returns list of all timeline branch names."""
        return list(self._branches.keys())

    def get_snapshot(self, shot_id: str) -> Optional[SceneSnapshot]:
        """Retrieves frozen snapshot for a shot ID."""
        return self._shots.get(shot_id)

    def get_shot(self, shot_id: str) -> Optional[SceneSnapshot]:
        """Alias for get_snapshot."""
        return self._shots.get(shot_id)

    def get_timeline(self, branch_name: Optional[str] = None) -> List[SceneSnapshot]:
        """Returns ordered sequence of snapshots on the requested branch (or current branch)."""
        branch = branch_name or self._current_branch
        shot_ids = self._branches.get(branch, [])
        return [self._shots[sid] for sid in shot_ids if sid in self._shots]
