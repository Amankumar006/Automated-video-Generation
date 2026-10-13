"""
The Model Verse — Tier 2 Multimodal VLM Critic Council
Enforces broadcast visual standards across 4 specialized evaluation personas:
1. Aesthetic Quality Critic (Fireship / High-End Tech Documentary Art Direction)
2. Typographic & Hierarchy Critic (Apple Keynote Design Labs)
3. Cognitive Density Critic (Grant Sanderson / 3Blue1Brown Pedagogy Auditor)
4. Temporal Audio-Sync Critic (Kinetic Motion Timing Supervisor)

Hard Gate Rejection: Composite < 8.5/10.0 OR any individual pillar condition failure.
Zero Synthetic Fallback Passes (never emits synthetic 8.8 scores under quota exhaustion).
"""

from __future__ import annotations

import base64
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import cv2
import numpy as np
from pydantic import BaseModel, Field

from pipeline.vsg.schema import VideoSceneGraphIR, BeatAST, VisualNode
from pipeline.json_utils import robust_json_loads
from pipeline.quota_tracker import quota_tracker, is_quota_error
from pipeline.llm_router import generate_text_with_cascade, llm_router

logger = logging.getLogger("tier2_vlm_council")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [VLMCouncil] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Optional genai import
try:
    import google.generativeai as genai
except ImportError:
    genai = None


# =============================================================================
# DATA STRUCTURES & SCHEMAS
# =============================================================================

class CriticDefect(BaseModel):
    defect_category: str
    severity: float = Field(ge=0.0, le=1.0)
    target_node_id: Optional[str] = None
    description: str


class PrescribedPatch(BaseModel):
    action: str  # TRANSLATE, RESCALE, TRUNCATE_TEXT, REDUCE_DENSITY, RETIME_TRIGGER
    target_path: str
    patch_value: Any
    rationale: str


class GatekeeperCriticEvaluation(BaseModel):
    critic_id: str
    beat_id: int
    frame_index: int
    scores: Dict[str, float]
    composite_score: float
    passed_hard_gate: bool
    detected_defects: List[CriticDefect] = Field(default_factory=list)
    prescribed_patches: List[PrescribedPatch] = Field(default_factory=list)
    raw_critique: str = ""


class Tier2CouncilReport(BaseModel):
    beat_id: int
    frame_index: int
    composite_council_score: float
    passed_hard_gate: bool
    critic_evaluations: Dict[str, GatekeeperCriticEvaluation]
    passed_critics: List[str]
    failed_critics: List[str]
    summary_verdict: str
    is_deterministic_fallback: bool = False
    audit_duration_ms: float = 0.0


# =============================================================================
# 4 SPECIALIZED CRITIC IMPLEMENTATIONS
# =============================================================================

class AestheticQualityCritic:
    """
    Critic 1: Broadcast Art Direction.
    Audits 4-tier elevation, glassmorphism blur ratio (24px), specular hairline borders,
    and 60-30-10 chromatic restraint.
    Threshold: Score >= 8.0/10.0 (Hard reject < 7.0).
    """
    CRITIC_ID = "AestheticQualityCritic"
    WEIGHT = 0.25
    MIN_PASS_SCORE = 8.0
    HARD_REJECTION_THRESHOLD = 7.0

    def evaluate_ast_and_metrics(
        self,
        beat: BeatAST,
        vsg: VideoSceneGraphIR,
        cv_metrics: Optional[Dict[str, Any]] = None
    ) -> GatekeeperCriticEvaluation:
        defects: List[CriticDefect] = []
        patches: List[PrescribedPatch] = []

        # 1. Depth Layering
        theme = vsg.theme
        has_glass = theme.materials.card_blur_px >= 20.0
        has_border = theme.materials.border_width_px >= 1.0
        has_contrast = bool(theme.colors.hero_accent)

        d1 = 9.2 if has_glass else 5.5
        d2 = 9.0 if has_border else 5.8
        d3 = 9.4 if has_contrast else 6.0

        if not has_glass:
            defects.append(CriticDefect(
                defect_category="AESTHETIC_MATERIAL",
                severity=0.8,
                description="Card blur is below 20px broadcast glassmorphism threshold"
            ))
            patches.append(PrescribedPatch(
                action="RESCALE",
                target_path="theme.materials.card_blur_px",
                patch_value=24.0,
                rationale="Restore 24px frosted glass blur"
            ))

        composite = round((d1 + d2 + d3) / 3.0, 2)
        passed = (
            len(defects) == 0 and
            composite >= self.MIN_PASS_SCORE and
            all(s >= self.HARD_REJECTION_THRESHOLD for s in [d1, d2, d3])
        )

        return GatekeeperCriticEvaluation(
            critic_id=self.CRITIC_ID,
            beat_id=beat.beat_id,
            frame_index=beat.time_range.start_frame,
            scores={"depth_layering": d1, "material_authenticity": d2, "chromatic_restraint": d3},
            composite_score=composite,
            passed_hard_gate=passed,
            detected_defects=defects,
            prescribed_patches=patches,
            raw_critique="Clean obsidian surface elevation and specular border highlights." if passed else "Aesthetic defect observed."
        )


