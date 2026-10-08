"""Project Aether Autonomous Director Orchestrator.

The master end-to-end virtual studio director unifying all 6 pillars of Project Aether v2:
1. Narrative World Modeling (Pillar 2 / WBS 1.3)
2. Complexity Planning & Shot Compilation (Pillar 3 & 4 / WBS 1.4)
3. Candidate Generation with Speculative Draft Gating (Efficiency Stack / WBS 1.4 & 1.10)
4. Critic Council Binary Hard Quality Gating (Pillar 5 / WBS 1.5)
5. Surgical Repair Engine (Pillar 6 / WBS 1.7)
6. Multi-Shot Continuity Auditing (Pillar 2 & 5 / WBS 1.3)
7. Dream-RSI Teacher Engine Episode Logging (Phase 9 / WBS 1.10)
"""

from __future__ import annotations

import copy
import logging
import os
from pathlib import Path
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import uuid

logger = logging.getLogger(__name__)

from aether.compiler.complexity import ComplexityPlanner
from aether.compiler.compiler import ShotCompiler
from aether.compiler.schemas import (
    AudioRequirement,
    ComplexityLevel,
    ComplexityPlan,
    CompiledModelPayload,
    ProviderTarget,
    ShotRequirement,
    SpatialRepresentationPackage,
)
from aether.council.council import CriticCouncil
from aether.council.schemas import (
    CouncilEvaluationReport,
    CouncilStatus,
    CriticFailureObject,
    DefectSeverity,
    HardGateType,
)
from aether.director.schemas import (
    DirectorProductionBrief,
    DirectorProductionStatus,
    FilmScene,
    MasteredFilm,
    ProductionState,
    ShotTimelineRecord,
)
from aether.repair.executor import SurgicalRepairExecutor
from aether.repair.planner import RepairPlanner
from aether.repair.schemas import (
    RepairActionType,
    RepairExecutionResult,
    RepairPlan,
)
from aether.state.continuity import ContinuityAuditor, ContinuityAuditResult
from aether.state.graph import AetherWorldModel
from aether.state.schemas import (
    ActionType,
    CameraState,
    CharacterState,
    EnvironmentState,
    HandAttachment,
    PropState,
    SceneAction,
    SceneSnapshot,
    SceneState,
    WardrobeItemState,
)
from aether.teacher.replay_simulator import ReplaySimulatorPool
from aether.teacher.schemas import DiscoveryTraceTree, ExplorationPolicy
from aether.teacher.trace_logger import TraceLogger


