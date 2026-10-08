"""Comprehensive Test Suite for Phase 6: Surgical Repair Engine (WBS 1.7).

Verifies:
1. Pydantic V2 schemas (RepairActionType, RepairBoundaryMask, ProtectedRegion,
   SurgicalRepairTask, RepairPlan, RepairExecutionResult, ComputeTier).
2. Spatio-Temporal Masking Engine (TemporalMaskEngine):
   - Bounding box expansion and spatial boundary preservation.
   - Continuous distance-based spatial feathering (Gaussian, cosine, linear falloffs).
   - Temporal ramp-in and ramp-out frame padding weights (eliminating boundary strobing).
   - Clean background and actor face protection shielding.
   - Boundary seam metric validation addressing RSK-004.
3. Surgical Repair Planner (RepairPlanner) with Minimum Necessary Intervention:
   - Dialogue desync / clipping -> AUDIO_REMASTER_VOICE without touching video pixels.
   - Foley audio mismatch -> AUDIO_REMASTER_FOLEY.
   - Localized hand deformation at t=5.8-6.4s in 8s shot -> REGIONAL_TEMPORAL_INPAINTING
     targeting hand sub-region without re-rendering entire shot.
   - Physical trajectory failure -> SPATIAL_PREVIS_REBLOCK targeting UE5 motion guides.
   - Defect escalation to FULL_SHOT_REGENERATION when > 3 severe non-localized defects exist.
   - Defect escalation to FULL_SHOT_REGENERATION when multiple hard gates fail across > 70% frames.
   - Clean pass / NO_OP verification for accepted shots.
   - Overlapping spatial/temporal defect deduplication and task merging.
4. Surgical Repair Executor (SurgicalRepairExecutor):
   - Inpainting payload synthesis for ComfyUI.
   - Audio remux payload synthesis for FFmpeg with zero video modification.
   - Spatial previs reblock payload synthesis for UE5.
   - Full shot regeneration payload synthesis.
   - Boundary seam metric validation and council verification flagging.
   - High seam metric fallback triggering.
   - Sequential plan execution with cascading asset URIs.
"""

from __future__ import annotations

import math
from pathlib import Path
import sys
import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from aether.compiler.schemas import AudioRequirement, ShotRequirement
from aether.council.schemas import (
    CouncilEvaluationReport,
    CouncilStatus,
    CriticFailureObject,
    CriticType,
    DefectSeverity,
    HardGateType,
    RepairRecommendation,
)
from aether.repair import (
    ComputeTier,
    ProtectedRegion,
    ProtectedRegionType,
    RepairActionType,
    RepairBoundaryMask,
    RepairExecutionResult,
    RepairPlan,
    RepairPlanner,
    SurgicalRepairExecutor,
    SurgicalRepairTask,
    TemporalMaskEngine,
)
from aether.state.schemas import CharacterState, SceneState


# ===========================================================================
# 1. Schemas Tests
# ===========================================================================

class TestRepairSchemas:
    """Tests Pydantic V2 schemas for the Surgical Repair Engine."""

    def test_repair_action_type_enum(self) -> None:
        assert RepairActionType.REGIONAL_TEMPORAL_INPAINTING == "REGIONAL_TEMPORAL_INPAINTING"
        assert RepairActionType.AUDIO_REMASTER_VOICE == "AUDIO_REMASTER_VOICE"
        assert RepairActionType.AUDIO_REMASTER_FOLEY == "AUDIO_REMASTER_FOLEY"
        assert RepairActionType.SPATIAL_PREVIS_REBLOCK == "SPATIAL_PREVIS_REBLOCK"
        assert RepairActionType.FULL_SHOT_REGENERATION == "FULL_SHOT_REGENERATION"
        assert RepairActionType.NO_OP == "NO_OP"

        # Alias support for prompt typo
        assert RepairActionType.REGIONAL_TEMONTAL_INPAINTING == RepairActionType.REGIONAL_TEMPORAL_INPAINTING

        # Coercion from strings
        assert RepairActionType.from_str("regional_temporal_inpainting") == RepairActionType.REGIONAL_TEMPORAL_INPAINTING
        assert RepairActionType.from_str("REGIONAL_TEMONTAL_INPAINTING") == RepairActionType.REGIONAL_TEMPORAL_INPAINTING
        assert RepairActionType.from_str("audio_remaster_voice") == RepairActionType.AUDIO_REMASTER_VOICE
        assert RepairActionType.from_str("spatial_previs_reblock") == RepairActionType.SPATIAL_PREVIS_REBLOCK

    def test_protected_region_schema(self) -> None:
        pr = ProtectedRegion(
            region_type="FACE",
            bounding_box=[0.3, 0.1, 0.5, 0.3],
            frame_bounds=[0, 100],
            protection_strength=0.95,
            description="Actor face shield",
        )
        assert pr.region_type == ProtectedRegionType.FACE
        assert pr.bounding_box == (0.3, 0.1, 0.5, 0.3)
        assert pr.frame_bounds == (0, 100)
        assert pr.protection_strength == 0.95

    def test_repair_boundary_mask_schema(self) -> None:
        mask = RepairBoundaryMask(
            bounding_box=(0.1, 0.2, 0.4, 0.5),
            frame_bounds=(10, 30),
            feather_radius_px=20.0,
            temporal_pad_frames=5,
        )
        assert mask.x1 == 0.1
        assert mask.y1 == 0.2
        assert mask.x2 == 0.4
        assert mask.y2 == 0.5
        assert mask.start_frame == 10
        assert mask.end_frame == 30
        assert mask.duration_frames == 21
        assert mask.padded_start_frame == 5
        assert mask.padded_end_frame == 35
        assert pytest.approx(mask.area, 0.001) == 0.09

        # Coordinate clamping and ordering
        inverted = RepairBoundaryMask(
            bounding_box=(0.8, 0.9, 0.2, 0.1),
            frame_bounds=(50, 20),
        )
        assert inverted.x1 == 0.2
        assert inverted.x2 == 0.8
        assert inverted.y1 == 0.1
        assert inverted.y2 == 0.9
        assert inverted.start_frame == 20
        assert inverted.end_frame == 50

    def test_surgical_repair_task_schema(self) -> None:
        task = SurgicalRepairTask(
            task_id="TASK_001",
            action_type=RepairActionType.REGIONAL_TEMPORAL_INPAINTING,
            target_defect_id="extra_fingers",
            defect_severity=DefectSeverity.SEVERE,
            priority=2,
            replacement_prompt="photorealistic hand",
            fallback_strategy=RepairActionType.FULL_SHOT_REGENERATION,
        )
        assert task.is_inpainting is True
        assert task.is_audio is False
        assert task.is_previs is False
        assert task.is_full_regen is False
        assert task.fallback_strategy == RepairActionType.FULL_SHOT_REGENERATION

    def test_repair_plan_schema(self) -> None:
        t1 = SurgicalRepairTask(
            task_id="T1",
            action_type=RepairActionType.AUDIO_REMASTER_VOICE,
            priority=3,
        )
        t2 = SurgicalRepairTask(
            task_id="T2",
            action_type=RepairActionType.REGIONAL_TEMPORAL_INPAINTING,
            priority=2,
        )
        plan = RepairPlan(
            plan_id="PLAN_001",
            original_shot_id="SHOT_001",
            ordered_tasks_list=[t2, t1],
            estimated_compute_tier=ComputeTier.TIER_2_REGIONAL_INPAINT,
            expected_latency=9.7,
            is_feasible=True,
        )
        assert plan.total_tasks_count == 2
        assert len(plan.tasks) == 2
        assert plan.has_inpainting is True
        assert plan.has_audio_repair is True
        assert plan.has_full_regen is False
        assert plan.is_empty is False

    def test_repair_execution_result_schema(self) -> None:
        res = RepairExecutionResult(
            task_id="TASK_001",
            success=True,
            repaired_asset_uri="shot_repaired.mp4",
            boundary_seam_metric=0.002,
            latency=5.4,
            verified_by_council_flag=True,
        )
        assert res.success is True
        assert res.is_seamless is True
        assert res.verified_by_council_flag is True


