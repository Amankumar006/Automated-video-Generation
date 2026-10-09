"""Project Aether Dream-RSI Teacher Engine Schemas.

Defines Pydantic V2 schemas for TraceNode, DiscoveryTraceTree, ReplaySimulatorWorld,
ExplorationPolicy (with tunable knobs), DreamEvaluationResult, and ProductionRule
for Phase 9: Dream-RSI Teacher Engine & Recursive Self-Improvement (WBS 1.10 / arXiv:2609.14858v1).
"""

from __future__ import annotations

import copy
import json
import random
import time
import uuid
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aether.compiler.schemas import ComplexityLevel, ProviderTarget, ComputeTier


class TraceNode(BaseModel):
    """Represents an atomic execution step or decision within a render episode."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    node_id: str = Field(default_factory=lambda: f"node_{uuid.uuid4().hex[:8]}", description="Unique trace node identifier")
    parent_id: Optional[str] = Field(None, description="Parent trace node identifier in exploration tree")
    step_type: str = Field("RENDER_STEP", description="Type of step (e.g. INITIAL_COMPILE, COUNCIL_AUDIT, REPAIR_PLAN, FINAL_RENDER)")
    policy_id: Optional[str] = Field(None, description="Identifier of the exploration policy governing this step")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Input state, requirements, or preceding node references")
    action: Dict[str, Any] = Field(default_factory=dict, description="Chosen action, complexity level, provider target, repair action")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="Produced artifacts, audit reports, generated video references")
    quality_score: float = Field(0.0, ge=0.0, le=10.0, description="Evaluated soft quality score (0.0 to 10.0)")
    hard_gates_passed: bool = Field(True, description="Whether all binary hard gates were satisfied")
    execution_cost: float = Field(0.0, ge=0.0, description="Financial or token execution cost (USD or credits)")
    token_count: int = Field(0, ge=0, description="Total API tokens consumed by this step")
    latency_seconds: float = Field(0.0, ge=0.0, description="Execution wall-clock latency in seconds")
    parallel_branches: int = Field(1, ge=1, description="Number of parallel workers/branches executed (k* factor)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic telemetry and profiler metrics")

    @property
    def is_root(self) -> bool:
        """True if node has no parent."""
        return self.parent_id is None

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace node to dictionary."""
        return self.model_dump(mode="json")


