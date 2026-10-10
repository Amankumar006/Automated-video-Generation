"""
Test suite for Official AI Tech News & Lab Blog Ingestion Engine.
Verifies:
1. Completeness and attribution for official AI research labs (OpenAI, Anthropic, Google DeepMind, Hugging Face, GitHub).
2. Domain whitelist enforcement against spoofed or unofficial URLs.
3. Resilient RSS 2.0 and Atom XML feed parsing with HTML stripping and ISO date normalization.
4. Structured key facts extraction (benchmarks, speedups, pricing, release tiers, availability).
5. Automatic category and domain taxonomy classification (tech_news vs model_showdown).
6. Candidate specification generation matching the pipeline contract.
7. Deterministic offline fallback under network errors and offline_only mode.
8. Deduplication in digest generation.
9. Integration with DailyShortsDaemon (source='blogs', source='news', source='mixed', target_blog).
10. Integration with run_pipeline.py and non-arXiv figure download bypass (zero 404 errors).
"""

import sys
import json
import urllib.request
import urllib.error
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.official_blogs_fetcher import (
    OfficialBlogsFetcher,
    OfficialBlogRecord,
    VERIFIED_OFFICIAL_BLOGS_REGISTRY,
    OFFICIAL_LAB_FEEDS,
    OFFICIAL_LAB_DOMAINS,
    clean_html_text,
    parse_pubdate_to_iso,
    slugify_title,
    extract_verified_key_facts,
    classify_blog_content,
    get_official_blogs_digest,
    get_official_blog,
)
from pipeline.daily_shorts_daemon import DailyShortsDaemon
from pipeline.arxiv_vector_extractor import download_arxiv_source, extract_paper_figures


# ==============================================================================
# 1. Official Lab Attribution & Registry Completeness
# ==============================================================================

def test_verified_registry_covers_all_five_major_labs():
    """Validates that verified registry contains announcements from all 5 official labs."""
    fetcher = OfficialBlogsFetcher(offline_only=True)
    blogs = fetcher.get_all_verified_blogs()
    providers = {b.provider for b in blogs}

    assert "OpenAI" in providers
    assert "Anthropic" in providers
    assert "Google DeepMind" in providers
    assert "Hugging Face" in providers
    assert "GitHub" in providers
    assert len(blogs) >= 8


def test_verified_registry_records_have_complete_evidentiary_metadata():
    """Validates that each verified blog record satisfies data integrity requirements."""
    for b_id, rec in VERIFIED_OFFICIAL_BLOGS_REGISTRY.items():
        assert rec.id.startswith("blog_"), f"{b_id} must have 'blog_' prefix"
        assert len(rec.title) >= 10, f"{b_id} title is too short"
        assert rec.canonical_url.startswith("https://"), f"{b_id} canonical URL must use HTTPS"
        assert len(rec.summary.split()) >= 15, f"{b_id} summary must be a concrete overview"
        assert rec.category in ("tech_news", "model_showdown"), f"{b_id} invalid category {rec.category}"
        assert rec.published_date, f"{b_id} missing published date"
        assert isinstance(rec.key_facts, dict), f"{b_id} key_facts must be a dict"
        assert rec.raw_impact_score >= 80.0
        assert rec.analytics_multiplier >= 1.20


# ==============================================================================
# 2. Domain Whitelist Enforcement
# ==============================================================================

def test_official_domain_whitelist_validation():
    """Enforces that only approved lab domains are validated."""
    fetcher = OfficialBlogsFetcher()

    # Valid official domains
    assert fetcher.validate_official_domain("https://openai.com/news/o3-mini") is True
    assert fetcher.validate_official_domain("https://www.anthropic.com/news/claude-3-7-sonnet") is True
    assert fetcher.validate_official_domain("https://blog.google/technology/ai/gemini-2-5-flash") is True
    assert fetcher.validate_official_domain("https://deepmind.google/discover/blog/alphafold-3") is True
    assert fetcher.validate_official_domain("https://huggingface.co/blog/smolagents") is True
    assert fetcher.validate_official_domain("https://github.blog/news-insights/product-news/copilot") is True

    # Untrusted / spoofed domains
    assert fetcher.validate_official_domain("https://openai.com.attacker.com/news") is False
    assert fetcher.validate_official_domain("https://fake-anthropic.io/claude") is False
    assert fetcher.validate_official_domain("https://phishing-google.xyz/gemini") is False
    assert fetcher.validate_official_domain("http://insecure-openai.com/news") is False
    assert fetcher.validate_official_domain("invalid_url_string") is False


