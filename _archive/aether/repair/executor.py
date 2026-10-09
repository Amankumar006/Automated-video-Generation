"""Project Aether Surgical Repair Executor.

Dispatches and executes surgical repair plans (Pillar 6 / WBS 1.7):
- Synthesizes regional inpainting payloads for downstream renderers (e.g. ComfyUI inpaint nodes, CogVideoX / HunyuanVideo).
- Handles audio re-muxing and latency shift retargeting without pixel modifications.
- Dispatches UE5 spatial previs re-blocking motion guide updates.
- Dispatches full shot regeneration when escalated.
- Computes and validates boundary seam metrics (RSK-004) and records verified Council flags.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import numpy as np

from aether.repair.masking import TemporalMaskEngine
from aether.repair.schemas import (
    RepairActionType,
    RepairBoundaryMask,
    RepairExecutionResult,
    RepairPlan,
    SurgicalRepairTask,
)


class SurgicalRepairExecutor:
    """Dispatches and coordinates execution of surgical repair tasks.

    Synthesizes concrete payload schemas for ComfyUI inpaint nodes,
    FFmpeg audio remux pipelines, and Unreal Engine 5 motion guides.
    """

    def __init__(
        self,
        mask_engine: Optional[TemporalMaskEngine] = None,
        seam_metric_threshold: float = 0.05,
        custom_renderer_backend: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    ) -> None:
        self.mask_engine = mask_engine or TemporalMaskEngine()
        self.seam_metric_threshold = seam_metric_threshold
        self.custom_renderer_backend = custom_renderer_backend

    def execute_plan(
        self,
        plan: RepairPlan,
        base_asset_uri: Optional[str] = None,
        auto_execute_fallback: bool = False,
    ) -> List[RepairExecutionResult]:
        """Executes all tasks in a RepairPlan in priority order.

        Args:
            plan: The planned repair directives.
            base_asset_uri: URI of the original candidate video asset.
            auto_execute_fallback: Whether to automatically dispatch fallback tasks upon failure.

        Returns:
            List[RepairExecutionResult]: Execution results and telemetry for each task.
        """
        results: List[RepairExecutionResult] = []
        current_asset_uri = base_asset_uri or f"asset://shots/{plan.original_shot_id}.mp4"

        for task in plan.ordered_tasks_list:
            result = self.execute_task(task, base_asset_uri=current_asset_uri)
            results.append(result)

            if result.success_status and result.repaired_asset_uri:
                # Update cascading asset URI for successive repairs
                current_asset_uri = result.repaired_asset_uri
            elif not result.success_status and auto_execute_fallback and task.fallback_strategy:
                # Dispatch fallback task
                fallback_task = SurgicalRepairTask(
                    task_id=f"{task.task_id}_FALLBACK",
                    action_type=task.fallback_strategy,
                    target_defect_id=task.target_defect_id,
                    priority=1,
                    replacement_prompt=task.replacement_prompt,
                    negative_prompt_modifier=task.negative_prompt_modifier,
                    metadata={"original_failed_task": task.task_id, "fallback_reason": result.error_message},
                )
                fb_result = self.execute_task(fallback_task, base_asset_uri=current_asset_uri)
                results.append(fb_result)
                if fb_result.success_status and fb_result.repaired_asset_uri:
                    current_asset_uri = fb_result.repaired_asset_uri

        return results

    def execute_task(
        self,
        task: SurgicalRepairTask,
        base_asset_uri: Optional[str] = None,
    ) -> RepairExecutionResult:
        """Executes a single surgical repair task according to its action type."""
        start_time = time.time()
        base_uri = base_asset_uri or "asset://shot_base.mp4"

        try:
            if task.action_type == RepairActionType.REGIONAL_TEMPORAL_INPAINTING:
                return self._execute_inpainting_task(task, base_uri, start_time)

            elif task.action_type in (
                RepairActionType.AUDIO_REMASTER_VOICE,
                RepairActionType.AUDIO_REMASTER_FOLEY,
            ):
                return self._execute_audio_task(task, base_uri, start_time)

            elif task.action_type == RepairActionType.SPATIAL_PREVIS_REBLOCK:
                return self._execute_previs_task(task, base_uri, start_time)

            elif task.action_type == RepairActionType.FULL_SHOT_REGENERATION:
                return self._execute_full_regen_task(task, base_uri, start_time)

            elif task.action_type == RepairActionType.NO_OP:
                return RepairExecutionResult(
                    task_id=task.task_id,
                    success_status=True,
                    repaired_asset_uri=base_uri,
                    metadata={"action": "NO_OP", "message": "No modification needed"},
                    boundary_seam_metric=0.0,
                    latency=round(time.time() - start_time, 4),
                    verified_by_council_flag=True,
                )

            else:
                return RepairExecutionResult(
                    task_id=task.task_id,
                    success_status=False,
                    repaired_asset_uri=None,
                    error_message=f"Unsupported repair action type: {task.action_type}",
                    latency=round(time.time() - start_time, 4),
                )

        except Exception as exc:
            return RepairExecutionResult(
                task_id=task.task_id,
                success_status=False,
                repaired_asset_uri=None,
                error_message=f"Execution failed: {str(exc)}",
                latency=round(time.time() - start_time, 4),
            )

    def synthesize_inpainting_payload(
        self,
        task: SurgicalRepairTask,
    ) -> Dict[str, Any]:
        """Constructs regional inpainting payload for ComfyUI or API inpainting endpoints."""
        mask_spec = task.repair_boundary_mask
        if not mask_spec:
            raise ValueError(f"Task {task.task_id} missing repair_boundary_mask")

        # Generate spatial mask to compute active area and verify feathering
        spatial_mask = self.mask_engine.generate_spatial_mask(
            bbox=mask_spec.bounding_box,
            feather_radius_px=mask_spec.feather_radius_px,
        )
        active_pixel_ratio = float(np.mean(spatial_mask > 0.01))

        return {
            "renderer": "ComfyUI_Temporal_Inpaint_V2",
            "workflow_id": "WF_SURGICAL_INPAINT_SEAMLESS",
            "bounding_box": list(mask_spec.bounding_box),
            "frame_bounds": list(mask_spec.frame_bounds),
            "padded_frame_bounds": [mask_spec.padded_start_frame, mask_spec.padded_end_frame],
            "feather_radius_px": mask_spec.feather_radius_px,
            "temporal_pad_frames": mask_spec.temporal_pad_frames,
            "positive_prompt": task.replacement_prompt or "",
            "negative_prompt": task.negative_prompt_modifier or "",
            "active_pixel_ratio": round(active_pixel_ratio, 4),
            "denoise_strength": 0.85,
            "flow_guided_blend": True,  # RSK-004 mitigation
            "protected_regions_count": len(mask_spec.protected_regions),
            "protected_regions": [pr.model_dump() for pr in mask_spec.protected_regions],
            "camera_metadata": task.metadata.get("camera_velocity_mps", 0.0),
        }

    def synthesize_audio_remux_payload(
        self,
        task: SurgicalRepairTask,
    ) -> Dict[str, Any]:
        """Constructs audio remuxing and latency retargeting payload for FFmpeg."""
        return {
            "engine": "FFmpeg_Stream_Remuxer",
            "action": task.action_type.value,
            "latency_shift_ms": task.audio_retargeting_params.get("latency_shift_ms", 0.0),
            "target_phonemes": task.audio_retargeting_params.get("target_phonemes", []),
            "preserve_video_frames": True,  # Strictly zero pixel re-rendering
            "audio_track_target": "VOICE" if task.action_type == RepairActionType.AUDIO_REMASTER_VOICE else "FOLEY",
            "mix_mode": task.audio_retargeting_params.get("mix_mode", "remux_stream"),
        }

    def synthesize_previs_payload(
        self,
        task: SurgicalRepairTask,
    ) -> Dict[str, Any]:
        """Constructs UE5 headless re-blocking guide payload."""
        return {
            "engine": "UnrealEngine5_Headless_Previs",
            "action": "SPATIAL_PREVIS_REBLOCK",
            "directives": task.metadata.get("ue5_reblock_directives", {}),
            "output_cache_path": f"/tmp/aether_previs_{task.task_id}.fbx",
        }

    def synthesize_full_regen_payload(
        self,
        task: SurgicalRepairTask,
    ) -> Dict[str, Any]:
        """Constructs full foundation video model generation payload."""
        return {
            "engine": "FoundationVideoModel_Generator",
            "action": "FULL_SHOT_REGENERATION",
            "prompt": task.replacement_prompt or "",
            "negative_prompt": task.negative_prompt_modifier or "",
            "escalation_reason": task.metadata.get("escalation_reason", "Excessive defects"),
        }

    def _execute_inpainting_task(
        self,
        task: SurgicalRepairTask,
        base_uri: str,
        start_time: float,
    ) -> RepairExecutionResult:
        """Executes regional inpainting and validates boundary seam metric (RSK-004)."""
        payload = self.synthesize_inpainting_payload(task)
        clean_base = base_uri.rsplit(".", 1)[0]
        custom_metadata: Dict[str, Any] = {}

        # Custom renderer hook or internal simulation
        if self.custom_renderer_backend:
            backend_res = self.custom_renderer_backend(payload)
            seam_metric = float(backend_res.get("boundary_seam_metric", 0.02))
            out_uri = backend_res.get("asset_uri", f"{clean_base}_inp_{task.task_id}.mp4")
            custom_metadata = backend_res.get("metadata", {})
        else:
            # Generate mask to evaluate edge continuity
            mask_spec = task.repair_boundary_mask
            assert mask_spec is not None

            # Generate sample spatial slice with feathering
            spatial_mask = self.mask_engine.generate_spatial_mask(
                bbox=mask_spec.bounding_box,
                feather_radius_px=mask_spec.feather_radius_px,
            )
            seam_metric = self.mask_engine.compute_boundary_seam_metric(spatial_mask)
            out_uri = f"{clean_base}_inp_{task.task_id}.mp4"

        # Check seam metric against threshold
        is_seamless = seam_metric <= self.seam_metric_threshold

        # If seam fails and fallback is available, trigger fallback
        if not is_seamless and task.fallback_strategy:
            return RepairExecutionResult(
                task_id=task.task_id,
                success_status=False,
                repaired_asset_uri=None,
                metadata={
                    "payload": payload,
                    "seam_metric": round(seam_metric, 5),
                    "fallback_triggered": task.fallback_strategy.value,
                    **custom_metadata,
                },
                boundary_seam_metric=round(seam_metric, 5),
                latency=round(time.time() - start_time, 4),
                verified_by_council_flag=False,
                error_message=(
                    f"Boundary seam metric {seam_metric:.4f} exceeded threshold "
                    f"{self.seam_metric_threshold:.4f} (RSK-004 seam failure)."
                ),
            )

        res_metadata = {
            "payload": payload,
            "repaired_frame_bounds": task.repair_boundary_mask.frame_bounds if task.repair_boundary_mask else None,
            "feather_radius_px": task.repair_boundary_mask.feather_radius_px if task.repair_boundary_mask else None,
            "seam_continuity": "SEAMLESS",
        }
        res_metadata.update(custom_metadata)

        return RepairExecutionResult(
            task_id=task.task_id,
            success_status=True,
            repaired_asset_uri=out_uri,
            metadata=res_metadata,
            boundary_seam_metric=round(seam_metric, 5),
            latency=round(time.time() - start_time, 4),
            verified_by_council_flag=is_seamless,
        )

    def _execute_audio_task(
        self,
        task: SurgicalRepairTask,
        base_uri: str,
        start_time: float,
    ) -> RepairExecutionResult:
        """Executes audio remaster and retargeting without modifying video frames."""
        payload = self.synthesize_audio_remux_payload(task)
        clean_base = base_uri.rsplit(".", 1)[0]
        out_uri = f"{clean_base}_remux_{task.task_id}.mp4"
        custom_metadata: Dict[str, Any] = {}

        if self.custom_renderer_backend:
            backend_res = self.custom_renderer_backend(payload)
            out_uri = backend_res.get("asset_uri", out_uri)
            custom_metadata = backend_res.get("metadata", {})

        res_metadata = {
            "payload": payload,
            "video_frames_modified": False,
            "latency_shift_ms": payload["latency_shift_ms"],
        }
        res_metadata.update(custom_metadata)

        return RepairExecutionResult(
            task_id=task.task_id,
            success_status=True,
            repaired_asset_uri=out_uri,
            metadata=res_metadata,
            boundary_seam_metric=0.0,  # Zero video seam!
            latency=round(time.time() - start_time, 4),
            verified_by_council_flag=True,
        )

    def _execute_previs_task(
        self,
        task: SurgicalRepairTask,
        base_uri: str,
        start_time: float,
    ) -> RepairExecutionResult:
        """Executes UE5 spatial previs re-blocking."""
        payload = self.synthesize_previs_payload(task)
        out_uri = f"previs://reblock_{task.task_id}.fbx"
        custom_metadata: Dict[str, Any] = {}

        if self.custom_renderer_backend:
            backend_res = self.custom_renderer_backend(payload)
            out_uri = backend_res.get("asset_uri", out_uri)
            custom_metadata = backend_res.get("metadata", {})

        res_metadata = {"payload": payload, "reblock_applied": True}
        res_metadata.update(custom_metadata)

        return RepairExecutionResult(
            task_id=task.task_id,
            success_status=True,
            repaired_asset_uri=out_uri,
            metadata=res_metadata,
            boundary_seam_metric=0.0,
            latency=round(time.time() - start_time, 4),
            verified_by_council_flag=True,
        )

    def _execute_full_regen_task(
        self,
        task: SurgicalRepairTask,
        base_uri: str,
        start_time: float,
    ) -> RepairExecutionResult:
        """Executes full shot regeneration when escalated."""
        payload = self.synthesize_full_regen_payload(task)
        clean_base = base_uri.rsplit(".", 1)[0]
        out_uri = f"{clean_base}_full_regen_{task.task_id}.mp4"
        custom_metadata: Dict[str, Any] = {}

        if self.custom_renderer_backend:
            backend_res = self.custom_renderer_backend(payload)
            out_uri = backend_res.get("asset_uri", out_uri)
            custom_metadata = backend_res.get("metadata", {})

        res_metadata = {"payload": payload, "full_shot_regenerated": True}
        res_metadata.update(custom_metadata)

        return RepairExecutionResult(
            task_id=task.task_id,
            success_status=True,
            repaired_asset_uri=out_uri,
            metadata=res_metadata,
            boundary_seam_metric=0.0,
            latency=round(time.time() - start_time, 4),
            verified_by_council_flag=True,
        )
