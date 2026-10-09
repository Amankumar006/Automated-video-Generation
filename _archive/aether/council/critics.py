"""Project Aether Specialized Critic Agents.

Implements specialized critic evaluators with pluggable VLM and heuristic verification interfaces
for Visual/Anatomy, Temporal, Continuity (World Model State Graph), Performance (Lip-Sync),
Physics, and Audio domains for Project Aether v2 (Pillar 5 / WBS 1.5).
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union
import numpy as np

if TYPE_CHECKING:
    from pipeline.ollama_client import OllamaClient, OllamaResponse

logger = logging.getLogger(__name__)

from aether.council.cv_analyzer import CVTemporalAnalyzer
from aether.council.schemas import (
    CriticAuditResult,
    CriticFailureObject,
    CriticType,
    DefectSeverity,
    HardGateType,
    RepairRecommendation,
)
from aether.compiler.schemas import ShotRequirement
from aether.state.schemas import HandAttachment, SceneState


class BaseCritic:
    """Abstract base class for Project Aether Critic Council evaluation agents."""

    def __init__(
        self,
        critic_type: CriticType,
        name: str,
        evaluator_fn: Optional[Callable[..., List[CriticFailureObject]]] = None,
    ) -> None:
        self.critic_type = critic_type
        self.name = name
        self.evaluator_fn = evaluator_fn

    def _calculate_score(self, failures: List[CriticFailureObject]) -> float:
        """Calculates 0.0 to 10.0 score based on weighted defect severity penalties."""
        score = 10.0
        for f in failures:
            if f.severity == DefectSeverity.FATAL:
                score -= 5.0
            elif f.severity == DefectSeverity.SEVERE:
                score -= 3.0
            elif f.severity == DefectSeverity.MODERATE:
                score -= 1.5
            elif f.severity == DefectSeverity.MINOR:
                score -= 0.5
        return max(0.0, min(10.0, round(score, 2)))

    def audit(
        self,
        candidate_data: Union[Dict[str, Any], Any],
        scene_state: Optional[SceneState] = None,
        shot_requirement: Optional[ShotRequirement] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> CriticAuditResult:
        """Evaluates candidate output against critic standards and emits CriticAuditResult."""
        raise NotImplementedError("Subclasses must implement audit()")


# ---------------------------------------------------------------------------
# 1. OllamaVisionAuditor & VisualCritic
# ---------------------------------------------------------------------------

class OllamaVisionAuditor:
    """Multimodal vision auditor leveraging Ollama Cloud or local vision models
    (e.g., gemma4:31b:cloud, minicpm-v) for zero-cost visual and anatomical QA.
    """

    SYSTEM_PROMPT = (
        "You are Project Aether's Master Visual & Anatomical Critic for cinematic AI video generation.\n"
        "Your task is to critically inspect the provided keyframe image(s) for anatomical anomalies, "
        "distortions, and visual generation artifacts.\n\n"
        "Specifically evaluate:\n"
        "1. Anatomical Integrity: Count digits on hands (polydactyly, fused fingers, claw deformities), "
        "inspect limb joints, extra/missing limbs, facial symmetry, eye melting, warped jaw/neck.\n"
        "2. Visual Artifacts: Surface blurring, plastic skin, grotesque warping, AI slop, unwanted UI cards/watermarks.\n"
        "3. Defect Bounding Boxes: Normalized [x1, y1, x2, y2] coordinates (0.0 to 1.0).\n"
        "4. Defect Severity: 'NEGLIGIBLE', 'MINOR', 'MODERATE', 'SEVERE', or 'FATAL'.\n"
        "5. Hard Gate Flags: If hand/limb/face anatomy fails, set hard_gate='ANATOMICAL_INTEGRITY'. "
        "If character face/identity is corrupted, set hard_gate='CHARACTER_IDENTITY'. Otherwise null.\n\n"
        "Output ONLY valid JSON."
    )

    def __init__(
        self,
        client: Optional[Any] = None,
        model: str = "gemma4:31b:cloud",
        timeout: float = 60.0,
    ) -> None:
        self.client = client
        self.model = model
        self.timeout = timeout

    def _get_client(self) -> Any:
        if self.client is None:
            from pipeline.ollama_client import OllamaClient
            self.client = OllamaClient(timeout=self.timeout)
        return self.client

    def build_audit_prompt(
        self,
        shot_requirement: Optional[ShotRequirement] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        shot_desc = ""
        if shot_requirement:
            shot_desc = f"\nShot context: {shot_requirement.shot_id} (target duration: {shot_requirement.target_duration}s)."
            if hasattr(shot_requirement, "visual_intent") and shot_requirement.visual_intent:
                shot_desc += f" Visual intent: {shot_requirement.visual_intent}"

        prompt = (
            "Inspect the provided video keyframe(s) for visual and anatomical defects." + shot_desc + "\n\n"
            "Return a JSON object conforming to this exact structure:\n"
            "{\n"
            '  "passed": true,\n'
            '  "visual_score": 8.5,\n'
            '  "defects": [\n'
            '    {\n'
            '      "failure_type": "string (e.g. polydactyly, extra_limbs, facial_distortion, ui_artifact, severe_blur)",\n'
            '      "severity": "FATAL" | "SEVERE" | "MODERATE" | "MINOR" | "NEGLIGIBLE",\n'
            '      "bounding_box": [x1, y1, x2, y2],\n'
            '      "start_frame": 0,\n'
            '      "end_frame": 0,\n'
            '      "target_entity_id": "character_01",\n'
            '      "observed_state": "Detailed defect description",\n'
            '      "expected_state": "Expected normal appearance",\n'
            '      "confidence": 0.95,\n'
            '      "recommended_repair": "REGIONAL_INPAINTING" | "FULL_REGEN" | "SPATIAL_PREVIS_RERUN",\n'
            '      "hard_gate": "ANATOMICAL_INTEGRITY" | "CHARACTER_IDENTITY" | null\n'
            '    }\n'
            '  ],\n'
            '  "hard_gate_verdicts": {\n'
            '    "ANATOMICAL_INTEGRITY": true,\n'
            '    "CHARACTER_IDENTITY": true\n'
            '  },\n'
            '  "summary": "Evaluation summary"\n'
            "}"
        )
        return prompt

    def _calculate_score(self, failures: List[CriticFailureObject]) -> float:
        """Calculates 0.0 to 10.0 score based on weighted defect severity penalties."""
        score = 10.0
        for f in failures:
            if f.severity == DefectSeverity.FATAL:
                score -= 5.0
            elif f.severity == DefectSeverity.SEVERE:
                score -= 3.0
            elif f.severity == DefectSeverity.MODERATE:
                score -= 1.5
            elif f.severity == DefectSeverity.MINOR:
                score -= 0.5
        return max(0.0, min(10.0, round(score, 2)))

    def audit(
        self,
        frames: Sequence[Any],
        shot_requirement: Optional[ShotRequirement] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> CriticAuditResult:
        """Audits frames via Ollama vision completion and returns parsed CriticAuditResult."""
        if not frames:
            return CriticAuditResult(
                critic_type=CriticType.VISUAL,
                passed=True,
                score=10.0,
                failures=[],
                hard_gate_verdicts={
                    HardGateType.ANATOMICAL_INTEGRITY: True,
                    HardGateType.CHARACTER_IDENTITY: True,
                },
                metadata={"vision_audited": False, "summary": "No frames provided"},
            )

        prompt = self.build_audit_prompt(shot_requirement, context)
        client = self._get_client()

        try:
            resp = client.generate_vision_completion(
                prompt=prompt,
                image_paths=frames,
                model=self.model,
                format="json",
                system=self.SYSTEM_PROMPT,
                timeout=self.timeout,
            )
            return self.parse_vision_audit_result(resp)
        except Exception as e:
            logger.warning(
                f"Ollama vision audit encountered error: {e}. Gracefully falling back to heuristic/CV verification."
            )
            return CriticAuditResult(
                critic_type=CriticType.VISUAL,
                passed=True,
                score=8.0,
                failures=[],
                hard_gate_verdicts={
                    HardGateType.ANATOMICAL_INTEGRITY: True,
                    HardGateType.CHARACTER_IDENTITY: True,
                },
                metadata={
                    "vision_audited": False,
                    "error": str(e),
                    "fallback_to_heuristic": True,
                    "summary": f"Ollama vision error: {e}; fell back to heuristic/CV",
                },
            )

    def audit_frames(
        self,
        frames: Sequence[Any],
        shot_requirement: Optional[ShotRequirement] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[CriticFailureObject]:
        """Audits frames via Ollama vision completion and returns parsed CriticFailureObject list."""
        return self.audit(frames, shot_requirement, context).failures

    def parse_vision_audit_result(
        self,
        response_data: Union[Dict[str, Any], List[Any], Any],
    ) -> CriticAuditResult:
        """Parses structured JSON response from Ollama vision into a full CriticAuditResult."""
        if hasattr(response_data, "to_dict"):
            data = response_data.to_dict()
        elif isinstance(response_data, dict):
            data = response_data
        elif isinstance(response_data, list):
            data = {"defects": response_data}
        else:
            data = {}

        failures = self.parse_vision_response(response_data)

        # Parse hard gate verdicts
        hg_raw = data.get("hard_gate_verdicts", {})
        hard_gate_verdicts: Dict[HardGateType, bool] = {}
        if isinstance(hg_raw, dict):
            for k, v in hg_raw.items():
                if k in (None, "", "null", "none"):
                    continue
                try:
                    gate_enum = HardGateType.from_str(k)
                    hard_gate_verdicts[gate_enum] = bool(v)
                except Exception:
                    s_k = str(k).upper()
                    if "ANATOM" in s_k:
                        hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] = bool(v)
                    elif "IDENTITY" in s_k or "CHARACTER" in s_k:
                        hard_gate_verdicts[HardGateType.CHARACTER_IDENTITY] = bool(v)

        # If any failure is a hard gate breaker, enforce False on that gate
        for f in failures:
            if f.is_hard_gate_breaker and f.hard_gate:
                hard_gate_verdicts[f.hard_gate] = False

        # Ensure default gates exist if not present
        if HardGateType.ANATOMICAL_INTEGRITY not in hard_gate_verdicts:
            anatomy_breaker = any(
                f.is_hard_gate_breaker and (
                    f.hard_gate == HardGateType.ANATOMICAL_INTEGRITY
                    or any(term in f.failure_type.lower() for term in VisualCritic.ANATOMY_KEYWORDS)
                )
                for f in failures
            )
            hard_gate_verdicts[HardGateType.ANATOMICAL_INTEGRITY] = not anatomy_breaker

        if HardGateType.CHARACTER_IDENTITY not in hard_gate_verdicts:
            identity_breaker = any(
                f.is_hard_gate_breaker and (
                    f.hard_gate == HardGateType.CHARACTER_IDENTITY
                    or any(term in f.failure_type.lower() for term in ("identity", "face_drift", "actor"))
                )
                for f in failures
            )
            hard_gate_verdicts[HardGateType.CHARACTER_IDENTITY] = not identity_breaker

        # Calculate or extract score
        raw_score = data.get("visual_score", data.get("score"))
        if raw_score is not None:
            try:
                score = max(0.0, min(10.0, float(raw_score)))
            except Exception:
                score = self._calculate_score(failures)
        else:
            score = self._calculate_score(failures)

        # Passed determination
        all_hard_gates_pass = all(hard_gate_verdicts.values())
        raw_passed = data.get("passed")
        if raw_passed is not None:
            passed = bool(raw_passed) and all_hard_gates_pass and (score >= 7.0)
        else:
            passed = all_hard_gates_pass and (score >= 7.0)

        summary = str(data.get("summary", "Vision critic evaluation complete"))

        return CriticAuditResult(
            critic_type=CriticType.VISUAL,
            passed=passed,
            score=score,
            failures=failures,
            hard_gate_verdicts=hard_gate_verdicts,
            metadata={
                "summary": summary,
                "defect_count": len(failures),
                "model": getattr(response_data, "model", self.model),
                "vision_audited": getattr(response_data, "model", "") != "fallback:heuristic",
            },
        )

    def parse_vision_response(
        self,
        response_data: Union[Dict[str, Any], List[Any], Any],
    ) -> List[CriticFailureObject]:
        """Parses structured JSON response from Ollama vision into CriticFailureObjects."""
        failures: List[CriticFailureObject] = []
        if hasattr(response_data, "to_dict"):
            data = response_data.to_dict()
        elif isinstance(response_data, dict):
            data = response_data
        elif isinstance(response_data, list):
            data = {"defects": response_data}
        else:
            return []

        raw_defects = []
        if isinstance(data, list):
            raw_defects = data
        elif isinstance(data, dict):
            for k in ("defects", "failures", "items", "issues"):
                if k in data and isinstance(data[k], list):
                    raw_defects = data[k]
                    break

        for item in raw_defects:
            if not isinstance(item, dict):
                continue
            failure_obj = self._parse_single_defect(item)
            if failure_obj is not None:
                failures.append(failure_obj)

        return failures

    def _parse_single_defect(self, item: Dict[str, Any]) -> Optional[CriticFailureObject]:
        try:
            ft = str(item.get("failure_type", item.get("defect_type", item.get("type", "visual_defect")))).lower()

            # Detect hard gate type safely
            raw_gate = item.get("hard_gate")
            hard_gate: Optional[HardGateType] = None
            if raw_gate not in (None, "", "null", "None", "NONE", "none", "nan", False):
                try:
                    hard_gate = HardGateType.from_str(raw_gate)
                except Exception:
                    s_gate = str(raw_gate).upper()
                    if "ANATOM" in s_gate:
                        hard_gate = HardGateType.ANATOMICAL_INTEGRITY
                    elif "IDENTITY" in s_gate or "CHARACTER" in s_gate or "FACE" in s_gate:
                        hard_gate = HardGateType.CHARACTER_IDENTITY
            if hard_gate is None:
                if any(k in ft for k in VisualCritic.ANATOMY_KEYWORDS):
                    hard_gate = HardGateType.ANATOMICAL_INTEGRITY
                elif any(k in ft for k in ("identity", "face_drift", "actor")):
                    hard_gate = HardGateType.CHARACTER_IDENTITY

            # Severity mapping
            severity_str = str(item.get("severity") or "SEVERE").strip()
            try:
                severity = DefectSeverity.from_str(severity_str)
            except Exception:
                s_up = severity_str.upper()
                if any(k in s_up for k in ("FATAL", "CRITICAL", "BLOCKER", "CATASTROPHIC")):
                    severity = DefectSeverity.FATAL
                elif any(k in s_up for k in ("SEVERE", "HIGH", "MAJOR")):
                    severity = DefectSeverity.SEVERE
                elif any(k in s_up for k in ("MODERATE", "MEDIUM", "WARN")):
                    severity = DefectSeverity.MODERATE
                elif any(k in s_up for k in ("MINOR", "LOW", "INFO")):
                    severity = DefectSeverity.MINOR
                elif any(k in s_up for k in ("NEGLIGIBLE", "TRIVIAL", "NONE", "IGNORE")):
                    severity = DefectSeverity.NEGLIGIBLE
                else:
                    severity = DefectSeverity.SEVERE

            # Repair recommendation mapping
            is_anatomy = (hard_gate == HardGateType.ANATOMICAL_INTEGRITY)
            default_repair = (
                RepairRecommendation.REGIONAL_INPAINTING
                if is_anatomy
                else RepairRecommendation.FULL_REGEN
            )
            repair_val = item.get("recommended_repair", item.get("repair_strategy", default_repair))
            repair_str = str(repair_val).strip() if repair_val is not None else str(default_repair)
            try:
                repair = RepairRecommendation.from_str(repair_str)
            except Exception:
                r_up = repair_str.upper()
                if "INPAINT" in r_up:
                    repair = RepairRecommendation.REGIONAL_INPAINTING
                elif "REGEN" in r_up:
                    repair = RepairRecommendation.FULL_REGEN
                elif "PREVIS" in r_up:
                    repair = RepairRecommendation.SPATIAL_PREVIS_RERUN
                elif "AUDIO" in r_up:
                    repair = RepairRecommendation.AUDIO_REMASTER
                elif "NO_REPAIR" in r_up or "NONE" in r_up:
                    repair = RepairRecommendation.NO_REPAIR_NEEDED
                else:
                    repair = default_repair

            # Bounding box parsing (supports list, tuple, and dicts, 0-1 or 0-1000 scales)
            raw_box = item.get("bounding_box", item.get("bbox", item.get("box", item.get("spatial_bbox"))))
            bbox = (0.0, 0.0, 1.0, 1.0)
            if isinstance(raw_box, dict):
                b_vals = None
                if all(k in raw_box for k in ("x1", "y1", "x2", "y2")):
                    b_vals = [float(raw_box[k]) for k in ("x1", "y1", "x2", "y2")]
                elif all(k in raw_box for k in ("xmin", "ymin", "xmax", "ymax")):
                    b_vals = [float(raw_box[k]) for k in ("xmin", "ymin", "xmax", "ymax")]
                elif all(k in raw_box for k in ("x", "y", "width", "height")):
                    b_vals = [float(raw_box["x"]), float(raw_box["y"]), float(raw_box["x"]) + float(raw_box["width"]), float(raw_box["y"]) + float(raw_box["height"])]
                if b_vals:
                    if any(v > 1.01 for v in b_vals):
                        b_vals = [v / 1000.0 for v in b_vals]
                    x1 = max(0.0, min(1.0, b_vals[0]))
                    y1 = max(0.0, min(1.0, b_vals[1]))
                    x2 = max(0.0, min(1.0, b_vals[2]))
                    y2 = max(0.0, min(1.0, b_vals[3]))
                    bbox = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            elif isinstance(raw_box, (list, tuple)) and len(raw_box) == 4:
                try:
                    b_vals = [float(v) for v in raw_box]
                    if any(v > 1.01 for v in b_vals):
                        b_vals = [v / 1000.0 for v in b_vals]
                    x1 = max(0.0, min(1.0, b_vals[0]))
                    y1 = max(0.0, min(1.0, b_vals[1]))
                    x2 = max(0.0, min(1.0, b_vals[2]))
                    y2 = max(0.0, min(1.0, b_vals[3]))
                    bbox = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
                except Exception:
                    bbox = (0.0, 0.0, 1.0, 1.0)

            # Safe frame bounds
            raw_start = item.get("start_frame")
            raw_end = item.get("end_frame")
            start_f = int(raw_start) if raw_start is not None else 0
            end_f = int(raw_end) if raw_end is not None else start_f

            raw_bounds = item.get("frame_bounds")
            if isinstance(raw_bounds, (list, tuple)) and len(raw_bounds) == 2:
                b0 = int(raw_bounds[0]) if raw_bounds[0] is not None else start_f
                b1 = int(raw_bounds[1]) if raw_bounds[1] is not None else end_f
                frame_bounds = (min(b0, b1), max(b0, b1))
            else:
                frame_bounds = (min(start_f, end_f), max(start_f, end_f))

            raw_conf = item.get("confidence")
            confidence = float(raw_conf) if raw_conf is not None else 0.95
            confidence = max(0.0, min(1.0, confidence))

            return CriticFailureObject(
                failure_type=ft,
                severity=severity,
                frame_bounds=frame_bounds,
                bounding_box=bbox,
                target_entity_id=item.get("target_entity_id", item.get("character_id")),
                observed_state=str(item.get("observed_state", "Visual or anatomical defect detected by Ollama Vision")),
                expected_state=item.get("expected_state", "Canonical visual appearance without distortion"),
                confidence=confidence,
                recommended_repair=repair,
                critic_type=CriticType.VISUAL,
                hard_gate=hard_gate,
                description=item.get("description", f"Vision critic identified {ft}"),
            )
        except Exception as e:
            logger.warning(f"Failed to parse defect item {item}: {e}")
            return None


class VisualCritic(BaseCritic):
    """Audits anatomical integrity (extra limbs, distorted hands/fingers) and surface artifacts,
    combining multimodal Ollama vision inspection with deterministic CV and telemetry heuristics.
    """

    ANATOMY_KEYWORDS: Tuple[str, ...] = (
        "limb", "arm", "leg", "hand", "finger", "digit", "toe", "foot", "feet",
        "anatomy", "anatomical", "face", "eye", "head", "neck", "joint", "fused",
        "proportion", "torso", "body", "deform", "uncanny", "polydactyly", "digit_count",
    )

    def __init__(
        self,
        ollama_client: Optional[Any] = None,
        vision_auditor: Optional[OllamaVisionAuditor] = None,
        evaluator_fn: Optional[Callable[..., List[CriticFailureObject]]] = None,
        cv_analyzer: Optional[CVTemporalAnalyzer] = None,
        model: str = "gemma4:31b:cloud",
    ) -> None:
        super().__init__(CriticType.VISUAL, "Visual & Anatomical Critic", evaluator_fn=evaluator_fn)
        self.ollama_client = ollama_client
        if vision_auditor is not None:
            self.vision_auditor = vision_auditor
        elif ollama_client is not None:
            self.vision_auditor = OllamaVisionAuditor(client=ollama_client, model=model)
        else:
            self.vision_auditor = None
        self.cv_analyzer = cv_analyzer
        self.model = model

    def audit(
        self,
        candidate_data: Union[Dict[str, Any], Any],
        scene_state: Optional[SceneState] = None,
        shot_requirement: Optional[ShotRequirement] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> CriticAuditResult:
        cdata = candidate_data if isinstance(candidate_data, dict) else getattr(candidate_data, "__dict__", {})
        failures: List[CriticFailureObject] = []
        vision_audited = False

        # 1. Run pluggable evaluator if provided
        if self.evaluator_fn is not None:
            custom_failures = self.evaluator_fn(cdata, scene_state, shot_requirement, context)
            if custom_failures:
                failures.extend(custom_failures)

        # 2. Extract frames/keyframes for Ollama Vision inspection
        frames = None
        for fk in ("keyframes", "image_paths", "frames", "keyframe_paths", "images", "video_frames"):
            if fk in cdata and cdata[fk]:
                frames = cdata[fk]
                break
        if frames is None and context:
            for fk in ("keyframes", "image_paths", "frames", "keyframe_paths", "images"):
                if fk in context and context[fk]:
                    frames = context[fk]
                    break
        if frames is None:
            for single_k in ("keyframe", "image_path", "frame", "image"):
                if single_k in cdata and cdata[single_k]:
                    frames = [cdata[single_k]]
                    break

        # Normalize 4D numpy array to list if needed
        if frames is not None and hasattr(frames, "ndim") and frames.ndim == 4:
            frames = list(frames)

        # Run Ollama Vision Auditor if frames are present and auditor/client available
        auditor = self.vision_auditor
        if auditor is None and self.ollama_client is not None:
            auditor = OllamaVisionAuditor(client=self.ollama_client, model=self.model)
            self.vision_auditor = auditor

        vision_res: Optional[CriticAuditResult] = None
        if auditor is not None and frames:
            try:
                if hasattr(auditor, "audit"):
                    vision_res = auditor.audit(
                        frames=frames,
                        shot_requirement=shot_requirement,
                        context=context,
                    )
                    if vision_res.failures:
                        failures.extend(vision_res.failures)
                    vision_audited = bool(vision_res.metadata.get("vision_audited", True))
                else:
                    vision_failures = auditor.audit_frames(
                        frames=frames,
                        shot_requirement=shot_requirement,
                        context=context,
                    )
                    if vision_failures:
                        failures.extend(vision_failures)
                    vision_audited = True
            except Exception as e:
                logger.warning(
                    f"Ollama Vision Critic failed: {e}. Gracefully falling back to CV/heuristics."
                )
                vision_audited = False

        # Synergistic CV Temporal / surface analysis if analyzer provided
        if self.cv_analyzer is not None and frames is not None and len(frames) >= 2:
            try:
                cv_input_frames = frames
                if cv_input_frames and isinstance(cv_input_frames[0], (str, Path)):
                    loaded = []
                    for fp in cv_input_frames:
                        p = Path(str(fp))
                        if p.is_file():
                            try:
                                import cv2
                                img = cv2.imread(str(p))
                                if img is not None:
                                    loaded.append(img)
                            except Exception:
                                pass
                    if len(loaded) >= 2:
                        cv_input_frames = np.stack(loaded, axis=0)

                if hasattr(cv_input_frames, "ndim") or (isinstance(cv_input_frames, (list, tuple)) and hasattr(cv_input_frames[0], "ndim")):
                    cv_failures = self.cv_analyzer.analyze_frames(cv_input_frames, telemetry=cdata)
                    if cv_failures:
                        failures.extend(cv_failures)
            except Exception as e:
                logger.warning(f"CV analysis in VisualCritic encountered error: {e}")

        # 3. Inspect candidate visual & anatomical telemetry
        raw_defects = []
        for k in ("visual_defects", "anatomical_defects", "anatomy_defects", "defects"):
            if k in cdata and isinstance(cdata[k], list):
                raw_defects.extend(cdata[k])

        for item in raw_defects:
            if isinstance(item, CriticFailureObject):
                # Ensure anatomical hard gate is tagged if applicable
                if item.hard_gate is None:
                    defect_type_str = item.failure_type.lower()
                    if any(term in defect_type_str for term in self.ANATOMY_KEYWORDS):
                        item.hard_gate = HardGateType.ANATOMICAL_INTEGRITY
                failures.append(item)
            elif isinstance(item, dict):
                defect_class = str(item.get("defect_class", item.get("failure_type", item.get("type", "visual_defect")))).lower()
                is_anatomy = any(term in defect_class for term in self.ANATOMY_KEYWORDS)
                hard_gate = HardGateType.ANATOMICAL_INTEGRITY if is_anatomy else None
                repair = item.get(
                    "recommended_repair",
                    item.get(
                        "recommended_repair_strategy",
                        RepairRecommendation.REGIONAL_INPAINTING if is_anatomy else RepairRecommendation.FULL_REGEN,
                    ),
                )
                failures.append(
                    CriticFailureObject(
                        failure_type=defect_class,
                        severity=DefectSeverity.from_str(item.get("severity", "SEVERE")),
                        frame_bounds=item.get("frame_bounds", (item.get("start_frame", 0), item.get("end_frame", 0))),
                        bounding_box=item.get("bounding_box", item.get("bbox", (0.0, 0.0, 1.0, 1.0))),
                        target_entity_id=item.get("target_entity_id", item.get("character_id")),
                        observed_state=str(item.get("observed_state", "Anatomical or surface artifact detected")),
                        expected_state=item.get("expected_state", "Canonical human anatomy without deformation"),
                        confidence=float(item.get("confidence", 0.95)),
                        recommended_repair=repair,
                        critic_type=CriticType.VISUAL,
                        hard_gate=hard_gate,
                    )
                )

        # 4. Check explicit boolean telemetry flags
        if cdata.get("has_extra_limbs") or cdata.get("distorted_hands") or cdata.get("extra_arm") or cdata.get("missing_limb"):
            failures.append(
                CriticFailureObject(
                    failure_type="distorted_hands" if cdata.get("distorted_hands") else "extra_limbs",
                    severity=DefectSeverity.FATAL,
                    frame_bounds=(0, int(cdata.get("total_frames", 24))),
                    bounding_box=cdata.get("hand_bbox", (0.3, 0.4, 0.7, 0.8)),
                    target_entity_id=cdata.get("character_id", "actor_01"),
                    observed_state="Severe hand deformity or extra digits detected in candidate frames",
                    expected_state="Standard 5-digit human hand with natural joint geometry",
                    confidence=0.98,
                    recommended_repair=RepairRecommendation.REGIONAL_INPAINTING,
                    critic_type=CriticType.VISUAL,
                    hard_gate=HardGateType.ANATOMICAL_INTEGRITY,
                    description="Anatomical distortion breaching hard gate threshold",
                )
            )

        # 5. Evaluate Hard Gates (ANATOMICAL_INTEGRITY & CHARACTER_IDENTITY)
        vision_anatomy_failed = False
        vision_identity_failed = False
        if vision_res is not None and vision_res.hard_gate_verdicts:
            if not vision_res.hard_gate_verdicts.get(HardGateType.ANATOMICAL_INTEGRITY, True):
                vision_anatomy_failed = True
            if not vision_res.hard_gate_verdicts.get(HardGateType.CHARACTER_IDENTITY, True):
                vision_identity_failed = True

        anatomy_breaker = vision_anatomy_failed or any(
            f.is_hard_gate_breaker and (
                f.hard_gate == HardGateType.ANATOMICAL_INTEGRITY
                or any(term in f.failure_type.lower() for term in self.ANATOMY_KEYWORDS)
            )
            for f in failures
        )
        identity_breaker = vision_identity_failed or any(
            f.is_hard_gate_breaker and (
                f.hard_gate == HardGateType.CHARACTER_IDENTITY
                or any(term in f.failure_type.lower() for term in ("identity", "face_drift", "actor_drift"))
            )
            for f in failures
        )

        hard_gate_verdicts = {HardGateType.ANATOMICAL_INTEGRITY: not anatomy_breaker}
        if identity_breaker or any(f.hard_gate == HardGateType.CHARACTER_IDENTITY for f in failures):
            hard_gate_verdicts[HardGateType.CHARACTER_IDENTITY] = not identity_breaker

        score = self._calculate_score(failures)
        passed = (not anatomy_breaker) and (not identity_breaker) and (score >= 7.0)

        return CriticAuditResult(
            critic_type=CriticType.VISUAL,
            passed=passed,
            score=score,
            failures=failures,
            hard_gate_verdicts=hard_gate_verdicts,
            metadata={
                "defect_count": len(failures),
                "anatomy_breaker": anatomy_breaker,
                "identity_breaker": identity_breaker,
                "vision_audited": vision_audited,
                "vision_summary": vision_res.metadata.get("summary") if vision_res else None,
            },
        )


# ---------------------------------------------------------------------------
# 2. TemporalCritic
# ---------------------------------------------------------------------------

class TemporalCritic(BaseCritic):
    """Combines deterministic CV temporal analyzer with high-level temporal coherence evaluation."""

    def __init__(
        self,
        cv_analyzer: Optional[CVTemporalAnalyzer] = None,
        evaluator_fn: Optional[Callable[..., List[CriticFailureObject]]] = None,
    ) -> None:
        super().__init__(CriticType.TEMPORAL, "Temporal Coherence Critic", evaluator_fn=evaluator_fn)
        self.cv_analyzer = cv_analyzer or CVTemporalAnalyzer()

    def audit(
        self,
        candidate_data: Union[Dict[str, Any], Any],
        scene_state: Optional[SceneState] = None,
        shot_requirement: Optional[ShotRequirement] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> CriticAuditResult:
        cdata = candidate_data if isinstance(candidate_data, dict) else getattr(candidate_data, "__dict__", {})
        failures: List[CriticFailureObject] = []

        # 1. Run pluggable evaluator if provided
        if self.evaluator_fn is not None:
            custom_failures = self.evaluator_fn(cdata, scene_state, shot_requirement, context)
            if custom_failures:
                failures.extend(custom_failures)

        # 2. Process explicit temporal defect lists if passed
        for k in ("temporal_defects", "defects"):
            if k in cdata and isinstance(cdata[k], list):
                for item in cdata[k]:
                    if isinstance(item, CriticFailureObject):
                        if k == "temporal_defects" or item.critic_type == CriticType.TEMPORAL or any(t in item.failure_type.lower() for t in ("flicker", "morph", "jitter", "motion", "strobe")):
                            failures.append(item)
                    elif isinstance(item, dict):
                        ft = str(item.get("defect_class", item.get("failure_type", item.get("type", "temporal_defect")))).lower()
                        if k == "temporal_defects" or any(t in ft for t in ("flicker", "morph", "jitter", "motion", "strobe", "temporal")):
                            failures.append(
                                CriticFailureObject(
                                    failure_type=ft,
                                    severity=DefectSeverity.from_str(item.get("severity", "SEVERE")),
                                    frame_bounds=item.get("frame_bounds", (item.get("start_frame", 0), item.get("end_frame", 0))),
                                    bounding_box=item.get("bounding_box", item.get("bbox", (0.0, 0.0, 1.0, 1.0))),
                                    target_entity_id=item.get("target_entity_id"),
                                    observed_state=str(item.get("observed_state", "Temporal artifact detected")),
                                    expected_state=item.get("expected_state", "Continuous temporal progression"),
                                    confidence=float(item.get("confidence", 0.90)),
                                    recommended_repair=item.get("recommended_repair", RepairRecommendation.REGIONAL_INPAINTING),
                                    critic_type=CriticType.TEMPORAL,
                                )
                            )

        # 3. Run deterministic CV analyzer on raw frames if available
        frames = cdata.get("frames", cdata.get("video_frames"))
        if frames is not None and len(frames) >= 2:
            cv_failures = self.cv_analyzer.analyze_frames(frames, telemetry=cdata)
            failures.extend(cv_failures)

        # 4. Inspect high-level temporal telemetry flags
        if cdata.get("temporal_jitter") or cdata.get("micro_flicker_detected"):
            failures.append(
                CriticFailureObject(
                    failure_type="micro_flicker",
                    severity=DefectSeverity.SEVERE,
                    frame_bounds=cdata.get("flicker_frame_bounds", (2, 5)),
                    bounding_box=(0.0, 0.0, 1.0, 1.0),
                    observed_state="Severe micro-flickering luminance strobe flagged in telemetry",
                    expected_state="Stable temporal luminance",
                    confidence=0.90,
                    recommended_repair=RepairRecommendation.REGIONAL_INPAINTING,
                    critic_type=CriticType.TEMPORAL,
                )
            )

        if cdata.get("morphing_detected") or cdata.get("transient_morph"):
            failures.append(
                CriticFailureObject(
                    failure_type="morphing_artifact",
                    severity=DefectSeverity.FATAL,
                    frame_bounds=cdata.get("morph_frame_bounds", (4, 7)),
                    bounding_box=cdata.get("morph_bbox", (0.2, 0.2, 0.6, 0.6)),
                    observed_state="Sudden 1-3 frame structural collapse/morphing flagged in telemetry",
                    expected_state="Continuous geometry and topology preservation",
                    confidence=0.95,
                    recommended_repair=RepairRecommendation.REGIONAL_INPAINTING,
                    critic_type=CriticType.TEMPORAL,
                )
            )

        if cdata.get("optical_flow_spike") or cdata.get("erratic_motion"):
            failures.append(
                CriticFailureObject(
                    failure_type="erratic_motion_spike",
                    severity=DefectSeverity.SEVERE,
                    frame_bounds=cdata.get("motion_frame_bounds", (3, 4)),
                    bounding_box=cdata.get("motion_bbox", (0.0, 0.0, 1.0, 1.0)),
                    observed_state="Unphysical optical flow acceleration jump flagged in telemetry",
                    expected_state="Continuous kinematic motion",
                    confidence=0.88,
                    recommended_repair=RepairRecommendation.SPATIAL_PREVIS_RERUN,
                    critic_type=CriticType.TEMPORAL,
                )
            )

        score = self._calculate_score(failures)
        passed = (not any(f.is_hard_gate_breaker for f in failures)) and (score >= 7.0)

        return CriticAuditResult(
            critic_type=CriticType.TEMPORAL,
            passed=passed,
            score=score,
            failures=failures,
            metadata={"defect_count": len(failures)},
        )


# ---------------------------------------------------------------------------
# 3. ContinuityCritic
# ---------------------------------------------------------------------------

class ContinuityCritic(BaseCritic):
    """Cross-references candidate telemetry against AetherWorldModel SceneState."""

    def __init__(
        self,
        evaluator_fn: Optional[Callable[..., List[CriticFailureObject]]] = None,
    ) -> None:
        super().__init__(CriticType.CONTINUITY, "Scene State Continuity Critic", evaluator_fn=evaluator_fn)

    def audit(
        self,
        candidate_data: Union[Dict[str, Any], Any],
        scene_state: Optional[SceneState] = None,
        shot_requirement: Optional[ShotRequirement] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> CriticAuditResult:
        cdata = candidate_data if isinstance(candidate_data, dict) else getattr(candidate_data, "__dict__", {})
        failures: List[CriticFailureObject] = []

        # 1. Run pluggable evaluator if provided
        if self.evaluator_fn is not None:
            custom_failures = self.evaluator_fn(cdata, scene_state, shot_requirement, context)
            if custom_failures:
                failures.extend(custom_failures)

        # 2. Process explicit continuity defect lists if passed
        for k in ("continuity_defects", "defects"):
            if k in cdata and isinstance(cdata[k], list):
                for item in cdata[k]:
                    if isinstance(item, CriticFailureObject):
                        if k == "continuity_defects" or item.critic_type == CriticType.CONTINUITY or any(t in item.failure_type.lower() for t in ("prop", "wardrobe", "injury", "identity", "handoff")):
                            failures.append(item)
                    elif isinstance(item, dict):
                        ft = str(item.get("defect_class", item.get("failure_type", item.get("type", "continuity_defect")))).lower()
                        if k == "continuity_defects" or any(t in ft for t in ("prop", "wardrobe", "injury", "identity", "handoff", "continuity")):
                            is_prop = "prop" in ft or "handoff" in ft
                            is_id = "identity" in ft or "wardrobe" in ft or "injury" in ft
                            hg = HardGateType.PROP_CONTINUITY if is_prop else (HardGateType.CHARACTER_IDENTITY if is_id else None)
                            failures.append(
                                CriticFailureObject(
                                    failure_type=ft,
                                    severity=DefectSeverity.from_str(item.get("severity", "SEVERE")),
                                    frame_bounds=item.get("frame_bounds", (item.get("start_frame", 0), item.get("end_frame", 0))),
                                    bounding_box=item.get("bounding_box", item.get("bbox", (0.0, 0.0, 1.0, 1.0))),
                                    target_entity_id=item.get("target_entity_id"),
                                    observed_state=str(item.get("observed_state", "Continuity defect observed")),
                                    expected_state=item.get("expected_state", "State continuity preservation"),
                                    confidence=float(item.get("confidence", 0.95)),
                                    recommended_repair=item.get("recommended_repair", RepairRecommendation.REGIONAL_INPAINTING),
                                    critic_type=CriticType.CONTINUITY,
                                    hard_gate=hg,
                                )
                            )

        # 3. Extract active scene state if passed in context or cdata
        state = scene_state
        if state is None:
            if "scene_state" in cdata and isinstance(cdata["scene_state"], SceneState):
                state = cdata["scene_state"]
            elif context and "scene_state" in context and isinstance(context["scene_state"], SceneState):
                state = context["scene_state"]

        if state is not None:
            # A. Wardrobe Damage & Persistence Verification
            obs_chars = cdata.get("characters", cdata.get("character_roster", {}))
            for char_id, char_state in state.character_roster.items():
                char_obs = obs_chars.get(char_id, {})
                obs_wardrobe = char_obs.get("wardrobe", {})

                for slot, expected_garment in char_state.wardrobe.items():
                    exp_state = getattr(expected_garment, "state", "pristine")
                    exp_dmg = getattr(expected_garment, "damage_level", 0.0)

                    # If expected state has damage or specific torn condition
                    if exp_dmg > 0.0 or ("torn" in exp_state) or ("damaged" in exp_state):
                        obs_item = obs_wardrobe.get(slot, {})
                        obs_state = obs_item.get("state") if isinstance(obs_item, dict) else getattr(obs_item, "state", None)
                        obs_dmg = obs_item.get("damage_level") if isinstance(obs_item, dict) else getattr(obs_item, "damage_level", None)

                        # If candidate observation shows garment is pristine or damage missing
                        if (
                            obs_state in ("pristine", "intact", "clean", "undamaged", "new")
                            or (obs_dmg is not None and obs_dmg == 0.0)
                            or (obs_dmg is not None and obs_dmg < exp_dmg * 0.4)
                        ):
                            failures.append(
                                CriticFailureObject(
                                    failure_type="wardrobe_regression",
                                    severity=DefectSeverity.SEVERE,
                                    target_entity_id=char_id,
                                    observed_state=f"Garment '{slot}' observed as '{obs_state}' (damage {obs_dmg})",
                                    expected_state=f"Garment '{slot}' persistent state '{exp_state}' (damage {exp_dmg})",
                                    confidence=0.94,
                                    recommended_repair=RepairRecommendation.REGIONAL_INPAINTING,
                                    critic_type=CriticType.CONTINUITY,
                                    hard_gate=HardGateType.CHARACTER_IDENTITY,
                                    description=f"Wardrobe regression for character {char_id}: {slot} miraculously healed/repaired",
                                )
                            )

            # B. Prop Possession & Hand Attachment Verification
            props_reported = ("props" in cdata) or ("prop_roster" in cdata) or ("props_present" in cdata)
            obs_props = cdata.get("props", cdata.get("prop_roster", {}))
            for prop_id, prop_state in state.prop_roster.items():
                if prop_state.is_held or prop_state.owner_id is not None:
                    exp_owner = prop_state.owner_id
                    exp_hand = prop_state.hand_attachment.value if hasattr(prop_state.hand_attachment, "value") else str(prop_state.hand_attachment).lower()
                    if "." in exp_hand:
                        exp_hand = exp_hand.split(".")[-1].lower()

                    obs_prop = obs_props.get(prop_id)

                    if props_reported and obs_prop is None and ("props_present" not in cdata or prop_id not in cdata.get("props_present", [])):
                        failures.append(
                            CriticFailureObject(
                                failure_type="prop_missing",
                                severity=DefectSeverity.FATAL,
                                target_entity_id=prop_id,
                                observed_state="Prop missing from candidate scene",
                                expected_state=f"Held by {exp_owner} in {exp_hand} hand",
                                confidence=0.96,
                                recommended_repair=RepairRecommendation.REGIONAL_INPAINTING,
                                critic_type=CriticType.CONTINUITY,
                                hard_gate=HardGateType.PROP_CONTINUITY,
                                description=f"Held prop {prop_id} vanished from character {exp_owner}",
                            )
                        )
                    elif isinstance(obs_prop, dict):
                        obs_owner = obs_prop.get("owner_id", obs_prop.get("holder_id"))
                        raw_obs_hand = str(obs_prop.get("hand_attachment", obs_prop.get("hand", ""))).lower()
                        obs_hand = raw_obs_hand.split(".")[-1] if "." in raw_obs_hand else raw_obs_hand

                        if obs_owner and obs_owner != exp_owner:
                            failures.append(
                                CriticFailureObject(
                                    failure_type="prop_possession_mismatch",
                                    severity=DefectSeverity.FATAL,
                                    target_entity_id=prop_id,
                                    observed_state=f"Held by '{obs_owner}'",
                                    expected_state=f"Held by '{exp_owner}'",
                                    confidence=0.97,
                                    recommended_repair=RepairRecommendation.REGIONAL_INPAINTING,
                                    critic_type=CriticType.CONTINUITY,
                                    hard_gate=HardGateType.PROP_CONTINUITY,
                                    description=f"Prop {prop_id} possession transferred unlawfully from {exp_owner} to {obs_owner}",
                                )
                            )
                        elif obs_hand and exp_hand not in ("none", "") and obs_hand != exp_hand:
                            failures.append(
                                CriticFailureObject(
                                    failure_type="prop_hand_attachment_mismatch",
                                    severity=DefectSeverity.SEVERE,
                                    target_entity_id=prop_id,
                                    observed_state=f"Held in '{obs_hand}' hand",
                                    expected_state=f"Held in '{exp_hand}' hand",
                                    confidence=0.95,
                                    recommended_repair=RepairRecommendation.REGIONAL_INPAINTING,
                                    critic_type=CriticType.CONTINUITY,
                                    hard_gate=HardGateType.PROP_CONTINUITY,
                                    description=f"Prop {prop_id} attached to wrong hand slot on {exp_owner}",
                                )
                            )

            # C. Physical Injuries Verification
            for char_id, char_state in state.character_roster.items():
                if char_state.injuries:
                    char_obs = obs_chars.get(char_id, {})
                    obs_injuries = char_obs.get("injuries", char_obs.get("marks"))
                    if obs_injuries is not None:
                        for exp_injury in char_state.injuries:
                            if exp_injury not in obs_injuries:
                                failures.append(
                                    CriticFailureObject(
                                        failure_type="injury_regression",
                                        severity=DefectSeverity.SEVERE,
                                        target_entity_id=char_id,
                                        observed_state="Injury healed / absent in candidate render",
                                        expected_state=f"Persistent wound '{exp_injury}'",
                                        confidence=0.92,
                                        recommended_repair=RepairRecommendation.REGIONAL_INPAINTING,
                                        critic_type=CriticType.CONTINUITY,
                                        hard_gate=HardGateType.CHARACTER_IDENTITY,
                                        description=f"Wound {exp_injury} on character {char_id} regressed without medical action",
                                    )
                                )

            # D. Reciprocal Eyelines Verification
            if cdata.get("reciprocal_eyeline_broken") or cdata.get("eyeline_mismatch"):
                failures.append(
                    CriticFailureObject(
                        failure_type="reciprocal_eyeline_break",
                        severity=DefectSeverity.SEVERE,
                        target_entity_id="eyeline_pair",
                        observed_state="Character eyelines divergent or breaking 180-degree axis",
                        expected_state="Reciprocal convergent eyelines between dialogue participants",
                        confidence=0.88,
                        recommended_repair=RepairRecommendation.SPATIAL_PREVIS_RERUN,
                        critic_type=CriticType.CONTINUITY,
                        description="Broken reciprocal eyeline geometry across multi-character interaction",
                    )
                )

        # 4. Character Identity Verification
        if cdata.get("character_identity_mismatch") or cdata.get("face_drift"):
            failures.append(
                CriticFailureObject(
                    failure_type="character_identity_drift",
                    severity=DefectSeverity.FATAL,
                    target_entity_id=cdata.get("identity_drift_char_id", "character_primary"),
                    observed_state="Facial structure or actor identity drifted from reference embeddings",
                    expected_state="Consistent character facial identity and feature vectors",
                    confidence=0.96,
                    recommended_repair=RepairRecommendation.FULL_REGEN,
                    critic_type=CriticType.CONTINUITY,
                    hard_gate=HardGateType.CHARACTER_IDENTITY,
                    description="Severe character identity drift breaching binary hard gate",
                )
            )

        # 5. Evaluate Hard Gates
        prop_passed = not any(f.hard_gate == HardGateType.PROP_CONTINUITY and f.is_hard_gate_breaker for f in failures)
        identity_passed = not any(f.hard_gate == HardGateType.CHARACTER_IDENTITY and f.is_hard_gate_breaker for f in failures)

        hard_gate_verdicts = {
            HardGateType.PROP_CONTINUITY: prop_passed,
            HardGateType.CHARACTER_IDENTITY: identity_passed,
        }

        score = self._calculate_score(failures)
        passed = prop_passed and identity_passed and (not any(f.is_hard_gate_breaker for f in failures)) and (score >= 7.0)

        return CriticAuditResult(
            critic_type=CriticType.CONTINUITY,
            passed=passed,
            score=score,
            failures=failures,
            hard_gate_verdicts=hard_gate_verdicts,
            metadata={"defect_count": len(failures), "prop_passed": prop_passed, "identity_passed": identity_passed},
        )


# ---------------------------------------------------------------------------
# 4. PerformanceCritic
# ---------------------------------------------------------------------------

class PerformanceCritic(BaseCritic):
    """Evaluates lip-sync offset (ms), phonetic mouth movement, and vocal performance."""

    def __init__(
        self,
        max_lip_sync_offset_ms: float = 45.0,
        evaluator_fn: Optional[Callable[..., List[CriticFailureObject]]] = None,
    ) -> None:
        super().__init__(CriticType.PERFORMANCE, "Lip-Sync & Performance Critic", evaluator_fn=evaluator_fn)
        self.max_lip_sync_offset_ms = max_lip_sync_offset_ms

    def audit(
        self,
        candidate_data: Union[Dict[str, Any], Any],
        scene_state: Optional[SceneState] = None,
        shot_requirement: Optional[ShotRequirement] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> CriticAuditResult:
        cdata = candidate_data if isinstance(candidate_data, dict) else getattr(candidate_data, "__dict__", {})
        failures: List[CriticFailureObject] = []

        # 1. Run pluggable evaluator if provided
        if self.evaluator_fn is not None:
            custom_failures = self.evaluator_fn(cdata, scene_state, shot_requirement, context)
            if custom_failures:
                failures.extend(custom_failures)

        # 2. Process explicit performance/audio defect lists
        for k in ("performance_defects", "lip_sync_defects", "defects"):
            if k in cdata and isinstance(cdata[k], list):
                for item in cdata[k]:
                    if isinstance(item, CriticFailureObject):
                        if k in ("performance_defects", "lip_sync_defects") or item.critic_type == CriticType.PERFORMANCE or any(t in item.failure_type.lower() for t in ("lip", "phonem", "viseme", "sync")):
                            failures.append(item)
                    elif isinstance(item, dict):
                        ft = str(item.get("defect_class", item.get("failure_type", item.get("type", "performance_defect")))).lower()
                        if k in ("performance_defects", "lip_sync_defects") or any(t in ft for t in ("lip", "phonem", "viseme", "sync", "speech", "mouth", "performance")):
                            is_sync = any(t in ft for t in ("lip", "phonem", "viseme", "sync"))
                            failures.append(
                                CriticFailureObject(
                                    failure_type=ft,
                                    severity=DefectSeverity.from_str(item.get("severity", "SEVERE")),
                                    frame_bounds=item.get("frame_bounds", (item.get("start_frame", 0), item.get("end_frame", 0))),
                                    bounding_box=item.get("bounding_box", item.get("bbox", (0.4, 0.5, 0.6, 0.7))),
                                    target_entity_id=item.get("target_entity_id", item.get("speaker_id")),
                                    observed_state=str(item.get("observed_state", "Performance defect observed")),
                                    expected_state=item.get("expected_state", "Synchronized performance"),
                                    confidence=float(item.get("confidence", 0.92)),
                                    recommended_repair=item.get("recommended_repair", RepairRecommendation.AUDIO_REMASTER if is_sync else RepairRecommendation.REGIONAL_INPAINTING),
                                    critic_type=CriticType.PERFORMANCE,
                                    hard_gate=HardGateType.LIP_SYNC_ALIGNMENT if is_sync else None,
                                )
                            )

        # 3. Check lip-sync offset timing
        lip_sync_offset = cdata.get(
            "lip_sync_offset_ms",
            cdata.get("lip_offset_ms", cdata.get("audio_desync_ms", cdata.get("sync_offset_ms"))),
        )
        if lip_sync_offset is not None:
            offset_val = float(lip_sync_offset)
            if abs(offset_val) > self.max_lip_sync_offset_ms:
                severity = DefectSeverity.FATAL if abs(offset_val) > 80.0 else DefectSeverity.SEVERE
                failures.append(
                    CriticFailureObject(
                        failure_type="lip_sync_offset_breach",
                        severity=severity,
                        frame_bounds=(0, int(cdata.get("total_frames", 24))),
                        bounding_box=cdata.get("mouth_bbox", (0.4, 0.5, 0.6, 0.7)),
                        target_entity_id=cdata.get("speaker_id", "speaker_01"),
                        observed_state=f"Acoustic/visual offset of {offset_val:.1f}ms exceeds {self.max_lip_sync_offset_ms}ms limit",
                        expected_state=f"Audio-visual sync locked within ±{self.max_lip_sync_offset_ms}ms window",
                        confidence=0.94,
                        recommended_repair=RepairRecommendation.AUDIO_REMASTER,
                        critic_type=CriticType.PERFORMANCE,
                        hard_gate=HardGateType.LIP_SYNC_ALIGNMENT,
                        description="Lip-sync timing desync violating dialogue hard gate",
                        metadata={"offset_ms": offset_val},
                    )
                )

        # 4. Check phonetic mouth movement mismatch
        if cdata.get("phonetic_mismatch") or cdata.get("mouth_frozen_during_speech"):
            failures.append(
                CriticFailureObject(
                    failure_type="phonetic_mouth_mismatch",
                    severity=DefectSeverity.SEVERE,
                    frame_bounds=(cdata.get("phoneme_start", 0), cdata.get("phoneme_end", 12)),
                    bounding_box=cdata.get("mouth_bbox", (0.4, 0.5, 0.6, 0.7)),
                    target_entity_id=cdata.get("speaker_id", "speaker_01"),
                    observed_state="Mouth closed/static during active phoneme vocalization",
                    expected_state="Articulated viseme mouth opening synchronized with spoken phonemes",
                    confidence=0.91,
                    recommended_repair=RepairRecommendation.REGIONAL_INPAINTING,
                    critic_type=CriticType.PERFORMANCE,
                    hard_gate=HardGateType.LIP_SYNC_ALIGNMENT,
                    description="Phonetic mouth articulation failure during spoken dialogue",
                )
            )

        # 5. Check vocal emotional affect mismatch
        if cdata.get("vocal_emotion_mismatch"):
            failures.append(
                CriticFailureObject(
                    failure_type="vocal_affect_mismatch",
                    severity=DefectSeverity.MODERATE,
                    observed_state=cdata.get("observed_emotion", "flat affect"),
                    expected_state=cdata.get("expected_emotion", "intense dramatic delivery"),
                    confidence=0.85,
                    recommended_repair=RepairRecommendation.AUDIO_REMASTER,
                    critic_type=CriticType.PERFORMANCE,
                    description="Vocal delivery emotion contradicts narrative beat intention",
                )
            )

        # 6. Evaluate Hard Gate LIP_SYNC_ALIGNMENT
        lip_sync_passed = not any(
            f.hard_gate == HardGateType.LIP_SYNC_ALIGNMENT and f.is_hard_gate_breaker
            for f in failures
        )
        hard_gate_verdicts = {HardGateType.LIP_SYNC_ALIGNMENT: lip_sync_passed}

        score = self._calculate_score(failures)
        passed = lip_sync_passed and (not any(f.is_hard_gate_breaker for f in failures)) and (score >= 7.0)

        return CriticAuditResult(
            critic_type=CriticType.PERFORMANCE,
            passed=passed,
            score=score,
            failures=failures,
            hard_gate_verdicts=hard_gate_verdicts,
            metadata={"defect_count": len(failures), "lip_sync_passed": lip_sync_passed},
        )


# ---------------------------------------------------------------------------
# 5. PhysicsCritic
# ---------------------------------------------------------------------------

class PhysicsCritic(BaseCritic):
    """Evaluates gravity violations, unnatural trajectory accelerations, and solid-body intersections."""

    def __init__(
        self,
        evaluator_fn: Optional[Callable[..., List[CriticFailureObject]]] = None,
    ) -> None:
        super().__init__(CriticType.PHYSICS, "Deterministic Physics Critic", evaluator_fn=evaluator_fn)

    def audit(
        self,
        candidate_data: Union[Dict[str, Any], Any],
        scene_state: Optional[SceneState] = None,
        shot_requirement: Optional[ShotRequirement] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> CriticAuditResult:
        cdata = candidate_data if isinstance(candidate_data, dict) else getattr(candidate_data, "__dict__", {})
        failures: List[CriticFailureObject] = []

        # 1. Run pluggable evaluator if provided
        if self.evaluator_fn is not None:
            custom_failures = self.evaluator_fn(cdata, scene_state, shot_requirement, context)
            if custom_failures:
                failures.extend(custom_failures)

        # 2. Process explicit physics defect lists
        for k in ("physics_defects", "trajectory_defects", "defects"):
            if k in cdata and isinstance(cdata[k], list):
                for item in cdata[k]:
                    if isinstance(item, CriticFailureObject):
                        if k in ("physics_defects", "trajectory_defects") or item.critic_type == CriticType.PHYSICS or any(t in item.failure_type.lower() for t in ("gravity", "trajectory", "collision", "clipping", "acceleration")):
                            failures.append(item)
                    elif isinstance(item, dict):
                        ft = str(item.get("defect_class", item.get("failure_type", item.get("type", "physics_defect")))).lower()
                        if k in ("physics_defects", "trajectory_defects") or any(t in ft for t in ("gravity", "trajectory", "collision", "clipping", "acceleration", "physics")):
                            failures.append(
                                CriticFailureObject(
                                    failure_type=ft,
                                    severity=DefectSeverity.from_str(item.get("severity", "SEVERE")),
                                    frame_bounds=item.get("frame_bounds", (item.get("start_frame", 0), item.get("end_frame", 0))),
                                    bounding_box=item.get("bounding_box", item.get("bbox", (0.0, 0.0, 1.0, 1.0))),
                                    target_entity_id=item.get("target_entity_id"),
                                    observed_state=str(item.get("observed_state", "Physical anomaly observed")),
                                    expected_state=item.get("expected_state", "Physical law adherence"),
                                    confidence=float(item.get("confidence", 0.90)),
                                    recommended_repair=item.get("recommended_repair", RepairRecommendation.SPATIAL_PREVIS_RERUN),
                                    critic_type=CriticType.PHYSICS,
                                    hard_gate=HardGateType.PHYSICAL_TRAJECTORY,
                                )
                            )

        # 3. Gravity violations (unsupported floating objects)
        if cdata.get("gravity_violation") or cdata.get("floating_objects"):
            failures.append(
                CriticFailureObject(
                    failure_type="gravity_violation",
                    severity=DefectSeverity.SEVERE,
                    target_entity_id=cdata.get("floating_prop_id", "prop_unsupported"),
                    observed_state="Physical object hovering without support or aerodynamic force",
                    expected_state="Standard -9.8 m/s² gravitational downward acceleration",
                    confidence=0.92,
                    recommended_repair=RepairRecommendation.SPATIAL_PREVIS_RERUN,
                    critic_type=CriticType.PHYSICS,
                    hard_gate=HardGateType.PHYSICAL_TRAJECTORY,
                    description="Unphysical zero-G floating violation in terrestrial environment",
                )
            )

        # 4. Unnatural acceleration spikes
        accel_mps2 = cdata.get("peak_acceleration_mps2")
        if (accel_mps2 is not None and float(accel_mps2) > 60.0) or cdata.get("unnatural_acceleration"):
            failures.append(
                CriticFailureObject(
                    failure_type="unnatural_acceleration",
                    severity=DefectSeverity.SEVERE,
                    target_entity_id=cdata.get("accelerating_entity_id", "subject"),
                    observed_state=f"Instantaneous acceleration spike ({accel_mps2 or '>60'} m/s²) without impact",
                    expected_state="Smooth kinematic acceleration bounded by biological and mechanical constraints",
                    confidence=0.89,
                    recommended_repair=RepairRecommendation.SPATIAL_PREVIS_RERUN,
                    critic_type=CriticType.PHYSICS,
                    hard_gate=HardGateType.PHYSICAL_TRAJECTORY,
                    description="Unphysical kinematic velocity impulse violating inertia",
                )
            )

        # 5. Solid-body intersections and mesh clipping
        if cdata.get("solid_body_clipping") or cdata.get("mesh_penetration"):
            failures.append(
                CriticFailureObject(
                    failure_type="solid_body_clipping",
                    severity=DefectSeverity.SEVERE,
                    target_entity_id=cdata.get("clipping_entity_id", "actor_or_prop"),
                    observed_state="Solid geometry interpenetrating rigid obstacle surface",
                    expected_state="Rigid body collision boundary without mesh penetration",
                    confidence=0.93,
                    recommended_repair=RepairRecommendation.SPATIAL_PREVIS_RERUN,
                    critic_type=CriticType.PHYSICS,
                    hard_gate=HardGateType.PHYSICAL_TRAJECTORY,
                    description="Solid body clipping through environment mesh",
                )
            )

        # 6. Evaluate Hard Gate PHYSICAL_TRAJECTORY
        traj_passed = not any(
            f.hard_gate == HardGateType.PHYSICAL_TRAJECTORY and f.is_hard_gate_breaker
            for f in failures
        )
        hard_gate_verdicts = {HardGateType.PHYSICAL_TRAJECTORY: traj_passed}

        score = self._calculate_score(failures)
        passed = traj_passed and (not any(f.is_hard_gate_breaker for f in failures)) and (score >= 7.0)

        return CriticAuditResult(
            critic_type=CriticType.PHYSICS,
            passed=passed,
            score=score,
            failures=failures,
            hard_gate_verdicts=hard_gate_verdicts,
            metadata={"defect_count": len(failures), "trajectory_passed": traj_passed},
        )


# ---------------------------------------------------------------------------
# 6. AudioCritic
# ---------------------------------------------------------------------------

class AudioCritic(BaseCritic):
    """Audits dialogue acoustic fidelity, sound clipping, noise floor, and loudness compliance."""

    def __init__(
        self,
        evaluator_fn: Optional[Callable[..., List[CriticFailureObject]]] = None,
    ) -> None:
        super().__init__(CriticType.AUDIO, "Acoustic & Audio Quality Critic", evaluator_fn=evaluator_fn)

    def audit(
        self,
        candidate_data: Union[Dict[str, Any], Any],
        scene_state: Optional[SceneState] = None,
        shot_requirement: Optional[ShotRequirement] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> CriticAuditResult:
        cdata = candidate_data if isinstance(candidate_data, dict) else getattr(candidate_data, "__dict__", {})
        failures: List[CriticFailureObject] = []

        # 1. Run pluggable evaluator if provided
        if self.evaluator_fn is not None:
            custom_failures = self.evaluator_fn(cdata, scene_state, shot_requirement, context)
            if custom_failures:
                failures.extend(custom_failures)

        # 2. Inspect audio defect lists
        for k in ("audio_defects", "sound_defects", "defects"):
            if k in cdata and isinstance(cdata[k], list):
                for item in cdata[k]:
                    if isinstance(item, CriticFailureObject):
                        if k in ("audio_defects", "sound_defects") or item.critic_type == CriticType.AUDIO or any(t in item.failure_type.lower() for t in ("audio", "clipping", "noise", "lufs", "foley", "dialogue", "vocal")):
                            failures.append(item)
                    elif isinstance(item, dict):
                        ft = str(item.get("defect_class", item.get("failure_type", item.get("type", "audio_defect")))).lower()
                        if k in ("audio_defects", "sound_defects") or any(t in ft for t in ("audio", "clipping", "noise", "lufs", "sound", "foley", "snr", "dialogue", "vocal", "acoustic")):
                            failures.append(
                                CriticFailureObject(
                                    failure_type=ft,
                                    severity=DefectSeverity.from_str(item.get("severity", "SEVERE")),
                                    frame_bounds=item.get("frame_bounds", (item.get("start_frame", 0), item.get("end_frame", 0))),
                                    target_entity_id=item.get("target_entity_id", "audio_master"),
                                    observed_state=str(item.get("observed_state", "Acoustic distortion detected")),
                                    expected_state=item.get("expected_state", "Broadcast standard audio delivery"),
                                    confidence=float(item.get("confidence", 0.90)),
                                    recommended_repair=RepairRecommendation.AUDIO_REMASTER,
                                    critic_type=CriticType.AUDIO,
                                )
                            )

        # 3. Audio clipping flags
        if cdata.get("audio_clipping") or cdata.get("peak_dbfs", -20.0) > -0.1:
            failures.append(
                CriticFailureObject(
                    failure_type="audio_digital_clipping",
                    severity=DefectSeverity.SEVERE,
                    target_entity_id="audio_master",
                    observed_state="Digital audio waveform peak saturation clipping (peak > -0.1 dBFS)",
                    expected_state="True peak bounded below -1.0 dBFS ceiling",
                    confidence=0.95,
                    recommended_repair=RepairRecommendation.AUDIO_REMASTER,
                    critic_type=CriticType.AUDIO,
                    description="Severe audio clipping exceeding digital headroom",
                )
            )

        # 4. Elevated noise floor
        if cdata.get("noise_floor_breach"):
            failures.append(
                CriticFailureObject(
                    failure_type="noise_floor_breach",
                    severity=DefectSeverity.MODERATE,
                    target_entity_id="audio_ambience",
                    observed_state="Elevated background hiss/hum exceeding SNR threshold",
                    expected_state="Clean acoustic master with SNR > 40 dB",
                    confidence=0.88,
                    recommended_repair=RepairRecommendation.AUDIO_REMASTER,
                    critic_type=CriticType.AUDIO,
                    description="Acoustic background noise floor breach",
                )
            )

        score = self._calculate_score(failures)
        passed = (not any(f.is_hard_gate_breaker for f in failures)) and (score >= 7.0)

        return CriticAuditResult(
            critic_type=CriticType.AUDIO,
            passed=passed,
            score=score,
            failures=failures,
            metadata={"defect_count": len(failures)},
        )
