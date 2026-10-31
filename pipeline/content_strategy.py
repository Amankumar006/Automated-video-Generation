"""Audience-led topic strategy for The Model Verse.

The production daemon historically ranked fresh research and then asked an LLM
to choose a visually teachable paper.  This module adds a deterministic,
audience-aware layer before that step.  It intentionally has no network or LLM
dependencies so dry-runs, tests, and production selection use the same policy.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


CONTENT_STRATEGY_VERSION = "audience-led-v1"
COOLDOWN_DAYS = 30

AUDIENCE_PROFILE: Dict[str, Any] = {
    "id": "global_ai_builder",
    "language": "en",
    "segments": ["developer", "student", "indie_hacker", "technical_founder"],
    "priority": "qualified_growth",
}

FORMAT_PROFILES: Dict[str, Dict[str, str]] = {
    "practical_demo": {
        "label": "Practical demo",
        "brief": "Show a real workflow, result, limitation, and who should use it.",
    },
    "comparison": {
        "label": "Comparison",
        "brief": "Compare named tools or models using one meaningful, source-backed metric.",
    },
    "current_release": {
        "label": "Current release",
        "brief": "Explain what changed in a current release and why builders should care now.",
    },
    "mechanism": {
        "label": "Mechanism with payoff",
        "brief": "Animate the mechanism only after establishing the practical problem it solves.",
    },
}

FORMAT_ALIASES = {
    "tool_reaction": "practical_demo",
    "system_reveal": "practical_demo",
    "motion_story": "mechanism",
    "character_analogy": "mechanism",
}

INITIAL_FORMAT_TARGETS = {
    "practical_demo": 8,
    "comparison": 5,
    "current_release": 4,
    "mechanism": 3,
}

_SOURCE_URL_KEYS = (
    "source_url",
    "canonical_url",
    "official_url",
    "url",
    "arxiv_url",
    "claim_url",
)
_DATE_KEYS = ("published_at", "published_date", "publishedAt", "updated_at", "date")
_UTILITY_TERMS = (
    "how",
    "use",
    "tool",
    "agent",
    "coding",
    "developer",
    "startup",
    "credit",
    "free",
    "cost",
    "faster",
    "speed",
    "latency",
    "memory",
    "local",
    "laptop",
    "benchmark",
    "compare",
    "versus",
    " vs ",
)
_BUILDER_TERMS = (
    "developer",
    "coding",
    "agent",
    "repo",
    "github",
    "api",
    "model",
    "inference",
    "gpu",
    "local",
    "open source",
    "open-source",
    "workflow",
    "startup",
    "credits",
    "benchmark",
    "robot",
    "security",
)
_MECHANISM_TERMS = (
    "attention",
    "cache",
    "quantization",
    "kernel",
    "router",
    "routing",
    "diffusion",
    "flow matching",
    "memory",
    "latency",
    "token",
    "agent",
    "robot",
    "retrieval",
    "reasoning",
)
_ABSTRACT_TITLE_TERMS = (
    "architecture",
    "paradigm",
    "framework",
    "approach",
    "dynamics",
    "representation",
    "technical report",
)


@dataclass(frozen=True)
class StrategyDecision:
    """Serializable decision produced for one source candidate."""

    eligible: bool
    score: float
    audience_fit: float
    demand: float
    utility: float
    demonstrability: float
    freshness: float
    evidence: float
    recommended_format: str
    primary_segment: str
    viewer_problem: str
    promised_payoff: str
    proof_asset: str
    hook: str
    hard_rejections: Tuple[str, ...] = ()
    penalties: Tuple[str, ...] = ()
    reasons: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _nested(candidate: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = candidate.get(key)
        if value not in (None, "", []):
            return value
    return None


def _source(candidate: Dict[str, Any]) -> str:
    source = str(candidate.get("source") or "").lower()
    if source:
        return source
    candidate_id = str(candidate.get("id") or "").lower()
    if candidate_id.startswith("gh_"):
        return "github"
    if candidate_id.startswith(("blog_", "news_")):
        return "blogs"
    if candidate_id.startswith("perk_"):
        return "perks"
    return "arxiv"


def _source_url(candidate: Dict[str, Any]) -> str:
    for key in _SOURCE_URL_KEYS:
        value = candidate.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value
    for container_key in ("repo_metadata", "blog_metadata", "perk_metadata", "model_metadata"):
        container = candidate.get(container_key) or {}
        if not isinstance(container, dict):
            continue
        for key in _SOURCE_URL_KEYS:
            value = container.get(key)
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                return value
    candidate_id = str(candidate.get("id") or "")
    if re.fullmatch(r"\d{4}\.\d{4,5}", candidate_id):
        return f"https://arxiv.org/abs/{candidate_id}"
    if candidate_id.startswith("gh_"):
        repo = candidate_id[3:].replace("_", "/", 1)
        return f"https://github.com/{repo}"
    return ""


def _date_value(candidate: Dict[str, Any]) -> Optional[str]:
    source = _source(candidate)
    if source in {"github", "github_api", "github_search_api", "curated_trending"}:
        container = candidate.get("repo_metadata") or {}
        return _nested(container, "pushed_at", "updated_at") or _nested(candidate, "updated_at")
    if source in {"perks", "verified_perks"}:
        container = candidate.get("perk_metadata") or {}
        return _nested(container, "last_verified_date") or _nested(candidate, "last_verified_date")
    if source in {"huggingface_models", "huggingface", "hf_models"}:
        container = candidate.get("model_metadata") or {}
        return _nested(container, "last_modified", "updated_at") or _nested(candidate, "updated_at", "published_at")
    blog = candidate.get("blog_metadata") or {}
    return _nested(candidate, *_DATE_KEYS) or _nested(blog, *_DATE_KEYS)


def _parse_date(value: Optional[str]) -> Optional[dt.datetime]:
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = dt.datetime.strptime(text[:10], "%Y-%m-%d")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _age_days(candidate: Dict[str, Any], reference_date: Optional[dt.date]) -> Optional[int]:
    parsed = _parse_date(_date_value(candidate))
    if parsed is None:
        return None
    now = dt.datetime.combine(
        reference_date or dt.datetime.now(dt.timezone.utc).date(),
        dt.time.min,
        tzinfo=dt.timezone.utc,
    )
    return max(0, (now - parsed).days)


def _text_blob(candidate: Dict[str, Any]) -> str:
    fields = [
        candidate.get("title", ""),
        candidate.get("abstract", ""),
        candidate.get("description", ""),
        candidate.get("topic", ""),
        candidate.get("recommended_hook", ""),
    ]
    for key in ("editorial_notes", "repo_metadata", "blog_metadata", "perk_metadata", "model_metadata"):
        value = candidate.get(key)
        if isinstance(value, dict):
            fields.extend(str(v) for v in value.values() if isinstance(v, (str, int, float)))
    return " ".join(str(value) for value in fields if value).lower()


def _taxonomy(candidate: Dict[str, Any]) -> str:
    return str(
        candidate.get("taxonomy")
        or candidate.get("domain_taxonomy")
        or candidate.get("recommended_taxonomy")
        or "general_breakthroughs"
    ).lower()


def _category(candidate: Dict[str, Any]) -> str:
    return str(candidate.get("recommended_category") or candidate.get("category") or "mechanism_deepdive").lower()


def _recommended_format(candidate: Dict[str, Any]) -> str:
    category = _category(candidate)
    source = _source(candidate)
    blob = _text_blob(candidate)
    if category in {"model_showdown", "benchmark_news"} or any(term in blob for term in (" versus ", " vs ", "comparison", "benchmark")):
        return "comparison"
    if category == "developer_perks" or source in {"perks", "verified_perks"}:
        return "practical_demo"
    if source in {"blogs", "official_blogs", "news"} or category == "tech_news":
        return "current_release"
    if source in {"github", "github_api", "github_search_api", "curated_trending"}:
        return "practical_demo"
    if source in {"huggingface_models", "huggingface", "hf_models"}:
        return "practical_demo"
    return "mechanism"


def _primary_segment(candidate: Dict[str, Any]) -> str:
    blob = _text_blob(candidate)
    if any(term in blob for term in ("startup", "credits", "founder", "cost")):
        return "technical_founder"
    if any(term in blob for term in ("student", "beginner", "tutorial", "learn")):
        return "student"
    if any(term in blob for term in ("agent", "repo", "github", "coding", "api", "inference", "kernel")):
        return "developer"
    return "developer"


def _viewer_problem(candidate: Dict[str, Any], fmt: str) -> str:
    notes = candidate.get("editorial_notes") or {}
    if isinstance(notes, dict):
        for key in ("viewer_problem", "problem", "recommended_problem"):
            if notes.get(key):
                return str(notes[key]).strip()
    title = str(candidate.get("title") or "this AI system").strip().rstrip(".")
    if fmt == "comparison":
        return f"Builders need to know which option is actually better for {title}."
    if fmt == "practical_demo":
        return f"Builders need to know what {title} changes in a real workflow."
    if fmt == "current_release":
        return f"Builders need to understand why {title} matters now."
    return f"Builders need a usable mental model for {title}."


def _promised_payoff(candidate: Dict[str, Any], fmt: str) -> str:
    notes = candidate.get("editorial_notes") or {}
    if isinstance(notes, dict):
        for key in ("promised_payoff", "payoff", "viewer_payoff"):
            if notes.get(key):
                return str(notes[key]).strip()
    title = str(candidate.get("title") or "the system").strip().rstrip(".")
    if fmt == "comparison":
        return f"Leave knowing which {title} option deserves a test."
    if fmt == "practical_demo":
        return f"Leave knowing when to try {title} and what limitation to expect."
    if fmt == "current_release":
        return f"Leave knowing the practical consequence of {title}."
    return f"Leave understanding the mechanism behind {title} and its practical payoff."


def _proof_asset(candidate: Dict[str, Any]) -> str:
    if candidate.get("code_snippet"):
        return "source code or execution kernel"
    if candidate.get("benchmark_comparison") or candidate.get("benchmarks"):
        return "source-backed benchmark"
    if candidate.get("repo_metadata") or candidate.get("model_metadata"):
        return "repository metadata and README"
    if candidate.get("key_facts") or candidate.get("paper_figures"):
        return "source-backed facts or figure"
    if candidate.get("abstract") or candidate.get("description"):
        return "source-backed mechanism"
    return ""


def _hook(candidate: Dict[str, Any], fmt: str) -> str:
    notes = candidate.get("editorial_notes") or {}
    if isinstance(notes, dict) and notes.get("recommended_hook"):
        return str(notes["recommended_hook"]).strip()
    title = str(candidate.get("title") or "This AI system").strip().rstrip(".")
    if fmt == "comparison":
        return f"{title}: which one actually wins when you use it?"
    if fmt == "practical_demo":
        return f"I tested {title} so you can see what it actually changes."
    if fmt == "current_release":
        return f"{title} is getting attention—here is the part builders should care about."
    return f"{title} sounds abstract, but its practical bottleneck is surprisingly concrete."


def _source_claims(candidate: Dict[str, Any]) -> List[str]:
    """Normalize source-backed facts without asking an LLM to invent them."""
    claims = candidate.get("source_claims") or candidate.get("claims") or candidate.get("key_facts") or []
    if isinstance(claims, str):
        claims = [claims]
    if isinstance(claims, dict):
        claims = [f"{key}: {value}" for key, value in claims.items()]
    if not isinstance(claims, list):
        claims = []
    normalized = [str(claim).strip() for claim in claims if str(claim).strip()]
    if not normalized and candidate.get("abstract"):
        normalized.append(str(candidate["abstract"]).strip()[:500])
    return normalized[:8]


def _risk_flags(candidate: Dict[str, Any]) -> List[str]:
    flags = [str(flag) for flag in (candidate.get("risk_flags") or [])]
    if candidate.get("unsupported_numerical_claims"):
        flags.append("unsupported numerical claim")
    if candidate.get("claim_validation") is False:
        flags.append("source claim validation failed")
    return sorted(set(flags))


def _trend_score(candidate: Dict[str, Any], analytics: Optional[Dict[str, Any]]) -> float:
    score = 0.0
    upvotes = float(candidate.get("upvotes") or 0)
    stars = float((candidate.get("repo_metadata") or {}).get("stars") or candidate.get("stars") or 0)
    forks = float((candidate.get("repo_metadata") or {}).get("forks") or candidate.get("forks") or 0)
    score += min(upvotes / 50.0, 1.0) * 0.35
    score += min(stars / 100_000.0, 1.0) * 0.35
    score += min(forks / 10_000.0, 1.0) * 0.15
    multiplier = float(candidate.get("analytics_multiplier") or 1.0)
    if analytics:
        multipliers = analytics.get("category_multipliers") or analytics.get("taxonomy_multipliers") or {}
        multiplier = float(multipliers.get(_taxonomy(candidate), multiplier))
    score += min(max(multiplier - 0.75, 0.0) / 1.25, 1.0) * 0.15
    return min(score, 1.0)


def _freshness_score(age_days: Optional[int], source: str) -> float:
    if age_days is None:
        return 0.0
    windows = {
        "arxiv": 7,
        "huggingface": 7,
        "hf": 7,
        "huggingface_models": 7,
        "hf_models": 7,
        "github": 7,
        "github_api": 7,
        "github_search_api": 7,
        "curated_trending": 7,
        "blogs": 14,
        "official_blogs": 14,
        "news": 14,
        "perks": 14,
        "verified_perks": 14,
    }
    latest = windows.get(source, 7)
    if age_days <= latest:
        return 1.0
    if age_days <= 30:
        return max(0.0, 1.0 - ((age_days - latest) / max(1, 30 - latest))) * 0.65
    return 0.0


def _history_records(history: Optional[Dict[str, Any]]) -> Iterable[Tuple[str, Dict[str, Any]]]:
    if not history:
        return []
    records = history.get("processed_papers", history.get("videos", {}))
    if isinstance(records, dict):
        return records.items()
    if isinstance(records, list):
        return ((str(record.get("id") or record.get("video_id") or ""), record) for record in records)
    return []


def _format_mix_counts(history: Optional[Dict[str, Any]]) -> Dict[str, int]:
    """Normalize prior engine formats into the four experiment formats."""
    counts = {name: 0 for name in INITIAL_FORMAT_TARGETS}
    for _, record in _history_records(history):
        raw_format = record.get("recommended_format") or record.get("content_format")
        normalized = FORMAT_ALIASES.get(str(raw_format), str(raw_format))
        if normalized in counts:
            counts[normalized] += 1
    return counts


def _is_duplicate(candidate: Dict[str, Any], history: Optional[Dict[str, Any]], reference_date: Optional[dt.date]) -> bool:
    candidate_id = str(candidate.get("id") or "").lower()
    candidate_title = re.sub(r"[^a-z0-9]+", " ", str(candidate.get("title") or "").lower()).strip()
    candidate_tokens = {token for token in candidate_title.split() if len(token) >= 5}
    current_date = reference_date or dt.datetime.now(dt.timezone.utc).date()
    for record_id, record in _history_records(history):
        if str(record_id).lower() == candidate_id and candidate_id:
            return True
        record_date = _parse_date(record.get("produced_at") or record.get("published_at"))
        if record_date is None or (current_date - record_date.date()).days > COOLDOWN_DAYS:
            continue
        record_title = re.sub(r"[^a-z0-9]+", " ", str(record.get("title") or "").lower()).strip()
        record_tokens = {token for token in record_title.split() if len(token) >= 5}
        if candidate_tokens and record_tokens:
            overlap = len(candidate_tokens & record_tokens) / max(1, len(candidate_tokens | record_tokens))
            if overlap >= 0.6:
                return True
    return False


def evaluate_candidate(
    candidate: Dict[str, Any],
    *,
    history: Optional[Dict[str, Any]] = None,
    analytics: Optional[Dict[str, Any]] = None,
    reference_date: Optional[dt.date] = None,
    audience_profile: Optional[Dict[str, Any]] = None,
) -> StrategyDecision:
    """Evaluate one candidate using the fixed audience-led score policy."""
    audience_profile = audience_profile or AUDIENCE_PROFILE
    source = _source(candidate)
    blob = _text_blob(candidate)
    title = str(candidate.get("title") or "").strip()
    fmt = _recommended_format(candidate)
    age_days = _age_days(candidate, reference_date)
    source_url = _source_url(candidate)
    proof = _proof_asset(candidate)
    problem = _viewer_problem(candidate, fmt)
    payoff = _promised_payoff(candidate, fmt)
    hook = _hook(candidate, fmt)

    hard_rejections: List[str] = []
    penalties: List[str] = []
    reasons: List[str] = []
    if not source_url:
        hard_rejections.append("missing source URL")
    if age_days is None:
        hard_rejections.append("missing dated evidence")
    if age_days is not None and age_days > 30:
        hard_rejections.append(f"stale evidence ({age_days} days)")
    if not problem or not payoff:
        hard_rejections.append("missing viewer problem or payoff")
    if not proof and not any(term in blob for term in _MECHANISM_TERMS):
        hard_rejections.append("missing proof asset or visual mechanism")
    if _is_duplicate(candidate, history, reference_date):
        hard_rejections.append("duplicate within cooldown window")
    risk_flags = _risk_flags(candidate)
    if risk_flags:
        hard_rejections.extend(risk_flags)

    utility_hits = sum(1 for term in _UTILITY_TERMS if term in blob)
    builder_hits = sum(1 for term in _BUILDER_TERMS if term in blob)
    mechanism_hits = sum(1 for term in _MECHANISM_TERMS if term in blob)
    evidence_parts = sum(bool(value) for value in (source_url, _date_value(candidate), candidate.get("abstract") or candidate.get("description"), proof))

    demand = _trend_score(candidate, analytics)
    utility = min(1.0, 0.35 + (min(utility_hits, 5) / 5.0) * 0.65)
    demonstrability = min(1.0, 0.25 + (min(mechanism_hits, 5) / 5.0) * 0.45 + (0.30 if proof else 0.0))
    freshness = _freshness_score(age_days, source)
    evidence = min(1.0, evidence_parts / 4.0)
    audience_fit = min(1.0, 0.25 + (min(builder_hits, 6) / 6.0) * 0.75)

    if len(set(re.findall(r"[a-z0-9]+", title.lower())) & set(_ABSTRACT_TITLE_TERMS)) >= 2:
        penalties.append("abstract title packaging")
    if history:
        recent_formats = []
        recent_taxonomies = []
        for _, record in list(_history_records(history))[-5:]:
            if record.get("content_format"):
                recent_formats.append(record["content_format"])
            if record.get("taxonomy"):
                recent_taxonomies.append(record["taxonomy"])
        if recent_formats and recent_formats[-1] == fmt:
            penalties.append("repeated format")
        if recent_taxonomies and recent_taxonomies[-1] == _taxonomy(candidate):
            penalties.append("repeated taxonomy")

    score = round(
        demand * 25
        + utility * 20
        + demonstrability * 20
        + freshness * 15
        + evidence * 10
        + audience_fit * 10
        - len(penalties) * 5,
        2,
    )
    if demand >= 0.55:
        reasons.append("has measurable momentum")
    if utility >= 0.65:
        reasons.append("has a builder-facing use case")
    if demonstrability >= 0.65:
        reasons.append("can show a concrete mechanism or proof")
    if freshness >= 0.75:
        reasons.append("is within the latest window")
    if audience_fit >= 0.65:
        reasons.append("matches the global builder audience")

    eligible = not hard_rejections and score >= 55
    if score < 55:
        hard_rejections.append("below audience-led score threshold")

    return StrategyDecision(
        eligible=eligible,
        score=score,
        audience_fit=round(audience_fit, 3),
        demand=round(demand, 3),
        utility=round(utility, 3),
        demonstrability=round(demonstrability, 3),
        freshness=round(freshness, 3),
        evidence=round(evidence, 3),
        recommended_format=fmt,
        primary_segment=_primary_segment(candidate),
        viewer_problem=problem,
        promised_payoff=payoff,
        proof_asset=proof,
        hook=hook,
        hard_rejections=tuple(hard_rejections),
        penalties=tuple(penalties),
        reasons=tuple(reasons),
    )


def attach_strategy(candidate: Dict[str, Any], decision: StrategyDecision) -> Dict[str, Any]:
    """Attach a serializable editorial brief without changing source facts."""
    enriched = dict(candidate)
    enriched["content_strategy"] = {
        "version": CONTENT_STRATEGY_VERSION,
        "audience_profile": AUDIENCE_PROFILE["id"],
        "source_title": str(candidate.get("title") or "").strip(),
        "source_url": _source_url(candidate),
        "source_date": _date_value(candidate),
        "source_claims": _source_claims(candidate),
        "risk_flags": _risk_flags(candidate),
        "primary_segment": decision.primary_segment,
        "viewer_problem": decision.viewer_problem,
        "promised_payoff": decision.promised_payoff,
        "proof_asset": decision.proof_asset,
        "recommended_hook": decision.hook,
        "recommended_format": decision.recommended_format,
        "format_profile": FORMAT_PROFILES[decision.recommended_format],
        "score": decision.score,
        "score_breakdown": {
            "demand": round(decision.demand * 25, 2),
            "utility": round(decision.utility * 20, 2),
            "demonstrability": round(decision.demonstrability * 20, 2),
            "freshness": round(decision.freshness * 15, 2),
            "evidence": round(decision.evidence * 10, 2),
            "audience_fit": round(decision.audience_fit * 10, 2),
        },
        "penalties": list(decision.penalties),
        "reasons": list(decision.reasons),
        "hard_rejections": list(decision.hard_rejections),
    }
    enriched["editorial_notes"] = {
        **(enriched.get("editorial_notes") or {}),
        "recommended_hook": decision.hook,
        "viewer_problem": decision.viewer_problem,
        "promised_payoff": decision.promised_payoff,
        "proof_asset": decision.proof_asset,
        "primary_segment": decision.primary_segment,
        "recommended_format": decision.recommended_format,
    }
    enriched["content_format"] = decision.recommended_format
    return enriched


def rank_candidates(
    candidates: Sequence[Dict[str, Any]],
    *,
    count: int = 1,
    history: Optional[Dict[str, Any]] = None,
    analytics: Optional[Dict[str, Any]] = None,
    reference_date: Optional[dt.date] = None,
    audience_profile: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Rank eligible candidates and apply lightweight format/taxonomy diversity."""
    scored: List[Tuple[StrategyDecision, Dict[str, Any]]] = []
    for candidate in candidates:
        decision = evaluate_candidate(
            candidate,
            history=history,
            analytics=analytics,
            reference_date=reference_date,
            audience_profile=audience_profile,
        )
        enriched = attach_strategy(candidate, decision)
        if decision.eligible:
            scored.append((decision, enriched))

    format_counts = _format_mix_counts(history)

    def selection_key(item: Tuple[StrategyDecision, Dict[str, Any]]) -> Tuple[float, float, float, float]:
        decision, _candidate = item
        target = INITIAL_FORMAT_TARGETS.get(decision.recommended_format, 0)
        deficit = max(0, target - format_counts.get(decision.recommended_format, 0))
        # A small quota bonus prevents a strong format from crowding out the
        # planned 8/5/4/3 mix while keeping evidence score as the main signal.
        quota_bonus = min(4.0, deficit * 0.75)
        return (decision.score + quota_bonus, decision.score, decision.freshness, decision.demand)

    scored.sort(key=selection_key, reverse=True)
    selected: List[Dict[str, Any]] = []
    seen_formats: set[str] = set()
    seen_taxonomies: set[str] = set()
    for decision, candidate in scored:
        tax = _taxonomy(candidate)
        fmt = decision.recommended_format
        diversity_penalty = (fmt in seen_formats) + (tax in seen_taxonomies)
        candidate["content_strategy"]["selection_penalty"] = diversity_penalty
        target = INITIAL_FORMAT_TARGETS.get(fmt, 0)
        candidate["content_strategy"]["format_target"] = target
        candidate["content_strategy"]["format_count_before_selection"] = format_counts.get(fmt, 0)
        if selected and diversity_penalty >= 2 and len(scored) - len(selected) > count - len(selected):
            continue
        selected.append(candidate)
        seen_formats.add(fmt)
        seen_taxonomies.add(tax)
        if len(selected) >= max(1, count):
            break
    return selected


def strategy_report(candidates: Sequence[Dict[str, Any]], **kwargs: Any) -> List[Dict[str, Any]]:
    """Return dry-run-friendly decisions for eligible and rejected candidates."""
    report: List[Dict[str, Any]] = []
    for candidate in candidates:
        decision = evaluate_candidate(candidate, **kwargs)
        report.append({
            "id": candidate.get("id"),
            "title": candidate.get("title"),
            "source": _source(candidate),
            "eligible": decision.eligible,
            "score": decision.score,
            "format": decision.recommended_format,
            "audience": decision.primary_segment,
            "hook": decision.hook,
            "viewer_problem": decision.viewer_problem,
            "payoff": decision.promised_payoff,
            "reasons": list(decision.reasons),
            "rejections": list(decision.hard_rejections),
            "penalties": list(decision.penalties),
        })
    return sorted(report, key=lambda item: item["score"], reverse=True)
