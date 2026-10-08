"""AetherBench Benchmark Runner & Validator Harness.

Provides scenario validation, multi-gate evaluation (Hard Gates + Soft Scoring),
synthetic defect auditing, surgical repair recommendations, and batch execution
across model candidates.
"""

from __future__ import annotations

import datetime
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field

from aether.bench.schemas import (
    AetherScenario,
    CandidateEvaluationInput,
    DefectAnnotation,
    GateEvaluationResult,
    GateStatus,
    HardGateType,
    RepairStrategy,
    ScenarioEvaluationReport,
    StressTestCategory,
)


class ValidationResult(BaseModel):
    """Result of static scenario semantic validation."""
    model_config = ConfigDict(extra="forbid")

    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ScenarioValidator:
    """Validates physical and logical feasibility of benchmark scenarios."""

    @staticmethod
    def validate(scenario: AetherScenario) -> ValidationResult:
        """Perform semantic validation on an AetherScenario."""
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Coordinate & Collision checks
        chars = scenario.characters
        for i in range(len(chars)):
            for j in range(i + 1, len(chars)):
                p1, p2 = chars[i].position, chars[j].position
                dist = math.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(p1, p2)))
                if dist < 0.05 and scenario.category != StressTestCategory.ANATOMICAL_STRESS:
                    errors.append(
                        f"Characters '{chars[i].id}' and '{chars[j].id}' have overlapping coordinates (dist={dist:.3f}m)"
                    )

        # 2. Camera trajectory sanity
        cam = scenario.camera
        p_start, p_end = cam.start_position, cam.end_position
        cam_dist = math.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(p_start, p_end)))
        if cam.velocity_mps > 0 and cam_dist < 0.01:
            warnings.append(
                f"Camera has velocity {cam.velocity_mps} m/s but start and end positions are nearly identical."
            )
        if cam.velocity_mps == 0 and cam_dist > 0.1:
            warnings.append(
                f"Camera moves {cam_dist:.2f}m between start and end, but velocity_mps is 0.0."
            )

        # 3. Prop handoff consistency
        hg = scenario.hard_gate_constraints
        if scenario.category == StressTestCategory.HAND_OBJECT_HANDOFF:
            if not hg.handoff_prop_id:
                errors.append("HAND_OBJECT_HANDOFF scenario must specify handoff_prop_id.")
            if not hg.handoff_source_character:
                errors.append("HAND_OBJECT_HANDOFF scenario must specify handoff_source_character.")
            if not hg.handoff_target_character:
                errors.append("HAND_OBJECT_HANDOFF scenario must specify handoff_target_character.")
            if len(chars) < 2:
                errors.append("HAND_OBJECT_HANDOFF scenario requires at least 2 characters.")

        if scenario.category == StressTestCategory.MULTI_CHARACTER_INTERACTION and len(chars) < 2:
            errors.append("MULTI_CHARACTER_INTERACTION scenario requires at least 2 characters.")

        if hg.handoff_prop_id:
            src_char = next((c for c in chars if c.id == hg.handoff_source_character), None)
            if src_char:
                has_prop = any(hg.handoff_prop_id in val for val in src_char.props.values())
                if not has_prop:
                    warnings.append(
                        f"Handoff source character '{src_char.id}' does not have prop '{hg.handoff_prop_id}' in props."
                    )
            if hg.handoff_window_start_sec is None or hg.handoff_window_end_sec is None:
                errors.append("Handoff prop specified but handoff window timestamps are missing.")

        # 4. Complexity level alignment
        comp_level = int(scenario.complexity_level)
        if len(chars) >= 2 and comp_level < 3:
            warnings.append(
                f"Scenario has {len(chars)} interacting characters but complexity level is {comp_level} (Level >= 3 recommended)."
            )

        if scenario.category == StressTestCategory.FLUID_COLLISION_PHYSICS and comp_level < 4:
            warnings.append(
                f"Fluid collision physics typically requires complexity Level 4 or 5, got Level {comp_level}."
            )

        return ValidationResult(is_valid=(len(errors) == 0), errors=errors, warnings=warnings)


