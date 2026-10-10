"""
Test suite for Autonomous Content Diversification Rotation in DailyShortsDaemon.
Verifies:
1. Strict classification of history records into 3 core channel pillars:
   - (1) Academic mechanism deep dives ('arxiv')
   - (2) Official AI lab releases ('blogs' / 'news')
   - (3) Actionable developer perks & startup credits ('perks')
2. ISO datetime parsing and timestamp extraction with UTC normalization.
3. Alternating least-recently produced category rotation ordering (empty, partial, round-robin).
4. Candidate resolution across pillars with processed paper deduplication.
5. DailyShortsDaemon single-reel and multi-reel rotation selection under source='mixed' and source='auto'.
6. Graceful fallback when the prioritized pillar has zero unprocessed candidates.
7. Explicit source filtering under source='arxiv', source='blogs', and source='perks'.
8. Production history ledger updating with source persistence.
9. Simulation across the 5 daily pre-peak cron upload windows.
"""

import json
import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from pipeline.daily_shorts_daemon import (
    DailyShortsDaemon,
    CONTENT_PILLARS,
    PILLAR_DISPLAY_NAMES,
    parse_iso_datetime,
    classify_history_entry_pillar,
    get_content_rotation_order,
    fetch_candidates_for_pillar,
    evaluate_pedagogical_viability,
    SLOT_SCHEDULE
)
from pipeline.batch_digest import load_history, record_paper_production


@pytest.fixture(autouse=True)
def prevent_analytics_mutation(monkeypatch):
    """Prevents retention analytics from mutating ledger files during tests."""
    monkeypatch.setattr(
        "pipeline.daily_shorts_daemon.retention_analytics.generate_and_save_ledger",
        lambda *args, **kwargs: None
    )


def _mock_generated_script(topic="", category="mechanism_deepdive", arxiv_meta=None, **kwargs):
    """Lightweight test mock for generate_script to bypass LLM generation during tests."""
    clean_id = (arxiv_meta.get("id") if arxiv_meta else "mock_id") or "mock_id"
    return {
        "id": clean_id,
        "title": topic or "Mock Title",
        "category": category,
        "arxiv_id": clean_id,
        "beats": [
            {
                "beat_id": 1,
                "text": f"Why this breakthrough in {topic} changes the fundamental bottleneck of AI.",
                "visual_focus": "Chalkboard opening hook.",
                "highlight_words": {"bottleneck": "#EF4444"},
                "svo_action": {"subject": "AI", "action_verb": "shatters", "direct_object": "limits"}
            },
            {
                "beat_id": 2,
                "text": "Every existing architecture suffered from memory traffic idling compute.",
                "visual_focus": "Memory wall illustration.",
                "highlight_words": {"memory traffic": "#F59E0B"},
                "svo_action": {"subject": "Memory", "action_verb": "chokes", "direct_object": "cores"}
            },
            {
                "beat_id": 3,
                "text": "Here is the core mechanism breaking the limitation.",
                "visual_focus": "Core mechanism blueprint.",
                "highlight_words": {"mechanism": "#38BDF8"},
                "svo_action": {"subject": "System", "action_verb": "streams", "direct_object": "state"}
            },
            {
                "beat_id": 4,
                "text": "By restructuring data movement, the system avoids memory stalling.",
                "visual_focus": "Data flow geometry.",
                "highlight_words": {"data movement": "#A855F7"},
                "svo_action": {"subject": "Pipeline", "action_verb": "fuses", "direct_object": "stages"}
            },
            {
                "beat_id": 5,
                "text": "Empirical tests show a 3x throughput improvement over baselines.",
                "visual_focus": "Performance chart.",
                "highlight_words": {"3x throughput": "#34D399"},
                "svo_action": {"subject": "Benchmarks", "action_verb": "prove", "direct_object": "gains"}
            },
            {
                "beat_id": 6,
                "text": "Follow The Model Verse for daily deep-dives into modern AI mechanisms.",
                "visual_focus": "Outro signature.",
                "highlight_words": {"The Model Verse": "#34D399"},
                "svo_action": {"subject": "Channel", "action_verb": "teaches", "direct_object": "mechanisms"}
            }
        ],
        "editorial_notes": {
            "recommended_hook": "How modern AI shatters previous architectural boundaries",
            "suggested_everyday_analogy": "A precision conveyor belt bypassing warehouse traffic"
        }
    }


# ==============================================================================
# 1. Content Pillar Classification Tests
# ==============================================================================