class AetherDirector:
    """Master end-to-end virtual studio director unifying all 6 architectural pillars."""

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        world_model: Optional[AetherWorldModel] = None,
        complexity_planner: Optional[ComplexityPlanner] = None,
        shot_compiler: Optional[ShotCompiler] = None,
        critic_council: Optional[CriticCouncil] = None,
        repair_planner: Optional[RepairPlanner] = None,
        repair_executor: Optional[SurgicalRepairExecutor] = None,
        continuity_auditor: Optional[ContinuityAuditor] = None,
        trace_logger: Optional[TraceLogger] = None,
        replay_pool: Optional[ReplaySimulatorPool] = None,
        active_policy: Optional[ExplorationPolicy] = None,
        candidate_generator: Optional[Callable[..., Any]] = None,
        status_callback: Optional[Callable[[DirectorProductionStatus], None]] = None,
        llm_client: Optional[Any] = None,
    ) -> None:
        self.output_dir = Path(output_dir) if output_dir else Path("./output/aether_films")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.renders_dir = self.output_dir / "renders"
        self.renders_dir.mkdir(parents=True, exist_ok=True)
        self.traces_dir = self.output_dir / "traces"
        self.traces_dir.mkdir(parents=True, exist_ok=True)

        self.active_policy = active_policy
        self._initial_world_model = world_model
        self.world_model = world_model or AetherWorldModel()
        self.complexity_planner = complexity_planner or ComplexityPlanner(
            active_policy=active_policy,
            llm_client=llm_client,
        )
        self.shot_compiler = shot_compiler or ShotCompiler(
            planner=self.complexity_planner,
            active_policy=active_policy,
        )
        self.critic_council = critic_council or CriticCouncil()
        self.repair_planner = repair_planner or RepairPlanner(active_policy=active_policy)
        self.repair_executor = repair_executor or SurgicalRepairExecutor()
        self.continuity_auditor = continuity_auditor or ContinuityAuditor()
        self.trace_logger = trace_logger or TraceLogger(storage_dir=self.traces_dir)
        self.replay_pool = replay_pool or ReplaySimulatorPool()

        self.candidate_generator = candidate_generator
        self.status_callback = status_callback
        self.llm_client = llm_client
        self.status = DirectorProductionStatus()

    def _check_budget(self, budget_limit: float, context: str) -> None:
        """Enforces hard budget limit across all stages of production."""
        if self.status.estimated_total_cost > budget_limit:
            self._update_status(
                ProductionState.FAILED,
                f"Production budget limit ${budget_limit:.2f} exceeded during {context} "
                f"(accrued: ${self.status.estimated_total_cost:.4f})",
            )
            raise RuntimeError(
                f"Production budget limit ${budget_limit:.2f} exceeded during {context} "
                f"(accrued: ${self.status.estimated_total_cost:.4f})"
            )

    def produce(
        self,
        brief: Union[DirectorProductionBrief, str, Dict[str, Any]],
        dry_run: bool = False,
        run_now: bool = True,
    ) -> MasteredFilm:
        """Executes full autonomous prompt-to-mastered-film virtual studio production."""
        start_wall_clock = time.time()
        film_id = f"FILM_{int(start_wall_clock)}_{uuid.uuid4().hex[:6].upper()}"

        # -------------------------------------------------------------------
        # Step 0: Ingest & Normalize Production Brief
        # -------------------------------------------------------------------
        normalized_brief = self._normalize_brief(brief)
        scenes = self._resolve_scenes(normalized_brief)
        total_shots = sum(len(sc.shot_list_requirements) for sc in scenes)

        self.status = DirectorProductionStatus(
            state=ProductionState.INITIALIZING,
            total_shots=total_shots,
            current_shot_index=0,
            shots_passed_count=0,
            repairs_performed_count=0,
            estimated_total_cost=0.0,
            elapsed_time=0.0,
            message=f"Production initialized for '{normalized_brief.title}'",
        )
        self._notify_status()

        # -------------------------------------------------------------------
        # Step 1: Establish Narrative World Model
        # -------------------------------------------------------------------
        self._update_status(
            ProductionState.WORLD_SETUP,
            f"Establishing narrative structure and persistent world state for '{normalized_brief.title}'",
        )
        self._setup_world_model(scenes)

        timeline_ledger: List[Dict[str, Any]] = []
        trace_episode_ids: List[str] = []
        transition_audit_records: List[Dict[str, Any]] = []
        prev_shot_snapshot: Optional[SceneSnapshot] = None
        global_shot_index = 0

        # -------------------------------------------------------------------
        # Staged Run Check: If run_now is False, stage plan and return
        # -------------------------------------------------------------------
        if not run_now:
            self._update_status(
                ProductionState.COMPILING_SHOTS,
                f"Staging production plan and world model for '{normalized_brief.title}' (run_now=False)",
            )
            for scene_idx, scene in enumerate(scenes):
                self.status.current_scene_id = scene.scene_id
                if scene_idx > 0:
                    self.world_model.active_state.scene_id = scene.scene_id
                    if scene.location:
                        self.world_model.active_state.location = scene.location
                    for cdata in scene.characters:
                        char = CharacterState(**cdata) if isinstance(cdata, dict) else cdata
                        if char.character_id not in self.world_model.active_state.character_roster:
                            self.world_model.active_state.character_roster[char.character_id] = char
                    for pdata in scene.props:
                        prop = PropState(**pdata) if isinstance(pdata, dict) else pdata
                        if prop.prop_id not in self.world_model.active_state.prop_roster:
                            self.world_model.active_state.prop_roster[prop.prop_id] = prop

                for shot_req in scene.shot_list_requirements:
                    global_shot_index += 1
                    active_scene_state = self.world_model.active_state
                    comp_plan = self.complexity_planner.plan(
                        scene_state=active_scene_state,
                        shot_requirement=shot_req,
                    )
                    pref_provider = None
                    if normalized_brief.target_models:
                        rec_val = comp_plan.recommended_provider.value
                        if rec_val in normalized_brief.target_models:
                            pref_provider = rec_val
                        else:
                            pref_provider = normalized_brief.target_models[0]
                    else:
                        pref_provider = comp_plan.recommended_provider.value

                    compiled_payload = self.shot_compiler.compile_auto(
                        scene_state=active_scene_state,
                        shot_requirement=shot_req,
                        complexity_level=comp_plan.complexity_level,
                        preferred_provider=pref_provider,
                    )
                    shot_snapshot = self.world_model.freeze_shot(
                        shot_id=shot_req.shot_id,
                        metadata={"scene_id": scene.scene_id, "duration": shot_req.target_duration},
                    )
                    if prev_shot_snapshot is not None:
                        audit_res = self.continuity_auditor.audit_transition(
                            shot_a=prev_shot_snapshot.state,
                            shot_b=shot_snapshot.state,
                            elapsed_seconds=shot_req.target_duration,
                            metadata={"shot_a_id": prev_shot_snapshot.shot_id, "shot_b_id": shot_snapshot.shot_id},
                        )
                        transition_audit_records.append({
                            "shot_a_id": prev_shot_snapshot.shot_id,
                            "shot_b_id": shot_snapshot.shot_id,
                            "is_valid": audit_res.is_valid,
                            "violations": [v.model_dump(mode="json") for v in audit_res.violations],
                        })
                    prev_shot_snapshot = shot_snapshot

                    record = ShotTimelineRecord(
                        shot_id=shot_req.shot_id,
                        scene_id=scene.scene_id,
                        sequence_index=global_shot_index - 1,
                        duration=shot_req.target_duration,
                        provider=compiled_payload.provider_target.value,
                        complexity_level=comp_plan.complexity_level.value,
                        video_uri=f"asset://staged/{shot_req.shot_id}.mp4",
                        audio_uri=f"asset://staged/{shot_req.shot_id}_audio.wav",
                        council_score=0.0,
                        passed_hard_gates=False,
                        repairs_count=0,
                        cost=0.0,
                        speculative_draft_passed=False,
                        trace_episode_id=None,
                        continuity_passed=True,
                        metadata={"status": "staged"},
                    )
                    timeline_ledger.append(record.model_dump(mode="json"))

            total_duration = sum(item.get("duration", 0.0) for item in timeline_ledger)
            return MasteredFilm(
                film_id=film_id,
                title=normalized_brief.title,
                scenes_count=len(scenes),
                total_shots_count=len(timeline_ledger),
                duration_seconds=total_duration,
                master_video_artifact_uri=f"{self.output_dir}/{film_id}_staged.mp4",
                master_audio_artifact_uri=f"{self.output_dir}/{film_id}_staged.wav",
                total_production_cost=0.0,
                production_timeline_ledger=timeline_ledger,
                dream_rsi_trace_episode_id=f"staged_{film_id}",
                trace_episode_ids=[],
                status="STAGED",
                created_at=time.time(),
                metadata={"staged": True},
            )

        # -------------------------------------------------------------------
        # Iterate Through Scenes and Shots
        # -------------------------------------------------------------------
        for scene_idx, scene in enumerate(scenes):
            self.status.current_scene_id = scene.scene_id

            # Apply scene-level transitions if changing scenes
            if scene_idx > 0:
                self.world_model.active_state.scene_id = scene.scene_id
                if scene.location:
                    self.world_model.active_state.location = scene.location
                if scene.environment_parameters:
                    self.world_model.apply_action(
                        SceneAction(
                            action_id=f"act_env_{scene.scene_id}_{scene_idx}",
                            action_type=ActionType.ENVIRONMENT_CHANGE,
                            elapsed_seconds=1.0,
                            metadata=scene.environment_parameters,
                        )
                    )
                for cdata in scene.characters:
                    char = CharacterState(**cdata) if isinstance(cdata, dict) else cdata
                    if char.character_id not in self.world_model.active_state.character_roster:
                        self.world_model.active_state.character_roster[char.character_id] = char
                for pdata in scene.props:
                    prop = PropState(**pdata) if isinstance(pdata, dict) else pdata
                    if prop.prop_id not in self.world_model.active_state.prop_roster:
                        self.world_model.active_state.prop_roster[prop.prop_id] = prop

            for shot_req in scene.shot_list_requirements:
                global_shot_index += 1
                self.status.current_shot_index = global_shot_index
                self.status.current_shot_id = shot_req.shot_id

                # Check budget limit before starting shot compute
                self._check_budget(normalized_brief.budget_limit, f"pre-shot check for {shot_req.shot_id}")

                # -----------------------------------------------------------
                # Step 2: Complexity Planning & Shot Compilation
                # -----------------------------------------------------------
                self._update_status(
                    ProductionState.COMPILING_SHOTS,
                    f"Compiling shot {global_shot_index}/{total_shots}: {shot_req.shot_id}",
                )

                active_scene_state = self.world_model.active_state
                comp_plan = self.complexity_planner.plan(
                    scene_state=active_scene_state,
                    shot_requirement=shot_req,
                )

                # Determine preferred provider from plan and allowed brief models
                pref_provider = None
                if normalized_brief.target_models:
                    rec_val = comp_plan.recommended_provider.value
                    if rec_val in normalized_brief.target_models:
                        pref_provider = rec_val
                    else:
                        pref_provider = normalized_brief.target_models[0]
                else:
                    pref_provider = comp_plan.recommended_provider.value

                compiled_payload = self.shot_compiler.compile_auto(
                    scene_state=active_scene_state,
                    shot_requirement=shot_req,
                    complexity_level=comp_plan.complexity_level,
                    preferred_provider=pref_provider,
                )

                # -----------------------------------------------------------
                # Step 3 & 4: Candidate Generation & Critic Council Audit
                # -----------------------------------------------------------
                self._update_status(
                    ProductionState.RENDERING_AND_CRITIQUING,
                    f"Rendering and auditing shot {shot_req.shot_id} (Complexity L{comp_plan.complexity_level.value})",
                )

                shot_cost = 0.0
                shot_latency = 0.0
                repairs_count = 0
                draft_passed = True
                final_repair_plan: Optional[RepairPlan] = None

                if dry_run:
                    # Dry-run execution: zero external cost, synthetic passing report
                    candidate_data = self._generate_dry_run_candidate(shot_req, compiled_payload)
                    council_report = self._evaluate_dry_run_report(shot_req)
                    shot_cost = 0.0
                    shot_latency = 0.05
                else:
                    # Speculative 480p draft gating (if enabled in brief or shot)
                    enable_spec = normalized_brief.speculative_draft or shot_req.enable_speculative_draft
                    if enable_spec:
                        draft_candidate, draft_cost = self._generate_candidate_asset(
                            shot_req=shot_req,
                            compiled_payload=compiled_payload,
                            is_speculative_draft=True,
                        )
                        shot_cost += draft_cost
                        self.status.estimated_total_cost += draft_cost
                        self._check_budget(normalized_brief.budget_limit, f"speculative draft generation for {shot_req.shot_id}")

                        # Audit 480p draft against hard gates
                        draft_report = self.critic_council.evaluate(
                            candidate_data=draft_candidate,
                            scene_state=self.world_model.active_state,
                            shot_requirement=shot_req,
                        )
                        shot_cost += 0.015  # VLM token audit cost
                        self.status.estimated_total_cost += 0.015
                        self._check_budget(normalized_brief.budget_limit, f"speculative draft audit for {shot_req.shot_id}")

                        if not draft_report.is_accepted:
                            draft_passed = False
                            # Attempt rapid repair on draft up to max_repair_attempts
                            draft_repair_attempts = 0
                            while not draft_report.is_accepted and draft_repair_attempts < normalized_brief.max_repair_attempts:
                                if len(draft_report.failures) == 0:
                                    break
                                draft_repair_attempts += 1
                                draft_repair_plan = self.repair_planner.plan_repair(
                                    draft_report,
                                    shot_requirement=shot_req,
                                    scene_state=self.world_model.active_state,
                                )
                                if not draft_repair_plan.ordered_tasks_list:
                                    break
                                final_repair_plan = draft_repair_plan

                                repair_results = self.repair_executor.execute_plan(
                                    draft_repair_plan,
                                    base_asset_uri=draft_candidate.get("video_uri"),
                                )
                                r_cost = len(draft_repair_plan.ordered_tasks_list) * 0.02
                                shot_cost += r_cost
                                self.status.estimated_total_cost += r_cost
                                self._check_budget(normalized_brief.budget_limit, f"draft repair attempt {draft_repair_attempts} for {shot_req.shot_id}")
                                repairs_count += 1
                                self.status.repairs_performed_count += 1

                                # Update draft candidate and re-evaluate
                                draft_candidate = self._apply_repair_to_candidate(
                                    draft_candidate,
                                    repair_results,
                                    draft_repair_plan,
                                )
                                draft_report = self.critic_council.evaluate(
                                    candidate_data=draft_candidate,
                                    scene_state=self.world_model.active_state,
                                    shot_requirement=shot_req,
                                )
                                shot_cost += 0.015
                                self.status.estimated_total_cost += 0.015
                                self._check_budget(normalized_brief.budget_limit, f"draft re-audit {draft_repair_attempts} for {shot_req.shot_id}")
                                if draft_report.is_accepted:
                                    draft_passed = True
                                    break

                    if enable_spec and not draft_passed:
                        # GATING: Speculative draft failed hard gates. Do not generate expensive 1080p upscale!
                        candidate_data = draft_candidate
                        council_report = draft_report
                    else:
                        # Generate Full-Resolution Candidate (1080p latent generation)
                        candidate_data, gen_cost = self._generate_candidate_asset(
                            shot_req=shot_req,
                            compiled_payload=compiled_payload,
                            is_speculative_draft=False,
                        )
                        shot_cost += gen_cost
                        self.status.estimated_total_cost += gen_cost
                        self._check_budget(normalized_brief.budget_limit, f"full candidate generation for {shot_req.shot_id}")

                        # Audit full candidate with CriticCouncil
                        council_report = self.critic_council.evaluate(
                            candidate_data=candidate_data,
                            scene_state=self.world_model.active_state,
                            shot_requirement=shot_req,
                        )
                        shot_cost += 0.015  # VLM token audit cost
                        self.status.estimated_total_cost += 0.015
                        self._check_budget(normalized_brief.budget_limit, f"full candidate audit for {shot_req.shot_id}")

                        # -------------------------------------------------------
                        # Step 5: Surgical Repair Dispatch
                        # -------------------------------------------------------
                        current_candidate = candidate_data
                        repair_attempts = 0

                        while not council_report.is_accepted and repair_attempts < normalized_brief.max_repair_attempts:
                            if len(council_report.failures) == 0:
                                break
                            repair_attempts += 1
                            self._update_status(
                                ProductionState.SURGICAL_REPAIRING,
                                f"Surgical repair attempt {repair_attempts}/{normalized_brief.max_repair_attempts} "
                                f"for shot {shot_req.shot_id}",
                            )

                            repair_plan = self.repair_planner.plan_repair(
                                council_report,
                                shot_requirement=shot_req,
                                scene_state=self.world_model.active_state,
                            )
                            if not repair_plan.ordered_tasks_list:
                                break
                            final_repair_plan = repair_plan

                            repair_results = self.repair_executor.execute_plan(
                                repair_plan,
                                base_asset_uri=current_candidate.get("video_uri"),
                            )
                            r_cost = len(repair_plan.ordered_tasks_list) * 0.04
                            shot_cost += r_cost
                            self.status.estimated_total_cost += r_cost
                            self._check_budget(normalized_brief.budget_limit, f"candidate repair attempt {repair_attempts} for {shot_req.shot_id}")
                            repairs_count += 1
                            self.status.repairs_performed_count += 1

                            # Apply repairs to candidate representation
                            current_candidate = self._apply_repair_to_candidate(
                                current_candidate,
                                repair_results,
                                repair_plan,
                            )

                            # Re-evaluate repaired candidate
                            council_report = self.critic_council.evaluate(
                                candidate_data=current_candidate,
                                scene_state=self.world_model.active_state,
                                shot_requirement=shot_req,
                            )
                            shot_cost += 0.015
                            self.status.estimated_total_cost += 0.015
                            self._check_budget(normalized_brief.budget_limit, f"candidate re-audit {repair_attempts} for {shot_req.shot_id}")

                        candidate_data = current_candidate

                # -----------------------------------------------------------
                # Step 6: Multi-shot Continuity Auditing & State Freezing
                # -----------------------------------------------------------
                # Freeze snapshot into AetherWorldModel
                shot_snapshot = self.world_model.freeze_shot(
                    shot_id=shot_req.shot_id,
                    metadata={"scene_id": scene.scene_id, "duration": shot_req.target_duration},
                )

                continuity_passed = True
                if prev_shot_snapshot is not None:
                    audit_res = self.continuity_auditor.audit_transition(
                        shot_a=prev_shot_snapshot.state,
                        shot_b=shot_snapshot.state,
                        elapsed_seconds=shot_req.target_duration,
                        metadata={"shot_a_id": prev_shot_snapshot.shot_id, "shot_b_id": shot_snapshot.shot_id},
                    )
                    continuity_passed = audit_res.is_valid
                    transition_audit_records.append({
                        "shot_a_id": prev_shot_snapshot.shot_id,
                        "shot_b_id": shot_snapshot.shot_id,
                        "is_valid": audit_res.is_valid,
                        "violations": [v.model_dump(mode="json") for v in audit_res.violations],
                    })

                prev_shot_snapshot = shot_snapshot

                # Update passed shots count
                if council_report.is_accepted:
                    self.status.shots_passed_count += 1

                # -----------------------------------------------------------
                # Step 7: Dream-RSI Trace Logging Integration
                # -----------------------------------------------------------
                final_video_uri = candidate_data.get("video_uri", f"asset://renders/{shot_req.shot_id}.mp4")
                final_audio_uri = candidate_data.get("audio_uri", f"asset://renders/{shot_req.shot_id}_audio.wav")
                final_score = council_report.overall_score if council_report.is_accepted else 0.0

                trace_tree = self.trace_logger.log_episode(
                    shot_id=shot_req.shot_id,
                    scene_state=shot_snapshot.state,
                    shot_requirement=shot_req,
                    complexity_plan=comp_plan,
                    compiled_payload=compiled_payload,
                    council_report=council_report,
                    repair_plan=final_repair_plan,
                    final_score=final_score,
                    final_cost=round(shot_cost, 4),
                    execution_latency=round(shot_latency, 2),
                    final_video_uri=final_video_uri,
                    success=council_report.is_accepted,
                    metadata={"film_id": film_id, "scene_id": scene.scene_id},
                )
                self.replay_pool.add_trace(trace_tree)
                trace_episode_ids.append(trace_tree.tree_id)

                # Record in production timeline ledger
                record = ShotTimelineRecord(
                    shot_id=shot_req.shot_id,
                    scene_id=scene.scene_id,
                    sequence_index=global_shot_index - 1,
                    duration=shot_req.target_duration,
                    provider=compiled_payload.provider_target.value,
                    complexity_level=comp_plan.complexity_level.value,
                    video_uri=final_video_uri,
                    audio_uri=final_audio_uri,
                    council_score=final_score,
                    passed_hard_gates=council_report.all_hard_gates_passed,
                    repairs_count=repairs_count,
                    cost=round(shot_cost, 4),
                    speculative_draft_passed=draft_passed,
                    trace_episode_id=trace_tree.tree_id,
                    continuity_passed=continuity_passed,
                    metadata={
                        "resolution": shot_req.resolution,
                        "aspect_ratio": shot_req.aspect_ratio,
                    },
                )
                timeline_ledger.append(record.model_dump(mode="json"))

        # -------------------------------------------------------------------
        # Step 8: Mastering & Assembly
        # -------------------------------------------------------------------
        self._update_status(
            ProductionState.MASTERING,
            f"Assembling mastered timeline and final audio mix for '{normalized_brief.title}'",
        )

        total_duration = sum(item.get("duration", 0.0) for item in timeline_ledger)
        master_video_uri = f"{self.output_dir}/{film_id}_master.mp4"
        master_audio_uri = f"{self.output_dir}/{film_id}_master.wav"

        # Create master output placeholder / manifest file on disk
        self._write_master_manifest(
            film_id=film_id,
            brief=normalized_brief,
            timeline_ledger=timeline_ledger,
            master_video_uri=master_video_uri,
            master_audio_uri=master_audio_uri,
        )

        elapsed_total = round(time.time() - start_wall_clock, 2)
        self.status.elapsed_time = elapsed_total

        all_valid = all(t.get("is_valid", True) for t in transition_audit_records)
        continuity_summary = {
            "all_transitions_valid": all_valid,
            "total_transitions_checked": len(transition_audit_records),
            "transitions": transition_audit_records,
        }

        all_passed = (self.status.shots_passed_count == total_shots) and (total_shots > 0)
        final_state = ProductionState.COMPLETED if all_passed else ProductionState.FAILED
        final_film_status = "COMPLETED" if all_passed else "FAILED"

        status_msg = (
            f"Production completed: '{normalized_brief.title}' mastered in {elapsed_total}s"
            if all_passed
            else f"Production failed: only {self.status.shots_passed_count}/{total_shots} shots passed quality gates"
        )
        self._update_status(final_state, status_msg)

        primary_episode_id = trace_episode_ids[0] if trace_episode_ids else f"tree_{film_id}"

        mastered_film = MasteredFilm(
            film_id=film_id,
            title=normalized_brief.title,
            scenes_count=len(scenes),
            total_shots_count=len(timeline_ledger),
            duration_seconds=total_duration,
            master_video_artifact_uri=master_video_uri,
            master_audio_artifact_uri=master_audio_uri,
            total_production_cost=round(self.status.estimated_total_cost, 4),
            production_timeline_ledger=timeline_ledger,
            dream_rsi_trace_episode_id=primary_episode_id,
            trace_episode_ids=trace_episode_ids,
            continuity_report=continuity_summary,
            status=final_film_status,
            created_at=time.time(),
            metadata={
                "aspect_ratio": normalized_brief.aspect_ratio,
                "visual_style": normalized_brief.visual_style,
                "elapsed_seconds": elapsed_total,
                "repairs_performed": self.status.repairs_performed_count,
                "shots_passed_count": self.status.shots_passed_count,
            },
        )
        return mastered_film

    # -----------------------------------------------------------------------
    # Helper & Decomposition Methods
    # -----------------------------------------------------------------------

    def _normalize_brief(
        self,
        brief: Union[DirectorProductionBrief, str, Dict[str, Any]],
    ) -> DirectorProductionBrief:
        """Converts raw prompt, dict, or existing brief into DirectorProductionBrief."""
        if isinstance(brief, DirectorProductionBrief):
            return brief
        if isinstance(brief, str):
            clean_str = brief.strip()
            title = clean_str[:40].strip() or "Aether Cinematic Production"
            return DirectorProductionBrief(
                title=title,
                logline=clean_str,
                target_duration=30.0,
                aspect_ratio="9:16",
            )
        if isinstance(brief, dict):
            return DirectorProductionBrief.model_validate(brief)
        raise TypeError(f"Unsupported brief type: {type(brief)}")

    def _resolve_scenes(self, brief: DirectorProductionBrief) -> List[FilmScene]:
        """Resolves scenes from brief, or auto-decomposes narrative prompt into structured scenes."""
        if brief.scenes:
            return brief.scenes
        use_llm = bool(brief.metadata.get("use_llm", False)) if brief.metadata else False
        if (use_llm or os.environ.get("AETHER_USE_LLM_BREAKDOWN") == "1") and os.environ.get("AETHER_DISABLE_LLM_BREAKDOWN") != "1":
            try:
                scenes = self.decompose_narrative_with_llm(brief)
                if scenes:
                    return scenes
            except Exception as e:
                logger.warning(f"⚠️ LLM narrative breakdown failed ({e}), falling back to deterministic baseline")
        return self._decompose_brief_to_scenes(brief)

    def decompose_narrative_with_llm(
        self,
        brief: DirectorProductionBrief,
        model: str = "gpt-oss:120b:cloud",
        client: Optional[Any] = None,
    ) -> List[FilmScene]:
        """Uses Ollama Cloud LLM backend to break down a narrative brief into structured FilmScene objects."""
        from pipeline.ollama_client import OllamaClient
        ollama = client or self.llm_client or OllamaClient()

        prompt = (
            "You are the Lead Cinematographer and Screenplay Director for Project Aether.\n"
            "Decompose the following cinematic production brief into coherent scenes, characters, props, and camera shots:\n\n"
            f"Title: {brief.title}\n"
            f"Logline: {brief.logline}\n"
            f"Target Duration: {brief.target_duration}s\n"
            f"Aspect Ratio: {brief.aspect_ratio}\n"
            f"Visual Style: {brief.visual_style}\n\n"
            "Generate a JSON object with a 'scenes' list strictly following this structure:\n"
            "{\n"
            '  "scenes": [\n'
            "    {\n"
            '      "scene_id": "SC_001",\n'
            '      "narrative_beat": "dramatic description of the scene beat",\n'
            '      "location": "location name",\n'
            '      "environment_parameters": {"lighting": "volumetric rim lighting", "mood": "tense"},\n'
            '      "characters": [\n'
            "        {\n"
            '          "character_id": "character_slug",\n'
            '          "name": "Character Name",\n'
            '          "emotional_state": "hyper-vigilant",\n'
            '          "position": [0.0, 0.0, 2.5]\n'
            "        }\n"
            "      ],\n"
            '      "props": [\n'
            "        {\n"
            '          "prop_id": "prop_slug",\n'
            '          "name": "Prop Name",\n'
            '          "owner_id": "character_slug"\n'
            "        }\n"
            "      ],\n"
            '      "shot_list_requirements": [\n'
            "        {\n"
            '          "shot_id": "SHOT_001",\n'
            '          "target_duration": 5.0,\n'
            f'          "aspect_ratio": "{brief.aspect_ratio}",\n'
            '          "camera_movement": "dolly_in",\n'
            '          "character_ids_involved": ["character_slug"],\n'
            '          "audio": {\n'
            '            "dialogue": false,\n'
            '            "dialogue_text": null,\n'
            '            "music_mood": "tense_ambient"\n'
            "          }\n"
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}\n"
        )
        res = ollama.generate_completion(prompt=prompt, model=model, format="json")
        scenes_data = res.get("scenes") if isinstance(res, dict) else None
        if scenes_data and isinstance(scenes_data, list):
            scenes: List[FilmScene] = []
            for sc in scenes_data:
                try:
                    scenes.append(FilmScene.model_validate(sc))
                except Exception:
                    continue
            if scenes:
                return scenes

        return self._decompose_brief_to_scenes(brief)

    @classmethod
    def generate_production_brief(
        cls,
        premise: str,
        target_duration: float = 30.0,
        aspect_ratio: str = "9:16",
        visual_style: str = "cinematic photorealistic",
        model: str = "gpt-oss:120b:cloud",
        client: Optional[Any] = None,
    ) -> DirectorProductionBrief:
        """Generates a comprehensive DirectorProductionBrief from a high-level premise using Ollama Cloud."""
        from pipeline.ollama_client import OllamaClient
        ollama = client or OllamaClient()

        prompt = (
            "You are the Executive Producer & Director for Project Aether.\n"
            "Convert the following narrative premise into a broadcast-grade DirectorProductionBrief:\n\n"
            f"Premise: {premise}\n"
            f"Target Duration: {target_duration}s\n"
            f"Aspect Ratio: {aspect_ratio}\n"
            f"Visual Style: {visual_style}\n\n"
            "Output a JSON object strictly following this format:\n"
            "{\n"
            '  "title": "Short Punchy Title",\n'
            '  "logline": "1-2 sentence dramatic logline",\n'
            f'  "target_duration": {target_duration},\n'
            f'  "aspect_ratio": "{aspect_ratio}",\n'
            f'  "visual_style": "{visual_style}",\n'
            '  "target_models": ["veo_3_1", "kling_3_0", "runway_gen_4_5", "comfyui_cogvideox"],\n'
            '  "speculative_draft": true,\n'
            '  "budget_limit": 100.0,\n'
            f'  "metadata": {{"premise": "{premise[:100]}"}}\n'
            "}\n"
        )
        try:
            res = ollama.generate_completion(prompt=prompt, model=model, format="json")
            if isinstance(res, dict) and ("title" in res or "logline" in res):
                return DirectorProductionBrief.model_validate(res)
        except Exception as e:
            logger.warning(f"⚠️ Failed to generate brief with Ollama ({e}), using baseline.")

        return DirectorProductionBrief(
            title=premise[:40].strip() or "Cinematic Production",
            logline=premise,
            target_duration=target_duration,
            aspect_ratio=aspect_ratio,
            visual_style=visual_style,
        )

    def _decompose_brief_to_scenes(self, brief: DirectorProductionBrief) -> List[FilmScene]:
        """Decomposes concept prompt into coherent narrative scenes, characters, and shots."""
        target_dur = max(6.0, float(brief.target_duration))
        ar = brief.aspect_ratio
        spec = brief.speculative_draft

        # Calculate shot count based on pacing (e.g. 5.0s per shot)
        shot_duration = 5.0
        num_shots = max(2, int(round(target_dur / shot_duration)))
        per_shot_duration = round(target_dur / num_shots, 2)

        # Base character roster with persistent wardrobe damage and held props
        maya_character = {
            "character_id": "maya",
            "name": "Maya Lin",
            "position": [0.0, 0.0, 2.5],
            "facing_angle": 180.0,
            "eyeline_vector": [0.0, 0.0, -1.0],
            "emotional_state": "hyper-vigilant",
            "wardrobe": {
                "jacket": {
                    "id": "leather_jacket",
                    "state": "left_sleeve_torn",
                    "damage_level": 0.5,
                }
            },
            "injuries": ["blood_cheek_right"],
            "held_props": {"right": "spectrometer_device_01"},
        }

        spectrometer_prop = {
            "prop_id": "spectrometer_device_01",
            "name": "Spectrometer Device",
            "owner_id": "maya",
            "hand_attachment": "right",
            "physical_state": "pristine",
        }

        # Build shot list requirements
        shots: List[ShotRequirement] = []
        for i in range(num_shots):
            shot_id = f"SHOT_{i+1:03d}"
            movement = "dolly_in" if i == 0 else ("pan_right" if i == 1 else "static")
            shot = ShotRequirement(
                shot_id=shot_id,
                target_duration=per_shot_duration,
                aspect_ratio=ar,
                resolution="1080p",
                camera_movement=movement,
                character_ids_involved=["maya"],
                enable_speculative_draft=spec,
                enable_teacache=True,
                enable_pab=True,
                sampling_steps=8,
                audio=AudioRequirement(
                    dialogue=(i == 1),
                    dialogue_text="We have three seconds before breach." if i == 1 else None,
                    music_mood="high_tension_electronic",
                ),
                metadata={"scene_id": "SC_001", "brief_title": brief.title},
            )
            shots.append(shot)

        scene = FilmScene(
            scene_id="SC_001",
            narrative_beat=brief.logline or "Establishing tension in cleanroom",
            location="abandoned_cleanroom",
            environment_parameters={
                "lighting": "emergency_red_pulsing",
                "particulates": "steam_leak",
                "wetness": 0.85,
                "reflections": True,
            },
            characters=[maya_character],
            props=[spectrometer_prop],
            shot_list_requirements=shots,
            duration=target_dur,
        )
        return [scene]

    def _setup_world_model(self, scenes: List[FilmScene]) -> None:
        """Initializes AetherWorldModel with characters, wardrobe damage, and props."""
        if self._initial_world_model is not None:
            self.world_model = self._initial_world_model
        else:
            self.world_model = AetherWorldModel()
        if not scenes:
            return

        initial_scene = scenes[0]
        # Construct initial SceneState if world model is in default state
        if self.world_model.active_state.scene_id == "SC_INIT":
            initial_state = SceneState(
                scene_id=initial_scene.scene_id,
                location=initial_scene.location,
                timestamp="00:00",
                environment=EnvironmentState(**initial_scene.environment_parameters),
            )

            # Register characters
            for cdata in initial_scene.characters:
                char = CharacterState(**cdata) if isinstance(cdata, dict) else cdata
                initial_state.character_roster[char.character_id] = char

            # Register props
            for pdata in initial_scene.props:
                prop = PropState(**pdata) if isinstance(pdata, dict) else pdata
                initial_state.prop_roster[prop.prop_id] = prop

            # Set active camera
            initial_state.active_camera = CameraState(
                lens_focal_length_mm=35.0,
                camera_position=[0.0, 1.2, 5.0],
                eyeline_vector=[0.0, 0.0, -1.0],
            )
            self.world_model.set_active_state(initial_state)
        else:
            # Sync characters and props into existing world model
            for cdata in initial_scene.characters:
                char = CharacterState(**cdata) if isinstance(cdata, dict) else cdata
                if char.character_id not in self.world_model.active_state.character_roster:
                    self.world_model.active_state.character_roster[char.character_id] = char
            for pdata in initial_scene.props:
                prop = PropState(**pdata) if isinstance(pdata, dict) else pdata
                if prop.prop_id not in self.world_model.active_state.prop_roster:
                    self.world_model.active_state.prop_roster[prop.prop_id] = prop

    def _generate_candidate_asset(
        self,
        shot_req: ShotRequirement,
        compiled_payload: CompiledModelPayload,
        is_speculative_draft: bool = False,
    ) -> Tuple[Dict[str, Any], float]:
        """Generates candidate asset via custom candidate_generator or internal simulation."""
        if self.candidate_generator is not None:
            custom_cand = self.candidate_generator(
                shot_req=shot_req,
                compiled_payload=compiled_payload,
                is_speculative_draft=is_speculative_draft,
            )
            if isinstance(custom_cand, tuple) and len(custom_cand) == 2:
                return custom_cand[0], float(custom_cand[1])
            cost = 0.02 if is_speculative_draft else 0.08
            return custom_cand, cost

        # Internal simulation
        suffix = "_draft_480p" if is_speculative_draft else ""
        res = "480p" if is_speculative_draft else shot_req.resolution
        fps = 15.0 if is_speculative_draft else 30.0
        cost = 0.02 if is_speculative_draft else 0.08

        # Check injected defects from shot metadata (for testing)
        injected = shot_req.metadata.get("injected_defect")
        injected_draft = shot_req.metadata.get("injected_draft_defect")
        visual_defects: List[Dict[str, Any]] = []

        if is_speculative_draft and injected_draft:
            visual_defects.append(injected_draft)
        elif not is_speculative_draft and injected:
            visual_defects.append(injected)

        cand: Dict[str, Any] = {
            "shot_id": shot_req.shot_id,
            "video_uri": f"{self.renders_dir}/{shot_req.shot_id}{suffix}.mp4",
            "audio_uri": f"{self.renders_dir}/{shot_req.shot_id}_audio.wav",
            "duration": shot_req.target_duration,
            "resolution": res,
            "fps": fps,
            "cinematography_score": 9.2,
            "atmosphere_score": 9.0,
            "performance_score": 8.8,
            "pacing_score": 8.5,
            "lip_sync_offset_ms": shot_req.metadata.get("lip_sync_offset_ms", 10.0),
            "visual_defects": visual_defects,
        }
        return cand, cost

    def _apply_repair_to_candidate(
        self,
        candidate_data: Dict[str, Any],
        repair_results: List[RepairExecutionResult],
        repair_plan: RepairPlan,
    ) -> Dict[str, Any]:
        """Applies successful surgical repairs to the candidate data."""
        repaired = copy.deepcopy(candidate_data)
        if not repair_results:
            return repaired

        successful = [r for r in repair_results if r.success_status]
        if not successful:
            return repaired

        successful_with_uri = [r for r in successful if r.repaired_asset_uri]
        if successful_with_uri:
            repaired["video_uri"] = successful_with_uri[-1].repaired_asset_uri

        successful_task_ids = {r.task_id for r in successful}
        successful_actions = {
            t.action_type
            for t in repair_plan.ordered_tasks_list
            if t.task_id in successful_task_ids
        }

        # Clear resolved visual defects only if inpainting or full regeneration succeeded
        if (
            RepairActionType.REGIONAL_TEMPORAL_INPAINTING in successful_actions
            or RepairActionType.FULL_SHOT_REGENERATION in successful_actions
            or RepairActionType.SPATIAL_PREVIS_REBLOCK in successful_actions
        ):
            repaired["visual_defects"] = []

        # Clear audio desync only if audio remaster or full regeneration succeeded
        if (
            RepairActionType.AUDIO_REMASTER_VOICE in successful_actions
            or RepairActionType.AUDIO_REMASTER_FOLEY in successful_actions
            or RepairActionType.FULL_SHOT_REGENERATION in successful_actions
        ):
            repaired["lip_sync_offset_ms"] = 10.0

        return repaired

    def _generate_dry_run_candidate(
        self,
        shot_req: ShotRequirement,
        compiled_payload: CompiledModelPayload,
    ) -> Dict[str, Any]:
        """Synthesizes candidate representation for dry-run simulation."""
        return {
            "shot_id": shot_req.shot_id,
            "video_uri": f"asset://dry_run/{shot_req.shot_id}.mp4",
            "audio_uri": f"asset://dry_run/{shot_req.shot_id}_audio.wav",
            "duration": shot_req.target_duration,
            "resolution": shot_req.resolution,
            "fps": 30.0,
            "cinematography_score": 9.5,
            "atmosphere_score": 9.5,
            "performance_score": 9.5,
            "pacing_score": 9.5,
            "lip_sync_offset_ms": 5.0,
            "visual_defects": [],
        }

    def _evaluate_dry_run_report(self, shot_req: ShotRequirement) -> CouncilEvaluationReport:
        """Returns synthetic passing CouncilEvaluationReport for dry-run simulation."""
        return CouncilEvaluationReport(
            hard_gate_verdicts={
                HardGateType.ANATOMICAL_INTEGRITY: True,
                HardGateType.CHARACTER_IDENTITY: True,
                HardGateType.PROP_CONTINUITY: True,
                HardGateType.LIP_SYNC_ALIGNMENT: True,
            },
            all_hard_gates_passed=True,
            overall_score=9.5,
            soft_scores={
                "Cinematography": 9.5,
                "Atmosphere": 9.5,
                "Performance": 9.5,
                "Pacing": 9.5,
            },
            status=CouncilStatus.ACCEPTED,
            shot_id=shot_req.shot_id,
            summary=f"Dry run audit passed for {shot_req.shot_id}",
        )

    def _write_master_manifest(
        self,
        film_id: str,
        brief: DirectorProductionBrief,
        timeline_ledger: List[Dict[str, Any]],
        master_video_uri: str,
        master_audio_uri: str,
    ) -> None:
        """Writes master film manifest JSON to output directory."""
        manifest_path = self.output_dir / f"{film_id}_manifest.json"
        manifest_data = {
            "film_id": film_id,
            "title": brief.title,
            "logline": brief.logline,
            "aspect_ratio": brief.aspect_ratio,
            "target_duration": brief.target_duration,
            "actual_duration": sum(t.get("duration", 0.0) for t in timeline_ledger),
            "total_shots": len(timeline_ledger),
            "master_video_uri": master_video_uri,
            "master_audio_uri": master_audio_uri,
            "timeline": timeline_ledger,
            "created_at": time.time(),
        }
        import json
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

    def _update_status(self, new_state: ProductionState, message: Optional[str] = None) -> None:
        """Transitions production state and invokes status callback."""
        self.status.transition_to(new_state, message)
        self._notify_status()

    def _notify_status(self) -> None:
        """Dispatches status notification hook if registered."""
        if self.status_callback is not None:
            self.status_callback(self.status)


def generate_production_brief(
    premise: str,
    target_duration: float = 30.0,
    aspect_ratio: str = "9:16",
    visual_style: str = "cinematic photorealistic",
    model: str = "gpt-oss:120b:cloud",
    client: Optional[Any] = None,
) -> DirectorProductionBrief:
    """Convenience helper to generate a DirectorProductionBrief using Ollama Cloud."""
    return AetherDirector.generate_production_brief(
        premise=premise,
        target_duration=target_duration,
        aspect_ratio=aspect_ratio,
        visual_style=visual_style,
        model=model,
        client=client,
    )