class BenchmarkEvaluator:
    """Evaluates candidate execution results against scenario constraints and gates."""

    @staticmethod
    def evaluate(scenario: AetherScenario, candidate: CandidateEvaluationInput) -> ScenarioEvaluationReport:
        """Evaluate a model candidate's output against scenario constraints."""
        gate_results: Dict[str, GateEvaluationResult] = {}
        defects: List[DefectAnnotation] = list(candidate.synthetic_defects)
        recommended_repairs: List[RepairStrategy] = []

        hg_constraints = scenario.hard_gate_constraints
        temp_constraints = scenario.temporal_constraints
        soft_spec = scenario.soft_scoring_spec

        # 1. Gate: ANATOMICAL_INTEGRITY
        if hg_constraints.anatomical_integrity:
            threshold = 1.0 - hg_constraints.max_limb_deformation_tolerance
            score = candidate.anatomical_score
            has_defect = any(d.gate == HardGateType.ANATOMICAL_INTEGRITY for d in defects)
            passed_anatomy = (score >= threshold) and not has_defect

            gate_results[HardGateType.ANATOMICAL_INTEGRITY.value] = GateEvaluationResult(
                gate=HardGateType.ANATOMICAL_INTEGRITY,
                status=GateStatus.PASS if passed_anatomy else GateStatus.FAIL,
                score=score,
                threshold=threshold,
                message="Anatomical skeleton and limb fidelity maintained" if passed_anatomy else "Limb distortion or joint popping detected",
                defect_count=sum(1 for d in defects if d.gate == HardGateType.ANATOMICAL_INTEGRITY),
            )
            if not passed_anatomy:
                if score < 0.80:
                    recommended_repairs.append(RepairStrategy.SPATIAL_PREVIS_FALLBACK)
                else:
                    recommended_repairs.append(RepairStrategy.TEMPORAL_INPAINTING)

        # 2. Gate: CHARACTER_IDENTITY
        if hg_constraints.character_identity_preservation and scenario.characters:
            threshold = hg_constraints.min_face_embedding_cosine
            score = candidate.face_similarity_cosine
            has_defect = any(d.gate == HardGateType.CHARACTER_IDENTITY for d in defects)
            passed_id = (score >= threshold) and not has_defect

            gate_results[HardGateType.CHARACTER_IDENTITY.value] = GateEvaluationResult(
                gate=HardGateType.CHARACTER_IDENTITY,
                status=GateStatus.PASS if passed_id else GateStatus.FAIL,
                score=score,
                threshold=threshold,
                message="Character face identity and wardrobe preserved" if passed_id else "Face embedding drift or wardrobe mutation detected",
                defect_count=sum(1 for d in defects if d.gate == HardGateType.CHARACTER_IDENTITY),
            )
            if not passed_id:
                recommended_repairs.append(RepairStrategy.TEMPORAL_INPAINTING)

        # 3. Gate: PROP_CONTINUITY
        if hg_constraints.prop_continuity:
            has_defect = any(d.gate == HardGateType.PROP_CONTINUITY for d in defects)
            passed_prop = candidate.prop_handoff_success and not has_defect
            msg_ok = "Prop maintained physical continuity and transfer" if hg_constraints.handoff_prop_id else "Prop persistence and geometry preserved"
            msg_fail = "Prop dropped, vanished, or fused during handoff" if hg_constraints.handoff_prop_id else "Prop vanished, deformed, or mutated during scene"

            gate_results[HardGateType.PROP_CONTINUITY.value] = GateEvaluationResult(
                gate=HardGateType.PROP_CONTINUITY,
                status=GateStatus.PASS if passed_prop else GateStatus.FAIL,
                score=1.0 if passed_prop else 0.0,
                threshold=1.0,
                message=msg_ok if passed_prop else msg_fail,
                defect_count=sum(1 for d in defects if d.gate == HardGateType.PROP_CONTINUITY),
            )
            if not passed_prop:
                recommended_repairs.append(RepairStrategy.KEYFRAME_INTERPOLATION)

        # 4. Gate: LIP_SYNC_ALIGNMENT
        if hg_constraints.lip_sync_alignment:
            threshold = hg_constraints.max_phoneme_offset_ms
            score = abs(candidate.lip_sync_offset_ms)
            has_defect = any(d.gate == HardGateType.LIP_SYNC_ALIGNMENT for d in defects)
            passed_lipsync = (score <= threshold) and not has_defect

            gate_results[HardGateType.LIP_SYNC_ALIGNMENT.value] = GateEvaluationResult(
                gate=HardGateType.LIP_SYNC_ALIGNMENT,
                status=GateStatus.PASS if passed_lipsync else GateStatus.FAIL,
                score=score,
                threshold=threshold,
                message="Phoneme-to-viseme temporal offset within tolerance" if passed_lipsync else f"Lip sync offset {score:.1f}ms exceeds {threshold:.1f}ms threshold",
                defect_count=sum(1 for d in defects if d.gate == HardGateType.LIP_SYNC_ALIGNMENT),
            )
            if not passed_lipsync:
                recommended_repairs.append(RepairStrategy.AUDIO_ONLY_REMASTER)

        # Temporal Continuity Auditing
        flow_ok = candidate.optical_flow_jitter <= temp_constraints.max_optical_flow_jitter
        ssim_ok = candidate.min_observed_ssim >= temp_constraints.min_ssim_frame_to_frame
        flicker_ok = candidate.observed_flicker_ratio <= temp_constraints.max_flicker_ratio
        loa_ok = candidate.line_of_action_preserved or not temp_constraints.line_of_action_180_deg_enforced

        temporal_passed = flow_ok and ssim_ok and flicker_ok and loa_ok
        if not temporal_passed:
            if not flow_ok or not ssim_ok or not flicker_ok:
                recommended_repairs.append(RepairStrategy.TEMPORAL_INPAINTING)
            if not loa_ok:
                recommended_repairs.append(RepairStrategy.SPATIAL_PREVIS_FALLBACK)

        temporal_metrics = {
            "optical_flow_jitter": {
                "observed": candidate.optical_flow_jitter,
                "threshold": temp_constraints.max_optical_flow_jitter,
                "passed": flow_ok,
            },
            "min_ssim": {
                "observed": candidate.min_observed_ssim,
                "threshold": temp_constraints.min_ssim_frame_to_frame,
                "passed": ssim_ok,
            },
            "flicker_ratio": {
                "observed": candidate.observed_flicker_ratio,
                "threshold": temp_constraints.max_flicker_ratio,
                "passed": flicker_ok,
            },
            "line_of_action_180_deg": {
                "preserved": candidate.line_of_action_preserved,
                "enforced": temp_constraints.line_of_action_180_deg_enforced,
                "passed": loa_ok,
            },
            "passed": temporal_passed,
        }

        # Soft Aesthetic Scoring
        soft_scores = {
            "cinematography": candidate.soft_cinematography,
            "visual_aesthetic": candidate.soft_aesthetic,
            "narrative_pacing": candidate.soft_pacing,
        }
        aggregate_soft = (
            soft_spec.cinematography_weight * candidate.soft_cinematography
            + soft_spec.aesthetic_weight * candidate.soft_aesthetic
            + soft_spec.pacing_weight * candidate.soft_pacing
        )

        sub_fails = []
        if candidate.soft_cinematography < soft_spec.min_cinematography:
            sub_fails.append(f"cinematography ({candidate.soft_cinematography} < {soft_spec.min_cinematography})")
        if candidate.soft_aesthetic < soft_spec.min_visual_aesthetic:
            sub_fails.append(f"aesthetic ({candidate.soft_aesthetic} < {soft_spec.min_visual_aesthetic})")
        if candidate.soft_pacing < soft_spec.min_narrative_pacing:
            sub_fails.append(f"pacing ({candidate.soft_pacing} < {soft_spec.min_narrative_pacing})")

        agg_fail = aggregate_soft < soft_spec.min_aggregate_score
        soft_passed = (not agg_fail) and (len(sub_fails) == 0)

        # Overall Status
        hard_gates_passed = all(gr.status == GateStatus.PASS for gr in gate_results.values())
        overall_passed = hard_gates_passed and temporal_passed and soft_passed

        # Deduplicate recommended repairs
        deduped_repairs = list(dict.fromkeys(recommended_repairs))
        if not overall_passed and not deduped_repairs:
            deduped_repairs.append(scenario.expected_repair_strategy_on_failure or RepairStrategy.FULL_REGENERATION)

        summary_parts = []
        if overall_passed:
            summary_parts.append(
                f"PASS: Candidate passed all {len(gate_results)} hard gates and soft score ({aggregate_soft:.2f} >= {soft_spec.min_aggregate_score})."
            )
        else:
            failed_gates = [k for k, v in gate_results.items() if v.status == GateStatus.FAIL]
            if failed_gates:
                summary_parts.append(f"FAIL Hard Gates: {', '.join(failed_gates)}.")
            if not temporal_passed:
                temporal_fails = []
                if not flow_ok:
                    temporal_fails.append(
                        f"optical_flow ({candidate.optical_flow_jitter:.3f} > {temp_constraints.max_optical_flow_jitter:.3f})"
                    )
                if not ssim_ok:
                    temporal_fails.append(
                        f"ssim ({candidate.min_observed_ssim:.3f} < {temp_constraints.min_ssim_frame_to_frame:.3f})"
                    )
                if not flicker_ok:
                    temporal_fails.append(
                        f"flicker ({candidate.observed_flicker_ratio:.3f} > {temp_constraints.max_flicker_ratio:.3f})"
                    )
                if not loa_ok:
                    temporal_fails.append("180_deg_line_of_action")
                summary_parts.append(f"FAIL Temporal Continuity: {', '.join(temporal_fails)}.")
            if agg_fail:
                summary_parts.append(f"FAIL Soft Aggregate Score: {aggregate_soft:.2f} < {soft_spec.min_aggregate_score}.")
            if sub_fails:
                summary_parts.append(f"FAIL Soft Sub-criteria: {', '.join(sub_fails)}.")

        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return ScenarioEvaluationReport(
            scenario_id=scenario.id,
            model_id=candidate.model_id,
            candidate_id=candidate.candidate_id,
            passed=overall_passed,
            hard_gates_passed=hard_gates_passed,
            temporal_passed=temporal_passed,
            gate_results=gate_results,
            temporal_metrics=temporal_metrics,
            soft_scores=soft_scores,
            aggregate_soft_score=round(aggregate_soft, 2),
            defects=defects,
            recommended_repairs=deduped_repairs,
            execution_timestamp=now_str,
            summary=" ".join(summary_parts),
        )


