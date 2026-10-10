"""Comprehensive Test Suite for Phase 4: Critic Council & Quality Gatekeeping (WBS 1.5).

Verifies:
1. Pydantic V2 schemas (CriticType, DefectSeverity, HardGateType, RepairRecommendation,
   CriticFailureObject, CriticAuditResult, CouncilEvaluationReport, RepairActionDirective).
2. Deterministic Computer Vision temporal & artifact analyzer (CVTemporalAnalyzer):
   - Pixel differentials, exact SSIM, and optical flow displacement vector variance.
   - Micro-flickering detection on synthetic alternating luminance sequences.
   - Transient 1-4 frame strobing/morphing detection and bounding box localization (RSK-002).
   - Unphysical motion acceleration spikes.
3. Specialized Critic implementations:
   - VisualCritic: Anatomical integrity (extra limbs, distorted hands) and surface artifacts.
   - TemporalCritic: Hybrid CV temporal analyzer + high-level coherence.
   - ContinuityCritic: World Model State Graph cross-referencing (wardrobe damage,
     prop possession & hand attachment, persistent injuries, reciprocal eyelines, identity).
   - PerformanceCritic: Lip-sync offset (ms), phonetic mouth movement, and vocal emotion.
   - PhysicsCritic: Gravity violations, unnatural accelerations, and solid-body clipping.
4. Master CriticCouncil coordinator:
   - Execution across all specialized critics.
   - Binary Hard Gate enforcement: FATAL/SEVERE defect trips Hard Gate PASS/FAIL.
   - Soft Aesthetic Scores (Cinematography, Atmosphere, Performance, Pacing) evaluated
     ONLY when all Hard Gates pass.
   - Candidate with high aesthetic potential is strictly REJECTED when anatomy fails.
   - Actionable Prioritized Repair Plan synthesis.
"""

from __future__ import annotations

import math
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from aether.council import (
    AudioCritic,
    CouncilEvaluationReport,
    CouncilStatus,
    CriticAuditResult,
    CriticCouncil,
    CriticFailureObject,
    CriticType,
    CVTemporalAnalyzer,
    DefectSeverity,
    HardGateType,
    RepairActionDirective,
    RepairRecommendation,
    ContinuityCritic,
    OllamaVisionAuditor,
    PerformanceCritic,
    PhysicsCritic,
    TemporalCritic,
    VisualCritic,
)
from aether.compiler.schemas import AudioRequirement, ShotRequirement
from aether.state.graph import AetherWorldModel
from aether.state.schemas import (
    ActionType,
    CharacterState,
    EnvironmentState,
    HandAttachment,
    PropState,
    SceneAction,
    SceneState,
    WardrobeItemState,
)


# ===========================================================================
# 1. Council Schemas Tests
# ===========================================================================

class TestCouncilSchemas:
    """Tests Pydantic V2 schemas for Critic Council."""

    def test_critic_type_enum(self) -> None:
        assert CriticType.VISUAL == "VISUAL"
        assert CriticType.TEMPORAL == "TEMPORAL"
        assert CriticType.CONTINUITY == "CONTINUITY"
        assert CriticType.PERFORMANCE == "PERFORMANCE"
        assert CriticType.PHYSICS == "PHYSICS"
        assert CriticType.AUDIO == "AUDIO"

        # Case-insensitivity and string coercion
        assert CriticType.from_str("visual") == CriticType.VISUAL
        assert CriticType.from_str("CriticType.TEMPORAL") == CriticType.TEMPORAL

    def test_defect_severity_enum(self) -> None:
        assert DefectSeverity.FATAL == "FATAL"
        assert DefectSeverity.SEVERE == "SEVERE"
        assert DefectSeverity.MODERATE == "MODERATE"
        assert DefectSeverity.MINOR == "MINOR"
        assert DefectSeverity.NEGLIGIBLE == "NEGLIGIBLE"

        # Hard gate breaker checks
        assert DefectSeverity.FATAL.is_hard_gate_breaker is True
        assert DefectSeverity.SEVERE.is_hard_gate_breaker is True
        assert DefectSeverity.MODERATE.is_hard_gate_breaker is False
        assert DefectSeverity.MINOR.is_hard_gate_breaker is False

        # Priority ranks
        assert DefectSeverity.FATAL.rank < DefectSeverity.SEVERE.rank
        assert DefectSeverity.SEVERE.rank < DefectSeverity.MODERATE.rank

    def test_hard_gate_type_enum(self) -> None:
        gates = {
            HardGateType.ANATOMICAL_INTEGRITY,
            HardGateType.CHARACTER_IDENTITY,
            HardGateType.PROP_CONTINUITY,
            HardGateType.LIP_SYNC_ALIGNMENT,
            HardGateType.PHYSICAL_TRAJECTORY,
        }
        assert len(gates) == 5
        assert HardGateType.from_str("anatomical_integrity") == HardGateType.ANATOMICAL_INTEGRITY

    def test_repair_recommendation_enum(self) -> None:
        recommendations = {
            RepairRecommendation.REGIONAL_INPAINTING,
            RepairRecommendation.AUDIO_REMASTER,
            RepairRecommendation.SPATIAL_PREVIS_RERUN,
            RepairRecommendation.FULL_REGEN,
            RepairRecommendation.NO_REPAIR_NEEDED,
        }
        assert len(recommendations) == 5
        assert RepairRecommendation.from_str("regional_inpainting") == RepairRecommendation.REGIONAL_INPAINTING

    def test_critic_failure_object_creation_and_normalization(self) -> None:
        failure = CriticFailureObject(
            failure_type="extra_limbs",
            severity=DefectSeverity.FATAL,
            frame_bounds=(10, 20),
            bounding_box=(0.1, 0.2, 0.5, 0.6),
            target_entity_id="char_maya",
            observed_state="Three arms rendered on character torso",
            expected_state="Two arms attached to shoulder joints",
            confidence=0.98,
            recommended_repair=RepairRecommendation.REGIONAL_INPAINTING,
            critic_type=CriticType.VISUAL,
            hard_gate=HardGateType.ANATOMICAL_INTEGRITY,
        )

        assert failure.start_frame == 10
        assert failure.end_frame == 20
        assert failure.bounding_box == (0.1, 0.2, 0.5, 0.6)
        assert failure.is_hard_gate_breaker is True
        assert failure.hard_gate == HardGateType.ANATOMICAL_INTEGRITY

    def test_critic_failure_object_aliases_and_clamping(self) -> None:
        # Pass aliases: bbox, start_frame, end_frame, defect_class, strategy
        raw_dict = {
            "defect_class": "fused_fingers",
            "severity": "severe",
            "start_frame": 15,
            "end_frame": 18,
            "bbox": [-0.1, 0.2, 1.2, 0.8],  # Coordinates outside [0, 1] clamped
            "character_id": "maya",
            "strategy": "regional_inpainting",
        }
        f = CriticFailureObject(**raw_dict)
        assert f.failure_type == "fused_fingers"
        assert f.severity == DefectSeverity.SEVERE
        assert f.frame_bounds == (15, 18)
        assert f.bounding_box == (0.0, 0.2, 1.0, 0.8)
        assert f.target_entity_id == "maya"
        assert f.recommended_repair == RepairRecommendation.REGIONAL_INPAINTING

    def test_critic_audit_result_helpers(self) -> None:
        failures = [
            CriticFailureObject(failure_type="f1", severity=DefectSeverity.FATAL),
            CriticFailureObject(failure_type="f2", severity=DefectSeverity.SEVERE),
            CriticFailureObject(failure_type="f3", severity=DefectSeverity.MODERATE),
        ]
        result = CriticAuditResult(
            critic_type=CriticType.VISUAL,
            passed=False,
            score=3.5,
            failures=failures,
            hard_gate_verdicts={HardGateType.ANATOMICAL_INTEGRITY: False},
        )
        assert result.has_fatal_or_severe is True
        assert result.failure_count == 3
        assert result.fatal_count == 1
        assert result.severe_count == 1

    def test_council_evaluation_report_properties(self) -> None:
        report = CouncilEvaluationReport(
            hard_gate_verdicts={
                HardGateType.ANATOMICAL_INTEGRITY: True,
                HardGateType.CHARACTER_IDENTITY: False,
            },
            all_hard_gates_passed=False,
            soft_scores={"Cinematography": 0.0},
            overall_score=0.0,
            status=CouncilStatus.REJECTED_FOR_REPAIR,
        )
        assert report.is_accepted is False
        assert report.failed_hard_gates == [HardGateType.CHARACTER_IDENTITY]

    def test_critic_failure_object_coordinate_properties_and_repair_strategy(self) -> None:
        """Verifies bbox, coordinate accessors (x1, y1, x2, y2), and repair strategy aliases."""
        f = CriticFailureObject(
            failure_type="test_glitch",
            bbox=(0.1, 0.2, 0.8, 0.9),
            start_frame=3,
            end_frame=7,
            recommended_repair_strategy=RepairRecommendation.REGIONAL_INPAINTING,
        )
        assert f.bbox == (0.1, 0.2, 0.8, 0.9)
        assert f.bounding_box == (0.1, 0.2, 0.8, 0.9)
        assert f.x1 == 0.1
        assert f.y1 == 0.2
        assert f.x2 == 0.8
        assert f.y2 == 0.9
        assert f.start_frame == 3
        assert f.end_frame == 7
        assert f.frame_bounds == (3, 7)
        assert f.recommended_repair_strategy == RepairRecommendation.REGIONAL_INPAINTING
        assert f.recommended_repair == RepairRecommendation.REGIONAL_INPAINTING

        # Dict-based model_validate with coordinate aliases and strategy alias
        f2 = CriticFailureObject.model_validate({
            "type": "custom_defect",
            "x1": 0.05,
            "y1": 0.15,
            "x2": 0.85,
            "y2": 0.95,
            "start_frame": 1,
            "end_frame": 5,
            "repair_strategy": "SPATIAL_PREVIS_RERUN",
        })
        assert f2.bbox == (0.05, 0.15, 0.85, 0.95)
        assert f2.recommended_repair == RepairRecommendation.SPATIAL_PREVIS_RERUN


