"""Project Aether Surgical Repair Planner.

Implements the Minimum Necessary Intervention logic (Pillar 6 / WBS 1.7):
- Evaluates CouncilEvaluationReport from CriticCouncil alongside ShotRequirement and SceneState.
- Localized hand/limb deformation -> Regional Temporal Inpainting without re-rendering entire shot.
- Dialogue desync/audio clipping -> Audio Remastering without touching video pixels.
- Trajectory/physics breakdown -> UE5 Spatial Previs Re-blocking.
- Over-threshold defects (>3 severe non-localized or multiple hard gates across >70% frames) -> Full Shot Regeneration.
- Generates optimized, deduplicated, and prioritized RepairPlan.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid

from aether.compiler.schemas import ShotRequirement
from aether.council.schemas import (
    CouncilEvaluationReport,
    CouncilStatus,
    CriticFailureObject,
    CriticType,
    DefectSeverity,
    HardGateType,
    RepairRecommendation,
)
from aether.repair.masking import TemporalMaskEngine
from aether.repair.schemas import (
    ComputeTier,
    ProtectedRegion,
    ProtectedRegionType,
    RepairActionType,
    RepairBoundaryMask,
    RepairPlan,
    SurgicalRepairTask,
)
from aether.state.schemas import SceneState


class RepairPlanner:
    """Master surgical repair planner executing the Minimum Necessary Intervention policy.

    Avoids brute-force re-rolling of entire shots by decomposing critic council defects
    into localized, non-destructive surgical corrections.
    """

    def __init__(
        self,
        mask_engine: Optional[TemporalMaskEngine] = None,
        default_fps: float = 30.0,
        escalation_defect_threshold: int = 3,
        escalation_frame_coverage_threshold: float = 0.70,
        repair_iou_threshold: float = 0.30,
        active_policy: Optional[Any] = None,
    ) -> None:
        self.mask_engine = mask_engine or TemporalMaskEngine()
        self.default_fps = default_fps
        self.escalation_defect_threshold = escalation_defect_threshold
        self.escalation_frame_coverage_threshold = escalation_frame_coverage_threshold
        self.repair_iou_threshold = repair_iou_threshold
        self.active_policy = active_policy

    ANATOMY_KEYWORDS: Tuple[str, ...] = (
        "limb", "arm", "leg", "hand", "finger", "digit", "toe", "foot", "feet",
        "anatomy", "anatomical", "face", "eye", "head", "neck", "joint", "fused",
        "proportion", "torso", "body", "deform", "uncanny", "polydactyly",
    )

    def _resolve_failure_hard_gate(self, failure: CriticFailureObject) -> Optional[HardGateType]:
        """Resolves violated hard gate from defect object, matching CriticCouncil taxonomy."""
        if failure.hard_gate is not None:
            return failure.hard_gate

        ft = failure.failure_type.lower()
        if any(k in ft for k in self.ANATOMY_KEYWORDS):
            return HardGateType.ANATOMICAL_INTEGRITY
        if any(k in ft for k in ("identity", "face_drift", "actor", "wardrobe", "injury", "wound", "scar")):
            return HardGateType.CHARACTER_IDENTITY
        if any(k in ft for k in ("prop", "handoff", "possession", "attachment")):
            return HardGateType.PROP_CONTINUITY
        if any(k in ft for k in ("lip_sync", "phonem", "viseme", "sync_offset", "speech", "mouth", "audio", "dialogue")):
            return HardGateType.LIP_SYNC_ALIGNMENT
        if any(k in ft for k in ("gravity", "trajectory", "clipping", "solid_body", "acceleration", "motion_spike", "physics")):
            return HardGateType.PHYSICAL_TRAJECTORY

        if failure.critic_type == CriticType.VISUAL:
            return HardGateType.ANATOMICAL_INTEGRITY
        elif failure.critic_type == CriticType.CONTINUITY:
            return HardGateType.CHARACTER_IDENTITY
        elif failure.critic_type in (CriticType.PERFORMANCE, CriticType.AUDIO):
            return HardGateType.LIP_SYNC_ALIGNMENT
        elif failure.critic_type == CriticType.PHYSICS:
            return HardGateType.PHYSICAL_TRAJECTORY
        return None

    def _is_physics_defect(self, failure: CriticFailureObject) -> bool:
        """Determines if a defect is physical kinematics / 3D trajectory / mesh clipping."""
        if failure.critic_type == CriticType.PHYSICS:
            return True
        if failure.recommended_repair == RepairRecommendation.SPATIAL_PREVIS_RERUN:
            return True
        if failure.hard_gate == HardGateType.PHYSICAL_TRAJECTORY:
            return True
        f_type = failure.failure_type.lower()
        physics_keywords = (
            "trajectory", "gravity", "acceleration", "momentum", "solid_body_clipping",
            "mesh_clipping", "geometry_clipping", "kinematics", "physical", "physics",
            "collision", "fall_through_floor"
        )
        return any(k in f_type for k in physics_keywords)

    def _is_audio_defect(self, failure: CriticFailureObject) -> bool:
        """Determines if a defect is exclusively auditory / speech / lip-sync."""
        if failure.critic_type == CriticType.AUDIO:
            return True
        if failure.recommended_repair == RepairRecommendation.AUDIO_REMASTER:
            return True
        if failure.hard_gate == HardGateType.LIP_SYNC_ALIGNMENT:
            return True
        f_type = failure.failure_type.lower()
        audio_keywords = (
            "audio", "dialogue", "speech", "voice", "lip_sync", "desync",
            "phoneme", "viseme", "foley", "audio_clipping", "dialogue_clipping",
            "voice_clipping", "speech_clipping", "sound", "volume", "mix"
        )
        if any(k in f_type for k in audio_keywords):
            if not self._is_physics_defect(failure):
                return True
        return False

    def plan_repair(
        self,
        report: CouncilEvaluationReport,
        shot_requirement: Optional[ShotRequirement] = None,
        scene_state: Optional[SceneState] = None,
    ) -> RepairPlan:
        """Generates an optimized, prioritized surgical RepairPlan for an evaluated shot.

        Args:
            report: Evaluation findings from the CriticCouncil.
            shot_requirement: Requirements of the shot being evaluated.
            scene_state: Current world state / scene snapshot.

        Returns:
            RepairPlan: Structured, non-redundant repair instructions.
        """
        shot_id = report.shot_id or (shot_requirement.shot_id if shot_requirement else "SHOT_UNKNOWN")
        plan_id = f"PLAN_{shot_id}_{uuid.uuid4().hex[:8]}"

        # 1. Clean Pass Check: If council accepted and no non-negligible defects exist
        actionable_failures = [
            f for f in report.failures if f.severity != DefectSeverity.NEGLIGIBLE
        ]

        # Convert directives if report has prioritized_repair_plan but failures list is empty
        if not actionable_failures and report.prioritized_repair_plan:
            for directive in report.prioritized_repair_plan:
                if directive.severity != DefectSeverity.NEGLIGIBLE:
                    actionable_failures.append(
                        CriticFailureObject(
                            failure_type=directive.defect_type,
                            severity=directive.severity,
                            frame_bounds=directive.frame_bounds,
                            bounding_box=directive.bounding_box,
                            target_entity_id=directive.target_entity_id,
                            observed_state=directive.action_description,
                            recommended_repair=directive.repair_type,
                            metadata=directive.parameters,
                        )
                    )

        if report.status == CouncilStatus.ACCEPTED and not actionable_failures:
            return RepairPlan(
                plan_id=plan_id,
                original_shot_id=shot_id,
                total_tasks_count=0,
                ordered_tasks_list=[],
                estimated_compute_tier=ComputeTier.TIER_0_NOOP,
                expected_latency=0.0,
                is_feasible=True,
                summary="Shot accepted by Critic Council. No repair interventions required.",
            )

        total_frames = self._resolve_total_frames(report, shot_requirement)

        # 2. Escalation Gate Check: Full Shot Regeneration Check
        should_escalate, escalation_reason = self._should_escalate_to_full_regen(
            report, actionable_failures, total_frames
        )

        if should_escalate:
            regen_task = self._create_full_regen_task(
                report=report,
                shot_id=shot_id,
                actionable_failures=actionable_failures,
                reason=escalation_reason,
            )
            return RepairPlan(
                plan_id=plan_id,
                original_shot_id=shot_id,
                total_tasks_count=1,
                ordered_tasks_list=[regen_task],
                estimated_compute_tier=ComputeTier.TIER_4_FULL_REGEN,
                expected_latency=60.0,
                is_feasible=True,
                summary=f"Escalated to Full Shot Regeneration: {escalation_reason}",
                metadata={"escalation_reason": escalation_reason, "total_frames": total_frames},
            )

        # 3. Minimum Necessary Intervention Dispatch
        raw_tasks: List[SurgicalRepairTask] = []
        task_counter = 1

        # Extract protected regions from scene state and shot requirement
        protected_regions = self._extract_protected_regions(
            scene_state=scene_state,
            shot_requirement=shot_requirement,
            failures=actionable_failures,
        )

        for failure in actionable_failures:
            task = self._triage_failure(
                failure=failure,
                task_idx=task_counter,
                total_frames=total_frames,
                protected_regions=protected_regions,
                shot_requirement=shot_requirement,
            )
            if task:
                raw_tasks.append(task)
                task_counter += 1

        # If any triaged task mandated full regeneration, upgrade whole plan cleanly
        if any(t.is_full_regen for t in raw_tasks):
            escalation_reasons = [
                str(t.metadata.get("escalation_reason", t.target_defect_id))
                for t in raw_tasks if t.is_full_regen
            ]
            regen_task = self._create_full_regen_task(
                report=report,
                shot_id=shot_id,
                actionable_failures=actionable_failures,
                reason="; ".join(escalation_reasons) or "Full shot regeneration required.",
            )
            return RepairPlan(
                plan_id=plan_id,
                original_shot_id=shot_id,
                total_tasks_count=1,
                ordered_tasks_list=[regen_task],
                estimated_compute_tier=ComputeTier.TIER_4_FULL_REGEN,
                expected_latency=60.0,
                is_feasible=True,
                summary=f"Escalated to Full Shot Regeneration: {regen_task.metadata.get('escalation_reason', '')}",
                metadata={"escalation_reason": regen_task.metadata.get("escalation_reason", ""), "total_frames": total_frames},
            )

        # 4. Deduplicate and merge overlapping regional inpaint tasks
        optimized_tasks = self._deduplicate_and_optimize_tasks(raw_tasks)

        # 5. Order tasks by execution hierarchy
        ordered_tasks = self._order_tasks_by_priority(optimized_tasks)

        # 6. Compute tiers and latency
        compute_tier = self._estimate_compute_tier(ordered_tasks)
        expected_latency = self._estimate_expected_latency(ordered_tasks)

        summary = (
            f"Scheduled {len(ordered_tasks)} surgical intervention tasks: "
            f"{sum(1 for t in ordered_tasks if t.is_audio)} audio remaster, "
            f"{sum(1 for t in ordered_tasks if t.is_inpainting)} localized inpaint, "
            f"{sum(1 for t in ordered_tasks if t.is_previs)} previs reblock."
        )

        return RepairPlan(
            plan_id=plan_id,
            original_shot_id=shot_id,
            total_tasks_count=len(ordered_tasks),
            ordered_tasks_list=ordered_tasks,
            estimated_compute_tier=compute_tier,
            expected_latency=expected_latency,
            is_feasible=True,
            summary=summary,
            metadata={"raw_defect_count": len(actionable_failures), "total_frames": total_frames},
        )

    def _resolve_total_frames(
        self,
        report: CouncilEvaluationReport,
        shot_requirement: Optional[ShotRequirement],
    ) -> int:
        """Determines total frame count from shot requirements or defect spans."""
        if shot_requirement and shot_requirement.target_duration > 0:
            return max(1, int(round(shot_requirement.target_duration * self.default_fps)))
        
        # Fallback to highest observed frame index
        max_frame = 0
        for f in report.failures:
            max_frame = max(max_frame, f.end_frame)
        if max_frame > 0:
            return max_frame + 1
        return int(round(5.0 * self.default_fps))  # Default 5s @ 30fps

    def _should_escalate_to_full_regen(
        self,
        report: CouncilEvaluationReport,
        actionable_failures: List[CriticFailureObject],
        total_frames: int,
    ) -> Tuple[bool, str]:
        """Evaluates whether defects exceed localized surgical feasibility.

        Escalation conditions (WBS 1.7 / Pillar 6):
        1. > 3 severe non-localized visual/spatial defects exist.
        2. Multiple hard gates fail across > 70% of frames.
        3. Explicit FULL_REGEN recommendation for catastrophic failures.
        """
        # Condition 1: Severe non-localized visual defects count > threshold
        severe_non_localized_visual = [
            f for f in actionable_failures
            if f.severity in (DefectSeverity.SEVERE, DefectSeverity.FATAL)
            and self._is_non_localized(f)
        ]
        if len(severe_non_localized_visual) > self.escalation_defect_threshold:
            return (
                True,
                f"Defect count exceeded threshold: {len(severe_non_localized_visual)} severe non-localized defects "
                f"(threshold: >{self.escalation_defect_threshold}).",
            )

        # Condition 2: Multiple hard gates fail across > 70% of frames
        failed_gates = set(report.failed_hard_gates)
        for f in actionable_failures:
            resolved_gate = self._resolve_failure_hard_gate(f)
            if resolved_gate and f.severity.is_hard_gate_breaker:
                failed_gates.add(resolved_gate)

        if len(failed_gates) >= 2 and total_frames > 0:
            frame_indices_impacted: Set[int] = set()
            for f in actionable_failures:
                resolved_gate = self._resolve_failure_hard_gate(f)
                if (resolved_gate in failed_gates) and f.severity.is_hard_gate_breaker:
                    for frame_idx in range(f.start_frame, f.end_frame + 1):
                        frame_indices_impacted.add(frame_idx)

            coverage_ratio = len(frame_indices_impacted) / float(total_frames)
            if coverage_ratio > self.escalation_frame_coverage_threshold:
                sorted_gates = sorted([g.value for g in failed_gates])
                return (
                    True,
                    f"Multiple hard gates ({sorted_gates}) failed across "
                    f"{coverage_ratio * 100:.1f}% of shot frames (threshold: >{self.escalation_frame_coverage_threshold * 100:.0f}%).",
                )

        # Condition 3: Catastrophic fatal non-localized defect
        for f in actionable_failures:
            if f.severity == DefectSeverity.FATAL and self._is_non_localized(f):
                return True, f"Fatal catastrophic defect detected across full frame: {f.failure_type}"

        return False, ""

    def _is_non_localized(self, failure: CriticFailureObject) -> bool:
        """Checks if a failure is widespread/global rather than sub-regional."""
        if self._is_audio_defect(failure):
            return False
        x1, y1, x2, y2 = failure.bounding_box
        area = (x2 - x1) * (y2 - y1)
        # Full-frame bounds or covering > 60% of frame area
        if area >= 0.60 or failure.bounding_box == (0.0, 0.0, 1.0, 1.0):
            return True
        return False

    def _triage_failure(
        self,
        failure: CriticFailureObject,
        task_idx: int,
        total_frames: int,
        protected_regions: List[ProtectedRegion],
        shot_requirement: Optional[ShotRequirement],
    ) -> Optional[SurgicalRepairTask]:
        """Applies Minimum Necessary Intervention dispatch for an individual defect."""
        # Rule 1: Physical Trajectory / Kinematics failure -> UE5 Spatial Previs Reblock
        if self._is_physics_defect(failure):
            return self._create_previs_reblock_task(failure, task_idx)

        # Rule 2: Audio / Lip-Sync Dialogue / Foley defects -> Audio Remaster without touching pixels
        if self._is_audio_defect(failure):
            return self._create_audio_repair_task(failure, task_idx)

        # Rule 3: Visual defect
        # Non-localized visual defect -> Full Shot Regeneration
        if self._is_non_localized(failure):
            return self._create_full_regen_task(
                report=None,
                shot_id="SHOT",
                actionable_failures=[failure],
                reason=f"Non-localized visual defect {failure.failure_type} requires full shot regeneration.",
            )

        # Localized defect -> Regional temporal inpainting
        return self._create_inpainting_repair_task(
            failure=failure,
            task_idx=task_idx,
            total_frames=total_frames,
            protected_regions=protected_regions,
            shot_requirement=shot_requirement,
        )

    def _create_audio_repair_task(
        self,
        failure: CriticFailureObject,
        task_idx: int,
    ) -> SurgicalRepairTask:
        """Constructs an audio-only repair task without touching video pixels."""
        f_type = failure.failure_type.lower()
        is_foley = "foley" in f_type or "sfx" in f_type or "ambient" in f_type
        action_type = (
            RepairActionType.AUDIO_REMASTER_FOLEY
            if is_foley
            else RepairActionType.AUDIO_REMASTER_VOICE
        )

        latency_ms = failure.metadata.get("offset_ms", failure.metadata.get("latency_shift_ms", -100.0))
        target_phonemes = failure.metadata.get("target_phonemes", [])

        params = {
            "latency_shift_ms": latency_ms,
            "target_phonemes": target_phonemes,
            "mix_mode": "remux_stream",
            "preserve_video_stream": True,
        }

        return SurgicalRepairTask(
            task_id=f"TASK_AUDIO_{task_idx:03d}",
            action_type=action_type,
            target_defect_id=failure.failure_type,
            defect_severity=failure.severity,
            priority=3,  # Audio remux executes alongside or after render
            repair_boundary_mask=None,  # Zero pixel modification
            audio_retargeting_params=params,
            fallback_strategy=RepairActionType.FULL_SHOT_REGENERATION,
            metadata={
                "observed_state": failure.observed_state,
                "expected_state": failure.expected_state,
                "target_entity_id": failure.target_entity_id,
            },
        )

    def _create_previs_reblock_task(
        self,
        failure: CriticFailureObject,
        task_idx: int,
    ) -> SurgicalRepairTask:
        """Constructs a spatial previs reblock task targeting UE5 motion guides."""
        return SurgicalRepairTask(
            task_id=f"TASK_PREVIS_{task_idx:03d}",
            action_type=RepairActionType.SPATIAL_PREVIS_REBLOCK,
            target_defect_id=failure.failure_type,
            defect_severity=failure.severity,
            priority=1,  # Previs reblock must execute first before rendering
            repair_boundary_mask=None,
            metadata={
                "ue5_reblock_directives": {
                    "adjust_trajectory": True,
                    "target_entity_id": failure.target_entity_id,
                    "frame_bounds": failure.frame_bounds,
                    "observed_anomaly": failure.observed_state,
                },
            },
            fallback_strategy=RepairActionType.FULL_SHOT_REGENERATION,
        )

    def _create_inpainting_repair_task(
        self,
        failure: CriticFailureObject,
        task_idx: int,
        total_frames: int,
        protected_regions: List[ProtectedRegion],
        shot_requirement: Optional[ShotRequirement],
    ) -> SurgicalRepairTask:
        """Constructs a localized spatio-temporal inpainting task."""
        # Camera velocity compensation for feather radius
        cam_vel = shot_requirement.camera_velocity_mps if shot_requirement else 0.0
        adjusted_feather = max(16.0, 16.0 * (1.0 + 0.1 * cam_vel))

        boundary_mask = self.mask_engine.create_boundary_mask(
            failure=failure,
            feather_radius_px=adjusted_feather,
            temporal_pad_frames=4,
            box_expansion_ratio=0.15,
            protected_regions=protected_regions,
        )

        # Synthesize targeted replacement and negative prompts
        f_type = failure.failure_type.lower()
        if "hand" in f_type or "finger" in f_type or "limb" in f_type:
            pos_prompt = "photorealistic anatomically correct human hand, sharp five fingers, realistic skin texture, natural joint bending"
            neg_prompt = "extra fingers, missing fingers, mutated hands, deformed limbs, floating digits, malformed joints, blurry artifacts"
        elif "face" in f_type or "eye" in f_type:
            pos_prompt = "cinematic photorealistic expressive human face, sharp eyes, natural gaze, consistent skin tone"
            neg_prompt = "distorted face, asymmetrical eyes, warped pupils, melting skin, facial artifacts"
        else:
            pos_prompt = "cinematic coherent texture, high fidelity photorealistic surface, seamless lighting integration"
            neg_prompt = "flickering, strobing, digital noise, tearing, seam line, morphing artifacts"

        return SurgicalRepairTask(
            task_id=f"TASK_INPAINT_{task_idx:03d}",
            action_type=RepairActionType.REGIONAL_TEMPORAL_INPAINTING,
            target_defect_id=failure.failure_type,
            defect_severity=failure.severity,
            priority=2,
            repair_boundary_mask=boundary_mask,
            replacement_prompt=pos_prompt,
            negative_prompt_modifier=neg_prompt,
            fallback_strategy=RepairActionType.FULL_SHOT_REGENERATION,
            metadata={
                "target_entity_id": failure.target_entity_id,
                "observed_state": failure.observed_state,
                "frame_span": failure.frame_bounds,
                "camera_velocity_mps": cam_vel,
            },
        )

    def _create_full_regen_task(
        self,
        report: Optional[CouncilEvaluationReport],
        shot_id: str,
        actionable_failures: List[CriticFailureObject],
        reason: str,
    ) -> SurgicalRepairTask:
        """Constructs a full shot regeneration task when surgical repair is infeasible."""
        observed_defects = [f.failure_type for f in actionable_failures]
        neg_prompt = ", ".join(set(observed_defects + ["deformed limbs", "temporal flicker", "motion jitter", "audio desync"]))

        return SurgicalRepairTask(
            task_id=f"TASK_REGEN_{uuid.uuid4().hex[:6]}",
            action_type=RepairActionType.FULL_SHOT_REGENERATION,
            target_defect_id="MULTIPLE_CATASTROPHIC_DEFECTS",
            defect_severity=DefectSeverity.FATAL,
            priority=1,
            repair_boundary_mask=None,
            replacement_prompt="masterpiece cinematic render, flawless anatomical integrity, deterministic physics",
            negative_prompt_modifier=neg_prompt,
            fallback_strategy=None,
            metadata={"escalation_reason": reason, "defects_addressed": observed_defects},
        )

    def _extract_protected_regions(
        self,
        scene_state: Optional[SceneState],
        shot_requirement: Optional[ShotRequirement],
        failures: List[CriticFailureObject],
    ) -> List[ProtectedRegion]:
        """Identifies clean background, camera trajectories, and uninvolved actors to shield."""
        protected: List[ProtectedRegion] = []

        # 1. Camera Trajectory Protection
        if shot_requirement:
            traj_path = getattr(shot_requirement, "camera_trajectory_path", None)
            cam_mov = getattr(shot_requirement, "camera_movement", None)
            if traj_path or cam_mov:
                protected.append(
                    ProtectedRegion(
                        region_type=ProtectedRegionType.CAMERA_MOTION,
                        description=f"Shielding camera trajectory '{cam_mov or 'motion_vector'}'",
                        metadata={"trajectory_path": traj_path, "camera_movement": cam_mov},
                    )
                )
        elif scene_state and getattr(scene_state, "active_camera", None):
            cam = scene_state.active_camera
            protected.append(
                ProtectedRegion(
                    region_type=ProtectedRegionType.CAMERA_MOTION,
                    description="Shielding active camera kinematics",
                    metadata={"camera": getattr(cam, "model_dump", lambda: {})()},
                )
            )

        # 2. Clean Background Protection
        if scene_state and getattr(scene_state, "location", None):
            protected.append(
                ProtectedRegion(
                    region_type=ProtectedRegionType.BACKGROUND,
                    description=f"Preserving stable background scenery for location '{scene_state.location}'",
                )
            )

        # 3. Shield clean characters not associated with defects
        if scene_state:
            defect_entities = {f.target_entity_id for f in failures if f.target_entity_id}
            for char_id, char_state in getattr(scene_state, "characters", {}).items():
                if char_id not in defect_entities:
                    bbox = getattr(char_state, "bounding_box", None)
                    if not bbox and hasattr(char_state, "metadata"):
                        bbox = char_state.metadata.get("bounding_box") or char_state.metadata.get("screen_bbox")
                    if bbox:
                        protected.append(
                            ProtectedRegion(
                                region_type=ProtectedRegionType.FACE if "face" in char_id.lower() else ProtectedRegionType.OTHER,
                                bounding_box=bbox,
                                protection_strength=1.0,
                                description=f"Shielding uninvolved character {char_id}",
                            )
                        )

        return protected

    def _deduplicate_and_optimize_tasks(
        self,
        tasks: List[SurgicalRepairTask],
    ) -> List[SurgicalRepairTask]:
        """Merges heavily overlapping regional inpaint tasks to avoid redundant compute."""
        inpaint_tasks = [t for t in tasks if t.is_inpainting and t.repair_boundary_mask]
        other_tasks = [t for t in tasks if not (t.is_inpainting and t.repair_boundary_mask)]

        if len(inpaint_tasks) <= 1:
            return tasks

        merged_inpaint: List[SurgicalRepairTask] = []
        consumed = set()

        for i, t1 in enumerate(inpaint_tasks):
            if i in consumed:
                continue
            m1 = t1.repair_boundary_mask
            assert m1 is not None

            cur_task = t1
            cur_box = list(m1.bounding_box)
            cur_frames = list(m1.frame_bounds)
            cur_severity = t1.defect_severity
            cur_feather = m1.feather_radius_px
            cur_pad = m1.temporal_pad_frames
            cur_protected = list(m1.protected_regions)

            for j in range(i + 1, len(inpaint_tasks)):
                if j in consumed:
                    continue
                t2 = inpaint_tasks[j]
                m2 = t2.repair_boundary_mask
                assert m2 is not None

                # Compute Spatial IoU
                iou = self._compute_box_iou(tuple(cur_box), m2.bounding_box)
                # Compute Temporal Overlap
                t_overlap = self._compute_temporal_overlap(tuple(cur_frames), m2.frame_bounds)

                # Merge if both spatial and temporal overlap are significant
                if iou > self.repair_iou_threshold and t_overlap > 0.30:
                    consumed.add(j)
                    # Union bounding box
                    cur_box = [
                        min(cur_box[0], m2.bounding_box[0]),
                        min(cur_box[1], m2.bounding_box[1]),
                        max(cur_box[2], m2.bounding_box[2]),
                        max(cur_box[3], m2.bounding_box[3]),
                    ]
                    # Union frame span
                    cur_frames = [
                        min(cur_frames[0], m2.frame_bounds[0]),
                        max(cur_frames[1], m2.frame_bounds[1]),
                    ]
                    # Feather and pad take the maximum to ensure smooth coverage
                    cur_feather = max(cur_feather, m2.feather_radius_px)
                    cur_pad = max(cur_pad, m2.temporal_pad_frames)

                    # Merge protected regions without duplication
                    for pr in m2.protected_regions:
                        if not any(
                            existing.region_type == pr.region_type and existing.bounding_box == pr.bounding_box
                            for existing in cur_protected
                        ):
                            cur_protected.append(pr)

                    # Update task prompt/intent if t2 has strictly higher severity
                    if t2.defect_severity.rank < cur_severity.rank:
                        cur_severity = t2.defect_severity
                        cur_task = t2

            # Create merged task
            merged_mask = RepairBoundaryMask(
                bounding_box=tuple(cur_box),
                frame_bounds=tuple(cur_frames),
                feather_radius_px=cur_feather,
                temporal_pad_frames=cur_pad,
                protected_regions=cur_protected,
            )
            merged_task = SurgicalRepairTask(
                task_id=cur_task.task_id,
                action_type=RepairActionType.REGIONAL_TEMPORAL_INPAINTING,
                target_defect_id=cur_task.target_defect_id,
                defect_severity=cur_severity,
                priority=cur_task.priority,
                repair_boundary_mask=merged_mask,
                replacement_prompt=cur_task.replacement_prompt,
                negative_prompt_modifier=cur_task.negative_prompt_modifier,
                fallback_strategy=cur_task.fallback_strategy,
                metadata=cur_task.metadata,
            )
            merged_inpaint.append(merged_task)

        return other_tasks + merged_inpaint

    def _compute_box_iou(
        self,
        box1: Tuple[float, float, float, float],
        box2: Tuple[float, float, float, float],
    ) -> float:
        """Calculates 2D Intersection-over-Union."""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        inter_w = max(0.0, x2 - x1)
        inter_h = max(0.0, y2 - y1)
        inter_area = inter_w * inter_h

        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union_area = area1 + area2 - inter_area

        if union_area <= 0.0:
            return 0.0
        return inter_area / union_area

    def _compute_temporal_overlap(
        self,
        f1: Tuple[int, int],
        f2: Tuple[int, int],
    ) -> float:
        """Calculates 1D temporal frame intersection over union."""
        start = max(f1[0], f2[0])
        end = min(f1[1], f2[1])
        inter = max(0, end - start + 1)

        len1 = f1[1] - f1[0] + 1
        len2 = f2[1] - f2[0] + 1
        union = len1 + len2 - inter

        if union <= 0:
            return 0.0
        return inter / float(union)

    def _order_tasks_by_priority(
        self,
        tasks: List[SurgicalRepairTask],
    ) -> List[SurgicalRepairTask]:
        """Orders tasks: Previs reblock -> Inpainting / Full Regen -> Audio Remaster."""
        def sort_key(t: SurgicalRepairTask) -> Tuple[int, int, int]:
            # Hierarchy: Previs (1) -> Visual/Regen (2) -> Audio (3)
            if t.is_previs:
                type_rank = 1
            elif t.is_full_regen or t.is_inpainting:
                type_rank = 2
            else:
                type_rank = 3
            return (t.priority, type_rank, t.defect_severity.rank)

        return sorted(tasks, key=sort_key)

    def _estimate_compute_tier(self, tasks: List[SurgicalRepairTask]) -> ComputeTier:
        """Determines peak compute tier across all scheduled tasks."""
        if not tasks:
            return ComputeTier.TIER_0_NOOP
        if any(t.is_full_regen for t in tasks):
            return ComputeTier.TIER_4_FULL_REGEN
        if any(t.is_previs for t in tasks):
            return ComputeTier.TIER_3_PREVIS_REBLOCK
        if any(t.is_inpainting for t in tasks):
            return ComputeTier.TIER_2_REGIONAL_INPAINT
        if any(t.is_audio for t in tasks):
            return ComputeTier.TIER_1_AUDIO
        return ComputeTier.TIER_0_NOOP

    def _estimate_expected_latency(self, tasks: List[SurgicalRepairTask]) -> float:
        """Estimates total wall-clock repair turnaround latency in seconds."""
        if not tasks:
            return 0.0
        if any(t.is_full_regen for t in tasks):
            return 60.0

        latency = 0.0
        for t in tasks:
            if t.is_previs:
                latency += 18.0
            elif t.is_inpainting:
                latency += 8.5
            elif t.is_audio:
                latency += 1.2
        return round(latency, 2)