# ===========================================================================
# 2. Temporal Mask Engine Tests (RSK-004 Mitigations)
# ===========================================================================

class TestTemporalMaskEngine:
    """Tests spatio-temporal mask synthesis and boundary feathering."""

    @pytest.fixture
    def engine(self) -> TemporalMaskEngine:
        return TemporalMaskEngine(
            default_feather_radius_px=16.0,
            default_temporal_pad_frames=4,
            default_box_expansion_ratio=0.10,
            default_resolution=(720, 1280),
        )

    def test_expand_bounding_box(self, engine: TemporalMaskEngine) -> None:
        raw_box = (0.3, 0.4, 0.5, 0.6)  # width 0.2, height 0.2
        expanded = engine.expand_bounding_box(raw_box, expansion_ratio=0.10)
        # Expansion by 10% of 0.2 is 0.02
        assert pytest.approx(expanded[0], 0.001) == 0.28
        assert pytest.approx(expanded[1], 0.001) == 0.38
        assert pytest.approx(expanded[2], 0.001) == 0.52
        assert pytest.approx(expanded[3], 0.001) == 0.62

        # Expansion clamped at border [0.0, 1.0]
        near_edge = (0.01, 0.01, 0.99, 0.99)
        clamped = engine.expand_bounding_box(near_edge, expansion_ratio=0.20)
        assert clamped[0] == 0.0
        assert clamped[1] == 0.0
        assert clamped[2] == 1.0
        assert clamped[3] == 1.0

    def test_create_boundary_mask(self, engine: TemporalMaskEngine) -> None:
        failure = CriticFailureObject(
            failure_type="hand_deformation",
            severity=DefectSeverity.SEVERE,
            frame_bounds=(174, 192),
            bounding_box=(0.60, 0.50, 0.70, 0.60),
        )
        mask = engine.create_boundary_mask(
            failure=failure,
            feather_radius_px=24.0,
            temporal_pad_frames=6,
            box_expansion_ratio=0.15,
        )
        assert mask.frame_bounds == (174, 192)
        assert mask.feather_radius_px == 24.0
        assert mask.temporal_pad_frames == 6
        assert mask.start_frame == 174
        assert mask.end_frame == 192
        # Verify expanded box is larger than raw box
        assert mask.x1 < 0.60
        assert mask.x2 > 0.70

    def test_spatial_mask_feathering_falloff(self, engine: TemporalMaskEngine) -> None:
        bbox = (0.3, 0.3, 0.7, 0.7)
        res = (720, 1280)

        # 1. Cosine falloff
        mask_cosine = engine.generate_spatial_mask(bbox, resolution=res, feather_radius_px=16.0, falloff="cosine")
        assert mask_cosine.shape == res
        # Center core must be strictly 1.0
        assert mask_cosine[360, 640] == 1.0
        # Far corner must be strictly 0.0
        assert mask_cosine[10, 10] == 0.0
        # Values must be within [0.0, 1.0]
        assert mask_cosine.min() >= 0.0
        assert mask_cosine.max() <= 1.0

        # 2. Gaussian falloff
        mask_gauss = engine.generate_spatial_mask(bbox, resolution=res, feather_radius_px=16.0, falloff="gaussian")
        assert mask_gauss.shape == res
        assert mask_gauss[360, 640] == 1.0
        assert mask_gauss[10, 10] == 0.0

        # 3. Linear falloff
        mask_linear = engine.generate_spatial_mask(bbox, resolution=res, feather_radius_px=16.0, falloff="linear")
        assert mask_linear.shape == res
        assert mask_linear[360, 640] == 1.0
        assert mask_linear[10, 10] == 0.0

    def test_temporal_weights_ramping(self, engine: TemporalMaskEngine) -> None:
        total_frames = 100
        start = 40
        end = 60
        pad = 4
        weights = engine.compute_temporal_weights(total_frames, start, end, pad_frames=pad)

        assert weights.shape == (total_frames,)
        # Frames before pad must be strictly 0.0
        assert np.all(weights[:36] == 0.0)
        # Core defect frames must be strictly 1.0
        assert np.all(weights[40:61] == 1.0)
        # Frames after pad must be strictly 0.0
        assert np.all(weights[65:] == 0.0)

        # Ramp-in monotonic increase
        assert 0.0 < weights[36] < weights[37] < weights[38] < weights[39] < 1.0
        # Ramp-out monotonic decrease
        assert 1.0 > weights[61] > weights[62] > weights[63] > weights[64] > 0.0

    def test_spatio_temporal_3d_tensor(self, engine: TemporalMaskEngine) -> None:
        bmask = RepairBoundaryMask(
            bounding_box=(0.4, 0.4, 0.6, 0.6),
            frame_bounds=(5, 10),
            feather_radius_px=8.0,
            temporal_pad_frames=2,
        )
        res = (120, 160)
        tensor = engine.generate_spatio_temporal_mask(bmask, total_frames=20, resolution=res)

        assert tensor.shape == (20, 120, 160)
        # Frame 0 is outside temporal range -> all zeros
        assert np.all(tensor[0] == 0.0)
        # Frame 7 is in the defect core -> active mask with max 1.0
        assert tensor[7].max() == 1.0
        # Frame 3 is in ramp-in -> active mask with max < 1.0
        assert 0.0 < tensor[3].max() < 1.0

    def test_protected_region_shielding(self, engine: TemporalMaskEngine) -> None:
        res = (200, 200)
        # Inpainting mask covers entire region (0.1 to 0.9)
        base_mask = engine.generate_spatial_mask((0.1, 0.1, 0.9, 0.9), resolution=res, feather_radius_px=0.0)

        # Protect a face area at (0.3, 0.3, 0.5, 0.5)
        face_protection = ProtectedRegion(
            region_type=ProtectedRegionType.FACE,
            bounding_box=(0.3, 0.3, 0.5, 0.5),
            protection_strength=1.0,
        )
        shielded = engine.apply_protection_to_mask(base_mask, [face_protection], resolution=res)

        # Protected region should be strictly 0.0
        assert np.all(shielded[60:100, 60:100] == 0.0)
        # Outside protected region should remain 1.0
        assert shielded[30, 30] == 1.0

    def test_rsk004_boundary_seam_metric_feathered_vs_raw(self, engine: TemporalMaskEngine) -> None:
        """Verifies RSK-004: Feathering eliminates sharp edge seam discontinuity."""
        res = (400, 400)
        box = (0.2, 0.2, 0.6, 0.6)

        # Raw unfeathered binary mask (sharp step edge)
        raw_mask = engine.generate_spatial_mask(box, resolution=res, feather_radius_px=0.0)
        seam_raw = engine.compute_boundary_seam_metric(raw_mask)

        # Continuous feathered mask (16px feather radius)
        feathered_mask = engine.generate_spatial_mask(box, resolution=res, feather_radius_px=16.0)
        seam_feathered = engine.compute_boundary_seam_metric(feathered_mask)

        # Raw step edge must exhibit severe seam variance (> 0.20)
        assert seam_raw > 0.20, f"Raw seam metric {seam_raw} should exceed 0.20"

        # Feathered edge must exhibit low seam variance (<= 0.05)
        assert seam_feathered <= 0.05, f"Feathered seam metric {seam_feathered} should be <= 0.05"
        assert seam_feathered < seam_raw