# ===========================================================================
# 2. Computer Vision Temporal Analyzer Tests (RSK-002)
# ===========================================================================

class TestCVTemporalAnalyzer:
    """Verifies deterministic OpenCV/NumPy temporal & artifact analysis."""

    @pytest.fixture
    def analyzer(self) -> CVTemporalAnalyzer:
        return CVTemporalAnalyzer(
            flicker_amplitude_threshold=0.04,
            ssim_drop_threshold=0.15,
            ssim_absolute_min=0.75,
            motion_spike_multiplier=3.0,
            motion_variance_threshold=10.0,
        )

    def test_frame_normalization(self, analyzer: CVTemporalAnalyzer) -> None:
        # uint8 RGB frames
        raw_uint8 = np.random.randint(0, 256, (5, 32, 32, 3), dtype=np.uint8)
        gf, gu = analyzer.normalize_frames(raw_uint8)
        assert gf.shape == (5, 32, 32)
        assert gu.shape == (5, 32, 32)
        assert gf.dtype == np.float32
        assert 0.0 <= np.min(gf) and np.max(gf) <= 1.0
        assert gu.dtype == np.uint8

        # Empty frames edge case
        empty_gf, empty_gu = analyzer.normalize_frames([])
        assert empty_gf.shape == (0, 0, 0)
        assert empty_gu.shape == (0, 0, 0)

    def test_frame_normalization_dtype_and_scale_boundaries(self, analyzer: CVTemporalAnalyzer) -> None:
        """Verifies normalization handles float overshoot (>1.0) and dark uint8 frames without scale corruption."""
        # 1. Float frames in [0.0, 1.0] with small overshoot (1.005)
        float_overshoot = np.full((3, 16, 16), 1.005, dtype=np.float32)
        gf, gu = analyzer.normalize_frames(float_overshoot)
        assert gf.dtype == np.float32
        assert gu.dtype == np.uint8
        assert np.all(gf <= 1.0) and np.all(gf >= 0.99)
        assert np.all(gu == 255)

        # 2. Dark uint8 frames where max_val <= 1 (should be treated as uint8, scaled by 1/255.0)
        dark_uint8 = np.ones((3, 16, 16), dtype=np.uint8)
        gf_dark, gu_dark = analyzer.normalize_frames(dark_uint8)
        assert np.isclose(gf_dark[0, 0, 0], 1.0 / 255.0, atol=1e-4)
        assert gu_dark[0, 0, 0] == 1

        # 3. Standard uint8 frames
        std_uint8 = np.full((3, 16, 16), 128, dtype=np.uint8)
        gf_std, gu_std = analyzer.normalize_frames(std_uint8)
        assert np.isclose(gf_std[0, 0, 0], 128.0 / 255.0, atol=1e-3)
        assert gu_std[0, 0, 0] == 128

    def test_clean_sequence_zero_defects(self, analyzer: CVTemporalAnalyzer) -> None:
        clean = analyzer.generate_clean_sequence(num_frames=16, height=64, width=64)
        failures = analyzer.analyze_frames(clean)
        # Clean smooth video should trigger zero temporal defects
        assert len(failures) == 0

    def test_micro_flicker_detection(self, analyzer: CVTemporalAnalyzer) -> None:
        clean = analyzer.generate_clean_sequence(num_frames=16, height=64, width=64)
        flicker_video = analyzer.inject_flicker(clean, start_frame=4, end_frame=7, amplitude=0.30)

        failures = analyzer.analyze_frames(flicker_video)
        flicker_failures = [f for f in failures if f.failure_type == "micro_flicker"]

        assert len(flicker_failures) >= 1
        f = flicker_failures[0]
        assert f.critic_type == CriticType.TEMPORAL
        assert f.severity in (DefectSeverity.SEVERE, DefectSeverity.MODERATE)
        assert f.frame_bounds[0] <= 4
        assert f.frame_bounds[1] >= 6
        assert f.confidence >= 0.85

    def test_localized_micro_flicker_detection_on_subgrid(self, analyzer: CVTemporalAnalyzer) -> None:
        """Verifies spatial subgrid block detection catches localized strobing that global mean luminance misses."""
        clean = analyzer.generate_clean_sequence(num_frames=12, height=64, width=64)
        flickered = clean.copy()
        # Corrupt only a 16x16 corner block (top-left) with alternating luminance
        for idx in range(3, 7):
            sign = 1.0 if idx % 2 == 0 else -1.0
            flickered[idx, 0:16, 0:16] = np.clip(flickered[idx, 0:16, 0:16] + sign * 0.25, 0.0, 1.0)

        gf, _ = analyzer.normalize_frames(flickered)
        failures = analyzer.detect_micro_flicker(gf)
        assert len(failures) >= 1
        f = failures[0]
        assert f.failure_type == "micro_flicker"
        assert f.frame_bounds[0] <= 4 <= f.frame_bounds[1]
        # Bounding box should localize to upper-left quadrant
        assert f.bbox[2] <= 0.6
        assert f.bbox[3] <= 0.6

    def test_sudden_1_to_4_frame_morphing_detection(self, analyzer: CVTemporalAnalyzer) -> None:
        clean = analyzer.generate_clean_sequence(num_frames=16, height=64, width=64)
        # Inject localized 2-frame morphing artifact (frames 6 to 7)
        morph_bbox = (0.2, 0.2, 0.5, 0.5)
        morphed_video = analyzer.inject_morph(clean, start_frame=6, end_frame=7, bbox=morph_bbox)

        failures = analyzer.analyze_frames(morphed_video)
        morph_failures = [f for f in failures if f.failure_type == "morphing_artifact"]

        assert len(morph_failures) >= 1
        f = morph_failures[0]
        assert f.critic_type == CriticType.TEMPORAL
        assert f.severity in (DefectSeverity.FATAL, DefectSeverity.SEVERE)
        assert f.frame_bounds[0] <= 6
        assert f.frame_bounds[1] >= 7
        # Verify spatial bounding box localization captured corrupted patch
        bx1, by1, bx2, by2 = f.bounding_box
        assert bx1 <= 0.35 and by1 <= 0.35
        assert bx2 >= 0.45 and by2 >= 0.45
        assert f.recommended_repair == RepairRecommendation.REGIONAL_INPAINTING

    def test_erratic_motion_displacement_spike_detection(self, analyzer: CVTemporalAnalyzer) -> None:
        clean = analyzer.generate_clean_sequence(num_frames=16, height=64, width=64)
        spike_video = analyzer.inject_motion_spike(clean, spike_frame=8, displacement=(20, 20))

        failures = analyzer.analyze_frames(spike_video)
        motion_failures = [f for f in failures if f.failure_type == "erratic_motion_spike"]

        assert len(motion_failures) >= 1
        f = motion_failures[0]
        assert f.critic_type == CriticType.TEMPORAL
        assert f.frame_bounds[0] <= 8
        assert f.recommended_repair in (RepairRecommendation.REGIONAL_INPAINTING, RepairRecommendation.SPATIAL_PREVIS_RERUN)

    def test_ssim_exact_computation(self, analyzer: CVTemporalAnalyzer) -> None:
        im1 = np.tile(np.linspace(0.1, 0.9, 32, dtype=np.float32), (32, 1))
        im2 = im1.copy()
        seq = np.stack([im1, im2], axis=0)

        ssim_val = analyzer.compute_ssim_sequence(seq)
        assert len(ssim_val) == 1
        assert abs(float(ssim_val[0]) - 1.0) < 1e-4

        # Inverted image should have low/negative SSIM
        im_inv = 1.0 - im1
        seq_diff = np.stack([im1, im_inv], axis=0)
        ssim_diff = analyzer.compute_ssim_sequence(seq_diff)
        assert float(ssim_diff[0]) < 0.2