def test_classify_history_entry_pillar_arxiv():
    """Validates that academic arXiv papers are accurately classified as 'arxiv'."""
    assert classify_history_entry_pillar("2407.08608", {"category": "mechanism_deepdive"}) == "arxiv"
    assert classify_history_entry_pillar("2501.12948", {"category": "benchmark_news"}) == "arxiv"
    assert classify_history_entry_pillar("2412.19437", {"category": "architecture_breakdown"}) == "arxiv"
    assert classify_history_entry_pillar("2610.11287", {"category": "mechanism_deepdive"}) == "arxiv"
    assert classify_history_entry_pillar("hep-th/9912012", {"category": "general"}) == "arxiv"
    # Explicit source
    assert classify_history_entry_pillar("custom_id", {"source": "arxiv"}) == "arxiv"
    assert classify_history_entry_pillar("custom_id", {"source": "hf"}) == "arxiv"


def test_classify_history_entry_pillar_blogs():
    """Validates that official lab announcements are accurately classified as 'blogs'."""
    assert classify_history_entry_pillar("blog_openai_o3_mini", {"category": "tech_news"}) == "blogs"
    assert classify_history_entry_pillar("blog_claude_3_7_sonnet", {"category": "model_showdown"}) == "blogs"
    assert classify_history_entry_pillar("blog_deepmind_gemini_2_5_flash", {"category": "tech_news"}) == "blogs"
    assert classify_history_entry_pillar("news_openai_announcement", {"category": "tech_news"}) == "blogs"
    # Category based
    assert classify_history_entry_pillar("random_drop_id", {"category": "official_blogs"}) == "blogs"
    assert classify_history_entry_pillar("random_drop_id", {"category": "tech_news"}) == "blogs"
    # Explicit source
    assert classify_history_entry_pillar("custom_lab", {"source": "official_blogs"}) == "blogs"
    assert classify_history_entry_pillar("custom_lab", {"source": "blogs"}) == "blogs"


def test_classify_history_entry_pillar_perks():
    """Validates that verified developer tech perks are accurately classified as 'perks'."""
    assert classify_history_entry_pillar("perk_anthropic_startup_program", {"category": "developer_perks"}) == "perks"
    assert classify_history_entry_pillar("perk_microsoft_founders_hub", {"category": "developer_perks"}) == "perks"
    assert classify_history_entry_pillar("perk_google_for_startups", {"category": "developer_perks"}) == "perks"
    # Category based
    assert classify_history_entry_pillar("credits_deal", {"category": "developer_perks"}) == "perks"
    assert classify_history_entry_pillar("credits_deal", {"category": "startup_credits"}) == "perks"
    # Explicit source
    assert classify_history_entry_pillar("custom_grant", {"source": "verified_perks"}) == "perks"
    assert classify_history_entry_pillar("custom_grant", {"source": "perks"}) == "perks"


# ==============================================================================
# 2. ISO Datetime Parsing Tests
# ==============================================================================

def test_parse_iso_datetime():
    """Validates resilient parsing of UTC ISO timestamps."""
    assert parse_iso_datetime(None) is None
    assert parse_iso_datetime("") is None
    assert parse_iso_datetime("invalid-date") is None

    dt1 = parse_iso_datetime("2026-09-26T11:36:28Z")
    assert dt1 is not None
    assert dt1.tzinfo is not None
    assert dt1.year == 2026 and dt1.month == 9 and dt1.day == 26

    dt2 = parse_iso_datetime("2026-10-10T14:49:20.361440+00:00")
    assert dt2 is not None
    assert dt2.hour == 14 and dt2.minute == 49


# ==============================================================================
# 3. Alternating Category Selection Algorithm Tests
# ==============================================================================

def test_rotation_order_empty_history():
    """Validates default rotation order when history is completely empty."""
    order = get_content_rotation_order({"processed_papers": {}})
    # Starts with canonical cycle: arxiv -> blogs -> perks
    assert order == ["arxiv", "blogs", "perks"]


def test_rotation_order_when_only_arxiv_in_history():
    """
    Validates that when history only contains arXiv papers (the current real-world repository state),
    the least-recently produced categories are prioritized: blogs first, then perks, then arxiv.
    """
    history = {
        "processed_papers": {
            "2610.11287": {
                "title": "REMORY: Learning Residual Memory for Context Compaction",
                "category": "mechanism_deepdive",
                "produced_at": "2026-10-10T14:49:20.361440+00:00",
                "status": "completed"
            },
            "2606.03335": {
                "title": "A GPU-Parallel Framework for RL",
                "category": "benchmark_news",
                "produced_at": "2026-10-10T11:30:37.187740+00:00",
                "status": "completed"
            }
        }
    }
    order = get_content_rotation_order(history)
    # Since arXiv was last produced, next in cycle must be blogs, followed by perks, then arxiv
    assert order == ["blogs", "perks", "arxiv"]


