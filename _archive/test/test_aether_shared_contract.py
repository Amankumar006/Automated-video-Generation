"""Unit Tests for Project Aether & The Model Verse Shorts Shared Contracts.

Verifies:
1. EducationalAssetRole & EducationalAssetConditioningPackage schemas and methods.
2. HybridRenderMode & DualEnginePipelineConfig models and beat allocation resolution.
3. ScriptToFilmSceneAdapter conversions:
   - VideoSpec -> DirectorProductionBrief
   - BeatSpec -> ShotRequirement & FilmScene
   - Paper figure dict -> EducationalAssetConditioningPackage
   - Conditioning package application to ShotRequirement (Levels 1-4, PIP, Plate, HUD)
   - Reverse outline conversion (DirectorProductionBrief -> VideoSpec outline)
4. Edge cases, duck typing, and Pydantic V2 validations.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from aether.compiler.schemas import (
    ComplexityLevel,
    ShotRequirement,
)
from aether.director.schemas import (
    DirectorProductionBrief,
    FilmScene,
)
from aether.shared_contract import (
    DualEnginePipelineConfig,
    EducationalAssetConditioningPackage,
    EducationalAssetRole,
    HybridRenderMode,
    ScriptToFilmSceneAdapter,
)
from pipeline.schemas import (
    BeatSpec,
    SFXCue,
    VideoCategory,
    VideoSpec,
)


class TestEducationalAssetConditioningPackage:
    """Tests for EducationalAssetConditioningPackage and EducationalAssetRole."""

    def test_role_enum_values_and_str(self):
        assert EducationalAssetRole.LEVEL_1_REFERENCE_IMAGE.value == "LEVEL_1_REFERENCE_IMAGE"
        assert str(EducationalAssetRole.LEVEL_1_REFERENCE_IMAGE) == "LEVEL_1_REFERENCE_IMAGE"
        assert EducationalAssetRole.PICTURE_IN_PICTURE_OVERLAY.value == "PIP_OVERLAY"
        assert EducationalAssetRole.BACKGROUND_PROJECTION_PLATE.value == "BACKGROUND_PLATE"
        assert EducationalAssetRole.CHALKBOARD_HUD.value == "CHALKBOARD_HUD"

    def test_package_initialization_and_type_checks(self):
        pkg = EducationalAssetConditioningPackage(
            asset_id="fig_arch_01",
            role=EducationalAssetRole.LEVEL_1_REFERENCE_IMAGE,
            file_uri="public/arxiv_cache/2407.08608/fig_1.svg",
            source_beat_id=3,
            media_type="image/svg+xml",
            caption="Attention Architecture Diagram",
        )
        assert pkg.is_vector() is True
        assert pkg.is_raster() is False
        assert pkg.is_video() is False
        assert pkg.caption == "Attention Architecture Diagram"

    def test_raster_and_video_type_checks(self):
        png_pkg = EducationalAssetConditioningPackage(
            asset_id="raster_01",
            role=EducationalAssetRole.LEVEL_1_REFERENCE_IMAGE,
            file_uri="public/figures/figure_1.png",
            media_type="image/png",
        )
        assert png_pkg.is_raster() is True
        assert png_pkg.is_vector() is False
        assert png_pkg.is_video() is False

        video_pkg = EducationalAssetConditioningPackage(
            asset_id="hud_anim_01",
            role=EducationalAssetRole.PICTURE_IN_PICTURE_OVERLAY,
            file_uri="public/manim_renders/beat_3_hud.mp4",
            media_type="video/mp4",
        )
        assert video_pkg.is_video() is True
        assert video_pkg.is_raster() is False
        assert video_pkg.is_vector() is False

    def test_spatial_bounds_validation(self):
        # Valid bounds
        pkg = EducationalAssetConditioningPackage(
            asset_id="pip_01",
            role=EducationalAssetRole.PICTURE_IN_PICTURE_OVERLAY,
            file_uri="diagram.png",
            spatial_bounds=[0.1, 0.2, 0.8, 0.9],
        )
        assert pkg.spatial_bounds == [0.1, 0.2, 0.8, 0.9]

        # Invalid length
        with pytest.raises(ValueError, match="must contain exactly 4 floats"):
            EducationalAssetConditioningPackage(
                asset_id="err_01",
                role=EducationalAssetRole.PICTURE_IN_PICTURE_OVERLAY,
                file_uri="diagram.png",
                spatial_bounds=[0.1, 0.2, 0.8],
            )

        # Coordinate out of [0, 1] range
        with pytest.raises(ValueError, match="coordinates must be in"):
            EducationalAssetConditioningPackage(
                asset_id="err_02",
                role=EducationalAssetRole.PICTURE_IN_PICTURE_OVERLAY,
                file_uri="diagram.png",
                spatial_bounds=[-0.1, 0.2, 0.8, 0.9],
            )

        # Inverted x coordinates (x1 >= x2)
        with pytest.raises(ValueError, match="positive area"):
            EducationalAssetConditioningPackage(
                asset_id="err_03",
                role=EducationalAssetRole.PICTURE_IN_PICTURE_OVERLAY,
                file_uri="diagram.png",
                spatial_bounds=[0.8, 0.1, 0.2, 0.9],
            )

        # Inverted y coordinates (y1 >= y2)
        with pytest.raises(ValueError, match="positive area"):
            EducationalAssetConditioningPackage(
                asset_id="err_04",
                role=EducationalAssetRole.PICTURE_IN_PICTURE_OVERLAY,
                file_uri="diagram.png",
                spatial_bounds=[0.1, 0.9, 0.5, 0.2],
            )

        # Zero area box
        with pytest.raises(ValueError, match="positive area"):
            EducationalAssetConditioningPackage(
                asset_id="err_05",
                role=EducationalAssetRole.PICTURE_IN_PICTURE_OVERLAY,
                file_uri="diagram.png",
                spatial_bounds=[0.5, 0.5, 0.5, 0.5],
            )

    def test_from_figure_dict_raster_preferred(self):
        fig_dict = {
            "caption": "Transformer Decoder Stack",
            "page_num": 3,
            "svg_path": "public/arxiv/fig_1.svg",
            "image_path": "public/arxiv/fig_1.png",
            "original_type": "pdf",
            "score": 0.95,
        }
        pkg = EducationalAssetConditioningPackage.from_figure_dict(
            fig=fig_dict,
            beat_id=3,
            role=EducationalAssetRole.LEVEL_1_REFERENCE_IMAGE,
            prefer_vector=False,
        )
        assert pkg.file_uri == "public/arxiv/fig_1.png"
        assert pkg.media_type == "image/png"
        assert pkg.source_beat_id == 3
        assert pkg.caption == "Transformer Decoder Stack"
        assert pkg.complexity_level_target == ComplexityLevel.REFERENCE_IMAGE
        assert pkg.metadata["score"] == 0.95

    def test_from_figure_dict_vector_preferred(self):
        fig_dict = {
            "caption": "Sparse Autoencoder Feature Map",
            "page_num": 4,
            "svg_path": "public/arxiv/fig_2.svg",
            "image_path": "public/arxiv/fig_2.png",
            "original_type": "svg",
            "score": 0.88,
        }
        pkg = EducationalAssetConditioningPackage.from_figure_dict(
            fig=fig_dict,
            beat_id=3,
            role=EducationalAssetRole.LEVEL_3_TRAJECTORY_GUIDE,
            prefer_vector=True,
        )
        assert pkg.file_uri == "public/arxiv/fig_2.svg"
        assert pkg.media_type == "image/svg+xml"
        assert pkg.complexity_level_target == ComplexityLevel.TWOD_TRAJECTORY_POSE

    def test_apply_to_shot_level_1_reference(self):
        pkg = EducationalAssetConditioningPackage(
            asset_id="asset_l1",
            role=EducationalAssetRole.LEVEL_1_REFERENCE_IMAGE,
            file_uri="public/figures/hero_plate.png",
            caption="Hero Network Architecture",
        )
        shot = ShotRequirement(shot_id="SHOT_003")
        pkg.apply_to_shot(shot)

        assert shot.first_frame_uri == "public/figures/hero_plate.png"
        assert shot.metadata["reference_image_uri"] == "public/figures/hero_plate.png"
        assert shot.metadata["conditioning_asset_id"] == "asset_l1"
        assert "Hero Network Architecture" in (shot.target_focal_intent or "")

    def test_apply_to_shot_level_2_keyframes(self):
        start_pkg = EducationalAssetConditioningPackage(
            asset_id="asset_l2_s",
            role=EducationalAssetRole.LEVEL_2_KEYFRAME_START,
            file_uri="frame_start.png",
        )
        end_pkg = EducationalAssetConditioningPackage(
            asset_id="asset_l2_e",
            role=EducationalAssetRole.LEVEL_2_KEYFRAME_END,
            file_uri="frame_end.png",
        )
        shot = ShotRequirement(shot_id="SHOT_004")
        start_pkg.apply_to_shot(shot)
        end_pkg.apply_to_shot(shot)

        assert shot.first_frame_uri == "frame_start.png"
        assert shot.last_frame_uri == "frame_end.png"

    def test_apply_to_shot_pip_and_hud(self):
        pip_pkg = EducationalAssetConditioningPackage(
            asset_id="asset_pip",
            role=EducationalAssetRole.PICTURE_IN_PICTURE_OVERLAY,
            file_uri="chalkboard_overlay.png",
            spatial_bounds=[0.6, 0.1, 0.9, 0.4],
        )
        hud_pkg = EducationalAssetConditioningPackage(
            asset_id="asset_hud",
            role=EducationalAssetRole.CHALKBOARD_HUD,
            file_uri="hud_card.svg",
        )
        shot = ShotRequirement(shot_id="SHOT_005")
        pip_pkg.apply_to_shot(shot)
        hud_pkg.apply_to_shot(shot)

        assert "pip_overlay" in shot.metadata
        assert shot.metadata["pip_overlay"]["uri"] == "chalkboard_overlay.png"
        assert shot.metadata["pip_overlay"]["bounds"] == [0.6, 0.1, 0.9, 0.4]

        assert "chalkboard_hud" in shot.metadata
        assert shot.metadata["chalkboard_hud"]["uri"] == "hud_card.svg"


class TestHybridRenderModeAndConfig:
    """Tests for HybridRenderMode and DualEnginePipelineConfig."""

    def test_render_mode_values(self):
        assert HybridRenderMode.PURE_MANIM_2D.value == "PURE_MANIM_2D"
        assert HybridRenderMode.PURE_AETHER_3D.value == "PURE_AETHER_3D"
        assert HybridRenderMode.HYBRID_COMPOSITE.value == "HYBRID_COMPOSITE"
        assert HybridRenderMode.DUAL_STREAM_PIP.value == "DUAL_STREAM_PIP"
        assert HybridRenderMode.SEQUENTIAL_ALTERNATING.value == "SEQUENTIAL_ALTERNATING"

    def test_config_defaults_and_beat_resolution(self):
        cfg = DualEnginePipelineConfig()
        assert cfg.default_mode == HybridRenderMode.HYBRID_COMPOSITE
        assert cfg.get_beat_mode(1) == HybridRenderMode.HYBRID_COMPOSITE
        assert cfg.is_hybrid() is True
        assert cfg.framerate == 60
        assert cfg.resolution == "1440x2560"

    def test_config_per_beat_overrides(self):
        cfg = DualEnginePipelineConfig(
            default_mode=HybridRenderMode.PURE_AETHER_3D,
            beat_modes={
                1: HybridRenderMode.PURE_AETHER_3D,
                3: HybridRenderMode.PURE_MANIM_2D,
                5: HybridRenderMode.HYBRID_COMPOSITE,
            },
        )
        assert cfg.get_beat_mode(1) == HybridRenderMode.PURE_AETHER_3D
        assert cfg.get_beat_mode(2) == HybridRenderMode.PURE_AETHER_3D  # fallback to default
        assert cfg.get_beat_mode(3) == HybridRenderMode.PURE_MANIM_2D
        assert cfg.get_beat_mode(5) == HybridRenderMode.HYBRID_COMPOSITE
        assert cfg.is_hybrid() is True

    def test_pure_non_hybrid_config(self):
        cfg = DualEnginePipelineConfig(
            default_mode=HybridRenderMode.PURE_MANIM_2D,
            beat_modes={1: HybridRenderMode.PURE_MANIM_2D, 2: HybridRenderMode.PURE_MANIM_2D},
        )
        assert cfg.is_hybrid() is False

    def test_config_field_validations(self):
        # Invalid hud_safe_bounds (out of range)
        with pytest.raises(ValueError, match="coordinates must be in"):
            DualEnginePipelineConfig(hud_safe_bounds=[-0.1, 0.1, 0.9, 0.9])

        # Invalid hud_safe_bounds (inverted)
        with pytest.raises(ValueError, match="positive area"):
            DualEnginePipelineConfig(hud_safe_bounds=[0.9, 0.1, 0.1, 0.9])

        # Invalid audio_master
        with pytest.raises(ValueError, match="audio_master must be one of"):
            DualEnginePipelineConfig(audio_master="invalid_audio_engine")

        # Invalid blend_mode
        with pytest.raises(ValueError, match="blend_mode must be one of"):
            DualEnginePipelineConfig(blend_mode="destroy_mode")

        # Invalid beat_modes key (non-positive int)
        with pytest.raises(ValueError, match="positive integers"):
            DualEnginePipelineConfig(beat_modes={0: HybridRenderMode.PURE_MANIM_2D})

        with pytest.raises(ValueError, match="positive integers"):
            DualEnginePipelineConfig(beat_modes={-1: HybridRenderMode.PURE_MANIM_2D})


class TestScriptToFilmSceneAdapter:
    """Tests for ScriptToFilmSceneAdapter conversions."""

    @pytest.fixture
    def sample_video_spec(self) -> VideoSpec:
        return VideoSpec(
            id="spec_test_radix",
            title="RadixAttention: Fast KV-Cache Tree Search",
            category=VideoCategory.ARCHITECTURE_BREAKDOWN,
            hook_tag="Speeding up LLMs by 10x",
            beats=[
                BeatSpec(
                    beat_id=1,
                    text="Every time you chat with an LLM, it recomputes shared system prompts.",
                    visual_focus="Visualizing redundant token KV caches flooding GPU memory",
                    camera_action="dolly_in",
                    expected_duration=5.0,
                ),
                BeatSpec(
                    beat_id=2,
                    text="Standard linear memory allocators cause severe fragmentation.",
                    visual_focus="Memory fragmentation heat map showing trapped wasted VRAM",
                    camera_action="orbit",
                    expected_duration=5.5,
                ),
                BeatSpec(
                    beat_id=3,
                    text="RadixAttention organizes KV caches into an adaptive prefix radix tree.",
                    visual_focus="Radix tree nodes dynamically merging shared prompt branches",
                    camera_action="pan",
                    expected_duration=6.0,
                ),
                BeatSpec(
                    beat_id=4,
                    text="Here is the core CUDA radix cache kernel in under thirty lines.",
                    visual_focus="Syntax-highlighted CUDA C++ kernel scanning active line sweeps",
                    camera_action="static",
                    expected_duration=5.0,
                ),
                BeatSpec(
                    beat_id=5,
                    text="Look at the benchmark showdown: 5x higher throughput under multi-turn chat.",
                    visual_focus="Horizontal Drag-Race bars showing RadixAttention versus vLLM",
                    camera_action="crane",
                    expected_duration=5.5,
                ),
                BeatSpec(
                    beat_id=6,
                    text="Radix trees unlock zero-overhead multi-turn serving for next-gen agents.",
                    visual_focus="Contemplative vista of autonomous AI agent server farms",
                    camera_action="dolly_out",
                    expected_duration=4.5,
                ),
            ],
            sfx_cues=[
                SFXCue(timestamp=0.1, sound_type="sub_impact", volume=0.5),
                SFXCue(timestamp=10.5, sound_type="whoosh", volume=0.3),
            ],
            metadata={
                "paper_figures": [
                    {
                        "caption": "Radix Tree Memory Architecture",
                        "page_num": 4,
                        "svg_path": "public/arxiv_cache/radix/fig_1.svg",
                        "image_path": "public/arxiv_cache/radix/fig_1.png",
                        "score": 0.94,
                    }
                ]
            },
        )

    def test_beat_cinematic_mapping_completeness(self):
        mapping = ScriptToFilmSceneAdapter.BEAT_CINEMATIC_MAPPING
        assert len(mapping) == 6
        for beat_id in range(1, 7):
            assert beat_id in mapping
            beat_cfg = mapping[beat_id]
            assert "scene_id" in beat_cfg
            assert "location" in beat_cfg
            assert "lighting" in beat_cfg
            assert "camera_movement" in beat_cfg
            assert "complexity_level" in beat_cfg

    def test_extract_conditioning_assets(self, sample_video_spec: VideoSpec):
        packages = ScriptToFilmSceneAdapter.extract_conditioning_assets(sample_video_spec)
        assert len(packages) >= 1
        pkg = packages[0]
        assert pkg.source_beat_id == 3
        assert "fig_1.png" in pkg.file_uri
        assert pkg.caption == "Radix Tree Memory Architecture"
        assert pkg.role == EducationalAssetRole.LEVEL_1_REFERENCE_IMAGE

    def test_convert_beat_to_shot(self, sample_video_spec: VideoSpec):
        beat1 = sample_video_spec.beats[0]
        shot = ScriptToFilmSceneAdapter.convert_beat_to_shot(
            beat=beat1,
            spec_title=sample_video_spec.title,
            aspect_ratio="9:16",
        )
        assert shot.shot_id == "SHOT_001"
        assert shot.target_duration == 5.0
        assert shot.aspect_ratio == "9:16"
        assert shot.camera_movement == "dolly_in"
        assert shot.audio.dialogue is True
        assert shot.audio.dialogue_transcript == beat1.text
        assert shot.metadata["source_beat_id"] == 1

    def test_convert_beat_to_film_scene(self, sample_video_spec: VideoSpec):
        beat3 = sample_video_spec.beats[2]
        scene = ScriptToFilmSceneAdapter.convert_beat_to_film_scene(
            beat=beat3,
            spec_title=sample_video_spec.title,
        )
        assert scene.scene_id == "SC_003_MECHANISM"
        assert "SC_003" in scene.scene_id
        assert len(scene.shot_list_requirements) == 1
        assert scene.duration == 6.0
        assert "Holographic" in scene.location or "Virtual" in scene.location
        assert scene.metadata["source_beat_id"] == 3

    def test_convert_spec_to_scenes(self, sample_video_spec: VideoSpec):
        scenes = ScriptToFilmSceneAdapter.convert_spec_to_scenes(sample_video_spec)
        assert len(scenes) == 6
        assert scenes[0].scene_id == "SC_001_HOOK"
        assert scenes[1].scene_id == "SC_002_BOTTLENECK"
        assert scenes[2].scene_id == "SC_003_MECHANISM"
        assert scenes[3].scene_id == "SC_004_CODE"
        assert scenes[4].scene_id == "SC_005_SHOWDOWN"
        assert scenes[5].scene_id == "SC_006_OUTRO"

        # Check conditioning applied to Beat 3 scene
        beat3_shot = scenes[2].shot_list_requirements[0]
        assert beat3_shot.first_frame_uri is not None
        assert "fig_1.png" in beat3_shot.first_frame_uri

    def test_convert_spec_to_brief(self, sample_video_spec: VideoSpec):
        brief = ScriptToFilmSceneAdapter.convert_spec_to_brief(
            spec=sample_video_spec,
            visual_style="dark cyberpunk tech documentary",
            target_models=["veo_3_1", "kling_3_0"],
            aspect_ratio="9:16",
        )
        assert isinstance(brief, DirectorProductionBrief)
        assert brief.title == sample_video_spec.title
        assert brief.aspect_ratio == "9:16"
        assert brief.visual_style == "dark cyberpunk tech documentary"
        assert len(brief.scenes) == 6
        assert brief.target_models == ["veo_3_1", "kling_3_0"]
        assert brief.metadata["is_adapted_educational_short"] is True
        assert brief.metadata["category"] == "architecture_breakdown"

        # Check total duration calculation
        expected_total = sum(b.expected_duration for b in sample_video_spec.beats)
        assert brief.target_duration == pytest.approx(expected_total)

    def test_convert_spec_dict_without_models(self):
        spec_dict = {
            "id": "spec_dict_01",
            "title": "BitNet b1.58: 1-Bit LLMs",
            "category": "mechanism_deepdive",
            "hook_tag": "Zero multiplications at inference",
            "beats": [
                {
                    "beat_id": 1,
                    "text": "What if neural networks used zero floating-point multiplications?",
                    "visual_focus": "Floating point multiplication matrix crumbling into ternary gates",
                    "expected_duration": 4.5,
                },
                {
                    "beat_id": 2,
                    "text": "FP16 weights consume immense memory bandwidth.",
                    "visual_focus": "Bandwidth saturation meter at maximum throttle",
                    "expected_duration": 5.0,
                },
            ],
            "paper_figures": [
                {
                    "caption": "Ternary Weight Quantization",
                    "page_num": 2,
                    "image_path": "public/figures/bitnet.png",
                }
            ],
        }

        brief = ScriptToFilmSceneAdapter.convert_spec_to_brief(spec_dict)
        assert isinstance(brief, DirectorProductionBrief)
        assert brief.title == "BitNet b1.58: 1-Bit LLMs"
        assert len(brief.scenes) == 2
        assert brief.metadata["source_spec_id"] == "spec_dict_01"

    def test_convert_brief_to_spec_outline_round_trip(self, sample_video_spec: VideoSpec):
        brief = ScriptToFilmSceneAdapter.convert_spec_to_brief(sample_video_spec)
        outline = ScriptToFilmSceneAdapter.convert_brief_to_spec_outline(brief)

        assert outline["title"] == sample_video_spec.title
        assert outline["category"] == "architecture_breakdown"
        assert len(outline["beats"]) == 6
        assert outline["beats"][0]["beat_id"] == 1
        assert "Every time you chat" in outline["beats"][0]["text"]
        assert outline["beats"][0]["camera_action"] == "dolly_in"
        assert outline["beats"][0]["expected_duration"] == 5.0

    def test_pydantic_json_serialization(self, sample_video_spec: VideoSpec):
        brief = ScriptToFilmSceneAdapter.convert_spec_to_brief(sample_video_spec)
        dumped = brief.model_dump_json()
        assert isinstance(dumped, str)
        reconstructed = DirectorProductionBrief.model_validate_json(dumped)
        assert reconstructed.title == brief.title
        assert len(reconstructed.scenes) == 6

    def test_silent_beat_brief_to_outline_does_not_leak_narrative_beat(self):
        brief_dict = {
            "title": "Silent Scene Test",
            "scenes": [
                {
                    "scene_id": "SC_001",
                    "narrative_beat": "Directorial stage instruction that must not be spoken",
                    "shot_list_requirements": [
                        {
                            "shot_id": "SHOT_001",
                            "audio": {
                                "dialogue": False,
                                "dialogue_transcript": None,
                            },
                            "target_focal_intent": "Visual focus intent",
                        }
                    ],
                }
            ],
        }
        outline = ScriptToFilmSceneAdapter.convert_brief_to_spec_outline(brief_dict)
        assert outline["beats"][0]["text"] == ""
        assert outline["beats"][0]["visual_focus"] == "Visual focus intent"

    def test_coerced_beat_id_in_scenes_and_shots(self):
        spec_dict = {
            "title": "Beat ID Coercion Test",
            "beats": [
                {"beat_id": "intro", "text": "Opening", "visual_focus": "Hook"},
                {"beat_id": "2", "text": "Body", "visual_focus": "Mechanism"},
                {"beat_id": None, "text": "Conclusion", "visual_focus": "Wrap"},
            ],
        }
        scenes = ScriptToFilmSceneAdapter.convert_spec_to_scenes(spec_dict)
        assert len(scenes) == 3
        assert scenes[0].scene_id == "SC_001_HOOK"
        assert scenes[1].scene_id == "SC_002_BOTTLENECK"
        assert scenes[2].scene_id == "SC_003_MECHANISM"
        assert scenes[0].shot_list_requirements[0].shot_id == "SHOT_001"
        assert scenes[1].shot_list_requirements[0].shot_id == "SHOT_002"
        assert scenes[2].shot_list_requirements[0].shot_id == "SHOT_003"

    def test_convert_beat_to_film_scene_explicit_complexity(self):
        # Explicit complexity on beat
        scene_explicit = ScriptToFilmSceneAdapter.convert_beat_to_film_scene({
            "beat_id": 1,
            "text": "Simulating black hole collision",
            "visual_focus": "Relativistic spacetime grid",
            "complexity_level": ComplexityLevel.FULL_PHYSICAL_SIMULATION,
        })
        assert scene_explicit.metadata.get("complexity_level") == ComplexityLevel.FULL_PHYSICAL_SIMULATION

        # Explicit complexity from conditioning asset
        pkg = EducationalAssetConditioningPackage(
            asset_id="asset_custom",
            role=EducationalAssetRole.LEVEL_4_SURFACE_TEXTURE,
            file_uri="texture.png",
            source_beat_id=1,
            spatial_bounds=[0.1, 0.1, 0.9, 0.9],
            complexity_level_target=ComplexityLevel.THREED_BLOCKING,
        )
        scene_from_asset = ScriptToFilmSceneAdapter.convert_beat_to_film_scene(
            beat={"beat_id": 1, "text": "Text", "visual_focus": "Focus"},
            conditioning_assets=[pkg],
        )
        assert scene_from_asset.metadata.get("complexity_level") == ComplexityLevel.THREED_BLOCKING