# ===========================================================================
# 3. Specialized Domain Critics Tests
# ===========================================================================

class TestVisualCritic:
    """Verifies anatomical integrity and surface artifact evaluation."""

    def test_clean_visual_candidate_passes(self) -> None:
        critic = VisualCritic()
        result = critic.audit({"visual_defects": []})
        assert result.passed is True
        assert result.score == 10.0
        assert result.hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] is True
        assert len(result.failures) == 0

    def test_extra_limbs_and_distorted_hands_fail_hard_gate(self) -> None:
        critic = VisualCritic()
        # Candidate with anatomical hand deformity
        cdata = {
            "visual_defects": [
                {
                    "defect_class": "fused_fingers",
                    "severity": "FATAL",
                    "start_frame": 0,
                    "end_frame": 24,
                    "bbox": [0.3, 0.4, 0.6, 0.7],
                    "character_id": "maya",
                    "observed_state": "6 fused digits on right hand",
                }
            ]
        }
        result = critic.audit(cdata)
        assert result.passed is False
        assert result.hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] is False
        assert result.score < 6.0
        assert len(result.failures) == 1
        assert result.failures[0].recommended_repair == RepairRecommendation.REGIONAL_INPAINTING

    def test_surface_minor_artifact_penalizes_score_without_breaking_hard_gate(self) -> None:
        critic = VisualCritic()
        cdata = {
            "visual_defects": [
                {
                    "defect_class": "texture_tearing",
                    "severity": "MINOR",
                    "start_frame": 12,
                    "end_frame": 14,
                    "bbox": [0.1, 0.1, 0.2, 0.2],
                    "observed_state": "Slight background texture tearing",
                }
            ]
        }
        result = critic.audit(cdata)
        assert result.passed is True
        assert result.score == 9.5
        assert result.hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] is True

    def test_extra_arm_and_missing_limb_fail_anatomical_hard_gate(self) -> None:
        """Verifies extra arm, missing limb, extra head, etc. reliably trigger ANATOMICAL_INTEGRITY hard gate failure."""
        critic = VisualCritic()

        # Telemetry flags
        res1 = critic.audit({"extra_arm": True})
        assert res1.passed is False
        assert res1.hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] is False

        res2 = critic.audit({"missing_limb": True})
        assert res2.passed is False
        assert res2.hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] is False

        # Raw defect dictionaries with expanded anatomical taxonomy
        res3 = critic.audit({
            "visual_defects": [
                {"defect_class": "extra_head", "severity": "SEVERE"},
            ]
        })
        assert res3.passed is False
        assert res3.hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] is False

        res4 = critic.audit({
            "visual_defects": [
                {"defect_class": "missing_arm_geometry", "severity": "FATAL"},
            ]
        })
        assert res4.passed is False
        assert res4.hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] is False


class TestTemporalCritic:
    """Verifies temporal coherence and CV analyzer integration."""

    def test_temporal_critic_with_clean_frames(self) -> None:
        critic = TemporalCritic()
        analyzer = CVTemporalAnalyzer()
        clean_frames = analyzer.generate_clean_sequence(12)
        result = critic.audit({"frames": clean_frames})
        assert result.passed is True
        assert result.score == 10.0
        assert len(result.failures) == 0

    def test_temporal_critic_with_telemetry_flags(self) -> None:
        critic = TemporalCritic()
        cdata = {
            "micro_flicker_detected": True,
            "flicker_frame_bounds": (3, 6),
        }
        result = critic.audit(cdata)
        assert result.passed is False
        assert result.score <= 7.0
        assert any(f.failure_type == "micro_flicker" for f in result.failures)


