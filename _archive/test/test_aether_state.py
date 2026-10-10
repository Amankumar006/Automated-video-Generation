"""Comprehensive Test Suite for Phase 2: Aether World Model (Scene State Graph).

Verifies Pydantic V2 scene schemas, multi-shot character tracking, prop handoffs,
wardrobe damage persistence, timeline branching and rollbacks, granular StateDelta
computations, ContinuityAuditor defect detections (teleportation, prop conservation,
wardrobe regression, reciprocal eyelines), and WorldStateStore persistence and query APIs.
(WBS 1.3).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys
import tempfile
import pytest
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
from aether.state.graph import AetherWorldModel
from aether.state.continuity import (
    ContinuityAuditor,
    ContinuityAuditResult,
    ContinuitySeverity,
    ContinuityViolation,
    ContinuityViolationType,
)
from aether.state.store import (
    CharacterMovementPoint,
    InjuryRecord,
    PropPossessionRecord,
    WardrobeRecord,
    WorldStateStore,
)


class TestSceneSchemas:
    """Verifies Pydantic V2 validation, aliases, edge cases, and defaults for schemas."""

    def test_character_state_valid_and_defaults(self):
        char = CharacterState(
            character_id="maya",
            name="Maya Lin",
            position=[1.0, 2.0, 3.0],
            facing_angle=90.0,
            eyeline_vector=[0.0, 0.0, 1.0],
        )
        assert char.id == "maya"
        assert char.character_id == "maya"
        assert char.name == "Maya Lin"
        assert char.position == [1.0, 2.0, 3.0]
        assert char.facing_angle == 90.0
        assert char.emotional_state == "neutral"
        assert char.wardrobe == {}
        assert char.injuries == []
        assert char.held_props == {}
        assert char.normalized_eyeline() == [0.0, 0.0, 1.0]

    def test_character_state_distance_calculation(self):
        c1 = CharacterState(character_id="c1", position=[0.0, 0.0, 0.0])
        c2 = CharacterState(character_id="c2", position=[3.0, 4.0, 0.0])
        assert c1.distance_to(c2) == pytest.approx(5.0)
        assert c1.distance_to([3.0, 4.0, 0.0]) == pytest.approx(5.0)

    def test_character_state_invalid_position_dimension(self):
        with pytest.raises(ValidationError):
            CharacterState(character_id="c1", position=[1.0, 2.0])  # Only 2 coordinates
        with pytest.raises(ValidationError):
            CharacterState(character_id="c1", position=[1.0, 2.0, 3.0, 4.0])

    def test_character_state_invalid_eyeline_zero_vector(self):
        with pytest.raises(ValidationError):
            CharacterState(character_id="c1", eyeline_vector=[0.0, 0.0, 0.0])

    def test_character_state_facing_angle_bounds(self):
        with pytest.raises(ValidationError):
            CharacterState(character_id="c1", facing_angle=-10.0)
        with pytest.raises(ValidationError):
            CharacterState(character_id="c1", facing_angle=361.0)

    def test_character_wardrobe_coercion(self):
        char = CharacterState(
            id="maya",
            wardrobe={
                "jacket": {"id": "leather_004", "state": "left_sleeve_torn", "damage_level": 0.6},
                "pants": "pristine",
                "boots": WardrobeItemState(id="boots_01", state="mud_splattered"),
            },
        )
        assert char.id == "maya"
        assert char.wardrobe["jacket"].state == "left_sleeve_torn"
        assert char.wardrobe["jacket"].damage_level == 0.6
        assert char.wardrobe["pants"].state == "pristine"
        assert char.wardrobe["boots"].state == "mud_splattered"

    def test_prop_state_fields_and_aliases(self):
        prop = PropState(
            prop_id="vial_01",
            name="Sample Vial",
            owner_id="maya",
            hand_attachment="right",
            physical_state="pristine",
        )
        assert prop.id == "vial_01"
        assert prop.holder_id == "maya"
        assert prop.hand_attachment == HandAttachment.RIGHT
        assert prop.is_held is True
        assert prop.world_coordinates is None

    def test_prop_state_world_position_unheld(self):
        prop = PropState(
            id="relic_99",
            name="Ancient Relic",
            position=[10.5, 0.0, -2.3],
            hand="none",
        )
        assert prop.id == "relic_99"
        assert prop.world_coordinates == [10.5, 0.0, -2.3]
        assert prop.owner_id is None
        assert prop.is_held is False

    def test_prop_state_invalid_coordinates(self):
        with pytest.raises(ValidationError):
            PropState(prop_id="p1", name="p", world_coordinates=[1.0, 2.0])

    def test_camera_state_validation_and_aliases(self):
        cam = CameraState(
            lens_focal_length_mm=50.0,
            aperture=1.8,
            position=[0.0, 1.2, -4.5],
            focus_distance=4.5,
        )
        assert cam.focal_length_mm == 50.0
        assert cam.focal_length == 50.0
        assert cam.lens_mm == 50.0
        assert cam.aperture == 1.8

        cam2 = CameraState(lens_mm=85.0)
        assert cam2.lens_focal_length_mm == 85.0

    def test_camera_state_invalid_values(self):
        with pytest.raises(ValidationError):
            CameraState(lens_focal_length_mm=0.0)
        with pytest.raises(ValidationError):
            CameraState(aperture=-1.0)

    def test_environment_state_normalization(self):
        env = EnvironmentState(
            weather="rain",
            wetness=0.85,
            lighting="emergency_red",
            floor={"wetness": 0.9, "reflections": True},
            global_lighting_vector=[0.0, -1.0, 0.0],
        )
        assert env.wetness == 0.9
        assert env.reflections is True
        assert env.global_lighting_vectors == [[0.0, -1.0, 0.0]]

    def test_scene_state_aliases_and_accessors(self):
        scene = SceneState(
            id="SC_014",
            location="abandoned_cleanroom",
            time="23:42",
            characters={
                "maya": CharacterState(character_id="maya", position=[3.2, 0.0, 6.7]),
            },
            props={
                "spectrometer": PropState(prop_id="spectrometer", name="Device", owner_id="maya", hand="right"),
            },
            camera=CameraState(lens_mm=35.0),
        )
        assert scene.id == "SC_014"
        assert scene.scene_id == "SC_014"
        assert scene.time_of_day == "23:42"
        assert "maya" in scene.characters
        assert "maya" in scene.character_roster
        assert "spectrometer" in scene.props
        assert scene.camera is not None
        assert scene.active_camera.lens_focal_length_mm == 35.0

    def test_scene_action_normalization(self):
        action = SceneAction(
            id="ACT_01",
            type="PROP_TRANSFER",
            actor_id="maya",
            target_id="bob",
            duration=1.5,
            metadata={"prop_id": "vial"},
        )
        assert action.action_id == "ACT_01"
        assert action.action_type == "PROP_TRANSFER"
        assert action.elapsed_seconds == 1.5


class TestAetherWorldModel:
    """Verifies world state engine, mutations, delta calculations, branching, and rollbacks."""

    def test_initial_state_and_defaults(self):
        wm = AetherWorldModel()
        assert wm.current_branch == "main"
        assert wm.active_state.scene_id == "SC_INIT"
        assert len(wm.shots) == 0
        assert len(wm.action_history) == 0

    def test_apply_character_move_action(self):
        maya = CharacterState(character_id="maya", position=[0.0, 0.0, 0.0], facing_angle=0.0)
        scene = SceneState(scene_id="SC_01", location="hangar", characters={"maya": maya})
        wm = AetherWorldModel(initial_state=scene)

        action = SceneAction(
            action_id="A1",
            action_type=ActionType.CHARACTER_MOVE,
            actor_id="maya",
            metadata={"position": [3.0, 0.0, 4.0], "facing_angle": 180.0, "eyeline_vector": [0.0, 0.0, -1.0]},
            elapsed_seconds=2.0,
        )
        wm.apply_action(action)

        updated_maya = wm.characters["maya"]
        assert updated_maya.position == [3.0, 0.0, 4.0]
        assert updated_maya.facing_angle == 180.0
        assert updated_maya.eyeline_vector == [0.0, 0.0, -1.0]
        assert wm._timeline_clock == 2.0
        assert len(wm.action_history) == 1

    def test_apply_prop_transfer_between_characters(self):
        maya = CharacterState(character_id="maya", held_props={"right": "decoder"})
        bob = CharacterState(character_id="bob")
        prop = PropState(prop_id="decoder", name="Code Decoder", owner_id="maya", hand_attachment="right")
        scene = SceneState(scene_id="SC_01", location="lab", characters={"maya": maya, "bob": bob}, props={"decoder": prop})
        wm = AetherWorldModel(initial_state=scene)

        action = SceneAction(
            action_id="A_HANDOFF",
            action_type=ActionType.PROP_TRANSFER,
            actor_id="maya",
            target_id="bob",
            metadata={"prop_id": "decoder", "recipient": "bob", "hand": "left"},
            elapsed_seconds=1.0,
        )
        wm.apply_action(action)

        # Decoder is now held by Bob in left hand
        p = wm.props["decoder"]
        assert p.owner_id == "bob"
        assert p.hand_attachment == HandAttachment.LEFT
        assert p.is_held is True
        assert wm.characters["bob"].held_props.get("left") == "decoder"
        assert "right" not in wm.characters["maya"].held_props

    def test_apply_prop_drop_to_world_and_pickup(self):
        maya = CharacterState(character_id="maya", held_props={"right": "keycard"})
        prop = PropState(prop_id="keycard", name="Keycard", owner_id="maya", hand_attachment="right")
        scene = SceneState(scene_id="SC_01", location="corridor", characters={"maya": maya}, props={"keycard": prop})
        wm = AetherWorldModel(initial_state=scene)

        # 1. Drop keycard to floor
        drop_action = SceneAction(
            action_id="A_DROP",
            action_type=ActionType.PROP_TRANSFER,
            actor_id="maya",
            metadata={"prop_id": "keycard", "drop": True, "position": [1.0, 0.0, 2.0]},
            elapsed_seconds=0.5,
        )
        wm.apply_action(drop_action)
        k = wm.props["keycard"]
        assert k.owner_id is None
        assert k.hand_attachment == HandAttachment.NONE
        assert k.is_held is False
        assert k.world_coordinates == [1.0, 0.0, 2.0]

        # 2. Pick up keycard
        pickup_action = SceneAction(
            action_id="A_PICKUP",
            action_type=ActionType.PROP_TRANSFER,
            actor_id="maya",
            metadata={"prop_id": "keycard", "recipient": "maya", "hand": "right"},
            elapsed_seconds=0.8,
        )
        wm.apply_action(pickup_action)
        assert k.owner_id == "maya"
        assert k.hand_attachment == HandAttachment.RIGHT
        assert k.is_held is True
        assert k.world_coordinates is None

    def test_apply_wardrobe_damage_mutation(self):
        maya = CharacterState(
            character_id="maya",
            wardrobe={"jacket": WardrobeItemState(id="leather_01", state="pristine", damage_level=0.0)},
        )
        scene = SceneState(scene_id="SC_01", location="alley", characters={"maya": maya})
        wm = AetherWorldModel(initial_state=scene)

        action = SceneAction(
            action_id="A_TEAR",
            action_type=ActionType.WARDROBE_MUTATION,
            actor_id="maya",
            metadata={"slot": "jacket", "state": "left_sleeve_torn", "damage_level": 0.75},
            elapsed_seconds=0.5,
        )
        wm.apply_action(action)

        jacket = wm.characters["maya"].wardrobe["jacket"]
        assert jacket.state == "left_sleeve_torn"
        assert jacket.damage_level == 0.75

    def test_apply_environment_change(self):
        scene = SceneState(scene_id="SC_01", location="courtyard")
        wm = AetherWorldModel(initial_state=scene)

        action = SceneAction(
            action_id="A_ENV",
            action_type=ActionType.ENVIRONMENT_CHANGE,
            metadata={"weather": "storm", "wetness": 0.8, "particulates": "heavy_rain", "lighting": "lightning_flash"},
            elapsed_seconds=1.0,
        )
        wm.apply_action(action)

        env = wm.active_state.environment
        assert env.weather == "storm"
        assert env.wetness == 0.8
        assert env.particulates == "heavy_rain"
        assert env.lighting == "lightning_flash"

    def test_freeze_shot_and_immutability(self):
        maya = CharacterState(character_id="maya", position=[0.0, 0.0, 0.0])
        scene = SceneState(scene_id="SC_01", location="stage", characters={"maya": maya})
        wm = AetherWorldModel(initial_state=scene)

        snap1 = wm.freeze_shot("SHOT_001")
        assert snap1.shot_id == "SHOT_001"
        assert snap1.state.characters["maya"].position == [0.0, 0.0, 0.0]

        # Mutate active state after freeze
        wm.apply_action(
            SceneAction(
                action_id="A2",
                action_type=ActionType.CHARACTER_MOVE,
                actor_id="maya",
                metadata={"position": [10.0, 0.0, 10.0]},
                elapsed_seconds=2.0,
            )
        )
        snap2 = wm.freeze_shot("SHOT_002")

        # Snapshot 1 remains immutable!
        assert snap1.state.characters["maya"].position == [0.0, 0.0, 0.0]
        assert snap2.state.characters["maya"].position == [10.0, 0.0, 10.0]
        assert wm.shots["SHOT_001"].state.characters["maya"].position == [0.0, 0.0, 0.0]

    def test_state_delta_computation(self):
        maya = CharacterState(
            character_id="maya",
            position=[0.0, 0.0, 0.0],
            facing_angle=0.0,
            emotional_state="calm",
            wardrobe={"jacket": WardrobeItemState(id="j1", state="pristine")},
        )
        cam = CameraState(lens_mm=35.0, aperture=2.8, position=[0.0, 1.5, -3.0], focus_distance=3.0)
        prop = PropState(prop_id="p1", name="Relic", owner_id="maya", hand="right")
        scene = SceneState(scene_id="SC_01", location="chamber", characters={"maya": maya}, props={"p1": prop}, camera=cam)
        wm = AetherWorldModel(initial_state=scene)
        wm.freeze_shot("SHOT_A")

        # Apply multi-factor action
        move_action = SceneAction(
            action_id="ACT_M",
            action_type=ActionType.CHARACTER_MOVE,
            actor_id="maya",
            metadata={"position": [3.0, 4.0, 0.0], "facing_angle": 90.0},
            elapsed_seconds=2.0,
        )
        tear_action = SceneAction(
            action_id="ACT_T",
            action_type=ActionType.WARDROBE_MUTATION,
            actor_id="maya",
            metadata={"slot": "jacket", "state": "torn", "damage_level": 0.8},
        )
        cam_action = SceneAction(
            action_id="ACT_C",
            action_type=ActionType.CAMERA_MOVE,
            metadata={"lens_focal_length_mm": 50.0},
        )
        wm.apply_actions([move_action, tear_action, cam_action])
        wm.freeze_shot("SHOT_B")

        delta = wm.compute_delta("SHOT_A", "SHOT_B")
        assert delta.shot_a_id == "SHOT_A"
        assert delta.shot_b_id == "SHOT_B"
        assert delta.elapsed_seconds == 2.0
        assert delta.has_changes is True

        char_delta = delta.character_deltas["maya"]
        assert char_delta.distance_moved == pytest.approx(5.0)
        assert char_delta.velocity_mps == pytest.approx(2.5)
        assert char_delta.facing_angle_delta == 90.0
        assert char_delta.wardrobe_changes["jacket"] == ("pristine", "torn")

        assert delta.camera_delta is not None
        assert delta.camera_delta.focal_length_delta == pytest.approx(15.0)

    def test_timeline_branching_and_rollback(self):
        maya = CharacterState(character_id="maya", position=[0.0, 0.0, 0.0])
        scene = SceneState(scene_id="SC_01", location="crossroads", characters={"maya": maya})
        wm = AetherWorldModel(initial_state=scene)
        wm.freeze_shot("SHOT_01")

        # Step forward to Shot 2
        wm.apply_action(
            SceneAction(
                action_id="A_LEFT",
                action_type=ActionType.CHARACTER_MOVE,
                actor_id="maya",
                metadata={"position": [-5.0, 0.0, 0.0]},
                elapsed_seconds=1.0,
            )
        )
        wm.freeze_shot("SHOT_02")
        assert wm.active_state.characters["maya"].position == [-5.0, 0.0, 0.0]

        # Branch timeline from Shot 01: "right_turn_branch"
        wm.create_branch("right_turn_branch", from_shot_id="SHOT_01")
        assert wm.current_branch == "right_turn_branch"
        assert wm.active_state.characters["maya"].position == [0.0, 0.0, 0.0]

        # Move right on new branch
        wm.apply_action(
            SceneAction(
                action_id="A_RIGHT",
                action_type=ActionType.CHARACTER_MOVE,
                actor_id="maya",
                metadata={"position": [5.0, 0.0, 0.0]},
                elapsed_seconds=1.0,
            )
        )
        wm.freeze_shot("SHOT_02_ALT")
        assert wm.active_state.characters["maya"].position == [5.0, 0.0, 0.0]

        # Switch back to main branch
        wm.checkout_branch("main")
        assert wm.current_branch == "main"
        assert wm.active_state.characters["maya"].position == [-5.0, 0.0, 0.0]

        # Test rollback on main branch back to SHOT_01
        wm.rollback_to_shot("SHOT_01")
        assert wm.active_state.characters["maya"].position == [0.0, 0.0, 0.0]
        assert wm.branches["main"] == ["SHOT_01"]


class TestContinuityAuditor:
    """Verifies detection of unphysical velocities, prop violations, wardrobe regressions, and eyelines."""

    @pytest.fixture
    def auditor(self):
        return ContinuityAuditor(
            max_character_speed_mps=10.0,
            instant_move_tolerance_m=0.05,
            reciprocal_eyeline_tolerance_deg=35.0,
        )

    def test_clean_shot_transition_passes(self, auditor):
        char_a = CharacterState(character_id="maya", position=[0.0, 0.0, 0.0])
        char_b = CharacterState(character_id="maya", position=[4.0, 0.0, 0.0])
        prop_a = PropState(prop_id="vial", name="Vial", owner_id="maya", hand="right")
        prop_b = PropState(prop_id="vial", name="Vial", owner_id="maya", hand="right")

        shot_a = SceneState(scene_id="S1", location="hall", characters={"maya": char_a}, props={"vial": prop_a})
        shot_b = SceneState(scene_id="S2", location="hall", characters={"maya": char_b}, props={"vial": prop_b})

        result = auditor.audit_transition(shot_a, shot_b, elapsed_seconds=2.0)  # 2.0 m/s
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_teleportation_instantaneous_displacement(self, auditor):
        char_a = CharacterState(character_id="maya", position=[0.0, 0.0, 0.0])
        char_b = CharacterState(character_id="maya", position=[3.5, 0.0, 0.0])

        shot_a = SceneState(scene_id="S1", location="room", characters={"maya": char_a})
        shot_b = SceneState(scene_id="S2", location="room", characters={"maya": char_b})

        # Elapsed time is 0.0s (instantaneous cut)
        result = auditor.audit_transition(shot_a, shot_b, elapsed_seconds=0.0)
        assert result.is_valid is False
        assert result.has_violation_of_type(ContinuityViolationType.TELEPORTATION)
        v = result.violations[0]
        assert v.severity == ContinuitySeverity.CRITICAL
        assert "3.50m with 0.0s elapsed" in v.message

    def test_unphysical_velocity_exceeds_threshold(self, auditor):
        char_a = CharacterState(character_id="maya", position=[0.0, 0.0, 0.0])
        char_b = CharacterState(character_id="maya", position=[30.0, 0.0, 0.0])

        shot_a = SceneState(scene_id="S1", location="room", characters={"maya": char_a})
        shot_b = SceneState(scene_id="S2", location="room", characters={"maya": char_b})

        # 30 meters in 1.0s = 30 m/s > 10 m/s threshold
        result = auditor.audit_transition(shot_a, shot_b, elapsed_seconds=1.0)
        assert result.is_valid is False
        assert result.has_violation_of_type(ContinuityViolationType.UNPHYSICAL_VELOCITY)
        v = result.violations[0]
        assert v.severity == ContinuitySeverity.ERROR
        assert "30.00 m/s exceeds max threshold" in v.message

    def test_prop_conservation_vanishing_prop(self, auditor):
        prop_a = PropState(prop_id="device", name="Scanner", owner_id="maya", hand="right")
        char_a = CharacterState(character_id="maya")
        char_b = CharacterState(character_id="maya")

        shot_a = SceneState(scene_id="S1", location="lab", characters={"maya": char_a}, props={"device": prop_a})
        shot_b = SceneState(scene_id="S2", location="lab", characters={"maya": char_b}, props={})  # Missing prop!

        result = auditor.audit_transition(shot_a, shot_b, elapsed_seconds=1.0)
        assert result.is_valid is False
        assert result.has_violation_of_type(ContinuityViolationType.PROP_CONSERVATION)
        v = [v for v in result.violations if v.violation_type == ContinuityViolationType.PROP_CONSERVATION][0]
        assert v.severity == ContinuitySeverity.CRITICAL
        assert "vanished in Shot B" in v.message

    def test_prop_conservation_appearing_prop(self, auditor):
        char_a = CharacterState(character_id="maya")
        char_b = CharacterState(character_id="maya")
        prop_b = PropState(prop_id="gun", name="Plasma Gun", owner_id="maya", hand="right")

        shot_a = SceneState(scene_id="S1", location="lab", characters={"maya": char_a}, props={})
        shot_b = SceneState(scene_id="S2", location="lab", characters={"maya": char_b}, props={"gun": prop_b})

        result = auditor.audit_transition(shot_a, shot_b, elapsed_seconds=1.0)
        assert result.is_valid is False
        assert result.has_violation_of_type(ContinuityViolationType.PROP_CONSERVATION)
        assert "appeared in Shot B without an introductory action" in result.violations[0].message

    def test_prop_conservation_hand_switch_without_action(self, auditor):
        prop_a = PropState(prop_id="scanner", name="Scanner", owner_id="maya", hand="right")
        prop_b = PropState(prop_id="scanner", name="Scanner", owner_id="maya", hand="left")  # Switched hands!
        char_a = CharacterState(character_id="maya")
        char_b = CharacterState(character_id="maya")

        shot_a = SceneState(scene_id="S1", location="lab", characters={"maya": char_a}, props={"scanner": prop_a})
        shot_b = SceneState(scene_id="S2", location="lab", characters={"maya": char_b}, props={"scanner": prop_b})

        result = auditor.audit_transition(shot_a, shot_b, actions=[], elapsed_seconds=1.0)
        assert result.is_valid is False
        assert result.has_violation_of_type(ContinuityViolationType.PROP_CONSERVATION)
        assert "without an explicit PROP_TRANSFER action" in result.violations[0].message

    def test_prop_transfer_with_action_passes(self, auditor):
        prop_a = PropState(prop_id="scanner", name="Scanner", owner_id="maya", hand="right")
        prop_b = PropState(prop_id="scanner", name="Scanner", owner_id="bob", hand="left")
        char_a = CharacterState(character_id="maya")
        char_b = CharacterState(character_id="bob")

        shot_a = SceneState(scene_id="S1", location="lab", characters={"maya": char_a, "bob": char_b}, props={"scanner": prop_a})
        shot_b = SceneState(scene_id="S2", location="lab", characters={"maya": char_a, "bob": char_b}, props={"scanner": prop_b})

        transfer_act = SceneAction(
            action_id="A_TRANS",
            action_type=ActionType.PROP_TRANSFER,
            actor_id="maya",
            target_id="bob",
            metadata={"prop_id": "scanner", "recipient": "bob", "hand": "left"},
            elapsed_seconds=1.0,
        )
        result = auditor.audit_transition(shot_a, shot_b, actions=[transfer_act], elapsed_seconds=1.0)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_wardrobe_regression_torn_to_pristine(self, auditor):
        char_a = CharacterState(
            character_id="maya",
            wardrobe={"jacket": WardrobeItemState(id="j1", state="left_sleeve_torn", damage_level=0.8)},
        )
        char_b = CharacterState(
            character_id="maya",
            wardrobe={"jacket": WardrobeItemState(id="j1", state="pristine", damage_level=0.0)},
        )

        shot_a = SceneState(scene_id="S1", location="alley", characters={"maya": char_a})
        shot_b = SceneState(scene_id="S2", location="alley", characters={"maya": char_b})

        result = auditor.audit_transition(shot_a, shot_b, actions=[], elapsed_seconds=1.0)
        assert result.is_valid is False
        assert result.has_violation_of_type(ContinuityViolationType.WARDROBE_REGRESSION)
        v = [v for v in result.violations if v.violation_type == ContinuityViolationType.WARDROBE_REGRESSION][0]
        assert "regressed from damaged state 'left_sleeve_torn' to pristine state 'pristine'" in v.message

    def test_wardrobe_repair_with_action_passes(self, auditor):
        char_a = CharacterState(
            character_id="maya",
            wardrobe={"jacket": WardrobeItemState(id="j1", state="left_sleeve_torn", damage_level=0.8)},
        )
        char_b = CharacterState(
            character_id="maya",
            wardrobe={"jacket": WardrobeItemState(id="j1", state="pristine", damage_level=0.0)},
        )

        shot_a = SceneState(scene_id="S1", location="tailor", characters={"maya": char_a})
        shot_b = SceneState(scene_id="S2", location="tailor", characters={"maya": char_b})

        repair_act = SceneAction(
            action_id="A_REP",
            action_type=ActionType.WARDROBE_MUTATION,
            actor_id="maya",
            metadata={"slot": "jacket", "action": "repair", "is_repair": True},
            elapsed_seconds=5.0,
        )
        result = auditor.audit_transition(shot_a, shot_b, actions=[repair_act], elapsed_seconds=5.0)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_reciprocal_eyeline_aligned_passes(self, auditor):
        # Maya at [0, 0, 0] looking toward [0, 0, 5] -> eyeline [0, 0, 1]
        maya = CharacterState(character_id="maya", position=[0.0, 0.0, 0.0], eyeline_vector=[0.0, 0.0, 1.0])
        # Bob at [0, 0, 5] looking toward [0, 0, 0] -> eyeline [0, 0, -1]
        bob = CharacterState(character_id="bob", position=[0.0, 0.0, 5.0], eyeline_vector=[0.0, 0.0, -1.0])

        violation = auditor.check_reciprocal_eyeline(maya, bob)
        assert violation is None

    def test_reciprocal_eyeline_broken_flags_violation(self, auditor):
        # Maya looking at Bob with eyeline [0, 0, 1]
        maya = CharacterState(character_id="maya", position=[0.0, 0.0, 0.0], eyeline_vector=[0.0, 0.0, 1.0])
        # Bob looking AWAY from Maya with eyeline [0, 0, 1] (same direction!)
        bob = CharacterState(character_id="bob", position=[0.0, 0.0, 5.0], eyeline_vector=[0.0, 0.0, 1.0])

        violation = auditor.check_reciprocal_eyeline(maya, bob)
        assert violation is not None
        assert violation.violation_type == ContinuityViolationType.RECIPROCAL_EYELINE
        assert violation.severity == ContinuitySeverity.ERROR
        assert "Reciprocal eyeline violation" in violation.message

    def test_reciprocal_eyeline_perpendicular_flags_violation(self, auditor):
        maya = CharacterState(character_id="maya", position=[0.0, 0.0, 0.0], eyeline_vector=[0.0, 0.0, 1.0])
        bob = CharacterState(character_id="bob", position=[0.0, 0.0, 5.0], eyeline_vector=[1.0, 0.0, 0.0])  # 90 degrees away

        violation = auditor.check_reciprocal_eyeline(maya, bob)
        assert violation is not None
        assert violation.violation_type == ContinuityViolationType.RECIPROCAL_EYELINE

    def test_audit_shots_entire_timeline(self, auditor):
        # 3-shot sequence: Shot 1 clean, Shot 2 clean, Shot 3 has teleportation
        maya = CharacterState(character_id="maya", position=[0.0, 0.0, 0.0])
        scene = SceneState(scene_id="SC_01", location="hall", characters={"maya": maya})
        wm = AetherWorldModel(initial_state=scene)
        wm.freeze_shot("SHOT_1")

        # Shot 1 -> Shot 2: walks 2m in 2s (valid)
        wm.apply_action(
            SceneAction(
                action_id="A_WALK",
                action_type=ActionType.CHARACTER_MOVE,
                actor_id="maya",
                metadata={"position": [2.0, 0.0, 0.0]},
                elapsed_seconds=2.0,
            )
        )
        wm.freeze_shot("SHOT_2")

        # Shot 2 -> Shot 3: teleports 100m in 0.5s (invalid)
        wm.apply_action(
            SceneAction(
                action_id="A_WARP",
                action_type=ActionType.CHARACTER_MOVE,
                actor_id="maya",
                metadata={"position": [102.0, 0.0, 0.0]},
                elapsed_seconds=0.5,
            )
        )
        wm.freeze_shot("SHOT_3")

        results = auditor.audit_shots(wm)
        assert len(results) == 2
        # Transition 1 -> 2 passes
        assert results[0].shot_a_id == "SHOT_1"
        assert results[0].shot_b_id == "SHOT_2"
        assert results[0].is_valid is True
        # Transition 2 -> 3 fails
        assert results[1].shot_a_id == "SHOT_2"
        assert results[1].shot_b_id == "SHOT_3"
        assert results[1].is_valid is False
        assert results[1].has_violation_of_type(ContinuityViolationType.UNPHYSICAL_VELOCITY)


class TestWorldStateStore:
    """Verifies persistence, JSON serialization, query API, and production state ledger."""

    def test_json_serialization_and_roundtrip(self):
        maya = CharacterState(
            character_id="maya",
            name="Maya",
            position=[1.2, 0.0, 3.4],
            wardrobe={"jacket": WardrobeItemState(id="leather", state="torn")},
        )
        prop = PropState(prop_id="p1", name="Relic", owner_id="maya", hand="right")
        cam = CameraState(lens_mm=50.0, aperture=2.0)
        scene = SceneState(scene_id="SC_TEST", location="bunker", characters={"maya": maya}, props={"p1": prop}, camera=cam)

        wm = AetherWorldModel(initial_state=scene)
        wm.freeze_shot("SHOT_01")

        # Mutate
        wm.apply_action(
            SceneAction(
                action_id="A1",
                action_type=ActionType.CHARACTER_MOVE,
                actor_id="maya",
                metadata={"position": [2.0, 0.0, 4.0]},
                elapsed_seconds=1.0,
            )
        )
        wm.freeze_shot("SHOT_02")

        # Serialize
        json_str = WorldStateStore.to_json(wm)
        assert "SC_TEST" in json_str
        assert "SHOT_01" in json_str
        assert "SHOT_02" in json_str

        # Deserialize
        restored = WorldStateStore.from_json(json_str)
        assert restored.active_state.scene_id == "SC_TEST"
        assert len(restored.shots) == 2
        assert restored.shots["SHOT_01"].state.characters["maya"].position == [1.2, 0.0, 3.4]
        assert restored.shots["SHOT_02"].state.characters["maya"].position == [2.0, 0.0, 4.0]

    def test_save_and_load_file(self):
        maya = CharacterState(character_id="maya", position=[0.0, 0.0, 0.0])
        scene = SceneState(scene_id="SC_SAVE", location="vault", characters={"maya": maya})
        wm = AetherWorldModel(initial_state=scene)
        wm.freeze_shot("SHOT_INIT")

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "world_state.json"
            saved_path = WorldStateStore.save(wm, file_path)
            assert saved_path.exists()

            loaded_wm = WorldStateStore.load(saved_path)
            assert loaded_wm.shots["SHOT_INIT"].state.characters["maya"].position == [0.0, 0.0, 0.0]

    def test_query_prop_possession_history(self):
        maya = CharacterState(character_id="maya", held_props={"right": "amulet"})
        bob = CharacterState(character_id="bob")
        prop = PropState(prop_id="amulet", name="Ancient Amulet", owner_id="maya", hand="right")
        scene = SceneState(scene_id="SC_01", location="temple", characters={"maya": maya, "bob": bob}, props={"amulet": prop})

        wm = AetherWorldModel(initial_state=scene)
        wm.freeze_shot("SHOT_1")

        # Transfer to Bob
        wm.apply_action(
            SceneAction(
                action_id="A_TR",
                action_type=ActionType.PROP_TRANSFER,
                actor_id="maya",
                target_id="bob",
                metadata={"prop_id": "amulet", "recipient": "bob", "hand": "left"},
                elapsed_seconds=2.0,
            )
        )
        wm.freeze_shot("SHOT_2")

        # Drop to floor
        wm.apply_action(
            SceneAction(
                action_id="A_DR",
                action_type=ActionType.PROP_TRANSFER,
                actor_id="bob",
                metadata={"prop_id": "amulet", "drop": True, "position": [1.5, 0.0, 3.0]},
                elapsed_seconds=1.0,
            )
        )
        wm.freeze_shot("SHOT_3")

        history = WorldStateStore.query_prop_possession_history(wm, "amulet")
        assert len(history) == 3
        # Shot 1: Maya holding in right hand
        assert history[0].shot_id == "SHOT_1"
        assert history[0].owner_id == "maya"
        assert history[0].hand_attachment == "right"
        assert history[0].is_held is True

        # Shot 2: Bob holding in left hand
        assert history[1].shot_id == "SHOT_2"
        assert history[1].owner_id == "bob"
        assert history[1].hand_attachment == "left"
        assert history[1].is_held is True

        # Shot 3: Dropped on floor
        assert history[2].shot_id == "SHOT_3"
        assert history[2].owner_id is None
        assert history[2].is_held is False
        assert history[2].world_coordinates == [1.5, 0.0, 3.0]

    def test_query_character_movement_path(self):
        maya = CharacterState(character_id="maya", position=[0.0, 0.0, 0.0])
        scene = SceneState(scene_id="SC_01", location="plaza", characters={"maya": maya})
        wm = AetherWorldModel(initial_state=scene)
        wm.freeze_shot("SHOT_1")

        # Move to (3, 4, 0) in 2 seconds (5m / 2s = 2.5 m/s)
        wm.apply_action(
            SceneAction(
                action_id="A_MV",
                action_type=ActionType.CHARACTER_MOVE,
                actor_id="maya",
                metadata={"position": [3.0, 4.0, 0.0]},
                elapsed_seconds=2.0,
            )
        )
        wm.freeze_shot("SHOT_2")

        path = WorldStateStore.query_character_movement_path(wm, "maya")
        assert len(path) == 2
        assert path[0].position == [0.0, 0.0, 0.0]
        assert path[0].distance_from_previous == 0.0
        assert path[1].position == [3.0, 4.0, 0.0]
        assert path[1].distance_from_previous == pytest.approx(5.0)
        assert path[1].velocity_from_previous == pytest.approx(2.5)

    def test_query_wardrobe_and_injury_history(self):
        maya = CharacterState(
            character_id="maya",
            wardrobe={"jacket": WardrobeItemState(id="j1", state="pristine")},
            injuries=[],
        )
        scene = SceneState(scene_id="SC_01", location="alley", characters={"maya": maya})
        wm = AetherWorldModel(initial_state=scene)
        wm.freeze_shot("SHOT_1")

        wm.apply_action(
            SceneAction(
                action_id="A_DMG",
                action_type=ActionType.WARDROBE_MUTATION,
                actor_id="maya",
                metadata={"slot": "jacket", "state": "torn", "damage_level": 0.5},
            )
        )
        wm.apply_action(
            SceneAction(
                action_id="A_INJ",
                action_type=ActionType.INJURY_ADDED,
                actor_id="maya",
                metadata={"injury": "cut_arm_left"},
            )
        )
        wm.freeze_shot("SHOT_2")

        w_history = WorldStateStore.query_wardrobe_history(wm, "maya", garment_slot="jacket")
        assert len(w_history) == 2
        assert w_history[0].state == "pristine"
        assert w_history[1].state == "torn"

        inj_history = WorldStateStore.query_injuries_history(wm, "maya")
        assert len(inj_history) == 2
        assert inj_history[0].injuries == []
        assert inj_history[1].injuries == ["cut_arm_left"]

    def test_export_state_ledger(self):
        maya = CharacterState(character_id="maya", position=[1.0, 0.0, 2.0])
        prop = PropState(prop_id="flare", name="Flare", owner_id="maya", hand="right")
        cam = CameraState(lens_mm=35.0)
        scene = SceneState(scene_id="SC_01", location="runway", characters={"maya": maya}, props={"flare": prop}, camera=cam)
        wm = AetherWorldModel(initial_state=scene)
        wm.freeze_shot("SHOT_1")

        ledger = WorldStateStore.export_state_ledger(wm)
        assert ledger["ledger_version"] == "2.0"
        assert ledger["active_branch"] == "main"
        assert ledger["total_shots"] == 1
        assert "maya" in ledger["characters_summary"]
        assert "flare" in ledger["props_summary"]
        assert len(ledger["timeline_shots"]) == 1
        assert ledger["timeline_shots"][0]["shot_id"] == "SHOT_1"


class TestEdgeCasesAndStress:
    """Verifies edge cases: empty states, coincident positions, zero-time cuts, multiple branches."""

    def test_empty_scene_state(self):
        empty_scene = SceneState(scene_id="EMPTY_01", location="void")
        wm = AetherWorldModel(initial_state=empty_scene)
        snap = wm.freeze_shot("SHOT_VOID")
        assert len(snap.state.character_roster) == 0
        assert len(snap.state.prop_roster) == 0

        auditor = ContinuityAuditor()
        result = auditor.audit_transition(snap.state, snap.state, elapsed_seconds=1.0)
        assert result.is_valid is True
        assert len(result.violations) == 0

    def test_characters_at_coincident_positions(self):
        # Characters located at the exact same spatial coordinate
        c1 = CharacterState(character_id="c1", position=[2.0, 0.0, 2.0], eyeline_vector=[0.0, 0.0, 1.0])
        c2 = CharacterState(character_id="c2", position=[2.0, 0.0, 2.0], eyeline_vector=[0.0, 0.0, -1.0])
        auditor = ContinuityAuditor()
        # Coincident position distance is < 0.001, eyelines are inverse ([0,0,1] and [0,0,-1])
        violation = auditor.check_reciprocal_eyeline(c1, c2)
        assert violation is None

    def test_multiple_divergent_branches(self):
        maya = CharacterState(character_id="maya", position=[0.0, 0.0, 0.0])
        wm = AetherWorldModel(initial_state=SceneState(scene_id="BASE", location="lab", characters={"maya": maya}))
        wm.freeze_shot("SHOT_BASE")

        for b_name in ("branch_alpha", "branch_beta", "branch_gamma"):
            wm.create_branch(b_name, from_shot_id="SHOT_BASE")
            wm.apply_action(
                SceneAction(
                    action_id=f"A_{b_name}",
                    action_type=ActionType.CHARACTER_MOVE,
                    actor_id="maya",
                    metadata={"position": [float(len(b_name)), 0.0, 0.0]},
                )
            )
            wm.freeze_shot(f"SHOT_{b_name}")

        branches = wm.list_branches()
        assert "main" in branches
        assert "branch_alpha" in branches
        assert "branch_beta" in branches
        assert "branch_gamma" in branches

        # Verify independence of branch alpha
        alpha_shots = wm.get_timeline("branch_alpha")
        assert len(alpha_shots) == 2
        assert alpha_shots[1].shot_id == "SHOT_branch_alpha"


class TestContinuityAuditorHardening:
    """Verifies edge cases and bug fixes for ContinuityAuditor."""

    @pytest.fixture
    def auditor(self):
        return ContinuityAuditor(
            max_character_speed_mps=10.0,
            instant_move_tolerance_m=0.05,
            reciprocal_eyeline_tolerance_deg=35.0,
        )

    def test_prop_transfer_wrong_recipient_flagged(self, auditor):
        """If action transfers prop to Charlie, but Bob ends up with it, flag violation."""
        c_alice = CharacterState(character_id="alice", position=[0.0, 0.0, 0.0])
        c_bob = CharacterState(character_id="bob", position=[2.0, 0.0, 0.0])
        c_charlie = CharacterState(character_id="charlie", position=[4.0, 0.0, 0.0])
        prop_a = PropState(prop_id="keycard", name="Keycard", owner_id="alice", hand="right")

        shot_a = SceneState(
            scene_id="SC_A",
            location="hall",
            characters={"alice": c_alice, "bob": c_bob, "charlie": c_charlie},
            props={"keycard": prop_a},
        )

        # Action: Alice transfers keycard to Charlie
        transfer_act = SceneAction(
            action_id="ACT_T1",
            action_type=ActionType.PROP_TRANSFER,
            actor_id="alice",
            target_id="charlie",
            metadata={"prop_id": "keycard", "recipient": "charlie"},
            elapsed_seconds=1.0,
        )

        # Shot B: Keycard erroneously possessed by Bob!
        prop_b = PropState(prop_id="keycard", name="Keycard", owner_id="bob", hand="right")
        shot_b = SceneState(
            scene_id="SC_B",
            location="hall",
            characters={"alice": c_alice, "bob": c_bob, "charlie": c_charlie},
            props={"keycard": prop_b},
        )

        result = auditor.audit_transition(shot_a, shot_b, actions=[transfer_act], elapsed_seconds=1.0)
        assert result.is_valid is False
        assert result.has_violation_of_type(ContinuityViolationType.PROP_CONSERVATION)
        assert any("actions transferred it to 'charlie'" in v.message for v in result.violations)

    def test_prop_transfer_hand_mismatch_flagged(self, auditor):
        """If action specifies left hand, but prop is in right hand in Shot B, flag violation."""
        c_alice = CharacterState(character_id="alice", position=[0.0, 0.0, 0.0])
        c_bob = CharacterState(character_id="bob", position=[2.0, 0.0, 0.0])
        prop_a = PropState(prop_id="dagger", name="Dagger", owner_id="alice", hand="right")

        shot_a = SceneState(
            scene_id="SC_A",
            location="armory",
            characters={"alice": c_alice, "bob": c_bob},
            props={"dagger": prop_a},
        )

        # Action: transfer to bob specifying LEFT hand
        transfer_act = SceneAction(
            action_id="ACT_T2",
            action_type=ActionType.PROP_TRANSFER,
            actor_id="alice",
            target_id="bob",
            metadata={"prop_id": "dagger", "recipient": "bob", "hand": "left"},
            elapsed_seconds=1.0,
        )

        # Shot B: Bob holds dagger in RIGHT hand
        prop_b = PropState(prop_id="dagger", name="Dagger", owner_id="bob", hand="right")
        shot_b = SceneState(
            scene_id="SC_B",
            location="armory",
            characters={"alice": c_alice, "bob": c_bob},
            props={"dagger": prop_b},
        )

        result = auditor.audit_transition(shot_a, shot_b, actions=[transfer_act], elapsed_seconds=1.0)
        assert result.is_valid is False
        assert result.has_violation_of_type(ContinuityViolationType.PROP_CONSERVATION)
        assert any("specified 'left' hand" in v.message for v in result.violations)

    def test_unheld_prop_teleportation_flagged(self, auditor):
        """Unheld prop moved 10m instantaneously without an action must be caught."""
        prop_a = PropState(prop_id="cup", name="Coffee Cup", world_coordinates=[0.0, 1.0, 0.0])
        prop_b = PropState(prop_id="cup", name="Coffee Cup", world_coordinates=[10.0, 1.0, 0.0])

        shot_a = SceneState(scene_id="SC_A", location="cafe", props={"cup": prop_a})
        shot_b = SceneState(scene_id="SC_B", location="cafe", props={"cup": prop_b})

        result = auditor.audit_transition(shot_a, shot_b, actions=[], elapsed_seconds=0.0)
        assert result.is_valid is False
        assert result.has_violation_of_type(ContinuityViolationType.PROP_CONSERVATION)
        assert any("Unheld prop 'cup'" in v.message for v in result.violations)

    def test_wardrobe_repair_slot_specificity(self, auditor):
        """Repairing jacket only must NOT allow pants to regress to pristine without violation."""
        c_a = CharacterState(
            character_id="alice",
            position=[0.0, 0.0, 0.0],
            wardrobe={
                "jacket": WardrobeItemState(id="jacket", state="torn", damage_level=0.9),
                "pants": WardrobeItemState(id="pants", state="torn", damage_level=0.8),
            },
        )
        # In Shot B, both jacket and pants are pristine!
        c_b = CharacterState(
            character_id="alice",
            position=[0.0, 0.0, 0.0],
            wardrobe={
                "jacket": WardrobeItemState(id="jacket", state="pristine", damage_level=0.0),
                "pants": WardrobeItemState(id="pants", state="pristine", damage_level=0.0),
            },
        )

        shot_a = SceneState(scene_id="SC_A", location="dressing_room", characters={"alice": c_a})
        shot_b = SceneState(scene_id="SC_B", location="dressing_room", characters={"alice": c_b})

        # Action: specifically repairs jacket ONLY
        repair_jacket = SceneAction(
            action_id="ACT_R1",
            action_type=ActionType.WARDROBE_REPAIR,
            actor_id="alice",
            metadata={"slot": "jacket", "action": "repair"},
            elapsed_seconds=10.0,
        )

        result = auditor.audit_transition(shot_a, shot_b, actions=[repair_jacket], elapsed_seconds=10.0)
        assert result.is_valid is False
        assert result.has_violation_of_type(ContinuityViolationType.WARDROBE_REGRESSION)
        # Jacket should pass, pants must be flagged
        pants_violations = [v for v in result.violations if "pants" in v.entity_id]
        assert len(pants_violations) == 1
        jacket_violations = [v for v in result.violations if "jacket" in v.entity_id]
        assert len(jacket_violations) == 0

    def test_injury_healing_specificity(self, auditor):
        """Treating bruise only must NOT allow broken_arm to disappear silently."""
        c_a = CharacterState(
            character_id="alice",
            position=[0.0, 0.0, 0.0],
            injuries=["bruise", "broken_arm"],
        )
        c_b = CharacterState(
            character_id="alice",
            position=[0.0, 0.0, 0.0],
            injuries=[],  # both disappeared!
        )

        shot_a = SceneState(scene_id="SC_A", location="clinic", characters={"alice": c_a})
        shot_b = SceneState(scene_id="SC_B", location="clinic", characters={"alice": c_b})

        heal_bruise = SceneAction(
            action_id="ACT_H1",
            action_type=ActionType.HEALING,
            actor_id="alice",
            metadata={"injury": "bruise", "healed": True},
            elapsed_seconds=5.0,
        )

        result = auditor.audit_transition(shot_a, shot_b, actions=[heal_bruise], elapsed_seconds=5.0)
        # broken_arm vanishing without action generates warning/violation
        injury_violations = [v for v in result.violations if v.violation_type == ContinuityViolationType.INJURY_REGRESSION]
        assert len(injury_violations) == 1
        assert "broken_arm" in injury_violations[0].message

    def test_reciprocal_eyeline_autodetect_dialogue_pair(self, auditor):
        """Auto-detection must catch broken eyeline when Maya looks at Bob, but Bob looks away."""
        maya_b = CharacterState(
            character_id="maya",
            position=[0.0, 0.0, 0.0],
            eyeline_vector=[0.0, 0.0, 1.0],  # Looking directly at Bob
        )
        bob_b = CharacterState(
            character_id="bob",
            position=[0.0, 0.0, 4.0],
            eyeline_vector=[1.0, 0.0, 0.0],  # Looking 90 degrees away from Maya!
        )

        shot_a = SceneState(scene_id="SC_A", location="lounge", characters={"maya": maya_b, "bob": bob_b})
        shot_b = SceneState(scene_id="SC_B", location="lounge", characters={"maya": maya_b, "bob": bob_b})

        # No metadata pair supplied - auditor must auto-detect that Maya is looking at Bob
        result = auditor.audit_transition(shot_a, shot_b, actions=[], elapsed_seconds=1.0)
        assert result.is_valid is False
        assert result.has_violation_of_type(ContinuityViolationType.RECIPROCAL_EYELINE)


class TestWorldModelMutations:
    """Verifies AetherWorldModel action dispatch, spawns, consumes, deltas, and branching."""

    def test_prop_spawned_and_consumed(self):
        wm = AetherWorldModel(initial_state=SceneState(scene_id="SC_01", location="room"))
        assert len(wm.active_state.prop_roster) == 0

        # Spawn prop
        spawn_act = SceneAction(
            action_id="SPAWN_1",
            action_type=ActionType.PROP_SPAWNED,
            target_id="torch",
            metadata={"name": "Torch", "world_coordinates": [1.0, 1.0, 0.0], "physical_state": "burning"},
        )
        wm.apply_action(spawn_act)
        assert "torch" in wm.active_state.prop_roster
        assert wm.active_state.prop_roster["torch"].physical_state == "burning"

        # Consume prop
        consume_act = SceneAction(
            action_id="CONSUME_1",
            action_type=ActionType.PROP_CONSUMED,
            target_id="torch",
            metadata={"reason": "used_up"},
        )
        wm.apply_action(consume_act)
        assert "torch" not in wm.active_state.prop_roster

    def test_wardrobe_repair_and_healing_mutations(self):
        char = CharacterState(
            character_id="maya",
            position=[0.0, 0.0, 0.0],
            wardrobe={"boots": WardrobeItemState(id="boots", state="muddy", damage_level=0.5)},
            injuries=["scraped_knee"],
        )
        wm = AetherWorldModel(initial_state=SceneState(scene_id="SC_01", location="camp", characters={"maya": char}))

        # Repair boots
        repair_act = SceneAction(
            action_id="R_1",
            action_type=ActionType.WARDROBE_REPAIR,
            actor_id="maya",
            metadata={"slot": "boots", "new_state": "pristine", "damage_level": 0.0},
        )
        wm.apply_action(repair_act)
        assert wm.active_state.character_roster["maya"].wardrobe["boots"].state == "pristine"
        assert wm.active_state.character_roster["maya"].wardrobe["boots"].damage_level == 0.0

        # Heal scraped_knee
        heal_act = SceneAction(
            action_id="H_1",
            action_type=ActionType.HEALING,
            actor_id="maya",
            metadata={"injury": "scraped_knee"},
        )
        wm.apply_action(heal_act)
        assert "scraped_knee" not in wm.active_state.character_roster["maya"].injuries

    def test_state_delta_with_entering_exiting_entities(self):
        c1 = CharacterState(character_id="c1", position=[0.0, 0.0, 0.0])
        p1 = PropState(prop_id="p1", name="Box", world_coordinates=[0.0, 0.0, 0.0])
        state_a = SceneState(scene_id="A", location="lab", characters={"c1": c1}, props={"p1": p1})

        c2 = CharacterState(character_id="c2", position=[5.0, 0.0, 0.0])
        p2 = PropState(prop_id="p2", name="Sphere", world_coordinates=[5.0, 0.0, 0.0])
        # In state B: c1 exited, c2 entered; p1 consumed, p2 spawned
        state_b = SceneState(scene_id="B", location="lab", characters={"c2": c2}, props={"p2": p2})

        delta = AetherWorldModel.compute_delta_between_states(state_a, state_b)
        assert delta.has_changes is True
        assert "c2" in delta.characters_entered
        assert "c1" in delta.characters_exited
        assert "p2" in delta.props_spawned
        assert "p1" in delta.props_consumed

    def test_freeze_shot_duplicate_id_raises_value_error(self):
        wm = AetherWorldModel(initial_state=SceneState(scene_id="SC_01", location="hall"))
        wm.freeze_shot("SHOT_UNIQUE")
        with pytest.raises(ValueError, match="already"):
            wm.freeze_shot("SHOT_UNIQUE")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

