"""
Test Suite: Closed-Loop Automated Layout Repair (Phase 3)
Verifies deterministic AST mutations, bounds clamping, rescaling, copy truncation,
and convergence within <= 3 iterations.
"""

import pytest

from pipeline.qa.closed_loop_repair import ClosedLoopRepairEngine, repair_engine
from pipeline.qa.tier1_cv_gatekeeper import (
    Tier1AuditReport,
    GatekeeperVerdict,
    GatekeeperViolation
)
from pipeline.qa.tier2_vlm_council import Tier2VLMCouncil
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
    THEME_CYBER_CYAN
)


@pytest.fixture
def flawed_vsg() -> VideoSceneGraphIR:
    canvas = CanvasMetadata(
        width_px=1080,
        height_px=1920,
        fps=60,
        duration_seconds=3.0,
        total_frames=180
    )
    audio = AudioMetadata(
        master_voiceover_path="audio/voice.wav",
        sample_rate_hz=24000,
        music_ducking_db=-18.0
    )
    meta = ProjectMetadata(
        project_id="test_repair_short",
        title="Flawed Short Needing Repair",
        domain_taxonomy="frontier_ai_architectures",
        canvas=canvas,
        audio=audio
    )
    beat = BeatAST(
        beat_id=1,
        time_range=TimeRange(
            start_sec=0.0,
            end_sec=3.0,
            start_frame=0,
            end_frame=180
        ),
        narrative=NarrativeInfo(
            spoken_text="DeepSeek V3 routes 8 experts dynamically.",
            intent="Explain routing",
            visual_metaphor="MoERouterMatrix",
            primary_focus_node_id="hud_flawed"
        ),
        layout_containers=[
            LayoutContainer(
                container_id="c_stage",
                band=BandType.BAND_3_STAGE,
                # Safe-zone breach: y_min is 1500 (inside bottom exclusion zone 1420-1920)
                bounds=BoundingBoxPx(
                    x_min_px=140,
                    y_min_px=1500,
                    width_px=800,
                    height_px=300
                ),
                nodes=[
                    VisualNode(
                        id="hud_flawed",
                        node_type=NodeType.GLASS_HUD_CARD,
                        props={
                            "title": "FLAWED NODE",
                            # Exceeds word cap: 22 words
                            "bodyText": "This is an extremely wordy sentence that goes on and on and introduces severe cognitive clutter and split attention overload for the viewer."
                        },
                        bounds=BoundingBoxPx(
                            x_min_px=140,
                            y_min_px=1500,
                            width_px=800,
                            height_px=300
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


class TestClosedLoopRepair:

    def test_repair_safe_zone_clamping(self, flawed_vsg: VideoSceneGraphIR):
        engine = ClosedLoopRepairEngine()

        # Simulate Tier 1 CV Gatekeeper Safe Zone Violation
        violation = GatekeeperViolation(
            rule="SAFE_ZONE_BREACH",
            message="Node 'hud_flawed' overlaps mobile bottom exclusion mask",
            target_id="hud_flawed",
            metrics={"box": [140, 1500, 940, 1800]}
        )
        t1_rep = Tier1AuditReport(
            verdict=GatekeeperVerdict.FAIL,
            frame_index=0,
            latency_ms=12.5,
            violations=[violation]
        )

        repaired, ledger = engine.repair_ast(flawed_vsg, tier1_reports=[t1_rep], current_iteration=1)

        assert ledger.total_iterations == 1
        assert len(ledger.patches) > 0

        # Check bounds clamped out of bottom exclusion zone (< 1420)
        repaired_node = repaired.beats[0].layout_containers[0].nodes[0]
        assert repaired_node.bounds.y_min_px <= engine.SAFE_Y_MAX - repaired_node.bounds.height_px
        assert repaired_node.bounds.y_min_px < 1420

    def test_repair_text_truncation(self, flawed_vsg: VideoSceneGraphIR):
        engine = ClosedLoopRepairEngine()
        council = Tier2VLMCouncil()

        # VLM council detects excessive word count
        t2_rep = council.evaluate_beat(flawed_vsg.beats[0], flawed_vsg)
        assert not t2_rep.passed_hard_gate

        repaired, ledger = engine.repair_ast(flawed_vsg, tier2_reports=[t2_rep], current_iteration=1)

        repaired_node = repaired.beats[0].layout_containers[0].nodes[0]
        repaired_text = repaired_node.props["bodyText"]
        words = repaired_text.split()
        assert len(words) <= 13  # truncated to <= 12 plus ellipsis

    def test_repair_convergence_within_3_iterations(self, flawed_vsg: VideoSceneGraphIR):
        engine = ClosedLoopRepairEngine()
        council = Tier2VLMCouncil()

        current_vsg = flawed_vsg
        converged = False

        for iter_num in range(1, 4):
            t2_rep = council.evaluate_beat(current_vsg.beats[0], current_vsg)
            if t2_rep.passed_hard_gate:
                converged = True
                break

            current_vsg, ledger = engine.repair_ast(current_vsg, tier2_reports=[t2_rep], current_iteration=iter_num)

        assert converged is True
        assert iter_num <= 3

    def test_repair_collision_rescaling(self, flawed_vsg: VideoSceneGraphIR):
        """Verifies that AABB_SPATIAL_COLLISION with composite target_id 'node_a vs node_b' is repaired."""
        engine = ClosedLoopRepairEngine()
        orig_w = flawed_vsg.beats[0].layout_containers[0].nodes[0].bounds.width_px
        violation = GatekeeperViolation(
            rule="AABB_SPATIAL_COLLISION",
            message="Collision detected between nodes 'hud_flawed' and 'other_node'",
            target_id="hud_flawed vs other_node",
            metrics={"iou": 0.25}
        )
        t1_rep = Tier1AuditReport(
            verdict=GatekeeperVerdict.FAIL,
            frame_index=0,
            latency_ms=15.0,
            violations=[violation]
        )
        repaired, ledger = engine.repair_ast(flawed_vsg, tier1_reports=[t1_rep], current_iteration=1)
        assert len(ledger.patches) >= 1
        assert ledger.patches[0].action == "RESCALE"
        repaired_node = repaired.beats[0].layout_containers[0].nodes[0]
        assert repaired_node.bounds.width_px < orig_w

    def test_repair_theme_materials_rescaling(self, flawed_vsg: VideoSceneGraphIR):
        """Verifies that theme material rescale patches are applied to the AST."""
        from pipeline.qa.tier2_vlm_council import PrescribedPatch, GatekeeperCriticEvaluation, Tier2CouncilReport
        engine = ClosedLoopRepairEngine()
        flawed_vsg.theme.materials.card_blur_px = 8.0
        patch = PrescribedPatch(
            action="RESCALE",
            target_path="theme.materials.card_blur_px",
            patch_value=24.0,
            rationale="Restore 24px frosted glass blur"
        )
        eval_item = GatekeeperCriticEvaluation(
            critic_id="AestheticQualityCritic",
            beat_id=1,
            frame_index=0,
            scores={"depth": 5.0},
            composite_score=5.0,
            passed_hard_gate=False,
            prescribed_patches=[patch]
        )
        t2_rep = Tier2CouncilReport(
            beat_id=1,
            frame_index=0,
            composite_council_score=5.0,
            passed_hard_gate=False,
            critic_evaluations={"AestheticQualityCritic": eval_item},
            passed_critics=[],
            failed_critics=["AestheticQualityCritic"],
            summary_verdict="REJECTED_TRIPPED_GATE"
        )
        repaired, ledger = engine.repair_ast(flawed_vsg, tier2_reports=[t2_rep], current_iteration=1)
        assert len(ledger.patches) == 1
        assert ledger.patches[0].action == "RESCALE"
        assert repaired.theme.materials.card_blur_px == 24.0