class TestContinuityCritic:
    """Verifies state graph cross-referencing for wardrobe, props, injuries, and eyelines."""

    @pytest.fixture
    def world_model(self) -> AetherWorldModel:
        scene = SceneState(
            scene_id="SC_014",
            location="cleanroom",
            timestamp="23:42",
            character_roster={
                "maya": CharacterState(
                    character_id="maya",
                    name="Maya Lin",
                    position=[0.0, 0.0, 2.0],
                    wardrobe={"jacket": WardrobeItemState(id="leather_004", state="left_sleeve_torn", damage_level=0.75)},
                    injuries=["blood_cheek_right"],
                    held_props={"right": "spectrometer_device_01"},
                ),
                "kai": CharacterState(
                    character_id="kai",
                    name="Kai Vance",
                    position=[2.0, 0.0, 2.0],
                    wardrobe={"suit": WardrobeItemState(id="hazmat_01", state="pristine")},
                ),
            },
            prop_roster={
                "spectrometer_device_01": PropState(
                    prop_id="spectrometer_device_01",
                    name="Spectrometer",
                    owner_id="maya",
                    hand_attachment=HandAttachment.RIGHT,
                    physical_state="pristine",
                )
            },
        )
        return AetherWorldModel(initial_state=scene)

    def test_clean_continuity_candidate_passes(self, world_model: AetherWorldModel) -> None:
        critic = ContinuityCritic()
        cdata = {
            "characters": {
                "maya": {
                    "wardrobe": {"jacket": {"state": "left_sleeve_torn", "damage_level": 0.75}},
                    "injuries": ["blood_cheek_right"],
                },
                "kai": {"wardrobe": {"suit": {"state": "pristine"}}},
            },
            "props": {
                "spectrometer_device_01": {"owner_id": "maya", "hand_attachment": "right"}
            },
        }
        result = critic.audit(cdata, scene_state=world_model.active_state)
        assert result.passed is True
        assert result.score == 10.0
        assert result.hard_gate_verdicts[HardGateType.PROP_CONTINUITY] is True
        assert result.hard_gate_verdicts[HardGateType.CHARACTER_IDENTITY] is True
        assert len(result.failures) == 0

    def test_wardrobe_regression_detected(self, world_model: AetherWorldModel) -> None:
        critic = ContinuityCritic()
        # Candidate shows Maya's torn jacket miraculously pristine
        cdata = {
            "characters": {
                "maya": {
                    "wardrobe": {"jacket": {"state": "pristine", "damage_level": 0.0}},
                    "injuries": ["blood_cheek_right"],
                }
            },
            "props": {
                "spectrometer_device_01": {"owner_id": "maya", "hand_attachment": "right"}
            },
        }
        result = critic.audit(cdata, scene_state=world_model.active_state)
        assert result.passed is False
        assert any(f.failure_type == "wardrobe_regression" for f in result.failures)
        wf = next(f for f in result.failures if f.failure_type == "wardrobe_regression")
        assert wf.target_entity_id == "maya"
        assert wf.recommended_repair == RepairRecommendation.REGIONAL_INPAINTING

    def test_prop_handoff_and_possession_mismatch_fails_hard_gate(self, world_model: AetherWorldModel) -> None:
        critic = ContinuityCritic()
        # Spectrometer mistakenly rendered held by Kai instead of Maya
        cdata = {
            "characters": {
                "maya": {
                    "wardrobe": {"jacket": {"state": "left_sleeve_torn", "damage_level": 0.75}},
                    "injuries": ["blood_cheek_right"],
                }
            },
            "props": {
                "spectrometer_device_01": {"owner_id": "kai", "hand_attachment": "left"}
            },
        }
        result = critic.audit(cdata, scene_state=world_model.active_state)
        assert result.passed is False
        assert result.hard_gate_verdicts[HardGateType.PROP_CONTINUITY] is False
        prop_failure = next(f for f in result.failures if f.failure_type == "prop_possession_mismatch")
        assert prop_failure.target_entity_id == "spectrometer_device_01"
        assert prop_failure.severity == DefectSeverity.FATAL

    def test_prop_hand_attachment_slot_mismatch(self, world_model: AetherWorldModel) -> None:
        critic = ContinuityCritic()
        # Held by Maya, but on LEFT hand instead of canonical RIGHT hand
        cdata = {
            "characters": {
                "maya": {
                    "wardrobe": {"jacket": {"state": "left_sleeve_torn", "damage_level": 0.75}},
                    "injuries": ["blood_cheek_right"],
                }
            },
            "props": {
                "spectrometer_device_01": {"owner_id": "maya", "hand_attachment": "left"}
            },
        }
        result = critic.audit(cdata, scene_state=world_model.active_state)
        assert result.passed is False
        assert result.hard_gate_verdicts[HardGateType.PROP_CONTINUITY] is False
        hf = next(f for f in result.failures if f.failure_type == "prop_hand_attachment_mismatch")
        assert hf.severity == DefectSeverity.SEVERE

    def test_injury_regression_detected(self, world_model: AetherWorldModel) -> None:
        critic = ContinuityCritic()
        # Maya cheek wound disappeared
        cdata = {
            "characters": {
                "maya": {
                    "wardrobe": {"jacket": {"state": "left_sleeve_torn", "damage_level": 0.75}},
                    "injuries": [],  # Wound missing!
                }
            },
            "props": {
                "spectrometer_device_01": {"owner_id": "maya", "hand_attachment": "right"}
            },
        }
        result = critic.audit(cdata, scene_state=world_model.active_state)
        assert result.passed is False
        assert any(f.failure_type == "injury_regression" for f in result.failures)

    def test_character_identity_drift_fails_hard_gate(self, world_model: AetherWorldModel) -> None:
        critic = ContinuityCritic()
        cdata = {
            "character_identity_mismatch": True,
            "identity_drift_char_id": "maya",
        }
        result = critic.audit(cdata, scene_state=world_model.active_state)
        assert result.passed is False
        assert result.hard_gate_verdicts[HardGateType.CHARACTER_IDENTITY] is False
        idf = next(f for f in result.failures if f.failure_type == "character_identity_drift")
        assert idf.severity == DefectSeverity.FATAL
        assert idf.recommended_repair == RepairRecommendation.FULL_REGEN

    def test_wardrobe_regression_trips_character_identity_hard_gate(
        self,
        world_model: AetherWorldModel,
    ) -> None:
        """Verifies wardrobe damage regression trips the CHARACTER_IDENTITY hard gate."""
        critic = ContinuityCritic()
        cdata = {
            "characters": {
                "maya": {
                    "wardrobe": {"jacket": {"state": "pristine", "damage_level": 0.0}}
                }
            }
        }
        res = critic.audit(cdata, scene_state=world_model.active_state)
        assert res.passed is False
        assert res.hard_gate_verdicts[HardGateType.CHARACTER_IDENTITY] is False
        assert any(f.failure_type == "wardrobe_regression" for f in res.failures)
        f = next(f for f in res.failures if f.failure_type == "wardrobe_regression")
        assert f.hard_gate == HardGateType.CHARACTER_IDENTITY
        assert f.severity == DefectSeverity.SEVERE

    def test_missing_held_prop_without_props_present_trips_prop_continuity(
        self,
        world_model: AetherWorldModel,
    ) -> None:
        """Verifies missing held prop trips PROP_CONTINUITY when props dict is provided without props_present."""
        critic = ContinuityCritic()
        cdata = {
            "props": {
                "random_prop_99": {"owner_id": "kai"}
            }
        }
        res = critic.audit(cdata, scene_state=world_model.active_state)
        assert res.passed is False
        assert res.hard_gate_verdicts[HardGateType.PROP_CONTINUITY] is False
        assert any(f.failure_type == "prop_missing" for f in res.failures)
        f = next(f for f in res.failures if f.failure_type == "prop_missing")
        assert f.target_entity_id == "spectrometer_device_01"
        assert f.hard_gate == HardGateType.PROP_CONTINUITY


class TestPerformanceCritic:
    """Verifies lip-sync timing, viseme mouth movements, and vocal performance."""

    def test_clean_lip_sync_passes(self) -> None:
        critic = PerformanceCritic(max_lip_sync_offset_ms=45.0)
        result = critic.audit({"lip_sync_offset_ms": 12.0})
        assert result.passed is True
        assert result.score == 10.0
        assert result.hard_gate_verdicts[HardGateType.LIP_SYNC_ALIGNMENT] is True

    def test_lip_sync_offset_breach_fails_hard_gate(self) -> None:
        critic = PerformanceCritic(max_lip_sync_offset_ms=45.0)
        # 85ms desync breaches hard gate
        result = critic.audit({"lip_sync_offset_ms": 85.0})
        assert result.passed is False
        assert result.hard_gate_verdicts[HardGateType.LIP_SYNC_ALIGNMENT] is False
        f = next(f for f in result.failures if f.failure_type == "lip_sync_offset_breach")
        assert f.severity == DefectSeverity.FATAL
        assert f.recommended_repair == RepairRecommendation.AUDIO_REMASTER

    def test_phonetic_mouth_mismatch(self) -> None:
        critic = PerformanceCritic()
        result = critic.audit({"phonetic_mismatch": True, "speaker_id": "maya"})
        assert result.passed is False
        assert result.hard_gate_verdicts[HardGateType.LIP_SYNC_ALIGNMENT] is False
        f = next(f for f in result.failures if f.failure_type == "phonetic_mouth_mismatch")
        assert f.recommended_repair == RepairRecommendation.REGIONAL_INPAINTING


