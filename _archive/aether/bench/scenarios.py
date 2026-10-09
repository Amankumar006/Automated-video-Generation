"""AetherBench Benchmark Scenario Suite.

Contains handcrafted gold-standard stress-test scenarios representing core
cinematic challenges (multi-character blocking, handoffs, whip pans, glass optics,
pulsing strobes, and fluid physics) plus a deterministic suite generator
for expanding to the full 250 AetherBench scenarios.
"""

from __future__ import annotations

import math
import random
from typing import List, Optional

from aether.bench.registry import ScenarioRegistry, get_default_registry
from aether.bench.schemas import (
    AetherScenario,
    CameraMovementType,
    CameraParameters,
    CharacterDescriptor,
    ComplexityLevel,
    EnvironmentLighting,
    HardGateConstraints,
    PhysicsChallengeType,
    PhysicsDifficulty,
    PhysicsProfile,
    RepairStrategy,
    SceneVariables,
    SoftScoringSpec,
    StressTestCategory,
    SurfaceProperties,
    TemporalContinuityConstraints,
    WardrobeGarment,
)


def get_gold_standard_scenarios() -> List[AetherScenario]:
    """Return the foundational suite of 8 handcrafted gold-standard cinematic scenarios."""

    # 1. Multi-Character Interaction: Interrogation Standoff
    bench_mc_001 = AetherScenario(
        id="BENCH-MC-001",
        title="Interrogation Eyeline & Blocking Standoff",
        description=(
            "Two opposing agents seated across a steel interrogation table. Maya Lin is seated "
            "rigidly, hands handcuffed to the table, maintaining an unblinking gaze. Detective Thorne "
            "paces slowly behind her chair, breaking and reconnecting eyelines. Strict enforcement of "
            "the 180-degree line-of-action rule across multiple focal cuts."
        ),
        category=StressTestCategory.MULTI_CHARACTER_INTERACTION,
        complexity_level=ComplexityLevel.LEVEL_4_3D_BLOCKING,
        duration_seconds=6.0,
        target_fps=24,
        resolution=(1920, 1080),
        scene_variables=SceneVariables(
            location="interrogation_room_sub_b",
            time_of_day="03:15",
            environment=EnvironmentLighting(
                ambient_description="overhead_harsh_tungsten_single_source",
                color_temperature_k=3200,
                strobe_frequency_hz=0.0,
                key_light_direction=[0.0, -1.0, 0.2],
                contrast_ratio=4.5,
                shadow_sharpness=0.95,
            ),
            particulates="suspended_cigarette_smoke",
            surface=SurfaceProperties(wetness=0.05, reflections=False, roughness=0.7),
            weather="indoor",
            audio_ambience="sub_bass_electrical_hum_low",
        ),
        characters=[
            CharacterDescriptor(
                id="maya",
                name="Maya Lin",
                position=[0.0, 0.0, 1.2],
                facing_angle=0.0,
                eyeline_vector=[0.0, 0.1, 0.99],
                wardrobe={
                    "jacket": WardrobeGarment(
                        id="wardrobe_inmate_01",
                        type="jumpsuit",
                        state="creased_rough",
                        color="#D97706",
                    )
                },
                injuries=["bruise_left_jaw"],
                props={"wrists": "steel_handcuffs_linked"},
                emotional_state="unyielding_defiance",
                action_description="Sits motionless, leaning slightly forward, fixing eyes on detective",
            ),
            CharacterDescriptor(
                id="thorne",
                name="Detective Thorne",
                position=[-0.8, 0.0, 2.4],
                facing_angle=140.0,
                eyeline_vector=[0.4, -0.15, -0.9],
                wardrobe={
                    "coat": WardrobeGarment(
                        id="coat_thorne_01",
                        type="trench_coat",
                        state="weathered",
                        color="#1E293B",
                    )
                },
                injuries=[],
                props={"right_hand": "unlit_cigarette"},
                emotional_state="predatory_scrutiny",
                action_description="Paces in an arc behind Maya, leaning down to level with her ear",
            ),
        ],
        camera=CameraParameters(
            lens_mm=50.0,
            sensor_format="full_frame",
            aperture_fstop=2.0,
            shutter_angle_deg=180.0,
            movement_type=CameraMovementType.TRACKING,
            start_position=[-1.2, 1.3, 0.8],
            end_position=[-0.3, 1.3, 0.5],
            velocity_mps=0.25,
            eyeline_vector=[0.7, -0.1, 0.7],
            focus_distance_m=1.6,
            rack_focus=True,
            rack_focus_target_m=2.3,
        ),
        physics_profile=PhysicsProfile(
            difficulty=PhysicsDifficulty.MEDIUM,
            challenges=[
                PhysicsChallengeType.SMOKE_VOLUMETRICS,
                PhysicsChallengeType.RAPID_SHADOW_INVERSION,
            ],
            gravity_vector=[0.0, -9.81, 0.0],
            simulation_tolerance=0.04,
        ),
        hard_gate_constraints=HardGateConstraints(
            anatomical_integrity=True,
            max_limb_deformation_tolerance=0.03,
            character_identity_preservation=True,
            min_face_embedding_cosine=0.90,
            prop_continuity=True,
            lip_sync_alignment=False,
        ),
        temporal_constraints=TemporalContinuityConstraints(
            max_optical_flow_jitter=0.08,
            min_ssim_frame_to_frame=0.88,
            max_flicker_ratio=0.03,
            line_of_action_180_deg_enforced=True,
        ),
        soft_scoring_spec=SoftScoringSpec(
            min_cinematography=8.5,
            min_visual_aesthetic=8.5,
            min_narrative_pacing=8.0,
            min_aggregate_score=8.4,
        ),
        tags=["interrogation", "two_shot", "eyeline_match", "smoke", "dramatic"],
        expected_repair_strategy_on_failure=RepairStrategy.SPATIAL_PREVIS_FALLBACK,
    )

    # 2. Hand-Object Handoff: Cryogenic Vial Transfer
    bench_ho_001 = AetherScenario(
        id="BENCH-HO-001",
        title="Cryogenic Vial Handoff in Abandoned Cleanroom",
        description=(
            "Close-up tracking shot of an exchange between two characters in an abandoned bio-cleanroom. "
            "Maya extends her right hand holding the frosted cryo-vial (spectrometer_device_01). "
            "Thorne reaches forward with gloved left hand and firmly closes fingers around the vial cylinder. "
            "The object must remain geometrically rigid, with zero phantom fingers, clipping, or vanishing."
        ),
        category=StressTestCategory.HAND_OBJECT_HANDOFF,
        complexity_level=ComplexityLevel.LEVEL_4_3D_BLOCKING,
        duration_seconds=5.0,
        target_fps=24,
        resolution=(1920, 1080),
        scene_variables=SceneVariables(
            location="abandoned_cleanroom",
            time_of_day="23:42",
            environment=EnvironmentLighting(
                ambient_description="emergency_red_pulsing",
                color_temperature_k=1800,
                strobe_frequency_hz=1.2,
                key_light_direction=[-0.6, -0.8, 0.0],
                contrast_ratio=3.8,
                shadow_sharpness=0.85,
            ),
            particulates="steam_leak",
            surface=SurfaceProperties(wetness=0.85, reflections=True, roughness=0.15, specular_intensity=0.9),
            weather="indoor",
            audio_ambience="steam_valve_hiss_with_emergency_siren",
        ),
        characters=[
            CharacterDescriptor(
                id="maya",
                name="Maya Lin",
                position=[0.0, 0.0, 0.0],
                facing_angle=45.0,
                eyeline_vector=[0.7, 0.0, 0.7],
                wardrobe={
                    "jacket": WardrobeGarment(
                        id="leather_004",
                        type="jacket",
                        state="left_sleeve_torn",
                        color="#111827",
                    )
                },
                injuries=["blood_cheek_right"],
                props={"right_hand": "spectrometer_device_01"},
                emotional_state="hyper-vigilant",
                action_description="Extends right arm steadily with glowing cryo vial",
            ),
            CharacterDescriptor(
                id="thorne",
                name="Detective Thorne",
                position=[0.65, 0.0, 0.65],
                facing_angle=225.0,
                eyeline_vector=[-0.7, 0.0, -0.7],
                wardrobe={
                    "coat": WardrobeGarment(
                        id="coat_thorne_01",
                        type="trench_coat",
                        state="wet",
                        color="#1E293B",
                    )
                },
                injuries=[],
                props={},
                emotional_state="tense",
                action_description="Reaches with gloved left hand to grasp the spectrometer vial",
            ),
        ],
        camera=CameraParameters(
            lens_mm=85.0,
            sensor_format="full_frame",
            aperture_fstop=1.8,
            shutter_angle_deg=180.0,
            movement_type=CameraMovementType.DOLLY_IN,
            start_position=[0.3, 1.2, -0.8],
            end_position=[0.32, 1.15, -0.3],
            velocity_mps=0.12,
            eyeline_vector=[0.0, -0.2, 0.98],
            focus_distance_m=0.8,
        ),
        physics_profile=PhysicsProfile(
            difficulty=PhysicsDifficulty.HIGH,
            challenges=[
                PhysicsChallengeType.RIGID_BODY_COLLISION,
                PhysicsChallengeType.SPECULAR_REFLECTION,
            ],
            simulation_tolerance=0.02,
        ),
        hard_gate_constraints=HardGateConstraints(
            anatomical_integrity=True,
            max_limb_deformation_tolerance=0.02,
            character_identity_preservation=True,
            min_face_embedding_cosine=0.88,
            prop_continuity=True,
            handoff_prop_id="spectrometer_device_01",
            handoff_source_character="maya",
            handoff_target_character="thorne",
            handoff_window_start_sec=2.2,
            handoff_window_end_sec=3.8,
            lip_sync_alignment=False,
        ),
        temporal_constraints=TemporalContinuityConstraints(
            max_optical_flow_jitter=0.06,
            min_ssim_frame_to_frame=0.85,
            max_flicker_ratio=0.05,
            line_of_action_180_deg_enforced=True,
        ),
        soft_scoring_spec=SoftScoringSpec(
            min_cinematography=8.8,
            min_visual_aesthetic=8.5,
            min_narrative_pacing=8.0,
            min_aggregate_score=8.5,
        ),
        tags=["handoff", "prop_continuity", "macro_hands", "high_stakes", "cleanroom"],
        expected_repair_strategy_on_failure=RepairStrategy.TEMPORAL_INPAINTING,
    )

    # 3. Rapid Camera Movement: Whip Pan & Crane Plunge
    bench_rc_001 = AetherScenario(
        id="BENCH-RC-001",
        title="Supersonic Crane Plunge & 180-Degree Whip Pan",
        description=(
            "A high-speed vertical crane plunge from a 12-meter cathedral roof beam downwards to a "
            "stone floor, terminating in an explosive 180-degree whip pan that locks onto a sprinting figure. "
            "Tests camera trajectory preservation, motion blur coherence, and background perspective consistency."
        ),
        category=StressTestCategory.RAPID_CAMERA_MOVEMENT,
        complexity_level=ComplexityLevel.LEVEL_4_3D_BLOCKING,
        duration_seconds=4.0,
        target_fps=24,
        resolution=(1920, 1080),
        scene_variables=SceneVariables(
            location="abandoned_cathedral_nave",
            time_of_day="dusk",
            environment=EnvironmentLighting(
                ambient_description="shafts_of_twilight_through_broken_rose_window",
                color_temperature_k=5200,
                contrast_ratio=5.0,
                shadow_sharpness=0.9,
            ),
            particulates="floating_dust_motes",
            surface=SurfaceProperties(wetness=0.2, reflections=True, roughness=0.4),
            audio_ambience="gusting_wind_through_broken_stained_glass",
        ),
        characters=[
            CharacterDescriptor(
                id="runner",
                name="Courier Vance",
                position=[0.0, 0.0, 5.0],
                facing_angle=180.0,
                eyeline_vector=[0.0, 0.0, -1.0],
                wardrobe={
                    "tactical_suit": WardrobeGarment(
                        id="courier_suit_09",
                        type="jumpsuit",
                        state="worn",
                        color="#374151",
                    )
                },
                action_description="Sprints full tilt toward foreground, vaulting stone debris",
            )
        ],
        camera=CameraParameters(
            lens_mm=24.0,
            sensor_format="imax",
            aperture_fstop=4.0,
            shutter_angle_deg=144.0,
            movement_type=CameraMovementType.WHIP_PAN,
            start_position=[0.0, 11.5, 0.0],
            end_position=[0.0, 1.4, 2.0],
            velocity_mps=9.8,
            focus_distance_m=4.5,
        ),
        physics_profile=PhysicsProfile(
            difficulty=PhysicsDifficulty.HIGH,
            challenges=[
                PhysicsChallengeType.HIGH_VELOCITY_IMPACT,
                PhysicsChallengeType.RAPID_SHADOW_INVERSION,
            ],
            simulation_tolerance=0.03,
        ),
        hard_gate_constraints=HardGateConstraints(
            anatomical_integrity=True,
            character_identity_preservation=True,
            prop_continuity=False,
            lip_sync_alignment=False,
        ),
        temporal_constraints=TemporalContinuityConstraints(
            max_optical_flow_jitter=0.22,  # whip pan allows higher flow magnitude but coherent vectors
            min_ssim_frame_to_frame=0.65,  # high motion blur naturally drops raw ssim
            max_flicker_ratio=0.06,
            allow_motion_blur=True,
        ),
        soft_scoring_spec=SoftScoringSpec(
            min_cinematography=8.5,
            min_visual_aesthetic=8.0,
            min_narrative_pacing=9.0,
            min_aggregate_score=8.4,
        ),
        tags=["whip_pan", "crane_plunge", "high_velocity", "perspective_warp"],
        expected_repair_strategy_on_failure=RepairStrategy.SPATIAL_PREVIS_FALLBACK,
    )

    # 4. Glass & Reflection Physics: Dual Neon Reflection
    bench_gr_001 = AetherScenario(
        id="BENCH-GR-001",
        title="Dual Neon Specular Reflection on Wet Storefront Glass",
        description=(
            "Close profile shot of a protagonist standing outside a retro diner in heavy downpour. "
            "A double-pane storefront window separates the camera from interior patrons. "
            "The glass reflects exterior neon signage (magenta and cyan) while simultaneously "
            "transmitting refractive light from inside. Evaluates specular reflection consistency and Fresnel effects."
        ),
        category=StressTestCategory.GLASS_REFLECTION_OPTICS,
        complexity_level=ComplexityLevel.LEVEL_5_DETERMINISTIC_SIM,
        duration_seconds=5.0,
        target_fps=24,
        resolution=(1920, 1080),
        scene_variables=SceneVariables(
            location="tokyo_alleyway_storefront",
            time_of_day="01:20",
            environment=EnvironmentLighting(
                ambient_description="neon_magenta_and_cyan_dual_rim",
                color_temperature_k=7000,
                strobe_frequency_hz=0.0,
                contrast_ratio=6.0,
                shadow_sharpness=0.9,
            ),
            particulates="heavy_rain_curtain",
            surface=SurfaceProperties(wetness=1.0, reflections=True, roughness=0.05, specular_intensity=0.98),
            weather="heavy_rain",
            audio_ambience="torrential_rain_with_distant_traffic",
        ),
        characters=[
            CharacterDescriptor(
                id="kaito",
                name="Kaito",
                position=[-0.2, 0.0, 0.8],
                facing_angle=90.0,
                eyeline_vector=[1.0, 0.0, 0.0],
                wardrobe={
                    "coat": WardrobeGarment(
                        id="drench_coat_kaito",
                        type="overcoat",
                        state="soaked",
                        color="#0F172A",
                    )
                },
                emotional_state="contemplative_exhaustion",
                action_description="Looks at reflection in shopfront glass; raindrops roll down the surface",
            )
        ],
        camera=CameraParameters(
            lens_mm=50.0,
            sensor_format="full_frame",
            aperture_fstop=1.4,
            shutter_angle_deg=180.0,
            movement_type=CameraMovementType.DOLLY_IN,
            start_position=[-0.6, 1.4, 0.0],
            end_position=[-0.35, 1.4, 0.4],
            velocity_mps=0.08,
            focus_distance_m=0.85,
        ),
        physics_profile=PhysicsProfile(
            difficulty=PhysicsDifficulty.EXTREME,
            challenges=[
                PhysicsChallengeType.GLASS_REFRACTION,
                PhysicsChallengeType.SPECULAR_REFLECTION,
                PhysicsChallengeType.FLUID_DYNAMICS,
            ],
            optical_refraction_index=1.52,  # Crown glass
            simulation_tolerance=0.02,
        ),
        hard_gate_constraints=HardGateConstraints(
            anatomical_integrity=True,
            character_identity_preservation=True,
            min_face_embedding_cosine=0.86,
            prop_continuity=False,
            lip_sync_alignment=False,
        ),
        temporal_constraints=TemporalContinuityConstraints(
            max_optical_flow_jitter=0.09,
            min_ssim_frame_to_frame=0.82,
            max_flicker_ratio=0.07,
            allow_motion_blur=True,
        ),
        soft_scoring_spec=SoftScoringSpec(
            min_cinematography=9.0,
            min_visual_aesthetic=9.0,
            min_narrative_pacing=8.0,
            min_aggregate_score=8.7,
        ),
        tags=["neon", "reflections", "glass", "rain", "cyberpunk", "optics"],
        expected_repair_strategy_on_failure=RepairStrategy.KEYFRAME_INTERPOLATION,
    )

    # 5. Temporal Continuity: 10-Second Continuous Tracking with Strobe
    bench_tc_001 = AetherScenario(
        id="BENCH-TC-001",
        title="10-Second Continuous Tracking Shot with Pulsing Red Strobe",
        description=(
            "An unbroken 10-second tracking shot following Maya navigating a labyrinthine industrial corridor. "
            "An emergency strobe flashes rhythmically at 2.5 Hz. Her torn leather jacket ('left_sleeve_torn') "
            "and dried blood mark ('blood_cheek_right') must persist identically across all 240 frames without "
            "morphing, healing, or flickering into clean wardrobe states."
        ),
        category=StressTestCategory.TEMPORAL_CONTINUITY,
        complexity_level=ComplexityLevel.LEVEL_4_3D_BLOCKING,
        duration_seconds=10.0,
        target_fps=24,
        resolution=(1920, 1080),
        scene_variables=SceneVariables(
            location="industrial_corridor_sector_7",
            time_of_day="00:00",
            environment=EnvironmentLighting(
                ambient_description="rhythmic_red_emergency_strobe",
                color_temperature_k=1500,
                strobe_frequency_hz=2.5,
                contrast_ratio=5.5,
                shadow_sharpness=0.9,
            ),
            particulates="suspended_steam_haze",
            surface=SurfaceProperties(wetness=0.6, reflections=True, roughness=0.3),
            weather="indoor",
            audio_ambience="pulsing_klaxon_and_footsteps",
        ),
        characters=[
            CharacterDescriptor(
                id="maya",
                name="Maya Lin",
                position=[0.0, 0.0, 0.0],
                facing_angle=0.0,
                eyeline_vector=[0.0, 0.0, 1.0],
                wardrobe={
                    "jacket": WardrobeGarment(
                        id="leather_004",
                        type="jacket",
                        state="left_sleeve_torn",
                        color="#111827",
                    )
                },
                injuries=["blood_cheek_right"],
                props={"right_hand": "flashlight_torch"},
                emotional_state="hyper-vigilant",
                action_description="Walks briskly along corridor, flashlight beam sweeping side walls",
            )
        ],
        camera=CameraParameters(
            lens_mm=35.0,
            sensor_format="full_frame",
            aperture_fstop=2.2,
            shutter_angle_deg=180.0,
            movement_type=CameraMovementType.TRACKING,
            start_position=[0.0, 1.3, -1.8],
            end_position=[0.0, 1.3, 3.2],
            velocity_mps=0.5,
            focus_distance_m=1.8,
        ),
        physics_profile=PhysicsProfile(
            difficulty=PhysicsDifficulty.HIGH,
            challenges=[
                PhysicsChallengeType.RAPID_SHADOW_INVERSION,
                PhysicsChallengeType.PARTICLE_EMISSION,
            ],
            simulation_tolerance=0.03,
        ),
        hard_gate_constraints=HardGateConstraints(
            anatomical_integrity=True,
            character_identity_preservation=True,
            min_face_embedding_cosine=0.90,
            prop_continuity=True,
            lip_sync_alignment=False,
        ),
        temporal_constraints=TemporalContinuityConstraints(
            max_optical_flow_jitter=0.07,
            min_ssim_frame_to_frame=0.83,
            max_flicker_ratio=0.10,  # accounts for intentional strobe frequency
            line_of_action_180_deg_enforced=True,
        ),
        soft_scoring_spec=SoftScoringSpec(
            min_cinematography=8.5,
            min_visual_aesthetic=8.5,
            min_narrative_pacing=8.5,
            min_aggregate_score=8.5,
        ),
        tags=["long_take", "temporal_drift", "strobe_lighting", "wardrobe_preservation", "corridor"],
        expected_repair_strategy_on_failure=RepairStrategy.TEMPORAL_INPAINTING,
    )

    # 6. Fluid & Collision Physics: Hydraulic Pipe Rupture
    bench_fp_001 = AetherScenario(
        id="BENCH-FP-001",
        title="High-Pressure Hydraulic Pipe Rupture & Fluid Cascade",
        description=(
            "A pressurized hydraulic pipeline suddenly fractures. A thick jet of viscous amber hydraulic oil "
            "bursts outwards at 7.5 m/s, impacts an angled steel blast deflector, atomizes into droplets, "
            "and spatters over a wet checkerboard floor. Verifies conservation of momentum and non-Newtonian fluid cohesion."
        ),
        category=StressTestCategory.FLUID_COLLISION_PHYSICS,
        complexity_level=ComplexityLevel.LEVEL_5_DETERMINISTIC_SIM,
        duration_seconds=4.5,
        target_fps=24,
        resolution=(1920, 1080),
        scene_variables=SceneVariables(
            location="hydraulic_manifold_substation",
            time_of_day="continuous_operation",
            environment=EnvironmentLighting(
                ambient_description="overhead_yellow_industrial_flood",
                color_temperature_k=2700,
                contrast_ratio=3.0,
                shadow_sharpness=0.8,
            ),
            particulates="fine_oil_mist",
            surface=SurfaceProperties(wetness=0.9, reflections=True, roughness=0.1, specular_intensity=0.95),
            weather="indoor",
            audio_ambience="metallic_clank_followed_by_pressurized_fluid_hiss",
        ),
        characters=[],
        camera=CameraParameters(
            lens_mm=40.0,
            sensor_format="super35",
            aperture_fstop=3.5,
            shutter_angle_deg=90.0,  # crisp droplets
            movement_type=CameraMovementType.DOLLY_OUT,
            start_position=[0.0, 1.2, 1.5],
            end_position=[0.0, 1.4, 3.2],
            velocity_mps=0.38,
            focus_distance_m=1.8,
        ),
        physics_profile=PhysicsProfile(
            difficulty=PhysicsDifficulty.EXTREME,
            challenges=[
                PhysicsChallengeType.FLUID_DYNAMICS,
                PhysicsChallengeType.RIGID_BODY_COLLISION,
                PhysicsChallengeType.PARTICLE_EMISSION,
            ],
            gravity_vector=[0.0, -9.81, 0.0],
            fluid_viscosity=0.045,  # ISO VG 46 hydraulic oil
            collision_elasticity=0.15,
            simulation_tolerance=0.02,
        ),
        hard_gate_constraints=HardGateConstraints(
            anatomical_integrity=True,
            character_identity_preservation=False,
            prop_continuity=False,
            lip_sync_alignment=False,
        ),
        temporal_constraints=TemporalContinuityConstraints(
            max_optical_flow_jitter=0.18,
            min_ssim_frame_to_frame=0.75,
            max_flicker_ratio=0.06,
        ),
        soft_scoring_spec=SoftScoringSpec(
            min_cinematography=8.0,
            min_visual_aesthetic=8.5,
            min_narrative_pacing=8.0,
            min_aggregate_score=8.2,
        ),
        tags=["fluid_simulation", "hydraulic_oil", "droplets", "rigid_impact", "high_speed_particles"],
        expected_repair_strategy_on_failure=RepairStrategy.FULL_REGENERATION,
    )

    # 7. Rapid Lighting Transition: Blackout to Rotating Beacon
    bench_lt_001 = AetherScenario(
        id="BENCH-LT-001",
        title="Sudden Power Grid Blackout to Rotating Emergency Beacon",
        description=(
            "Sudden transition from warm ambient light (5000K, 600 lux) to pitch-black blackout for 0.75 seconds, "
            "followed by the activation of an intense rotating amber emergency beacon (120 RPM). "
            "Evaluates model exposure recovery, shadow vector flipping, and prevention of hallucinated artifacts in dark frames."
        ),
        category=StressTestCategory.RAPID_LIGHTING_TRANSITION,
        complexity_level=ComplexityLevel.LEVEL_4_3D_BLOCKING,
        duration_seconds=5.0,
        target_fps=24,
        resolution=(1920, 1080),
        scene_variables=SceneVariables(
            location="command_bunker_terminal",
            time_of_day="incident_time_zero",
            environment=EnvironmentLighting(
                ambient_description="blackout_followed_by_amber_rotator",
                color_temperature_k=2200,
                strobe_frequency_hz=2.0,
                contrast_ratio=8.0,
                shadow_sharpness=0.95,
            ),
            particulates="rising_cooling_smoke",
            surface=SurfaceProperties(wetness=0.1, reflections=True, roughness=0.5),
            weather="indoor",
            audio_ambience="substation_breaker_trip_klaxon",
        ),
        characters=[
            CharacterDescriptor(
                id="commander",
                name="Commander Chen",
                position=[0.0, 0.0, 1.0],
                facing_angle=0.0,
                eyeline_vector=[0.0, 0.0, 1.0],
                wardrobe={
                    "uniform": WardrobeGarment(
                        id="naval_grey_01",
                        type="tunic",
                        state="pristine",
                        color="#4B5563",
                    )
                },
                injuries=[],
                emotional_state="shock_to_resolve",
                action_description="Looks upward as main lighting cuts out; amber beam sweeps face",
            )
        ],
        camera=CameraParameters(
            lens_mm=50.0,
            sensor_format="full_frame",
            aperture_fstop=1.8,
            shutter_angle_deg=180.0,
            movement_type=CameraMovementType.DOLLY_IN,
            start_position=[0.0, 1.4, -0.8],
            end_position=[0.0, 1.4, 0.0],
            velocity_mps=0.16,
            focus_distance_m=1.8,
        ),
        physics_profile=PhysicsProfile(
            difficulty=PhysicsDifficulty.HIGH,
            challenges=[
                PhysicsChallengeType.RAPID_SHADOW_INVERSION,
                PhysicsChallengeType.SPECULAR_REFLECTION,
            ],
            simulation_tolerance=0.04,
        ),
        hard_gate_constraints=HardGateConstraints(
            anatomical_integrity=True,
            character_identity_preservation=True,
            min_face_embedding_cosine=0.88,
            prop_continuity=False,
            lip_sync_alignment=False,
        ),
        temporal_constraints=TemporalContinuityConstraints(
            max_optical_flow_jitter=0.12,
            min_ssim_frame_to_frame=0.68,  # blackout creates a natural structural dip
            max_flicker_ratio=0.15,
            allow_motion_blur=True,
        ),
        soft_scoring_spec=SoftScoringSpec(
            min_cinematography=8.8,
            min_visual_aesthetic=8.5,
            min_narrative_pacing=8.5,
            min_aggregate_score=8.6,
        ),
        tags=["lighting_transition", "blackout", "emergency_beacon", "shadow_inversion"],
        expected_repair_strategy_on_failure=RepairStrategy.KEYFRAME_INTERPOLATION,
    )

    # 8. Anatomical Stress: Martial Arts Grapple
    bench_an_001 = AetherScenario(
        id="BENCH-AN-001",
        title="Martial Arts Close-Quarters Grapple & Joint Articulation",
        description=(
            "Close-quarters kinetic grapple sequence between two martial artists. One fighter executes "
            "an wrist lock and rotational hip throw. Fingers, wrists, elbows, and knee joints must preserve "
            "biological topology with zero limb twisting, unnatural elongation, or merging torsos."
        ),
        category=StressTestCategory.ANATOMICAL_STRESS,
        complexity_level=ComplexityLevel.LEVEL_5_DETERMINISTIC_SIM,
        duration_seconds=4.0,
        target_fps=24,
        resolution=(1920, 1080),
        scene_variables=SceneVariables(
            location="dojo_training_floor",
            time_of_day="afternoon",
            environment=EnvironmentLighting(
                ambient_description="diffuse_natural_tatami_light",
                color_temperature_k=5500,
                contrast_ratio=2.2,
                shadow_sharpness=0.6,
            ),
            surface=SurfaceProperties(wetness=0.0, reflections=False, roughness=0.8),
            audio_ambience="tatami_impact_and_exhale",
        ),
        characters=[
            CharacterDescriptor(
                id="fighter_a",
                name="Fighter Alpha",
                position=[-0.3, 0.0, 0.0],
                facing_angle=90.0,
                eyeline_vector=[1.0, 0.0, 0.0],
                wardrobe={
                    "gi": WardrobeGarment(id="gi_white_01", type="gi", state="worn", color="#FFFFFF")
                },
                emotional_state="focused",
                action_description="Gripping lapel and executing rotational hip throw",
            ),
            CharacterDescriptor(
                id="fighter_b",
                name="Fighter Beta",
                position=[0.3, 0.0, 0.0],
                facing_angle=270.0,
                eyeline_vector=[-1.0, 0.0, 0.0],
                wardrobe={
                    "gi": WardrobeGarment(id="gi_black_01", type="gi", state="worn", color="#111827")
                },
                emotional_state="resisting",
                action_description="Airborne rotation over Fighter Alpha's hip",
            ),
        ],
        camera=CameraParameters(
            lens_mm=35.0,
            sensor_format="full_frame",
            aperture_fstop=2.8,
            shutter_angle_deg=144.0,
            movement_type=CameraMovementType.ORBIT,
            start_position=[-1.8, 1.2, -1.2],
            end_position=[1.2, 1.1, -1.8],
            velocity_mps=0.85,
            focus_distance_m=1.9,
        ),
        physics_profile=PhysicsProfile(
            difficulty=PhysicsDifficulty.EXTREME,
            challenges=[
                PhysicsChallengeType.SOFT_BODY_DEFORMATION,
                PhysicsChallengeType.CLOTH_SIMULATION,
                PhysicsChallengeType.RIGID_BODY_COLLISION,
            ],
            simulation_tolerance=0.02,
        ),
        hard_gate_constraints=HardGateConstraints(
            anatomical_integrity=True,
            max_limb_deformation_tolerance=0.015,  # extremely strict on anatomy
            character_identity_preservation=True,
            min_face_embedding_cosine=0.85,
            prop_continuity=False,
            lip_sync_alignment=False,
        ),
        temporal_constraints=TemporalContinuityConstraints(
            max_optical_flow_jitter=0.14,
            min_ssim_frame_to_frame=0.80,
            max_flicker_ratio=0.04,
            line_of_action_180_deg_enforced=True,
        ),
        soft_scoring_spec=SoftScoringSpec(
            min_cinematography=8.5,
            min_visual_aesthetic=8.5,
            min_narrative_pacing=9.0,
            min_aggregate_score=8.6,
        ),
        tags=["martial_arts", "grapple", "skeletal_rig", "anatomy", "high_articulation"],
        expected_repair_strategy_on_failure=RepairStrategy.SPATIAL_PREVIS_FALLBACK,
    )

    return [
        bench_mc_001,
        bench_ho_001,
        bench_rc_001,
        bench_gr_001,
        bench_tc_001,
        bench_fp_001,
        bench_lt_001,
        bench_an_001,
    ]


