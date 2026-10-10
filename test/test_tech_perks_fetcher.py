"""
Test suite for Ground-Truth Tech Perks & Developer Credits Engine.
Verifies:
1. Ground-truth verified programs registry (Anthropic, Microsoft, Google Cloud, GitHub, AWS, Cloudflare).
2. Evidentiary integrity: strict eligibility criteria, numbered steps, official documentation URLs.
3. Official domain whitelist enforcement against fraudulent or spoofed links.
4. Active rumor busting and hallucination rejection (Codex standalone, OpenAI direct forms, unlimited GPUs).
5. Candidate specification conversion matching the pipeline contract.
6. Trending perks digest generation for daemon and scheduler discovery.
"""

import pytest
from pipeline.tech_perks_fetcher import (
    TechPerksFetcher,
    PerkEvidenceRecord,
    PerkVerificationStatus,
    VERIFIED_PERKS_REGISTRY,
    DEBUNKED_RUMORS_REGISTRY,
    OFFICIAL_DOMAINS_WHITELIST,
    get_verified_perks_digest
)


def test_verified_registry_programs_completeness():
    """Validates that all essential verified programs exist and are active."""
    fetcher = TechPerksFetcher()
    active_perks = fetcher.get_all_verified_perks()
    prog_ids = [p.program_id for p in active_perks]

    assert "anthropic_startup_program" in prog_ids
    assert "microsoft_founders_hub" in prog_ids
    assert "google_cloud_ai_startups" in prog_ids
    assert "github_for_startups" in prog_ids
    assert "aws_activate_founders" in prog_ids
    assert "cloudflare_startup_launchpad" in prog_ids
    assert len(active_perks) >= 6


def test_evidentiary_integrity_and_documentation():
    """Validates that every verified program has complete step-by-step instructions and criteria."""
    for prog_id, perk in VERIFIED_PERKS_REGISTRY.items():
        assert perk.headline, f"{prog_id} missing headline"
        assert perk.benefit_summary, f"{prog_id} missing benefit summary"
        assert len(perk.eligibility_criteria) >= 2, f"{prog_id} requires at least 2 eligibility criteria"
        assert len(perk.step_by_step_application) >= 3, f"{prog_id} requires at least 3 application steps"
        assert perk.official_url.startswith("https://"), f"{prog_id} official URL must be https"
        assert perk.status == PerkVerificationStatus.VERIFIED_ACTIVE
        assert perk.anti_hallucination_notes, f"{prog_id} requires anti-hallucination guidance"


def test_official_domain_whitelist_validation():
    """Enforces that only whitelisted official company domains are accepted."""
    fetcher = TechPerksFetcher()

    # Valid domains
    assert fetcher.validate_official_domain("https://console.claude.com/settings") is True
    assert fetcher.validate_official_domain("https://startups.microsoft.com/en-us/apply") is True
    assert fetcher.validate_official_domain("https://cloud.google.com/startup") is True
    assert fetcher.validate_official_domain("https://github.com/enterprise/startups") is True
    assert fetcher.validate_official_domain("https://aws.amazon.com/startups") is True
    assert fetcher.validate_official_domain("https://www.cloudflare.com/startups/") is True

    # Invalid / untrusted domains
    assert fetcher.validate_official_domain("https://free-ai-coupons.scam.io") is False
    assert fetcher.validate_official_domain("https://chatgpt-free-credits.blogspot.com") is False
    assert fetcher.validate_official_domain("https://phishing-microsoft.com") is False
    assert fetcher.validate_official_domain("invalid-url") is False


def test_rumor_buster_debunks_codex_free_month():
    """Verifies that rumors about standalone Codex free month are debunked with official alternatives."""
    fetcher = TechPerksFetcher()
    audit = fetcher.verify_perk_claim("ChatGPT is giving one month free subscription of Codex")

    assert audit["is_verified"] is False
    assert audit["status"] == PerkVerificationStatus.DISCONTINUED.value
    assert audit["requires_correction"] is True
    assert "retired" in audit["explanation"].lower() or "discontinued" in audit["explanation"].lower()
    assert "startups.microsoft.com" in audit["recommended_action"] or "github copilot free" in audit["recommended_action"].lower()


def test_rumor_buster_debunks_openai_direct_form():
    """Verifies that outdated claims of direct OpenAI self-serve startup credit forms are flagged."""
    fetcher = TechPerksFetcher()
    audit = fetcher.verify_perk_claim("OpenAI direct startup apply form for $2500 credits")

    assert audit["is_verified"] is False
    assert audit["status"] == PerkVerificationStatus.DISCONTINUED.value
    assert audit["requires_correction"] is True
    assert "founders hub" in audit["recommended_action"].lower()


def test_rumor_buster_rejects_unverified_claims():
    """Verifies that unverified claims lacking official provider documentation are rejected."""
    fetcher = TechPerksFetcher()
    audit = fetcher.verify_perk_claim("Claiming perpetual unlimited free GPU from an unverified server")

    assert audit["is_verified"] is False
    assert audit["status"] in (PerkVerificationStatus.UNVERIFIED_RUMOR.value, "unverified_rumor")
    assert audit["requires_correction"] is True


def test_verify_perk_claim_resolves_anthropic():
    """Verifies that queries for the Claude startup program resolve to the verified Anthropic record."""
    fetcher = TechPerksFetcher()
    audit = fetcher.verify_perk_claim("Anthropic Claude startup program 1 year free team plan")

    assert audit["is_verified"] is True
    assert audit["provider"] == "Anthropic"
    assert audit["program_id"] == "anthropic_startup_program"
    assert "console.claude.com" in audit["official_url"]
    assert audit["requires_correction"] is False


def test_to_candidate_spec_matches_pipeline_contract():
    """Verifies that PerkEvidenceRecord converts to candidate dict matching daemon/pipeline interface."""
    perk = VERIFIED_PERKS_REGISTRY["microsoft_founders_hub"]
    cand = perk.to_candidate_spec()

    assert cand["id"] == "perk_microsoft_founders_hub"
    assert cand["title"] == perk.headline
    assert cand["recommended_category"] == "developer_perks"
    assert cand["domain_taxonomy"] == "developer_perks"
    assert cand["taxonomy"] == "developer_perks"
    assert cand["source"] == "verified_perks"
    assert "startups.microsoft.com" in cand["abstract"]
    assert cand["impact_score"] >= 90.0
    assert cand["analytics_multiplier"] == 1.25

    # Editorial notes
    ed = cand["editorial_notes"]
    assert "recommended_hook" in ed
    assert "suggested_everyday_analogy" in ed


def test_get_verified_perks_digest():
    """Verifies helper function produces top scored perk candidates."""
    digest = get_verified_perks_digest(limit=3)
    assert len(digest) == 3
    for item in digest:
        assert item["id"].startswith("perk_")
        assert item["recommended_category"] == "developer_perks"
        assert item["impact_score"] > 0
        assert "perk_metadata" in item
