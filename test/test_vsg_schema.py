"""
The Model Verse — Tests for VSG-IR v1.0.0 Declarative AST Schema
"""

import pytest
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.vsg.schema import (
    VideoSceneGraphIR,
    ProjectMetadata,
    CanvasMetadata,
    AudioMetadata,
    ThemeTokens,
    ThemeId,
    THEME_CYBER_CYAN,
    THEME_NEON_VIOLET,
    THEME_SOLAR_AMBER,
    THEME_DARK_OBSIDIAN,
    BeatAST,
    TimeRange,
    NarrativeInfo,
    AcousticAnchor,
    LayoutContainer,
    VisualNode,
    NodeType,
    MotionTrack,
    EnterMotion,
    FocalHighlight,
    ExitMotion,
    MotionType,
    BandType,
    BoundingBoxPx,
    LinkedSemanticAction
)


def create_sample_ast() -> VideoSceneGraphIR:
    """Helper to build a valid minimal production VSG-IR AST."""
    return VideoSceneGraphIR(
        metadata=ProjectMetadata(
            project_id="deepseek_v3_moe_architecture",
            title="DeepSeek-V3: Multi-Head Latent Attention & Sparse MoE",
            domain_taxonomy="frontier_ai_architectures",
            canvas=CanvasMetadata(
                width_px=1080,
                height_px=1920,
                fps=60,
                duration_seconds=15.0,
                total_frames=900
            ),
            audio=AudioMetadata(
                master_voiceover_path="public/audio/deepseek_v3_narration.wav",
                sample_rate_hz=24000,
                music_ducking_db=-18.0
            )
        ),
        theme=THEME_CYBER_CYAN,
        beats=[
            BeatAST(
                beat_id=1,
                time_range=TimeRange(
                    start_sec=0.0,
                    end_sec=5.0,
                    start_frame=0,
                    end_frame=300
                ),
                narrative=NarrativeInfo(
                    spoken_text="DeepSeek-V3 executes 671 billion parameters, but activates only 37 billion per token.",
                    intent="Hook viewer with parameter scale paradox",
                    visual_metaphor="Hero metric comparison card with sparse active node matrix",
                    primary_focus_node_id="hero_metric_card"
                ),
                acoustic_anchors=[
                    AcousticAnchor(
                        word="DeepSeek-V3",
                        timestamp_sec=0.15,
                        frame_trigger=9,
                        linked_node_id="header_pill",
                        linked_action=LinkedSemanticAction.ENTER
                    ),
                    AcousticAnchor(
                        word="671 billion",
                        timestamp_sec=1.8,
                        frame_trigger=108,
                        linked_node_id="hero_metric_card",
                        linked_action=LinkedSemanticAction.HIGHLIGHT
                    )
                ],
                layout_containers=[
                    LayoutContainer(
                        container_id="c_header",
                        band=BandType.BAND_1_HEADER,
                        bounds=BoundingBoxPx(x_min_px=140, y_min_px=240, width_px=800, height_px=60),
                        nodes=[
                            VisualNode(
                                id="header_pill",
                                node_type=NodeType.METRIC_PILL,
                                props={"label": "DEEPSEEK-V3 ARCHITECTURE LAB"},
                                bounds=BoundingBoxPx(x_min_px=140, y_min_px=240, width_px=400, height_px=50),
                                motion_track=MotionTrack(
                                    enter=EnterMotion(type=MotionType.EASE_OUT_EXPO, start_frame=0, duration_frames=20)
                                )
                            )
                        ]
                    ),
                    LayoutContainer(
                        container_id="c_stage",
                        band=BandType.BAND_3_STAGE,
                        bounds=BoundingBoxPx(x_min_px=140, y_min_px=400, width_px=800, height_px=900),
                        nodes=[
                            VisualNode(
                                id="hero_metric_card",
                                node_type=NodeType.GLASS_HUD_CARD,
                                props={"metric": "671B / 37B Active", "headline": "Sparse MoE Routing"},
                                bounds=BoundingBoxPx(x_min_px=160, y_min_px=450, width_px=760, height_px=320),
                                motion_track=MotionTrack(
                                    enter=EnterMotion(type=MotionType.SPRING_DAMPED, start_frame=15, duration_frames=30),
                                    focal_highlight=FocalHighlight(trigger_frame=108, duration_frames=24, scale_multiplier=1.08)
                                )
                            )
                        ]
                    )
                ]
            )
        ]
    )


class TestVSGIRSchema:
    def test_schema_instantiation_and_validation(self):
        ast = create_sample_ast()
        assert ast.version == "1.0.0"
        assert ast.metadata.project_id == "deepseek_v3_moe_architecture"
        assert len(ast.beats) == 1
        assert ast.metadata.canvas.total_frames == 900
        assert ast.theme.theme_id == ThemeId.CYBER_CYAN

    def test_bounding_box_geometry(self):
        box1 = BoundingBoxPx(x_min_px=100, y_min_px=100, width_px=200, height_px=100)
        assert box1.x_max_px == 300
        assert box1.y_max_px == 200
        assert box1.area_px == 20000

        # Overlapping box
        box2 = BoundingBoxPx(x_min_px=200, y_min_px=150, width_px=200, height_px=100)
        assert box1.intersects(box2)
        iou = box1.intersection_iou(box2)
        assert 0.0 < iou < 1.0

        # Disjoint box
        box3 = BoundingBoxPx(x_min_px=500, y_min_px=500, width_px=100, height_px=100)
        assert not box1.intersects(box3)
        assert box1.intersection_iou(box3) == 0.0

    def test_theme_presets(self):
        assert THEME_CYBER_CYAN.theme_id == ThemeId.CYBER_CYAN
        assert THEME_NEON_VIOLET.theme_id == ThemeId.NEON_VIOLET
        assert THEME_SOLAR_AMBER.theme_id == ThemeId.SOLAR_AMBER
        assert THEME_DARK_OBSIDIAN.theme_id == ThemeId.DARK_OBSIDIAN
        assert THEME_CYBER_CYAN.colors.hero_accent == "#38BDF8"
        assert THEME_NEON_VIOLET.colors.hero_accent == "#A855F7"

    def test_json_round_trip_serialization(self):
        ast = create_sample_ast()
        json_str = ast.to_json()
        assert isinstance(json_str, str)

        parsed = VideoSceneGraphIR.from_json(json_str)
        assert parsed.metadata.project_id == ast.metadata.project_id
        assert len(parsed.beats) == len(ast.beats)
        assert parsed.beats[0].narrative.spoken_text == ast.beats[0].narrative.spoken_text
        assert parsed.theme.colors.canvas_void == ast.theme.colors.canvas_void

    def test_node_query_helpers(self):
        ast = create_sample_ast()
        beat1 = ast.get_beat(1)
        assert beat1 is not None

        node = beat1.get_node("hero_metric_card")
        assert node is not None
        assert node.node_type == NodeType.GLASS_HUD_CARD

        non_existent = beat1.get_node("phantom_node")
        assert non_existent is None

        all_nodes = ast.all_nodes()
        assert len(all_nodes) == 2
        assert {n.id for n in all_nodes} == {"header_pill", "hero_metric_card"}

    def test_json_schema_export(self):
        schema = VideoSceneGraphIR.export_json_schema()
        assert "properties" in schema
        assert "version" in schema["properties"]
        assert "metadata" in schema["properties"]
        assert "theme" in schema["properties"]
        assert "beats" in schema["properties"]
