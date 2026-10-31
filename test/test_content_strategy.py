import datetime as dt

from pipeline.content_strategy import (
    AUDIENCE_PROFILE,
    evaluate_candidate,
    rank_candidates,
    strategy_report,
)


REFERENCE_DATE = dt.date(2026, 10, 29)


def _candidate(**overrides):
    candidate = {
        "id": "gh_example_agent",
        "source": "github_search_api",
        "title": "Open source coding agent security audit",
        "description": "Audit a repository for security findings before merge.",
        "repo_metadata": {
            "url": "https://github.com/example/agent",
            "stars": 12000,
            "forks": 500,
            "pushed_at": "2026-10-28T00:00:00Z",
        },
        "code_snippet": {"lines": ["audit(repository)"]},
    }
    candidate.update(overrides)
    return candidate


def test_global_builder_profile_is_stable():
    assert AUDIENCE_PROFILE == {
        "id": "global_ai_builder",
        "language": "en",
        "segments": ["developer", "student", "indie_hacker", "technical_founder"],
        "priority": "qualified_growth",
    }


def test_candidate_gets_viewer_facing_brief_and_score():
    decision = evaluate_candidate(_candidate(), reference_date=REFERENCE_DATE)

    assert decision.eligible is True
    assert 0 <= decision.score <= 100
    assert decision.primary_segment == "developer"
    assert decision.viewer_problem
    assert decision.promised_payoff
    assert decision.proof_asset == "source code or execution kernel"
    assert decision.recommended_format == "practical_demo"
    assert "matches the global builder audience" in decision.reasons


def test_missing_date_and_source_are_hard_rejections():
    decision = evaluate_candidate(
        {"id": "paper_without_provenance", "title": "A New Architecture", "abstract": "A mechanism."},
        reference_date=REFERENCE_DATE,
    )

    assert decision.eligible is False
    assert "missing source URL" in decision.hard_rejections
    assert "missing dated evidence" in decision.hard_rejections


def test_duplicate_is_rejected_inside_cooldown():
    history = {
        "processed_papers": {
            "old_id": {
                "title": "Open source coding agent security audit",
                "produced_at": "2026-10-20T00:00:00Z",
            }
        }
    }
    decision = evaluate_candidate(_candidate(id="different_id"), history=history, reference_date=REFERENCE_DATE)

    assert decision.eligible is False
    assert "duplicate within cooldown window" in decision.hard_rejections


def test_stale_candidate_is_rejected_even_with_strong_momentum():
    stale = _candidate(repo_metadata={
        "url": "https://github.com/example/agent",
        "stars": 500000,
        "forks": 10000,
        "pushed_at": "2026-09-01T00:00:00Z",
    })
    decision = evaluate_candidate(stale, reference_date=REFERENCE_DATE)

    assert decision.eligible is False
    assert any("stale evidence" in reason for reason in decision.hard_rejections)


def test_rank_candidates_attaches_strategy_and_preserves_source_facts():
    candidates = [
        _candidate(id="gh_demo", title="Build a coding agent workflow", source="github_search_api"),
        _candidate(
            id="blog_release",
            source="official_blogs",
            title="New local AI model release",
            description="A local model for laptop inference.",
            canonical_url="https://example.com/release",
            published_at="2026-10-29T00:00:00Z",
            repo_metadata=None,
            code_snippet=None,
        ),
    ]

    selected = rank_candidates(candidates, count=2, reference_date=REFERENCE_DATE)

    assert len(selected) == 2
    assert {item["content_strategy"]["audience_profile"] for item in selected} == {"global_ai_builder"}
    assert all(item["content_strategy"]["score"] >= 55 for item in selected)
    assert all(item["editorial_notes"]["recommended_hook"] for item in selected)
    assert all(item["id"] in {"gh_demo", "blog_release"} for item in selected)


def test_strategy_report_includes_rejections_for_dry_run():
    report = strategy_report(
        [_candidate(), {"id": "missing", "title": "Unverified architecture"}],
        reference_date=REFERENCE_DATE,
    )

    assert len(report) == 2
    rejected = next(row for row in report if row["id"] == "missing")
    assert rejected["eligible"] is False
    assert rejected["rejections"]


def test_rank_candidates_exposes_experiment_format_mix_metadata():
    selected = rank_candidates(
        [_candidate(id="gh_demo_a"), _candidate(id="gh_demo_b", title="Build a local inference tool")],
        count=2,
        history={"processed_papers": {}},
        reference_date=REFERENCE_DATE,
    )
    assert len(selected) == 2
    assert all("format_target" in item["content_strategy"] for item in selected)