# ===========================================================================
# 3. Surgical Repair Planner Tests (Minimum Necessary Intervention)
# ===========================================================================

class TestRepairPlanner:
    """Tests the Minimum Necessary Intervention planning logic."""

    @pytest.fixture
    def planner(self) -> RepairPlanner:
        return RepairPlanner(
            default_fps=30.0,
            escalation_defect_threshold=3,
            escalation_frame_coverage_threshold=0.70,
        )

    def test_clean_pass_no_op(self, planner: RepairPlanner) -> None:
        """Shots passing all gates without defects produce an empty NO-OP plan."""
        report = CouncilEvaluationReport(
            status=CouncilStatus.ACCEPTED,
            hard_gate_verdicts={
                HardGateType.ANATOMICAL_INTEGRITY: True,
                HardGateType.CHARACTER_IDENTITY: True,
                HardGateType.PROP_CONTINUITY: True,
                HardGateType.LIP_SYNC_ALIGNMENT: True,
                HardGateType.PHYSICAL_TRAJECTORY: True,
            },
            failures=[],
            shot_id="SHOT_HERO_001",
        )
        plan = planner.plan_repair(report)
        assert plan.total_tasks_count == 0
        assert plan.is_empty is True
        assert plan.estimated_compute_tier == ComputeTier.TIER_0_NOOP
        assert plan.expected_latency == 0.0
        assert plan.is_feasible is True

    def test_audio_only_minimum_intervention(self, planner: RepairPlanner) -> None:
        """Dialogue desync at t=2.0-3.0s triggers AUDIO_REMASTER_VOICE without touching pixels."""
        failure = CriticFailureObject(
            failure_type="dialogue_latency_offset",
            severity=DefectSeverity.SEVERE,
            frame_bounds=(60, 90),
            bounding_box=(0.0, 0.0, 1.0, 1.0),
            target_entity_id="char_maya",
            critic_type=CriticType.AUDIO,
            metadata={"latency_shift_ms": -140.0, "target_phonemes": ["M", "AY", "AH"]},
        )
        report = CouncilEvaluationReport(
            status=CouncilStatus.REJECTED_FOR_REPAIR,
            hard_gate_verdicts={HardGateType.LIP_SYNC_ALIGNMENT: False},
            failures=[failure],
            shot_id="SHOT_DIALOGUE_002",
        )
        shot_req = ShotRequirement(shot_id="SHOT_DIALOGUE_002", target_duration=5.0)

        plan = planner.plan_repair(report, shot_requirement=shot_req)

        assert plan.total_tasks_count == 1
        task = plan.tasks[0]
        assert task.action_type == RepairActionType.AUDIO_REMASTER_VOICE
        # Zero pixel alteration
        assert task.repair_boundary_mask is None
        assert task.audio_retargeting_params["latency_shift_ms"] == -140.0
        assert task.audio_retargeting_params["preserve_video_stream"] is True
        assert plan.estimated_compute_tier == ComputeTier.TIER_1_AUDIO

    def test_foley_remaster_intervention(self, planner: RepairPlanner) -> None:
        """Foley sound artifact triggers AUDIO_REMASTER_FOLEY."""
        failure = CriticFailureObject(
            failure_type="foley_footstep_mismatch",
            severity=DefectSeverity.MODERATE,
            frame_bounds=(10, 40),
            bounding_box=(0.0, 0.0, 1.0, 1.0),
            critic_type=CriticType.AUDIO,
            metadata={"latency_shift_ms": 50.0},
        )
        report = CouncilEvaluationReport(
            status=CouncilStatus.REJECTED_FOR_REPAIR,
            failures=[failure],
            shot_id="SHOT_FOLEY_003",
        )
        plan = planner.plan_repair(report)
        assert plan.total_tasks_count == 1
        assert plan.tasks[0].action_type == RepairActionType.AUDIO_REMASTER_FOLEY

    def test_localized_hand_inpainting_intervention(self, planner: RepairPlanner) -> None:
        """Hand/limb deformation at t=5.8-6.4s in 8s shot dispatches localized inpainting."""
        # 8s shot at 30 fps = 240 frames total.
        # t=5.8s -> frame 174, t=6.4s -> frame 192.
        failure = CriticFailureObject(
            failure_type="extra_fingers_hand_distortion",
            severity=DefectSeverity.SEVERE,
            frame_bounds=(174, 192),
            bounding_box=(0.60, 0.50, 0.75, 0.65),  # localized hand region (area = 0.0225)
            target_entity_id="char_maya",
            hard_gate=HardGateType.ANATOMICAL_INTEGRITY,
            critic_type=CriticType.VISUAL,
        )
        report = CouncilEvaluationReport(
            status=CouncilStatus.REJECTED_FOR_REPAIR,
            hard_gate_verdicts={HardGateType.ANATOMICAL_INTEGRITY: False},
            failures=[failure],
            shot_id="SHOT_HAND_004",
        )
        shot_req = ShotRequirement(shot_id="SHOT_HAND_004", target_duration=8.0)

        plan = planner.plan_repair(report, shot_requirement=shot_req)

        assert plan.total_tasks_count == 1
        task = plan.tasks[0]
        assert task.action_type == RepairActionType.REGIONAL_TEMPORAL_INPAINTING
        # Mask targets strictly localized sub-region
        assert task.repair_boundary_mask is not None
        assert task.repair_boundary_mask.frame_bounds == (174, 192)
        assert task.repair_boundary_mask.area < 0.20  # Sub-region only, not full frame
        assert "hand" in (task.replacement_prompt or "")
        assert "extra fingers" in (task.negative_prompt_modifier or "")
        assert plan.estimated_compute_tier == ComputeTier.TIER_2_REGIONAL_INPAINT

    def test_spatial_previs_reblock_intervention(self, planner: RepairPlanner) -> None:
        """Physical trajectory / gravity breakdown triggers UE5 SPATIAL_PREVIS_REBLOCK."""
        failure = CriticFailureObject(
            failure_type="unphysical_gravity_acceleration_spike",
            severity=DefectSeverity.SEVERE,
            frame_bounds=(30, 75),
            bounding_box=(0.2, 0.2, 0.8, 0.8),
            target_entity_id="actor_hero",
            hard_gate=HardGateType.PHYSICAL_TRAJECTORY,
            critic_type=CriticType.PHYSICS,
            recommended_repair=RepairRecommendation.SPATIAL_PREVIS_RERUN,
        )
        report = CouncilEvaluationReport(
            status=CouncilStatus.REJECTED_FOR_REPAIR,
            hard_gate_verdicts={HardGateType.PHYSICAL_TRAJECTORY: False},
            failures=[failure],
            shot_id="SHOT_PHYSICS_005",
        )
        plan = planner.plan_repair(report)

        assert plan.total_tasks_count == 1
        task = plan.tasks[0]
        assert task.action_type == RepairActionType.SPATIAL_PREVIS_REBLOCK
        assert "ue5_reblock_directives" in task.metadata
        assert plan.estimated_compute_tier == ComputeTier.TIER_3_PREVIS_REBLOCK

    def test_escalation_to_full_regen_defect_count(self, planner: RepairPlanner) -> None:
        """Escalates to FULL_SHOT_REGENERATION when > 3 severe non-localized defects exist."""
        failures = [
            CriticFailureObject(
                failure_type=f"global_flicker_defect_{i}",
                severity=DefectSeverity.SEVERE,
                frame_bounds=(0, 50),
                bounding_box=(0.0, 0.0, 1.0, 1.0),  # non-localized full frame
            )
            for i in range(4)  # 4 defects > threshold of 3
        ]
        report = CouncilEvaluationReport(
            status=CouncilStatus.REJECTED_FOR_REPAIR,
            failures=failures,
            shot_id="SHOT_ESCALATE_006",
        )
        plan = planner.plan_repair(report)

        assert plan.total_tasks_count == 1
        assert plan.tasks[0].action_type == RepairActionType.FULL_SHOT_REGENERATION
        assert plan.estimated_compute_tier == ComputeTier.TIER_4_FULL_REGEN
        assert plan.has_full_regen is True
        assert "Defect count exceeded threshold" in plan.summary

    def test_escalation_to_full_regen_multiple_hard_gates_70_percent(self, planner: RepairPlanner) -> None:
        """Escalates to FULL_SHOT_REGENERATION when multiple hard gates fail across > 70% frames."""
        # 5s shot @ 30fps = 150 frames. 70% of 150 = 105 frames.
        # Defect 1: ANATOMICAL_INTEGRITY failing frames 0 to 120 (121 frames = 80.6%)
        f1 = CriticFailureObject(
            failure_type="severe_body_deformation",
            severity=DefectSeverity.SEVERE,
            frame_bounds=(0, 120),
            bounding_box=(0.2, 0.2, 0.5, 0.5),
            hard_gate=HardGateType.ANATOMICAL_INTEGRITY,
        )
        # Defect 2: CHARACTER_IDENTITY failing frames 20 to 130
        f2 = CriticFailureObject(
            failure_type="character_face_drift",
            severity=DefectSeverity.SEVERE,
            frame_bounds=(20, 130),
            bounding_box=(0.3, 0.1, 0.6, 0.4),
            hard_gate=HardGateType.CHARACTER_IDENTITY,
        )
        report = CouncilEvaluationReport(
            status=CouncilStatus.REJECTED_FOR_REPAIR,
            hard_gate_verdicts={
                HardGateType.ANATOMICAL_INTEGRITY: False,
                HardGateType.CHARACTER_IDENTITY: False,
            },
            failures=[f1, f2],
            shot_id="SHOT_ESCALATE_007",
        )
        shot_req = ShotRequirement(shot_id="SHOT_ESCALATE_007", target_duration=5.0)

        plan = planner.plan_repair(report, shot_requirement=shot_req)

        assert plan.total_tasks_count == 1
        assert plan.tasks[0].action_type == RepairActionType.FULL_SHOT_REGENERATION
        assert plan.estimated_compute_tier == ComputeTier.TIER_4_FULL_REGEN
        assert "Multiple hard gates" in plan.summary

    def test_deduplication_and_merging_of_overlapping_defects(self, planner: RepairPlanner) -> None:
        """Merges two overlapping inpaint defects into a single unified task."""
        # Two hand defects slightly overlapping spatially and temporally
        f1 = CriticFailureObject(
            failure_type="extra_finger",
            severity=DefectSeverity.MODERATE,
            frame_bounds=(40, 60),
            bounding_box=(0.50, 0.50, 0.65, 0.65),
            target_entity_id="char_maya",
        )
        f2 = CriticFailureObject(
            failure_type="hand_texture_seam",
            severity=DefectSeverity.SEVERE,
            frame_bounds=(45, 65),
            bounding_box=(0.52, 0.52, 0.70, 0.70),
            target_entity_id="char_maya",
        )
        report = CouncilEvaluationReport(
            status=CouncilStatus.REJECTED_FOR_REPAIR,
            failures=[f1, f2],
            shot_id="SHOT_MERGE_008",
        )
        plan = planner.plan_repair(report)

        # Must merge the 2 defects into 1 unified task
        assert plan.total_tasks_count == 1
        merged_task = plan.tasks[0]
        assert merged_task.action_type == RepairActionType.REGIONAL_TEMPORAL_INPAINTING
        # Takes highest severity (SEVERE)
        assert merged_task.defect_severity == DefectSeverity.SEVERE
        mask = merged_task.repair_boundary_mask
        assert mask is not None
        # Merged frame bounds covers both [40, 65]
        assert mask.start_frame <= 40
        assert mask.end_frame >= 65


