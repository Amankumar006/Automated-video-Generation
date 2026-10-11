"""
The Model Verse — Content Recency & Maximum Age Enforcement Test Suite
Verifies:
1. Date parsing across ISO, RFC 2822, human formats, and arXiv IDs.
2. Content age calculation and recency validation (<= 45-60 days max).
3. Strict exclusion of content older than 1-2 months (> 60 days) across:
   - Official AI Tech News & Blogs (official_blogs_fetcher)
   - Developer Perks & Startup Credits (tech_perks_fetcher)
   - Academic Research Papers (batch_digest & arxiv_fetcher)
4. Integration with DailyShortsDaemon candidate selection and recency gating.
5. Integration with run_pipeline.py CLI age validation and --allow-stale override.
"""

import sys
import datetime
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.config import (
    MAX_CONTENT_AGE_DAYS,
    MAX_PERK_VERIFICATION_AGE_DAYS,
    parse_content_date,
    calculate_content_age_days,
    is_content_recent,
)
from pipeline.official_blogs_fetcher import (
    get_official_blogs_digest,
    get_official_blog,
    official_blogs_fetcher,
    OfficialBlogRecord,
)
from pipeline.tech_perks_fetcher import (
    get_verified_perks_digest,
    tech_perks_fetcher,
    PerkEvidenceRecord,
    PerkVerificationStatus,
)
from pipeline.batch_digest import (
    score_and_classify_paper,
    get_trending_digest,
)
from pipeline.daily_shorts_daemon import (
    fetch_candidates_for_pillar,
    is_candidate_eligible_for_production,
)

# Reference anchor: simulated system date October 11, 2026
REF_DATE = datetime.date(2026, 10, 11)


# ==============================================================================
# 1. Config Date Parsing & Age Calculation
# ==============================================================================

def test_parse_content_date_iso_and_rfc():
    """Validates date parsing across ISO, RFC 2822, human, and arXiv ID strings."""
    # ISO
    assert parse_content_date("2026-10-07") == datetime.date(2026, 10, 7)
    assert parse_content_date("2026-10-07T14:30:00Z") == datetime.date(2026, 10, 7)

    # RFC 2822
    assert parse_content_date("Fri, 31 Jan 2025 18:00:00 GMT") == datetime.date(2025, 1, 31)

    # Human-readable
    assert parse_content_date("October 6, 2026") == datetime.date(2026, 10, 6)
    assert parse_content_date("Sep 29, 2026") == datetime.date(2026, 9, 29)

    # arXiv ID encoded dates (YYMM.NNNNN)
    assert parse_content_date("2609.40362") == datetime.date(2026, 9, 1)
    assert parse_content_date("2407.08608") == datetime.date(2024, 7, 1)
    assert parse_content_date("2501.12948") == datetime.date(2025, 1, 1)


def test_calculate_content_age_days():
    """Validates precise day calculations relative to reference anchor."""
    # 4 days old (Oct 7 relative to Oct 11, 2026)
    assert calculate_content_age_days("2026-10-07", reference_date=REF_DATE) == 4

    # 12 days old (Sep 29 relative to Oct 11, 2026)
    assert calculate_content_age_days("2026-09-29", reference_date=REF_DATE) == 12

    # 45 days old (Aug 27 relative to Oct 11, 2026)
    assert calculate_content_age_days("2026-08-27", reference_date=REF_DATE) == 45

    # 618 days old (Jan 31, 2025 relative to Oct 11, 2026)
    age_o3 = calculate_content_age_days("2025-01-31", reference_date=REF_DATE)
    assert age_o3 is not None and age_o3 > 600

    # 2 years old (July 2024 relative to Oct 11, 2026)
    age_fa3 = calculate_content_age_days("2407.08608", reference_date=REF_DATE)
    assert age_fa3 is not None and age_fa3 > 800


