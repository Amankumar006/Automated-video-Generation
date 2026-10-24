"""
The Model Verse — Tests for Pre-Render AST Linter & PBD Collision Solver
"""

import pytest
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
    THEME_CYBER_CYAN,
    BeatAST,
    TimeRange,
    NarrativeInfo,
    LayoutContainer,
    VisualNode,
    NodeType,
    MotionTrack,
    EnterMotion,
    BandType,
    BoundingBoxPx
)
from pipeline.vsg.linter import (
    VSGASTLinter,
    SAFE_ZONE_X_MIN,
    SAFE_ZONE_X_MAX,
    SAFE_ZONE_Y_MIN,
    SAFE_ZONE_Y_MAX,
    MAX_WORDS_PER_CARD
)


def get_base_ast() -> VideoSceneGraphIR:
    return VideoSceneGraphIR(
        metadata=ProjectMetadata(
            project_id="test_linter_proj",
            title="Linter Test Project",
            canvas=CanvasMetadata(width_px=1080, height_px=1920, fps=60, duration_seconds=10.0, total_frames=600),
            audio=AudioMetadata(master_voiceover_path="public/audio/test.wav", sample_rate_hz=24000)
        ),
        theme=THEME_CYBER_CYAN,
        beats=[
            BeatAST(
                beat_id=1,
                time_range=TimeRange(start_sec=0.0, end_sec=5.0, start_frame=0, end_frame=300),
                narrative=NarrativeInfo(
                    spoken_text="Valid spoken narration for beat 1.",
                    intent="Introduce concept",
                    visual_metaphor="Single clean card",
                    primary_focus_node_id="node_valid"
                ),
                layout_containers=[
                    LayoutContainer(
                        container_id="c_valid",
                        band=BandType.BAND_3_STAGE,
                        bounds=BoundingBoxPx(x_min_px=200, y_min_px=400, width_px=680, height_px=600),
                        nodes=[
                            VisualNode(
                                id="node_valid",
                                node_type=NodeType.GLASS_HUD_CARD,
                                props={"headline": "Clean Card", "label": "Verified"},
                                bounds=BoundingBoxPx(x_min_px=220, y_min_px=420, width_px=640, height_px=300),
                                motion_track=MotionTrack(enter=EnterMotion(start_frame=0, duration_frames=20))
                            )
                        ]
                    )
                ]
            )
        ]
    )


class TestVSGASTLinter:
    def test_valid_ast_passes_cleanly(self):
        ast = get_base_ast()
        linter = VSGASTLinter()
        report = linter.lint(ast)
        assert report.is_valid
        assert report.error_count == 0

    def test_rule_of_one_focus_node_missing(self):
        ast = get_base_ast()
        ast.beats[0].narrative.primary_focus_node_id = "non_existent_node"
        linter = VSGASTLinter()
        report = linter.lint(ast)
        assert not report.is_valid
        assert any(v.rule == "RULE_OF_ONE_FOCUS" for v in report.violations)

    def test_word_density_cap_violation(self):
        ast = get_base_ast()
        # Card with 20 words (exceeds MAX_WORDS_PER_CARD of 14)
        wordy_text = "This is an extremely long and verbose explanation that completely violates the maximum word count constraint by containing far too many words"
        ast.beats[0].layout_containers[0].nodes[0].props["headline"] = wordy_text

        linter = VSGASTLinter()
        report = linter.lint(ast)
        assert not report.is_valid
        assert any(v.rule == "CARD_WORD_DENSITY" for v in report.violations)

    def test_safe_zone_breach_detection(self):
        ast = get_base_ast()
        # Place container in bottom exclusion zone (y_max > 1420)
        ast.beats[0].layout_containers[0].bounds = BoundingBoxPx(
            x_min_px=200, y_min_px=1300, width_px=600, height_px=400  # y_max = 1700
        )
        linter = VSGASTLinter()
        report = linter.lint(ast)
        assert not report.is_valid
        assert any(v.rule == "CONTAINER_SAFE_ZONE" for v in report.violations)

    def test_aabb_collision_detection_and_pbd_relaxation(self):
        ast = get_base_ast()
        # Add a second overlapping node in the same container
        node1 = ast.beats[0].layout_containers[0].nodes[0]
        node1.bounds = BoundingBoxPx(x_min_px=300, y_min_px=500, width_px=400, height_px=200)

        node2 = VisualNode(
            id="node_colliding",
            node_type=NodeType.METRIC_PILL,
            props={"label": "Overlapping Pill"},
            bounds=BoundingBoxPx(x_min_px=350, y_min_px=550, width_px=300, height_px=100),
            motion_track=MotionTrack(enter=EnterMotion(start_frame=10, duration_frames=20))
        )
        ast.beats[0].layout_containers[0].nodes.append(node2)

        linter = VSGASTLinter()
        # Test detection without auto-relaxation
        report_no_relax = linter.lint(ast, auto_relax_pbd=False)
        assert not report_no_relax.is_valid
        assert any(v.rule == "AABB_COLLISION" for v in report_no_relax.violations)

        # Test automatic PBD relaxation
        report_relaxed = linter.lint(ast, auto_relax_pbd=True)
        assert report_relaxed.auto_relaxed
        assert report_relaxed.is_valid
        assert report_relaxed.relaxed_ast is not None

        # Verify relaxed nodes no longer intersect
        rel_beat = report_relaxed.relaxed_ast.beats[0]
        rel_nodes = rel_beat.all_nodes()
        rel_box1 = rel_nodes[0].bounds
        rel_box2 = rel_nodes[1].bounds
        assert not rel_box1.intersects(rel_box2)
        assert rel_box1.intersection_iou(rel_box2) == 0.0