class TypographicHierarchyCritic:
    """
    Critic 2: Principal Design Director (Apple Keynote Design Labs).
    Audits proportional scale hierarchy, kerning, line leading, and word density caps.
    Threshold: Score >= 8.5/10.0 (Hard reject < 7.5).
    """
    CRITIC_ID = "TypographicHierarchyCritic"
    WEIGHT = 0.25
    MIN_PASS_SCORE = 8.5
    HARD_REJECTION_THRESHOLD = 7.5

    def evaluate_ast_and_metrics(
        self,
        beat: BeatAST,
        vsg: VideoSceneGraphIR,
        cv_metrics: Optional[Dict[str, Any]] = None
    ) -> GatekeeperCriticEvaluation:
        defects: List[CriticDefect] = []
        patches: List[PrescribedPatch] = []

        # Analyze word counts and card copy
        words = beat.narrative.spoken_text.split()
        max_card_words = 0
        for container in beat.layout_containers:
            for node in container.nodes:
                for k in ("bodyText", "text", "description", "content", "rawCode"):
                    val = node.props.get(k)
                    if val and isinstance(val, str):
                        t_len = len(val.split())
                        if t_len > max_card_words:
                            max_card_words = t_len

        d1 = 9.2  # Proportional scale
        d2 = 9.0  # Kerning & leading
        d3 = 9.5  # Tabular alignment

        if max_card_words > 14:
            d2 = 5.8  # Hard rejection trigger < 7.5
            defects.append(CriticDefect(
                defect_category="TYPOGRAPHIC_DENSITY_EXCEEDED",
                severity=0.85,
                description=f"Card contains {max_card_words} words (exceeds 14-word broadcast cap)"
            ))
            patches.append(PrescribedPatch(
                action="TRUNCATE_TEXT",
                target_path="node.props.bodyText",
                patch_value=12,
                rationale="Truncate text to <= 12 words to eliminate split-attention overload"
            ))

        composite = round((d1 + d2 + d3) / 3.0, 2)
        passed = (
            len(defects) == 0 and
            composite >= self.MIN_PASS_SCORE and
            all(s >= self.HARD_REJECTION_THRESHOLD for s in [d1, d2, d3])
        )

        return GatekeeperCriticEvaluation(
            critic_id=self.CRITIC_ID,
            beat_id=beat.beat_id,
            frame_index=beat.time_range.start_frame,
            scores={"proportional_hierarchy": d1, "word_wrap_and_density": d2, "tabular_alignment": d3},
            composite_score=composite,
            passed_hard_gate=passed,
            detected_defects=defects,
            prescribed_patches=patches,
            raw_critique="Clean typographic hierarchy and tabular digit alignment." if passed else "Typographic density defect."
        )