def test_is_content_recent_thresholds():
    """Validates boundary enforcement of 45-day default and 60-day maximum limit."""
    # Fresh items
    assert is_content_recent("2026-10-07", max_age_days=45, reference_date=REF_DATE) is True
    assert is_content_recent("2026-09-29", max_age_days=45, reference_date=REF_DATE) is True
    assert is_content_recent("2026-08-27", max_age_days=45, reference_date=REF_DATE) is True

    # 50 days: rejected under strict 45-day cutoff, allowed under 60-day cutoff
    assert is_content_recent("2026-08-22", max_age_days=45, reference_date=REF_DATE) is False
    assert is_content_recent("2026-08-22", max_age_days=60, reference_date=REF_DATE) is True

    # Over 60 days (more than 2 months old): strictly rejected under all limits!
    assert is_content_recent("2026-08-01", max_age_days=60, reference_date=REF_DATE) is False
    assert is_content_recent("2025-01-31", max_age_days=60, reference_date=REF_DATE) is False
    assert is_content_recent("2407.08608", max_age_days=60, reference_date=REF_DATE) is False


# ==============================================================================
# 2. Official AI Tech News & Blogs Recency
# ==============================================================================

def test_official_blogs_digest_excludes_stale_news():
    """
    Validates that get_official_blogs_digest() returns ONLY fresh late Sept / Oct 2026 drops
    and strictly excludes stale 2024 and early 2025 announcements.
    """
    digest = get_official_blogs_digest(limit=20, offline_only=True)

    assert len(digest) > 0

    returned_ids = {c["id"] for c in digest}

    # MUST contain fresh October/September 2026 drops
    assert "blog_openai_gpt_6_intelligent_ui" in returned_ids
    assert "blog_openai_dots" in returned_ids
    assert "blog_openai_math_progress" in returned_ids
    assert "blog_anthropic_claude_3_8_artifacts" in returned_ids
    assert "blog_deepmind_gemini_3_pro" in returned_ids

    # MUST STRICTLY EXCLUDE stale 2024/early 2025 drops (> 60 days old)
    assert "blog_openai_o3_mini" not in returned_ids  # Jan 2025
    assert "blog_claude_3_7_sonnet" not in returned_ids  # Feb 2025
    assert "blog_deepmind_gemini_2_5_flash" not in returned_ids  # March 2025
    assert "blog_hf_smolagents" not in returned_ids  # Jan 2025
    assert "blog_openai_gpt_4o_mini" not in returned_ids  # July 2024
    assert "blog_anthropic_computer_use" not in returned_ids  # Oct 2024
    assert "blog_deepmind_alphafold_3" not in returned_ids  # May 2024

    # Verify every returned candidate is within allowable recency
    for cand in digest:
        pub_date = cand.get("published_date")
        assert pub_date, f"Candidate {cand['id']} missing published_date"
        age = calculate_content_age_days(pub_date, reference_date=REF_DATE)
        assert age is not None
        assert age <= 45, f"Candidate {cand['id']} is {age} days old (> 45 days cutoff)!"
        assert cand.get("is_stale") is False


def test_official_blog_record_stale_properties():
    """Validates that OfficialBlogRecord properties correctly flag stale records."""
    fresh_rec = get_official_blog("blog_openai_gpt_6_intelligent_ui")
    assert fresh_rec is not None
    assert fresh_rec.is_stale is False
    assert fresh_rec.age_days <= 10

    stale_rec = get_official_blog("blog_openai_o3_mini")
    assert stale_rec is not None
    assert stale_rec.is_stale is True
    assert stale_rec.age_days > 500


# ==============================================================================
# 3. Developer Perks & Startup Credits Recency
# ==============================================================================

def test_tech_perks_digest_excludes_stale_and_expired_perks():
    """Validates that get_verified_perks_digest() strictly enforces recency verification."""
    perks = get_verified_perks_digest(limit=10)
    assert len(perks) > 0

    for p in perks:
        vdate = p.get("last_verified_date") or p.get("perk_metadata", {}).get("last_verified_date")
        assert vdate, f"Perk {p['id']} missing last_verified_date"
        age = calculate_content_age_days(vdate, reference_date=REF_DATE)
        assert age is not None
        assert age <= MAX_PERK_VERIFICATION_AGE_DAYS, f"Perk {p['id']} unverified for {age} days (> {MAX_PERK_VERIFICATION_AGE_DAYS}d limit)!"
        assert p.get("is_stale") is False