class TestPhysicsCritic:
    """Verifies gravity consistency, solid body collisions, and physical trajectories."""

    def test_clean_physics_passes(self) -> None:
        critic = PhysicsCritic()
        result = critic.audit({})
        assert result.passed is True
        assert result.hard_gate_verdicts[HardGateType.PHYSICAL_TRAJECTORY] is True

    def test_gravity_violation_fails_hard_gate(self) -> None:
        critic = PhysicsCritic()
        result = critic.audit({"gravity_violation": True, "floating_prop_id": "wrench_01"})
        assert result.passed is False
        assert result.hard_gate_verdicts[HardGateType.PHYSICAL_TRAJECTORY] is False
        f = next(f for f in result.failures if f.failure_type == "gravity_violation")
        assert f.recommended_repair == RepairRecommendation.SPATIAL_PREVIS_RERUN

    def test_solid_body_clipping_fails_hard_gate(self) -> None:
        critic = PhysicsCritic()
        result = critic.audit({"solid_body_clipping": True, "clipping_entity_id": "actor_maya"})
        assert result.passed is False
        assert result.hard_gate_verdicts[HardGateType.PHYSICAL_TRAJECTORY] is False
        f = next(f for f in result.failures if f.failure_type == "solid_body_clipping")
        assert f.recommended_repair == RepairRecommendation.SPATIAL_PREVIS_RERUN


class TestAudioCritic:
    """Verifies AudioCritic dialogue acoustics, clipping, noise floor, and repair recommendations."""

    def test_clean_audio_passes(self) -> None:
        critic = AudioCritic()
        res = critic.audit({})
        assert res.passed is True
        assert res.score == 10.0
        assert len(res.failures) == 0

    def test_audio_critic_audits_clipping_and_defect_lists(self) -> None:
        """Verifies clipping detection, audio defect lists parsing, and audio remaster repair recommendations."""
        critic = AudioCritic()
        cdata = {
            "audio_clipping": True,
            "peak_dbfs": 0.5,
            "audio_defects": [
                {
                    "defect_class": "dialogue_vocal_distortion",
                    "severity": "SEVERE",
                    "start_frame": 10,
                    "end_frame": 24,
                }
            ],
        }
        res = critic.audit(cdata)
        assert res.passed is False
        assert res.score < 7.0
        assert len(res.failures) >= 2
        f_clip = next(f for f in res.failures if f.failure_type == "audio_digital_clipping")
        assert f_clip.severity == DefectSeverity.SEVERE
        assert f_clip.recommended_repair == RepairRecommendation.AUDIO_REMASTER
        f_dist = next(f for f in res.failures if "vocal_distortion" in f.failure_type)
        assert f_dist.severity == DefectSeverity.SEVERE
        assert f_dist.recommended_repair == RepairRecommendation.AUDIO_REMASTER

    def test_audio_noise_floor_breach(self) -> None:
        """Verifies elevated background hiss/hum flags noise floor breach."""
        critic = AudioCritic()
        res = critic.audit({"noise_floor_breach": True})
        assert len(res.failures) == 1
        assert res.failures[0].failure_type == "noise_floor_breach"
        assert res.failures[0].severity == DefectSeverity.MODERATE
        assert res.failures[0].recommended_repair == RepairRecommendation.AUDIO_REMASTER


# ===========================================================================
# 4. Master Critic Council Orchestration & Quality Gatekeeping Tests
# ===========================================================================