def test_rotation_order_after_blogs_produced():
    """Validates that after a blog drop is produced, perks is prioritized next."""
    history = {
        "processed_papers": {
            "2610.11287": {
                "title": "Arxiv Paper",
                "category": "mechanism_deepdive",
                "produced_at": "2026-10-10T14:49:20+00:00",
                "status": "completed"
            },
            "blog_openai_o3_mini": {
                "title": "OpenAI o3-mini",
                "category": "tech_news",
                "source": "blogs",
                "produced_at": "2026-10-10T16:00:00+00:00",
                "status": "completed"
            }
        }
    }
    order = get_content_rotation_order(history)
    # Perks has never been produced (timestamp -inf), so it has highest priority
    assert order[0] == "perks"
    assert order[1] == "arxiv"
    assert order[2] == "blogs"


def test_rotation_order_after_perks_produced():
    """Validates that after a perk is produced, arxiv rotates back to the top priority."""
    history = {
        "processed_papers": {
            "2610.11287": {
                "title": "Arxiv Paper",
                "category": "mechanism_deepdive",
                "produced_at": "2026-10-10T14:00:00+00:00",
                "status": "completed"
            },
            "blog_openai_o3_mini": {
                "title": "OpenAI o3-mini",
                "category": "tech_news",
                "source": "blogs",
                "produced_at": "2026-10-10T15:00:00+00:00",
                "status": "completed"
            },
            "perk_anthropic_startup_program": {
                "title": "Anthropic Startup Program",
                "category": "developer_perks",
                "source": "perks",
                "produced_at": "2026-10-10T16:00:00+00:00",
                "status": "completed"
            }
        }
    }
    order = get_content_rotation_order(history)
    # Arxiv was produced at 14:00 (least recent), so it rotates back to #1
    assert order == ["arxiv", "blogs", "perks"]


def test_rotation_order_continuous_round_robin_simulation():
    """
    Simulates 9 consecutive daily cycles to prove that get_content_rotation_order
    generates a perfect alternating sequence:
    arxiv -> blogs -> perks -> arxiv -> blogs -> perks -> arxiv -> blogs -> perks.
    """
    sim_history = {"processed_papers": {}}
    base_time = datetime.datetime(2026, 10, 10, 10, 0, 0, tzinfo=datetime.timezone.utc)

    expected_sequence = ["arxiv", "blogs", "perks", "arxiv", "blogs", "perks", "arxiv", "blogs", "perks"]
    actual_sequence = []

    for i in range(len(expected_sequence)):
        order = get_content_rotation_order(sim_history)
        chosen = order[0]
        actual_sequence.append(chosen)

        # Simulate production of this category
        entry_time = (base_time + datetime.timedelta(hours=i)).isoformat()
        sim_history["processed_papers"][f"{chosen}_item_{i}"] = {
            "title": f"Produced {chosen} {i}",
            "category": "developer_perks" if chosen == "perks" else ("tech_news" if chosen == "blogs" else "mechanism_deepdive"),
            "source": chosen,
            "produced_at": entry_time,
            "status": "completed"
        }

    assert actual_sequence == expected_sequence


# ==============================================================================
# 4. Candidate Resolution Tests
# ==============================================================================

def test_fetch_candidates_for_pillar_deduplication():
    """Validates that candidate resolution excludes already processed IDs."""
    test_history = {
        "processed_papers": {
            "blog_openai_o3_mini": {
                "title": "OpenAI o3-mini",
                "category": "tech_news",
                "status": "completed"
            },
            "perk_anthropic_startup_program": {
                "title": "Anthropic Program",
                "category": "developer_perks",
                "status": "completed"
            }
        }
    }

    blog_candidates = fetch_candidates_for_pillar("blogs", limit=5, history=test_history)
    perk_candidates = fetch_candidates_for_pillar("perks", limit=5, history=test_history)

    assert all(b["id"] != "blog_openai_o3_mini" for b in blog_candidates)
    assert all(p["id"] != "perk_anthropic_startup_program" for p in perk_candidates)
    assert len(blog_candidates) > 0
    assert len(perk_candidates) > 0


# ==============================================================================
# 5. DailyShortsDaemon Rotation Integration Tests
# ==============================================================================

def test_daemon_run_daily_cycle_mixed_count_1(monkeypatch):
    """
    Validates that run_daily_cycle under source='mixed' automatically selects
    the least-recently produced pillar (blogs) when history only contains arXiv papers.
    """
    monkeypatch.setattr("pipeline.script_generator.generate_script", _mock_generated_script)
    monkeypatch.setenv("GEMINI_API_KEY", "")

    daemon = DailyShortsDaemon()
    res = daemon.run_daily_cycle(
        count=1,
        dry_run=True,
        source="mixed"
    )

    assert len(res) == 1
    report = res[0]
    paper = report["paper"]
    assert report["source"] == "blogs"
    assert paper["id"].startswith("blog_")
    assert paper["category"] in ("tech_news", "model_showdown")
    assert report["status"] == "dry_run_success"