class DiscoveryTraceTree(BaseModel):
    """Structured, immutable discovery trace tree representing a full render episode.

    Maps (SceneState -> Complexity -> Compiled Payload -> Council Report -> Repair Plan -> Final Outcome).
    Forms the atomic unit of the Dream-RSI Replay World Pool (H_t).
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    tree_id: str = Field(default_factory=lambda: f"tree_{uuid.uuid4().hex[:8]}", description="Unique discovery tree identifier")
    shot_id: str = Field("SHOT_001", description="Cinematic shot identifier")
    root_node_id: str = Field("", description="Root node identifier")
    nodes: Dict[str, TraceNode] = Field(default_factory=dict, description="Mapping of node IDs to TraceNode objects")
    best_node_id: Optional[str] = Field(None, description="Identifier of highest-quality successful leaf/trajectory node")
    created_at: float = Field(default_factory=time.time, description="Unix timestamp of tree creation")
    scene_state_initial: Dict[str, Any] = Field(default_factory=dict, description="Initial frozen SceneState snapshot")
    shot_requirement: Dict[str, Any] = Field(default_factory=dict, description="Target ShotRequirement parameters")
    total_cost: float = Field(0.0, ge=0.0, description="Aggregated execution cost across all tree nodes")
    total_latency: float = Field(0.0, ge=0.0, description="Aggregated execution latency across all tree nodes")
    success: bool = Field(False, description="Whether episode resulted in accepted generation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Episode metadata and director tags")

    def add_node(self, node: TraceNode) -> None:
        """Add node to trace tree and update root or best node if applicable."""
        self.nodes[node.node_id] = node
        if not self.root_node_id or node.is_root:
            self.root_node_id = node.node_id

        # Update totals
        self.total_cost = sum(n.execution_cost for n in self.nodes.values())
        self.total_latency = sum(n.latency_seconds for n in self.nodes.values())

        # Update best node tracking
        if node.hard_gates_passed:
            if not self.best_node_id:
                self.best_node_id = node.node_id
            else:
                cur_best = self.nodes.get(self.best_node_id)
                if cur_best and node.quality_score > cur_best.quality_score:
                    self.best_node_id = node.node_id

    def get_node(self, node_id: str) -> Optional[TraceNode]:
        """Retrieve node by ID."""
        return self.nodes.get(node_id)

    def get_root_node(self) -> Optional[TraceNode]:
        """Retrieve root node."""
        return self.nodes.get(self.root_node_id)

    def get_best_node(self) -> Optional[TraceNode]:
        """Retrieve the highest scoring valid node in tree."""
        if not self.nodes:
            return None
        if self.best_node_id and self.best_node_id in self.nodes:
            node = self.nodes[self.best_node_id]
            if node.hard_gates_passed:
                return node
        # Fallback: Find max quality node passing hard gates
        valid_nodes = [n for n in self.nodes.values() if n.hard_gates_passed]
        if valid_nodes:
            return max(valid_nodes, key=lambda n: n.quality_score)
        # If no node passed hard gates, return best node by score
        if self.best_node_id and self.best_node_id in self.nodes:
            return self.nodes[self.best_node_id]
        return max(self.nodes.values(), key=lambda n: n.quality_score)

    def get_leaf_nodes(self) -> List[TraceNode]:
        """Return all nodes that have no child nodes."""
        parent_ids = {n.parent_id for n in self.nodes.values() if n.parent_id is not None}
        return [n for n in self.nodes.values() if n.node_id not in parent_ids]

    def get_trajectory(self, target_node_id: Optional[str] = None) -> List[TraceNode]:
        """Reconstruct linear path from root to specified node (or best node)."""
        best = self.get_best_node()
        curr_id = target_node_id or (self.best_node_id if self.best_node_id in self.nodes else None) or (best.node_id if best else None)
        if not curr_id or curr_id not in self.nodes:
            return []

        path: List[TraceNode] = []
        visited = set()
        while curr_id and curr_id in self.nodes and curr_id not in visited:
            visited.add(curr_id)
            node = self.nodes[curr_id]
            path.append(node)
            curr_id = node.parent_id

        path.reverse()
        return path

    def to_dict(self) -> Dict[str, Any]:
        """Serialize tree to dict."""
        return self.model_dump(mode="json")

    def to_json(self, indent: int = 2) -> str:
        """Serialize tree to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DiscoveryTraceTree:
        """Instantiate DiscoveryTraceTree from dict."""
        if not isinstance(data, dict):
            raise ValueError(f"Expected dictionary for DiscoveryTraceTree, got {type(data)}")
        if not any(k in data for k in ("tree_id", "nodes", "shot_id", "scene_state_initial")):
            raise ValueError("Dictionary lacks DiscoveryTraceTree structural markers")
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> DiscoveryTraceTree:
        """Instantiate DiscoveryTraceTree from JSON string."""
        return cls.from_dict(json.loads(json_str))


class ReplaySimulatorWorld(BaseModel):
    """World holding indexed historical discovery trees H_t for zero-cost replay."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    world_id: str = Field(default_factory=lambda: f"world_{uuid.uuid4().hex[:8]}", description="Unique world pool identifier")
    trees: Dict[str, DiscoveryTraceTree] = Field(default_factory=dict, description="Mapping of tree IDs to DiscoveryTraceTree instances")
    created_at: float = Field(default_factory=time.time, description="Unix timestamp of pool creation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Pool metadata and dataset provenance")

    @property
    def tree_count(self) -> int:
        """Total number of historical discovery trees in the world pool."""
        return len(self.trees)

    def add_tree(self, tree: DiscoveryTraceTree) -> None:
        """Add discovery tree into historical pool."""
        self.trees[tree.tree_id] = tree

    def get_tree(self, tree_id: str) -> Optional[DiscoveryTraceTree]:
        """Retrieve tree by ID."""
        return self.trees.get(tree_id)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize world to dict."""
        return self.model_dump(mode="json")

    def to_json(self, indent: int = 2) -> str:
        """Serialize world to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ReplaySimulatorWorld:
        """Instantiate ReplaySimulatorWorld from dict."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> ReplaySimulatorWorld:
        """Instantiate ReplaySimulatorWorld from JSON string."""
        return cls.from_dict(json.loads(json_str))


