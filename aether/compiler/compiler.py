"""Project Aether Shot Compiler.

Translates persistent scene graph states, state deltas, and spatial representation
packages into model-specific generation payloads for Google Veo 3.1, Kling 3.0,
Runway Gen-4.5, and open-weights CogVideoX / HunyuanVideo ComfyUI nodes (Pillar 4 / WBS 1.4).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple, Union

from aether.compiler.complexity import ComplexityPlanner
from aether.compiler.schemas import (
    ComplexityLevel,
    CompiledModelPayload,
    ComputeTier,
    ProviderTarget,
    ShotRequirement,
    SpatialRepresentationPackage,
)
from aether.state.schemas import (
    CameraState,
    CharacterState,
    EnvironmentState,
    PropState,
    SceneSnapshot,
    SceneState,
    StateDelta,
)


class ShotCompiler:
    """Translates abstract cinematic scene graphs into model-specific generation payloads."""

    def __init__(
        self,
        planner: Optional[ComplexityPlanner] = None,
        active_policy: Optional[Any] = None,
        default_enable_teacache: Optional[bool] = None,
        default_enable_pab: Optional[bool] = None,
        default_sampling_steps: Optional[int] = None,
        default_enable_speculative_draft: Optional[bool] = None,
    ) -> None:
        self._planner = planner or ComplexityPlanner()
        self.active_policy = active_policy
        self.default_enable_teacache = (
            default_enable_teacache
            if default_enable_teacache is not None
            else (getattr(active_policy, "enable_teacache", True) if active_policy else True)
        )
        self.default_enable_pab = (
            default_enable_pab
            if default_enable_pab is not None
            else (getattr(active_policy, "enable_pab", True) if active_policy else True)
        )
        self.default_sampling_steps = (
            default_sampling_steps
            if default_sampling_steps is not None
            else (getattr(active_policy, "sampling_steps", 8) if active_policy else 8)
        )
        self.default_enable_speculative_draft = (
            default_enable_speculative_draft
            if default_enable_speculative_draft is not None
            else (getattr(active_policy, "enable_speculative_draft", False) if active_policy else False)
        )

    # ----------------- PROVIDER COMPILERS -----------------

    def compile_for_veo(
        self,
        scene_state: Union[SceneState, SceneSnapshot, Any],
        shot_requirement: Optional[Union[ShotRequirement, Dict[str, Any]]] = None,
        state_delta: Optional[StateDelta] = None,
        spatial_package: Optional[SpatialRepresentationPackage] = None,
        complexity_level: Optional[Union[ComplexityLevel, int, str]] = None,
    ) -> CompiledModelPayload:
        """Compile shot into Google Veo 3.1 API payload with native audio flags and keyframe pairs."""
        state = self._extract_scene_state(scene_state)
        req = self._normalize_shot_requirement(shot_requirement)

        prompt = self._build_cinematic_prompt(state, req, state_delta)
        negative_prompt = (
            "low quality, cartoonish, 3d render look, blurry, oversaturated, "
            "morphing limbs, distorted fingers, flickering, inconsistent lighting, text watermark"
        )

        first_frame = (
            (spatial_package.photoreal_ref_uri if spatial_package else None)
            or (spatial_package.first_frame_uri if spatial_package else None)
            or (spatial_package.clay_render_uri if spatial_package else None)
            or req.first_frame_uri
            or req.metadata.get("first_frame_uri")
        )
        last_frame = (
            req.last_frame_uri
            or req.metadata.get("last_frame_uri")
            or (spatial_package.last_frame_uri if spatial_package else None)
            or (spatial_package.metadata.get("last_frame_uri") if spatial_package else None)
        )

        reference_images: List[str] = []
        if first_frame:
            reference_images.append(first_frame)
        if last_frame and last_frame not in reference_images:
            reference_images.append(last_frame)
        if spatial_package and spatial_package.photoreal_ref_uri and spatial_package.photoreal_ref_uri not in reference_images:
            reference_images.append(spatial_package.photoreal_ref_uri)

        active_cids = req.character_ids_involved or list(state.character_roster.keys())
        for cid in active_cids:
            char = state.get_character(cid)
            if char and "reference_image" in char.metadata:
                ref = char.metadata["reference_image"]
                if ref not in reference_images:
                    reference_images.append(ref)

        # Native audio flags
        generate_audio = bool(
            req.audio.dialogue
            or req.audio.foley
            or req.audio.score
            or req.audio.native_audio_requested
        )
        audio_components: List[str] = []
        if req.audio.dialogue:
            if req.audio.dialogue_transcript:
                audio_components.append(f'Spoken dialogue: "{req.audio.dialogue_transcript}"')
            else:
                audio_components.append("Synchronous high-fidelity character speech and dialogue")
        if req.audio.foley:
            if req.audio.foley_cues:
                audio_components.append(f"Foley sound events: {', '.join(req.audio.foley_cues)}")
            else:
                audio_components.append("Realistic environmental foley and spatial audio acoustics")
        if req.audio.score:
            if req.audio.score_mood:
                audio_components.append(f"Atmospheric score mood: {req.audio.score_mood}")
            else:
                audio_components.append("Cinematic musical score accompaniment")
        audio_prompt = ". ".join(audio_components) if audio_components else None

        camera_params = self._extract_camera_parameters(state, req, state_delta)

        provider_config = {
            "model": "veo-3.1",
            "aspect_ratio": req.aspect_ratio,
            "resolution": req.resolution,
            "duration_seconds": req.target_duration,
            "fps": 24,
            "generate_audio": generate_audio,
            "audio_prompt": audio_prompt,
            "prompt_enhancement": True,
            "person_generation": "allow_adult",
            "sampling_steps": req.sampling_steps,
            "enable_speculative_draft": req.enable_speculative_draft,
        }

        assigned_level = ComplexityLevel.from_val(complexity_level) if complexity_level is not None else None

        return CompiledModelPayload(
            shot_id=req.shot_id,
            provider_target=ProviderTarget.VEO_3_1,
            prompt=prompt,
            negative_prompt=negative_prompt,
            reference_images=reference_images,
            first_frame_uri=first_frame,
            last_frame_uri=last_frame,
            camera_motion_parameters=camera_params,
            provider_config=provider_config,
            required_compute_tier=ComputeTier.CLOUD_SERVERLESS,
            duration_seconds=req.target_duration,
            aspect_ratio=req.aspect_ratio,
            resolution=req.resolution,
            complexity_level=assigned_level,
            enable_teacache=req.enable_teacache,
            enable_pab=req.enable_pab,
            sampling_steps=req.sampling_steps,
            enable_speculative_draft=req.enable_speculative_draft,
            metadata={"compiler": "ShotCompiler", "target": "veo_3_1"},
        )

    def compile_for_kling(
        self,
        scene_state: Union[SceneState, SceneSnapshot, Any],
        shot_requirement: Optional[Union[ShotRequirement, Dict[str, Any]]] = None,
        state_delta: Optional[StateDelta] = None,
        spatial_package: Optional[SpatialRepresentationPackage] = None,
        complexity_level: Optional[Union[ComplexityLevel, int, str]] = None,
    ) -> CompiledModelPayload:
        """Compile shot into Kling 3.0 payload with dynamic motion brush and lip-sync audio track."""
        state = self._extract_scene_state(scene_state)
        req = self._normalize_shot_requirement(shot_requirement)

        prompt = self._build_cinematic_prompt(state, req, state_delta)
        negative_prompt = (
            "blur, distortion, low resolution, bad anatomy, deformed limbs, "
            "missing fingers, inconsistent identity, temporal jitter"
        )

        first_frame = (
            (spatial_package.photoreal_ref_uri if spatial_package else None)
            or (spatial_package.first_frame_uri if spatial_package else None)
            or (spatial_package.clay_render_uri if spatial_package else None)
            or req.first_frame_uri
            or req.metadata.get("first_frame_uri")
        )
        last_frame = (
            req.last_frame_uri
            or req.metadata.get("last_frame_uri")
            or (spatial_package.last_frame_uri if spatial_package else None)
            or (spatial_package.metadata.get("last_frame_uri") if spatial_package else None)
        )

        active_cids = req.character_ids_involved or list(state.character_roster.keys())
        reference_images: List[str] = []
        if first_frame:
            reference_images.append(first_frame)
        if last_frame and last_frame not in reference_images:
            reference_images.append(last_frame)
        if spatial_package and spatial_package.photoreal_ref_uri and spatial_package.photoreal_ref_uri not in reference_images:
            reference_images.append(spatial_package.photoreal_ref_uri)
        for cid in active_cids:
            char = state.get_character(cid)
            if char and "reference_image" in char.metadata:
                ref = char.metadata["reference_image"]
                if ref not in reference_images:
                    reference_images.append(ref)

        # Motion brush & element tracking list
        element_tracking: List[Dict[str, Any]] = []
        if spatial_package and spatial_package.segmentation_masks:
            for entity_id, mask_uri in spatial_package.segmentation_masks.items():
                trajectory = [0.0, 0.0]
                if state_delta and state_delta.character_deltas and entity_id in state_delta.character_deltas:
                    cd = state_delta.character_deltas[entity_id]
                    if cd.position_delta and len(cd.position_delta) >= 2:
                        trajectory = [round(cd.position_delta[0], 2), round(cd.position_delta[1], 2)]
                element_tracking.append({
                    "element_id": entity_id,
                    "mask_uri": mask_uri,
                    "brush_mode": "dynamic_mask",
                    "motion_trajectory": trajectory,
                    "weight": 0.85,
                })
        elif state_delta and state_delta.character_deltas:
            for cid, cd in state_delta.character_deltas.items():
                if cd.distance_moved > 0.01:
                    element_tracking.append({
                        "element_id": cid,
                        "brush_mode": "element_tracking",
                        "trajectory_vector": cd.position_delta,
                        "distance_moved": round(cd.distance_moved, 2),
                        "velocity_mps": round(cd.velocity_mps, 2),
                        "weight": 0.80,
                    })
        else:
            for cid in active_cids:
                element_tracking.append({
                    "element_id": cid,
                    "brush_mode": "auto_detect",
                    "weight": 0.70,
                })

        # Lip-sync audio setup
        target_char_id = (
            req.metadata.get("speaker_id")
            or req.metadata.get("target_character_id")
            or (active_cids[0] if active_cids else None)
        )
        lip_sync_config = {
            "enabled": req.has_dialogue,
            "audio_uri": req.audio.dialogue_audio_uri,
            "transcript": req.audio.dialogue_transcript,
            "target_character_id": target_char_id,
            "voice_match": True,
        }

        # Kling pro modes: 5s or 10s
        duration_mode = 10.0 if req.target_duration > 5.0 else 5.0

        camera_params = self._extract_camera_parameters(state, req, state_delta)

        provider_config = {
            "model_version": "kling-v3-0",
            "mode": "pro",
            "duration": duration_mode,
            "target_duration_requested": req.target_duration,
            "aspect_ratio": req.aspect_ratio,
            "motion_brush_elements": element_tracking,
            "lip_sync": lip_sync_config,
            "cfg_scale": 0.5,
            "sampling_steps": req.sampling_steps,
            "enable_speculative_draft": req.enable_speculative_draft,
        }

        assigned_level = ComplexityLevel.from_val(complexity_level) if complexity_level is not None else None

        return CompiledModelPayload(
            shot_id=req.shot_id,
            provider_target=ProviderTarget.KLING_3_0,
            prompt=prompt,
            negative_prompt=negative_prompt,
            reference_images=reference_images,
            first_frame_uri=first_frame,
            last_frame_uri=last_frame,
            camera_motion_parameters=camera_params,
            provider_config=provider_config,
            required_compute_tier=ComputeTier.PREMIUM,
            duration_seconds=req.target_duration,
            aspect_ratio=req.aspect_ratio,
            resolution=req.resolution,
            complexity_level=assigned_level,
            enable_teacache=req.enable_teacache,
            enable_pab=req.enable_pab,
            sampling_steps=req.sampling_steps,
            enable_speculative_draft=req.enable_speculative_draft,
            metadata={"compiler": "ShotCompiler", "target": "kling_3_0"},
        )

    def compile_for_runway(
        self,
        scene_state: Union[SceneState, SceneSnapshot, Any],
        shot_requirement: Optional[Union[ShotRequirement, Dict[str, Any]]] = None,
        state_delta: Optional[StateDelta] = None,
        spatial_package: Optional[SpatialRepresentationPackage] = None,
        complexity_level: Optional[Union[ComplexityLevel, int, str]] = None,
    ) -> CompiledModelPayload:
        """Compile shot into Runway Gen-4.5 payload with Director Mode camera syntax."""
        state = self._extract_scene_state(scene_state)
        req = self._normalize_shot_requirement(shot_requirement)

        base_prompt = self._build_cinematic_prompt(state, req, state_delta)
        director_mode, director_syntax = self._generate_runway_director_mode(state, req, state_delta)

        # Embed Director Mode camera syntax in prompt
        compiled_prompt = f"{director_syntax} {base_prompt}".strip()
        negative_prompt = (
            "grainy, pixelated, oversaturated, morphing, unnatural physics, "
            "double exposure, jittery camera shake, deformed facial features"
        )

        first_frame = (
            (spatial_package.photoreal_ref_uri if spatial_package else None)
            or (spatial_package.first_frame_uri if spatial_package else None)
            or (spatial_package.clay_render_uri if spatial_package else None)
            or req.first_frame_uri
            or req.metadata.get("first_frame_uri")
        )
        last_frame = (
            req.last_frame_uri
            or req.metadata.get("last_frame_uri")
            or (spatial_package.last_frame_uri if spatial_package else None)
            or (spatial_package.metadata.get("last_frame_uri") if spatial_package else None)
        )

        active_cids = req.character_ids_involved or list(state.character_roster.keys())
        reference_images: List[str] = []
        if first_frame:
            reference_images.append(first_frame)
        if last_frame and last_frame not in reference_images:
            reference_images.append(last_frame)
        if spatial_package and spatial_package.photoreal_ref_uri and spatial_package.photoreal_ref_uri not in reference_images:
            reference_images.append(spatial_package.photoreal_ref_uri)
        for cid in active_cids:
            char = state.get_character(cid)
            if char and "reference_image" in char.metadata:
                ref = char.metadata["reference_image"]
                if ref not in reference_images:
                    reference_images.append(ref)

        camera_params = self._extract_camera_parameters(state, req, state_delta)
        camera_params["runway_director_mode"] = director_mode

        provider_config = {
            "model": "gen4.5",
            "director_mode": director_mode,
            "camera_command_syntax": director_syntax,
            "director_syntax": director_syntax,
            "aspect_ratio": req.aspect_ratio,
            "duration": req.target_duration,
            "motion_score": min(10.0, max(1.0, req.camera_velocity_mps * 2.0 or 5.0)),
            "watermark": False,
            "sampling_steps": req.sampling_steps,
            "enable_speculative_draft": req.enable_speculative_draft,
        }

        assigned_level = ComplexityLevel.from_val(complexity_level) if complexity_level is not None else None

        return CompiledModelPayload(
            shot_id=req.shot_id,
            provider_target=ProviderTarget.RUNWAY_GEN_4_5,
            prompt=compiled_prompt,
            negative_prompt=negative_prompt,
            reference_images=reference_images,
            first_frame_uri=first_frame,
            last_frame_uri=last_frame,
            camera_motion_parameters=camera_params,
            provider_config=provider_config,
            required_compute_tier=ComputeTier.PREMIUM,
            duration_seconds=req.target_duration,
            aspect_ratio=req.aspect_ratio,
            resolution=req.resolution,
            complexity_level=assigned_level,
            enable_teacache=req.enable_teacache,
            enable_pab=req.enable_pab,
            sampling_steps=req.sampling_steps,
            enable_speculative_draft=req.enable_speculative_draft,
            metadata={"compiler": "ShotCompiler", "target": "runway_gen_4_5"},
        )

    def compile_for_comfyui(
        self,
        scene_state: Union[SceneState, SceneSnapshot, Any],
        shot_requirement: Optional[Union[ShotRequirement, Dict[str, Any]]] = None,
        state_delta: Optional[StateDelta] = None,
        spatial_package: Optional[SpatialRepresentationPackage] = None,
        complexity_level: Optional[Union[ComplexityLevel, int, str]] = None,
    ) -> CompiledModelPayload:
        """Compile shot into open-weights CogVideoX / HunyuanVideo ComfyUI ControlNet payload."""
        state = self._extract_scene_state(scene_state)
        req = self._normalize_shot_requirement(shot_requirement)

        prompt = self._build_cinematic_prompt(state, req, state_delta)
        negative_prompt = (
            "deformed, bad anatomy, bad limbs, motion blur, noisy, low resolution, "
            "overexposed, underexposed, bad proportions, unnatural limb orientation"
        )

        # ControlNet mapping
        controlnet_configs: List[Dict[str, Any]] = []
        if spatial_package:
            if spatial_package.depth_map_uri:
                controlnet_configs.append({
                    "node_type": "ControlNetApplyDepth",
                    "control_type": "depth",
                    "image_uri": spatial_package.depth_map_uri,
                    "strength": 0.85,
                    "start_percent": 0.0,
                    "end_percent": 1.0,
                })
            if spatial_package.surface_normals_uri:
                controlnet_configs.append({
                    "node_type": "ControlNetApplySurfaceNormals",
                    "control_type": "surface_normals",
                    "image_uri": spatial_package.surface_normals_uri,
                    "strength": 0.75,
                    "start_percent": 0.0,
                    "end_percent": 0.85,
                })
            if spatial_package.clay_render_uri:
                controlnet_configs.append({
                    "node_type": "ControlNetApplyCanny",
                    "control_type": "canny",
                    "image_uri": spatial_package.clay_render_uri,
                    "strength": 0.70,
                    "start_percent": 0.0,
                    "end_percent": 0.80,
                })
            if spatial_package.skeleton_pose_metadata:
                controlnet_configs.append({
                    "node_type": "ControlNetApplyOpenPose",
                    "control_type": "openpose",
                    "pose_metadata": spatial_package.skeleton_pose_metadata,
                    "strength": 0.90,
                    "start_percent": 0.0,
                    "end_percent": 1.0,
                })
            if spatial_package.motion_vectors_uri:
                controlnet_configs.append({
                    "node_type": "OpticalFlowGuidance",
                    "control_type": "optical_flow",
                    "flow_uri": spatial_package.motion_vectors_uri,
                    "strength": 0.80,
                    "start_percent": 0.0,
                    "end_percent": 1.0,
                })

        # Calculate latent dimensions
        latent_dims = self._calculate_latent_dimensions(req.resolution, req.aspect_ratio, req.target_duration)

        # Character LoRAs for active actors
        active_cids = req.character_ids_involved or list(state.character_roster.keys())
        lora_weights: List[Dict[str, Any]] = []
        for cid in active_cids:
            char = state.get_character(cid)
            lora_name = char.metadata.get("lora_name", f"lora_char_{cid}") if char else f"lora_char_{cid}"
            lora_strength = float(char.metadata.get("lora_strength", 0.85)) if char else 0.85
            lora_weights.append({
                "lora_name": lora_name,
                "character_id": cid,
                "strength_model": lora_strength,
                "strength_clip": lora_strength,
            })

        # Base model determination (CogVideoX vs HunyuanVideo)
        base_model_name = req.metadata.get("base_model") or req.metadata.get("model") or "CogVideoX-5B"

        # ComfyUI Workflow Graph
        workflow_graph = self._build_comfyui_workflow_graph(
            prompt=prompt,
            negative_prompt=negative_prompt,
            latent_dims=latent_dims,
            controlnet_configs=controlnet_configs,
            lora_weights=lora_weights,
            base_model=base_model_name,
            enable_teacache=req.enable_teacache,
            enable_pab=req.enable_pab,
            sampling_steps=req.sampling_steps,
        )

        camera_params = self._extract_camera_parameters(state, req, state_delta)
        if spatial_package and spatial_package.camera_trajectory_path:
            camera_params["trajectory_curve_path"] = spatial_package.camera_trajectory_path

        first_frame = (
            (spatial_package.photoreal_ref_uri if spatial_package else None)
            or (spatial_package.first_frame_uri if spatial_package else None)
            or (spatial_package.clay_render_uri if spatial_package else None)
            or req.first_frame_uri
            or req.metadata.get("first_frame_uri")
        )
        last_frame = (
            req.last_frame_uri
            or req.metadata.get("last_frame_uri")
            or (spatial_package.last_frame_uri if spatial_package else None)
            or (spatial_package.metadata.get("last_frame_uri") if spatial_package else None)
        )

        reference_images: List[str] = []
        if first_frame:
            reference_images.append(first_frame)
        if last_frame and last_frame not in reference_images:
            reference_images.append(last_frame)
        if spatial_package and spatial_package.photoreal_ref_uri and spatial_package.photoreal_ref_uri not in reference_images:
            reference_images.append(spatial_package.photoreal_ref_uri)
        for cid in active_cids:
            char = state.get_character(cid)
            if char and "reference_image" in char.metadata:
                ref = char.metadata["reference_image"]
                if ref not in reference_images:
                    reference_images.append(ref)

        provider_config = {
            "base_model": base_model_name,
            "enable_teacache": req.enable_teacache,
            "enable_pab": req.enable_pab,
            "sampling_steps": req.sampling_steps,
            "enable_speculative_draft": req.enable_speculative_draft,
            "controlnet_configs": controlnet_configs,
            "latent_dimensions": latent_dims,
            "lora_weights": lora_weights,
            "comfyui_workflow": workflow_graph,
            "workflow_graph": workflow_graph,
            "sampler_settings": {
                "steps": req.sampling_steps,
                "cfg": 7.0,
                "sampler_name": "euler_ancestral",
                "scheduler": "karras",
            },
        }

        assigned_level = ComplexityLevel.from_val(complexity_level) if complexity_level is not None else None

        return CompiledModelPayload(
            shot_id=req.shot_id,
            provider_target=ProviderTarget.COGVIDEOX_COMFYUI,
            prompt=prompt,
            negative_prompt=negative_prompt,
            reference_images=reference_images,
            first_frame_uri=first_frame,
            last_frame_uri=last_frame,
            camera_motion_parameters=camera_params,
            provider_config=provider_config,
            required_compute_tier=ComputeTier.DEDICATED_A100,
            duration_seconds=req.target_duration,
            aspect_ratio=req.aspect_ratio,
            resolution=req.resolution,
            complexity_level=assigned_level,
            enable_teacache=req.enable_teacache,
            enable_pab=req.enable_pab,
            sampling_steps=req.sampling_steps,
            enable_speculative_draft=req.enable_speculative_draft,
            metadata={"compiler": "ShotCompiler", "target": "cogvideox_comfyui"},
        )

    def compile_auto(
        self,
        scene_state: Union[SceneState, SceneSnapshot, Any],
        shot_requirement: Optional[Union[ShotRequirement, Dict[str, Any]]] = None,
        state_delta: Optional[StateDelta] = None,
        spatial_package: Optional[SpatialRepresentationPackage] = None,
        complexity_level: Optional[Union[ComplexityLevel, int, str]] = None,
        preferred_provider: Optional[Union[ProviderTarget, str]] = None,
    ) -> CompiledModelPayload:
        """Automatically routes and compiles based on ComplexityLevel and shot requirements."""
        state = self._extract_scene_state(scene_state)
        req = self._normalize_shot_requirement(shot_requirement)

        # Evaluate complexity level if not explicitly provided
        if complexity_level is None:
            plan = self._planner.plan(state, req, state_delta, spatial_package)
            level = plan.complexity_level
        else:
            level = ComplexityLevel.from_val(complexity_level)

        # User override preferred provider
        if preferred_provider:
            target = ProviderTarget.from_val(preferred_provider)
            if target == ProviderTarget.VEO_3_1:
                payload = self.compile_for_veo(state, req, state_delta, spatial_package, complexity_level=level)
            elif target == ProviderTarget.KLING_3_0:
                payload = self.compile_for_kling(state, req, state_delta, spatial_package, complexity_level=level)
            elif target == ProviderTarget.RUNWAY_GEN_4_5:
                payload = self.compile_for_runway(state, req, state_delta, spatial_package, complexity_level=level)
            elif target == ProviderTarget.COGVIDEOX_COMFYUI:
                payload = self.compile_for_comfyui(state, req, state_delta, spatial_package, complexity_level=level)
            else:
                raise ValueError(f"Unknown preferred provider: {preferred_provider}")
            payload.complexity_level = level
            return payload

        # Route by level and empirical capability
        if level == ComplexityLevel.PROMPT_ONLY:
            payload = self.compile_for_veo(state, req, state_delta, spatial_package, complexity_level=level)
        elif level == ComplexityLevel.REFERENCE_IMAGE:
            payload = self.compile_for_runway(state, req, state_delta, spatial_package, complexity_level=level)
        elif level == ComplexityLevel.KEYFRAMES_INTERPOLATION:
            payload = self.compile_for_veo(state, req, state_delta, spatial_package, complexity_level=level)
        elif level == ComplexityLevel.TWOD_TRAJECTORY_POSE:
            if req.has_dialogue:
                payload = self.compile_for_kling(state, req, state_delta, spatial_package, complexity_level=level)
            else:
                payload = self.compile_for_veo(state, req, state_delta, spatial_package, complexity_level=level)
        elif level == ComplexityLevel.THREED_BLOCKING:
            if spatial_package and not spatial_package.is_empty:
                payload = self.compile_for_comfyui(state, req, state_delta, spatial_package, complexity_level=level)
            else:
                payload = self.compile_for_runway(state, req, state_delta, spatial_package, complexity_level=level)
        elif level == ComplexityLevel.FULL_PHYSICAL_SIMULATION:
            payload = self.compile_for_comfyui(state, req, state_delta, spatial_package, complexity_level=level)
        else:
            payload = self.compile_for_veo(state, req, state_delta, spatial_package, complexity_level=level)

        payload.complexity_level = level
        return payload

    # ----------------- PRIVATE HELPER METHODS -----------------

    def _extract_scene_state(self, scene_state_or_snapshot: Any) -> SceneState:
        """Extract SceneState from wrapper."""
        if hasattr(scene_state_or_snapshot, "active_state"):
            return scene_state_or_snapshot.active_state
        if hasattr(scene_state_or_snapshot, "state"):
            return scene_state_or_snapshot.state
        if isinstance(scene_state_or_snapshot, SceneState):
            return scene_state_or_snapshot
        if isinstance(scene_state_or_snapshot, dict):
            return SceneState(**scene_state_or_snapshot)
        raise ValueError(f"Unsupported scene state input: {type(scene_state_or_snapshot)}")

    def _normalize_shot_requirement(
        self,
        req: Optional[Union[ShotRequirement, Dict[str, Any]]],
    ) -> ShotRequirement:
        """Normalize shot requirement, applying compiler efficiency defaults if not explicitly specified."""
        if req is None:
            return ShotRequirement(
                enable_teacache=self.default_enable_teacache,
                enable_pab=self.default_enable_pab,
                sampling_steps=self.default_sampling_steps,
                enable_speculative_draft=self.default_enable_speculative_draft,
            )
        if isinstance(req, dict):
            d = dict(req)
            if "enable_teacache" not in d and "teacache" not in d:
                d["enable_teacache"] = self.default_enable_teacache
            if "enable_pab" not in d and "pab" not in d:
                d["enable_pab"] = self.default_enable_pab
            if "sampling_steps" not in d and "steps" not in d and "num_steps" not in d:
                d["sampling_steps"] = self.default_sampling_steps
            if "enable_speculative_draft" not in d and "speculative" not in d and "speculative_draft" not in d:
                d["enable_speculative_draft"] = self.default_enable_speculative_draft
            return ShotRequirement(**d)
        if isinstance(req, ShotRequirement):
            return req
        raise ValueError(f"Unsupported shot requirement: {type(req)}")

    def _build_cinematic_prompt(
        self,
        state: SceneState,
        req: ShotRequirement,
        delta: Optional[StateDelta],
    ) -> str:
        """Build rich cinematic prompt incorporating location, environment, lighting, characters, and optics."""
        parts: List[str] = []

        # 1. Location & Setting
        parts.append(f"Cinematic {state.timestamp} film scene inside {state.location.replace('_', ' ')}.")

        # 2. Environment, Weather & Lighting
        env = state.environment
        env_desc = f"Atmosphere: {env.weather} weather with {env.lighting.replace('_', ' ')} lighting."
        if env.particulates:
            env_desc += f" Volumetric {env.particulates.replace('_', ' ')} drifting through frame."
        if env.wetness > 0.0:
            env_desc += f" Surfaces exhibit wetness ({int(env.wetness * 100)}% moisture)"
            if env.reflections:
                env_desc += " with sharp specular ground reflections."
            else:
                env_desc += "."
        parts.append(env_desc)

        # 2b. Environment Shifts / Transitions from StateDelta
        if delta and delta.environment_delta:
            ed = delta.environment_delta
            if ed.lighting_transition:
                parts.append(f"Lighting transitions from {ed.lighting_transition[0]} to {ed.lighting_transition[1]}.")
            if ed.weather_transition:
                parts.append(f"Weather shifts from {ed.weather_transition[0]} to {ed.weather_transition[1]}.")
            if ed.particulates_transition and ed.particulates_transition[1]:
                parts.append(f"Particulates transition to {ed.particulates_transition[1]}.")
            if abs(ed.wetness_delta) > 0.05:
                parts.append(f"Surface moisture shift delta: {ed.wetness_delta:+.2f}.")

        # 3. Optics & Camera
        if state.active_camera:
            cam = state.active_camera
            optics_str = f"Shot on {cam.lens_focal_length_mm:.0f}mm lens, f/{cam.aperture:.1f} aperture, focus plane at {cam.focus_distance:.1f}m."
            parts.append(optics_str)
        if req.target_focal_intent:
            parts.append(f"Focal intent: {req.target_focal_intent}.")
        if req.camera_movement:
            parts.append(f"Camera kinematic movement: {req.camera_movement.replace('_', ' ')}.")

        # 4. Characters, Wardrobe, Eyelines, Injuries, Props
        active_cids = req.character_ids_involved or list(state.character_roster.keys())
        for cid in active_cids:
            char = state.get_character(cid)
            if not char:
                char_name = cid.replace('_', ' ').title()
                parts.append(f"Featuring character {char_name} (ID: {cid}).")
                continue
            char_name = char.name or char.character_id.title()
            pos = char.position if (char.position and len(char.position) >= 3) else [0.0, 0.0, 0.0]
            eyeline = char.eyeline_vector if (char.eyeline_vector and len(char.eyeline_vector) >= 3) else [0.0, 0.0, 1.0]
            char_desc = (
                f"{char_name} positioned at [{pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}], "
                f"facing {char.facing_angle:.0f} degrees, eyeline oriented along [{eyeline[0]:.2f}, {eyeline[1]:.2f}, {eyeline[2]:.2f}]. "
                f"Emotional micro-expression: {char.emotional_state.replace('_', ' ')}."
            )

            # Delta momentum / transition for character
            if delta and delta.character_deltas and cid in delta.character_deltas:
                cd = delta.character_deltas[cid]
                if cd.emotional_transition:
                    char_desc += f" Emotional shift: from {cd.emotional_transition[0]} to {cd.emotional_transition[1]}."
                if cd.distance_moved > 0.01:
                    char_desc += f" Momentum: traversed {cd.distance_moved:.2f}m."

            # Wardrobe
            if char.wardrobe:
                w_items = []
                for slot, item in char.wardrobe.items():
                    item_state_str = f"{slot} '{item.id}' ({item.state.replace('_', ' ')}"
                    if item.damage_level > 0.0:
                        item_state_str += f", damage {int(item.damage_level * 100)}%"
                    item_state_str += ")"
                    w_items.append(item_state_str)
                char_desc += f" Wardrobe: {', '.join(w_items)}."

            # Injuries
            if char.injuries:
                injuries_str = ", ".join(inj.replace("_", " ") for inj in char.injuries)
                char_desc += f" Visible physical trauma / injuries: {injuries_str}."

            # Held Props
            if char.held_props:
                props_held = []
                for slot, pid in char.held_props.items():
                    p = state.get_prop(pid)
                    p_name = p.name if p else pid.replace("_", " ")
                    props_held.append(f"{p_name} in {slot} hand")
                char_desc += f" Holding {', '.join(props_held)}."

            parts.append(char_desc)

        # 4b. Actions applied from StateDelta
        if delta and delta.actions_applied:
            act_names = []
            for act in delta.actions_applied:
                act_str = act.action_type.value if hasattr(act.action_type, "value") else str(act.action_type)
                act_names.append(act_str.replace("_", " "))
            if act_names:
                parts.append(f"Action context: {', '.join(act_names)}.")

        # 5. Narrative Emotional Beat & Physical Phenomena
        if req.emotional_beat:
            parts.append(f"Dramatic beat: {req.emotional_beat}.")
        if req.physical_challenges:
            parts.append(f"Physical elements: {', '.join(pc.replace('_', ' ') for pc in req.physical_challenges)}.")

        # 6. Cinematic Master Quality Tag
        parts.append("Master cinematography, photorealistic 8k, 35mm film stock, Arri Alexa LF color grading.")

        return " ".join(parts)

    def _extract_camera_parameters(
        self,
        state: SceneState,
        req: ShotRequirement,
        delta: Optional[StateDelta],
    ) -> Dict[str, Any]:
        """Extract camera kinematics, focal length, aperture, and delta trajectories."""
        params: Dict[str, Any] = {
            "movement": req.camera_movement or "static",
            "velocity_mps": req.camera_velocity_mps,
        }
        if state.active_camera:
            cam = state.active_camera
            params.update({
                "lens_focal_length_mm": cam.lens_focal_length_mm,
                "aperture": cam.aperture,
                "focus_distance": cam.focus_distance,
                "position": cam.position,
                "eyeline_vector": cam.eyeline_vector,
            })
        if delta and delta.camera_delta:
            cd = delta.camera_delta
            params["delta"] = {
                "distance_moved": cd.distance_moved,
                "position_delta": cd.position_delta,
                "focal_length_delta": cd.focal_length_delta,
            }
        return params

    def _generate_runway_director_mode(
        self,
        state: SceneState,
        req: ShotRequirement,
        delta: Optional[StateDelta],
    ) -> Tuple[Dict[str, float], str]:
        """Calculates Runway Director Mode camera controls [-10 to +10] and formatted command syntax."""
        director_mode: Dict[str, float] = {
            "pan": 0.0,
            "tilt": 0.0,
            "zoom": 0.0,
            "roll": 0.0,
            "truck": 0.0,
            "pedestal": 0.0,
        }

        # Check for explicit manual override in metadata
        if req.metadata:
            dm_override = req.metadata.get("director_mode") or req.metadata.get("runway_director_mode")
            if isinstance(dm_override, dict):
                for k, v in dm_override.items():
                    if k in director_mode:
                        director_mode[k] = round(float(v), 1)

        m = (req.camera_movement or "").lower().replace("_", " ").strip()
        vel = max(req.camera_velocity_mps, 1.0)
        scale = min(10.0, vel * 1.5)

        # Semantic mappings
        if "pan right" in m:
            director_mode["pan"] = round(scale, 1)
        elif "pan left" in m:
            director_mode["pan"] = round(-scale, 1)
        elif "pan" in m and director_mode["pan"] == 0.0:
            director_mode["pan"] = round(scale, 1)

        if "tilt up" in m:
            director_mode["tilt"] = round(scale, 1)
        elif "tilt down" in m:
            director_mode["tilt"] = round(-scale, 1)
        elif "tilt" in m and director_mode["tilt"] == 0.0:
            director_mode["tilt"] = round(scale, 1)

        if "zoom in" in m or "dolly in" in m:
            director_mode["zoom"] = round(scale, 1)
        elif "zoom out" in m or "dolly out" in m:
            director_mode["zoom"] = round(-scale, 1)
        elif ("zoom" in m or "dolly" in m) and director_mode["zoom"] == 0.0:
            director_mode["zoom"] = round(scale, 1)

        if "truck right" in m:
            director_mode["truck"] = round(scale, 1)
        elif "truck left" in m:
            director_mode["truck"] = round(-scale, 1)
        elif "truck" in m and director_mode["truck"] == 0.0:
            director_mode["truck"] = round(scale, 1)

        if "pedestal up" in m or "crane up" in m or "crane" in m or "pedestal" in m:
            director_mode["pedestal"] = round(scale, 1)
        elif "pedestal down" in m or "crane down" in m:
            director_mode["pedestal"] = round(-scale, 1)

        if "roll cw" in m or "roll clockwise" in m or "roll" in m:
            director_mode["roll"] = round(scale, 1)
        elif "roll ccw" in m or "roll counter_clockwise" in m or "roll counterclockwise" in m:
            director_mode["roll"] = round(-scale, 1)

        # Enhance with delta if present
        if delta and delta.camera_delta:
            cd = delta.camera_delta
            if cd.position_delta and len(cd.position_delta) == 3:
                dx, dy, dz = cd.position_delta
                if abs(dx) > 0.01 and director_mode["truck"] == 0.0:
                    director_mode["truck"] = round(min(10.0, max(-10.0, dx * 2.0)), 1)
                if abs(dy) > 0.01 and director_mode["pedestal"] == 0.0:
                    director_mode["pedestal"] = round(min(10.0, max(-10.0, dy * 2.0)), 1)
                if abs(dz) > 0.01 and director_mode["zoom"] == 0.0:
                    director_mode["zoom"] = round(min(10.0, max(-10.0, dz * 2.0)), 1)
            # Map focal length delta to zoom if zoom is still 0
            if getattr(cd, "focal_length_delta", 0.0) != 0.0 and director_mode["zoom"] == 0.0:
                f_delta = cd.focal_length_delta
                director_mode["zoom"] = round(min(10.0, max(-10.0, f_delta * 0.2)), 1)

        # Generate syntax string e.g. [Camera: Pan Right +3.0, Dolly In +2.5]
        syntax_terms: List[str] = []
        if director_mode["pan"] != 0.0:
            dir_str = "Right" if director_mode["pan"] > 0 else "Left"
            syntax_terms.append(f"Pan {dir_str} {director_mode['pan']:+.1f}")
        if director_mode["tilt"] != 0.0:
            dir_str = "Up" if director_mode["tilt"] > 0 else "Down"
            syntax_terms.append(f"Tilt {dir_str} {director_mode['tilt']:+.1f}")
        if director_mode["zoom"] != 0.0:
            dir_str = "In" if director_mode["zoom"] > 0 else "Out"
            syntax_terms.append(f"Zoom {dir_str} {director_mode['zoom']:+.1f}")
        if director_mode["truck"] != 0.0:
            dir_str = "Right" if director_mode["truck"] > 0 else "Left"
            syntax_terms.append(f"Truck {dir_str} {director_mode['truck']:+.1f}")
        if director_mode["pedestal"] != 0.0:
            dir_str = "Up" if director_mode["pedestal"] > 0 else "Down"
            syntax_terms.append(f"Pedestal {dir_str} {director_mode['pedestal']:+.1f}")
        if director_mode["roll"] != 0.0:
            dir_str = "CW" if director_mode["roll"] > 0 else "CCW"
            syntax_terms.append(f"Roll {dir_str} {director_mode['roll']:+.1f}")

        if not syntax_terms:
            syntax_str = "[Camera: Static]"
        else:
            syntax_str = f"[Camera: {', '.join(syntax_terms)}]"

        return director_mode, syntax_str

    def _calculate_latent_dimensions(
        self,
        resolution: str,
        aspect_ratio: str,
        duration: float,
    ) -> Dict[str, int]:
        """Compute pixel and VAE latent tensor dimensions for CogVideoX/Hunyuan."""
        res_low = resolution.lower()
        if "4k" in res_low or "2160" in res_low:
            base_w, base_h = 3840, 2160
        elif "2k" in res_low or "1440" in res_low:
            base_w, base_h = 2560, 1440
        elif "720" in res_low:
            base_w, base_h = 1280, 720
        elif "480" in res_low or "sd" in res_low:
            base_w, base_h = 856, 480
        else:
            base_w, base_h = 1920, 1080

        # Adjust for aspect ratio
        if aspect_ratio == "9:16":
            width, height = base_h, base_w
        elif aspect_ratio == "1:1":
            dim = min(base_w, base_h)
            width, height = dim, dim
        elif aspect_ratio == "4:3":
            width = int(base_h * 4 / 3)
            height = base_h
        elif aspect_ratio == "3:4":
            width = int(base_w * 3 / 4)
            height = base_w
        elif aspect_ratio in ("21:9", "2.39:1"):
            width = base_w
            if aspect_ratio == "21:9":
                height = int(base_w * 9 / 21)
            else:
                height = int(base_w / 2.39)
        else:
            width, height = base_w, base_h

        # Enforce multiple of 8
        width = (width // 8) * 8
        height = (height // 8) * 8

        num_frames = max(1, int(duration * 24))

        return {
            "width": width,
            "height": height,
            "num_frames": num_frames,
            "fps": 24,
            "latent_width": width // 8,
            "latent_height": height // 8,
            "latent_frames": max(1, num_frames // 4),
        }

    def _build_comfyui_workflow_graph(
        self,
        prompt: str,
        negative_prompt: str,
        latent_dims: Dict[str, int],
        controlnet_configs: List[Dict[str, Any]],
        lora_weights: List[Dict[str, Any]],
        base_model: str = "CogVideoX-5B",
        enable_teacache: bool = True,
        enable_pab: bool = True,
        sampling_steps: int = 8,
    ) -> Dict[str, Any]:
        """Construct a structured ComfyUI video execution node graph."""
        nodes: Dict[str, Any] = {}
        is_hunyuan = "hunyuan" in base_model.lower()

        # 1. Base Model & VAE Loaders
        if is_hunyuan:
            nodes["1"] = {
                "class_type": "HunyuanVideoModelLoader",
                "inputs": {"model_name": base_model, "precision": "bf16"},
            }
            nodes["2"] = {
                "class_type": "HunyuanVideoVAELoader",
                "inputs": {"vae_name": "HunyuanVideo_VAE.pt"},
            }
        else:
            nodes["1"] = {
                "class_type": "CogVideoXModelLoader",
                "inputs": {"model_name": base_model or "CogVideoX-5B", "precision": "fp16"},
            }
            nodes["2"] = {
                "class_type": "CogVideoXVAELoader",
                "inputs": {"vae_name": "CogVideoX_VAE.pt"},
            }

        # 2. Text Conditioning
        last_model_node = "1"
        if lora_weights:
            # Chain LoRA loader
            lora_class = "HunyuanVideoLoRALoader" if is_hunyuan else "CogVideoXLoRALoader"
            nodes["3"] = {
                "class_type": lora_class,
                "inputs": {
                    "model": [last_model_node, 0],
                    "loras": lora_weights,
                },
            }
            last_model_node = "3"

        text_encode_class = "HunyuanVideoTextEncode" if is_hunyuan else "CogVideoXTextEncode"
        nodes["4"] = {
            "class_type": text_encode_class,
            "inputs": {"prompt": prompt, "model": [last_model_node, 0]},
        }
        nodes["5"] = {
            "class_type": text_encode_class,
            "inputs": {"prompt": negative_prompt, "model": [last_model_node, 0]},
        }

        # 2b. DiT Acceleration Nodes (TeaCache & PAB)
        if enable_teacache:
            nodes["teacache"] = {
                "class_type": "TeaCacheLoader",
                "inputs": {
                    "model": [last_model_node, 0],
                    "threshold": 0.25,
                    "rel_l1_thresh": 0.25,
                    "cache_device": "cuda",
                },
            }
            last_model_node = "teacache"

        if enable_pab:
            nodes["pab"] = {
                "class_type": "PABApply",
                "inputs": {
                    "model": [last_model_node, 0],
                    "cross_broadcast": True,
                    "spatial_broadcast": True,
                },
            }
            last_model_node = "pab"

        # 3. Empty Latent Video Generator
        empty_latent_class = "EmptyHunyuanVideoLatentVideo" if is_hunyuan else "EmptyCogVideoXLatentVideo"
        nodes["6"] = {
            "class_type": empty_latent_class,
            "inputs": {
                "width": latent_dims["width"],
                "height": latent_dims["height"],
                "num_frames": latent_dims["num_frames"],
                "fps": latent_dims["fps"],
            },
        }

        # 4. ControlNet Conditioning Chain
        pos_cond_link = ["4", 0]
        neg_cond_link = ["5", 0]
        node_id_counter = 10

        for cn in controlnet_configs:
            cn_node_id = str(node_id_counter)
            nodes[cn_node_id] = {
                "class_type": cn.get("node_type", "ControlNetApply"),
                "inputs": {
                    "positive": pos_cond_link,
                    "negative": neg_cond_link,
                    "control_type": cn.get("control_type", "depth"),
                    "strength": cn.get("strength", 0.8),
                    "image": cn.get("image_uri") or cn.get("flow_uri") or cn.get("pose_metadata"),
                },
            }
            pos_cond_link = [cn_node_id, 0]
            neg_cond_link = [cn_node_id, 1]
            node_id_counter += 1

        # 5. KSampler
        sampler_node_id = str(node_id_counter)
        nodes[sampler_node_id] = {
            "class_type": "KSampler",
            "inputs": {
                "model": [last_model_node, 0],
                "positive": pos_cond_link,
                "negative": neg_cond_link,
                "latent_image": ["6", 0],
                "seed": 42,
                "steps": sampling_steps,
                "cfg": 7.0,
                "sampler_name": "euler_ancestral",
                "scheduler": "karras",
                "denoise": 1.0,
            },
        }
        node_id_counter += 1

        # 6. VAE Decode & Video Save
        vae_decode_class = "HunyuanVideoVAEDecode" if is_hunyuan else "CogVideoXVAEDecode"
        nodes[str(node_id_counter)] = {
            "class_type": vae_decode_class,
            "inputs": {
                "samples": [sampler_node_id, 0],
                "vae": ["2", 0],
            },
        }
        node_id_counter += 1

        nodes[str(node_id_counter)] = {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": [str(node_id_counter - 1), 0],
                "frame_rate": 24,
                "format": "video/h264-mp4",
            },
        }

        return nodes