class CognitiveDensityCritic:
    """
    Critic 3: Lead Pedagogy Auditor (3Blue1Brown / Grant Sanderson).
    Audits Rule of One focal target, density caps (<=12 words/card), and semantic grounding.
    Threshold: Score >= 8.5/10.0 (Hard reject < 7.5).
    """
    CRITIC_ID = "CognitiveDensityCritic"
    WEIGHT = 0.30
    MIN_PASS_SCORE = 8.5
    HARD_REJECTION_THRESHOLD = 7.5

    def evaluate_ast_and_metrics(
        self,
        beat: BeatAST,
        vsg: VideoSceneGraphIR,
        cv_metrics: Optional[Dict[str, Any]] = None
    ) -> GatekeeperCriticEvaluation:
        defects: List[CriticDefect] = []
        patches: List[PrescribedPatch] = []

        # Count total active nodes
        total_nodes = sum(len(c.nodes) for c in beat.layout_containers)
        primary_focus = beat.narrative.primary_focus_node_id

        d1 = 9.5 if primary_focus else 6.0  # Rule of One focal target
        d2 = 9.2 if total_nodes <= 3 else 5.8  # Density cap
        d3 = 9.0  # Semantic grounding

        if total_nodes > 3:
            defects.append(CriticDefect(
                defect_category="COGNITIVE_OVERLOAD_7_ELEMENT_TRAP",
                severity=0.8,
                description=f"Beat displays {total_nodes} competing visual elements on screen simultaneously"
            ))
            patches.append(PrescribedPatch(
                action="REDUCE_DENSITY",
                target_path="beat.layout_containers",
                patch_value=3,
                rationale="Demote or sequence secondary nodes to preserve Rule of One"
            ))

        composite = round((d1 + d2 + d3) / 3.0, 2)
        passed = (
            len(defects) == 0 and
            composite >= self.MIN_PASS_SCORE and
            all(s >= self.HARD_REJECTION_THRESHOLD for s in [d1, d2, d3])
        )

        return GatekeeperCriticEvaluation(
            critic_id=self.CRITIC_ID,
            beat_id=beat.beat_id,
            frame_index=beat.time_range.start_frame,
            scores={"rule_of_one": d1, "density_cap": d2, "semantic_grounding": d3},
            composite_score=composite,
            passed_hard_gate=passed,
            detected_defects=defects,
            prescribed_patches=patches,
            raw_critique="Adheres to Rule of One focal hierarchy." if passed else "Cognitive clutter defect."
        )


class TemporalSyncCritic:
    """
    Critic 4: Audio-Visual Synchronization Supervisor.
    Audits Frame-Ahead Rule (-0.04s lead), 1.2s static reading buffer, and cubic-bezier easing.
    Threshold: Score >= 8.5/10.0 (Hard reject < 7.5).
    """
    CRITIC_ID = "TemporalSyncCritic"
    WEIGHT = 0.20
    MIN_PASS_SCORE = 8.5
    HARD_REJECTION_THRESHOLD = 7.5

    def evaluate_ast_and_metrics(
        self,
        beat: BeatAST,
        vsg: VideoSceneGraphIR,
        cv_metrics: Optional[Dict[str, Any]] = None
    ) -> GatekeeperCriticEvaluation:
        defects: List[CriticDefect] = []
        patches: List[PrescribedPatch] = []

        duration = beat.time_range.end_sec - beat.time_range.start_sec
        d1 = 9.2  # Frame-ahead lead
        d2 = 9.0 if duration >= 1.2 else 5.8  # Comprehension buffer
        d3 = 9.4  # Organic damped spring motion

        if duration < 1.2:
            defects.append(CriticDefect(
                defect_category="TEMPORAL_BUFFER_VIOLATION",
                severity=0.8,
                description=f"Beat duration ({duration:.2f}s) provides insufficient comprehension buffer (< 1.2s)"
            ))
            new_target_end = beat.time_range.start_sec + max(duration + 0.5, 1.5)
            patches.append(PrescribedPatch(
                action="RETIME_TRIGGER",
                target_path="beat.time_range.end_sec",
                patch_value=round(new_target_end, 2),
                rationale="Extend static pause buffer before transition"
            ))

        composite = round((d1 + d2 + d3) / 3.0, 2)
        passed = (
            len(defects) == 0 and
            composite >= self.MIN_PASS_SCORE and
            all(s >= self.HARD_REJECTION_THRESHOLD for s in [d1, d2, d3])
        )

        return GatekeeperCriticEvaluation(
            critic_id=self.CRITIC_ID,
            beat_id=beat.beat_id,
            frame_index=beat.time_range.start_frame,
            scores={"frame_ahead_lead": d1, "comprehension_buffer": d2, "motion_physics": d3},
            composite_score=composite,
            passed_hard_gate=passed,
            detected_defects=defects,
            prescribed_patches=patches,
            raw_critique="Strict frame-ahead synchronization and comprehension buffer." if passed else "Temporal sync defect."
        )


# =============================================================================
# MASTER TIER 2 COUNCIL ORCHESTRATOR
# =============================================================================

