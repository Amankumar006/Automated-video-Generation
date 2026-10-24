"""
Test Suite: Pluggable Render Adapters & Engine Routing (Phase 2 & Phase 4)
Verifies RemotionBroadcastAdapter, ManimLegacyAdapter, and HybridEngineRouter.
"""

import json
import os
import tempfile
import numpy as np
import pytest

from pipeline.adapters.base_adapter import (
    RenderOptions,
    RenderResult,
    CompiledSceneManifest,
)
from pipeline.adapters.remotion_adapter import RemotionBroadcastAdapter
from pipeline.adapters.manim_adapter import ManimLegacyAdapter
from pipeline.engine_router import HybridEngineRouter
from pipeline.vsg.schema import (
    VideoSceneGraphIR,
    ProjectMetadata,
    CanvasMetadata,
    AudioMetadata,
    TimeRange,
    NarrativeInfo,
    BeatAST,
    LayoutContainer,
    VisualNode,
    NodeType,
    MotionTrack,
    EnterMotion,
    MotionType,
    BandType,
    BoundingBoxPx,
    THEME_CYBER_CYAN,
    THEME_SOLAR_AMBER
)


@pytest.fixture
def sample_vsg() -> VideoSceneGraphIR:
    canvas = CanvasMetadata(
        width_px=1080,
        height_px=1920,
        fps=60,
        duration_seconds=5.0,
        total_frames=300
    )
    audio = AudioMetadata(
        master_voiceover_path="audio/voice.wav",
        sample_rate_hz=24000,
        music_ducking_db=-18.0
    )
    meta = ProjectMetadata(
        project_id="test_showcase_short",
        title="DeepSeek-V3 MoE Architecture Breakdown",
        domain_taxonomy="frontier_ai_architectures",
        canvas=canvas,
        audio=audio
    )
    beat = BeatAST(
        beat_id=1,
        time_range=TimeRange(
            start_sec=0.0,
            end_sec=5.0,
            start_frame=0,
            end_frame=300
        ),
        narrative=NarrativeInfo(
            spoken_text="DeepSeek V3 routes 8 experts dynamically per token.",
            intent="Explain sparse routing mechanism",
            visual_metaphor="MoERouterMatrix",
            primary_focus_node_id="moe_core"
        ),
        layout_containers=[
            LayoutContainer(
                container_id="c_stage",
                band=BandType.BAND_3_STAGE,
                bounds=BoundingBoxPx(
                    x_min_px=140,
                    y_min_px=500,
                    width_px=800,
                    height_px=650
                ),
                nodes=[
                    VisualNode(
                        id="moe_core",
                        node_type=NodeType.MOE_ROUTER_MATRIX,
                        props={"tokenText": "transformer", "totalExperts": 256, "activeRouted": 8},
                        bounds=BoundingBoxPx(
                            x_min_px=140,
                            y_min_px=500,
                            width_px=800,
                            height_px=650
                        ),
                        motion_track=MotionTrack(
                            enter=EnterMotion(
                                type=MotionType.SPRING_DAMPED,
                                start_frame=0,
                                duration_frames=30
                            )
                        )
                    )
                ]
            )
        ]
    )
    return VideoSceneGraphIR(
        version="1.0.0",
        metadata=meta,
        theme=THEME_CYBER_CYAN,
        beats=[beat]
    )


class TestRenderAdapters:

    def test_remotion_adapter_properties(self):
        adapter = RemotionBroadcastAdapter()
        assert adapter.engine_name == "remotion"
        assert adapter.supports_frame_seek is True

    def test_remotion_compile_scene_graph(self, sample_vsg: VideoSceneGraphIR):
        adapter = RemotionBroadcastAdapter()
        with tempfile.TemporaryDirectory() as tmp_dir:
            manifest = adapter.compile_scene_graph(sample_vsg, output_dir=tmp_dir)
            assert manifest.engine_name == "remotion"
            assert manifest.manifest_id == "test_showcase_short"
            assert manifest.total_frames == 300
            assert os.path.exists(manifest.props_file_path)

            with open(manifest.props_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert "vsg" in data
            assert data["vsg"]["metadata"]["title"] == sample_vsg.metadata.title

    def test_remotion_render_still_frame(self, sample_vsg: VideoSceneGraphIR):
        adapter = RemotionBroadcastAdapter()
        manifest = adapter.compile_scene_graph(sample_vsg)

        # Fast still frame seek
        frame_bgr = adapter.render_frame(frame_index=15, manifest=manifest)
        assert isinstance(frame_bgr, np.ndarray)
        assert frame_bgr.shape == (1920, 1080, 3)
        assert frame_bgr.dtype == np.uint8

        # Verify not blank
        assert np.mean(frame_bgr) > 0.0

    def test_manim_adapter_properties_and_compile(self, sample_vsg: VideoSceneGraphIR):
        adapter = ManimLegacyAdapter()
        assert adapter.engine_name == "manim"
        assert adapter.supports_frame_seek is False

        with tempfile.TemporaryDirectory() as tmp_dir:
            manifest = adapter.compile_scene_graph(sample_vsg, output_dir=tmp_dir)
            assert manifest.engine_name == "manim"
            assert os.path.exists(manifest.props_file_path)

            # Test frame generation
            frame = adapter.render_frame(0, manifest)
            assert frame.shape == (1920, 1080, 3)

    def test_hybrid_engine_router(self, sample_vsg: VideoSceneGraphIR):
        router = HybridEngineRouter()

        # 1. Default for systems architecture goes to Remotion
        adapter = router.select_engine(sample_vsg, engine_override="hybrid")
        assert adapter.engine_name == "remotion"

        # 2. Mathematical taxonomy routes to Manim
        math_vsg = sample_vsg.model_copy(deep=True)
        math_vsg.metadata.domain_taxonomy = "differential_geometry_calculus"
        adapter_math = router.select_engine(math_vsg, engine_override="hybrid")
        assert adapter_math.engine_name == "manim"

        # 3. Explicit override flags
        assert router.select_engine(sample_vsg, engine_override="remotion").engine_name == "remotion"
        assert router.select_engine(sample_vsg, engine_override="manim").engine_name == "manim"

    def test_tech_perks_and_news_node_types_render(self, sample_vsg: VideoSceneGraphIR):
        """Verifies Remotion renders still frames containing new Perk and News node types."""
        adapter = RemotionBroadcastAdapter()

        # Build VSG with PerkPortalWindow node
        perk_vsg = sample_vsg.model_copy(deep=True)
        perk_node = VisualNode(
            id="perk_portal",
            node_type=NodeType.PERK_PORTAL_WINDOW,
            props={
                "portalUrl": "anthropic.com/startups",
                "programTitle": "Claude Startups Accelerator",
                "creditValue": "$1,000 FREE CREDITS"
            },
            bounds=BoundingBoxPx(x_min_px=140, y_min_px=500, width_px=760, height_px=650),
            motion_track=MotionTrack(
                enter=EnterMotion(
                    type=MotionType.SPRING_DAMPED,
                    start_frame=0,
                    duration_frames=30
                )
            )
        )
        perk_vsg.beats[0].layout_containers[0].nodes = [perk_node]

        manifest = adapter.compile_scene_graph(perk_vsg)
        frame_bgr = adapter.render_frame(10, manifest)
        assert frame_bgr.shape == (1920, 1080, 3)
        assert np.mean(frame_bgr) > 0.0