# ===========================================================================
# 4. Surgical Repair Executor Tests
# ===========================================================================

class TestSurgicalRepairExecutor:
    """Tests the dispatch, payload synthesis, and execution of repair plans."""

    @pytest.fixture
    def executor(self) -> SurgicalRepairExecutor:
        return SurgicalRepairExecutor(seam_metric_threshold=0.05)

    def test_synthesize_inpainting_payload(self, executor: SurgicalRepairExecutor) -> None:
        mask = RepairBoundaryMask(
            bounding_box=(0.2, 0.3, 0.5, 0.6),
            frame_bounds=(10, 25),
            feather_radius_px=16.0,
            temporal_pad_frames=4,
        )
        task = SurgicalRepairTask(
            task_id="TASK_INP_001",
            action_type=RepairActionType.REGIONAL_TEMPORAL_INPAINTING,
            repair_boundary_mask=mask,
            replacement_prompt="photorealistic hand",
            negative_prompt_modifier="extra limbs",
        )
        payload = executor.synthesize_inpainting_payload(task)

        assert payload["renderer"] == "ComfyUI_Temporal_Inpaint_V2"
        assert payload["bounding_box"] == [0.2, 0.3, 0.5, 0.6]
        assert payload["frame_bounds"] == [10, 25]
        assert payload["padded_frame_bounds"] == [6, 29]
        assert payload["positive_prompt"] == "photorealistic hand"
        assert payload["negative_prompt"] == "extra limbs"
        assert payload["feather_radius_px"] == 16.0
        assert payload["flow_guided_blend"] is True

    def test_execute_inpainting_task_seamless(self, executor: SurgicalRepairExecutor) -> None:
        mask = RepairBoundaryMask(
            bounding_box=(0.3, 0.3, 0.6, 0.6),
            frame_bounds=(20, 40),
            feather_radius_px=16.0,
        )
        task = SurgicalRepairTask(
            task_id="TASK_INP_002",
            action_type=RepairActionType.REGIONAL_TEMPORAL_INPAINTING,
            repair_boundary_mask=mask,
            replacement_prompt="clean render",
        )
        result = executor.execute_task(task, base_asset_uri="shots/hero.mp4")

        assert result.success_status is True
        assert result.repaired_asset_uri is not None
        assert "hero_inp_TASK_INP_002.mp4" in result.repaired_asset_uri
        assert result.boundary_seam_metric <= 0.05
        assert result.is_seamless is True
        assert result.verified_by_council_flag is True

    def test_execute_audio_remux_task(self, executor: SurgicalRepairExecutor) -> None:
        task = SurgicalRepairTask(
            task_id="TASK_AUD_001",
            action_type=RepairActionType.AUDIO_REMASTER_VOICE,
            audio_retargeting_params={"latency_shift_ms": -120.0},
        )
        result = executor.execute_task(task, base_asset_uri="shots/hero.mp4")

        assert result.success_status is True
        assert "hero_remux_TASK_AUD_001.mp4" in (result.repaired_asset_uri or "")
        assert result.metadata["video_frames_modified"] is False
        assert result.boundary_seam_metric == 0.0
        assert result.verified_by_council_flag is True

    def test_execute_previs_reblock_task(self, executor: SurgicalRepairExecutor) -> None:
        task = SurgicalRepairTask(
            task_id="TASK_PREVIS_001",
            action_type=RepairActionType.SPATIAL_PREVIS_REBLOCK,
            metadata={"ue5_reblock_directives": {"adjust_trajectory": True}},
        )
        result = executor.execute_task(task)

        assert result.success_status is True
        assert "previs://reblock_TASK_PREVIS_001.fbx" in (result.repaired_asset_uri or "")
        assert result.boundary_seam_metric == 0.0
        assert result.verified_by_council_flag is True

    def test_execute_full_regen_task(self, executor: SurgicalRepairExecutor) -> None:
        task = SurgicalRepairTask(
            task_id="TASK_REGEN_001",
            action_type=RepairActionType.FULL_SHOT_REGENERATION,
            replacement_prompt="complete regeneration",
        )
        result = executor.execute_task(task, base_asset_uri="shots/hero.mp4")

        assert result.success_status is True
        assert "hero_full_regen_TASK_REGEN_001.mp4" in (result.repaired_asset_uri or "")
        assert result.boundary_seam_metric == 0.0
        assert result.verified_by_council_flag is True

    def test_high_seam_metric_fallback_trigger(self) -> None:
        """When an unfeathered mask creates a seam above threshold, triggers fallback."""
        # Custom backend simulating high seam metric
        def mock_failing_backend(payload: dict) -> dict:
            return {"boundary_seam_metric": 0.28, "asset_uri": "failed_seam.mp4"}

        executor = SurgicalRepairExecutor(
            seam_metric_threshold=0.05,
            custom_renderer_backend=mock_failing_backend,
        )
        mask = RepairBoundaryMask(bounding_box=(0.1, 0.1, 0.5, 0.5), feather_radius_px=0.0)
        task = SurgicalRepairTask(
            task_id="TASK_SEAM_FAIL",
            action_type=RepairActionType.REGIONAL_TEMPORAL_INPAINTING,
            repair_boundary_mask=mask,
            fallback_strategy=RepairActionType.FULL_SHOT_REGENERATION,
        )
        result = executor.execute_task(task)

        assert result.success_status is False
        assert result.repaired_asset_uri is None
        assert result.metadata["fallback_triggered"] == "FULL_SHOT_REGENERATION"
        assert result.verified_by_council_flag is False
        assert "RSK-004 seam failure" in (result.error_message or "")

    def test_execute_plan_cascading_assets(self, executor: SurgicalRepairExecutor) -> None:
        """Multi-task execution cascades repaired asset URIs through successive stages."""
        mask = RepairBoundaryMask(bounding_box=(0.1, 0.1, 0.3, 0.3), feather_radius_px=16.0)
        t_inpaint = SurgicalRepairTask(
            task_id="T_INP",
            action_type=RepairActionType.REGIONAL_TEMPORAL_INPAINTING,
            repair_boundary_mask=mask,
            priority=2,
        )
        t_audio = SurgicalRepairTask(
            task_id="T_AUD",
            action_type=RepairActionType.AUDIO_REMASTER_VOICE,
            audio_retargeting_params={"latency_shift_ms": -80.0},
            priority=3,
        )
        plan = RepairPlan(
            plan_id="PLAN_CASCADE",
            original_shot_id="SHOT_CASCADE",
            ordered_tasks_list=[t_inpaint, t_audio],
            estimated_compute_tier=ComputeTier.TIER_2_REGIONAL_INPAINT,
        )
        results = executor.execute_plan(plan, base_asset_uri="asset://shots/shot_001.mp4")

        assert len(results) == 2
        # First task repairs the base video
        assert "shot_001_inp_T_INP.mp4" in results[0].repaired_asset_uri
        # Second task remuxes the output of the first task
        assert "shot_001_inp_T_INP_remux_T_AUD.mp4" in results[1].repaired_asset_uri
        assert all(r.success_status for r in results)
        assert all(r.verified_by_council_flag for r in results)


