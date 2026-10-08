"""Project Aether Master Critic Council & Quality Gatekeeper.

Coordinates multi-critic verification, executes binary hard quality gates,
computes soft aesthetic scores, and synthesizes prioritized surgical repair action plans
for Project Aether v2 (Pillar 5 / WBS 1.5).
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from aether.council.critics import (
    AudioCritic,
    BaseCritic,
    ContinuityCritic,
    OllamaVisionAuditor,
    PerformanceCritic,
    PhysicsCritic,
    TemporalCritic,
    VisualCritic,
)
from aether.council.schemas import (
    CouncilEvaluationReport,
    CouncilStatus,
    CriticAuditResult,
    CriticFailureObject,
    CriticType,
    DefectSeverity,
    HardGateType,
    RepairActionDirective,
    RepairRecommendation,
)
from aether.compiler.schemas import ShotRequirement
from aether.state.graph import AetherWorldModel
from aether.state.schemas import SceneState


class CriticCouncil:
    """Master coordinator executing multi-critic inspection, binary hard gating, and repair planning."""

    ANATOMY_KEYWORDS: Tuple[str, ...] = (
        "limb", "arm", "leg", "hand", "finger", "digit", "toe", "foot", "feet",
        "anatomy", "anatomical", "face", "eye", "head", "neck", "joint", "fused",
        "proportion", "torso", "body", "deform", "uncanny", "polydactyly",
    )

    def __init__(
        self,
        visual_critic: Optional[VisualCritic] = None,
        temporal_critic: Optional[TemporalCritic] = None,
        continuity_critic: Optional[ContinuityCritic] = None,
        performance_critic: Optional[PerformanceCritic] = None,
        physics_critic: Optional[PhysicsCritic] = None,
        audio_critic: Optional[AudioCritic] = None,
        custom_critics: Optional[List[BaseCritic]] = None,
        soft_score_threshold: float = 7.0,
        ollama_client: Optional[Any] = None,
        use_ollama: bool = False,
    ) -> None:
        if ollama_client is None and (use_ollama or os.environ.get("LLM_PROVIDER") == "ollama"):
            from pipeline.ollama_client import OllamaClient
            ollama_client = OllamaClient()

        self.ollama_client = ollama_client
        if visual_critic is not None:
            self.visual_critic = visual_critic
            if ollama_client is not None and getattr(self.visual_critic, "ollama_client", None) is None:
                self.visual_critic.ollama_client = ollama_client
                if getattr(self.visual_critic, "vision_auditor", None) is None:
                    self.visual_critic.vision_auditor = OllamaVisionAuditor(client=ollama_client)
        else:
            self.visual_critic = VisualCritic(ollama_client=ollama_client)

        self.temporal_critic = temporal_critic or TemporalCritic()
        if getattr(self.visual_critic, "cv_analyzer", None) is None and getattr(self.temporal_critic, "cv_analyzer", None) is not None:
            self.visual_critic.cv_analyzer = self.temporal_critic.cv_analyzer
        self.continuity_critic = continuity_critic or ContinuityCritic()
        self.performance_critic = performance_critic or PerformanceCritic()
        self.physics_critic = physics_critic or PhysicsCritic()
        self.audio_critic = audio_critic or AudioCritic()
        self.custom_critics = custom_critics or []
        self.soft_score_threshold = soft_score_threshold

    def evaluate(
        self,
        candidate_data: Union[Dict[str, Any], Any],
        scene_state: Optional[Union[SceneState, AetherWorldModel]] = None,
        shot_requirement: Optional[ShotRequirement] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> CouncilEvaluationReport:
        """Executes full Critic Council audit against candidate video generation."""
        cdata = candidate_data if isinstance(candidate_data, dict) else getattr(candidate_data, "__dict__", {})
        ctx = dict(context or {})

        # Extract active SceneState if AetherWorldModel provided
        active_state: Optional[SceneState] = None
        if isinstance(scene_state, AetherWorldModel):
            active_state = scene_state.active_state
        elif isinstance(scene_state, SceneState):
            active_state = scene_state
        elif "scene_state" in ctx and isinstance(ctx["scene_state"], SceneState):
            active_state = ctx["scene_state"]
        elif "scene_state" in cdata and isinstance(cdata["scene_state"], SceneState):
            active_state = cdata["scene_state"]

        # Shot ID identification
        shot_id = "SHOT_UNSPECIFIED"
        if shot_requirement and shot_requirement.shot_id:
            shot_id = shot_requirement.shot_id
        elif "shot_id" in cdata:
            shot_id = str(cdata["shot_id"])
        elif "id" in cdata:
            shot_id = str(cdata["id"])

        # -------------------------------------------------------------------
        # 1. Execute All Specialized Critics
        # -------------------------------------------------------------------
        audit_results: Dict[CriticType, CriticAuditResult] = {}
        all_failures: List[CriticFailureObject] = []

        # Visual Critic
        vis_res = self.visual_critic.audit(cdata, active_state, shot_requirement, ctx)
        audit_results[CriticType.VISUAL] = vis_res
        all_failures.extend(vis_res.failures)

        # Temporal Critic
        temp_res = self.temporal_critic.audit(cdata, active_state, shot_requirement, ctx)
        audit_results[CriticType.TEMPORAL] = temp_res
        all_failures.extend(temp_res.failures)

        # Continuity Critic
        cont_res = self.continuity_critic.audit(cdata, active_state, shot_requirement, ctx)
        audit_results[CriticType.CONTINUITY] = cont_res
        all_failures.extend(cont_res.failures)

        # Performance Critic
        perf_res = self.performance_critic.audit(cdata, active_state, shot_requirement, ctx)
        audit_results[CriticType.PERFORMANCE] = perf_res
        all_failures.extend(perf_res.failures)

        # Physics Critic
        phys_res = self.physics_critic.audit(cdata, active_state, shot_requirement, ctx)
        audit_results[CriticType.PHYSICS] = phys_res
        all_failures.extend(phys_res.failures)

        # Audio Critic
        audio_res = self.audio_critic.audit(cdata, active_state, shot_requirement, ctx)
        audit_results[CriticType.AUDIO] = audio_res
        all_failures.extend(audio_res.failures)

        # Custom Critics
        for custom in self.custom_critics:
            c_res = custom.audit(cdata, active_state, shot_requirement, ctx)
            audit_results[custom.critic_type] = c_res
            all_failures.extend(c_res.failures)

        # -------------------------------------------------------------------
        # 2. Enforce Binary Hard Gates
        # -------------------------------------------------------------------
        hard_gate_verdicts: Dict[HardGateType, bool] = {
            HardGateType.ANATOMICAL_INTEGRITY: True,
            HardGateType.CHARACTER_IDENTITY: True,
            HardGateType.PROP_CONTINUITY: True,
            HardGateType.LIP_SYNC_ALIGNMENT: True,
            HardGateType.PHYSICAL_TRAJECTORY: True,
        }

        # Merge verdicts directly emitted from individual critics
        for audit in audit_results.values():
            for gate, verdict in audit.hard_gate_verdicts.items():
                if not verdict:
                    hard_gate_verdicts[gate] = False

        # Fail hard gate if any FATAL or SEVERE failure matches domain
        for f in all_failures:
            if f.is_hard_gate_breaker:
                if f.hard_gate is not None:
                    hard_gate_verdicts[f.hard_gate] = False

                ft = f.failure_type.lower()
                # 1. Anatomical Integrity
                if any(k in ft for k in self.ANATOMY_KEYWORDS):
                    hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] = False

                # 2. Character Identity (including wardrobe & injury continuity)
                if any(k in ft for k in ("identity", "face_drift", "actor", "wardrobe", "injury", "wound", "scar")):
                    hard_gate_verdicts[HardGateType.CHARACTER_IDENTITY] = False

                # 3. Prop Continuity
                if any(k in ft for k in ("prop", "handoff", "possession", "attachment")):
                    hard_gate_verdicts[HardGateType.PROP_CONTINUITY] = False

                # 4. Lip-Sync Alignment
                if any(k in ft for k in ("lip_sync", "phonem", "viseme", "sync_offset", "speech", "mouth")):
                    hard_gate_verdicts[HardGateType.LIP_SYNC_ALIGNMENT] = False

                # 5. Physical Trajectory
                if any(k in ft for k in ("gravity", "trajectory", "clipping", "solid_body", "acceleration", "motion_spike")):
                    hard_gate_verdicts[HardGateType.PHYSICAL_TRAJECTORY] = False

                # Fallback attribution for unmapped custom defect types with SEVERE / FATAL severity
                if f.hard_gate is None:
                    if f.critic_type == CriticType.VISUAL:
                        hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] = False
                    elif f.critic_type == CriticType.CONTINUITY:
                        hard_gate_verdicts[HardGateType.CHARACTER_IDENTITY] = False
                    elif f.critic_type in (CriticType.PERFORMANCE, CriticType.AUDIO):
                        hard_gate_verdicts[HardGateType.LIP_SYNC_ALIGNMENT] = False
                    elif f.critic_type == CriticType.PHYSICS:
                        hard_gate_verdicts[HardGateType.PHYSICAL_TRAJECTORY] = False
                    else:
                        hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] = False

        # Enforce that NO candidate with any hard-gate breaker defect can pass all hard gates
        has_breaker_defect = any(f.is_hard_gate_breaker for f in all_failures)
        all_hard_gates_passed = all(hard_gate_verdicts.values()) and (not has_breaker_defect)

        # -------------------------------------------------------------------
        # 3. Evaluate Soft Aesthetic Scores (Only when all Hard Gates pass)
        # -------------------------------------------------------------------
        soft_scores: Dict[str, float] = {}
        overall_score: float = 0.0

        if all_hard_gates_passed:
            # Derive soft aesthetic scores from telemetry and critic fidelity
            cinematography = float(cdata.get("cinematography_score", vis_res.score))
            atmosphere = float(cdata.get("atmosphere_score", max(0.0, 9.5 - 0.5 * vis_res.failure_count)))
            performance = float(cdata.get("performance_score", perf_res.score))
            pacing = float(cdata.get("pacing_score", temp_res.score))

            soft_scores = {
                "Cinematography": round(max(0.0, min(10.0, cinematography)), 2),
                "Atmosphere": round(max(0.0, min(10.0, atmosphere)), 2),
                "Performance": round(max(0.0, min(10.0, performance)), 2),
                "Pacing": round(max(0.0, min(10.0, pacing)), 2),
            }

            # Weighted aggregate aesthetic score
            overall_score = round(
                0.30 * soft_scores["Cinematography"]
                + 0.25 * soft_scores["Atmosphere"]
                + 0.25 * soft_scores["Performance"]
                + 0.20 * soft_scores["Pacing"],
                2,
            )
            status = (
                CouncilStatus.ACCEPTED
                if overall_score >= self.soft_score_threshold
                else CouncilStatus.REJECTED_FOR_REPAIR
            )
        else:
            # Hard Gates Failed: Soft scores are gated / rejected, overall score is zeroed
            raw_cinematography = float(cdata.get("cinematography_score", vis_res.score))
            raw_atmosphere = float(cdata.get("atmosphere_score", 9.0))
            raw_performance = float(cdata.get("performance_score", perf_res.score))
            raw_pacing = float(cdata.get("pacing_score", temp_res.score))

            ctx["unrated_potential_soft_scores"] = {
                "Cinematography": raw_cinematography,
                "Atmosphere": raw_atmosphere,
                "Performance": raw_performance,
                "Pacing": raw_pacing,
            }

            soft_scores = {
                "Cinematography": 0.0,
                "Atmosphere": 0.0,
                "Performance": 0.0,
                "Pacing": 0.0,
            }
            overall_score = 0.0
            status = CouncilStatus.REJECTED_FOR_REPAIR

        # -------------------------------------------------------------------
        # 4. Assemble Prioritized Repair Action Directives
        # -------------------------------------------------------------------
        prioritized_repair_plan: List[RepairActionDirective] = []

        # Sort failures by severity priority rank (1 = FATAL, 2 = SEVERE...), then start frame
        sorted_failures = sorted(all_failures, key=lambda f: (f.severity.rank, f.start_frame))

        for idx, failure in enumerate(sorted_failures, start=1):
            target = failure.target_entity_id or "scene_region"
            frames_str = f"frames {failure.frame_bounds[0]}-{failure.frame_bounds[1]}"
            rtype = failure.recommended_repair

            if rtype == RepairRecommendation.REGIONAL_INPAINTING:
                desc = (
                    f"Execute regional temporal inpainting on '{target}' across {frames_str} "
                    f"within spatial bbox {failure.bounding_box} to repair {failure.failure_type}"
                )
            elif rtype == RepairRecommendation.AUDIO_REMASTER:
                desc = (
                    f"Execute audio-only remaster & lip-sync alignment for '{target}' "
                    f"across {frames_str} without modifying visual frames"
                )
            elif rtype == RepairRecommendation.SPATIAL_PREVIS_RERUN:
                desc = (
                    f"Rerun 3D geometric previs blocking and physical motion trajectory simulation for '{target}'"
                )
            elif rtype == RepairRecommendation.FULL_REGEN:
                desc = (
                    f"Initiate full shot regeneration due to catastrophic {failure.severity.value} "
                    f"defect ({failure.failure_type}) on '{target}'"
                )
            else:
                desc = f"No repair intervention required for {failure.failure_type}"

            directive = RepairActionDirective(
                priority=idx,
                repair_type=rtype,
                target_entity_id=failure.target_entity_id,
                frame_bounds=failure.frame_bounds,
                bounding_box=failure.bounding_box,
                defect_type=failure.failure_type,
                severity=failure.severity,
                action_description=desc,
                parameters={
                    "observed_state": failure.observed_state,
                    "expected_state": failure.expected_state,
                    "confidence": failure.confidence,
                },
            )
            prioritized_repair_plan.append(directive)

        # -------------------------------------------------------------------
        # 5. Executive Summary Construction
        # -------------------------------------------------------------------
        failed_gates = [gate.value for gate, passed in hard_gate_verdicts.items() if not passed]
        if status == CouncilStatus.ACCEPTED:
            summary = (
                f"Shot '{shot_id}' ACCEPTED: All 5 binary hard gates PASSED. "
                f"Overall soft aesthetic score: {overall_score:.2f}/10.0 (Threshold: {self.soft_score_threshold:.1f})."
            )
        else:
            if failed_gates:
                summary = (
                    f"Shot '{shot_id}' REJECTED_FOR_REPAIR: Violated Hard Gates: {failed_gates}. "
                    f"{len(prioritized_repair_plan)} surgical repair directives assembled for downstream Repair Planner."
                )
            else:
                summary = (
                    f"Shot '{shot_id}' REJECTED_FOR_REPAIR: Hard gates passed but overall aesthetic score "
                    f"{overall_score:.2f}/10.0 fell below minimum threshold {self.soft_score_threshold:.1f}."
                )

        return CouncilEvaluationReport(
            hard_gate_verdicts=hard_gate_verdicts,
            all_hard_gates_passed=all_hard_gates_passed,
            soft_scores=soft_scores,
            overall_score=overall_score,
            status=status,
            audit_results=audit_results,
            failures=all_failures,
            prioritized_repair_plan=prioritized_repair_plan,
            shot_id=shot_id,
            summary=summary,
            metadata=ctx,
        )
