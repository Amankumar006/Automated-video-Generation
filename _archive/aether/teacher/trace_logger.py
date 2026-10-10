"""Project Aether Discovery Trace Logger.

Serializes render episodes (SceneState -> Complexity -> Compiled Payload ->
Council Report -> Repair Plan -> Final Video Score & Cost) into immutable,
replayable DiscoveryTraceTree objects for Phase 9: Dream-RSI (WBS 1.10.1).
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Sequence, Union

from aether.compiler.schemas import ComplexityPlan, CompiledModelPayload, ShotRequirement
from aether.council.schemas import CouncilEvaluationReport, CouncilStatus
from aether.repair.schemas import RepairPlan
from aether.state.schemas import SceneState
from aether.teacher.schemas import DiscoveryTraceTree, TraceNode


class TraceLogger:
    """Serializes production render episodes into structured, immutable DiscoveryTraceTrees."""

    def __init__(self, storage_dir: Optional[Union[str, Path]] = None) -> None:
        self.storage_dir = Path(storage_dir) if storage_dir else None
        if self.storage_dir:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._history: Dict[str, DiscoveryTraceTree] = {}

    def log_episode(
        self,
        shot_id: str,
        scene_state: Union[SceneState, Dict[str, Any], Any],
        shot_requirement: Union[ShotRequirement, Dict[str, Any], Any],
        complexity_plan: Optional[Union[ComplexityPlan, Dict[str, Any]]] = None,
        compiled_payload: Optional[Union[CompiledModelPayload, Dict[str, Any]]] = None,
        council_report: Optional[Union[CouncilEvaluationReport, Dict[str, Any]]] = None,
        repair_plan: Optional[Union[RepairPlan, Dict[str, Any]]] = None,
        final_score: float = 0.0,
        final_cost: float = 0.0,
        execution_latency: float = 0.0,
        final_video_uri: Optional[str] = None,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DiscoveryTraceTree:
        """Serializes a complete render episode into a structured DiscoveryTraceTree."""
        # Normalize input states
        s_dict = scene_state if isinstance(scene_state, dict) else (
            scene_state.model_dump(mode="json") if hasattr(scene_state, "model_dump") else getattr(scene_state, "__dict__", {})
        )
        r_dict = shot_requirement if isinstance(shot_requirement, dict) else (
            shot_requirement.model_dump(mode="json") if hasattr(shot_requirement, "model_dump") else getattr(shot_requirement, "__dict__", {})
        )

        tree = DiscoveryTraceTree(
            shot_id=shot_id,
            scene_state_initial=s_dict,
            shot_requirement=r_dict,
            success=success,
            metadata=dict(metadata or {}),
        )

        # 1. Root Node: Specification & Initial Scene State
        root_node = TraceNode(
            parent_id=None,
            step_type="INITIAL_SPECIFICATION",
            inputs={"scene_state": s_dict, "shot_requirement": r_dict},
            action={"status": "INITIALIZED"},
            outputs={"shot_id": shot_id},
            quality_score=0.0,
            hard_gates_passed=True,
            execution_cost=0.0,
            latency_seconds=0.0,
        )
        tree.add_node(root_node)
        last_node_id = root_node.node_id

        # 2. Complexity Classification Node
        if complexity_plan:
            cp_dict = complexity_plan if isinstance(complexity_plan, dict) else complexity_plan.model_dump(mode="json")
            c_level = cp_dict.get("complexity_level", 0)
            comp_node = TraceNode(
                parent_id=last_node_id,
                step_type="COMPLEXITY_CLASSIFICATION",
                inputs={"shot_id": shot_id},
                action={"complexity_level": c_level, "provider_recommendation": cp_dict.get("recommended_provider")},
                outputs=cp_dict,
                quality_score=float(c_level),
                hard_gates_passed=True,
                execution_cost=0.001,
                latency_seconds=0.05,
            )
            tree.add_node(comp_node)
            last_node_id = comp_node.node_id

        # 3. Model Compilation Node
        if compiled_payload:
            payload_dict = compiled_payload if isinstance(compiled_payload, dict) else compiled_payload.model_dump(mode="json")
            comp_cost = 0.05 if payload_dict.get("enable_teacache") else 0.15
            compile_node = TraceNode(
                parent_id=last_node_id,
                step_type="PAYLOAD_COMPILATION",
                inputs={"complexity_node": last_node_id},
                action={
                    "provider_target": payload_dict.get("provider_target"),
                    "enable_teacache": payload_dict.get("enable_teacache", True),
                    "enable_pab": payload_dict.get("enable_pab", True),
                    "sampling_steps": payload_dict.get("sampling_steps", 8),
                    "enable_speculative_draft": payload_dict.get("enable_speculative_draft", False),
                },
                outputs={
                    "prompt": payload_dict.get("prompt"),
                    "provider_config": payload_dict.get("provider_config", {}),
                },
                quality_score=final_score * 0.5,
                hard_gates_passed=True,
                execution_cost=comp_cost,
                latency_seconds=0.20,
            )
            tree.add_node(compile_node)
            last_node_id = compile_node.node_id

        # 4. Critic Council Audit Node
        council_passed = True
        council_score = final_score
        if council_report:
            rep_dict = council_report if isinstance(council_report, dict) else council_report.model_dump(mode="json")
            council_passed = bool(
                rep_dict.get("passed_hard_gates", True)
                and rep_dict.get("status") in (CouncilStatus.ACCEPTED.value if hasattr(CouncilStatus.ACCEPTED, "value") else "ACCEPTED", "ACCEPTED")
            )
            council_score = float(rep_dict.get("overall_soft_score", final_score))
            audit_node = TraceNode(
                parent_id=last_node_id,
                step_type="COUNCIL_AUDIT",
                inputs={"compiled_node": last_node_id},
                action={"num_critics": 6, "vlm_context_caching": True},
                outputs=rep_dict,
                quality_score=council_score,
                hard_gates_passed=council_passed,
                execution_cost=0.015,  # 90% discounted VLM token cost
                latency_seconds=0.85,
            )
            tree.add_node(audit_node)
            last_node_id = audit_node.node_id

        # 5. Surgical Repair Node (if applicable)
        if repair_plan:
            rp_dict = repair_plan if isinstance(repair_plan, dict) else repair_plan.model_dump(mode="json")
            repair_node = TraceNode(
                parent_id=last_node_id,
                step_type="SURGICAL_REPAIR",
                inputs={"audit_node": last_node_id},
                action={
                    "total_repair_tasks": len(rp_dict.get("tasks", [])),
                    "requires_full_regeneration": rp_dict.get("requires_full_regeneration", False),
                },
                outputs=rp_dict,
                quality_score=council_score + 1.0,
                hard_gates_passed=True,
                execution_cost=0.08,
                latency_seconds=1.5,
            )
            tree.add_node(repair_node)
            last_node_id = repair_node.node_id

        # 6. Final Outcome Leaf Node
        final_node = TraceNode(
            parent_id=last_node_id,
            step_type="FINAL_OUTCOME",
            inputs={"last_step": last_node_id},
            action={"final_assembly": True},
            outputs={"final_video_uri": final_video_uri, "accepted": success},
            quality_score=final_score,
            hard_gates_passed=success,
            execution_cost=max(0.0, round(final_cost - tree.total_cost, 4)) if final_cost > tree.total_cost else 0.0,
            latency_seconds=max(0.0, round(execution_latency - tree.total_latency, 2)) if execution_latency > tree.total_latency else 0.0,
            parallel_branches=1,
            metadata={"final_video_uri": final_video_uri},
        )
        tree.add_node(final_node)
        if success:
            tree.best_node_id = final_node.node_id
        elif not tree.best_node_id:
            tree.best_node_id = last_node_id

        # Store in in-memory history
        self._history[tree.tree_id] = tree

        # Persist to disk if storage directory is configured
        if self.storage_dir:
            self.save_tree(tree, self.storage_dir / f"{tree.tree_id}.json")

        return tree

    def save_tree(self, tree: DiscoveryTraceTree, file_path: Union[str, Path]) -> Path:
        """Save DiscoveryTraceTree to JSON file."""
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(tree.to_json(indent=2))
        return p

    def load_tree(self, file_path: Union[str, Path]) -> DiscoveryTraceTree:
        """Load DiscoveryTraceTree from JSON file."""
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"Discovery trace tree file not found: {file_path}")
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            tree = DiscoveryTraceTree.from_dict(data)
        except Exception as e:
            raise ValueError(f"Failed to load discovery trace tree from {file_path}: {e}") from e
        self._history[tree.tree_id] = tree
        return tree

    def get_history(self) -> List[DiscoveryTraceTree]:
        """Return all in-memory logged discovery trace trees."""
        return list(self._history.values())

    def get_tree(self, tree_id: str) -> Optional[DiscoveryTraceTree]:
        """Retrieve discovery trace tree by ID."""
        return self._history.get(tree_id)

    def clear(self) -> None:
        """Clear in-memory logged trees."""
        self._history.clear()