def generate_benchmark_suite(target_count: int = 250, seed: int = 42) -> List[AetherScenario]:
    """Deterministically generate the standardized AetherBench 250 scenario suite.

    Includes the 8 foundational gold-standard scenarios and expands across all 8 stress test
    categories, complexity levels 0-5, diverse camera rigs, and physical constraints.

    Args:
        target_count: Total number of scenarios to produce (defaults to 250).
        seed: Random seed for deterministic generation.

    Returns:
        A list of target_count validated AetherScenario instances.
    """
    rng = random.Random(seed)
    scenarios: List[AetherScenario] = list(get_gold_standard_scenarios())

    if len(scenarios) >= target_count:
        return scenarios[:target_count]

    categories = list(StressTestCategory)
    camera_moves = list(CameraMovementType)
    physics_challenges = list(PhysicsChallengeType)
    difficulties = list(PhysicsDifficulty)

    location_templates = [
        ("subway_tunnel_maintenance", "underground", ["graffiti_corridor", "water_drip"]),
        ("orbital_shuttle_cockpit", "deep_space", ["instrument_glow", "microgravity"]),
        ("industrial_foundry_floor", "molten_heat", ["sparks", "heat_haze"]),
        ("high_altitude_cable_car", "alpine_blizzard", ["frost_layer", "high_winds"]),
        ("desert_solar_array", "noon_scorch", ["dust_devils", "mirage"]),
        ("cyberpunk_night_market", "neon_drizzle", ["steaming_woks", "neon_halos"]),
        ("bank_vault_antechamber", "sterile_security", ["laser_grid", "polished_granite"]),
        ("dense_pine_forest_ravine", "twilight_mist", ["pine_needles", "fog_banks"]),
    ]

    character_names = [
        ("alex", "Alex Mercer"),
        ("sarah", "Sarah Connor"),
        ("elena", "Elena Rostova"),
        ("jin", "Jin Kazama"),
        ("marcus", "Marcus Cole"),
        ("zara", "Zara Sterling"),
        ("victor", "Victor Vance"),
        ("nadia", "Nadia Petrova"),
    ]

    counter = len(scenarios) + 1
    while len(scenarios) < target_count:
        cat = categories[(counter - 1) % len(categories)]
        loc_name, loc_theme, particulates_list = rng.choice(location_templates)
        cam_move = rng.choice(camera_moves)
        diff = rng.choice(difficulties)

        # Map category to logical complexity level
        if cat in (StressTestCategory.GLASS_REFLECTION_OPTICS, StressTestCategory.FLUID_COLLISION_PHYSICS, StressTestCategory.ANATOMICAL_STRESS):
            complexity = ComplexityLevel.LEVEL_5_DETERMINISTIC_SIM
        elif cat in (StressTestCategory.MULTI_CHARACTER_INTERACTION, StressTestCategory.HAND_OBJECT_HANDOFF):
            complexity = ComplexityLevel.LEVEL_4_3D_BLOCKING
        elif cat == StressTestCategory.RAPID_CAMERA_MOVEMENT:
            complexity = rng.choice([ComplexityLevel.LEVEL_3_2D_TRAJECTORY, ComplexityLevel.LEVEL_4_3D_BLOCKING])
        elif cat == StressTestCategory.TEMPORAL_CONTINUITY:
            complexity = rng.choice([ComplexityLevel.LEVEL_3_2D_TRAJECTORY, ComplexityLevel.LEVEL_4_3D_BLOCKING])
        else:
            complexity = ComplexityLevel(rng.randint(2, 5))

        duration = round(rng.uniform(3.0, 9.0), 1)
        lens = rng.choice([24.0, 35.0, 50.0, 85.0, 105.0])

        # Generate camera coordinates and physically consistent velocity
        if cam_move == CameraMovementType.STATIC:
            cam_start = [round(rng.uniform(-2.0, 2.0), 2), 1.4, round(rng.uniform(-2.0, 0.0), 2)]
            cam_end = list(cam_start)
            vel = 0.0
        else:
            cam_start = [round(rng.uniform(-2.0, 2.0), 2), 1.4, round(rng.uniform(-2.0, -0.5), 2)]
            cam_end = [round(rng.uniform(-2.0, 2.0), 2), 1.4, round(rng.uniform(0.5, 3.0), 2)]
            dist = math.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(cam_start, cam_end)))
            vel = round(max(0.1, dist / duration), 2)

        # Create characters based on category
        chars: List[CharacterDescriptor] = []
        handoff_source = None
        handoff_target = None
        handoff_prop = None
        handoff_start = None
        handoff_end = None

        if cat == StressTestCategory.MULTI_CHARACTER_INTERACTION or cat == StressTestCategory.HAND_OBJECT_HANDOFF:
            c1_id, c1_name = character_names[counter % len(character_names)]
            c2_id, c2_name = character_names[(counter + 1) % len(character_names)]

            prop_name = f"artifact_device_{counter:03d}" if cat == StressTestCategory.HAND_OBJECT_HANDOFF else None
            c1_props = {"right_hand": prop_name} if prop_name else {}

            chars = [
                CharacterDescriptor(
                    id=c1_id,
                    name=c1_name,
                    position=[round(rng.uniform(-1.0, -0.2), 2), 0.0, round(rng.uniform(0.5, 1.5), 2)],
                    facing_angle=round(rng.uniform(20.0, 60.0), 1),
                    eyeline_vector=[0.7, 0.0, 0.7],
                    wardrobe={"main": WardrobeGarment(id=f"suit_{c1_id}", type="outfit", state="weathered")},
                    props=c1_props,
                    action_description="Primary interaction agent",
                ),
                CharacterDescriptor(
                    id=c2_id,
                    name=c2_name,
                    position=[round(rng.uniform(0.2, 1.2), 2), 0.0, round(rng.uniform(1.0, 2.0), 2)],
                    facing_angle=round(rng.uniform(200.0, 240.0), 1),
                    eyeline_vector=[-0.7, 0.0, -0.7],
                    wardrobe={"main": WardrobeGarment(id=f"suit_{c2_id}", type="outfit", state="standard")},
                    props={},
                    action_description="Secondary interaction agent",
                ),
            ]
            if cat == StressTestCategory.HAND_OBJECT_HANDOFF:
                handoff_source = c1_id
                handoff_target = c2_id
                handoff_prop = prop_name
                handoff_start = round(duration * 0.35, 2)
                handoff_end = round(duration * 0.70, 2)
        elif cat == StressTestCategory.ANATOMICAL_STRESS:
            c1_id, c1_name = character_names[counter % len(character_names)]
            c2_id, c2_name = character_names[(counter + 1) % len(character_names)]
            chars = [
                CharacterDescriptor(
                    id=c1_id,
                    name=c1_name,
                    position=[-0.3, 0.0, 0.0],
                    facing_angle=90.0,
                    eyeline_vector=[1.0, 0.0, 0.0],
                    wardrobe={"main": WardrobeGarment(id=f"gi_{c1_id}", type="gi", state="worn")},
                    action_description="Grapple initiator executing joint articulation",
                ),
                CharacterDescriptor(
                    id=c2_id,
                    name=c2_name,
                    position=[0.3, 0.0, 0.0],
                    facing_angle=270.0,
                    eyeline_vector=[-1.0, 0.0, 0.0],
                    wardrobe={"main": WardrobeGarment(id=f"gi_{c2_id}", type="gi", state="worn")},
                    action_description="Grapple defender in physical lock",
                ),
            ]
        elif cat != StressTestCategory.FLUID_COLLISION_PHYSICS:
            c_id, c_name = character_names[counter % len(character_names)]
            chars = [
                CharacterDescriptor(
                    id=c_id,
                    name=c_name,
                    position=[0.0, 0.0, 1.0],
                    facing_angle=0.0,
                    eyeline_vector=[0.0, 0.0, 1.0],
                    wardrobe={"main": WardrobeGarment(id=f"suit_{c_id}", type="uniform", state="intact")},
                    action_description="Solo focal subject",
                )
            ]

        # Challenges
        selected_challenges = rng.sample(physics_challenges, k=rng.randint(1, 3))

        scenario_id = f"BENCH-GEN-{counter:03d}"
        scenario = AetherScenario(
            id=scenario_id,
            title=f"Stress Test #{counter:03d}: {cat.value.replace('_', ' ').title()} in {loc_name.replace('_', ' ').title()}",
            description=(
                f"Evaluation scenario testing {cat.value} under {diff.value} physical difficulty. "
                f"Features {cam_move.value} camera move ({lens}mm lens) in {loc_theme} environment with "
                f"{len(chars)} characters tracked across {duration}s."
            ),
            category=cat,
            complexity_level=complexity,
            duration_seconds=duration,
            target_fps=24,
            resolution=(1920, 1080),
            scene_variables=SceneVariables(
                location=loc_name,
                time_of_day="variable",
                environment=EnvironmentLighting(
                    ambient_description=f"dynamic_lighting_{loc_theme}",
                    color_temperature_k=rng.randint(2000, 7500),
                    strobe_frequency_hz=round(rng.uniform(0.0, 1.5), 1),
                    contrast_ratio=round(rng.uniform(2.0, 5.0), 1),
                ),
                particulates=rng.choice(particulates_list),
                surface=SurfaceProperties(
                    wetness=round(rng.uniform(0.0, 0.9), 2),
                    reflections=rng.choice([True, False]),
                    roughness=round(rng.uniform(0.1, 0.8), 2),
                ),
            ),
            characters=chars,
            camera=CameraParameters(
                lens_mm=lens,
                sensor_format="full_frame",
                aperture_fstop=round(rng.choice([1.4, 2.0, 2.8, 4.0, 5.6]), 1),
                movement_type=cam_move,
                start_position=cam_start,
                end_position=cam_end,
                velocity_mps=vel,
                eyeline_vector=[0.0, 0.0, 1.0],
                focus_distance_m=round(rng.uniform(1.2, 3.5), 2),
            ),
            physics_profile=PhysicsProfile(
                difficulty=diff,
                challenges=selected_challenges,
                optical_refraction_index=1.52 if PhysicsChallengeType.GLASS_REFRACTION in selected_challenges else None,
                fluid_viscosity=0.03 if PhysicsChallengeType.FLUID_DYNAMICS in selected_challenges else None,
            ),
            hard_gate_constraints=HardGateConstraints(
                anatomical_integrity=True,
                character_identity_preservation=bool(chars),
                prop_continuity=bool(handoff_prop),
                handoff_prop_id=handoff_prop,
                handoff_source_character=handoff_source,
                handoff_target_character=handoff_target,
                handoff_window_start_sec=handoff_start,
                handoff_window_end_sec=handoff_end,
                lip_sync_alignment=False,
            ),
            temporal_constraints=TemporalContinuityConstraints(
                max_optical_flow_jitter=0.15,
                min_ssim_frame_to_frame=0.80,
                max_flicker_ratio=0.08,
            ),
            soft_scoring_spec=SoftScoringSpec(
                min_cinematography=8.0,
                min_visual_aesthetic=8.0,
                min_narrative_pacing=8.0,
                min_aggregate_score=8.0,
            ),
            tags=[cat.value.lower(), loc_name, f"diff_{diff.value.lower()}"],
            expected_repair_strategy_on_failure=rng.choice(list(RepairStrategy)),
            metadata={"seed": seed, "generation_index": counter},
        )
        scenarios.append(scenario)
        counter += 1

    return scenarios


def populate_registry_with_benchmarks(
    registry: Optional[ScenarioRegistry] = None,
    include_generated_250: bool = False,
    allow_overwrite: bool = True,
) -> int:
    """Populate a registry with benchmark scenarios.

    Args:
        registry: Target ScenarioRegistry (defaults to global default_registry).
        include_generated_250: If True, populates all 250 standardized benchmark scenarios.
                               If False, populates the foundational gold-standard 8 scenarios.
        allow_overwrite: Whether to overwrite scenarios if already present.

    Returns:
        Count of registered scenarios.
    """
    target_registry = registry if registry is not None else get_default_registry()
    scenarios = generate_benchmark_suite(target_count=250) if include_generated_250 else get_gold_standard_scenarios()
    return target_registry.register_many(scenarios, allow_overwrite=allow_overwrite)
