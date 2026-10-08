"""Project Aether Policy Dreamer.

Offline meta-learning engine that evaluates candidate exploration and routing policies
over the Replay Simulator Pool at ZERO external API cost, optimizing the Dream-RSI
Pareto objective:
    V_{im} = max_v s_v - beta_1 N_{im} + beta_2 (N_{im} / max(1, k*_{im}))
and selecting pi_{t+1} for live studio redeployment (WBS 1.10.3 / arXiv:2609.14858v1).
"""

from __future__ import annotations

import copy
import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

from aether.teacher.replay_simulator import ReplaySimulatorPool
from aether.teacher.schemas import (
    DiscoveryTraceTree,
    DreamEvaluationResult,
    ExplorationPolicy,
)


class PolicyDreamer:
    """Dream-RSI Offline Policy Optimizer.

    Simulates thousands of counterfactual policy rollouts across pre-recorded discovery trees
    to discover Pareto-superior routing, complexity, and efficiency configurations.
    """

    def __init__(
        self,
        replay_pool: ReplaySimulatorPool,
        default_beta1: float = 0.05,
        default_beta2: float = 0.02,
    ) -> None:
        self.replay_pool = replay_pool
        self.default_beta1 = default_beta1
        self.default_beta2 = default_beta2

    def compute_pareto_value(
        self,
        quality_score: float,
        cost: float,
        parallel_branches: int = 1,
        beta1: Optional[float] = None,
        beta2: Optional[float] = None,
        hard_gates_passed: bool = True,
    ) -> float:
        """Computes the Dream-RSI Pareto objective:

        V_{im} = s_v - beta_1 * N_{im} + beta_2 * (N_{im} / max(1, k^*_{im}))

        Penalizes compute cost N_{im} while rewarding solution quality s_v and
        parallel batch execution speedup.
        """
        b1 = beta1 if beta1 is not None else self.default_beta1
        b2 = beta2 if beta2 is not None else self.default_beta2
        k_star = max(1, parallel_branches)

        # Baseline Pareto objective
        v = quality_score - (b1 * cost) + (b2 * (cost / k_star))

        # Heavy penalty if hard gate was tripped
        if not hard_gates_passed:
            v -= 3.0

        return round(v, 4)

    def evaluate_policy(
        self,
        policy: ExplorationPolicy,
        trees: Optional[Sequence[DiscoveryTraceTree]] = None,
    ) -> DreamEvaluationResult:
        """Deterministically evaluates a policy across the replay pool at ZERO external API cost."""
        target_trees = trees if trees is not None else self.replay_pool.get_all_trees()
        if not target_trees:
            return DreamEvaluationResult(
                policy_id=policy.policy_id,
                policy_name=policy.name,
                num_episodes_replayed=0,
                mean_quality_score=0.0,
                hard_gate_pass_rate=0.0,
                mean_cost=0.0,
                mean_latency=0.0,
                pareto_value=0.0,
                is_pareto_superior=False,
            )

        episode_scores: List[Dict[str, Any]] = []
        total_quality = 0.0
        total_cost = 0.0
        total_latency = 0.0
        passed_count = 0
        total_pareto = 0.0

        b1 = policy.beta1_cost_weight if policy.beta1_cost_weight is not None else self.default_beta1
        b2 = policy.beta2_parallel_weight if policy.beta2_parallel_weight is not None else self.default_beta2

        for t in target_trees:
            sim = self.replay_pool.simulate_policy_on_trace(policy, t)
            q = sim["quality_score"]
            c = sim["execution_cost"]
            lat = sim["latency_seconds"]
            passed = sim["hard_gates_passed"]
            k_star = sim.get("parallel_branches", 1)

            p_val = self.compute_pareto_value(
                quality_score=q,
                cost=c,
                parallel_branches=k_star,
                beta1=b1,
                beta2=b2,
                hard_gates_passed=passed,
            )
            sim["pareto_value"] = p_val
            episode_scores.append(sim)

            total_quality += q
            total_cost += c
            total_latency += lat
            total_pareto += p_val
            if passed:
                passed_count += 1

        n = len(target_trees)
        mean_quality = round(total_quality / n, 3)
        mean_cost = round(total_cost / n, 4)
        mean_latency = round(total_latency / n, 3)
        pass_rate = round(passed_count / n, 3)
        mean_pareto = round(total_pareto / n, 4)

        return DreamEvaluationResult(
            policy_id=policy.policy_id,
            policy_name=policy.name,
            num_episodes_replayed=n,
            mean_quality_score=mean_quality,
            hard_gate_pass_rate=pass_rate,
            mean_cost=mean_cost,
            mean_latency=mean_latency,
            pareto_value=mean_pareto,
            is_pareto_superior=False,
            episode_scores=episode_scores,
            details={
                "beta1": b1,
                "beta2": b2,
                "enable_teacache": policy.enable_teacache,
                "enable_pab": policy.enable_pab,
                "sampling_steps": policy.sampling_steps,
                "enable_speculative_draft": policy.enable_speculative_draft,
            },
        )

    def generate_candidate_policies(
        self,
        base_policy: Optional[ExplorationPolicy] = None,
        num_candidates: int = 10,
        mutation_scale: float = 0.20,
        seed: Optional[int] = 42,
    ) -> List[ExplorationPolicy]:
        """Synthesize candidate exploration policies spanning the hyperparameter space."""
        base = base_policy or ExplorationPolicy(name="BaselinePolicy")
        candidates: List[ExplorationPolicy] = []
        rng = random.Random(seed)

        # Candidate 0: The baseline policy unchanged
        candidates.append(base.copy_with(name=f"{base.name}_baseline"))

        # Candidate 1: Frontier Distilled Efficiency Policy (TeaCache + PAB + 8 steps)
        candidates.append(
            base.copy_with(
                name="Frontier_Distilled_Flow_Policy",
                enable_teacache=True,
                enable_pab=True,
                sampling_steps=8,
                enable_speculative_draft=True,
            )
        )

        # Candidate 2: Ultra-Fast Few-Step Draft Policy (4 steps)
        candidates.append(
            base.copy_with(
                name="Ultra_Fast_FewStep_Policy",
                enable_teacache=True,
                enable_pab=True,
                sampling_steps=4,
                enable_speculative_draft=True,
            )
        )

        # Candidate 3: Quality-First Reference Policy (16 steps, conservative repair escalation)
        candidates.append(
            base.copy_with(
                name="Quality_First_Policy",
                enable_teacache=True,
                enable_pab=False,
                sampling_steps=16,
                repair_escalation_threshold=2,
            )
        )

        # Additional stochastic mutations to fill target count
        for i in range(len(candidates), num_candidates):
            mut = base.mutate(mutation_scale=mutation_scale, seed=rng.randint(1, 1_000_000))
            mut.name = f"Dream_Candidate_{i:02d}"
            candidates.append(mut)

        return candidates[:num_candidates]

    def dream(
        self,
        num_candidates: int = 10,
        base_policy: Optional[ExplorationPolicy] = None,
        mutation_scale: float = 0.20,
        seed: Optional[int] = 42,
    ) -> Tuple[ExplorationPolicy, List[DreamEvaluationResult]]:
        """Executes full Stage 3 offline dreaming loop over the Replay Simulator World.

        1. Generates M candidate policies.
        2. Evaluates each candidate deterministically over historical discovery trees H_t.
        3. Computes Dream-RSI Pareto objective V_{im}.
        4. Identifies Pareto-superior policies and selects pi_{t+1}.
        """
        base = base_policy or ExplorationPolicy(name="Active_Online_Policy")
        base_result = self.evaluate_policy(base)

        candidates = self.generate_candidate_policies(
            base_policy=base,
            num_candidates=num_candidates,
            mutation_scale=mutation_scale,
            seed=seed,
        )

        evaluation_results: List[DreamEvaluationResult] = []

        for candidate in candidates:
            res = self.evaluate_policy(candidate)
            # Evaluate Pareto superiority: Higher Pareto score, non-degraded pass rate & quality
            is_superior = bool(
                res.pareto_value > base_result.pareto_value
                and res.hard_gate_pass_rate >= base_result.hard_gate_pass_rate
                and res.mean_quality_score >= (base_result.mean_quality_score - 0.2)
            )
            res.is_pareto_superior = is_superior
            evaluation_results.append(res)

        # Select winning policy pi_{t+1}:
        # Only policies demonstrably Pareto-superior to baseline are redeployed
        superior_results = [r for r in evaluation_results if r.is_pareto_superior]
        if superior_results:
            superior_results.sort(
                key=lambda r: (r.pareto_value, r.hard_gate_pass_rate, r.mean_quality_score),
                reverse=True,
            )
            winner_id = superior_results[0].policy_id
            winner_policy = next((c for c in candidates if c.policy_id == winner_id), base)
        else:
            # No candidate demonstrably outperformed baseline without regression; retain baseline
            winner_policy = base

        # Sort overall evaluation results: superior first, then by pareto value descending
        evaluation_results.sort(
            key=lambda r: (1 if r.is_pareto_superior else 0, r.pareto_value, r.hard_gate_pass_rate),
            reverse=True,
        )

        return winner_policy, evaluation_results

    def compare_policies(
        self,
        policy_a: ExplorationPolicy,
        policy_b: ExplorationPolicy,
    ) -> Dict[str, Any]:
        """Head-to-head comparison between two policies over the replay simulator."""
        res_a = self.evaluate_policy(policy_a)
        res_b = self.evaluate_policy(policy_b)

        delta_pareto = round(res_b.pareto_value - res_a.pareto_value, 4)
        delta_cost = round(res_b.mean_cost - res_a.mean_cost, 4)
        delta_quality = round(res_b.mean_quality_score - res_a.mean_quality_score, 3)

        return {
            "policy_a": {"id": policy_a.policy_id, "name": policy_a.name, "result": res_a.model_dump()},
            "policy_b": {"id": policy_b.policy_id, "name": policy_b.name, "result": res_b.model_dump()},
            "delta_pareto_value": delta_pareto,
            "delta_cost": delta_cost,
            "delta_quality": delta_quality,
            "winner": policy_b.policy_id if delta_pareto > 0 else policy_a.policy_id,
        }