class MockModelProvider:
    """Simulated video generation provider for benchmark harness calibration."""

    def __init__(
        self,
        model_id: str = "google_veo_3.1",
        base_latency_sec: float = 18.5,
        base_cost_usd: float = 0.45,
        default_fail_gates: Optional[List[HardGateType]] = None,
        soft_score_bias: float = 0.0,
        base_anatomical_score: float = 0.995,
        base_face_similarity: float = 0.95,
        base_cinematography: float = 9.2,
        base_aesthetic: float = 9.2,
        base_pacing: float = 9.2,
    ) -> None:
        self.model_id = model_id
        self.base_latency_sec = base_latency_sec
        self.base_cost_usd = base_cost_usd
        self.default_fail_gates = default_fail_gates or []
        self.soft_score_bias = soft_score_bias
        self.base_anatomical_score = base_anatomical_score
        self.base_face_similarity = base_face_similarity
        self.base_cinematography = base_cinematography
        self.base_aesthetic = base_aesthetic
        self.base_pacing = base_pacing

    def generate_candidate_input(
        self,
        scenario: AetherScenario,
        candidate_id: Optional[str] = None,
        inject_fail_gates: Optional[List[HardGateType]] = None,
    ) -> CandidateEvaluationInput:
        """Create a candidate evaluation payload for the scenario."""
        cand_id = candidate_id or f"{self.model_id}-cand-{scenario.id}"
        fails = set(self.default_fail_gates + (inject_fail_gates or []))

        defects: List[DefectAnnotation] = []

        # Anatomical
        if HardGateType.ANATOMICAL_INTEGRITY in fails:
            anat_score = 0.72
            defects.append(
                DefectAnnotation(
                    defect_id=f"DEF-ANAT-{scenario.id}",
                    gate=HardGateType.ANATOMICAL_INTEGRITY,
                    description="Finger fusion and elbow hyper-extension detected in frames 30-45",
                    start_frame=30,
                    end_frame=45,
                    bounding_box=(0.4, 0.3, 0.6, 0.7),
                    severity="FATAL",
                )
            )
        else:
            anat_score = self.base_anatomical_score

        # Identity
        if HardGateType.CHARACTER_IDENTITY in fails:
            face_sim = 0.75
            defects.append(
                DefectAnnotation(
                    defect_id=f"DEF-IDENT-{scenario.id}",
                    gate=HardGateType.CHARACTER_IDENTITY,
                    description="Facial feature drift; jaw structure morphs across cut",
                    start_frame=60,
                    end_frame=90,
                    bounding_box=(0.35, 0.2, 0.55, 0.45),
                    severity="FATAL",
                )
            )
        else:
            face_sim = self.base_face_similarity

        # Prop Handoff
        prop_success = HardGateType.PROP_CONTINUITY not in fails
        if not prop_success:
            defects.append(
                DefectAnnotation(
                    defect_id=f"DEF-PROP-{scenario.id}",
                    gate=HardGateType.PROP_CONTINUITY,
                    description="Vial vanishes from character hand before recipient grips",
                    start_frame=40,
                    end_frame=55,
                    bounding_box=(0.45, 0.4, 0.65, 0.6),
                    severity="FATAL",
                )
            )

        # Lip Sync
        lip_offset = 85.0 if HardGateType.LIP_SYNC_ALIGNMENT in fails else 15.0
        if HardGateType.LIP_SYNC_ALIGNMENT in fails:
            defects.append(
                DefectAnnotation(
                    defect_id=f"DEF-LIP-{scenario.id}",
                    gate=HardGateType.LIP_SYNC_ALIGNMENT,
                    description=f"Audio-video phoneme offset ({lip_offset:.1f}ms) desynchronization detected",
                    start_frame=15,
                    end_frame=45,
                    timestamp_sec=1.0,
                    bounding_box=(0.42, 0.35, 0.58, 0.50),
                    severity="FATAL",
                )
            )

        cinematography = max(0.0, min(10.0, self.base_cinematography + self.soft_score_bias))
        aesthetic = max(0.0, min(10.0, self.base_aesthetic + self.soft_score_bias))
        pacing = max(0.0, min(10.0, self.base_pacing + self.soft_score_bias))

        return CandidateEvaluationInput(
            scenario_id=scenario.id,
            model_id=self.model_id,
            candidate_id=cand_id,
            generation_latency_sec=round(self.base_latency_sec + scenario.duration_seconds * 1.5, 2),
            estimated_cost_usd=round(self.base_cost_usd + scenario.duration_seconds * 0.05, 3),
            anatomical_score=anat_score,
            face_similarity_cosine=face_sim,
            prop_handoff_success=prop_success,
            lip_sync_offset_ms=lip_offset,
            optical_flow_jitter=0.03,
            min_observed_ssim=0.91,
            observed_flicker_ratio=0.02,
            line_of_action_preserved=True,
            soft_cinematography=cinematography,
            soft_aesthetic=aesthetic,
            soft_pacing=pacing,
            synthetic_defects=defects,
            raw_frames_count=int(scenario.duration_seconds * scenario.target_fps),
        )


