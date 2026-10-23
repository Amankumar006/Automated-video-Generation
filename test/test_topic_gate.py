import datetime as dt

from pipeline.topic_gate import evaluate_topic_gate, filter_topic_candidates


REF_DATE = dt.date(2026, 10, 24)


def test_latest_candidate_passes_with_dated_evidence():
    candidate = {
        "id": "2609.99999",
        "source": "arxiv",
        "published_at": "2026-10-22",
        "title": "Fresh mechanism",
    }
    decision = evaluate_topic_gate(candidate, reference_date=REF_DATE)
    assert decision["eligible"] is True
    assert decision["classification"] == "latest"


def test_older_candidate_needs_multiple_momentum_signals():
    candidate = {
        "id": "gh_org_project",
        "source": "github_search_api",
        "repo_metadata": {
            "pushed_at": "2026-10-10",
            "stars": 12000,
            "forks": 450,
        },
    }
    decision = evaluate_topic_gate(candidate, reference_date=REF_DATE)
    assert decision["eligible"] is True
    assert decision["classification"] == "viral"


def test_missing_dated_evidence_is_rejected():
    candidate = {
        "id": "gh_curated_fallback",
        "source": "curated_trending",
        "repo_metadata": {"stars": 100000},
    }
    decision = evaluate_topic_gate(candidate, reference_date=REF_DATE)
    assert decision["eligible"] is False
    assert decision["reason"] == "missing dated evidence"


def test_filter_does_not_substitute_rejected_topics():
    candidates = [
        {"id": "stale", "source": "arxiv", "published_at": "2026-08-01"},
        {"id": "fresh", "source": "arxiv", "published_at": "2026-10-23"},
    ]
    accepted = filter_topic_candidates(candidates, reference_date=REF_DATE)
    assert [item["id"] for item in accepted] == ["fresh"]
