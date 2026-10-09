"""Project Aether Dream-RSI Replay Simulator Pool.

Maintains historical discovery trees H_t and enables deterministic offline replay
of candidate exploration policies across historical traces without executing any
real video generation or VLM API calls (zero external cost) (WBS 1.10.2 / arXiv:2609.14858v1).
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Sequence, Union

from aether.compiler.schemas import ComplexityLevel, ProviderTarget
from aether.teacher.schemas import (
    DiscoveryTraceTree,
    ExplorationPolicy,
    ReplaySimulatorWorld,
    TraceNode,
)


class ReplaySimulatorPool:
    """Historical discovery tree pool H_t for zero-cost offline policy dreaming and replay."""

    def __init__(self, world_id: Optional[str] = None) -> None:
        self.world = ReplaySimulatorWorld(world_id=world_id or f"world_{int(time.time())}")

    @property
    def size(self) -> int:
        """Count of historical discovery trace trees indexed in the pool."""
        return self.world.tree_count

    def add_trace(self, trace: DiscoveryTraceTree) -> None:
        """Indexes an immutable discovery trace tree into the replay pool H_t = H_{t-1} U {T_t}."""
        self.world.add_tree(trace)

    def add_traces(self, traces: Sequence[DiscoveryTraceTree]) -> None:
        """Indexes multiple discovery trace trees into the pool."""
        for t in traces:
            self.add_trace(t)

    def get_tree(self, tree_id: str) -> Optional[DiscoveryTraceTree]:
        """Retrieve a specific historical tree by ID."""
        return self.world.get_tree(tree_id)

    def get_all_trees(self) -> List[DiscoveryTraceTree]:
        """Return all historical trees currently indexed in the pool."""
        return list(self.world.trees.values())

    def load_from_directory(self, dir_path: Union[str, Path]) -> int:
        """Load and index all JSON discovery trace trees from a directory."""
        p = Path(dir_path)
        if not p.exists() or not p.is_dir():
            return 0
        loaded = 0
        for json_file in p.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                tree = DiscoveryTraceTree.from_dict(data)
                self.add_trace(tree)
                loaded += 1
            except Exception:
                continue
        return loaded

    def save_to_directory(self, dir_path: Union[str, Path]) -> int:
        """Export all discovery trees in pool to individual JSON files in a directory."""
        p = Path(dir_path)
        p.mkdir(parents=True, exist_ok=True)
        saved = 0
        for tree in self.world.trees.values():
            file_path = p / f"{tree.tree_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(tree.to_json(indent=2))
            saved += 1
        return saved

    def simulate_policy_on_trace(
        self,
        policy: ExplorationPolicy,
        tree: DiscoveryTraceTree,
    ) -> Dict[str, Any]:
        """Simulates candidate policy decision trajectory over a historical trace tree at ZERO external cost.

        Evaluates counterfactual decisions (complexity, provider routing, sampling steps, TeaCache,
        repair escalation) against recorded ground truth in the discovery tree.
        """
        # Ground truth baseline from historical tree
        best_node = tree.get_best_node()
        if not best_node or not tree.nodes:
            return {
                "tree_id": tree.tree_id,
                "shot_id": tree.shot_id,
                "quality_score": 0.0,
                "hard_gates_passed": False,
                "execution_cost": 0.0,
                "latency_seconds": 0.0,
                "parallel_branches": 1,
                "simulated_complexity": ComplexityLevel.PROMPT_ONLY.value,
                "simulated_provider": ProviderTarget.VEO_3_1.value,
            }

        base_quality = best_node.quality_score
        base_passed = best_node.hard_gates_passed
        base_cost = max(0.001, tree.total_cost if tree.total_cost > 0.0 else 0.10)
        base_latency = max(0.01, tree.total_latency if tree.total_latency > 0.0 else 1.0)

        # 1. Complexity Decision Simulation
        # Evaluate shot kinematics from initial conditions
        req = tree.shot_requirement or {}
        cam_vel = float(req.get("camera_velocity_mps", 0.0))
        chars = req.get("character_ids_involved", [])
        actor_count = len(chars)
        has_dialogue = bool(req.get("audio", {}).get("dialogue") or req.get("dialogue"))
        has_sim = bool(req.get("physical_challenges"))

        vel_thresh = policy.complexity_thresholds.get("velocity_threshold", 3.0)
        actor_thresh = policy.complexity_thresholds.get("actor_count_blocking_threshold", 2.0)

        # Simulated Complexity Level
        if has_sim:
            sim_complexity = ComplexityLevel.FULL_PHYSICAL_SIMULATION
        elif cam_vel >= vel_thresh or actor_count >= actor_thresh:
            sim_complexity = ComplexityLevel.THREED_BLOCKING
        elif has_dialogue:
            sim_complexity = ComplexityLevel.TWOD_TRAJECTORY_POSE
        elif cam_vel > 0.0 or actor_count > 1:
            sim_complexity = ComplexityLevel.KEYFRAMES_INTERPOLATION
        elif actor_count == 1:
            sim_complexity = ComplexityLevel.REFERENCE_IMAGE
        else:
            sim_complexity = ComplexityLevel.PROMPT_ONLY

        # 2. Provider Routing Simulation
        # Pick provider with highest priority weight matching complexity tier
        weights = policy.model_priority_weights
        if sim_complexity >= ComplexityLevel.THREED_BLOCKING:
            # Prefer ComfyUI or Runway for heavy blocking
            target_provider = (
                ProviderTarget.COGVIDEOX_COMFYUI.value
                if weights.get("cogvideox_comfyui", 1.0) >= weights.get("runway_gen_4_5", 1.0)
                else ProviderTarget.RUNWAY_GEN_4_5.value
            )
        elif has_dialogue:
            # Dialogue favored by Kling
            target_provider = (
                ProviderTarget.KLING_3_0.value
                if weights.get("kling_3_0", 1.0) >= weights.get("veo_3_1", 1.0)
                else ProviderTarget.VEO_3_1.value
            )
        else:
            # High-fidelity text/keyframe favored by Veo 3.1
            target_provider = (
                ProviderTarget.VEO_3_1.value
                if weights.get("veo_3_1", 1.0) >= weights.get("kling_3_0", 1.0)
                else ProviderTarget.KLING_3_0.value
            )

        # 3. Frontier Cost & Efficiency Stack Adjustments
        sim_cost = base_cost
        sim_latency = base_latency
        quality_delta = 0.0

        # TeaCache & PAB DiT Acceleration
        if policy.enable_teacache:
            # 65% - 80% compute cost discount on open-weights / GPU runs
            if "comfy" in target_provider.lower() or "cogvideo" in target_provider.lower():
                sim_cost *= 0.35
                sim_latency *= 0.40
            else:
                sim_cost *= 0.85
                sim_latency *= 0.85

        if policy.enable_pab:
            sim_cost *= 0.80
            sim_latency *= 0.75

        # Few-Step Flow Step Distillation
        # Standard diffusion baseline is ~30-50 steps. Distilled is 4-8 steps.
        steps_ratio = policy.sampling_steps / 30.0
        step_factor = min(1.0, max(0.20, steps_ratio))
        sim_cost *= step_factor
        sim_latency *= step_factor

        # Slight quality adjustment based on steps
        if policy.sampling_steps >= 8:
            quality_delta += 0.2  # Optimal distillation point
        elif policy.sampling_steps < 4:
            quality_delta -= 0.8  # Too few steps causes slight blurriness

        # Speculative 480p Draft Gating
        parallel_branches = 1
        if policy.enable_speculative_draft:
            parallel_branches = 2  # Draft + council gating in parallel
            if not base_passed:
                # Early draft rejection eliminates expensive 1080p latent upscaling (saves 75% compute)
                sim_cost *= 0.25
                sim_latency *= 0.30
                quality_delta += 0.5  # Prevented bad render rollout

        # 4. Repair Policy Escalation
        repair_nodes = [n for n in tree.nodes.values() if n.step_type == "SURGICAL_REPAIR"]
        if repair_nodes:
            repair_attempts = len(repair_nodes)
            if repair_attempts > policy.repair_escalation_threshold:
                # Policy escalates to full regen: higher cost, higher reliability
                sim_cost += 0.10
                quality_delta += 0.4

        # Final simulated scores
        simulated_quality = max(0.0, min(10.0, round(base_quality + quality_delta, 2)))
        simulated_cost = max(0.001, round(sim_cost, 4))
        simulated_latency = max(0.05, round(sim_latency, 2))
        simulated_passed = base_passed if quality_delta >= -0.5 else False

        return {
            "tree_id": tree.tree_id,
            "shot_id": tree.shot_id,
            "quality_score": simulated_quality,
            "hard_gates_passed": simulated_passed,
            "execution_cost": simulated_cost,
            "latency_seconds": simulated_latency,
            "parallel_branches": parallel_branches,
            "simulated_complexity": sim_complexity.value,
            "simulated_provider": target_provider,
        }

    def replay_policy(self, policy: ExplorationPolicy) -> List[Dict[str, Any]]:
        """Simulate policy across all discovery trees in H_t at zero external API cost."""
        results: List[Dict[str, Any]] = []
        for tree in self.world.trees.values():
            res = self.simulate_policy_on_trace(policy, tree)
            results.append(res)
        return results