class TestCriticCouncil:
    """Verifies end-to-end Master Critic Council coordination, hard gating, and repair synthesis."""

    @pytest.fixture
    def council(self) -> CriticCouncil:
        return CriticCouncil(soft_score_threshold=7.0)

    @pytest.fixture
    def shot_req(self) -> ShotRequirement:
        return ShotRequirement(
            shot_id="SHOT_014_A",
            target_duration=4.5,
            character_ids_involved=["maya", "kai"],
            audio=AudioRequirement(dialogue=True, dialogue_text="Get behind the blast door!"),
        )

    def test_fully_clean_candidate_accepted(
        self,
        council: CriticCouncil,
        shot_req: ShotRequirement,
    ) -> None:
        cdata = {
            "cinematography_score": 9.2,
            "atmosphere_score": 9.0,
            "performance_score": 8.8,
            "pacing_score": 8.5,
            "lip_sync_offset_ms": 10.0,
        }
        report = council.evaluate(cdata, shot_requirement=shot_req)

        assert report.status == CouncilStatus.ACCEPTED
        assert report.is_accepted is True
        assert report.all_hard_gates_passed is True
        for gate, passed in report.hard_gate_verdicts.items():
            assert passed is True, f"Gate {gate} unexpectedly failed"

        # Soft scores should be fully populated
        assert report.soft_scores["Cinematography"] == 9.2
        assert report.soft_scores["Atmosphere"] == 9.0
        assert report.overall_score >= 8.5
        assert len(report.failures) == 0
        assert len(report.prioritized_repair_plan) == 0

    def test_hard_gate_rejection_overrides_high_aesthetic_scores(
        self,
        council: CriticCouncil,
        shot_req: ShotRequirement,
    ) -> None:
        """Core requirement: High aesthetic scores MUST be rejected if anatomical deformity exists."""
        cdata = {
            # Pristine aesthetic metrics
            "cinematography_score": 9.8,
            "atmosphere_score": 9.5,
            "performance_score": 9.2,
            "pacing_score": 9.4,
            # BUT: Severe anatomical defect (e.g. 6 fingers / fused hand)
            "visual_defects": [
                {
                    "defect_class": "fused_fingers",
                    "severity": "FATAL",
                    "start_frame": 0,
                    "end_frame": 24,
                    "bbox": [0.4, 0.4, 0.6, 0.6],
                    "character_id": "maya",
                }
            ],
        }
        report = council.evaluate(cdata, shot_requirement=shot_req)

        # Must be strictly rejected!
        assert report.status == CouncilStatus.REJECTED_FOR_REPAIR
        assert report.is_accepted is False
        assert report.all_hard_gates_passed is False
        assert report.hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] is False

        # Soft aesthetic scores must be gated / zeroed out
        assert report.overall_score == 0.0
        assert report.soft_scores["Cinematography"] == 0.0
        assert report.soft_scores["Atmosphere"] == 0.0

        # Actionable repair plan generated
        assert len(report.prioritized_repair_plan) >= 1
        plan = report.prioritized_repair_plan[0]
        assert plan.repair_type == RepairRecommendation.REGIONAL_INPAINTING
        assert plan.priority == 1
        assert plan.defect_type == "fused_fingers"

    def test_lip_sync_failure_synthesizes_audio_remaster(
        self,
        council: CriticCouncil,
        shot_req: ShotRequirement,
    ) -> None:
        cdata = {
            "lip_sync_offset_ms": 75.0,  # 75ms desync
        }
        report = council.evaluate(cdata, shot_requirement=shot_req)

        assert report.status == CouncilStatus.REJECTED_FOR_REPAIR
        assert report.hard_gate_verdicts[HardGateType.LIP_SYNC_ALIGNMENT] is False

        assert len(report.prioritized_repair_plan) >= 1
        plan = report.prioritized_repair_plan[0]
        assert plan.repair_type == RepairRecommendation.AUDIO_REMASTER
        assert "audio-only remaster" in plan.action_description.lower()

    def test_cascading_multiple_defects_prioritization(
        self,
        council: CriticCouncil,
        shot_req: ShotRequirement,
    ) -> None:
        """Tests that multiple defects from different critics are prioritized correctly."""
        cdata = {
            "visual_defects": [
                {"defect_class": "extra_limbs", "severity": "FATAL", "start_frame": 5, "end_frame": 10},
                {"defect_class": "texture_noise", "severity": "MINOR", "start_frame": 15, "end_frame": 20},
            ],
            "lip_sync_offset_ms": 60.0,  # SEVERE
            "micro_flicker_detected": True,  # SEVERE
        }
        report = council.evaluate(cdata, shot_requirement=shot_req)

        assert report.status == CouncilStatus.REJECTED_FOR_REPAIR
        assert report.all_hard_gates_passed is False
        assert report.hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] is False
        assert report.hard_gate_verdicts[HardGateType.LIP_SYNC_ALIGNMENT] is False

        # Verify prioritized repair plan order
        severities = [p.severity for p in report.prioritized_repair_plan]
        # Fatal should come before Severe, which comes before Minor
        assert severities[0] == DefectSeverity.FATAL
        assert DefectSeverity.SEVERE in severities[1:]
        assert severities[-1] == DefectSeverity.MINOR

    def test_integration_with_aether_world_model_instance(
        self,
        council: CriticCouncil,
        shot_req: ShotRequirement,
    ) -> None:
        scene = SceneState(
            scene_id="SC_099",
            location="corridor",
            character_roster={
                "maya": CharacterState(
                    character_id="maya",
                    wardrobe={"coat": WardrobeItemState(id="coat_1", state="torn_shoulder", damage_level=0.5)},
                )
            },
            prop_roster={
                "keycard": PropState(
                    prop_id="keycard",
                    name="Security Keycard",
                    owner_id="maya",
                    hand_attachment=HandAttachment.LEFT,
                )
            },
        )
        wm = AetherWorldModel(initial_state=scene)

        # Candidate with missing keycard and healed coat
        cdata = {
            "characters": {"maya": {"wardrobe": {"coat": {"state": "pristine", "damage_level": 0.0}}}},
            "props_present": [],  # keycard missing
        }

        report = council.evaluate(cdata, scene_state=wm, shot_requirement=shot_req)
        assert report.status == CouncilStatus.REJECTED_FOR_REPAIR
        assert report.hard_gate_verdicts[HardGateType.PROP_CONTINUITY] is False

        defect_types = {f.failure_type for f in report.failures}
        assert "wardrobe_regression" in defect_types
        assert "prop_missing" in defect_types

    def test_soft_score_below_threshold_rejection(
        self,
        council: CriticCouncil,
        shot_req: ShotRequirement,
    ) -> None:
        """Tests that when hard gates pass, soft aesthetic score below 7.0 results in REJECTED_FOR_REPAIR."""
        cdata = {
            "cinematography_score": 5.2,
            "atmosphere_score": 5.5,
            "performance_score": 5.0,
            "pacing_score": 4.8,
            "lip_sync_offset_ms": 15.0,
        }
        report = council.evaluate(cdata, shot_requirement=shot_req)
        assert report.all_hard_gates_passed is True
        assert report.overall_score < 7.0
        assert report.status == CouncilStatus.REJECTED_FOR_REPAIR
        assert "fell below minimum threshold" in report.summary

    def test_all_five_hard_gates_simultaneous_failure(
        self,
        council: CriticCouncil,
        shot_req: ShotRequirement,
    ) -> None:
        """Stress-tests simultaneous failure across all 5 binary hard gates."""
        cdata = {
            # Anatomy failure
            "visual_defects": [{"defect_class": "extra_limbs", "severity": "FATAL"}],
            # Identity failure
            "character_identity_mismatch": True,
            # Lip-sync failure
            "lip_sync_offset_ms": 90.0,
            # Physics failure
            "gravity_violation": True,
            # Prop failure (missing from present props list)
            "props_present": [],
        }
        scene = SceneState(
            scene_id="SC_ALL_FAIL",
            location="chamber",
            prop_roster={
                "torch": PropState(prop_id="torch", name="Torch", owner_id="maya", hand_attachment=HandAttachment.RIGHT)
            },
        )
        report = council.evaluate(cdata, scene_state=scene, shot_requirement=shot_req)

        assert report.status == CouncilStatus.REJECTED_FOR_REPAIR
        assert report.all_hard_gates_passed is False
        assert report.hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] is False
        assert report.hard_gate_verdicts[HardGateType.CHARACTER_IDENTITY] is False
        assert report.hard_gate_verdicts[HardGateType.PROP_CONTINUITY] is False
        assert report.hard_gate_verdicts[HardGateType.LIP_SYNC_ALIGNMENT] is False
        assert report.hard_gate_verdicts[HardGateType.PHYSICAL_TRAJECTORY] is False
        assert len(report.failed_hard_gates) == 5

    def test_custom_critic_and_pluggable_evaluator_integration(
        self,
        shot_req: ShotRequirement,
    ) -> None:
        """Tests pluggable evaluator function and custom critic integration."""
        def mock_vlm_evaluator(candidate, state, req, ctx):
            return [
                CriticFailureObject(
                    failure_type="vlm_detected_uncanny_face",
                    severity=DefectSeverity.SEVERE,
                    frame_bounds=(0, 10),
                    bounding_box=(0.3, 0.2, 0.7, 0.6),
                    target_entity_id="maya",
                    observed_state="Facial musculature frozen in uncanny valley expression",
                    recommended_repair=RepairRecommendation.REGIONAL_INPAINTING,
                    critic_type=CriticType.VISUAL,
                    hard_gate=HardGateType.ANATOMICAL_INTEGRITY,
                )
            ]

        custom_visual = VisualCritic(evaluator_fn=mock_vlm_evaluator)
        council = CriticCouncil(visual_critic=custom_visual)
        report = council.evaluate({}, shot_requirement=shot_req)

        assert report.status == CouncilStatus.REJECTED_FOR_REPAIR
        assert report.hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] is False
        assert any(f.failure_type == "vlm_detected_uncanny_face" for f in report.failures)

    def test_cv_analyzer_numpy_fallback_optical_flow(self) -> None:
        """Tests pure NumPy optical flow calculation when HAS_OPENCV is disabled."""
        analyzer = CVTemporalAnalyzer()
        clean = analyzer.generate_clean_sequence(4, 32, 32)
        gf, gu = analyzer.normalize_frames(clean)

        # Force NumPy fallback path
        import aether.council.cv_analyzer as cv_mod
        orig_has_cv = cv_mod.HAS_OPENCV
        try:
            cv_mod.HAS_OPENCV = False
            mags, vars_ = analyzer.compute_optical_flow(gu, gf)
            assert len(mags) == 3
            assert len(vars_) == 3
            assert all(np.isfinite(mags))
            assert all(np.isfinite(vars_))
        finally:
            cv_mod.HAS_OPENCV = orig_has_cv

    def test_repair_directive_action_descriptions(self, council: CriticCouncil) -> None:
        """Verifies synthesized action descriptions across all RepairRecommendation strategies."""
        failures = [
            CriticFailureObject(
                failure_type="f_inpaint",
                severity=DefectSeverity.SEVERE,
                recommended_repair=RepairRecommendation.REGIONAL_INPAINTING,
                target_entity_id="maya_arm",
            ),
            CriticFailureObject(
                failure_type="f_audio",
                severity=DefectSeverity.SEVERE,
                recommended_repair=RepairRecommendation.AUDIO_REMASTER,
                target_entity_id="dialogue_track",
            ),
            CriticFailureObject(
                failure_type="f_spatial",
                severity=DefectSeverity.SEVERE,
                recommended_repair=RepairRecommendation.SPATIAL_PREVIS_RERUN,
                target_entity_id="camera_crane",
            ),
            CriticFailureObject(
                failure_type="f_regen",
                severity=DefectSeverity.FATAL,
                recommended_repair=RepairRecommendation.FULL_REGEN,
                target_entity_id="shot_main",
            ),
            CriticFailureObject(
                failure_type="f_none",
                severity=DefectSeverity.NEGLIGIBLE,
                recommended_repair=RepairRecommendation.NO_REPAIR_NEEDED,
            ),
        ]
        cdata = {"visual_defects": failures}
        report = council.evaluate(cdata)

        descriptions = [p.action_description for p in report.prioritized_repair_plan]
        assert any("regional temporal inpainting" in d.lower() for d in descriptions)
        assert any("audio-only remaster" in d.lower() for d in descriptions)
        assert any("rerun 3d geometric previs" in d.lower() for d in descriptions)
        assert any("full shot regeneration" in d.lower() for d in descriptions)
        assert any("no repair intervention" in d.lower() for d in descriptions)

    def test_unmapped_fatal_defect_strictly_rejected_by_council(
        self,
        council: CriticCouncil,
        shot_req: ShotRequirement,
    ) -> None:
        """Verifies that ANY breaker defect (even with unmapped hard_gate=None) forces REJECTED_FOR_REPAIR."""
        unmapped_failure = CriticFailureObject(
            failure_type="unknown_quantum_void_glitch",
            severity=DefectSeverity.FATAL,
            hard_gate=None,
            critic_type=None,
            observed_state="Spontaneous reality collapse anomaly",
            recommended_repair=RepairRecommendation.FULL_REGEN,
        )
        cdata = {
            "cinematography_score": 9.9,
            "atmosphere_score": 9.8,
            "performance_score": 9.7,
            "pacing_score": 9.6,
            "visual_defects": [unmapped_failure],
        }
        report = council.evaluate(cdata, shot_requirement=shot_req)
        assert report.status == CouncilStatus.REJECTED_FOR_REPAIR
        assert report.all_hard_gates_passed is False
        assert report.overall_score == 0.0
        assert report.is_accepted is False
        assert len(report.prioritized_repair_plan) >= 1
        assert report.prioritized_repair_plan[0].severity == DefectSeverity.FATAL

    def test_domain_specific_defect_lists_across_all_critics(
        self,
        council: CriticCouncil,
        shot_req: ShotRequirement,
    ) -> None:
        """Verifies each specialized critic parses its domain-specific defect list."""
        cdata = {
            "visual_defects": [
                {"defect_class": "extra_arm_mutation", "severity": "SEVERE"}
            ],
            "temporal_defects": [
                {"defect_class": "strobe_artifact", "severity": "SEVERE"}
            ],
            "continuity_defects": [
                {"defect_class": "prop_continuity_glitch", "severity": "SEVERE"}
            ],
            "performance_defects": [
                {"defect_class": "lip_sync_lag", "severity": "SEVERE"}
            ],
            "physics_defects": [
                {"defect_class": "gravity_failure", "severity": "SEVERE"}
            ],
            "audio_defects": [
                {"defect_class": "vocal_clipping", "severity": "SEVERE"}
            ],
        }
        report = council.evaluate(cdata, shot_requirement=shot_req)
        assert report.status == CouncilStatus.REJECTED_FOR_REPAIR
        assert report.all_hard_gates_passed is False
        # Every critic modality should have caught its respective defect
        for critic_type in (
            CriticType.VISUAL,
            CriticType.TEMPORAL,
            CriticType.CONTINUITY,
            CriticType.PERFORMANCE,
            CriticType.PHYSICS,
            CriticType.AUDIO,
        ):
            audit = report.audit_results[critic_type]
            assert len(audit.failures) >= 1, f"Critic {critic_type} failed to parse domain defects"


