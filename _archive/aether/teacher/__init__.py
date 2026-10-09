"""Project Aether Phase 9: Dream-RSI Teacher Engine & Recursive Self-Improvement (WBS 1.10).

Adopting the breakthrough Dream-RSI framework (arXiv:2609.14858v1):
1. Online Exploration & Trace Logging: Records render episodes into immutable DiscoveryTraceTree objects.
2. Replay Simulator Pool (H_t): Holds historical discovery trees for zero-cost counterfactual replay.
3. Offline Policy Dreaming: Evaluates candidate policies over the replay pool optimizing the Dream-RSI
   Pareto objective:
       V_{im} = max_v s_v - beta_1 N_{im} + beta_2 (N_{im} / max(1, k*_{im}))
4. Production Knowledge Ledger: Codifies Pareto-superior policies pi_{t+1} into verified production rules
   and redeploys to ComplexityPlanner, ShotCompiler, and RepairPlanner.
"""

from __future__ import annotations

from aether.teacher.schemas import (
    DiscoveryTraceTree,
    DreamEvaluationResult,
    ExplorationPolicy,
    ProductionRule,
    ReplaySimulatorWorld,
    TraceNode,
)
from aether.teacher.trace_logger import TraceLogger
from aether.teacher.replay_simulator import ReplaySimulatorPool
from aether.teacher.dreamer import PolicyDreamer
from aether.teacher.ledger import ProductionKnowledgeLedger

__all__ = [
    # Schemas
    "TraceNode",
    "DiscoveryTraceTree",
    "ReplaySimulatorWorld",
    "ExplorationPolicy",
    "DreamEvaluationResult",
    "ProductionRule",
    # Engine Components
    "TraceLogger",
    "ReplaySimulatorPool",
    "PolicyDreamer",
    "ProductionKnowledgeLedger",
]
