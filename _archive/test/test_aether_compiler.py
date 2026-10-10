"""Comprehensive Test Suite for Phase 3: Complexity Planner & Shot Compiler (WBS 1.4).

Verifies:
1. Pydantic V2 compiler schemas (ComplexityLevel, ShotRequirement, SpatialRepresentationPackage, CompiledModelPayload).
2. ComplexityPlanner classification across all 6 levels (Levels 0 through 5) based on actor count, camera velocity,
   physical challenges (fluids, grapples), prop handoffs, and continuity sensitivity.
3. ShotCompiler translations across all 4 target model families:
   - Google Veo 3.1 (cinematic prompt, native audio flags, first/last keyframes).
   - Kling 3.0 (motion brush, element tracking, lip-sync audio, duration modes).
   - Runway Gen-4.5 (Director Mode camera prompt syntax, image references).
   - CogVideoX / HunyuanVideo ComfyUI (ControlNet Canny/OpenPose/Depth/Normals, latent dimensions, LoRAs, node graph).
4. Automated capability routing (compile_auto) and preferred provider overrides.
5. End-to-end integration with AetherWorldModel, frozen SceneSnapshots, and StateDelta mutations.
6. Edge case and error handling validation.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import pytest
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from aether.compiler.schemas import (
    AudioRequirement,
    ComplexityLevel,
    ComplexityPlan,
    CompiledModelPayload,
    ComputeTier,
    ProviderTarget,
    ShotRequirement,
    ShotSlice,
    SpatialRepresentationPackage,
)
from aether.compiler.complexity import ComplexityPlanner
from aether.compiler.compiler import ShotCompiler
from aether.state.schemas import (
    ActionType,
    CameraState,
    CharacterState,
    EnvironmentState,
    HandAttachment,
    PropState,
    SceneAction,
    SceneSnapshot,
    SceneState,
    WardrobeItemState,
)
from aether.state.graph import AetherWorldModel


# ---------------------------------------------------------------------------
# Test Fixtures & Utilities
# ---------------------------------------------------------------------------

@pytest.fixture
def empty_scene() -> SceneState:
    """Atmospheric environmental scene with zero characters and zero props."""
    return SceneState(
        scene_id="SC_001",
        location="dune_sea_vista",
        timestamp="sunset",
        environment=EnvironmentState(
            weather="clear",
            lighting="golden_hour_warm",
            wetness=0.0,
            particulates="fine_sand_drift",
            reflections=False,
        ),
        active_camera=CameraState(
            lens_focal_length_mm=24.0,
            aperture=8.0,
            position=[0.0, 10.0, -50.0],
            focus_distance=50.0,
        ),
    )


@pytest.fixture
def portrait_scene() -> SceneState:
    """Single-actor portrait scene."""
    char = CharacterState(
        character_id="maya",
        name="Maya Lin",
        position=[0.0, 0.0, 2.0],
        facing_angle=0.0,
        eyeline_vector=[0.0, 0.0, -1.0],
        emotional_state="hyper-vigilant",
        wardrobe={
            "jacket": WardrobeItemState(id="leather_004", state="pristine", damage_level=0.0)
        },
    )
    return SceneState(
        scene_id="SC_PORTRAIT",
        location="minimalist_studio",
        timestamp="14:00",
        environment=EnvironmentState(weather="indoor", lighting="three_point_cinematic"),
        character_roster={"maya": char},
        active_camera=CameraState(
            lens_focal_length_mm=85.0,
            aperture=1.8,
            position=[0.0, 1.5, 0.0],
            focus_distance=2.0,
        ),
    )


@pytest.fixture
def two_character_handoff_scene() -> SceneState:
    """Two characters in close proximity with a prop."""
    maya = CharacterState(
        character_id="maya",
        name="Maya Lin",
        position=[1.0, 0.0, 2.0],
        facing_angle=90.0,
        eyeline_vector=[-1.0, 0.0, 0.0],
        emotional_state="resolute",
        wardrobe={
            "jacket": WardrobeItemState(id="leather_004", state="left_sleeve_torn", damage_level=0.4)
        },
        injuries=["blood_cheek_right"],
        held_props={"right": "spectrometer_device_01"},
    )
    elena = CharacterState(
        character_id="elena",
        name="Elena Rostova",
        position=[2.2, 0.0, 2.0],
        facing_angle=270.0,
        eyeline_vector=[1.0, 0.0, 0.0],
        emotional_state="concerned",
    )
    prop = PropState(
        prop_id="spectrometer_device_01",
        name="Spectrometer Device",
        owner_id="maya",
        hand_attachment=HandAttachment.RIGHT,
        physical_state="pristine",
    )
    return SceneState(
        scene_id="SC_HANDOFF",
        location="abandoned_cleanroom",
        timestamp="23:42",
        environment=EnvironmentState(
            weather="overcast",
            lighting="emergency_red_pulsing",
            wetness=0.85,
            particulates="steam_leak",
            reflections=True,
        ),
        character_roster={"maya": maya, "elena": elena},
        prop_roster={"spectrometer_device_01": prop},
        active_camera=CameraState(
            lens_focal_length_mm=35.0,
            aperture=2.8,
            position=[1.6, 1.4, -0.5],
            focus_distance=2.5,
        ),
    )


@pytest.fixture
def sample_spatial_package() -> SpatialRepresentationPackage:
    """Fully populated spatial representation package."""
    return SpatialRepresentationPackage(
        clay_render_uri="https://storage.aether.studio/renders/shot_001_clay.png",
        photoreal_ref_uri="https://storage.aether.studio/renders/shot_001_photoreal.png",
        depth_map_uri="https://storage.aether.studio/depth/shot_001_depth.exr",
        surface_normals_uri="https://storage.aether.studio/normals/shot_001_normals.exr",
        segmentation_masks={
            "maya": "https://storage.aether.studio/masks/shot_001_maya.png",
            "spectrometer_device_01": "https://storage.aether.studio/masks/shot_001_prop.png",
        },
        motion_vectors_uri="https://storage.aether.studio/flow/shot_001_flow.exr",
        camera_trajectory_path="https://storage.aether.studio/camera/shot_001_cam.json",
        skeleton_pose_metadata={
            "maya": {"head": [100, 200], "neck": [100, 250], "left_hand": [80, 400]}
        },
    )


# ---------------------------------------------------------------------------
# 1. Compiler Schemas Tests
# ---------------------------------------------------------------------------

class TestCompilerSchemas:
    """Verifies Pydantic V2 schemas, enum members, conversions, and aliases."""

    def test_complexity_level_enum_values(self):
        """ComplexityLevel must correctly define Levels 0 to 5."""
        assert ComplexityLevel.PROMPT_ONLY == 0
        assert ComplexityLevel.REFERENCE_IMAGE == 1
        assert ComplexityLevel.KEYFRAMES_INTERPOLATION == 2
        assert ComplexityLevel.TWOD_TRAJECTORY_POSE == 3
        assert ComplexityLevel.THREED_BLOCKING == 4
        assert ComplexityLevel.FULL_PHYSICAL_SIMULATION == 5

        # Ordering comparisons
        assert ComplexityLevel.FULL_PHYSICAL_SIMULATION > ComplexityLevel.THREED_BLOCKING
        assert ComplexityLevel.PROMPT_ONLY < ComplexityLevel.REFERENCE_IMAGE

    def test_complexity_level_aliases(self):
        """Enum aliases (LEVEL_0, LEVEL_4_3D_BLOCKING, etc.) must match canonical members."""
        assert ComplexityLevel.LEVEL_0 == ComplexityLevel.PROMPT_ONLY
        assert ComplexityLevel.LEVEL_1 == ComplexityLevel.REFERENCE_IMAGE
        assert ComplexityLevel.LEVEL_2 == ComplexityLevel.KEYFRAMES_INTERPOLATION
        assert ComplexityLevel.LEVEL_3 == ComplexityLevel.TWOD_TRAJECTORY_POSE
        assert ComplexityLevel.LEVEL_4 == ComplexityLevel.THREED_BLOCKING
        assert ComplexityLevel.LEVEL_5 == ComplexityLevel.FULL_PHYSICAL_SIMULATION

        assert ComplexityLevel.LEVEL_0_TEXT_ONLY == ComplexityLevel.PROMPT_ONLY
        assert ComplexityLevel.LEVEL_4_3D_BLOCKING == ComplexityLevel.THREED_BLOCKING
        assert ComplexityLevel.LEVEL_5_DETERMINISTIC_SIM == ComplexityLevel.FULL_PHYSICAL_SIMULATION

    def test_complexity_level_from_val(self):
        """from_val must parse integers, strings, and fuzzy names cleanly."""
        assert ComplexityLevel.from_val(0) == ComplexityLevel.PROMPT_ONLY
        assert ComplexityLevel.from_val(5) == ComplexityLevel.FULL_PHYSICAL_SIMULATION
        assert ComplexityLevel.from_val("PROMPT_ONLY") == ComplexityLevel.PROMPT_ONLY
        assert ComplexityLevel.from_val("level_4") == ComplexityLevel.THREED_BLOCKING
        assert ComplexityLevel.from_val("3D_BLOCKING") == ComplexityLevel.THREED_BLOCKING
        assert ComplexityLevel.from_val("simulation") == ComplexityLevel.FULL_PHYSICAL_SIMULATION
        assert ComplexityLevel.from_val("KEYFRAMES") == ComplexityLevel.KEYFRAMES_INTERPOLATION

        with pytest.raises(ValueError, match="Cannot parse"):
            ComplexityLevel.from_val("unknown_level_xyz")

    def test_complexity_level_metadata_properties(self):
        """label and description properties return informative documentation."""
        assert "Level 0" in ComplexityLevel.PROMPT_ONLY.label
        assert "Level 5" in ComplexityLevel.FULL_PHYSICAL_SIMULATION.label
        assert len(ComplexityLevel.THREED_BLOCKING.description) > 10

    def test_provider_target_and_compute_tier(self):
        """ProviderTarget and ComputeTier enums and helper methods."""
        assert ProviderTarget.VEO_3_1 == "veo_3_1"
        assert ProviderTarget.KLING_3_0 == "kling_3_0"
        assert ProviderTarget.RUNWAY_GEN_4_5 == "runway_gen_4_5"
        assert ProviderTarget.COGVIDEOX_COMFYUI == "cogvideox_comfyui"

        assert ProviderTarget.from_val("veo") == ProviderTarget.VEO_3_1
        assert ProviderTarget.from_val("kling") == ProviderTarget.KLING_3_0
        assert ProviderTarget.from_val("runway") == ProviderTarget.RUNWAY_GEN_4_5
        assert ProviderTarget.from_val("comfyui") == ProviderTarget.COGVIDEOX_COMFYUI

        with pytest.raises(ValueError, match="Unknown video provider"):
            ProviderTarget.from_val("non_existent_provider")

        assert ComputeTier.STANDARD == "standard"
        assert ComputeTier.DEDICATED_A100 == "dedicated_a100"
        assert ComputeTier.CLOUD_SERVERLESS == "cloud_serverless"

    def test_audio_requirement_normalization(self):
        """AudioRequirement normalizes dictionary keys and defaults."""
        audio = AudioRequirement()
        assert not audio.dialogue
        assert not audio.foley
        assert not audio.score

        # Dict normalization
        audio2 = AudioRequirement(
            has_dialogue=True,
            transcript="Hold your fire!",
            has_foley=True,
            score_genre="synthwave suspense",
        )
        assert audio2.dialogue
        assert audio2.dialogue_transcript == "Hold your fire!"
        assert audio2.foley
        assert audio2.score_mood == "synthwave suspense"

    def test_shot_requirement_validation_and_aliases(self):
        """ShotRequirement validates duration and accepts standard aliases."""
        req = ShotRequirement(
            shot_id="SHOT_042",
            duration=4.5,
            aspect_ratio="2.39:1",
            resolution="4k",
            characters=["maya", "elena"],
            focal_intent="rack focus to spectrometer",
            has_handoff=True,
            dialogue=True,
            dialogue_transcript="Take the device.",
        )

        assert req.shot_id == "SHOT_042"
        assert req.target_duration == 4.5
        assert req.duration == 4.5
        assert req.aspect_ratio == "2.39:1"
        assert req.resolution == "4k"
        assert req.character_ids_involved == ["maya", "elena"]
        assert req.characters_involved == ["maya", "elena"]
        assert req.target_focal_intent == "rack focus to spectrometer"
        assert req.has_prop_handoff
        assert req.has_dialogue
        assert req.audio.dialogue_transcript == "Take the device."

        # Duration validation
        with pytest.raises(ValidationError):
            ShotRequirement(target_duration=0.0)
        with pytest.raises(ValidationError):
            ShotRequirement(target_duration=-2.5)

    def test_spatial_representation_package_helpers(self, sample_spatial_package):
        """SpatialRepresentationPackage property helpers and aliases."""
        pkg = sample_spatial_package
        assert pkg.has_clay_render
        assert pkg.has_photoreal_ref
        assert pkg.has_depth
        assert pkg.has_normals
        assert pkg.has_motion_vectors
        assert pkg.has_camera_trajectory
        assert pkg.has_skeleton_poses
        assert pkg.has_segmentation_masks
        assert not pkg.is_empty
        assert pkg.optical_flow_uri == pkg.motion_vectors_uri

        empty_pkg = SpatialRepresentationPackage()
        assert empty_pkg.is_empty
        assert not empty_pkg.has_depth

    def test_compiled_model_payload_serialization(self):
        """CompiledModelPayload converts cleanly to dict and JSON."""
        payload = CompiledModelPayload(
            shot_id="SHOT_TEST",
            provider_target=ProviderTarget.VEO_3_1,
            prompt="Cinematic shot in desert.",
            negative_prompt="low quality",
            reference_images=["https://ref.png"],
            camera_motion_parameters={"pan": 1.0},
            provider_config={"model": "veo-3.1"},
            required_compute_tier=ComputeTier.CLOUD_SERVERLESS,
            duration_seconds=5.0,
            aspect_ratio="16:9",
            resolution="1080p",
            complexity_level=ComplexityLevel.KEYFRAMES_INTERPOLATION,
        )

        d = payload.to_api_payload()
        assert d["provider"] == "veo_3_1"
        assert d["prompt"] == "Cinematic shot in desert."
        assert d["compute_tier"] == "cloud_serverless"

        json_str = payload.to_json()
        parsed = json.loads(json_str)
        assert parsed["provider"] == "veo_3_1"
        assert parsed["duration"] == 5.0


# ---------------------------------------------------------------------------
# 2. Complexity Planner Tests (Levels 0 through 5)
# ---------------------------------------------------------------------------

class TestComplexityPlanner:
    """Verifies ComplexityPlanner classification rules across all 6 complexity tiers."""

    def test_level_0_prompt_only(self, empty_scene):
        """Level 0: Zero actors, no props, ambient atmosphere."""
        planner = ComplexityPlanner()
        req = ShotRequirement(
            shot_id="SHOT_L0",
            target_duration=4.0,
            camera_movement="static",
        )

        plan = planner.plan(empty_scene, req)
        assert plan.complexity_level == ComplexityLevel.PROMPT_ONLY
        assert plan.recommended_representations == []
        assert plan.recommended_provider == ProviderTarget.VEO_3_1
        assert any("No characters" in r for r in plan.rationale)

    def test_level_1_reference_image(self, portrait_scene):
        """Level 1: Single actor, static portrait, stationary camera."""
        planner = ComplexityPlanner()
        req = ShotRequirement(
            shot_id="SHOT_L1",
            target_duration=3.0,
            characters=["maya"],
            camera_movement="static",
            camera_velocity_mps=0.0,
        )

        plan = planner.plan(portrait_scene, req)
        assert plan.complexity_level == ComplexityLevel.REFERENCE_IMAGE
        assert plan.recommended_representations == ["photoreal_ref"]
        assert plan.recommended_provider == ProviderTarget.RUNWAY_GEN_4_5
        assert any("Single static actor portrait" in r for r in plan.rationale)

    def test_level_2_keyframes_interpolation(self, portrait_scene):
        """Level 2: Camera pan with single actor."""
        planner = ComplexityPlanner()
        req = ShotRequirement(
            shot_id="SHOT_L2",
            target_duration=5.0,
            characters=["maya"],
            camera_movement="pan_right",
            camera_velocity_mps=1.2,
        )

        plan = planner.plan(portrait_scene, req)
        assert plan.complexity_level == ComplexityLevel.KEYFRAMES_INTERPOLATION
        assert "first_frame" in plan.recommended_representations
        assert "last_frame" in plan.recommended_representations
        assert plan.recommended_provider == ProviderTarget.VEO_3_1
        assert any("camera movement" in r.lower() for r in plan.rationale)

    def test_level_2_continuity_escalation(self, portrait_scene):
        """Level 2: Single static actor escalated from Level 1 due to continuity_critical."""
        planner = ComplexityPlanner()
        req = ShotRequirement(
            shot_id="SHOT_L2_CONT",
            target_duration=3.0,
            characters=["maya"],
            camera_movement="static",
            continuity_critical=True,
        )

        plan = planner.plan(portrait_scene, req)
        assert plan.complexity_level == ComplexityLevel.KEYFRAMES_INTERPOLATION
        assert any("Continuity" in r for r in plan.rationale)

    def test_level_3_twod_trajectory_dialogue(self, portrait_scene):
        """Level 3: Character with dialogue requires 2D trajectory & lip-sync."""
        planner = ComplexityPlanner()
        req = ShotRequirement(
            shot_id="SHOT_L3_DIALOGUE",
            target_duration=5.0,
            characters=["maya"],
            audio=AudioRequirement(
                dialogue=True,
                dialogue_transcript="The signal is getting stronger.",
            ),
        )

        plan = planner.plan(portrait_scene, req)
        assert plan.complexity_level == ComplexityLevel.TWOD_TRAJECTORY_POSE
        assert "skeleton_pose_metadata" in plan.recommended_representations
        assert plan.recommended_provider == ProviderTarget.KLING_3_0
        assert any("dialogue" in r.lower() for r in plan.rationale)

    def test_level_3_twod_trajectory_walking(self, portrait_scene):
        """Level 3: Character walking towards camera."""
        planner = ComplexityPlanner()
        req = ShotRequirement(
            shot_id="SHOT_L3_WALK",
            target_duration=5.0,
            characters=["maya"],
            camera_movement="tracking",
        )

        plan = planner.plan(portrait_scene, req)
        assert plan.complexity_level == ComplexityLevel.TWOD_TRAJECTORY_POSE

    def test_level_4_threed_blocking_handoff(self, two_character_handoff_scene):
        """Level 4: Prop handoff between two characters requires 3D geometric previs."""
        planner = ComplexityPlanner()
        req = ShotRequirement(
            shot_id="SHOT_L4_HANDOFF",
            target_duration=5.0,
            characters=["maya", "elena"],
            has_handoff=True,
            emotional_beat="tense transfer of device",
        )

        plan = planner.plan(two_character_handoff_scene, req)
        assert plan.complexity_level == ComplexityLevel.THREED_BLOCKING
        assert "clay_render" in plan.recommended_representations
        assert "depth_map" in plan.recommended_representations
        assert "camera_trajectory" in plan.recommended_representations
        assert any("Prop handoff" in r for r in plan.rationale)

    def test_level_4_threed_blocking_crane_multi_actor(self, two_character_handoff_scene):
        """Level 4: Camera crane trajectory with multiple actors in scene."""
        planner = ComplexityPlanner()
        req = ShotRequirement(
            shot_id="SHOT_L4_CRANE",
            target_duration=6.0,
            characters=["maya", "elena"],
            camera_movement="crane_up",
            camera_velocity_mps=2.5,
        )

        plan = planner.plan(two_character_handoff_scene, req)
        assert plan.complexity_level == ComplexityLevel.THREED_BLOCKING

    def test_level_5_full_physical_simulation_fluids(self, two_character_handoff_scene):
        """Level 5: Physical challenge involving fluid dynamics."""
        planner = ComplexityPlanner()
        req = ShotRequirement(
            shot_id="SHOT_L5_FLUIDS",
            target_duration=4.0,
            characters=["maya"],
            physical_challenges=["fluids", "water_splash_impact"],
        )

        plan = planner.plan(two_character_handoff_scene, req)
        assert plan.complexity_level == ComplexityLevel.FULL_PHYSICAL_SIMULATION
        assert "surface_normals" in plan.recommended_representations
        assert "skeleton_pose_metadata" in plan.recommended_representations
        assert plan.recommended_provider == ProviderTarget.COGVIDEOX_COMFYUI
        assert any("Fluid dynamics" in r for r in plan.rationale)

    def test_level_5_full_physical_simulation_grapple_stunt(self, two_character_handoff_scene):
        """Level 5: Stunt collision or martial grapple."""
        planner = ComplexityPlanner()
        req = ShotRequirement(
            shot_id="SHOT_L5_STUNT",
            target_duration=3.5,
            characters=["maya", "elena"],
            physical_challenges=["grapple", "rigid_body_collision"],
        )

        plan = planner.plan(two_character_handoff_scene, req)
        assert plan.complexity_level == ComplexityLevel.FULL_PHYSICAL_SIMULATION
        assert any("collision" in r.lower() or "grapple" in r.lower() for r in plan.rationale)

    def test_classify_convenience_method(self, empty_scene):
        """classify() returns only ComplexityLevel enum."""
        planner = ComplexityPlanner()
        lvl = planner.classify(empty_scene)
        assert isinstance(lvl, ComplexityLevel)
        assert lvl == ComplexityLevel.PROMPT_ONLY


# ---------------------------------------------------------------------------
# 3. Shot Compiler Tests (All 4 Model Families)
# ---------------------------------------------------------------------------

class TestShotCompiler:
    """Verifies ShotCompiler translations into provider payloads."""

    def test_compile_for_veo(self, two_character_handoff_scene, sample_spatial_package):
        """Veo 3.1: first/last frames, cinematic prompt, native audio flags."""
        compiler = ShotCompiler()
        req = ShotRequirement(
            shot_id="SHOT_VEO_01",
            target_duration=5.0,
            aspect_ratio="16:9",
            resolution="1080p",
            characters=["maya", "elena"],
            audio=AudioRequirement(
                dialogue=True,
                dialogue_transcript="Take the scanner and run.",
                foley=True,
                foley_cues=["heavy footsteps", "steam hiss"],
                score=True,
                score_mood="intense pulsing synth",
            ),
            target_focal_intent="focus on Maya's injured face",
            camera_movement="pan_right",
        )

        payload = compiler.compile_for_veo(
            two_character_handoff_scene,
            req,
            spatial_package=sample_spatial_package,
        )

        assert payload.provider_target == ProviderTarget.VEO_3_1
        assert payload.required_compute_tier == ComputeTier.CLOUD_SERVERLESS
        assert payload.duration_seconds == 5.0
        assert payload.aspect_ratio == "16:9"

        # Check prompt contents
        assert "abandoned cleanroom" in payload.prompt.lower()
        assert "emergency red pulsing" in payload.prompt.lower()
        assert "maya" in payload.prompt.lower()
        assert "left sleeve torn" in payload.prompt.lower()
        assert "blood cheek right" in payload.prompt.lower()
        assert "spectrometer" in payload.prompt.lower()

        # Check audio flags in provider config
        config = payload.provider_config
        assert config["model"] == "veo-3.1"
        assert config["generate_audio"] is True
        assert "Take the scanner and run." in config["audio_prompt"]
        assert "steam hiss" in config["audio_prompt"]
        assert "intense pulsing synth" in config["audio_prompt"]

        # Check frames
        assert payload.first_frame_uri == sample_spatial_package.photoreal_ref_uri

    def test_compile_for_kling(self, two_character_handoff_scene, sample_spatial_package):
        """Kling 3.0: dynamic motion brush element tracking, lip-sync audio, duration."""
        compiler = ShotCompiler()
        req = ShotRequirement(
            shot_id="SHOT_KLING_01",
            target_duration=5.0,
            aspect_ratio="9:16",
            characters=["maya"],
            audio=AudioRequirement(
                dialogue=True,
                dialogue_transcript="Initiating sequence.",
                dialogue_audio_uri="https://storage.aether.studio/audio/maya_line.wav",
            ),
        )

        payload = compiler.compile_for_kling(
            two_character_handoff_scene,
            req,
            spatial_package=sample_spatial_package,
        )

        assert payload.provider_target == ProviderTarget.KLING_3_0
        assert payload.required_compute_tier == ComputeTier.PREMIUM
        assert payload.aspect_ratio == "9:16"

        config = payload.provider_config
        assert config["model_version"] == "kling-v3-0"
        assert config["mode"] == "pro"
        assert config["duration"] == 5.0

        # Element tracking from segmentation masks
        motion_brush = config["motion_brush_elements"]
        assert len(motion_brush) >= 1
        assert any(e["element_id"] == "maya" for e in motion_brush)

        # Lip sync configuration
        lip_sync = config["lip_sync"]
        assert lip_sync["enabled"] is True
        assert lip_sync["audio_uri"] == "https://storage.aether.studio/audio/maya_line.wav"
        assert lip_sync["transcript"] == "Initiating sequence."

    def test_compile_for_runway(self, portrait_scene):
        """Runway Gen-4.5: Director Mode camera prompt syntax [Camera: ...] and image references."""
        compiler = ShotCompiler()
        req = ShotRequirement(
            shot_id="SHOT_RUNWAY_01",
            target_duration=4.0,
            characters=["maya"],
            camera_movement="pan_right",
            camera_velocity_mps=2.0,
        )

        payload = compiler.compile_for_runway(portrait_scene, req)
        assert payload.provider_target == ProviderTarget.RUNWAY_GEN_4_5
        assert payload.required_compute_tier == ComputeTier.PREMIUM

        # Director Mode camera syntax in prompt
        assert "[Camera:" in payload.prompt
        assert "Pan Right" in payload.prompt

        config = payload.provider_config
        assert config["model"] == "gen4.5"
        assert "director_mode" in config
        assert config["director_mode"]["pan"] > 0.0

    def test_compile_for_comfyui(self, two_character_handoff_scene, sample_spatial_package):
        """CogVideoX / Hunyuan ComfyUI: ControlNet nodes, latent dimensions, LoRAs, node graph."""
        compiler = ShotCompiler()
        req = ShotRequirement(
            shot_id="SHOT_COMFY_01",
            target_duration=5.0,
            resolution="1080p",
            aspect_ratio="16:9",
            characters=["maya", "elena"],
        )

        payload = compiler.compile_for_comfyui(
            two_character_handoff_scene,
            req,
            spatial_package=sample_spatial_package,
        )

        assert payload.provider_target == ProviderTarget.COGVIDEOX_COMFYUI
        assert payload.required_compute_tier == ComputeTier.DEDICATED_A100

        config = payload.provider_config
        assert config["base_model"] == "CogVideoX-5B"

        # Check ControlNets from spatial package
        cn_configs = config["controlnet_configs"]
        assert len(cn_configs) >= 4
        types_present = {c["control_type"] for c in cn_configs}
        assert "depth" in types_present
        assert "surface_normals" in types_present
        assert "canny" in types_present
        assert "openpose" in types_present

        # Latent dimensions
        latents = config["latent_dimensions"]
        assert latents["width"] == 1920
        assert latents["height"] == 1080
        assert latents["num_frames"] == 120
        assert latents["latent_width"] == 1920 // 8
        assert latents["latent_height"] == 1080 // 8

        # ComfyUI Workflow Graph
        workflow = config["comfyui_workflow"]
        assert "1" in workflow
        assert workflow["1"]["class_type"] == "CogVideoXModelLoader"
        assert any(n["class_type"] == "KSampler" for n in workflow.values())
        assert any(n["class_type"] == "VHS_VideoCombine" for n in workflow.values())


# ---------------------------------------------------------------------------
# 4. Automated Routing (compile_auto) Tests
# ---------------------------------------------------------------------------

class TestAutomatedRouting:
    """Verifies compile_auto capability-based routing and preferred provider overrides."""

    def test_auto_route_level_0_to_veo(self, empty_scene):
        """Level 0 routes to Google Veo 3.1."""
        compiler = ShotCompiler()
        req = ShotRequirement(target_duration=4.0, camera_movement="static")
        payload = compiler.compile_auto(empty_scene, req)
        assert payload.provider_target == ProviderTarget.VEO_3_1
        assert payload.complexity_level == ComplexityLevel.PROMPT_ONLY

    def test_auto_route_level_1_to_runway(self, portrait_scene):
        """Level 1 static portrait routes to Runway Gen-4.5."""
        compiler = ShotCompiler()
        req = ShotRequirement(characters=["maya"], camera_movement="static")
        payload = compiler.compile_auto(portrait_scene, req)
        assert payload.provider_target == ProviderTarget.RUNWAY_GEN_4_5
        assert payload.complexity_level == ComplexityLevel.REFERENCE_IMAGE

    def test_auto_route_level_3_dialogue_to_kling(self, portrait_scene):
        """Level 3 dialogue routes to Kling 3.0."""
        compiler = ShotCompiler()
        req = ShotRequirement(
            characters=["maya"],
            audio=AudioRequirement(dialogue=True, dialogue_transcript="Look at that."),
        )
        payload = compiler.compile_auto(portrait_scene, req)
        assert payload.provider_target == ProviderTarget.KLING_3_0
        assert payload.complexity_level == ComplexityLevel.TWOD_TRAJECTORY_POSE

    def test_auto_route_level_4_with_spatial_pkg_to_comfyui(self, two_character_handoff_scene, sample_spatial_package):
        """Level 4 with spatial package passes routes to CogVideoX ComfyUI."""
        compiler = ShotCompiler()
        req = ShotRequirement(
            characters=["maya", "elena"],
            has_handoff=True,
        )
        payload = compiler.compile_auto(
            two_character_handoff_scene,
            req,
            spatial_package=sample_spatial_package,
        )
        assert payload.provider_target == ProviderTarget.COGVIDEOX_COMFYUI
        assert payload.complexity_level == ComplexityLevel.THREED_BLOCKING

    def test_auto_route_level_5_to_comfyui(self, two_character_handoff_scene):
        """Level 5 full physical simulation strictly routes to CogVideoX ComfyUI."""
        compiler = ShotCompiler()
        req = ShotRequirement(
            characters=["maya"],
            physical_challenges=["fluids", "water_jet"],
        )
        payload = compiler.compile_auto(two_character_handoff_scene, req)
        assert payload.provider_target == ProviderTarget.COGVIDEOX_COMFYUI
        assert payload.complexity_level == ComplexityLevel.FULL_PHYSICAL_SIMULATION

    def test_auto_route_preferred_provider_override(self, empty_scene):
        """preferred_provider overrides the automatic routing."""
        compiler = ShotCompiler()
        req = ShotRequirement(target_duration=4.0)

        # Force Runway on a Level 0 scene
        payload = compiler.compile_auto(empty_scene, req, preferred_provider="runway_gen_4_5")
        assert payload.provider_target == ProviderTarget.RUNWAY_GEN_4_5

        # Force Kling
        payload_kling = compiler.compile_auto(empty_scene, req, preferred_provider=ProviderTarget.KLING_3_0)
        assert payload_kling.provider_target == ProviderTarget.KLING_3_0


# ---------------------------------------------------------------------------
# 5. Integration with AetherWorldModel and StateDelta Tests
# ---------------------------------------------------------------------------

class TestIntegrationWithWorldModel:
    """Verifies integration with AetherWorldModel mutations, frozen snapshots, and StateDelta."""

    def test_world_model_snapshot_and_delta_integration(self):
        """Simulate multi-shot cut, freeze snapshots, calculate delta, and compile shot."""
        # Setup initial state in AetherWorldModel
        maya = CharacterState(
            character_id="maya",
            name="Maya Lin",
            position=[0.0, 0.0, 0.0],
            facing_angle=0.0,
            emotional_state="calm",
            wardrobe={"jacket": WardrobeItemState(id="leather_004", state="pristine")},
        )
        elena = CharacterState(
            character_id="elena",
            name="Elena Rostova",
            position=[5.0, 0.0, 0.0],
            facing_angle=180.0,
            emotional_state="neutral",
        )
        prop = PropState(
            prop_id="pda_01",
            name="Data PDA",
            owner_id="maya",
            hand_attachment=HandAttachment.RIGHT,
        )
        init_state = SceneState(
            scene_id="SC_EP01",
            location="hangar_bay",
            timestamp="night",
            environment=EnvironmentState(weather="rain", lighting="dim_fluorescent", wetness=0.6),
            character_roster={"maya": maya, "elena": elena},
            prop_roster={"pda_01": prop},
            active_camera=CameraState(lens_focal_length_mm=50.0, aperture=2.0),
        )

        world_model = AetherWorldModel(init_state)

        # Freeze Shot 1
        snapshot_1 = world_model.freeze_shot("SHOT_001")
        assert snapshot_1.shot_id == "SHOT_001"

        # Apply actions leading to Shot 2
        # Action 1: Move Elena closer to Maya
        move_action = SceneAction(
            action_id="ACT_01",
            action_type=ActionType.CHARACTER_MOVE,
            actor_id="elena",
            metadata={"new_position": [1.2, 0.0, 0.0], "distance_moved": 3.8, "velocity_mps": 1.9},
            elapsed_seconds=2.0,
        )
        # Action 2: Transfer PDA from Maya to Elena
        handoff_action = SceneAction(
            action_id="ACT_02",
            action_type=ActionType.PROP_TRANSFER,
            actor_id="maya",
            target_id="elena",
            metadata={"prop_id": "pda_01", "hand": "left"},
            elapsed_seconds=1.0,
        )
        world_model.apply_actions([move_action, handoff_action])

        # Freeze Shot 2
        snapshot_2 = world_model.freeze_shot("SHOT_002")

        # Compute delta between Shot 1 and Shot 2
        delta = world_model.compute_delta("SHOT_001", "SHOT_002")
        assert delta.has_changes
        assert "pda_01" in delta.prop_deltas
        assert delta.prop_deltas["pda_01"].ownership_transition == ("maya", "elena")

        # Planner analyzes frozen snapshot and delta
        planner = ComplexityPlanner()
        req_2 = ShotRequirement(shot_id="SHOT_002", characters=["maya", "elena"])
        plan_2 = planner.plan(snapshot_2, req_2, state_delta=delta)

        # Handoff in delta must trigger Level 4 (THREED_BLOCKING)
        assert plan_2.complexity_level == ComplexityLevel.THREED_BLOCKING
        assert any("handoff" in r.lower() or "transfer" in r.lower() for r in plan_2.rationale)

        # Compiler translates snapshot and delta
        compiler = ShotCompiler(planner=planner)
        payload = compiler.compile_auto(snapshot_2, req_2, state_delta=delta)

        # Verifies prop possession in compiled prompt reflects state after handoff
        assert "pda" in payload.prompt.lower()
        assert payload.complexity_level == ComplexityLevel.THREED_BLOCKING


# ---------------------------------------------------------------------------
# 6. Error Handling & Boundary Condition Tests
# ---------------------------------------------------------------------------

class TestErrorHandlingAndBoundaries:
    """Verifies graceful handling of invalid inputs and edge boundary values."""

    def test_invalid_scene_state_type_raises(self):
        """Unsupported object type for scene_state raises ValueError."""
        planner = ComplexityPlanner()
        with pytest.raises(ValueError, match="Unsupported scene state"):
            planner.plan("invalid_string_state")

    def test_missing_character_in_roster_handled_gracefully(self, empty_scene):
        """Character ID in requirement not present in roster should not crash."""
        compiler = ShotCompiler()
        req = ShotRequirement(characters=["unknown_ghost_actor"])

        payload = compiler.compile_for_veo(empty_scene, req)
        assert "Unknown_Ghost_Actor" in payload.prompt or "unknown_ghost_actor" in payload.prompt

    def test_spatial_package_partial_or_empty(self, empty_scene):
        """ComfyUI compilation with empty or None spatial package produces valid payload."""
        compiler = ShotCompiler()
        req = ShotRequirement(shot_id="SHOT_EMPTY_PKG", target_duration=3.0)

        payload = compiler.compile_for_comfyui(empty_scene, req, spatial_package=None)
        assert payload.provider_target == ProviderTarget.COGVIDEOX_COMFYUI
        assert payload.provider_config["base_model"] == "CogVideoX-5B"
        assert payload.first_frame_uri is None

    def test_extreme_camera_speed_clamped(self, portrait_scene):
        """Extreme camera velocities are capped to maximum valid API ranges."""
        compiler = ShotCompiler()
        req = ShotRequirement(
            camera_movement="pan_right",
            camera_velocity_mps=99.0,
        )

        payload = compiler.compile_for_runway(portrait_scene, req)
        # Motion score clamped to 10.0
        assert payload.provider_config["motion_score"] <= 10.0
        assert payload.provider_config["director_mode"]["pan"] <= 10.0

    def test_runway_director_mode_all_axes(self, portrait_scene):
        """Runway Director Mode supports tilt, zoom, truck, pedestal, roll."""
        compiler = ShotCompiler()
        req = ShotRequirement(
            camera_movement="tilt_down",
            camera_velocity_mps=2.0,
        )
        p1 = compiler.compile_for_runway(portrait_scene, req)
        assert p1.provider_config["director_mode"]["tilt"] < 0.0
        assert "Tilt Down" in p1.prompt

        req2 = ShotRequirement(camera_movement="dolly_out", camera_velocity_mps=3.0)
        p2 = compiler.compile_for_runway(portrait_scene, req2)
        assert p2.provider_config["director_mode"]["zoom"] < 0.0
        assert "Zoom Out" in p2.prompt

        req3 = ShotRequirement(camera_movement="truck_left", camera_velocity_mps=1.5)
        p3 = compiler.compile_for_runway(portrait_scene, req3)
        assert p3.provider_config["director_mode"]["truck"] < 0.0

        req4 = ShotRequirement(camera_movement="roll_cw", camera_velocity_mps=1.0)
        p4 = compiler.compile_for_runway(portrait_scene, req4)
        assert p4.provider_config["director_mode"]["roll"] > 0.0

    def test_comfyui_different_resolutions_and_aspect_ratios(self, empty_scene):
        """ComfyUI latent tensor dimensions correctly calculated for various aspect ratios."""
        compiler = ShotCompiler()

        # 720p 16:9
        req_720 = ShotRequirement(resolution="720p", aspect_ratio="16:9", target_duration=5.0)
        p_720 = compiler.compile_for_comfyui(empty_scene, req_720)
        dims_720 = p_720.provider_config["latent_dimensions"]
        assert dims_720["width"] == 1280
        assert dims_720["height"] == 720
        assert dims_720["latent_width"] == 160
        assert dims_720["latent_height"] == 90

        # 1080p vertical 9:16
        req_vert = ShotRequirement(resolution="1080p", aspect_ratio="9:16", target_duration=4.0)
        p_vert = compiler.compile_for_comfyui(empty_scene, req_vert)
        dims_vert = p_vert.provider_config["latent_dimensions"]
        assert dims_vert["width"] == 1080
        assert dims_vert["height"] == 1920
        assert dims_vert["latent_width"] == 135
        assert dims_vert["latent_height"] == 240

        # 4k 16:9
        req_4k = ShotRequirement(resolution="4k", aspect_ratio="16:9", target_duration=2.5)
        p_4k = compiler.compile_for_comfyui(empty_scene, req_4k)
        dims_4k = p_4k.provider_config["latent_dimensions"]
        assert dims_4k["width"] == 3840
        assert dims_4k["height"] == 2160

    def test_kling_motion_brush_from_character_delta(self, two_character_handoff_scene):
        """Kling element tracking is generated from StateDelta character displacement."""
        compiler = ShotCompiler()
        world_model = AetherWorldModel(two_character_handoff_scene)
        world_model.freeze_shot("SHOT_A")

        move_action = SceneAction(
            action_id="ACT_M",
            action_type=ActionType.CHARACTER_MOVE,
            actor_id="maya",
            metadata={"new_position": [3.0, 0.0, 2.0], "distance_moved": 2.0, "velocity_mps": 1.0},
            elapsed_seconds=2.0,
        )
        world_model.apply_action(move_action)
        world_model.freeze_shot("SHOT_B")
        delta = world_model.compute_delta("SHOT_A", "SHOT_B")

        req = ShotRequirement(characters=["maya"])
        payload = compiler.compile_for_kling(world_model.active_state, req, state_delta=delta)

        brush_elements = payload.provider_config["motion_brush_elements"]
        assert len(brush_elements) >= 1
        maya_elem = next(e for e in brush_elements if e["element_id"] == "maya")
        assert maya_elem["distance_moved"] > 0.0

    def test_direct_world_model_pass_to_planner_and_compiler(self, portrait_scene):
        """Passing AetherWorldModel instance directly to planner and compiler."""
        world_model = AetherWorldModel(portrait_scene)
        planner = ComplexityPlanner()
        compiler = ShotCompiler(planner=planner)

        req = ShotRequirement(characters=["maya"])
        plan = planner.plan(world_model, req)
        assert plan.complexity_level == ComplexityLevel.REFERENCE_IMAGE

        payload = compiler.compile_auto(world_model, req)
        assert payload.provider_target == ProviderTarget.RUNWAY_GEN_4_5

    def test_shot_requirement_dict_normalization_edge_cases(self):
        """ShotRequirement properly parses alternative dictionary keys."""
        d = {
            "duration_seconds": 6.5,
            "focal_point": "eyes of subject",
            "actors": ["maya"],
            "has_handoff": True,
            "has_dialogue": True,
            "transcript": "Status report.",
        }
        req = ShotRequirement(**d)
        assert req.target_duration == 6.5
        assert req.target_focal_intent == "eyes of subject"
        assert req.character_ids_involved == ["maya"]
        assert req.has_prop_handoff
        assert req.has_dialogue
        assert req.audio.dialogue_transcript == "Status report."

    def test_spatial_package_list_segmentation_masks(self):
        """SpatialRepresentationPackage converts list of masks into dict."""
        pkg = SpatialRepresentationPackage(
            segmentation_masks=["https://mask0.png", "https://mask1.png"]
        )
        assert isinstance(pkg.segmentation_masks, dict)
        assert "mask_0" in pkg.segmentation_masks
        assert pkg.segmentation_masks["mask_0"] == "https://mask0.png"


class TestCompilerHardeningAndEdgeCases:
    """Rigorous regression tests for newly hardened schemas, planner heuristics, and compiler outputs."""

    def test_shot_slice_alias_and_planning(self, empty_scene):
        """ShotSlice is a canonical alias for SceneSnapshot and fully supported by planner and compiler."""
        slice_obj = ShotSlice(shot_id="SHOT_001", state=empty_scene, sequence_index=0)
        planner = ComplexityPlanner()
        compiler = ShotCompiler(planner=planner)

        plan = planner.plan(slice_obj)
        assert plan.complexity_level == ComplexityLevel.PROMPT_ONLY

        payload = compiler.compile_auto(slice_obj)
        assert payload.complexity_level == ComplexityLevel.PROMPT_ONLY
        assert payload.provider_target == ProviderTarget.VEO_3_1

    def test_complexity_level_float_and_regex_parsing(self):
        """ComplexityLevel.from_val handles floats, float-strings, labels, and regex patterns."""
        assert ComplexityLevel.from_val(2.0) == ComplexityLevel.KEYFRAMES_INTERPOLATION
        assert ComplexityLevel.from_val("2.0") == ComplexityLevel.KEYFRAMES_INTERPOLATION
        assert ComplexityLevel.from_val("LEVEL 4") == ComplexityLevel.THREED_BLOCKING
        assert ComplexityLevel.from_val("level_5") == ComplexityLevel.FULL_PHYSICAL_SIMULATION
        assert ComplexityLevel.from_val("Level 0 - Prompt Only") == ComplexityLevel.PROMPT_ONLY
        assert ComplexityLevel.from_val("THREED_BLOCKING") == ComplexityLevel.THREED_BLOCKING

    def test_compiled_model_payload_aliases_and_api_dict(self):
        """CompiledModelPayload handles positive_prompt, provider, compute_tier aliases and to_api_payload()."""
        payload = CompiledModelPayload(
            positive_prompt="A lone wanderer in a sandstorm",
            provider="veo_3_1",
            camera_motion={"movement": "pan"},
            compute_tier="premium",
        )
        assert payload.prompt == "A lone wanderer in a sandstorm"
        assert payload.positive_prompt == "A lone wanderer in a sandstorm"
        assert payload.provider_target == ProviderTarget.VEO_3_1
        assert payload.provider == ProviderTarget.VEO_3_1
        assert payload.required_compute_tier == ComputeTier.PREMIUM
        assert payload.compute_tier == ComputeTier.PREMIUM
        assert payload.camera_motion == {"movement": "pan"}

        api_payload = payload.to_api_payload()
        assert api_payload["positive_prompt"] == "A lone wanderer in a sandstorm"
        assert api_payload["provider"] == "veo_3_1"
        assert api_payload["compute_tier"] == "premium"

    def test_planner_physical_challenges_spaced_words(self, empty_scene):
        """Physical challenge multi-word strings ('martial arts', 'rain puddle') trigger Level 5."""
        planner = ComplexityPlanner()

        req1 = ShotRequirement(physical_challenges=["martial arts"])
        assert planner.classify(empty_scene, req1) == ComplexityLevel.FULL_PHYSICAL_SIMULATION

        req2 = ShotRequirement(physical_challenges=["rain puddle"])
        assert planner.classify(empty_scene, req2) == ComplexityLevel.FULL_PHYSICAL_SIMULATION

        req3 = ShotRequirement(physical_challenges=["rigid body collision"])
        assert planner.classify(empty_scene, req3) == ComplexityLevel.FULL_PHYSICAL_SIMULATION

        req4 = ShotRequirement(physical_challenges=["cloth simulation"])
        assert planner.classify(empty_scene, req4) == ComplexityLevel.FULL_PHYSICAL_SIMULATION

    def test_planner_crane_camera_case_and_spacing(self, portrait_scene):
        """Crane movement with spaces/casing triggers Level 4 regardless of actor count."""
        planner = ComplexityPlanner()

        req_crane = ShotRequirement(camera_movement="Crane Up")
        plan_crane = planner.plan(portrait_scene, req_crane)
        assert plan_crane.complexity_level == ComplexityLevel.THREED_BLOCKING

        req_pan = ShotRequirement(camera_movement="Pan Right")
        plan_pan = planner.plan(portrait_scene, req_pan)
        assert plan_pan.complexity_level == ComplexityLevel.KEYFRAMES_INTERPOLATION

    def test_planner_string_level_and_dict_recommendations(self):
        """get_recommended_representations and get_recommended_provider accept strings, floats, and dicts."""
        reps = ComplexityPlanner.get_recommended_representations("LEVEL_4")
        assert "clay_render" in reps
        assert "depth_map" in reps
        assert ComplexityPlanner.get_recommended_representations("level 0") == []
        assert ComplexityPlanner.get_recommended_representations(1.0) == ["photoreal_ref"]

        prov_diag = ComplexityPlanner.get_recommended_provider(3, {"has_dialogue": True})
        assert prov_diag == ProviderTarget.KLING_3_0
        prov_l5 = ComplexityPlanner.get_recommended_provider("LEVEL_5")
        assert prov_l5 == ProviderTarget.COGVIDEOX_COMFYUI

    def test_compile_auto_preferred_provider_preserves_level(self, empty_scene):
        """compile_auto calculates and retains complexity_level even when preferred_provider override is used."""
        compiler = ShotCompiler()
        p = compiler.compile_auto(empty_scene, preferred_provider="runway_gen_4_5")
        assert p.provider_target == ProviderTarget.RUNWAY_GEN_4_5
        assert p.complexity_level == ComplexityLevel.PROMPT_ONLY

    def test_comfyui_loras_from_scene_roster_when_req_empty(self, two_character_handoff_scene):
        """ComfyUI compiler generates LoRAs from scene roster when ShotRequirement.character_ids_involved is empty."""
        compiler = ShotCompiler()
        p = compiler.compile_for_comfyui(two_character_handoff_scene, ShotRequirement())
        loras = p.provider_config["lora_weights"]
        cids = {l["character_id"] for l in loras}
        assert "maya" in cids
        assert "elena" in cids

    def test_runway_director_mode_focal_delta_and_overrides(self, portrait_scene):
        """Runway compiler handles manual director_mode metadata override and camera focal length delta."""
        from aether.state.schemas import CameraDelta, StateDelta

        compiler = ShotCompiler()
        req_meta = ShotRequirement(metadata={"director_mode": {"pan": 5.0, "zoom": -3.0}})
        p_meta = compiler.compile_for_runway(portrait_scene, req_meta)
        assert p_meta.provider_config["director_mode"]["pan"] == 5.0
        assert p_meta.provider_config["director_mode"]["zoom"] == -3.0
        assert "Pan Right +5.0" in p_meta.provider_config["director_syntax"]
        assert "Zoom Out -3.0" in p_meta.provider_config["director_syntax"]

        delta = StateDelta(
            shot_a_id="S1",
            shot_b_id="S2",
            camera_delta=CameraDelta(focal_length_delta=25.0),
        )
        p_focal = compiler.compile_for_runway(portrait_scene, ShotRequirement(), state_delta=delta)
        assert p_focal.provider_config["director_mode"]["zoom"] > 0.0
        assert "Zoom In" in p_focal.provider_config["director_syntax"]

    def test_comfyui_hunyuan_video_support_and_aspect_ratios(self, empty_scene, portrait_scene):
        """ComfyUI compiler calculates correct 4:3, 3:4, 21:9 dimensions and builds HunyuanVideo graph nodes."""
        compiler = ShotCompiler()

        # 4:3 aspect ratio
        req_4_3 = ShotRequirement(aspect_ratio="4:3", resolution="1080p")
        p_4_3 = compiler.compile_for_comfyui(empty_scene, req_4_3)
        dims_4_3 = p_4_3.provider_config["latent_dimensions"]
        assert dims_4_3["width"] == 1440
        assert dims_4_3["height"] == 1080
        assert dims_4_3["width"] % 8 == 0
        assert dims_4_3["height"] % 8 == 0

        # 3:4 aspect ratio
        req_3_4 = ShotRequirement(aspect_ratio="3:4", resolution="1080p")
        p_3_4 = compiler.compile_for_comfyui(empty_scene, req_3_4)
        dims_3_4 = p_3_4.provider_config["latent_dimensions"]
        assert dims_3_4["width"] % 8 == 0
        assert dims_3_4["height"] % 8 == 0

        # 21:9 aspect ratio
        req_21_9 = ShotRequirement(aspect_ratio="21:9", resolution="1080p")
        p_21_9 = compiler.compile_for_comfyui(empty_scene, req_21_9)
        dims_21_9 = p_21_9.provider_config["latent_dimensions"]
        assert dims_21_9["width"] == 1920
        assert dims_21_9["height"] % 8 == 0

        # Hunyuan Video graph
        req_hunyuan = ShotRequirement(metadata={"base_model": "HunyuanVideo-1.5"})
        p_hunyuan = compiler.compile_for_comfyui(portrait_scene, req_hunyuan)
        graph = p_hunyuan.provider_config["workflow_graph"]
        assert graph["1"]["class_type"] == "HunyuanVideoModelLoader"
        assert graph["2"]["class_type"] == "HunyuanVideoVAELoader"
        assert graph["4"]["class_type"] == "HunyuanVideoTextEncode"
        assert graph["6"]["class_type"] == "EmptyHunyuanVideoLatentVideo"

    def test_cinematic_prompt_state_delta_momentum(self, portrait_scene):
        """Cinematic prompt captures environmental transitions, character delta momentum, and applied actions."""
        from aether.state.schemas import CharacterDelta, EnvironmentDelta, StateDelta

        delta = StateDelta(
            shot_a_id="S1",
            shot_b_id="S2",
            environment_delta=EnvironmentDelta(
                lighting_transition=("golden_hour", "midnight_blue"),
                weather_transition=("clear", "thunderstorm"),
                wetness_delta=0.8,
            ),
            character_deltas={
                "maya": CharacterDelta(
                    character_id="maya",
                    distance_moved=4.5,
                    emotional_transition=("calm", "furious"),
                )
            },
            actions_applied=[
                SceneAction(action_id="A1", action_type=ActionType.PROP_TRANSFER)
            ],
        )
        compiler = ShotCompiler()
        p = compiler.compile_for_veo(portrait_scene, ShotRequirement(characters=["maya"]), state_delta=delta)
        assert "Lighting transitions from golden_hour to midnight_blue" in p.prompt
        assert "Weather shifts from clear to thunderstorm" in p.prompt
        assert "Emotional shift: from calm to furious" in p.prompt
        assert "Momentum: traversed 4.50m" in p.prompt
        assert "Action context: PROP TRANSFER" in p.prompt


if __name__ == "__main__":
    pytest.main([__file__, "-vv"])