# ===========================================================================
# 5. Ollama Vision Critic & Multimodal Integration Tests
# ===========================================================================

class TestOllamaVisionAuditor:
    """Tests for OllamaVisionAuditor prompt construction, response parsing, and error handling."""

    def test_build_audit_prompt(self) -> None:
        auditor = OllamaVisionAuditor()
        req = ShotRequirement(shot_id="SHOT_V01", target_duration=4.5)
        prompt = auditor.build_audit_prompt(shot_requirement=req)
        assert "SHOT_V01" in prompt
        assert "4.5s" in prompt
        assert "ANATOMICAL_INTEGRITY" in prompt
        assert "bounding_box" in prompt

    def test_parse_vision_response_with_bounding_boxes(self) -> None:
        auditor = OllamaVisionAuditor()
        raw_response = {
            "passed": False,
            "visual_score": 3.0,
            "defects": [
                {
                    "failure_type": "polydactyly",
                    "severity": "FATAL",
                    "bounding_box": [0.15, 0.25, 0.65, 0.75],
                    "start_frame": 0,
                    "end_frame": 24,
                    "target_entity_id": "actor_lead",
                    "observed_state": "Six fingers on left hand with fused pinky",
                    "expected_state": "Standard 5-digit human hand",
                    "confidence": 0.97,
                    "recommended_repair": "REGIONAL_INPAINTING",
                    "hard_gate": "ANATOMICAL_INTEGRITY",
                }
            ],
        }

        failures = auditor.parse_vision_response(raw_response)
        assert len(failures) == 1
        f = failures[0]
        assert f.failure_type == "polydactyly"
        assert f.severity == DefectSeverity.FATAL
        assert f.bounding_box == (0.15, 0.25, 0.65, 0.75)
        assert f.hard_gate == HardGateType.ANATOMICAL_INTEGRITY
        assert f.is_hard_gate_breaker is True
        assert f.recommended_repair == RepairRecommendation.REGIONAL_INPAINTING

    def test_parse_vision_response_character_identity(self) -> None:
        auditor = OllamaVisionAuditor()
        raw_response = {
            "passed": False,
            "defects": [
                {
                    "failure_type": "character_identity_drift",
                    "severity": "SEVERE",
                    "bounding_box": [0.3, 0.1, 0.7, 0.5],
                    "target_entity_id": "maya",
                    "observed_state": "Facial features transformed unexpectedly",
                    "hard_gate": "CHARACTER_IDENTITY",
                    "recommended_repair": "FULL_REGEN",
                }
            ],
        }

        failures = auditor.parse_vision_response(raw_response)
        assert len(failures) == 1
        assert failures[0].hard_gate == HardGateType.CHARACTER_IDENTITY
        assert failures[0].severity == DefectSeverity.SEVERE

    def test_parse_vision_audit_result_structured(self) -> None:
        auditor = OllamaVisionAuditor()
        raw_response = {
            "passed": False,
            "visual_score": 4.5,
            "defects": [
                {
                    "failure_type": "polydactyly",
                    "severity": "FATAL",
                    "bounding_box": [0.1, 0.2, 0.6, 0.7],
                    "target_entity_id": "actor_lead",
                    "observed_state": "6 fingers on hand",
                    "hard_gate": "ANATOMICAL_INTEGRITY",
                }
            ],
            "hard_gate_verdicts": {
                "ANATOMICAL_INTEGRITY": False,
                "CHARACTER_IDENTITY": True,
            },
            "summary": "Severe polydactyly identified",
        }
        result = auditor.parse_vision_audit_result(raw_response)
        assert isinstance(result, CriticAuditResult)
        assert result.critic_type == CriticType.VISUAL
        assert result.passed is False
        assert result.score == 4.5
        assert result.hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] is False
        assert result.hard_gate_verdicts[HardGateType.CHARACTER_IDENTITY] is True
        assert len(result.failures) == 1
        assert result.metadata["summary"] == "Severe polydactyly identified"
        assert result.metadata["vision_audited"] is True

    def test_parse_vision_response_null_gate_and_none_frames(self) -> None:
        auditor = OllamaVisionAuditor()
        raw_response = {
            "defects": [
                {
                    "failure_type": "subtle_hand_distortion",
                    "severity": "high",  # String synonym for SEVERE
                    "hard_gate": "null",  # LLM null as string
                    "start_frame": None,
                    "end_frame": None,
                    "confidence": None,
                    "recommended_repair": "inpaint",  # String synonym for REGIONAL_INPAINTING
                }
            ]
        }
        failures = auditor.parse_vision_response(raw_response)
        assert len(failures) == 1
        f = failures[0]
        # Should detect anatomical keyword from failure_type even when hard_gate was 'null'
        assert f.hard_gate == HardGateType.ANATOMICAL_INTEGRITY
        assert f.severity == DefectSeverity.SEVERE
        assert f.frame_bounds == (0, 0)
        assert f.confidence == 0.95
        assert f.recommended_repair == RepairRecommendation.REGIONAL_INPAINTING

    def test_parse_vision_response_dict_bounding_box_1000_scale(self) -> None:
        auditor = OllamaVisionAuditor()
        raw_response = {
            "defects": [
                {
                    "failure_type": "extra_limbs",
                    "severity": "FATAL",
                    "bounding_box": {"x1": 150, "y1": 250, "x2": 650, "y2": 750},
                }
            ]
        }
        failures = auditor.parse_vision_response(raw_response)
        assert len(failures) == 1
        assert failures[0].bounding_box == (0.15, 0.25, 0.65, 0.75)

    def test_auditor_audit_returns_critic_audit_result(self) -> None:
        mock_client = MagicMock()
        mock_client.generate_vision_completion.return_value = {
            "passed": True,
            "visual_score": 9.2,
            "defects": [],
            "hard_gate_verdicts": {
                "ANATOMICAL_INTEGRITY": True,
                "CHARACTER_IDENTITY": True,
            },
            "summary": "Clean visual generation",
        }
        auditor = OllamaVisionAuditor(client=mock_client)
        result = auditor.audit(["frame.png"])
        assert isinstance(result, CriticAuditResult)
        assert result.passed is True
        assert result.score == 9.2
        assert result.metadata["vision_audited"] is True

    def test_audit_frames_graceful_fallback_on_error(self) -> None:
        mock_client = MagicMock()
        mock_client.generate_vision_completion.side_effect = TimeoutError("Connection timed out")

        auditor = OllamaVisionAuditor(client=mock_client)
        failures = auditor.audit_frames(["dummy_path.png"])
        assert failures == []


