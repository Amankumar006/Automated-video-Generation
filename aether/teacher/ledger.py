"""Project Aether Production Knowledge Ledger.

Curates verified production rules and exports active runtime policies
to ComplexityPlanner, ShotCompiler, and RepairPlanner (WBS 1.10.4 / arXiv:2609.14858v1).
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Union

from aether.compiler.complexity import ComplexityPlanner
from aether.compiler.compiler import ShotCompiler
from aether.repair.planner import RepairPlanner
from aether.teacher.schemas import (
    DreamEvaluationResult,
    ExplorationPolicy,
    ProductionRule,
)


class ProductionKnowledgeLedger:
    """Production Knowledge Ledger managing active policies and codified studio rules."""

    def __init__(
        self,
        active_policy: Optional[ExplorationPolicy] = None,
        storage_file: Optional[Union[str, Path]] = None,
    ) -> None:
        self.active_policy = active_policy or ExplorationPolicy(name="Studio_Baseline_Policy")
        self.storage_file = Path(storage_file) if storage_file else None
        self.rules: Dict[str, ProductionRule] = {}
        self.promotions_history: List[Dict[str, Any]] = []

        # Bootstrap with foundational rules
        self._bootstrap_default_rules()

    def _bootstrap_default_rules(self) -> None:
        """Initialize ledger with baseline studio rules."""
        rule_efficiency = ProductionRule(
            rule_id="RULE_EFFICIENCY_001",
            rule_type="INFERENCE_EFFICIENCY",
            condition={"default": True},
            action={
                "enable_teacache": self.active_policy.enable_teacache,
                "enable_pab": self.active_policy.enable_pab,
                "sampling_steps": self.active_policy.sampling_steps,
                "enable_speculative_draft": self.active_policy.enable_speculative_draft,
            },
            confidence=0.98,
            provenance_policy_id=self.active_policy.policy_id,
            description="Frontier DiT TeaCache/PAB acceleration and 8-step distilled flow sampling",
        )
        self.add_rule(rule_efficiency)

        rule_complexity = ProductionRule(
            rule_id="RULE_COMPLEXITY_001",
            rule_type="COMPLEXITY_ROUTING",
            condition={"has_sim": True},
            action={"complexity_level": 5, "recommended_provider": "cogvideox_comfyui"},
            confidence=0.99,
            provenance_policy_id=self.active_policy.policy_id,
            description="Escalate complex physics, stunts, and fluid dynamics to Level 5 simulation",
        )
        self.add_rule(rule_complexity)

        rule_repair = ProductionRule(
            rule_id="RULE_REPAIR_001",
            rule_type="REPAIR_ESCALATION",
            condition={"defect_count": {"gt": self.active_policy.repair_escalation_threshold}},
            action={"escalate_full_regeneration": True},
            confidence=0.95,
            provenance_policy_id=self.active_policy.policy_id,
            description="Escalate surgical repair to full shot regeneration when defects exceed threshold",
        )
        self.add_rule(rule_repair)

    def add_rule(self, rule: ProductionRule) -> None:
        """Add or update a production rule in the ledger."""
        self.rules[rule.rule_id] = rule

    def get_rule(self, rule_id: str) -> Optional[ProductionRule]:
        """Retrieve a rule by ID."""
        return self.rules.get(rule_id)

    def get_active_rules(self, rule_type: Optional[str] = None) -> List[ProductionRule]:
        """Return all active rules, optionally filtered by rule_type."""
        rules = [r for r in self.rules.values() if r.active]
        if rule_type:
            rt_norm = rule_type.upper().strip()
            rules = [r for r in rules if r.rule_type.upper() == rt_norm]
        return rules

    def promote_policy(
        self,
        policy: ExplorationPolicy,
        evaluation_result: Optional[DreamEvaluationResult] = None,
    ) -> List[ProductionRule]:
        """Promotes winning policy pi_{t+1} from Dream-RSI to active studio production.

        Codifies its empirical parameters into immutable production rules.
        """
        self.active_policy = policy
        new_rules: List[ProductionRule] = []

        # 1. Distill Efficiency Rule
        eff_rule = ProductionRule(
            rule_type="INFERENCE_EFFICIENCY",
            condition={"active_generation": True},
            action={
                "enable_teacache": policy.enable_teacache,
                "enable_pab": policy.enable_pab,
                "sampling_steps": policy.sampling_steps,
                "enable_speculative_draft": policy.enable_speculative_draft,
            },
            confidence=0.99 if (evaluation_result and evaluation_result.is_pareto_superior) else 0.90,
            provenance_policy_id=policy.policy_id,
            description=f"Efficiency config distilled from policy {policy.name} (sampling_steps={policy.sampling_steps})",
        )
        self.add_rule(eff_rule)
        new_rules.append(eff_rule)

        # 2. Distill Complexity Rule
        comp_rule = ProductionRule(
            rule_type="COMPLEXITY_ROUTING",
            condition={"eval_thresholds": True},
            action=policy.complexity_thresholds,
            confidence=0.95,
            provenance_policy_id=policy.policy_id,
            description=f"Complexity thresholds distilled from policy {policy.name}",
        )
        self.add_rule(comp_rule)
        new_rules.append(comp_rule)

        # 3. Distill Surgical Repair Rule
        repair_rule = ProductionRule(
            rule_type="REPAIR_ESCALATION",
            condition={"repair_attempt": True},
            action={
                "repair_iou_threshold": policy.repair_iou_threshold,
                "repair_escalation_threshold": policy.repair_escalation_threshold,
            },
            confidence=0.95,
            provenance_policy_id=policy.policy_id,
            description=f"Repair thresholds (iou={policy.repair_iou_threshold}, escalation={policy.repair_escalation_threshold}) from {policy.name}",
        )
        self.add_rule(repair_rule)
        new_rules.append(repair_rule)

        # Track promotion history
        record = {
            "policy_id": policy.policy_id,
            "policy_name": policy.name,
            "timestamp": time.time(),
            "pareto_value": evaluation_result.pareto_value if evaluation_result else None,
            "mean_quality_score": evaluation_result.mean_quality_score if evaluation_result else None,
            "mean_cost": evaluation_result.mean_cost if evaluation_result else None,
            "created_rules": [r.rule_id for r in new_rules],
        }
        self.promotions_history.append(record)

        if self.storage_file:
            self.save(self.storage_file)

        return new_rules

    # -----------------------------------------------------------------------
    # Exporters to Production Engines
    # -----------------------------------------------------------------------

    def export_to_complexity_planner(
        self,
        planner: Optional[ComplexityPlanner] = None,
    ) -> ComplexityPlanner:
        """Configures or instantiates ComplexityPlanner with active ledger policy thresholds."""
        if planner:
            planner.active_policy = self.active_policy
            planner.complexity_thresholds = dict(self.active_policy.complexity_thresholds)
            return planner
        return ComplexityPlanner(
            complexity_thresholds=self.active_policy.complexity_thresholds,
            active_policy=self.active_policy,
        )

    def export_to_shot_compiler(
        self,
        compiler: Optional[ShotCompiler] = None,
    ) -> ShotCompiler:
        """Configures or instantiates ShotCompiler with active efficiency settings."""
        planner = self.export_to_complexity_planner()
        if compiler:
            compiler._planner = planner
            compiler.active_policy = self.active_policy
            compiler.default_enable_teacache = self.active_policy.enable_teacache
            compiler.default_enable_pab = self.active_policy.enable_pab
            compiler.default_sampling_steps = self.active_policy.sampling_steps
            compiler.default_enable_speculative_draft = self.active_policy.enable_speculative_draft
            return compiler
        return ShotCompiler(
            planner=planner,
            active_policy=self.active_policy,
            default_enable_teacache=self.active_policy.enable_teacache,
            default_enable_pab=self.active_policy.enable_pab,
            default_sampling_steps=self.active_policy.sampling_steps,
            default_enable_speculative_draft=self.active_policy.enable_speculative_draft,
        )

    def export_to_repair_planner(
        self,
        planner: Optional[RepairPlanner] = None,
    ) -> RepairPlanner:
        """Configures or instantiates RepairPlanner with active repair thresholds."""
        if planner:
            planner.escalation_defect_threshold = self.active_policy.repair_escalation_threshold
            planner.repair_iou_threshold = self.active_policy.repair_iou_threshold
            planner.active_policy = self.active_policy
            return planner

        return RepairPlanner(
            escalation_defect_threshold=self.active_policy.repair_escalation_threshold,
            repair_iou_threshold=self.active_policy.repair_iou_threshold,
            active_policy=self.active_policy,
        )

    # -----------------------------------------------------------------------
    # Serialization
    # -----------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Convert knowledge ledger to dictionary."""
        return {
            "active_policy": self.active_policy.model_dump(mode="json"),
            "rules": {k: r.model_dump(mode="json") for k, r in self.rules.items()},
            "promotions_history": self.promotions_history,
        }

    def save(self, file_path: Union[str, Path]) -> Path:
        """Persist knowledge ledger to JSON file."""
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        return p

    def load(self, file_path: Union[str, Path]) -> None:
        """Load knowledge ledger from JSON file."""
        p = Path(file_path)
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "active_policy" in data:
            self.active_policy = ExplorationPolicy(**data["active_policy"])
        if "rules" in data:
            self.rules = {k: ProductionRule(**v) for k, v in data["rules"].items()}
        if "promotions_history" in data:
            self.promotions_history = data["promotions_history"]

    def summary(self) -> Dict[str, Any]:
        """Provide diagnostic summary of ledger state."""
        return {
            "active_policy_id": self.active_policy.policy_id,
            "active_policy_name": self.active_policy.name,
            "total_rules": len(self.rules),
            "active_rules_count": len(self.get_active_rules()),
            "total_promotions": len(self.promotions_history),
            "efficiency_flags": {
                "enable_teacache": self.active_policy.enable_teacache,
                "enable_pab": self.active_policy.enable_pab,
                "sampling_steps": self.active_policy.sampling_steps,
                "enable_speculative_draft": self.active_policy.enable_speculative_draft,
            },
        }