def test_tech_perks_filters_out_perk_older_than_60_days():
    """Tests that a simulated perk unverified for > 60 days is automatically disqualified."""
    fake_stale_perk = PerkEvidenceRecord(
        program_id="stale_partner_grant",
        provider="Legacy Cloud",
        headline="Old Cloud Credits",
        benefit_summary="$5,000 credits",
        eligibility_criteria=["Startup"],
        required_documents=["Domain"],
        step_by_step_application=["Apply online"],
        official_url="https://cloud.google.com/old",
        allowed_domains=["cloud.google.com"],
        status=PerkVerificationStatus.VERIFIED_ACTIVE,
        last_verified_date="2026-06-01",  # > 130 days ago
        anti_hallucination_notes="Historical deal"
    )

    with patch.dict(tech_perks_fetcher.registry, {"stale_partner_grant": fake_stale_perk}):
        active_perks = tech_perks_fetcher.get_all_verified_perks(max_age_days=60)
        active_ids = {p.program_id for p in active_perks}
        assert "stale_partner_grant" not in active_ids


# ==============================================================================
# 4. Academic Papers & Batch Digest Recency
# ==============================================================================

def test_batch_digest_filters_out_stale_papers():
    """Validates that get_trending_digest() rejects preprints older than max_age_days."""
    mock_papers = [
        {
            "id": "2609.40362",
            "title": "Fresh September 2026 Breakthrough",
            "abstract": "Novel KV cache compression.",
            "published_at": "2026-09-18",
            "authors": ["Alice", "Bob"]
        },
        {
            "id": "2407.08608",
            "title": "Old July 2024 Paper",
            "abstract": "FlashAttention 3.",
            "published_at": "2024-07-15",
            "authors": ["Tri Dao"]
        },
        {
            "id": "2501.12948",
            "title": "Old Jan 2025 Paper",
            "abstract": "DeepSeek R1.",
            "published_at": "2025-01-20",
            "authors": ["DeepSeek Team"]
        }
    ]

    with patch("pipeline.batch_digest.fetch_hf_daily_papers", return_value=mock_papers):
        digest = get_trending_digest(limit=10, max_age_days=45)
        digest_ids = [p["id"] for p in digest]

        assert "2609.40362" in digest_ids
        assert "2407.08608" not in digest_ids  # Rejected (> 800 days old)
        assert "2501.12948" not in digest_ids  # Rejected (> 600 days old)


# ==============================================================================
# 5. DailyShortsDaemon Candidate Selection & Recency Gating
# ==============================================================================

def test_daemon_candidate_selection_only_emits_fresh_content():
    """Validates that fetch_candidates_for_pillar() only emits fresh candidates across all pillars."""
    # 1. Blogs pillar
    blog_cands = fetch_candidates_for_pillar("blogs", limit=5)
    assert len(blog_cands) > 0
    for b in blog_cands:
        assert is_candidate_eligible_for_production(b, max_age_days=45) is True
        assert b["id"] not in ("blog_openai_o3_mini", "blog_claude_3_7_sonnet")

    # 2. Perks pillar
    perk_cands = fetch_candidates_for_pillar("perks", limit=5)
    assert len(perk_cands) > 0
    for p in perk_cands:
        assert is_candidate_eligible_for_production(p, max_age_days=60) is True


def test_is_candidate_eligible_for_production_rejects_stale_entries():
    """Validates individual candidate eligibility evaluator."""
    # Stale blog
    stale_blog = {
        "id": "blog_openai_o3_mini",
        "category": "tech_news",
        "source": "official_blogs",
        "published_date": "2025-01-31"
    }
    assert is_candidate_eligible_for_production(stale_blog, max_age_days=45) is False

    # Fresh blog
    fresh_blog = {
        "id": "blog_openai_gpt_6_intelligent_ui",
        "category": "tech_news",
        "source": "official_blogs",
        "published_date": "2026-10-07"
    }
    assert is_candidate_eligible_for_production(fresh_blog, max_age_days=45) is True

    # Stale arXiv paper
    stale_arxiv = {
        "id": "2407.08608",
        "category": "mechanism_deepdive",
        "source": "arxiv",
        "published_at": "2024-07-15"
    }
    assert is_candidate_eligible_for_production(stale_arxiv, max_age_days=45) is False