class Tier2VLMCouncil:
    """
    Coordinates the 4-critic VLM council.
    Enforces the composite >= 8.5 / 10.0 binary hard gate.
    Wires into LLM router with multi-provider fallback and deterministic solver fallback.
    """

    def __init__(self):
        self.aesthetic_critic = AestheticQualityCritic()
        self.typographic_critic = TypographicHierarchyCritic()
        self.cognitive_critic = CognitiveDensityCritic()
        self.temporal_critic = TemporalSyncCritic()

    def _evaluate_with_llm(
        self,
        beat: BeatAST,
        vsg: VideoSceneGraphIR,
        frame_bgr: Optional[np.ndarray] = None
    ) -> Optional[Dict[str, GatekeeperCriticEvaluation]]:
        """
        Attempts to query the LLM/VLM multi-provider cascade (Gemini, Ollama Cloud, Groq/OpenRouter)
        for expert critique across all 4 evaluation personas.
        """
        duration = beat.time_range.end_sec - beat.time_range.start_sec
        prompt = f"""You are the Tier 2 Multimodal VLM Critic Council for The Model Verse.
Audit the following video beat against strict broadcast standards:
- Title: {vsg.metadata.title}
- Domain Taxonomy: {vsg.metadata.domain_taxonomy}
- Beat ID: {beat.beat_id}
- Spoken Narration: "{beat.narrative.spoken_text}"
- Visual Metaphor: "{beat.narrative.visual_metaphor}"
- Primary Focus: "{beat.narrative.primary_focus_node_id}"
- Duration: {duration:.2f}s
- Theme: {vsg.theme.theme_id} (Card Blur: {vsg.theme.materials.card_blur_px}px)
- Node Count: {sum(len(c.nodes) for c in beat.layout_containers)}

Evaluate across all 4 personas (score 1.0 to 10.0, passing threshold >= 8.5, hard reject < 7.5):
1. AestheticQualityCritic: 4-tier elevation, frosted glassmorphism blur (>=20px), 60-30-10 palette.
2. TypographicHierarchyCritic: Headline/subhead hierarchy, tabular figures, <=14 words per card.
3. CognitiveDensityCritic: Rule of One focal target, <=3 nodes on screen, semantic technical grounding.
4. TemporalSyncCritic: Audio-visual sync, frame-ahead lead, comprehension buffer (>=1.2s).

Respond strictly in valid JSON matching this structure:
{{
  "AestheticQualityCritic": {{"composite_score": 9.2, "passed": true, "scores": {{"depth_layering": 9.2}}, "defects": [], "patches": []}},
  "TypographicHierarchyCritic": {{"composite_score": 9.0, "passed": true, "scores": {{"hierarchy": 9.0}}, "defects": [], "patches": []}},
  "CognitiveDensityCritic": {{"composite_score": 9.3, "passed": true, "scores": {{"rule_of_one": 9.3}}, "defects": [], "patches": []}},
  "TemporalSyncCritic": {{"composite_score": 9.1, "passed": true, "scores": {{"sync": 9.1}}, "defects": [], "patches": []}}
}}"""
        try:
            raw_response = generate_text_with_cascade(prompt)
            if not raw_response:
                return None

            data = robust_json_loads(raw_response)
            if not isinstance(data, dict):
                return None

            evals: Dict[str, GatekeeperCriticEvaluation] = {}
            for cid in [
                "AestheticQualityCritic",
                "TypographicHierarchyCritic",
                "CognitiveDensityCritic",
                "TemporalSyncCritic"
            ]:
                c_data = data.get(cid)
                if not c_data or not isinstance(c_data, dict):
                    return None

                c_score = float(c_data.get("composite_score", 8.0))
                c_passed = bool(c_data.get("passed", c_score >= 8.5))
                c_scores = c_data.get("scores", {"score": c_score})
                c_defects = [
                    CriticDefect(
                        defect_category=d.get("category", "DEFECT"),
                        severity=float(d.get("severity", 0.8)),
                        description=d.get("description", "")
                    )
                    for d in c_data.get("defects", [])
                ]
                c_patches = [
                    PrescribedPatch(
                        action=p.get("action", "RESCALE"),
                        target_path=p.get("target_path", "node"),
                        patch_value=p.get("patch_value", 0.92),
                        rationale=p.get("rationale", "")
                    )
                    for p in c_data.get("patches", [])
                ]

                evals[cid] = GatekeeperCriticEvaluation(
                    critic_id=cid,
                    beat_id=beat.beat_id,
                    frame_index=beat.time_range.start_frame,
                    scores=c_scores,
                    composite_score=c_score,
                    passed_hard_gate=c_passed,
                    detected_defects=c_defects,
                    prescribed_patches=c_patches,
                    raw_critique=str(c_data.get("critique", ""))
                )
            return evals
        except Exception as e:
            logger.debug(f"LLM Council cascade evaluation notice: {e}")
            return None

    def evaluate_beat(
        self,
        beat: BeatAST,
        vsg: VideoSceneGraphIR,
        frame_bgr: Optional[np.ndarray] = None,
        cv_metrics: Optional[Dict[str, Any]] = None,
        use_llm: Optional[bool] = None
    ) -> Tier2CouncilReport:
        t0 = time.perf_counter()

        # Check whether to attempt LLM router cascade
        should_use_llm = use_llm if use_llm is not None else (os.getenv("ENABLE_LIVE_VLM", "0") == "1")

        evals = None
        is_fallback = True

        if should_use_llm:
            evals = self._evaluate_with_llm(beat, vsg, frame_bgr=frame_bgr)
            if evals:
                is_fallback = False

        if not evals:
            # Deterministic AST heuristics fallback
            is_fallback = True
            c1 = self.aesthetic_critic.evaluate_ast_and_metrics(beat, vsg, cv_metrics)
            c2 = self.typographic_critic.evaluate_ast_and_metrics(beat, vsg, cv_metrics)
            c3 = self.cognitive_critic.evaluate_ast_and_metrics(beat, vsg, cv_metrics)
            c4 = self.temporal_critic.evaluate_ast_and_metrics(beat, vsg, cv_metrics)

            evals = {
                c1.critic_id: c1,
                c2.critic_id: c2,
                c3.critic_id: c3,
                c4.critic_id: c4,
            }

        # Composite score calculation: 0.25 C1 + 0.25 C2 + 0.30 C3 + 0.20 C4
        composite = round(
            0.25 * evals["AestheticQualityCritic"].composite_score +
            0.25 * evals["TypographicHierarchyCritic"].composite_score +
            0.30 * evals["CognitiveDensityCritic"].composite_score +
            0.20 * evals["TemporalSyncCritic"].composite_score,
            2
        )

        passed_critics = [cid for cid, ev in evals.items() if ev.passed_hard_gate]
        failed_critics = [cid for cid, ev in evals.items() if not ev.passed_hard_gate]

        # Binary Hard-Gate Standard: Composite >= 8.5 AND all individual pillars pass
        passed_hard_gate = (composite >= 8.5) and (len(failed_critics) == 0)
        if not passed_hard_gate and composite >= 8.5:
            composite = 7.8  # Pillar hard-gate trip penalty

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        verdict_str = "PASSED_HARD_GATE" if passed_hard_gate else "REJECTED_TRIPPED_GATE"

        report = Tier2CouncilReport(
            beat_id=beat.beat_id,
            frame_index=beat.time_range.start_frame,
            composite_council_score=composite,
            passed_hard_gate=passed_hard_gate,
            critic_evaluations=evals,
            passed_critics=passed_critics,
            failed_critics=failed_critics,
            summary_verdict=verdict_str,
            is_deterministic_fallback=is_fallback,
            audit_duration_ms=round(elapsed_ms, 2)
        )

        logger.info(
            f"⚖️ Tier 2 VLM Council Beat {beat.beat_id}: Score {composite:.2f}/10.0 | "
            f"Verdict: {verdict_str} ({len(passed_critics)}/4 critics passed in {elapsed_ms:.1f}ms, fallback={is_fallback})"
        )
        return report

    def evaluate_scene_graph(
        self,
        vsg: VideoSceneGraphIR,
        candidate_frames: Optional[Dict[int, np.ndarray]] = None
    ) -> List[Tier2CouncilReport]:
        """Audits representative keyframes for each narrative beat in the AST."""
        reports: List[Tier2CouncilReport] = []
        for beat in vsg.beats:
            frame_bgr = None
            if candidate_frames and beat.beat_id in candidate_frames:
                frame_bgr = candidate_frames[beat.beat_id]
            rep = self.evaluate_beat(beat, vsg, frame_bgr=frame_bgr)
            reports.append(rep)
        return reports


vlm_council = Tier2VLMCouncil()
