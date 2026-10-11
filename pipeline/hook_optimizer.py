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


def clean_display_topic(topic: str) -> str:
    """Cleans raw topic slugs, prefixes, and colons into natural display names."""
    if not topic:
        return "Frontier AI"
    t = topic.split(":")[0].strip()
    for prefix in (
        "mechanism_deepdive_", "architecture_breakdown_", "model_showdown_",
        "benchmark_news_", "developer_perks_", "tech_news_", "perk_", "blog_", "news_", "gh_"
    ):
        if t.startswith(prefix):
            t = t[len(prefix):]
    t = t.replace("_", " ").strip()
    if t.islower():
        t = t.title()
    return t or "Frontier AI"


def extract_metric_from_context(
    arxiv_meta: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Extracts concrete metrics (dollars, multipliers, percentages, compute) without
    inventing a fake '50%' fallback.
    """
    text = ""
    if arxiv_meta and isinstance(arxiv_meta, dict):
        text += arxiv_meta.get("title", "") + " "
        text += arxiv_meta.get("abstract", "") + " "
        text += arxiv_meta.get("summary", "") + " "
        key_facts = arxiv_meta.get("key_facts", [])
        if isinstance(key_facts, list):
            text += " ".join(str(k) for k in key_facts) + " "
    if metadata and isinstance(metadata, dict):
        for k in ("payoff_stat", "scale_metric", "metric", "stat"):
            val = metadata.get(k)
            if val and isinstance(val, str) and val.strip() and val.strip() != "50%":
                return val.strip()

    if not text.strip():
        return None

    # 1. Dollar amounts ($25,000, $350k, etc.)
    m_dollars = re.findall(r"(\$\d+[\d,.]*(?:[kKmMbB]|(?:\s?(?:thousand|million|credits)))?)\b", text)
    if m_dollars:
        return m_dollars[0].strip()

    # 2. Multipliers (76x, 2.4x, 10x)
    m_multipliers = re.findall(r"\b(\d+[\d,.]*x)\b", text, re.I)
    if m_multipliers:
        return m_multipliers[0].strip()

    # 3. Percentages (68.7%, 90%, 98.2%)
    m_percent = re.findall(r"\b(\d+[\d,.]*%)\b", text)
    if m_percent:
        return m_percent[0].strip()

    # 4. Compute / Hardware units (1.2 PFLOPS, 800 TFLOPS, 24GB)
    m_compute = re.findall(r"\b(\d+[\d,.]*\s?(?:PFLOPS|TFLOPS|EFLOPS|GFLOPS|GB|TB|MB|ms))\b", text, re.I)
    if m_compute:
        return m_compute[0].strip()

    return None


def resolve_category_and_domain(
    topic: str,
    category: Optional[str] = None,
    domain_taxonomy: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    arxiv_meta: Optional[Dict[str, Any]] = None
) -> Tuple[str, str]:
    """Infers category and domain taxonomy from context."""
    cat = (
        category
        or (metadata.get("category") if metadata else None)
        or (arxiv_meta.get("category") if arxiv_meta else None)
        or ""
    ).lower()

    dom = (
        domain_taxonomy
        or (metadata.get("domain_taxonomy") if metadata else None)
        or (arxiv_meta.get("domain_taxonomy") if arxiv_meta else None)
        or ""
    ).lower()

    t_lower = topic.lower()

    # Prioritize specific detected categories from keywords in topic or ID
    if any(w in t_lower for w in ("perk", "credit", "grant", "tier", "founders", "startup program")) or (arxiv_meta and str(arxiv_meta.get("id", "")).startswith("perk_")):
        cat = "developer_perks"
    elif any(w in t_lower for w in ("blog_", "news_", "official_blog")) or (arxiv_meta and any(str(arxiv_meta.get("id", "")).startswith(p) for p in ("blog_", "news_"))):
        cat = "tech_news"
    elif not cat or cat in ("custom", "video", "paper"):
        if any(w in t_lower for w in (" vs ", "showdown", "compared", "benchmark")):
            cat = "model_showdown"
        elif any(w in t_lower for w in ("robot", "manipulation", "locomotion", "embodied", "tamp")):
            cat = "robotics_tamp"
        elif any(w in t_lower for w in ("diffusion", "video gen", "3d", "cinemagraph", "gaussian")):
            cat = "multimodal_diffusion"
        elif any(w in t_lower for w in ("sae", "interpretability", "dictionary learning")):
            cat = "neural_sae"
        elif any(w in t_lower for w in ("quant", "attention", "flash", "gpu", "kernel", "memory")):
            cat = "hardware_efficiency"
        else:
            cat = "mechanism_deepdive"

    return cat, dom


def is_candidate_relevant(candidate: str, category: str) -> bool:
    """Rejects cross-category contamination (e.g. GPU waste on perks videos)."""
    c_low = candidate.lower()
    if category == "developer_perks":
        if any(b in c_low for b in ("gpu cycles", "train your next model", "memory overhead", "render latency")):
            return False
    elif category in ("tech_news", "model_showdown"):
        if "gpu cycles waste compute" in c_low:
            return False
    elif category in ("robotics_tamp", "robotics"):
        if any(b in c_low for b in ("gpu cycles", "render latency", "diffusion")):
            return False
    return True


def generate_hook_candidates(
    topic: str,
    base_hook: Optional[str] = None,
    arxiv_meta: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    category: Optional[str] = None,
    domain_taxonomy: Optional[str] = None
) -> List[str]:
    """
    Synthesizes category-aware, diverse Beat 1 hooks inspired by proven archetypes from hooks.json:
    - The Statistic (concrete %/number + consequence)
    - The Mistake (name error viewer's architecture makes)
    - Contrarian Flip (challenge conventional wisdom)
    - The Warning (impending cost/failure before fix)
    - The Question (direct second-person query)
    - The Superlative / Teardown
    """
    candidates: List[str] = []

    # Preserve base hook
    if base_hook and base_hook.strip():
        b_clean = base_hook.strip()
        candidates.append(b_clean)
        # Create 1-2 story-preserving addressed refinements of base hook
        b_core = b_clean.rstrip(".")
        if len(b_core) > 5 and not any(w in b_core.lower() for w in ("welcome", "today we", "in this video")):
            # If base hook lacks second-person address, create an addressed variation
            if not any(y in b_core.lower() for y in ("you", "your")):
                candidates.append(f"Before you deploy your next project, see how {b_core[0].lower() + b_core[1:]}.")
                if not b_core.endswith("?"):
                    candidates.append(f"Did you know {b_core[0].lower() + b_core[1:]}?")

    # Resolve category and domain
    cat, dom = resolve_category_and_domain(
        topic=topic,
        category=category,
        domain_taxonomy=domain_taxonomy,
        metadata=metadata,
        arxiv_meta=arxiv_meta
    )

    # Extract real metric (NO fake 50% fallback)
    metric = extract_metric_from_context(arxiv_meta=arxiv_meta, metadata=metadata)
    clean_topic = clean_display_topic(topic)

    # Category-tailored candidate synthesis
    if cat == "developer_perks":
        if metric:
            candidates.append(
                f"Stop paying full price for AI APIs before you claim {metric} in free credits with {clean_topic}."
            )
            candidates.append(
                f"Are you burning your own cash on API bills before claiming this {metric} grant from {clean_topic}?"
            )
            candidates.append(
                f"Before you spend another dollar on model tokens, see how {clean_topic} gives you {metric} free."
            )
            candidates.append(
                f"Did you know you can claim up to {metric} in free compute right now through {clean_topic}?"
            )
        else:
            candidates.append(
                f"Stop paying full price for AI tokens before checking out {clean_topic}."
            )
            candidates.append(
                f"Are you burning your startup budget on API calls before claiming {clean_topic}?"
            )
            candidates.append(
                f"Before you pay your next cloud bill, make sure you aren't missing out on {clean_topic}."
            )
            candidates.append(
                f"You might be overpaying for AI infrastructure if you haven't applied for {clean_topic}."
            )

    elif cat in ("tech_news", "blogs", "news", "official_blogs"):
        if metric:
            candidates.append(
                f"Before you deploy your next model, see how {clean_topic} cuts costs by {metric}."
            )
            candidates.append(
                f"Why are leading AI teams switching to {clean_topic} after this {metric} breakthrough?"
            )
            candidates.append(
                f"You might be running outdated architecture before you test the {metric} speedup in {clean_topic}."
            )
            candidates.append(
                f"Everyone thought frontier models reached a ceiling, until {clean_topic} proved them wrong by {metric}."
            )
        else:
            candidates.append(
                f"Before you build your next AI workflow, see what {clean_topic} just dropped."
            )
            candidates.append(
                f"Why is everyone in the AI community talking about {clean_topic} today?"
            )
            candidates.append(
                f"You might be building on outdated tech before you test what {clean_topic} can do."
            )
            candidates.append(
                f"Everyone assumed standard models were good enough, until {clean_topic} changed the game."
            )

    elif cat in ("model_showdown", "benchmark_news") or " vs " in topic.lower():
        if metric:
            candidates.append(
                f"Does {clean_topic} actually crush the competition by {metric}, or is it just benchmark hype?"
            )
            candidates.append(
                f"Before you choose your foundation model, look at how {clean_topic} beats the leader by {metric}."
            )
            candidates.append(
                f"Why are top engineering teams abandoning old flagships for {clean_topic}'s {metric} gain?"
            )
            candidates.append(
                f"Everyone tells you to use the reigning model, but {clean_topic} outperforms it by {metric}."
            )
        else:
            candidates.append(
                f"Does {clean_topic} actually beat the reigning champion, or is it just marketing hype?"
            )
            candidates.append(
                f"Before you lock in your foundation model, see who actually wins this showdown with {clean_topic}."
            )
            candidates.append(
                f"You might be betting on the wrong AI architecture before you see this benchmark breakdown."
            )
            candidates.append(
                f"Everyone assumed the leaderboard was settled, until {clean_topic} entered the ring."
            )

    elif cat in ("robotics_tamp", "robotics") or dom == "robotics_tamp":
        if metric:
            candidates.append(
                f"Why do standard robots fail {metric} of real-world trials before {clean_topic} fixes execution?"
            )
            candidates.append(
                f"Before you deploy your next physical policy, see how {clean_topic} unlocks {metric} better precision."
            )
            candidates.append(
                f"You are probably training robot policies with the wrong primitives before testing {clean_topic}."
            )
        else:
            candidates.append(
                f"Why do multi-task robots struggle in the real world before {clean_topic} fixes their execution?"
            )
            candidates.append(
                f"Before you train your next physical robot policy, see how {clean_topic} bridges the sim-to-real gap."
            )
            candidates.append(
                f"Most robot foundation models fail on complex manipulation, but {clean_topic} proves a working fix."
            )

    elif cat in ("multimodal_diffusion", "diffusion", "vision") or dom == "multimodal_diffusion":
        if metric:
            candidates.append(
                f"Why do standard diffusion models waste {metric} of render latency before {clean_topic}?"
            )
            candidates.append(
                f"Before you generate another frame, see how {clean_topic} cuts render latency by {metric}."
            )
        else:
            candidates.append(
                f"Why do standard video and 3D models lose temporal coherence before {clean_topic} fixes it?"
            )
            candidates.append(
                f"Before you render your next diffusion frame, see how {clean_topic} solves the consistency bottleneck."
            )
            candidates.append(
                f"You are probably wasting render cycles if you haven't seen how {clean_topic} handles 3D generation."
            )

    else:
        # Academic papers / architecture breakdown / hardware efficiency
        if metric:
            candidates.append(
                f"Before you train your next model, see how {clean_topic} cuts {metric} of memory overhead."
            )
            candidates.append(
                f"Why do standard transformer architectures hit a memory wall before {clean_topic} unlocks {metric} gains?"
            )
            candidates.append(
                f"You might be leaving {metric} of your hardware performance on the table without {clean_topic}."
            )
            candidates.append(
                f"Everyone assumed standard attention was optimal, until {clean_topic} proved a {metric} leap."
            )
            candidates.append(
                f"Do not scale your next training run before you see how {clean_topic} delivers {metric}."
            )
        else:
            candidates.append(
                f"Before you scale your next model, see why {clean_topic} completely rethinks standard architecture."
            )
            candidates.append(
                f"Why do standard deep learning models hit a scaling bottleneck before {clean_topic} restructures it?"
            )
            candidates.append(
                f"You might be building on a flawed architecture before you understand how {clean_topic} works."
            )
            candidates.append(
                f"Everyone assumed scaling parameters was the only answer, until {clean_topic} proved otherwise."
            )
            candidates.append(
                f"Do not deploy your next AI architecture before testing how {clean_topic} operates."
            )

    # Filter out irrelevant cross-category candidates
    candidates = [c for c in candidates if is_candidate_relevant(c, cat)]

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
    Evaluates candidates, respects authentic high-quality base hooks from the LLM,
    selects the highest scoring category-aware hook for Beat 1,
    and updates the spec with audit metadata.
    """
    beats = spec.get("beats", [])
    if not beats:
        return spec

    topic = spec.get("title") or spec.get("id") or "Frontier AI"
    base_hook = beats[0].get("text", "")
    metadata = spec.get("metadata", {})
    category = spec.get("category")
    domain_taxonomy = spec.get("domain_taxonomy")

    if candidate_hooks and len(candidate_hooks) > 0:
        candidates = list(candidate_hooks)
        if base_hook and base_hook not in candidates:
            candidates.append(base_hook)
    else:
        candidates = generate_hook_candidates(
            topic=topic,
            base_hook=base_hook,
            arxiv_meta=arxiv_meta,
            metadata=metadata,
            category=category,
            domain_taxonomy=domain_taxonomy
        )

    winning_hook, winner_eval, all_evals = gate_and_select_best_hook(candidates)

    # Storyline preservation guard:
    # If the base hook from the LLM has a solid score (>= 58, WORKABLE/STRONG) and is
    # reasonably close to the top synthetic candidate (<= 8 points), prefer keeping
    # the LLM's bespoke narrative to avoid generic repetitive templates!
    if base_hook and base_hook.strip():
        base_eval = score_hook(base_hook.strip())
        if base_eval["verdict"] >= 58 and (winner_eval["verdict"] - base_eval["verdict"] <= 8):
            winning_hook = base_hook.strip()
            winner_eval = base_eval

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