def test_daemon_run_daily_cycle_mixed_count_3_balances_all_three_pillars(monkeypatch):
    """
    Validates that a multi-reel batch (count=3) under source='mixed'
    allocates one reel to each of the 3 content pillars in alternating succession.
    """
    monkeypatch.setattr("pipeline.script_generator.generate_script", _mock_generated_script)
    monkeypatch.setenv("GEMINI_API_KEY", "")

    daemon = DailyShortsDaemon()
    res = daemon.run_daily_cycle(
        count=3,
        dry_run=True,
        source="mixed"
    )

    assert len(res) == 3
    sources = [r["source"] for r in res]
    # Under current history where arXiv is latest: Reel 1 -> blogs, Reel 2 -> perks, Reel 3 -> arxiv
    assert sources == ["blogs", "perks", "arxiv"]


def test_daemon_run_daily_cycle_auto_alias(monkeypatch):
    """Validates that source='auto' behaves identically to source='mixed'."""
    monkeypatch.setattr("pipeline.script_generator.generate_script", _mock_generated_script)
    monkeypatch.setenv("GEMINI_API_KEY", "")

    daemon = DailyShortsDaemon()
    res = daemon.run_daily_cycle(
        count=1,
        dry_run=True,
        source="auto"
    )

    assert len(res) == 1
    assert res[0]["source"] == "blogs"


def test_daemon_run_daily_cycle_fallback_when_pillar_exhausted(monkeypatch):
    """
    Validates that if the prioritized pillar has 0 unprocessed candidates,
    the daemon gracefully falls back to the next least-recently produced pillar.
    """
    monkeypatch.setattr("pipeline.script_generator.generate_script", _mock_generated_script)
    monkeypatch.setenv("GEMINI_API_KEY", "")

    # Mock fetch_candidates_for_pillar so 'blogs' has 0 candidates
    real_fetch = fetch_candidates_for_pillar

    def mock_fetch(pillar, limit=10, history=None):
        if pillar == "blogs":
            return []
        return real_fetch(pillar, limit=limit, history=history)

    monkeypatch.setattr("pipeline.daily_shorts_daemon.fetch_candidates_for_pillar", mock_fetch)

    daemon = DailyShortsDaemon()
    res = daemon.run_daily_cycle(
        count=1,
        dry_run=True,
        source="mixed"
    )

    assert len(res) == 1
    # Fallback from blogs to perks!
    assert res[0]["source"] == "perks"
    assert res[0]["paper"]["id"].startswith("perk_")


def test_daemon_run_daily_cycle_explicit_sources(monkeypatch):
    """Validates that explicit source arguments override rotation and restrict discovery."""
    monkeypatch.setattr("pipeline.script_generator.generate_script", _mock_generated_script)
    monkeypatch.setenv("GEMINI_API_KEY", "")

    daemon = DailyShortsDaemon()

    # Explicit blogs
    res_b = daemon.run_daily_cycle(count=1, dry_run=True, source="blogs")
    assert len(res_b) == 1
    assert res_b[0]["source"] == "blogs"

    # Explicit perks
    res_p = daemon.run_daily_cycle(count=1, dry_run=True, source="perks")
    assert len(res_p) == 1
    assert res_p[0]["source"] == "perks"

    # Explicit arxiv
    res_a = daemon.run_daily_cycle(count=1, dry_run=True, source="arxiv")
    assert len(res_a) == 1
    assert res_a[0]["source"] == "arxiv"


def test_record_paper_production_persists_source(tmp_path, monkeypatch):
    """Validates that record_paper_production records the source tag into digest_history.json."""
    temp_hist = tmp_path / "digest_history.json"
    temp_hist.write_text('{"processed_papers": {}}', encoding="utf-8")
    monkeypatch.setattr("pipeline.batch_digest.HISTORY_FILE", temp_hist)

    record_paper_production(
        arxiv_id="blog_openai_o3_mini",
        title="OpenAI o3-mini Reasoning Model",
        category="tech_news",
        video_path="/tmp/test_blog.mp4",
        source="blogs"
    )

    hist = load_history()
    assert "blog_openai_o3_mini" in hist["processed_papers"]
    item = hist["processed_papers"]["blog_openai_o3_mini"]
    assert item["source"] == "blogs"
    assert item["category"] == "tech_news"
    assert item["status"] == "completed"


def test_slot_schedule_has_5_daily_upload_windows():
    """Validates that SLOT_SCHEDULE configures the 5 daily upload windows matching the GitHub Actions cron."""
    assert 1 in SLOT_SCHEDULE
    assert 5 in SLOT_SCHEDULE
    assert 9 in SLOT_SCHEDULE
    assert 12 in SLOT_SCHEDULE
    assert 16 in SLOT_SCHEDULE
    assert len(SLOT_SCHEDULE) == 5
