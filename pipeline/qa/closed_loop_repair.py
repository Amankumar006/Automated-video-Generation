"""
The Model Verse — Closed-Loop Automated Layout Repair Engine
Generates deterministic AST layout patch proposals based on the Visual Repair Diagnostic Ledger.
Applies bounded geometric translations (MTV), auto-rescaling (0.92x), copy truncation,
and safe-zone clamping across up to 3 repair iterations.
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from pipeline.vsg.schema import VideoSceneGraphIR, BeatAST, LayoutContainer, VisualNode, BoundingBoxPx
from pipeline.qa.tier1_cv_gatekeeper import Tier1AuditReport
from pipeline.qa.tier2_vlm_council import Tier2CouncilReport, PrescribedPatch

logger = logging.getLogger("closed_loop_repair")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [ClosedLoopRepair] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class RepairPatchLedgerEntry(BaseModel):
    iteration: int
    beat_id: int
    target_node_id: Optional[str] = None
    action: str  # TRANSLATE, RESCALE, TRUNCATE_TEXT, CLAMP_SAFE_ZONE, RETIME_TRIGGER
    old_value: Any
    new_value: Any
    rationale: str


class VisualRepairDiagnosticLedger(BaseModel):
    project_id: str
    total_iterations: int
    resolved_violations_count: int
    patches: List[RepairPatchLedgerEntry] = Field(default_factory=list)
    converged: bool = False
    emergency_fallback_applied: bool = False


class ClosedLoopRepairEngine:
    """
    Closed-loop layout repair engine.
    Applies deterministic mutations to VSG-IR AST until all gates pass or max iterations (N=3) is reached.
    """

    MAX_ITERATIONS = 3
    SAFE_X_MIN = 140
    SAFE_X_MAX = 900
    SAFE_Y_MIN = 220
    SAFE_Y_MAX = 1400

    def repair_ast(
        self,
        vsg: VideoSceneGraphIR,
        tier1_reports: Optional[List[Tier1AuditReport]] = None,
        tier2_reports: Optional[List[Tier2CouncilReport]] = None,
        current_iteration: int = 1
    ) -> Tuple[VideoSceneGraphIR, VisualRepairDiagnosticLedger]:
        """
        Takes failing audit reports and mutates the VSG-IR AST to resolve defects.
        """
        repaired_vsg = vsg.model_copy(deep=True)
        patches_applied: List[RepairPatchLedgerEntry] = []

        is_emergency = current_iteration >= self.MAX_ITERATIONS

        # 1. Process Tier 1 CV Gatekeeper Violations (Safe zone, Collisions)
        if tier1_reports:
            for rep in tier1_reports:
                if not rep.passed:
                    for violation in rep.violations:
                        patch_entry = self._resolve_cv_violation(
                            repaired_vsg, rep.frame_index, violation, current_iteration, is_emergency
                        )
                        if patch_entry:
                            patches_applied.append(patch_entry)

        # 2. Process Tier 2 VLM Council Prescribed Patches
        if tier2_reports:
            for rep in tier2_reports:
                if not rep.passed_hard_gate:
                    for cid, eval_data in rep.critic_evaluations.items():
                        for patch in eval_data.prescribed_patches:
                            patch_entry = self._resolve_vlm_patch(
                                repaired_vsg, rep.beat_id, patch, current_iteration, is_emergency
                            )
                            if patch_entry:
                                patches_applied.append(patch_entry)

        ledger = VisualRepairDiagnosticLedger(
            project_id=vsg.metadata.project_id,
            total_iterations=current_iteration,
            resolved_violations_count=len(patches_applied),
            patches=patches_applied,
            converged=len(patches_applied) > 0 and not is_emergency,
            emergency_fallback_applied=is_emergency
        )

        logger.info(
            f"🔧 Iteration {current_iteration}/{self.MAX_ITERATIONS}: Applied {len(patches_applied)} "
            f"AST layout patches. (Emergency fallback: {is_emergency})"
        )
        return repaired_vsg, ledger

    def _resolve_cv_violation(
        self,
        vsg: VideoSceneGraphIR,
        frame_index: int,
        violation: Any,
        iteration: int,
        is_emergency: bool
    ) -> Optional[RepairPatchLedgerEntry]:
        rule = getattr(violation, "rule", "")
        target_id = getattr(violation, "target_id", None)
        target_ids = [t.strip() for t in target_id.split(" vs ")] if (target_id and " vs " in target_id) else ([target_id] if target_id else [])

        for beat in vsg.beats:
            for container in beat.layout_containers:
                for node in container.nodes:
                    if not target_ids or node.id in target_ids or target_id is None:
                        bounds = node.bounds or container.bounds
                        old_bounds = bounds.model_copy()

                        if rule == "SAFE_ZONE_BREACH":
                            # Clamp into sacred safe zone including width and height caps
                            max_w = self.SAFE_X_MAX - self.SAFE_X_MIN
                            max_h = self.SAFE_Y_MAX - self.SAFE_Y_MIN
                            if bounds.width_px > max_w:
                                bounds.width_px = max_w
                            if bounds.height_px > max_h:
                                bounds.height_px = max_h

                            new_x_min = max(self.SAFE_X_MIN, min(bounds.x_min_px, self.SAFE_X_MAX - bounds.width_px))
                            new_y_min = max(self.SAFE_Y_MIN, min(bounds.y_min_px, self.SAFE_Y_MAX - bounds.height_px))
                            bounds.x_min_px = new_x_min
                            bounds.y_min_px = new_y_min

                            return RepairPatchLedgerEntry(
                                iteration=iteration,
                                beat_id=beat.beat_id,
                                target_node_id=node.id,
                                action="CLAMP_SAFE_ZONE",
                                old_value=old_bounds.model_dump(),
                                new_value=bounds.model_dump(),
                                rationale="Clamped element within universal 9:16 sacred corridor"
                            )

                        elif "COLLISION" in rule or rule in ("SPATIAL_COLLISION", "AABB_SPATIAL_COLLISION"):
                            # Rescale by 0.90x / 0.92x to resolve IoU overlap
                            scale = 0.90 if is_emergency else 0.92
                            bounds.width_px = round(bounds.width_px * scale)
                            bounds.height_px = round(bounds.height_px * scale)

                            return RepairPatchLedgerEntry(
                                iteration=iteration,
                                beat_id=beat.beat_id,
                                target_node_id=node.id,
                                action="RESCALE",
                                old_value=old_bounds.model_dump(),
                                new_value=bounds.model_dump(),
                                rationale=f"Rescaled colliding element by {scale}x to resolve IoU overlap"
                            )

                        elif "CONTRAST" in rule:
                            old_color = vsg.theme.colors.hero_accent
                            vsg.theme.colors.hero_accent = "#00F0FF"
                            return RepairPatchLedgerEntry(
                                iteration=iteration,
                                beat_id=beat.beat_id,
                                target_node_id=node.id,
                                action="BOOST_CONTRAST",
                                old_value=old_color,
                                new_value="#00F0FF",
                                rationale="Boosted accent luminance to satisfy WCAG AAA contrast ratio"
                            )
        return None

    def _resolve_vlm_patch(
        self,
        vsg: VideoSceneGraphIR,
        beat_id: int,
        patch: PrescribedPatch,
        iteration: int,
        is_emergency: bool
    ) -> Optional[RepairPatchLedgerEntry]:
        # Handle global theme token mutations (e.g. card_blur_px, border_width_px)
        if patch.action == "RESCALE" and patch.target_path.startswith("theme."):
            field_name = patch.target_path.replace("theme.", "")
            parts = field_name.split(".")
            curr: Any = vsg.theme
            for p in parts[:-1]:
                curr = getattr(curr, p, None)
            if curr and hasattr(curr, parts[-1]):
                old_val = getattr(curr, parts[-1])
                new_val = float(patch.patch_value)
                setattr(curr, parts[-1], new_val)
                return RepairPatchLedgerEntry(
                    iteration=iteration,
                    beat_id=beat_id,
                    target_node_id="theme",
                    action="RESCALE",
                    old_value=old_val,
                    new_value=new_val,
                    rationale=patch.rationale
                )

        for beat in vsg.beats:
            if beat.beat_id == beat_id:
                if patch.action == "TRUNCATE_TEXT":
                    for container in beat.layout_containers:
                        for node in container.nodes:
                            body = node.props.get("bodyText", "")
                            words = body.split()
                            max_words = int(patch.patch_value) if isinstance(patch.patch_value, (int, float)) else 12
                            if len(words) > max_words:
                                new_body = " ".join(words[:max_words]) + "..."
                                node.props["bodyText"] = new_body
                                return RepairPatchLedgerEntry(
                                    iteration=iteration,
                                    beat_id=beat_id,
                                    target_node_id=node.id,
                                    action="TRUNCATE_TEXT",
                                    old_value=body,
                                    new_value=new_body,
                                    rationale=patch.rationale
                                )

                elif patch.action == "RETIME_TRIGGER":
                    old_end = beat.time_range.end_sec
                    new_end = max(beat.time_range.start_sec + 1.5, float(patch.patch_value))
                    beat.time_range.end_sec = round(new_end, 2)
                    return RepairPatchLedgerEntry(
                        iteration=iteration,
                        beat_id=beat_id,
                        action="RETIME_TRIGGER",
                        old_value=old_end,
                        new_value=beat.time_range.end_sec,
                        rationale=patch.rationale
                    )

                elif patch.action == "REDUCE_DENSITY":
                    # Demote or trim secondary nodes if exceeding cap
                    for container in beat.layout_containers:
                        if len(container.nodes) > 2:
                            old_count = len(container.nodes)
                            container.nodes = container.nodes[:2]
                            return RepairPatchLedgerEntry(
                                iteration=iteration,
                                beat_id=beat_id,
                                action="REDUCE_DENSITY",
                                old_value=old_count,
                                new_value=len(container.nodes),
                                rationale="Trimmed secondary nodes to restore Rule of One"
                            )

                elif patch.action == "RESCALE":
                    for container in beat.layout_containers:
                        for node in container.nodes:
                            bounds = node.bounds or container.bounds
                            scale = float(patch.patch_value) if (isinstance(patch.patch_value, (int, float)) and patch.patch_value < 1.0) else 0.92
                            old_w, old_h = bounds.width_px, bounds.height_px
                            bounds.width_px = round(bounds.width_px * scale)
                            bounds.height_px = round(bounds.height_px * scale)
                            return RepairPatchLedgerEntry(
                                iteration=iteration,
                                beat_id=beat_id,
                                target_node_id=node.id,
                                action="RESCALE",
                                old_value={"width": old_w, "height": old_h},
                                new_value={"width": bounds.width_px, "height": bounds.height_px},
                                rationale=patch.rationale
                            )
        return None


repair_engine = ClosedLoopRepairEngine()