# ===========================================================================
# 5. Edge Cases & Boundary Value Tests
# ===========================================================================

class TestRepairEdgeCases:
    """Verifies boundary conditions, error handling, and serialization."""

    def test_single_frame_defect(self) -> None:
        engine = TemporalMaskEngine()
        weights = engine.compute_temporal_weights(total_frames=30, start_frame=15, end_frame=15, pad_frames=3)
        assert weights[15] == 1.0
        assert 0.0 < weights[14] < 1.0
        assert 0.0 < weights[16] < 1.0
        assert weights[11] == 0.0
        assert weights[19] == 0.0

    def test_temporal_padding_boundary_clamps(self) -> None:
        engine = TemporalMaskEngine()
        # Defect starting at frame 0 (cannot pad before 0)
        w_start = engine.compute_temporal_weights(total_frames=20, start_frame=0, end_frame=2, pad_frames=4)
        assert w_start[0] == 1.0
        assert w_start[1] == 1.0
        assert w_start[2] == 1.0
        assert w_start[3] < 1.0

        # Defect ending at last frame (cannot pad past total_frames - 1)
        w_end = engine.compute_temporal_weights(total_frames=20, start_frame=18, end_frame=19, pad_frames=4)
        assert w_end[18] == 1.0
        assert w_end[19] == 1.0
        assert w_end[17] < 1.0

    def test_camera_velocity_adjusts_feathering(self) -> None:
        planner = RepairPlanner()
        failure = CriticFailureObject(
            failure_type="hand_glitch",
            severity=DefectSeverity.SEVERE,
            frame_bounds=(10, 20),
            bounding_box=(0.4, 0.4, 0.6, 0.6),
        )
        report = CouncilEvaluationReport(status=CouncilStatus.REJECTED_FOR_REPAIR, failures=[failure])

        # Fast camera movement (5.0 m/s)
        shot_fast = ShotRequirement(shot_id="FAST_CAM", camera_velocity_mps=5.0)
        plan_fast = planner.plan_repair(report, shot_requirement=shot_fast)
        mask_fast = plan_fast.tasks[0].repair_boundary_mask
        assert mask_fast is not None
        # Base is 16.0, fast camera should expand feather
        assert mask_fast.feather_radius_px > 16.0

    def test_negligible_defect_ignored(self) -> None:
        planner = RepairPlanner()
        negligible_f = CriticFailureObject(
            failure_type="micro_flicker_negligible",
            severity=DefectSeverity.NEGLIGIBLE,
            frame_bounds=(5, 8),
            bounding_box=(0.1, 0.1, 0.2, 0.2),
        )
        report = CouncilEvaluationReport(
            status=CouncilStatus.ACCEPTED,
            failures=[negligible_f],
        )
        plan = planner.plan_repair(report)
        assert plan.total_tasks_count == 0
        assert plan.is_empty is True

    def test_executor_graceful_error_handling(self) -> None:
        executor = SurgicalRepairExecutor()
        # Create a task with invalid inpaint action but no mask
        bad_task = SurgicalRepairTask(
            task_id="BAD_TASK",
            action_type=RepairActionType.REGIONAL_TEMPORAL_INPAINTING,
            repair_boundary_mask=None,  # Missing required mask
        )
        res = executor.execute_task(bad_task)
        assert res.success_status is False
        assert res.repaired_asset_uri is None
        assert "Execution failed" in (res.error_message or "")

    def test_pydantic_serialization_roundtrip(self) -> None:
        mask = RepairBoundaryMask(
            bounding_box=(0.2, 0.2, 0.4, 0.4),
            frame_bounds=(10, 20),
            feather_radius_px=16.0,
            temporal_pad_frames=4,
        )
        task = SurgicalRepairTask(
            task_id="TASK_SERIALIZE",
            action_type=RepairActionType.REGIONAL_TEMPORAL_INPAINTING,
            repair_boundary_mask=mask,
            replacement_prompt="photorealistic hand",
        )
        plan = RepairPlan(
            plan_id="PLAN_SERIALIZE",
            original_shot_id="SHOT_SERIALIZE",
            ordered_tasks_list=[task],
            estimated_compute_tier=ComputeTier.TIER_2_REGIONAL_INPAINT,
        )
        json_data = plan.model_dump_json()
        reloaded = RepairPlan.model_validate_json(json_data)
        assert reloaded.plan_id == plan.plan_id
        assert len(reloaded.tasks) == 1
        assert reloaded.tasks[0].action_type == RepairActionType.REGIONAL_TEMPORAL_INPAINTING
        assert reloaded.tasks[0].repair_boundary_mask is not None
        assert reloaded.tasks[0].repair_boundary_mask.bounding_box == (0.2, 0.2, 0.4, 0.4)


