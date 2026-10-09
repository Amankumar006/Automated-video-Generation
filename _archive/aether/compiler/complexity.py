"""Project Aether Complexity Planner.

Analyzes scene state graphs and shot requirements to classify shots into
Complexity Levels 0 through 5 (Pillar 3 / WBS 1.4.1), providing structured
rationales and spatial representation package recommendations.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Set, Union

from aether.compiler.schemas import (
    ComplexityLevel,
    ComplexityPlan,
    ProviderTarget,
    ShotRequirement,
    SpatialRepresentationPackage,
)
from aether.state.schemas import (
    CharacterState,
    SceneSnapshot,
    SceneState,
    StateDelta,
)


# Physical challenge keyword sets
FLUID_CHALLENGES: Set[str] = {
    "fluid", "fluids", "fluid_dynamics", "water", "liquid", "splash",
    "splashing", "pouring", "blood_splatter", "blood", "rain_puddle", "rain",
    "puddle", "waves", "submersion", "foam", "moisture",
}

SIMULATION_CHALLENGES: Set[str] = {
    "grapple", "grappling", "stunt", "stunts", "fight", "fighting",
    "martial_arts", "martial", "combat", "tackle", "fall", "falling",
    "rigid_body_collision", "rigid_body", "collision", "collide", "high_velocity_impact",
    "high_velocity", "impact", "soft_body_deformation", "soft_body",
    "cloth_simulation", "cloth", "explosion", "destruction", "glass_shatter",
    "shatter", "physics_simulation", "physics", "simulation", "sim",
}

COMPLEX_CAMERA_MOVEMENTS: Set[str] = {
    "crane", "crane_up", "crane_down", "orbit", "whip_pan", "3d_tracking",
    "drone_flythrough", "spiral", "complex_rig", "flythrough", "aerial_tracking",
}

SIMPLE_CAMERA_MOVEMENTS: Set[str] = {
    "pan", "pan_left", "pan_right", "tilt", "tilt_up", "tilt_down",
    "dolly", "dolly_in", "dolly_out", "truck", "truck_left", "truck_right",
    "pedestal", "pedestal_up", "pedestal_down", "zoom", "zoom_in", "zoom_out",
}


class ComplexityPlanner:
    """Evaluates scene state and shot requirements to determine the minimum necessary

    deterministic complexity level (0 through 5) based on actor count, camera velocity,
    physical phenomena, prop handoffs, and temporal continuity sensitivity.
    """

    def __init__(
        self,
        complexity_thresholds: Optional[Dict[str, float]] = None,
        active_policy: Optional[Any] = None,
        llm_client: Optional[Any] = None,
    ) -> None:
        self.active_policy = active_policy
        self.llm_client = llm_client
        self.complexity_thresholds: Dict[str, float] = {
            "velocity_threshold": 3.0,
            "actor_count_blocking_threshold": 2.0,
            "actor_movement_threshold": 1.0,
            "close_proximity_threshold": 2.5,
        }
        if complexity_thresholds:
            self.complexity_thresholds.update(complexity_thresholds)
        elif active_policy and hasattr(active_policy, "complexity_thresholds"):
            self.complexity_thresholds.update(active_policy.complexity_thresholds)

    def plan(
        self,
        scene_state: Union[SceneState, SceneSnapshot, Any],
        shot_requirement: Optional[Union[ShotRequirement, Dict[str, Any]]] = None,
        state_delta: Optional[StateDelta] = None,
        spatial_package: Optional[SpatialRepresentationPackage] = None,
        use_llm: bool = False,
    ) -> ComplexityPlan:
        """Analyze scene state, shot requirements, and deltas to emit a full ComplexityPlan.

        Args:
            scene_state: Active SceneState, SceneSnapshot, or AetherWorldModel instance.
            shot_requirement: Shot requirements or dictionary defining target parameters.
            state_delta: Optional StateDelta from the preceding cut.
            spatial_package: Optional pre-existing spatial representation passes.

        Returns:
            ComplexityPlan with complexity level, rationale, recommendations, and metrics.
        """
        if use_llm:
            return self.evaluate_with_llm(
                scene_state=scene_state,
                shot_requirement=shot_requirement,
                state_delta=state_delta,
                spatial_package=spatial_package,
            )
        # Resolve state from snapshot or world model if needed
        state = self._extract_scene_state(scene_state)
        req = self._normalize_shot_requirement(shot_requirement)

        # Factor extraction
        actors = self._resolve_active_characters(state, req)
        actor_count = len(actors)
        camera_velocity, camera_movement = self._resolve_camera_kinematics(state, req, state_delta)
        has_fluids, has_sim = self._evaluate_physical_challenges(state, req)
        has_handoff = self._evaluate_prop_handoff(state, req, state_delta)
        has_dialogue = req.has_dialogue
        is_continuity_critical = req.continuity_critical or self._has_persistent_defects(state)
        actor_movement_dist = self._evaluate_actor_movement(actors, state_delta)

        # Thresholds configured via active exploration policy
        vel_thresh = self.complexity_thresholds.get("velocity_threshold", 3.0)
        actor_count_thresh = int(self.complexity_thresholds.get("actor_count_blocking_threshold", 2.0))
        actor_movement_thresh = self.complexity_thresholds.get("actor_movement_threshold", 1.0)
        prox_thresh = self.complexity_thresholds.get("close_proximity_threshold", 2.5)

        # Multi-character proximity evaluation
        actors_in_close_proximity = self._actors_close_together(actors, max_dist=prox_thresh)

        # Normalized kinematics for movement detection
        m_norm = (camera_movement or "").lower().replace(" ", "_")
        is_complex_camera = bool(
            m_norm in COMPLEX_CAMERA_MOVEMENTS
            or any(k in m_norm for k in ("crane", "orbit", "flythrough", "3d_tracking", "spiral", "whip_pan", "fly"))
        )
        is_simple_camera = bool(
            m_norm in SIMPLE_CAMERA_MOVEMENTS
            or any(k in m_norm for k in ("pan", "tilt", "dolly", "truck", "pedestal", "zoom"))
        )

        rationale: List[str] = []
        factors_detected: Dict[str, Any] = {
            "actor_count": actor_count,
            "actor_ids": [c.character_id for c in actors],
            "camera_velocity_mps": round(camera_velocity, 2),
            "camera_movement": camera_movement,
            "has_fluids": has_fluids,
            "has_physical_simulation": has_sim,
            "has_prop_handoff": has_handoff,
            "has_dialogue": has_dialogue,
            "is_continuity_critical": is_continuity_critical,
            "max_actor_movement_meters": round(actor_movement_dist, 2),
            "actors_in_close_proximity": actors_in_close_proximity,
        }

        # Determine level based on priority of physical and deterministic constraints
        level: ComplexityLevel

        # ---------------- LEVEL 5: FULL DETERMINISTIC PHYSICAL SIMULATION ----------------
        if has_fluids or has_sim:
            level = ComplexityLevel.FULL_PHYSICAL_SIMULATION
            if has_fluids:
                rationale.append("Fluid dynamics detected (water, blood splatters, splashing, or high surface wetness) requiring deterministic physics simulation.")
            if has_sim:
                rationale.append("High-order collision, stunt, grapple, or martial combat detected requiring rigid/soft body simulation.")
            if has_handoff:
                rationale.append("Prop handoff / transfer between characters also present; requires 3D spatial previs to prevent object teleportation or duplication.")

        # ---------------- LEVEL 4: 3D GEOMETRIC BLOCKING & HANDOFFS ----------------
        elif (
            has_handoff
            or (actor_count >= actor_count_thresh and actors_in_close_proximity)
            or actor_count >= (actor_count_thresh + 1)
            or is_complex_camera
            or camera_velocity >= vel_thresh
            or req.metadata.get("blocking")
            or req.metadata.get("multi_character_blocking")
        ):
            level = ComplexityLevel.THREED_BLOCKING
            if has_handoff:
                rationale.append("Prop handoff / transfer between characters detected; requires 3D spatial previs to prevent object teleportation or duplication.")
            if actor_count >= actor_count_thresh and actors_in_close_proximity:
                rationale.append(f"Multi-character interaction with {actor_count} actors in close proximity (<{prox_thresh:.1f}m); requires 3D geometric blocking to preserve spatial consistency.")
            elif actor_count >= (actor_count_thresh + 1):
                rationale.append(f"Multi-character ensemble staging with {actor_count} actors requires 3D geometric blocking.")
            if is_complex_camera:
                rationale.append(f"Complex camera trajectory '{camera_movement}' requires 3D camera path blocking.")
            if camera_velocity >= vel_thresh:
                rationale.append(f"High camera velocity ({camera_velocity:.1f} m/s >= {vel_thresh:.1f} m/s) with active subjects requires 3D spatial pre-visualization.")

        # ---------------- LEVEL 3: 2D TRAJECTORY & POSE ----------------
        elif (
            has_dialogue
            or actor_movement_dist > actor_movement_thresh
            or (actor_count >= 1 and any(k in m_norm for k in ("tracking", "walk_to_camera", "walk_towards_camera", "walking", "follow")))
            or req.metadata.get("talking_head")
            or req.metadata.get("gestures")
        ):
            level = ComplexityLevel.TWOD_TRAJECTORY_POSE
            if has_dialogue:
                transcript_snippet = f" ('{req.audio.dialogue_transcript[:25]}...')" if req.audio.dialogue_transcript else ""
                rationale.append(f"Synchronous character dialogue{transcript_snippet} requires 2D facial landmark / OpenPose lip-sync trajectory.")
            if actor_movement_dist > actor_movement_thresh:
                rationale.append(f"Character displacement of {actor_movement_dist:.1f}m requires 2D skeleton pose and trajectory tracking.")
            if any(k in m_norm for k in ("tracking", "walk_to_camera", "walk_towards_camera", "walking", "follow")):
                rationale.append(f"Actor walking towards camera / tracking motion ('{camera_movement}') requires 2D optical flow and pose guidance.")

        # ---------------- LEVEL 2: KEYFRAMES INTERPOLATION ----------------
        elif (
            camera_velocity > 0.0
            or is_simple_camera
            or actor_movement_dist > 0.05
            or is_continuity_critical
            or actor_count >= 2
        ):
            level = ComplexityLevel.KEYFRAMES_INTERPOLATION
            if is_simple_camera or camera_velocity > 0.0:
                rationale.append(f"Straightforward camera movement ('{camera_movement or 'motion'}', {camera_velocity:.1f} m/s) can be bounded by first and last frame keyframes.")
            if actor_movement_dist > 0.05:
                rationale.append(f"Minor actor motion ({actor_movement_dist:.1f}m) bounded by starting and ending keyframe states.")
            if is_continuity_critical:
                rationale.append("Continuity-critical visual state requires start-to-end keyframe interpolation to anchor visual condition.")
            if actor_count >= 2:
                rationale.append(f"Multiple actors ({actor_count}) present in wide staging; keyframe pair provides sufficient bounding geometry.")

        # ---------------- LEVEL 1: REFERENCE IMAGE CONDITIONED ----------------
        elif actor_count == 1:
            level = ComplexityLevel.REFERENCE_IMAGE
            rationale.append("Single static actor portrait or establishing shot; reference image provides sufficient identity and wardrobe grounding.")

        # ---------------- LEVEL 0: PURE TEXT PROMPT ----------------
        else:
            level = ComplexityLevel.PROMPT_ONLY
            rationale.append("No characters, no prop manipulations, and no complex physics detected; atmospheric vista or abstract cutaway is suitable for pure text prompt.")

        # Continuity escalation check
        if is_continuity_critical and level < ComplexityLevel.KEYFRAMES_INTERPOLATION:
            level = ComplexityLevel.KEYFRAMES_INTERPOLATION
            rationale.append("Continuity sensitivity escalated minimum level to Level 2 (KEYFRAMES_INTERPOLATION) to lock persistent visual state.")

        # Representation recommendations and provider mapping
        recommended_reps = self.get_recommended_representations(level)
        recommended_provider = self.get_recommended_provider(level, req, spatial_package)

        return ComplexityPlan(
            shot_id=req.shot_id,
            complexity_level=level,
            rationale=rationale,
            recommended_representations=recommended_reps,
            recommended_provider=recommended_provider,
            factors_detected=factors_detected,
        )

    def classify(
        self,
        scene_state: Union[SceneState, SceneSnapshot, Any],
        shot_requirement: Optional[Union[ShotRequirement, Dict[str, Any]]] = None,
        state_delta: Optional[StateDelta] = None,
    ) -> ComplexityLevel:
        """Convenience method returning solely the determined ComplexityLevel."""
        plan = self.plan(scene_state, shot_requirement, state_delta)
        return plan.complexity_level

    @staticmethod
    def get_recommended_representations(level: Union[ComplexityLevel, int, str]) -> List[str]:
        """Returns the list of advised spatial representation package passes for a given complexity level."""
        lvl = int(ComplexityLevel.from_val(level))
        if lvl == 0:
            return []
        elif lvl == 1:
            return ["photoreal_ref"]
        elif lvl == 2:
            return ["photoreal_ref", "first_frame", "last_frame"]
        elif lvl == 3:
            return ["photoreal_ref", "skeleton_pose_metadata", "motion_vectors"]
        elif lvl == 4:
            return ["clay_render", "depth_map", "camera_trajectory", "segmentation_masks", "photoreal_ref"]
        elif lvl == 5:
            return ["clay_render", "depth_map", "surface_normals", "motion_vectors", "camera_trajectory", "segmentation_masks", "skeleton_pose_metadata"]
        return ["photoreal_ref"]

    @staticmethod
    def get_recommended_provider(
        level: Union[ComplexityLevel, int, str],
        shot_requirement: Optional[Union[ShotRequirement, Dict[str, Any]]] = None,
        spatial_package: Optional[Union[SpatialRepresentationPackage, Dict[str, Any]]] = None,
    ) -> ProviderTarget:
        """Determines the default optimal generative model provider target for this tier."""
        lvl = int(ComplexityLevel.from_val(level))
        req = ShotRequirement(**shot_requirement) if isinstance(shot_requirement, dict) else shot_requirement
        pkg = SpatialRepresentationPackage(**spatial_package) if isinstance(spatial_package, dict) else spatial_package
        has_dialogue = bool(req and req.has_dialogue)
        has_spatial_passes = bool(pkg and not pkg.is_empty)

        if lvl == 0:
            return ProviderTarget.VEO_3_1
        elif lvl == 1:
            return ProviderTarget.RUNWAY_GEN_4_5
        elif lvl == 2:
            return ProviderTarget.VEO_3_1
        elif lvl == 3:
            if has_dialogue:
                return ProviderTarget.KLING_3_0
            return ProviderTarget.VEO_3_1
        elif lvl == 4:
            if has_spatial_passes:
                return ProviderTarget.COGVIDEOX_COMFYUI
            return ProviderTarget.RUNWAY_GEN_4_5
        elif lvl == 5:
            return ProviderTarget.COGVIDEOX_COMFYUI
        return ProviderTarget.VEO_3_1

    # ----------------- PRIVATE HELPER METHODS -----------------

    def _extract_scene_state(self, scene_state_or_snapshot: Any) -> SceneState:
        """Unpack SceneState from raw object, SceneSnapshot, or AetherWorldModel."""
        if hasattr(scene_state_or_snapshot, "active_state"):
            return scene_state_or_snapshot.active_state
        if hasattr(scene_state_or_snapshot, "state"):
            return scene_state_or_snapshot.state
        if isinstance(scene_state_or_snapshot, SceneState):
            return scene_state_or_snapshot
        if isinstance(scene_state_or_snapshot, dict):
            return SceneState(**scene_state_or_snapshot)
        raise ValueError(f"Unsupported scene state input type: {type(scene_state_or_snapshot)}")

    def _normalize_shot_requirement(
        self,
        req: Optional[Union[ShotRequirement, Dict[str, Any]]],
    ) -> ShotRequirement:
        """Convert None or dict to ShotRequirement instance."""
        if req is None:
            return ShotRequirement()
        if isinstance(req, ShotRequirement):
            return req
        if isinstance(req, dict):
            return ShotRequirement(**req)
        raise ValueError(f"Unsupported shot requirement type: {type(req)}")

    def _resolve_active_characters(
        self,
        state: SceneState,
        req: ShotRequirement,
    ) -> List[CharacterState]:
        """Find active CharacterState objects filtered by shot requirement or scene roster."""
        if req.character_ids_involved:
            actors = []
            for cid in req.character_ids_involved:
                c = state.get_character(cid)
                if c is not None:
                    actors.append(c)
                else:
                    # Fabricate minimal representation if character is specified in req but missing from roster
                    actors.append(CharacterState(character_id=cid, name=cid))
            return actors
        return list(state.character_roster.values())

    def _resolve_camera_kinematics(
        self,
        state: SceneState,
        req: ShotRequirement,
        delta: Optional[StateDelta],
    ) -> tuple[float, Optional[str]]:
        """Compute camera velocity (m/s) and camera movement descriptor."""
        movement = req.camera_movement
        velocity = req.camera_velocity_mps

        if delta and delta.camera_delta:
            cd = delta.camera_delta
            if cd.distance_moved > 0.0:
                elapsed = max(delta.elapsed_seconds, 1.0)
                calc_vel = cd.distance_moved / elapsed
                velocity = max(velocity, calc_vel)
                if not movement:
                    movement = "camera_translation"

        if movement and not velocity:
            m_low = movement.lower().replace(" ", "_")
            if any(k in m_low for k in ("whip", "fast", "sprint", "rush")):
                velocity = 4.0
            elif any(k in m_low for k in ("crane", "orbit", "fly", "spiral", "tracking", "3d")):
                velocity = 2.5
            elif any(k in m_low for k in ("pan", "tilt", "dolly", "truck", "pedestal", "zoom")):
                velocity = 1.0

        return velocity, movement

    def _evaluate_physical_challenges(
        self,
        state: SceneState,
        req: ShotRequirement,
    ) -> tuple[bool, bool]:
        """Check for fluid dynamics and high-order physics simulation challenges."""
        has_fluids = False
        has_sim = False

        # Check explicit challenges in requirement
        for pc in req.physical_challenges:
            pc_low = pc.lower().strip()
            pc_norm = pc_low.replace(" ", "_")
            words = set(pc_low.split()) | set(pc_norm.split("_"))
            if any(k in pc_low or k in pc_norm or k in words for k in FLUID_CHALLENGES):
                has_fluids = True
            if any(k in pc_low or k in pc_norm or k in words for k in SIMULATION_CHALLENGES):
                has_sim = True

        # Check explicit metadata requests
        if req.metadata.get("fluids_simulation") or req.metadata.get("dynamic_fluids"):
            has_fluids = True
        if req.metadata.get("physics_simulation") or req.metadata.get("rigid_body_simulation") or req.metadata.get("simulation"):
            has_sim = True

        return has_fluids, has_sim

    def _evaluate_prop_handoff(
        self,
        state: SceneState,
        req: ShotRequirement,
        delta: Optional[StateDelta],
    ) -> bool:
        """Detect whether a prop is being handed off or transferred between actors."""
        if req.has_prop_handoff:
            return True

        if delta and delta.prop_deltas:
            for pd in delta.prop_deltas.values():
                if pd.ownership_transition:
                    prev_owner, new_owner = pd.ownership_transition
                    if prev_owner != new_owner:
                        return True
                if pd.hand_transition:
                    prev_hand, new_hand = pd.hand_transition
                    if prev_hand != new_hand:
                        return True
                if pd.physical_state_transition:
                    prev_state, new_state = pd.physical_state_transition
                    if prev_state != new_state:
                        return True

        return False

    def _has_persistent_defects(self, state: SceneState) -> bool:
        """Check if any active character has persistent damage, scars, or wardrobe tears."""
        for c in state.character_roster.values():
            if c.injuries:
                return True
            for w in c.wardrobe.values():
                if w.damage_level > 0.0 or w.state not in ("pristine", "clean", "intact"):
                    return True
        for p in state.prop_roster.values():
            if p.physical_state not in ("pristine", "intact", "clean"):
                return True
        return False

    def _evaluate_actor_movement(
        self,
        actors: List[CharacterState],
        delta: Optional[StateDelta],
    ) -> float:
        """Find max distance moved by any active character across the cut."""
        if not delta or not delta.character_deltas:
            return 0.0
        max_dist = 0.0
        actor_ids = {a.character_id for a in actors}
        for cid, cd in delta.character_deltas.items():
            if not actor_ids or cid in actor_ids:
                max_dist = max(max_dist, cd.distance_moved)
        return max_dist

    def _actors_close_together(self, actors: List[CharacterState], max_dist: Optional[float] = None) -> bool:
        """Check if any two characters in the active set are within proximity threshold."""
        threshold = max_dist if max_dist is not None else self.complexity_thresholds.get("close_proximity_threshold", 2.5)
        if len(actors) < 2:
            return False
        for i in range(len(actors)):
            for j in range(i + 1, len(actors)):
                dist = actors[i].distance_to(actors[j])
                if dist <= threshold:
                    return True
        return False

    def evaluate_with_llm(
        self,
        scene_state: Union[SceneState, SceneSnapshot, Any],
        shot_requirement: Optional[Union[ShotRequirement, Dict[str, Any]]] = None,
        state_delta: Optional[StateDelta] = None,
        spatial_package: Optional[SpatialRepresentationPackage] = None,
        client: Optional[Any] = None,
        model: str = "gpt-oss:120b:cloud",
    ) -> ComplexityPlan:
        """Evaluates shot complexity level using Ollama Cloud LLM backend with automatic fallback

        to deterministic heuristic evaluation.
        """
        import logging
        logger = logging.getLogger(__name__)

        state = self._extract_scene_state(scene_state)
        req = self._normalize_shot_requirement(shot_requirement)

        # Baseline heuristic plan as baseline/safety guarantee
        baseline_plan = self.plan(state, req, state_delta, spatial_package, use_llm=False)

        try:
            from pipeline.ollama_client import OllamaClient
            ollama = client or self.llm_client or OllamaClient()

            prompt = (
                "You are the Lead Cinematographer and Spatial Complexity Planner for Project Aether v2.\n"
                "Analyze the following scene context and shot requirements to classify the shot into exactly one Complexity Level (0 through 5):\n\n"
                "Complexity Levels:\n"
                "- Level 0 (PROMPT_ONLY): Pure text prompt. No characters, no prop manipulations, no physics.\n"
                "- Level 1 (REFERENCE_IMAGE): Single static character portrait or establishing shot. Identity/wardrobe grounding.\n"
                "- Level 2 (KEYFRAMES_INTERPOLATION): Simple camera movement (pan/dolly), minor motion, start/end keyframe bounding.\n"
                "- Level 3 (TWOD_TRAJECTORY_POSE): Synchronous character dialogue, walking towards camera, 2D OpenPose tracking.\n"
                "- Level 4 (THREED_BLOCKING): 3D geometric blocking, prop handoffs, multi-character close proximity (<2.5m), complex camera (crane/orbit).\n"
                "- Level 5 (FULL_PHYSICAL_SIMULATION): Fluid dynamics (water, blood splatters, pouring), stunt combat, martial arts, soft/rigid body collision.\n\n"
                f"Shot ID: {req.shot_id}\n"
                f"Duration: {req.target_duration}s\n"
                f"Camera Movement: {req.camera_movement}\n"
                f"Characters: {req.character_ids_involved}\n"
                f"Dialogue: {req.audio.dialogue_transcript if req.audio else 'None'}\n"
                f"Continuity Critical: {req.continuity_critical}\n"
                f"Active Characters in Scene: {[c.name for c in state.character_roster.values()]}\n"
                f"Active Props: {[p.name for p in state.prop_roster.values()]}\n\n"
                "Output a JSON object strictly following this structure:\n"
                "{\n"
                '  "complexity_level": 0 to 5,\n'
                '  "rationale": ["bullet point 1", "bullet point 2"],\n'
                '  "recommended_representations": ["representation_pass_1", "representation_pass_2"],\n'
                '  "recommended_provider": "veo_3_1" | "kling_3_0" | "runway_gen_4_5" | "comfyui_cogvideox"\n'
                "}\n"
            )
            res = ollama.generate_completion(prompt=prompt, model=model, format="json")
            if isinstance(res, dict) and "complexity_level" in res:
                lvl_val = int(res["complexity_level"])
                lvl_val = max(0, min(5, lvl_val))
                level = ComplexityLevel(lvl_val)
                rationale = res.get("rationale")
                if not isinstance(rationale, list):
                    rationale = [str(rationale)] if rationale else baseline_plan.rationale

                provider_str = str(res.get("recommended_provider", baseline_plan.recommended_provider.value))
                try:
                    provider = ProviderTarget(provider_str)
                except ValueError:
                    provider = baseline_plan.recommended_provider

                reps = res.get("recommended_representations")
                if not isinstance(reps, list) or not reps:
                    reps = self.get_recommended_representations(level)

                return ComplexityPlan(
                    shot_id=req.shot_id,
                    complexity_level=level,
                    rationale=rationale,
                    recommended_representations=reps,
                    recommended_provider=provider,
                    factors_detected=baseline_plan.factors_detected,
                )
        except Exception as e:
            logger.warning(f"⚠️ LLM complexity evaluation failed ({e}), using deterministic heuristic baseline.")

        return baseline_plan