class BenchmarkSuiteReport(BaseModel):
    """Aggregate evaluation report for a suite execution."""
    model_config = ConfigDict(extra="forbid")

    total_scenarios: int
    passed_count: int
    failed_count: int
    pass_rate: float
    category_metrics: Dict[str, Dict[str, Any]]
    hard_gate_metrics: Dict[str, Dict[str, Any]]
    average_aggregate_soft_score: float
    average_latency_sec: float
    total_estimated_cost_usd: float
    reports: List[ScenarioEvaluationReport]

    def to_json(self, indent: int = 2) -> str:
        """Serialize report to JSON string."""
        return self.model_dump_json(indent=indent)

    def export_json(self, path: Union[str, Path]) -> None:
        """Export report to a JSON file."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(self.to_json())


class BenchmarkRunner:
    """Orchestrates single-scenario or batch suite benchmark runs."""

    def __init__(self, evaluator: Optional[BenchmarkEvaluator] = None) -> None:
        self.evaluator = evaluator or BenchmarkEvaluator()

    def run_scenario(
        self,
        scenario: AetherScenario,
        candidate_input: CandidateEvaluationInput,
    ) -> ScenarioEvaluationReport:
        """Run evaluation for a single scenario and candidate."""
        return self.evaluator.evaluate(scenario, candidate_input)

    def run_scenario_with_provider(
        self,
        scenario: AetherScenario,
        provider: MockModelProvider,
        inject_fail_gates: Optional[List[HardGateType]] = None,
    ) -> ScenarioEvaluationReport:
        """Generate candidate from provider and evaluate."""
        cand_input = provider.generate_candidate_input(scenario, inject_fail_gates=inject_fail_gates)
        return self.evaluator.evaluate(scenario, cand_input)

    def run_suite(
        self,
        scenarios: List[AetherScenario],
        provider: MockModelProvider,
        category_fail_injections: Optional[Dict[StressTestCategory, List[HardGateType]]] = None,
    ) -> BenchmarkSuiteReport:
        """Execute benchmark evaluation across a list of scenarios."""
        reports: List[ScenarioEvaluationReport] = []
        total_latencies: float = 0.0
        total_costs: float = 0.0
        total_soft_scores: float = 0.0

        cat_stats: Dict[str, Dict[str, int]] = {}
        gate_stats: Dict[str, Dict[str, int]] = {}

        for s in scenarios:
            injected = None
            if category_fail_injections and s.category in category_fail_injections:
                injected = category_fail_injections[s.category]

            cand_input = provider.generate_candidate_input(s, inject_fail_gates=injected)
            report = self.evaluator.evaluate(s, cand_input)
            reports.append(report)

            total_latencies += cand_input.generation_latency_sec
            total_costs += cand_input.estimated_cost_usd
            total_soft_scores += report.aggregate_soft_score

            # Category tracking
            c_name = s.category.value
            if c_name not in cat_stats:
                cat_stats[c_name] = {"total": 0, "passed": 0, "failed": 0}
            cat_stats[c_name]["total"] += 1
            if report.passed:
                cat_stats[c_name]["passed"] += 1
            else:
                cat_stats[c_name]["failed"] += 1

            # Gate tracking
            for g_name, g_res in report.gate_results.items():
                if g_name not in gate_stats:
                    gate_stats[g_name] = {"evaluated": 0, "passed": 0, "failed": 0}
                gate_stats[g_name]["evaluated"] += 1
                if g_res.status == GateStatus.PASS:
                    gate_stats[g_name]["passed"] += 1
                else:
                    gate_stats[g_name]["failed"] += 1

        total = len(scenarios)
        passed = sum(1 for r in reports if r.passed)
        failed = total - passed
        pass_rate = round(passed / total, 3) if total > 0 else 0.0

        cat_metrics: Dict[str, Dict[str, Any]] = {}
        for c_name, st in cat_stats.items():
            tot = st["total"]
            pass_rt = round(st["passed"] / tot, 3) if tot > 0 else 0.0
            cat_metrics[c_name] = {**st, "pass_rate": pass_rt}

        gate_metrics: Dict[str, Dict[str, Any]] = {}
        for g_name, st in gate_stats.items():
            tot = st["evaluated"]
            pass_rt = round(st["passed"] / tot, 3) if tot > 0 else 0.0
            gate_metrics[g_name] = {**st, "pass_rate": pass_rt}

        avg_soft = round(total_soft_scores / total, 2) if total > 0 else 0.0
        avg_lat = round(total_latencies / total, 2) if total > 0 else 0.0

        return BenchmarkSuiteReport(
            total_scenarios=total,
            passed_count=passed,
            failed_count=failed,
            pass_rate=pass_rate,
            category_metrics=cat_metrics,
            hard_gate_metrics=gate_metrics,
            average_aggregate_soft_score=avg_soft,
            average_latency_sec=avg_lat,
            total_estimated_cost_usd=round(total_costs, 3),
            reports=reports,
        )
