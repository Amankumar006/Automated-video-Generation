"""
Test suite for Category Diversity Balancing, Multi-Category Rotation, and Tech Perks Integration.
Verifies:
1. Category diversity balancing in evaluate_pedagogical_viability prevents category monopolization.
2. CATEGORY_SCENE_MAP in run_pipeline cleanly registers developer_perks and tech_news.
3. DailyShortsDaemon candidate discovery accurately ingests perks under source='perks' and source='mixed'.
4. Direct perk targeting via target_perk produces valid candidate specifications.
5. Direct arXiv targeting classifies papers dynamically into diverse categories instead of hardcoding.
6. History ledger recording accurately captures diverse categories and perk IDs.
"""

import pytest
from pipeline.daily_shorts_daemon import (
    DailyShortsDaemon,
    evaluate_pedagogical_viability,
    SLOT_SCHEDULE
)
from pipeline.run_pipeline import CATEGORY_SCENE_MAP
from pipeline.tech_perks_fetcher import tech_perks_fetcher
from pipeline.batch_digest import load_history, record_paper_production


@pytest.fixture(autouse=True)
def prevent_analytics_mutation(monkeypatch):
    monkeypatch.setattr(
        "pipeline.daily_shorts_daemon.retention_analytics.generate_and_save_ledger",
        lambda *args, **kwargs: None
    )


def test_category_scene_map_contains_expanded_categories():
    """Validates that CATEGORY_SCENE_MAP includes developer_perks and tech_news."""
    assert "developer_perks" in CATEGORY_SCENE_MAP
    assert "tech_news" in CATEGORY_SCENE_MAP
    assert "architecture_breakdown" in CATEGORY_SCENE_MAP
    assert "mechanism_deepdive" in CATEGORY_SCENE_MAP
    assert "model_showdown" in CATEGORY_SCENE_MAP
    assert "benchmark_news" in CATEGORY_SCENE_MAP


