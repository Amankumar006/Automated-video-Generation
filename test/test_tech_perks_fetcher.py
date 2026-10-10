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


def test_verify_perk_claim_relevance_ranking_without_greedy_bias():
    """
    Validates that relevance-scored matching correctly routes specific provider queries
    instead of greedily returning the first registry record (Anthropic) for common words.
    """
    fetcher = TechPerksFetcher()

    # AWS
    res_aws = fetcher.verify_perk_claim("AWS free credits for foundation models")
    assert res_aws["is_verified"] is True
    assert res_aws["provider"] == "Amazon Web Services"
    assert res_aws["program_id"] == "aws_activate_founders"

    # Google Cloud
    res_google = fetcher.verify_perk_claim("Google Cloud startup credits for Gemini")
    assert res_google["is_verified"] is True
    assert res_google["provider"] == "Google Cloud"
    assert res_google["program_id"] == "google_cloud_ai_startups"

    # Microsoft
    res_ms = fetcher.verify_perk_claim("microsoft startup credits for Azure OpenAI")
    assert res_ms["is_verified"] is True
    assert res_ms["provider"] == "Microsoft"
    assert res_ms["program_id"] == "microsoft_founders_hub"

    # Cloudflare
    res_cf = fetcher.verify_perk_claim("Cloudflare startup launchpad credits")
    assert res_cf["is_verified"] is True
    assert res_cf["provider"] == "Cloudflare"
    assert res_cf["program_id"] == "cloudflare_startup_launchpad"

    # OpenAI
    res_oai = fetcher.verify_perk_claim("OpenAI startup credits for GPT-4o")
    assert res_oai["is_verified"] is True
    assert res_oai["provider"] == "OpenAI"
    assert res_oai["program_id"] == "openai_for_startups"

    # User prompt scenario: "Cloud" typo with pro plan / 1 year subscription
    res_typo = fetcher.verify_perk_claim("Cloud is giving one year of subscription of its pro plan for startups")
    assert res_typo["is_verified"] is True
    assert res_typo["provider"] == "Anthropic"
    assert res_typo["program_id"] == "anthropic_startup_program"


def test_web_research_documentation_extraction_from_official_domain(monkeypatch):
    """Verifies that fetch_and_verify_web_documentation parses HTML criteria and steps from official URLs."""
    from unittest.mock import MagicMock
    import io

    sample_html = """
    <!DOCTYPE html>
    <html>
    <head><title>Official Cloud Startup Credits Program</title></head>
    <body>
        <h1>Startup Grants & Credits</h1>
        <p>Empowering early-stage founders with infrastructure credits.</p>
        <h2>Eligibility Requirements</h2>
        <ul>
            <li>Bootstrapped or funded tech startup founded within last 5 years</li>
            <li>Active live company website and corporate domain email</li>
        </ul>
        <h2>How to Apply</h2>
        <ul>
            <li>Step 1. Sign in to the official developer console portal</li>
            <li>Step 2. Submit application form with company website link</li>
            <li>Step 3. Receive decision and access dashboard credits</li>
        </ul>
    </body>
    </html>
    """.encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = sample_html
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=10: mock_resp)

    fetcher = TechPerksFetcher()
    doc_data = fetcher.fetch_and_verify_web_documentation("https://console.claude.com/startups")

    assert doc_data["is_verified"] is True
    assert doc_data["title"] == "Official Cloud Startup Credits Program"
    assert len(doc_data["eligibility_criteria"]) >= 1
    assert any("founded" in c.lower() for c in doc_data["eligibility_criteria"])
    assert len(doc_data["step_by_step_application"]) >= 1
    assert any("apply" in s.lower() or "step" in s.lower() for s in doc_data["step_by_step_application"])


def test_web_research_rejects_unwhitelisted_domains():
    """Verifies that web research rejects non-whitelisted or spoofed domains."""
    fetcher = TechPerksFetcher()
    doc_data = fetcher.fetch_and_verify_web_documentation("https://scam-cloud-credits.xyz/free")
    assert doc_data["is_verified"] is False
    assert "not in the official whitelist" in doc_data["error"]


def test_research_perk_unified_interface(monkeypatch):
    """Verifies research_perk handles both URLs and natural language queries."""
    fetcher = TechPerksFetcher()

    # Query path
    q_res = fetcher.research_perk("AWS Activate Founders program")
    assert q_res["is_verified"] is True
    assert q_res["provider"] == "Amazon Web Services"

    # URL path with invalid domain
    u_res = fetcher.research_perk("https://fake-credits.io/claim")
    assert u_res["is_verified"] is False


def test_verified_openai_startup_program_integrity():
    """Validates that openai_for_startups meets ground-truth evidentiary requirements."""
    fetcher = TechPerksFetcher()
    oai_perk = fetcher.get_verified_perk("openai_for_startups")

    assert oai_perk is not None
    assert oai_perk.provider == "OpenAI"
    assert len(oai_perk.eligibility_criteria) >= 2
    assert len(oai_perk.step_by_step_application) >= 3
    assert "startups.microsoft.com" in oai_perk.anti_hallucination_notes or "founders hub" in oai_perk.anti_hallucination_notes.lower()

