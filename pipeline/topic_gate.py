"""Strict freshness and momentum gate for autonomous topic selection.

The gate deliberately rejects candidates without dated, auditable evidence. It
is used by the production daemon, while legacy recency helpers remain useful
for historical tests and offline analysis.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

from pipeline.config import calculate_content_age_days


LATEST_WINDOWS = {
    "arxiv": 7,
    "hf": 7,
    "blogs": 14,
    "official_blogs": 14,
    "github": 7,
    "github_api": 7,
    "github_search_api": 7,
    "curated_trending": 7,
    "perks": 14,
    "verified_perks": 14,
}
VIRAL_WINDOW_DAYS = 30


def _source(candidate: Dict[str, Any]) -> str:
    source = str(candidate.get("source", "")).lower()
    if source:
        return source
    candidate_id = str(candidate.get("id", "")).lower()
    if candidate_id.startswith("gh_"):
        return "github"
    if candidate_id.startswith("blog_"):
        return "official_blogs"
    if candidate_id.startswith("perk_"):
        return "perks"
    return "arxiv"


def _date_value(candidate: Dict[str, Any], source: str) -> Optional[str]:
    repo = candidate.get("repo_metadata") or {}
    perk = candidate.get("perk_metadata") or {}
    blog = candidate.get("blog_metadata") or {}
    if source in {"github", "github_api", "github_search_api", "curated_trending"}:
        return repo.get("pushed_at") or repo.get("updated_at") or candidate.get("updated_at")
    if source in {"perks", "verified_perks"}:
        return candidate.get("last_verified_date") or perk.get("last_verified_date")
    return (
        candidate.get("published_at")
        or candidate.get("published_date")
        or candidate.get("date")
        or blog.get("published_date")
    )


def _momentum_evidence(candidate: Dict[str, Any], source: str, age_days: int) -> List[str]:
    evidence: List[str] = []
    repo = candidate.get("repo_metadata") or {}
    upvotes = int(candidate.get("upvotes") or 0)
    stars = int(repo.get("stars") or candidate.get("stars") or 0)
    forks = int(repo.get("forks") or candidate.get("forks") or 0)
    impact = float(candidate.get("impact_score") or 0)
    multiplier = float(candidate.get("analytics_multiplier") or 1.0)

    if upvotes >= 25:
        evidence.append(f"{upvotes} community upvotes")
    if stars >= 1000:
        evidence.append(f"{stars:,} GitHub stars")
    if forks >= 100:
        evidence.append(f"{forks:,} GitHub forks")
    if impact >= 100:
        evidence.append(f"impact score {impact:.0f}")
    if multiplier >= 1.2:
        evidence.append(f"audience multiplier {multiplier:.2f}x")
    if source in {"github", "github_api", "github_search_api", "curated_trending"} and age_days <= 14:
        evidence.append("recent repository activity")
    return evidence


def evaluate_topic_gate(
    candidate: Dict[str, Any],
    reference_date: Optional[dt.date] = None,
    mode: str = "latest_or_viral",
) -> Dict[str, Any]:
    """Return an auditable decision for latest-or-viral production eligibility."""
    source = _source(candidate)
    date_value = _date_value(candidate, source)
    age_days = calculate_content_age_days(date_value, reference_date=reference_date) if date_value else None
    latest_window = LATEST_WINDOWS.get(source, 7)

    result: Dict[str, Any] = {
        "eligible": False,
        "classification": "rejected",
        "source": source,
        "date_value": date_value,
        "age_days": age_days,
        "latest_window_days": latest_window,
        "viral_window_days": VIRAL_WINDOW_DAYS,
        "evidence": [],
        "reason": "missing dated evidence",
    }
    if mode in {"legacy", "recent"}:
        result.update(eligible=True, classification="recent", reason=f"topic mode: {mode}")
        return result
    if age_days is None:
        return result
    if age_days <= latest_window:
        result.update(
            eligible=True,
            classification="latest",
            evidence=[f"published/updated {age_days} day(s) ago"],
            reason=f"within {latest_window}-day latest window",
        )
        return result
    if age_days > VIRAL_WINDOW_DAYS:
        result["reason"] = f"too old: {age_days} days"
        return result

    evidence = _momentum_evidence(candidate, source, age_days)
    result["evidence"] = evidence
    if len(evidence) >= 2:
        result.update(
            eligible=True,
            classification="viral",
            reason="multiple current momentum signals",
        )
    else:
        result["reason"] = "not latest and insufficient momentum evidence"
    return result


def filter_topic_candidates(
    candidates: List[Dict[str, Any]],
    reference_date: Optional[dt.date] = None,
    mode: str = "latest_or_viral",
) -> List[Dict[str, Any]]:
    """Filter and annotate candidates without silently substituting stale data."""
    accepted: List[Dict[str, Any]] = []
    for candidate in candidates:
        gate = evaluate_topic_gate(candidate, reference_date=reference_date, mode=mode)
        candidate["topic_gate"] = gate
        if gate["eligible"]:
            accepted.append(candidate)
    return accepted
