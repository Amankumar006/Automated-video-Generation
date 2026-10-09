"""
The Model Verse — YouTube Hook Optimizer & Scoring Gating Engine
Integrates skills/yt-script (hookscore.py & hooks.json) into the automated script generation pipeline.
Generates candidate Beat 1 hooks inspired by proven archetypes and gates using weakest-link scoring.
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILLS_YT_SCRIPT_DIR = PROJECT_ROOT / "skills" / "yt-script"

# Ensure skills/yt-script is in sys.path for direct import of hookscore
if str(SKILLS_YT_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SKILLS_YT_SCRIPT_DIR))

try:
    import hookscore
except ImportError:
    hookscore = None

# Fallback regex patterns and constants if hookscore is missing or standalone
FILLER = {"basically", "actually", "literally", "just", "really", "very", "so", "kind", "sort", "like",
          "guys", "hey", "welcome", "today", "video", "subscribe", "channel"}
VAGUE = {"amazing", "incredible", "insane", "crazy", "huge", "massive", "game", "changer", "secret",
         "powerful", "ultimate", "best", "revolutionary", "mind", "blowing", "unbelievable"}
CONCRETE = re.compile(r"\b(\d[\d,.]*\s?(%|k|m|x|s|m|h)?|\$\d|\d+\s?(second|minute|hour|day|week|month|year)s?)\b", re.I)
YOU = re.compile(r"\b(you|your|you're|youre|yourself)\b", re.I)
STAKE = re.compile(r"\b(lose|lost|wasting|waste|quit|fail|broke|cost|risk|before|stop|never|die|dying|dead)\b", re.I)
CURIOSITY = re.compile(r"\b(why|how|what|which|until|before|but|nobody|almost|except|reason|actually)\b", re.I)

# Load formulas from hooks.json
HOOKS_JSON_PATH = SKILLS_YT_SCRIPT_DIR / "hooks.json"
FORMULAS: List[Dict[str, Any]] = []
if HOOKS_JSON_PATH.exists():
    try:
        with open(HOOKS_JSON_PATH, "r", encoding="utf-8") as f:
            FORMULAS = json.load(f).get("hooks", [])
    except Exception:
        FORMULAS = []


def words(text: str) -> List[str]:
    return re.findall(r"[a-z0-9'%$.]+", text.lower())


def score_hook(text: str) -> Dict[str, Any]:
    """
    Evaluates a candidate hook text using hookscore.py logic:
    Five properties (0-100 each):
      - SPECIFICITY
      - ADDRESS
      - STAKES
      - CURIOSITY
      - BREVITY
    Verdict: 60% mean + 40% weakest link.
    """
    t = text.strip()
    if hookscore is not None:
        parts, verdict, name, hits = hookscore.score(t)
        band_name = hookscore.band(verdict)
    else:
        # Standalone implementation if hookscore module fails to load
        w = words(t)
        nums = len(CONCRETE.findall(t))
        vague = sum(1 for x in w if x in VAGUE)
        filler = sum(1 for x in w if x in FILLER)
        spec = 34 + nums * 22 - vague * 16 - filler * 5
        spec += min(18, 6 * sum(1 for x in t.split()[1:] if x[:1].isupper()))
        spec = max(0, min(100, spec))

        n_you = len(YOU.findall(t))
        first_you = 30 if YOU.search(" ".join(t.split()[:6])) else 0
        addr = max(0, min(100, 26 + n_you * 20 + first_you))

        n_stake = len(STAKE.findall(t))
        stk = max(0, min(100, 22 + n_stake * 26 + (14 if CONCRETE.search(t) else 0)))

        n_cur = len(CURIOSITY.findall(t))
        q = 18 if t.strip().endswith("?") else 0
        closed = -18 if re.search(r"\b(because|so that|which means)\b", t, re.I) else 0
        cur = max(0, min(100, 24 + n_cur * 17 + q + closed))

        n_words = len(w)
        if n_words == 0:
            brev = 0
        elif 9 <= n_words <= 24:
            brev = 100
        elif n_words < 9:
            brev = max(30, 100 - (9 - n_words) * 11)
        else:
            brev = max(10, 100 - (n_words - 24) * 7)

        parts = {
            "SPECIFICITY": spec,
            "ADDRESS": addr,
            "STAKES": stk,
            "CURIOSITY": cur,
            "BREVITY": brev
        }
        vals = list(parts.values())
        verdict = round(0.6 * (sum(vals) / len(vals)) + 0.4 * min(vals))
        band_name = "STRONG" if verdict >= 72 else "WORKABLE" if verdict >= 55 else "WEAK"
        name = "Unclassified"
        hits = 0
        for f in FORMULAS:
            matched_p = sum(1 for p in f.get("match", []) if re.search(p, t, re.I))
            if matched_p > hits:
                name, hits = f.get("name", "Unclassified"), matched_p

    return {
        "hook": t,
        "properties": parts,
        "verdict": int(verdict),
        "band": band_name,
        "formula": name,
        "matched_patterns": hits,
        "weakest_property": min(parts, key=parts.get) if parts else "NONE"
    }


def generate_hook_candidates(
    topic: str,
    base_hook: Optional[str] = None,
    arxiv_meta: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Synthesizes candidate Beat 1 hooks inspired by proven archetypes from hooks.json:
    - The Statistic (concrete %/number + consequence)
    - The Mistake (name error viewer's architecture makes)
    - Contrarian Flip (challenge conventional wisdom)
    - The Warning (impending cost/failure before fix)
    - The Question (direct second-person query)
    - The Superlative / Teardown
    """
    candidates: List[str] = []
    if base_hook and base_hook.strip():
        candidates.append(base_hook.strip())

    # Extract concrete metrics if available
    metric = "50%"
    if arxiv_meta and isinstance(arxiv_meta, dict):
        abstract = arxiv_meta.get("abstract", "")
        m = re.findall(r"\b(\d+[\d,.]*(?:%|x|PFLOPS|TFLOPS|GB|MB))\b", abstract)
        if m:
            metric = m[0]
    elif metadata and isinstance(metadata, dict):
        metric = metadata.get("payoff_stat") or metadata.get("scale_metric") or "50%"

    clean_topic = topic.split(":")[0].strip()

    # 1. The Statistic archetype (numbers, address, stakes, curiosity)
    candidates.append(
        f"Over {metric} of your GPU memory is wasted before you see how {clean_topic} actually fixes it."
    )
    # 2. The Question archetype (curiosity trigger, stakes, address)
    candidates.append(
        f"Why do {metric} of your GPU cycles waste compute before {clean_topic} fixes the bottleneck?"
    )
    # 3. The Warning archetype (urgency, cost, concrete metric)
    candidates.append(
        f"Do not train your next model before you see how {clean_topic} cuts {metric} of your memory waste."
    )
    # 4. The Mistake / Address archetype (common error viewer makes)
    candidates.append(
        f"You are probably making the mistake of wasting compute before you test {clean_topic}."
    )
    # 5. Contrarian Flip archetype (challenge conventional advice)
    candidates.append(
        f"Everyone tells you your model needs more compute, but {clean_topic} proves that advice actually wrong."
    )
    # 6. The Superlative / Proof archetype (single breakthrough)
    candidates.append(
        f"This 1 breakthrough in {clean_topic} stops your GPU from wasting compute before you run out of memory."
    )

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for c in candidates:
        norm = c.strip().lower()
        if norm not in seen and len(norm) > 10:
            seen.add(norm)
            deduped.append(c.strip())

    return deduped


