"""Policy helpers for per-video visual generation.

The renderer keeps validated blueprint compositions as the safe fallback.  An
on-demand run gets a unique generation key so a repeated topic does not reuse
an older synthesized beat module by accident.
"""

from __future__ import annotations

import os
import hashlib
import uuid
from typing import Any, Dict, Optional

from pipeline.mechanism_visual_library import resolve_mechanism_family


VISUAL_MODES = {"blueprint", "hybrid", "on_demand"}

# Each beat in an on-demand run receives a different visual grammar.  These
# are intentionally mechanism-first compositions, not cosmetic skins for the
# same card layout.
VISUAL_GRAMMARS = (
    ("hero_field", "One hero object in a radial/vector field. Reveal its shape, then show one decisive transformation."),
    ("physical_analogy", "A concrete physical analogy with paths, forces, rays, or particles. Avoid UI panels and stacked cards."),
    ("exploded_mechanism", "An exploded layered or isometric mechanism. Separate components in depth, label only the critical parts, then reassemble."),
    ("live_trace", "A live execution trace: moving tokens, a timeline, a state machine, or a routing path. Motion must carry the explanation."),
    ("evidence_plot", "One quantitative proof visual: a chart, race, frontier, or measured comparison with exact values and a clear winner."),
    ("synthesis_lockup", "A final causal synthesis that transforms the earlier problem into the solved system. Use a clean geometric lockup, not an outro card."),
)


def resolve_visual_mode(value: Optional[str] = None) -> str:
    """Resolve and validate the visual generation policy."""
    mode = (value or os.getenv("VISUAL_GENERATION_MODE", "on_demand")).strip().lower()
    if mode not in VISUAL_MODES:
        choices = ", ".join(sorted(VISUAL_MODES))
        raise ValueError(f"Unsupported visual mode '{mode}'. Choose one of: {choices}.")
    return mode


def ensure_visual_generation_key(spec: Dict[str, Any], mode: str) -> Optional[str]:
    """Attach a fresh run key for modes that may synthesize custom graphics."""
    for beat in spec.get("beats", []):
        if beat.get("visual_source") == "bespoke":
            beat.pop("visual_source", None)
            beat.pop("bespoke_visual_path", None)

    if mode not in {"hybrid", "on_demand"}:
        return None

    # A production invocation is a new visual-generation request, even when
    # it loads the same topic template as an earlier invocation.
    key = uuid.uuid4().hex[:12]
    spec["visual_generation_key"] = key
    assign_visual_grammars(spec)
    for beat in spec.get("beats", []):
        beat["mechanism_family"] = resolve_mechanism_family(spec, beat)
    return key


def assign_visual_grammars(spec: Dict[str, Any]) -> None:
    """Assign a deterministic, non-repeating grammar cycle for this video."""
    title_key = "|".join(
        str(spec.get(field) or "").strip().lower()
        for field in ("title", "id", "category", "domain_taxonomy")
    )
    offset = int(hashlib.sha256(title_key.encode("utf-8")).hexdigest()[:8], 16) % len(VISUAL_GRAMMARS)
    for index, beat in enumerate(spec.get("beats", [])):
        grammar_id, _ = VISUAL_GRAMMARS[(offset + index) % len(VISUAL_GRAMMARS)]
        beat["visual_grammar"] = grammar_id


def visual_grammar_details(spec: Dict[str, Any], beat_idx: int) -> tuple[str, str]:
    """Return the assigned grammar and its direction for prompt construction."""
    beat = (spec.get("beats") or [])[beat_idx - 1] if 0 < beat_idx <= len(spec.get("beats", [])) else {}
    grammar_id = beat.get("visual_grammar")
    if grammar_id:
        for candidate_id, description in VISUAL_GRAMMARS:
            if candidate_id == grammar_id:
                return candidate_id, description
    candidate = VISUAL_GRAMMARS[(beat_idx - 1) % len(VISUAL_GRAMMARS)]
    return candidate


def mark_bespoke_visual(beat: Dict[str, Any], path: Optional[str]) -> None:
    """Record a verified generated module without disturbing blueprint data."""
    if path:
        beat["bespoke_visual_path"] = str(path)
        beat["visual_source"] = "bespoke"


def require_on_demand_visuals(spec: Dict[str, Any], mode: str) -> None:
    """Fail loudly if strict on-demand mode silently fell back to blueprints."""
    if mode != "on_demand":
        return
    missing = [
        str(beat.get("beat_id", index + 1))
        for index, beat in enumerate(spec.get("beats", []))
        if not beat.get("bespoke_visual_path")
    ]
    if missing:
        raise RuntimeError(
            "On-demand visual generation produced no verified module for beat(s): "
            + ", ".join(missing)
            + ". Refusing to silently reuse a repetitive blueprint."
        )