# ===========================================================================
# 6. Critical Bug Regression & Deep Verification Tests
# ===========================================================================

class TestRepairRegressionAndRobustness:
    """Verifies edge cases, triage rules, and regressions found during review."""

    def test_solid_body_clipping_triaged_as_previs_not_audio(self) -> None:
        """Physical solid body clipping must route to SPATIAL_PREVIS_REBLOCK, never AUDIO."""
        planner = RepairPlanner()
        failure = CriticFailureObject(
            failure_type="solid_body_clipping",
            severity=DefectSeverity.SEVERE,
            hard_gate=HardGateType.PHYSICAL_TRAJECTORY,
            frame_bounds=(10, 50),
            bounding_box=(0.1, 0.1, 0.5, 0.5),
        )
        report = CouncilEvaluationReport(
            status=CouncilStatus.REJECTED_FOR_REPAIR,
            hard_gate_verdicts={HardGateType.PHYSICAL_TRAJECTORY: False},
            failures=[failure],
        )
        plan = planner.plan_repair(report)
        assert plan.total_tasks_count == 1
        assert plan.tasks[0].action_type == RepairActionType.SPATIAL_PREVIS_REBLOCK

    def test_mesh_clipping_triaged_as_previs(self) -> None:
        """Mesh/geometry clipping must route to SPATIAL_PREVIS_REBLOCK."""
        planner = RepairPlanner()
        failure = CriticFailureObject(
            failure_type="mesh_clipping_actor_collision",
            severity=DefectSeverity.SEVERE,
            frame_bounds=(20, 40),
            bounding_box=(0.2, 0.2, 0.7, 0.7),
        )
        report = CouncilEvaluationReport(
            status=CouncilStatus.REJECTED_FOR_REPAIR,
            failures=[failure],
        )
        plan = planner.plan_repair(report)
        assert plan.total_tasks_count == 1
        assert plan.tasks[0].action_type == RepairActionType.SPATIAL_PREVIS_REBLOCK

    def test_multiple_audio_defects_do_not_escalate_video_to_full_regen(self) -> None:
        """4 severe audio defects must dispatch audio tasks and NOT re-render video."""
        planner = RepairPlanner()
        failures = [
            CriticFailureObject(
                failure_type=f"dialogue_desync_segment_{i}",
                severity=DefectSeverity.SEVERE,
                frame_bounds=(i * 30, (i + 1) * 30),
                bounding_box=(0.0, 0.0, 1.0, 1.0),
                critic_type=CriticType.AUDIO,
            )
            for i in range(4)
        ]
        report = CouncilEvaluationReport(
            status=CouncilStatus.REJECTED_FOR_REPAIR,
            failures=failures,
        )
        plan = planner.plan_repair(report)
        assert plan.has_full_regen is False
        assert plan.total_tasks_count == 4
        assert all(t.is_audio for t in plan.tasks)
        assert plan.estimated_compute_tier == ComputeTier.TIER_1_AUDIO

    def test_escalation_to_full_regen_when_hard_gate_is_none(self) -> None:
        """Escalates to full regen when hard gates fail across >70% frames even if f.hard_gate is None."""
        planner = RepairPlanner()
        f1 = CriticFailureObject(
            failure_type="limb_distortion",
            hard_gate=None,  # Inferred via domain rules
            severity=DefectSeverity.SEVERE,
            frame_bounds=(0, 180),
        )
        f2 = CriticFailureObject(
            failure_type="face_identity_shift",
            hard_gate=None,  # Inferred via domain rules
            severity=DefectSeverity.SEVERE,
            frame_bounds=(100, 240),
        )
        report = CouncilEvaluationReport(
            status=CouncilStatus.REJECTED_FOR_REPAIR,
            hard_gate_verdicts={
                HardGateType.ANATOMICAL_INTEGRITY: False,
                HardGateType.CHARACTER_IDENTITY: False,
            },
            failures=[f1, f2],
        )
        shot_req = ShotRequirement(shot_id="SHOT_COVERAGE", target_duration=8.0)  # 240 frames
        plan = planner.plan_repair(report, shot_requirement=shot_req)
        assert plan.has_full_regen is True
        assert plan.total_tasks_count == 1
        assert plan.estimated_compute_tier == ComputeTier.TIER_4_FULL_REGEN

    def test_no_mixed_plan_with_full_regen_and_inpainting(self) -> None:
        """When full regeneration is required, plan never contains redundant inpainting tasks."""
        planner = RepairPlanner()
        f_local = CriticFailureObject(
            failure_type="hand_glitch",
            severity=DefectSeverity.MODERATE,
            frame_bounds=(10, 20),
            bounding_box=(0.4, 0.4, 0.6, 0.6),
        )
        f_global = CriticFailureObject(
            failure_type="catastrophic_screen_melt",
            severity=DefectSeverity.FATAL,
            frame_bounds=(0, 60),
            bounding_box=(0.0, 0.0, 1.0, 1.0),
        )
        report = CouncilEvaluationReport(
            status=CouncilStatus.REJECTED_FOR_REPAIR,
            failures=[f_local, f_global],
        )
        plan = planner.plan_repair(report)
        assert plan.has_full_regen is True
        assert plan.total_tasks_count == 1
        assert plan.has_inpainting is False

    def test_deduplication_merges_protected_regions_and_takes_highest_severity_prompt(self) -> None:
        """Merging overlapping tasks combines protected regions and uses highest severity metadata."""
        planner = RepairPlanner()
        reg_face = ProtectedRegion(region_type=ProtectedRegionType.FACE, bounding_box=(0.1, 0.1, 0.2, 0.2))
        reg_prop = ProtectedRegion(region_type=ProtectedRegionType.OTHER, bounding_box=(0.8, 0.8, 0.9, 0.9))

        mask1 = RepairBoundaryMask(
            bounding_box=(0.4, 0.4, 0.6, 0.6),
            frame_bounds=(10, 30),
            feather_radius_px=8.0,
            temporal_pad_frames=2,
            protected_regions=[reg_face],
        )
        t1 = SurgicalRepairTask(
            task_id="TASK_T1",
            action_type=RepairActionType.REGIONAL_TEMPORAL_INPAINTING,
            target_defect_id="minor_digit_flicker",
            defect_severity=DefectSeverity.MODERATE,
            priority=2,
            repair_boundary_mask=mask1,
            replacement_prompt="minor hand touchup",
        )

        mask2 = RepairBoundaryMask(
            bounding_box=(0.45, 0.45, 0.65, 0.65),
            frame_bounds=(15, 35),
            feather_radius_px=24.0,
            temporal_pad_frames=6,
            protected_regions=[reg_prop],
        )
        t2 = SurgicalRepairTask(
            task_id="TASK_T2",
            action_type=RepairActionType.REGIONAL_TEMPORAL_INPAINTING,
            target_defect_id="extra_fingers_severe",
            defect_severity=DefectSeverity.SEVERE,
            priority=2,
            repair_boundary_mask=mask2,
            replacement_prompt="photorealistic anatomically correct hand with five fingers",
        )

        merged_tasks = planner._deduplicate_and_optimize_tasks([t1, t2])
        assert len(merged_tasks) == 1
        m_task = merged_tasks[0]

        # Must pick up SEVERE severity and t2 prompt
        assert m_task.defect_severity == DefectSeverity.SEVERE
        assert "photorealistic" in (m_task.replacement_prompt or "")

        # Mask must take max feather and pad
        m_mask = m_task.repair_boundary_mask
        assert m_mask is not None
        assert m_mask.feather_radius_px == 24.0
        assert m_mask.temporal_pad_frames == 6

        # Must combine both protected regions
        p_types = [p.region_type for p in m_mask.protected_regions]
        assert ProtectedRegionType.FACE in p_types
        assert ProtectedRegionType.OTHER in p_types

    def test_point_defect_expansion(self) -> None:
        """Point or zero-width defects expand to a valid non-zero bounding box."""
        engine = TemporalMaskEngine()
        expanded = engine.expand_bounding_box((0.5, 0.5, 0.5, 0.5), expansion_ratio=0.10)
        assert expanded[2] > expanded[0]
        assert expanded[3] > expanded[1]

        mask = engine.generate_spatial_mask(expanded, resolution=(100, 100), feather_radius_px=4.0)
        assert np.any(mask > 0.0)

    def test_protected_regions_accepts_strings_and_enums(self) -> None:
        """RepairBoundaryMask accepts string and enum items in protected_regions."""
        mask = RepairBoundaryMask(
            bounding_box=(0.2, 0.2, 0.8, 0.8),
            frame_bounds=(0, 10),
            protected_regions=["background", "face", ProtectedRegionType.CAMERA_MOTION],
        )
        assert len(mask.protected_regions) == 3
        types = [pr.region_type for pr in mask.protected_regions]
        assert ProtectedRegionType.BACKGROUND in types
        assert ProtectedRegionType.FACE in types
        assert ProtectedRegionType.CAMERA_MOTION in types

    def test_camera_motion_and_background_protected_regions_extracted(self) -> None:
        """Camera trajectory metadata and scene location background are extracted into protected regions."""
        planner = RepairPlanner()
        shot_req = ShotRequirement(
            shot_id="SHOT_CAM",
            camera_movement="dolly_in_rapid",
            camera_trajectory_path="trajectories/cam_001.fbx",
        )
        scene_st = SceneState(
            scene_id="SC_01",
            location="industrial_warehouse",
        )
        failure = CriticFailureObject(
            failure_type="hand_glitch",
            severity=DefectSeverity.SEVERE,
            frame_bounds=(10, 20),
            bounding_box=(0.4, 0.4, 0.6, 0.6),
        )
        protected = planner._extract_protected_regions(
            scene_state=scene_st,
            shot_requirement=shot_req,
            failures=[failure],
        )
        p_types = [p.region_type for p in protected]
        assert ProtectedRegionType.CAMERA_MOTION in p_types
        assert ProtectedRegionType.BACKGROUND in p_types

    def test_seam_metric_with_4d_video_frame_tensor(self) -> None:
        """compute_boundary_seam_metric evaluates 4D video tensors without crashing."""
        engine = TemporalMaskEngine()
        mask_3d = np.zeros((5, 100, 100), dtype=np.float32)
        # Create a feathered slice at peak frame 2
        mask_3d[2] = engine.generate_spatial_mask((0.2, 0.2, 0.8, 0.8), resolution=(100, 100), feather_radius_px=8.0)
        video_4d = np.random.rand(5, 100, 100, 3).astype(np.float32)

        metric = engine.compute_boundary_seam_metric(mask_3d, frame=video_4d)
        assert isinstance(metric, float)
        assert 0.0 <= metric <= 1.0

    def test_custom_renderer_backend_invoked_for_all_action_types(self) -> None:
        """Custom renderer backend is invoked for audio, previs, and full regen."""
        calls = []

        def tracking_backend(payload: dict) -> dict:
            action = payload.get("action")
            calls.append(action)
            return {"asset_uri": f"mock://custom_{action}.mp4", "metadata": {"handled": True}}

        executor = SurgicalRepairExecutor(custom_renderer_backend=tracking_backend)

        # Audio task
        t_audio = SurgicalRepairTask(
            task_id="AUD",
            action_type=RepairActionType.AUDIO_REMASTER_VOICE,
        )
        res_audio = executor.execute_task(t_audio)
        assert res_audio.success_status is True
        assert "mock://custom" in res_audio.repaired_asset_uri

        # Previs task
        t_previs = SurgicalRepairTask(
            task_id="PREV",
            action_type=RepairActionType.SPATIAL_PREVIS_REBLOCK,
        )
        res_previs = executor.execute_task(t_previs)
        assert res_previs.success_status is True

        # Full regen task
        t_regen = SurgicalRepairTask(
            task_id="REG",
            action_type=RepairActionType.FULL_SHOT_REGENERATION,
        )
        res_regen = executor.execute_task(t_regen)
        assert res_regen.success_status is True

        assert len(calls) == 3

    def test_execute_plan_with_auto_execute_fallback(self) -> None:
        """execute_plan automatically dispatches fallback when auto_execute_fallback=True."""
        def failing_inpaint_backend(payload: dict) -> dict:
            if payload.get("action") == "FULL_SHOT_REGENERATION":
                return {"asset_uri": "mock://full_regen_asset.mp4"}
            return {"boundary_seam_metric": 0.25, "asset_uri": "failed.mp4"}

        executor = SurgicalRepairExecutor(
            seam_metric_threshold=0.05,
            custom_renderer_backend=failing_inpaint_backend,
        )
        task = SurgicalRepairTask(
            task_id="TASK_FAIL",
            action_type=RepairActionType.REGIONAL_TEMPORAL_INPAINTING,
            repair_boundary_mask=RepairBoundaryMask(bounding_box=(0.1, 0.1, 0.5, 0.5)),
            fallback_strategy=RepairActionType.FULL_SHOT_REGENERATION,
        )
        plan = RepairPlan(
            plan_id="PLAN_FB",
            original_shot_id="SHOT_FB",
            ordered_tasks_list=[task],
        )
        results = executor.execute_plan(plan, base_asset_uri="asset://base.mp4", auto_execute_fallback=True)

        assert len(results) == 2
        # First task failed due to high seam
        assert results[0].success_status is False
        # Second task is the executed fallback (FULL_SHOT_REGENERATION)
        assert results[1].success_status is True
        assert results[1].task_id == "TASK_FAIL_FALLBACK"
        assert "full_regen" in results[1].repaired_asset_uri


# ===========================================================================
# 7. Entrypoint
# ===========================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])


