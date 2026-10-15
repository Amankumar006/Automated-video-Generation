"""
Test Suite: Tier 2 Multimodal VLM Critic Council (Phase 3)
Verifies the 4 specialized critics, scoring rubrics, and the binary >= 8.5/10.0 hard gate.
"""

import pytest

from pipeline.qa.tier2_vlm_council import (
    AestheticQualityCritic,
    TypographicHierarchyCritic,
    CognitiveDensityCritic,
    TemporalSyncCritic,
    Tier2VLMCouncil,
    vlm_council
)
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
def clean_vsg() -> VideoSceneGraphIR:
    canvas = CanvasMetadata(
        width_px=1080,
        height_px=1920,
        fps=60,
        duration_seconds=4.0,
        total_frames=240
    )
    audio = AudioMetadata(
        master_voiceover_path="audio/voice.wav",
        sample_rate_hz=24000,
        music_ducking_db=-18.0
    )
    meta = ProjectMetadata(
        project_id="qa_clean_short",
        title="High Precision Broadcast Short",
        domain_taxonomy="frontier_ai_architectures",
        canvas=canvas,
        audio=audio
    )
    beat = BeatAST(
        beat_id=1,
        time_range=TimeRange(
            start_sec=0.0,
            end_sec=3.5,
            start_frame=0,
            end_frame=210
        ),
        narrative=NarrativeInfo(
            spoken_text="DeepSeek V3 routes 8 experts per token with zero latency.",
            intent="Explain sparse routing mechanism",
            visual_metaphor="MoERouterMatrix",
            primary_focus_node_id="hud_1"
        ),
        layout_containers=[
            LayoutContainer(
                container_id="c_stage",
                band=BandType.BAND_3_STAGE,
                bounds=BoundingBoxPx(
                    x_min_px=140,
                    y_min_px=500,
                    width_px=800,
                    height_px=600
                ),
                nodes=[
                    VisualNode(
                        id="hud_1",
                        node_type=NodeType.GLASS_HUD_CARD,
                        props={"title": "ROUTING GATEWAY", "bodyText": "Top 8 active experts out of 256."},
                        bounds=BoundingBoxPx(
                            x_min_px=140,
                            y_min_px=500,
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


class TestTier2VLMCouncil:

    def test_aesthetic_quality_critic_pass(self, clean_vsg: VideoSceneGraphIR):
        critic = AestheticQualityCritic()
        res = critic.evaluate_ast_and_metrics(clean_vsg.beats[0], clean_vsg)
        assert res.critic_id == "AestheticQualityCritic"
        assert res.composite_score >= 8.0
        assert res.passed_hard_gate is True
        assert len(res.detected_defects) == 0

    def test_aesthetic_critic_flags_low_blur(self, clean_vsg: VideoSceneGraphIR):
        critic = AestheticQualityCritic()
        bad_vsg = clean_vsg.model_copy(deep=True)
        bad_vsg.theme.materials.card_blur_px = 5.0  # violates 20px min glassmorphism
        res = critic.evaluate_ast_and_metrics(bad_vsg.beats[0], bad_vsg)
        assert res.composite_score < 8.0
        assert res.passed_hard_gate is False
        assert any(d.defect_category == "AESTHETIC_MATERIAL" for d in res.detected_defects)
        assert any(p.action == "RESCALE" for p in res.prescribed_patches)

    def test_typographic_critic_flags_density_overflow(self, clean_vsg: VideoSceneGraphIR):
        critic = TypographicHierarchyCritic()
        bad_vsg = clean_vsg.model_copy(deep=True)
        # Exceeds 14-word broadcast cap
        bad_vsg.beats[0].layout_containers[0].nodes[0].props["bodyText"] = (
            "This is a massive wall of text containing far too many spoken tokens and words "
            "that immediately triggers cognitive split-attention overload on mobile displays."
        )
        res = critic.evaluate_ast_and_metrics(bad_vsg.beats[0], bad_vsg)
        assert res.passed_hard_gate is False
        assert any(d.defect_category == "TYPOGRAPHIC_DENSITY_EXCEEDED" for d in res.detected_defects)
        assert any(p.action == "TRUNCATE_TEXT" for p in res.prescribed_patches)

    def test_cognitive_density_critic_flags_7_element_trap(self, clean_vsg: VideoSceneGraphIR):
        critic = CognitiveDensityCritic()
        bad_vsg = clean_vsg.model_copy(deep=True)
        # Add 5 nodes in one beat (violates density ceiling of 3)
        container = bad_vsg.beats[0].layout_containers[0]
        for i in range(4):
            container.nodes.append(VisualNode(
                id=f"extra_{i}",
                node_type=NodeType.METRIC_PILL,
                props={"label": f"Metric {i}", "value": "100"},
                motion_track=MotionTrack(enter=EnterMotion(type=MotionType.FADE_DOWN, start_frame=0, duration_frames=10))
            ))
        res = critic.evaluate_ast_and_metrics(bad_vsg.beats[0], bad_vsg)
        assert res.passed_hard_gate is False
        assert any(d.defect_category == "COGNITIVE_OVERLOAD_7_ELEMENT_TRAP" for d in res.detected_defects)

    def test_temporal_sync_critic_flags_short_buffer(self, clean_vsg: VideoSceneGraphIR):
        critic = TemporalSyncCritic()
        bad_vsg = clean_vsg.model_copy(deep=True)
        bad_vsg.beats[0].time_range.end_sec = 0.5  # duration 0.5s is too short for comprehension
        res = critic.evaluate_ast_and_metrics(bad_vsg.beats[0], bad_vsg)
        assert res.passed_hard_gate is False
        assert any(d.defect_category == "TEMPORAL_BUFFER_VIOLATION" for d in res.detected_defects)

    def test_master_council_hard_gate_pass_and_fail(self, clean_vsg: VideoSceneGraphIR):
        council = Tier2VLMCouncil()

        # 1. Clean AST passes hard gate with >= 8.5/10.0
        report = council.evaluate_beat(clean_vsg.beats[0], clean_vsg)
        assert report.composite_council_score >= 8.5
        assert report.passed_hard_gate is True
        assert len(report.failed_critics) == 0

        # 2. Flawed AST trips the circuit breaker
        flawed_vsg = clean_vsg.model_copy(deep=True)
        flawed_vsg.theme.materials.card_blur_px = 5.0
        flawed_vsg.beats[0].layout_containers[0].nodes[0].props["bodyText"] = "Word " * 25
        flawed_report = council.evaluate_beat(flawed_vsg.beats[0], flawed_vsg)
        assert flawed_report.passed_hard_gate is False
        assert flawed_report.summary_verdict == "REJECTED_TRIPPED_GATE"
        assert len(flawed_report.failed_critics) > 0

    def test_temporal_sync_critic_deadzone_1_1s(self, clean_vsg: VideoSceneGraphIR):
        """Verifies that 1.1s duration (in deadzone 1.0-1.2s) properly flags violation and prescribes patch."""
        critic = TemporalSyncCritic()
        edge_vsg = clean_vsg.model_copy(deep=True)
        edge_vsg.beats[0].time_range.start_sec = 2.0
        edge_vsg.beats[0].time_range.end_sec = 3.1  # duration 1.1s
        res = critic.evaluate_ast_and_metrics(edge_vsg.beats[0], edge_vsg)
        assert res.passed_hard_gate is False
        assert any(d.defect_category == "TEMPORAL_BUFFER_VIOLATION" for d in res.detected_defects)
        assert len(res.prescribed_patches) == 1
        assert res.prescribed_patches[0].patch_value > 3.1  # Future timestamp

    def test_typographic_critic_checks_alternative_text_keys(self, clean_vsg: VideoSceneGraphIR):
        """Verifies that density cap checks description/text keys beyond bodyText."""
        critic = TypographicHierarchyCritic()
        bad_vsg = clean_vsg.model_copy(deep=True)
        bad_vsg.beats[0].layout_containers[0].nodes[0].props["description"] = "Word " * 20
        res = critic.evaluate_ast_and_metrics(bad_vsg.beats[0], bad_vsg)
        assert res.passed_hard_gate is False
        assert any(d.defect_category == "TYPOGRAPHIC_DENSITY_EXCEEDED" for d in res.detected_defects)

    def test_master_council_with_llm_router_cascade_mock(self, clean_vsg: VideoSceneGraphIR, monkeypatch):
        """Verifies that when LLM router cascade returns critique, it is parsed with is_deterministic_fallback=False."""
        mock_response = '''{
          "AestheticQualityCritic": {"composite_score": 9.4, "passed": true, "scores": {"depth": 9.4}, "defects": [], "patches": []},
          "TypographicHierarchyCritic": {"composite_score": 9.2, "passed": true, "scores": {"typo": 9.2}, "defects": [], "patches": []},
          "CognitiveDensityCritic": {"composite_score": 9.5, "passed": true, "scores": {"focus": 9.5}, "defects": [], "patches": []},
          "TemporalSyncCritic": {"composite_score": 9.1, "passed": true, "scores": {"sync": 9.1}, "defects": [], "patches": []}
        }'''
        monkeypatch.setattr(
            "pipeline.qa.tier2_vlm_council.generate_text_with_cascade",
            lambda prompt, system_instruction=None: mock_response
        )
        council = Tier2VLMCouncil()
        report = council.evaluate_beat(clean_vsg.beats[0], clean_vsg, use_llm=True)
        assert report.passed_hard_gate is True
        assert report.composite_council_score >= 9.0
        assert report.is_deterministic_fallback is False
        assert "AestheticQualityCritic" in report.critic_evaluations