class TestVisualCriticWithOllama:
    """Tests for VisualCritic multimodal inspection, hard gating, and fallbacks."""

    def test_visual_critic_inspects_frames_with_ollama(self) -> None:
        mock_client = MagicMock()
        mock_client.generate_vision_completion.return_value = {
            "passed": False,
            "defects": [
                {
                    "failure_type": "distorted_hand",
                    "severity": "SEVERE",
                    "bounding_box": [0.2, 0.3, 0.5, 0.6],
                    "hard_gate": "ANATOMICAL_INTEGRITY",
                    "target_entity_id": "character_01",
                }
            ],
        }

        critic = VisualCritic(ollama_client=mock_client)
        cdata = {"keyframes": ["/path/to/frame01.png"]}
        result = critic.audit(cdata)

        assert mock_client.generate_vision_completion.called
        assert len(result.failures) == 1
        assert result.metadata["vision_audited"] is True
        assert result.hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] is False
        assert result.passed is False

    def test_visual_critic_hard_gate_rejection_on_fatal_anatomy(self) -> None:
        mock_client = MagicMock()
        mock_client.generate_vision_completion.return_value = {
            "passed": False,
            "defects": [
                {
                    "failure_type": "extra_limbs",
                    "severity": "FATAL",
                    "bounding_box": [0.1, 0.2, 0.6, 0.8],
                    "hard_gate": "ANATOMICAL_INTEGRITY",
                }
            ],
        }

        critic = VisualCritic(ollama_client=mock_client)
        result = critic.audit({"keyframes": ["frame.png"]})

        assert result.passed is False
        assert result.hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] is False
        assert result.metadata["anatomy_breaker"] is True

    def test_visual_critic_fallback_on_ollama_failure(self) -> None:
        mock_client = MagicMock()
        mock_client.generate_vision_completion.side_effect = RuntimeError("503 Service Unavailable")

        critic = VisualCritic(ollama_client=mock_client)
        # Should gracefully degrade to heuristic check without raising exception
        result = critic.audit({"keyframes": ["frame.png"], "has_extra_limbs": True})

        assert len(result.failures) == 1  # From telemetry flag
        assert result.passed is False
        assert result.metadata["anatomy_breaker"] is True

    def test_visual_critic_synergy_with_cv_analyzer(self) -> None:
        mock_cv = MagicMock()
        mock_cv.analyze_frames.return_value = [
            CriticFailureObject(
                failure_type="cv_micro_flicker",
                severity=DefectSeverity.MODERATE,
                frame_bounds=(1, 3),
            )
        ]

        mock_client = MagicMock()
        mock_client.generate_vision_completion.return_value = {"passed": True, "defects": []}

        critic = VisualCritic(ollama_client=mock_client, cv_analyzer=mock_cv)
        frames = [np.zeros((32, 32, 3), dtype=np.uint8), np.zeros((32, 32, 3), dtype=np.uint8)]
        result = critic.audit({"frames": frames})

        assert mock_client.generate_vision_completion.called
        assert mock_cv.analyze_frames.called
        assert any(f.failure_type == "cv_micro_flicker" for f in result.failures)

    def test_visual_critic_synergy_with_cv_analyzer_image_paths(self, tmp_path) -> None:
        import cv2

        # Create 2 valid image files on disk
        img1_p = tmp_path / "frame1.png"
        img2_p = tmp_path / "frame2.png"
        cv2.imwrite(str(img1_p), np.zeros((32, 32, 3), dtype=np.uint8))
        cv2.imwrite(str(img2_p), np.zeros((32, 32, 3), dtype=np.uint8))

        mock_cv = MagicMock()
        mock_cv.analyze_frames.return_value = []
        mock_client = MagicMock()
        mock_client.generate_vision_completion.return_value = {"passed": True, "defects": []}

        critic = VisualCritic(ollama_client=mock_client, cv_analyzer=mock_cv)
        critic.audit({"keyframes": [str(img1_p), str(img2_p)]})

        assert mock_cv.analyze_frames.called
        call_arg = mock_cv.analyze_frames.call_args[0][0]
        assert hasattr(call_arg, "ndim")


class TestCriticCouncilWithOllama:
    """Tests for CriticCouncil wiring and end-to-end vision QA gatekeeping."""

    def test_council_wires_ollama_client_to_visual_critic(self) -> None:
        mock_client = MagicMock()
        council = CriticCouncil(ollama_client=mock_client)
        assert council.ollama_client == mock_client
        assert council.visual_critic.ollama_client == mock_client
        assert council.visual_critic.vision_auditor is not None

    def test_council_wires_cv_analyzer_to_visual_critic(self) -> None:
        mock_client = MagicMock()
        council = CriticCouncil(ollama_client=mock_client)
        assert council.visual_critic.cv_analyzer is not None
        assert council.visual_critic.cv_analyzer == council.temporal_critic.cv_analyzer

    def test_council_wires_ollama_when_use_ollama_true(self, monkeypatch) -> None:
        monkeypatch.setenv("LLM_PROVIDER", "ollama")
        with patch("pipeline.ollama_client.OllamaClient") as mock_cls:
            council = CriticCouncil()
            assert mock_cls.called
            assert council.ollama_client is not None

    def test_council_end_to_end_vision_hard_gate_rejection(self) -> None:
        mock_client = MagicMock()
        mock_client.generate_vision_completion.return_value = {
            "passed": False,
            "defects": [
                {
                    "failure_type": "polydactyly",
                    "severity": "FATAL",
                    "bounding_box": [0.3, 0.4, 0.7, 0.8],
                    "target_entity_id": "character_01",
                    "observed_state": "Six fingers on right hand with fused extra digit",
                    "expected_state": "Normal five-fingered human hand",
                    "confidence": 0.98,
                    "recommended_repair": "REGIONAL_INPAINTING",
                    "hard_gate": "ANATOMICAL_INTEGRITY",
                }
            ],
        }

        council = CriticCouncil(ollama_client=mock_client)
        cdata = {
            "shot_id": "SHOT_QA_001",
            "keyframes": ["/path/to/frame.png"],
            "cinematography_score": 9.5,
            "atmosphere_score": 9.0,
        }

        report = council.evaluate(cdata)

        # Candidate had high potential aesthetic score but MUST be rejected due to anatomical hard gate
        assert report.status == CouncilStatus.REJECTED_FOR_REPAIR
        assert report.all_hard_gates_passed is False
        assert report.hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] is False
        assert report.overall_score == 0.0

        # Prioritized repair plan must contain the surgical inpainting directive
        assert len(report.prioritized_repair_plan) >= 1
        directive = report.prioritized_repair_plan[0]
        assert directive.repair_type == RepairRecommendation.REGIONAL_INPAINTING
        assert directive.defect_type == "polydactyly"
        assert directive.severity == DefectSeverity.FATAL
        assert directive.bounding_box == (0.3, 0.4, 0.7, 0.8)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