def gate_and_select_best_hook(candidates: List[str]) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Programmatically runs hookscore on all candidates and selects the winner.
    Returns: (winning_hook_text, winning_eval_dict, all_evaluations_sorted)
    """
    if not candidates:
        raise ValueError("Cannot gate empty candidates list.")

    evaluations = [score_hook(c) for c in candidates if c.strip()]
    if not evaluations:
        raise ValueError("No valid candidate hooks provided.")

    # Sort descending by verdict score; tie-break by weakest property score
    evaluations.sort(
        key=lambda r: (
            r["verdict"],
            min(r["properties"].values()) if r["properties"] else 0,
            r["properties"].get("SPECIFICITY", 0)
        ),
        reverse=True
    )

    winner = evaluations[0]
    return winner["hook"], winner, evaluations


def optimize_script_hook(
    spec: Dict[str, Any],
    arxiv_meta: Optional[Dict[str, Any]] = None,
    candidate_hooks: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Integrates hook scoring gating directly into a script specification.
    Evaluates candidates, selects the highest scoring hook for Beat 1,
    and updates the spec with audit metadata.
    """
    beats = spec.get("beats", [])
    if not beats:
        return spec

    topic = spec.get("title") or spec.get("id") or "Frontier AI"
    base_hook = beats[0].get("text", "")
    metadata = spec.get("metadata", {})

    if candidate_hooks and len(candidate_hooks) > 0:
        candidates = list(candidate_hooks)
        if base_hook and base_hook not in candidates:
            candidates.append(base_hook)
    else:
        candidates = generate_hook_candidates(
            topic=topic,
            base_hook=base_hook,
            arxiv_meta=arxiv_meta,
            metadata=metadata
        )

    winning_hook, winner_eval, all_evals = gate_and_select_best_hook(candidates)

    # Update Beat 1 text with winning gated hook
    beats[0]["text"] = winning_hook
    beats[0]["hook_score"] = winner_eval["verdict"]
    beats[0]["hook_band"] = winner_eval["band"]
    beats[0]["hook_formula"] = winner_eval["formula"]

    # Store full gating audit on spec
    spec["hook_gating"] = {
        "selected_hook": winning_hook,
        "verdict": winner_eval["verdict"],
        "band": winner_eval["band"],
        "formula": winner_eval["formula"],
        "properties": winner_eval["properties"],
        "weakest_property": winner_eval["weakest_property"],
        "candidates_evaluated": len(all_evals),
        "rankings": [
            {
                "hook": e["hook"],
                "verdict": e["verdict"],
                "band": e["band"],
                "formula": e["formula"]
            }
            for e in all_evals
        ]
    }

    print(f"🎯 [Hook Scoring Gating] Winner ({winner_eval['verdict']}/100, {winner_eval['band']}, {winner_eval['formula']}): \"{winning_hook}\"")
    return spec