class ExplorationPolicy(BaseModel):
    """Tunable routing, complexity, and repair policy for generative video compilation.

    Contains tunable hyperparameter knobs optimized by Dream-RSI:
    - Complexity classification thresholds (velocity, actor counts, movements)
    - Generative model priority weights (Veo, Kling, Runway, ComfyUI)
    - Repair IoU and escalation thresholds
    - Frontier inference acceleration flags (TeaCache, PAB, Distilled Flow Sampling)
    - Dream-RSI Pareto objective weights (beta1, beta2)
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    policy_id: str = Field(default_factory=lambda: f"policy_{uuid.uuid4().hex[:8]}", description="Unique policy identifier")
    name: str = Field("StandardExplorationPolicy", description="Human-readable policy title")
    version: str = Field("1.0.0", description="Policy version string")

    # Tunable Complexity Classification Knobs
    complexity_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "velocity_threshold": 3.0,
            "actor_count_blocking_threshold": 2.0,
            "actor_movement_threshold": 1.0,
            "close_proximity_threshold": 2.5,
        },
        description="Thresholds governing ComplexityPlanner transitions",
    )

    # Model Provider Routing Priority Weights
    model_priority_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "veo_3_1": 1.0,
            "kling_3_0": 1.0,
            "runway_gen_4_5": 1.0,
            "cogvideox_comfyui": 1.0,
        },
        description="Relative preference weights when routing between competitive providers",
    )

    # Surgical Repair Knobs
    repair_iou_threshold: float = Field(0.30, ge=0.0, le=1.0, description="Spatial IoU threshold for mask clustering/deduplication")
    repair_escalation_threshold: int = Field(3, ge=1, description="Max defect attempts before escalating to full shot regeneration")

    # Frontier Efficiency Knobs
    enable_teacache: bool = Field(True, description="Enable Timestep Embedding Aware Cache DiT acceleration")
    enable_pab: bool = Field(True, description="Enable Pyramid Attention Broadcast DiT layer acceleration")
    sampling_steps: int = Field(8, ge=1, le=50, description="Flow matching distilled sampling steps (e.g. 4-8 vs 30-50)")
    enable_speculative_draft: bool = Field(False, description="Enable 480p speculative draft gatekeeper")

    # Dream-RSI Pareto Objective Weights
    beta1_cost_weight: float = Field(0.05, ge=0.0, description="Penalty coefficient beta_1 for computational work / API token cost")
    beta2_parallel_weight: float = Field(0.02, ge=0.0, description="Bonus coefficient beta_2 rewarding parallel execution speedup")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Policy training metadata and provenance")

    def mutate(self, mutation_scale: float = 0.2, seed: Optional[int] = None) -> ExplorationPolicy:
        """Create a mutated candidate policy by perturbing continuous knobs and toggling flags."""
        rng = random.Random(seed) if seed is not None else random.Random()
        mutated_thresholds = dict(self.complexity_thresholds)
        for k, v in mutated_thresholds.items():
            delta = rng.uniform(-mutation_scale, mutation_scale) * v
            mutated_thresholds[k] = max(0.1, round(v + delta, 3))

        mutated_weights = dict(self.model_priority_weights)
        for k, v in mutated_weights.items():
            delta = rng.uniform(-mutation_scale, mutation_scale) * v
            mutated_weights[k] = max(0.05, round(v + delta, 3))

        new_iou = min(0.9, max(0.1, round(self.repair_iou_threshold + rng.uniform(-0.05, 0.05), 3)))
        new_escalation = max(1, min(6, self.repair_escalation_threshold + rng.choice([-1, 0, 1])))

        # Discrete steps mutation
        new_steps = self.sampling_steps
        if rng.random() < 0.3:
            new_steps = max(4, min(30, self.sampling_steps + rng.choice([-2, 0, 2])))

        # Rare flag flips for exploration
        new_teacache = self.enable_teacache if rng.random() > 0.1 else (not self.enable_teacache)
        new_pab = self.enable_pab if rng.random() > 0.1 else (not self.enable_pab)
        new_spec = self.enable_speculative_draft if rng.random() > 0.2 else (not self.enable_speculative_draft)

        return ExplorationPolicy(
            policy_id=f"policy_{uuid.uuid4().hex[:8]}",
            name=f"{self.name}_mutated",
            version=self.version,
            complexity_thresholds=mutated_thresholds,
            model_priority_weights=mutated_weights,
            repair_iou_threshold=new_iou,
            repair_escalation_threshold=new_escalation,
            enable_teacache=new_teacache,
            enable_pab=new_pab,
            sampling_steps=new_steps,
            enable_speculative_draft=new_spec,
            beta1_cost_weight=self.beta1_cost_weight,
            beta2_parallel_weight=self.beta2_parallel_weight,
            metadata={"parent_policy_id": self.policy_id, "mutation_scale": mutation_scale},
        )

    def copy_with(self, **kwargs: Any) -> ExplorationPolicy:
        """Return a copy of policy with updated parameters."""
        d = self.model_dump()
        d.update(kwargs)
        return ExplorationPolicy(**d)


class DreamEvaluationResult(BaseModel):
    """Aggregate offline evaluation outcome for a policy across historical replay simulator trees."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    policy_id: str = Field(..., description="Evaluated exploration policy identifier")
    policy_name: str = Field("", description="Policy title")
    num_episodes_replayed: int = Field(0, description="Total discovery trees evaluated during offline dreaming")
    mean_quality_score: float = Field(0.0, description="Average quality score s_v across replayed episodes (0.0 to 10.0)")
    hard_gate_pass_rate: float = Field(0.0, ge=0.0, le=1.0, description="Fraction of episodes that satisfied all hard gates")
    mean_cost: float = Field(0.0, description="Average computational work N_im across episodes")
    mean_latency: float = Field(0.0, description="Average execution wall-clock latency in seconds")
    pareto_value: float = Field(0.0, description="Dream-RSI Pareto objective value V_im")
    is_pareto_superior: bool = Field(False, description="Whether this policy strictly outperforms the baseline")
    episode_scores: List[Dict[str, Any]] = Field(default_factory=list, description="Per-episode simulation metrics")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed diagnostic breakdown")