def test_evaluate_pedagogical_viability_balances_categories(monkeypatch):
    """
    Validates that when count > 1, evaluate_pedagogical_viability avoids
    monopolizing the quota with a single category if diverse high-velocity candidates exist.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "")

    candidates = [
        {
            "id": "cand_hw_1",
            "title": "KV Cache Quantization Part 1",
            "taxonomy": "hardware_efficiency",
            "recommended_category": "mechanism_deepdive",
            "analytics_multiplier": 1.19,
            "raw_impact_score": 60.0,
            "impact_score": 71.4,
            "abstract": "..."
        },
        {
            "id": "cand_hw_2",
            "title": "KV Cache Compression Part 2",
            "taxonomy": "hardware_efficiency",
            "recommended_category": "mechanism_deepdive",
            "analytics_multiplier": 1.19,
            "raw_impact_score": 58.0,
            "impact_score": 69.0,
            "abstract": "..."
        },
        {
            "id": "cand_perk",
            "title": "Anthropic Claude Team Program",
            "taxonomy": "developer_perks",
            "recommended_category": "developer_perks",
            "analytics_multiplier": 1.25,
            "raw_impact_score": 50.0,
            "impact_score": 62.5,
            "abstract": "..."
        },
        {
            "id": "cand_showdown",
            "title": "Claude 3.5 Sonnet vs GPT-4o",
            "taxonomy": "model_showdown",
            "recommended_category": "model_showdown",
            "analytics_multiplier": 1.10,
            "raw_impact_score": 52.0,
            "impact_score": 57.2,
            "abstract": "..."
        }
    ]

    # With count=2, it should pick top candidate cand_hw_1, then diversify to cand_perk instead of cand_hw_2
    selected = evaluate_pedagogical_viability(candidates, count=2)
    selected_ids = [c["id"] for c in selected]

    assert "cand_hw_1" in selected_ids
    assert "cand_perk" in selected_ids
    assert "cand_hw_2" not in selected_ids

    selected_categories = {c["recommended_category"] for c in selected}
    assert len(selected_categories) == 2
    assert "mechanism_deepdive" in selected_categories
    assert "developer_perks" in selected_categories


def _mock_spec(topic, category=None, arxiv_meta=None):
    return {
        "id": "mock_spec_123",
        "title": topic,
        "category": category or "developer_perks",
        "beats": [
            {
                "beat_id": 1,
                "text": "Every engineering team burns compute before discovering verified developer perks.",
                "duration": 5.0,
                "highlight_words": {"compute": "#34D399"}
            }
        ]
    }


def test_daemon_direct_perk_targeting(monkeypatch):
    """Validates that DailyShortsDaemon resolves direct target_perk into candidate spec."""
    monkeypatch.setattr("pipeline.script_generator.generate_script", _mock_spec)
    daemon = DailyShortsDaemon()
    res = daemon.run_daily_cycle(
        count=1,
        dry_run=True,
        target_perk="anthropic_startup_program"
    )

    assert len(res) == 1
    report = res[0]
    cand = report["paper"]
    assert cand["id"] == "perk_anthropic_startup_program"
    assert cand["recommended_category"] == "developer_perks"
    assert "Anthropic" in cand["title"]
    assert report["status"] == "dry_run_success"


def test_daemon_direct_perk_query_resolution(monkeypatch):
    """Validates that fuzzy perk queries (e.g. 'microsoft') resolve through verify_perk_claim."""
    monkeypatch.setattr("pipeline.script_generator.generate_script", _mock_spec)
    daemon = DailyShortsDaemon()
    res = daemon.run_daily_cycle(
        count=1,
        dry_run=True,
        target_perk="microsoft founders hub"
    )

    assert len(res) == 1
    cand = res[0]["paper"]
    assert cand["id"] == "perk_microsoft_founders_hub"
    assert cand["recommended_category"] == "developer_perks"


def test_daemon_direct_arxiv_dynamic_classification(monkeypatch):
    """Validates that direct arXiv targets are dynamically classified rather than hardcoded to mechanism_deepdive."""
    monkeypatch.setattr("pipeline.script_generator.generate_script", _mock_spec)
    daemon = DailyShortsDaemon()

    # Mock fetch_arxiv_paper
    fake_paper = {
        "arxiv_id": "2412.19437",
        "title": "DeepSeek-V3 Technical Report: Architecture & Mixture of Experts",
        "abstract": "A sparse mixture of experts foundation model with multi-head latent attention.",
        "authors": ["DeepSeek AI"]
    }
    monkeypatch.setattr("pipeline.arxiv_fetcher.fetch_arxiv_paper", lambda x: fake_paper)

    res = daemon.run_daily_cycle(
        count=1,
        dry_run=True,
        target_arxiv="2412.19437"
    )

    assert len(res) == 1
    cand = res[0]["paper"]
    assert cand["id"] == "2412.19437"
    # Should be classified as architecture_breakdown due to MoE & transformer keywords
    assert cand["recommended_category"] == "architecture_breakdown"


def test_daemon_mixed_source_candidate_diversity():
    """Validates that candidate scanning under source='mixed' includes verified developer perks."""
    from pipeline.tech_perks_fetcher import get_verified_perks_digest
    perks = get_verified_perks_digest(limit=5)

    assert len(perks) >= 5
    perk_ids = [p["id"] for p in perks]
    assert any("anthropic" in pid for pid in perk_ids)
    assert any("microsoft" in pid for pid in perk_ids)
    assert any("google" in pid for pid in perk_ids)


def test_record_perk_production_history(tmp_path, monkeypatch):
    """Validates that completed perk productions are saved in digest_history."""
    temp_hist = tmp_path / "digest_history.json"
    temp_hist.write_text('{"processed_papers": {}}', encoding="utf-8")
    monkeypatch.setattr("pipeline.batch_digest.HISTORY_FILE", temp_hist)

    test_id = "perk_test_program_verification"
    test_title = "Test AI Developer Grant Program"
    test_cat = "developer_perks"
    test_vid = "/tmp/test_perk_video.mp4"

    record_paper_production(test_id, test_title, test_cat, test_vid)
    history = load_history()

    assert test_id in history["processed_papers"]
    saved = history["processed_papers"][test_id]
    assert saved["title"] == test_title
    assert saved["category"] == test_cat
    assert saved["status"] == "completed"


def test_daemon_preferred_taxonomy_targeting(monkeypatch):
    """Validates that DailyShortsDaemon correctly applies preferred_taxonomy='developer_perks'."""
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setattr("pipeline.script_generator.generate_script", _mock_spec)
    daemon = DailyShortsDaemon()
    candidates = [
        {
            "id": "cand_hw",
            "title": "Hardware paper",
            "taxonomy": "hardware_efficiency",
            "recommended_category": "mechanism_deepdive",
            "analytics_multiplier": 1.19,
            "impact_score": 90.0,
            "abstract": "..."
        },
        {
            "id": "cand_perk",
            "title": "Anthropic Claude Team Program",
            "taxonomy": "developer_perks",
            "recommended_category": "developer_perks",
            "analytics_multiplier": 1.25,
            "impact_score": 85.0,
            "abstract": "..."
        }
    ]
    # Under preferred_taxonomy="developer_perks", cand_perk must be chosen over cand_hw
    selected = evaluate_pedagogical_viability(candidates, count=1, preferred_taxonomy="developer_perks")
    assert len(selected) == 1
    assert selected[0]["id"] == "cand_perk"
    assert selected[0]["taxonomy"] == "developer_perks"


def test_run_pipeline_bypasses_arxiv_figure_extraction_for_perks(monkeypatch):
    """Validates that run_pipeline bypasses arXiv figure extraction when processing perk IDs."""
    import sys
    from pipeline.run_pipeline import main as run_pipeline_main
    from unittest.mock import MagicMock

    mock_spec = {
        "id": "test_perk_spec",
        "title": "Anthropic Claude Team Program",
        "category": "developer_perks",
        "arxiv_id": "perk_anthropic_startup_program",
        "beats": [
            {
                "beat_id": 1,
                "text": "Every founder burns cloud runway before discovering verified perks.",
                "duration": 5.0
            }
        ]
    }

    mock_audio = {
        "master_audio": "/tmp/mock_audio.wav",
        "timing_data": [{"beat_id": 1, "duration": 5.0, "slot_duration": 5.0, "start": 0.0, "end": 5.0, "word_timings": []}]
    }

    figure_extraction_called = False
    def mock_extract_figures(*args, **kwargs):
        nonlocal figure_extraction_called
        figure_extraction_called = True
        return []

    monkeypatch.setattr("sys.argv", ["run_pipeline.py", "--perk", "anthropic_startup_program", "--dry-run"])
    monkeypatch.setattr("pipeline.run_pipeline.generate_script", lambda **kwargs: mock_spec)
    monkeypatch.setattr("pipeline.run_pipeline.synthesize_audio_for_spec", lambda *args, **kwargs: mock_audio)
    monkeypatch.setattr("pipeline.arxiv_vector_extractor.extract_paper_figures", mock_extract_figures)
    monkeypatch.setattr("pipeline.run_pipeline.render_scene", lambda *args, **kwargs: None)

    try:
        run_pipeline_main()
    except SystemExit:
        pass

    assert figure_extraction_called is False, "extract_paper_figures should NOT be called for perk IDs"