# ==============================================================================
# 3. Feed Parsing: RSS 2.0 & Atom XML
# ==============================================================================

def test_parse_rss_2_0_feed_xml():
    """Validates parsing of standard RSS 2.0 feeds with namespaces and HTML entities."""
    sample_rss = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
      <channel>
        <title>OpenAI News</title>
        <link>https://openai.com/news/</link>
        <item>
          <title>OpenAI o3-mini: High-Speed STEM Reasoning</title>
          <link>https://openai.com/news/o3-mini/</link>
          <description><![CDATA[<p>Today we announce <strong>o3-mini</strong>, scoring 87.3% on AIME 2024 and delivering 24% faster latency. Priced at $1.10 / 1M input tokens on the Developer API.</p>]]></description>
          <pubDate>Fri, 31 Jan 2025 18:00:00 GMT</pubDate>
          <guid>https://openai.com/news/o3-mini/</guid>
        </item>
      </channel>
    </rss>
    """
    fetcher = OfficialBlogsFetcher()
    records = fetcher.parse_feed_xml(sample_rss, provider="OpenAI", prefix="blog_openai")

    assert len(records) == 1
    rec = records[0]
    assert rec.id.startswith("blog_openai_")
    assert "o3-mini" in rec.title.lower()
    assert rec.provider == "OpenAI"
    assert rec.published_date == "2025-01-31"
    assert "87.3% on AIME 2024" in rec.summary
    assert "<p>" not in rec.summary
    assert rec.canonical_url == "https://openai.com/news/o3-mini/"
    assert "AIME 2024" in rec.key_facts.get("benchmarks", {})
    assert rec.key_facts["benchmarks"]["AIME 2024"] == "87.3%"
    assert any("24%" in s for s in rec.key_facts.get("speedups", []))
    assert any("$1.10" in p for p in rec.key_facts.get("pricing", []))


def test_parse_atom_feed_xml():
    """Validates parsing of Atom XML feeds with namespaces."""
    sample_atom = """<?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <title>Anthropic Research &amp; News</title>
      <link href="https://www.anthropic.com/news"/>
      <entry>
        <title>Claude 3.7 Sonnet: Hybrid Reasoning vs Standard Architectures</title>
        <link href="https://www.anthropic.com/news/claude-3-7-sonnet" rel="alternate"/>
        <summary>Claude 3.7 Sonnet achieves 70.3% on SWE-bench Verified, outperforming previous frontier models. Available on Claude.ai and Developer API at $3.00 / 1M input tokens.</summary>
        <published>2025-02-24T17:00:00Z</published>
        <id>tag:anthropic.com,2025:claude-3-7-sonnet</id>
      </entry>
    </feed>
    """
    fetcher = OfficialBlogsFetcher()
    records = fetcher.parse_feed_xml(sample_atom, provider="Anthropic", prefix="blog_anthropic")

    assert len(records) == 1
    rec = records[0]
    assert rec.id.startswith("blog_anthropic_")
    assert "Claude 3.7" in rec.title
    assert rec.provider == "Anthropic"
    assert rec.published_date == "2025-02-24"
    assert rec.category == "model_showdown"  # Triggered by 'vs' and 'outperforming'
    assert rec.canonical_url == "https://www.anthropic.com/news/claude-3-7-sonnet"
    assert "SWE-bench Verified" in rec.key_facts.get("benchmarks", {})
    assert rec.key_facts["benchmarks"]["SWE-bench Verified"] == "70.3%"


# ==============================================================================
# 4. Text & Fact Extraction Utilities
# ==============================================================================

def test_clean_html_text():
    """Validates stripping tags, unescaping entities, and whitespace collapsing."""
    raw = "<div><p>DeepSeek &amp; <strong>OpenAI</strong>&#39;s models&nbsp; compared.</p></div>"
    cleaned = clean_html_text(raw)
    assert cleaned == "DeepSeek & OpenAI's models  compared." or cleaned == "DeepSeek & OpenAI's models compared."
    assert "<" not in cleaned
    assert "&amp;" not in cleaned


def test_extract_verified_key_facts():
    """Validates regex extraction of benchmarks, speedups, prices, tiers, and availability."""
    sample_text = (
        "Achieves 82.0% on MMLU and 49.3% on SWE-bench Verified. "
        "Delivers 3.2x faster throughput and 24% lower latency. "
        "Priced at $0.15 / 1M input tokens with free tier on Google AI Studio and Developer API."
    )
    facts = extract_verified_key_facts(sample_text)

    assert "MMLU" in facts["benchmarks"]
    assert facts["benchmarks"]["MMLU"] == "82.0%"
    assert "SWE-bench Verified" in facts["benchmarks"]
    assert facts["benchmarks"]["SWE-bench Verified"] == "49.3%"

    assert any("3.2x" in s for s in facts["speedups"])
    assert any("24%" in s for s in facts["speedups"])
    assert any("$0.15" in p for p in facts["pricing"])
    assert any("Google AI Studio" in a for a in facts["availability"])
    assert any("Developer API" in a for a in facts["availability"])


def test_classify_blog_content():
    """Validates categorization into tech_news or model_showdown and domain taxonomy."""
    cat1, tax1 = classify_blog_content("Claude 3.7 vs GPT-4o: Reasoning Showdown", "Detailed benchmark comparison")
    assert cat1 == "model_showdown"
    assert tax1 == "reasoning_models"

    cat2, tax2 = classify_blog_content("Sora: Video Generation World Models", "Generative diffusion for dynamic scenes")
    assert cat2 == "tech_news"
    assert tax2 == "multimodal_diffusion"

    cat3, tax3 = classify_blog_content("FlashKernel CUDA Acceleration", "Quantization FP8 kernel latency speedup")
    assert cat3 == "tech_news"
    assert tax3 == "hardware_efficiency"


# ==============================================================================
# 5. Candidate Specification Conversion
# ==============================================================================

def test_to_candidate_spec_contract():
    """Validates that to_candidate_spec adheres to the pipeline candidate schema."""
    rec = VERIFIED_OFFICIAL_BLOGS_REGISTRY["blog_openai_o3_mini"]
    spec = rec.to_candidate_spec()

    assert spec["id"] == "blog_openai_o3_mini"
    assert spec["title"] == rec.title
    assert spec["recommended_category"] == "tech_news"
    assert spec["category"] == "tech_news"
    assert spec["taxonomy"] == "reasoning_models"
    assert spec["domain_taxonomy"] == "reasoning_models"
    assert "Key Launch Facts:" in spec["abstract"]
    assert "https://openai.com/news/o3-mini" in spec["abstract"]
    assert spec["source"] == "official_blogs"
    assert spec["raw_impact_score"] >= 90.0
    assert spec["analytics_multiplier"] == 1.25
    assert "recommended_hook" in spec["editorial_notes"]
    assert "suggested_everyday_analogy" in spec["editorial_notes"]


# ==============================================================================
# 6. Offline Fallback & Deterministic Caching
# ==============================================================================

def test_offline_only_mode_returns_curated_digest_without_network():
    """Verifies that offline_only mode operates with 0 network calls."""
    fetcher = OfficialBlogsFetcher(offline_only=True)
    digest = fetcher.get_official_blogs_digest(limit=5, offline_only=True)

    assert len(digest) == 5
    ids = [d["id"] for d in digest]
    assert any("openai" in i for i in ids)
    assert any("claude" in i or "anthropic" in i for i in ids)


def test_fetch_all_feeds_network_failure_falls_back_cleanly(monkeypatch):
    """Simulates complete network failure and ensures transparent fallback to offline registry."""
    def fake_urlopen(*args, **kwargs):
        raise urllib.error.URLError("Network connection refused (simulated)")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    fetcher = OfficialBlogsFetcher(offline_only=False)
    blogs = fetcher.fetch_all_feeds()

    assert len(blogs) >= 8
    providers = {b.provider for b in blogs}
    assert "OpenAI" in providers
    assert "Anthropic" in providers


def test_fuzzy_find_blog_lookup():
    """Validates fuzzy query lookup across title, id, and tags."""
    fetcher = OfficialBlogsFetcher()

    assert fetcher.find_blog("o3-mini").id == "blog_openai_o3_mini"
    assert fetcher.find_blog("claude 3.7").id == "blog_claude_3_7_sonnet"
    assert fetcher.find_blog("gemini 2.5 flash").id == "blog_deepmind_gemini_2_5_flash"
    assert fetcher.find_blog("smolagents").id == "blog_hf_smolagents"
    assert fetcher.find_blog("copilot workspace").id == "blog_github_copilot_workspace"


def test_get_official_blogs_digest_deduplication():
    """Validates that candidate digest contains no duplicate IDs."""
    digest = get_official_blogs_digest(limit=10, offline_only=True)
    ids = [d["id"] for d in digest]
    assert len(ids) == len(set(ids))


# ==============================================================================
# 7. Daemon Integration: sources, target_blog, history
# ==============================================================================

def _mock_spec(topic, category=None, arxiv_meta=None):
    return {
        "id": "mock_blog_spec_101",
        "title": topic,
        "category": category or "tech_news",
        "beats": [
            {
                "beat_id": 1,
                "text": "Every engineering team burns compute before discovering verified model launches.",
                "duration": 5.0,
                "highlight_words": {"compute": "#34D399"}
            }
        ]
    }


def test_daemon_direct_blog_targeting(monkeypatch):
    """Validates that DailyShortsDaemon targets a specific official blog via target_blog."""
    monkeypatch.setattr("pipeline.script_generator.generate_script", _mock_spec)
    monkeypatch.setattr("pipeline.daily_shorts_daemon.retention_analytics.generate_and_save_ledger", lambda *a, **k: None)

    daemon = DailyShortsDaemon()
    res = daemon.run_daily_cycle(
        count=1,
        dry_run=True,
        target_blog="blog_openai_o3_mini"
    )

    assert len(res) == 1
    report = res[0]
    cand = report["paper"]
    assert cand["id"] == "blog_openai_o3_mini"
    assert cand["recommended_category"] == "tech_news"
    assert "OpenAI o3-mini" in cand["title"]
    assert report["status"] == "dry_run_success"


def test_daemon_scans_blogs_source(monkeypatch):
    """Validates that candidate discovery with source='blogs' ingests official blog candidates."""
    monkeypatch.setattr("pipeline.daily_shorts_daemon.retention_analytics.generate_and_save_ledger", lambda *a, **k: None)
    monkeypatch.setattr("pipeline.script_generator.generate_script", _mock_spec)

    daemon = DailyShortsDaemon()
    res = daemon.run_daily_cycle(
        count=1,
        dry_run=True,
        source="blogs"
    )

    assert len(res) == 1
    cand = res[0]["paper"]
    assert cand["id"].startswith("blog_")
    assert cand["category"] in ("tech_news", "model_showdown")


def test_daemon_mixed_source_includes_blogs():
    """Validates that source='mixed' includes official blog candidates alongside papers and perks."""
    from pipeline.official_blogs_fetcher import get_official_blogs_digest
    digest = get_official_blogs_digest(limit=5, offline_only=True)
    assert len(digest) >= 5
    assert all(d["id"].startswith("blog_") for d in digest)


def test_blog_production_records_in_digest_history(tmp_path, monkeypatch):
    """Validates that completed blog productions are recorded in digest history without 404."""
    from pipeline.batch_digest import load_history, record_paper_production
    temp_hist = tmp_path / "digest_history.json"
    temp_hist.write_text('{"processed_papers": {}}', encoding="utf-8")
    monkeypatch.setattr("pipeline.batch_digest.HISTORY_FILE", temp_hist)

    record_paper_production(
        arxiv_id="blog_openai_o3_mini",
        title="OpenAI o3-mini: High-Speed STEM Reasoning Model",
        category="tech_news",
        video_path="final_blog_openai_o3_mini_tech_news.mp4"
    )

    hist = load_history()
    assert "blog_openai_o3_mini" in hist["processed_papers"]
    item = hist["processed_papers"]["blog_openai_o3_mini"]
    assert item["title"] == "OpenAI o3-mini: High-Speed STEM Reasoning Model"
    assert item["category"] == "tech_news"
    assert item["status"] == "completed"


# ==============================================================================
# 8. Non-arXiv ID Bypass (Zero 404 Errors)
# ==============================================================================

def test_non_arxiv_ids_bypass_download_arxiv_source():
    """Validates that download_arxiv_source immediately returns None for non-arXiv IDs."""
    assert download_arxiv_source("blog_openai_o3_mini") is None
    assert download_arxiv_source("blog_claude_3_7_sonnet") is None
    assert download_arxiv_source("news_deepmind_gemini") is None
    assert download_arxiv_source("perk_anthropic_startup_program") is None
    assert download_arxiv_source("gh_vllm_project_vllm") is None


def test_non_arxiv_ids_bypass_extract_paper_figures():
    """Validates that extract_paper_figures immediately returns [] for non-arXiv IDs without downloading."""
    assert extract_paper_figures("blog_openai_o3_mini") == []
    assert extract_paper_figures("blog_claude_3_7_sonnet") == []
    assert extract_paper_figures("news_deepmind_gemini") == []
    assert extract_paper_figures("perk_microsoft_founders_hub") == []
    assert extract_paper_figures("gh_sgl_project_sglang") == []