class ProductionRule(BaseModel):
    """Codified, verified production heuristic promoted to the studio knowledge ledger."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    rule_id: str = Field(default_factory=lambda: f"rule_{uuid.uuid4().hex[:8]}", description="Unique rule identifier")
    rule_type: str = Field("ROUTING", description="Rule classification: ROUTING, COMPLEXITY, REPAIR, or EFFICIENCY")
    condition: Dict[str, Any] = Field(default_factory=dict, description="Activation conditions (e.g. {'velocity_gte': 3.0})")
    action: Dict[str, Any] = Field(default_factory=dict, description="Applied configuration or routing override")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Empirical confidence score derived from offline dreaming")
    provenance_policy_id: Optional[str] = Field(None, description="Policy from which this rule was distilled")
    description: str = Field("", description="Human-readable explanation of production rule rationale")
    active: bool = Field(True, description="Whether this rule is active in live runtime production")
    created_at: float = Field(default_factory=time.time, description="Unix timestamp of rule creation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Rule metrics and performance delta")

    def matches(self, context: Dict[str, Any]) -> bool:
        """Evaluate whether the given context satisfies this rule's condition predicates."""
        for key, expected in self.condition.items():
            if key not in context:
                # Check for suffix operators e.g. "count_gt", "velocity_gte"
                matched_suffix = False
                for op, comp in (
                    ("_gt", lambda a, b: a > b),
                    ("_gte", lambda a, b: a >= b),
                    ("_lt", lambda a, b: a < b),
                    ("_lte", lambda a, b: a <= b),
                    ("_eq", lambda a, b: a == b),
                    ("_ne", lambda a, b: a != b),
                    ("_in", lambda a, b: a in b),
                ):
                    if key.endswith(op):
                        base_key = key[:-len(op)]
                        if base_key in context:
                            if not comp(context[base_key], expected):
                                return False
                            matched_suffix = True
                            break
                if not matched_suffix:
                    return False
                continue

            val = context[key]
            if isinstance(expected, dict):
                # Operator predicates: gt, gte, lt, lte, eq, in
                if "gt" in expected and not (val > expected["gt"]):
                    return False
                if "gte" in expected and not (val >= expected["gte"]):
                    return False
                if "lt" in expected and not (val < expected["lt"]):
                    return False
                if "lte" in expected and not (val <= expected["lte"]):
                    return False
                if "eq" in expected and not (val == expected["eq"]):
                    return False
                if "in" in expected and val not in expected["in"]:
                    return False
            else:
                if val != expected:
                    return False
        return True
