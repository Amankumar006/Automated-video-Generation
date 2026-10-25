"""
Test suite for Three-Category Dedicated Workflow Engines.

Verifies:
1. Track 1: Academic Mechanism Breakdown (formulas, SVO triples, blueprints intact)
2. Track 2: Official Tech News Engine (newsroom reporter voice, lab emblems, benchmark cards, pricing/latency)
3. Track 3: Developer Perks Engine (dollar value hook, bundle grid, eligibility checklist, console walkthrough, social proof)
4. Category routing across script_generator, run_pipeline, auto_produce, and daily_shorts_daemon
5. Vector primitives generation (lab emblems, browser mockup, cursor, ripple, social proof cards)
6. Manim Scene instantiation and spec hydration for TechNewsScene and DeveloperPerksScene
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from pipeline.tech_news_script_engine import TechNewsScriptEngine, tech_news_script_engine
from pipeline.developer_perks_script_engine import DeveloperPerksScriptEngine, developer_perks_script_engine
from pipeline.script_generator import generate_script, CATEGORIES
from pipeline.run_pipeline import CATEGORY_SCENE_MAP

# -------------------------------------------------------------------------
# 1. Tech News Script Engine Tests (Track 2)
# -------------------------------------------------------------------------

def test_tech_news_script_engine_generates_six_beats():
    """Validates that TechNewsScriptEngine produces a full 6-beat newsroom spec."""
    blog_data = {
        "id": "blog_deepmind_gemini_flash",
        "title": "Google DeepMind Launches Gemini 2.0 Flash Thinking",
        "provider": "google",
        "author": "Google DeepMind",
        "summary": "Google releases Gemini 2.0 Flash Thinking with 3x lower latency and competitive reasoning.",
        "url": "https://deepmind.google/technologies/gemini/",
        "benchmarks": {
            "math": "89.2% on MATH",
            "coding": "74.5% on HumanEval",
            "latency": "120ms TTFT"
        },
        "pricing": {
            "input": "$0.10 / 1M",
            "output": "$0.40 / 1M"
        }
    }

    spec = tech_news_script_engine.generate_news_script(
        topic="Google DeepMind Launches Gemini 2.0 Flash Thinking",
        blog_meta=blog_data,
        use_llm=False
    )

    assert spec["category"] == "tech_news"
    assert spec["provider"] == "google"
    assert "Gemini" in spec["title"]
    assert len(spec["beats"]) == 6

    # Verify newsroom beats
    beat_names = [b["name"] for b in spec["beats"]]
    assert "b1_hook" in beat_names
    assert "b2_predecessor" in beat_names
    assert "b3_core_breakthrough" in beat_names
    assert "b4_benchmarks" in beat_names
    assert "b5_pricing_availability" in beat_names
    assert "b6_brand_outro" in beat_names

    # Verify voice style and manim blueprints
    assert spec["voice_style"] == "newsroom_anchor"
    assert "manim_blueprints" in spec
    assert len(spec["manim_blueprints"]) == 6
    assert spec["manim_blueprints"][0]["type"] == "hero_announcement"
    assert spec["manim_blueprints"][3]["type"] == "benchmark_comparison"
    assert spec["manim_blueprints"][4]["type"] == "pricing_and_availability"


def test_tech_news_engine_does_not_invent_metrics_or_generic_before_opening():
    """A sparse source must produce an honest script instead of hard-coded hype."""
    spec = TechNewsScriptEngine().generate_news_script(
        topic="Aster Labs announces Aster One",
        blog_meta={
            "title": "Aster Labs announces Aster One",
            "provider": "Aster Labs",
        },
        use_llm=False,
    )

    all_text = " ".join(beat["text"] for beat in spec["beats"])
    assert "before" not in spec["beats"][0]["text"].lower()
    assert "3.2x" not in all_text
    assert "49.3%" not in all_text
    assert "-92%" not in all_text
    assert "$1.10" not in all_text
    assert spec["math_formulas"] == []
    assert "not reported" in all_text.lower()


def test_tech_news_engine_uses_explicit_facts_and_keeps_six_beat_arc():
    """Facts supplied by fetchers should reach the narration and visual params."""
    spec = TechNewsScriptEngine().generate_news_script(
        topic="Nova releases Nova 2",
        blog_meta={
            "title": "Nova releases Nova 2",
            "provider": "Nova Labs",
            "summary": "Nova 2 adds controllable tool use for production workflows",
            "architecture": "routes tool calls through a typed planner",
            "benchmarks": {"TaskBench": "78%"},
            "pricing": {"input": "$0.20 / 1M tokens"},
            "availability": ["API beta"],
            "speedups": ["18% lower latency in the release note"],
        },
        use_llm=False,
    )

    assert len(spec["beats"]) == 6
    assert "controllable tool use" in spec["beats"][0]["text"]
    assert "typed planner" in spec["beats"][2]["text"]
    assert "TaskBench: 78%" in spec["beats"][3]["text"]
    assert "$0.20 / 1M tokens" in spec["beats"][4]["text"]
    assert "API beta" in spec["beats"][4]["text"]
    assert spec["beats"][3]["visual_blueprint"]["params"]["benchmarks"] == {"TaskBench": "78%"}
    assert spec["beats"][4]["visual_blueprint"]["params"]["availability"] == ["API beta"]
    assert {formula["beat_id"] for formula in spec["math_formulas"]} == {3, 4, 5}


def test_tech_news_engine_provider_detection():
    """Validates provider identification across top AI labs."""
    engine = TechNewsScriptEngine()
    assert engine._detect_provider("OpenAI Unveils GPT-4.5 Orion", {}) == "openai"
    assert engine._detect_provider("Anthropic Claude 3.7 Sonnet Released", {}) == "anthropic"
    assert engine._detect_provider("Google DeepMind Gemma 3 Release", {}) == "google"
    assert engine._detect_provider("Hugging Face Open LLM Leaderboard 2", {}) == "huggingface"
    assert engine._detect_provider("Meta Llama 4 Preview", {}) == "general_tech"


# -------------------------------------------------------------------------
# 2. Developer Perks Script Engine Tests (Track 3)
# -------------------------------------------------------------------------

def test_developer_perks_script_engine_generates_six_beats():
    """Validates that DeveloperPerksScriptEngine produces an actionable deal guide spec."""
    perk_data = {
        "id": "perk_claude_startups",
        "title": "Claude for Startups $1,000 Credits",
        "provider": "anthropic",
        "value": "$1,000 in API Credits + 1 Year Claude Team",
        "value_numeric": 1000,
        "eligibility": [
            "Early stage AI startup",
            "Less than $5M raised in venture funding",
            "Working prototype with live demo"
        ],
        "application_url": "https://console.anthropic.com/startups",
        "steps": [
            "Navigate to console.anthropic.com",
            "Sign in with work email",
            "Submit company website and prototype link"
        ],
        "social_proof": [
            {"platform": "x", "quote": "Got $1,000 Anthropic credits approved in under 48 hours!", "author": "@ai_founder"}
        ]
    }

    spec = developer_perks_script_engine.generate_perks_script(
        topic="Claude for Startups $1,000 Credits",
        perk_meta=perk_data,
        use_llm=False
    )

    assert spec["category"] == "developer_perks"
    assert spec["provider"] == "anthropic"
    assert "$1,000" in spec["title"] or "Claude" in spec["title"]
    assert len(spec["beats"]) == 6

    # Verify perk beats
    beat_names = [b["name"] for b in spec["beats"]]
    assert "b1_dollar_value_hook" in beat_names
    assert "b2_bundle_breakdown" in beat_names
    assert "b3_eligibility_criteria" in beat_names
    assert "b4_console_walkthrough" in beat_names
    assert "b5_social_proof" in beat_names
    assert "b6_save_bookmark_cta" in beat_names

    # Verify voice style and manim blueprints
    assert spec["voice_style"] == "actionable_insider"
    assert "manim_blueprints" in spec
    assert len(spec["manim_blueprints"]) == 6
    assert spec["manim_blueprints"][0]["type"] == "dollar_value_hero"
    assert spec["manim_blueprints"][2]["type"] == "eligibility_checklist"
    assert spec["manim_blueprints"][3]["type"] == "console_walkthrough"
    assert spec["manim_blueprints"][4]["type"] == "social_proof_receipts"


def test_developer_perks_engine_dollar_extraction():
    """Validates dollar hook extraction from various text formats."""
    engine = DeveloperPerksScriptEngine()
    assert "$5,000" in engine._extract_dollar_value("AWS Activate provides $5,000 in credits", {})
    assert "$1,000" in engine._extract_dollar_value("Anthropic Startup Program $1000", {})
    assert "$2,500" in engine._extract_dollar_value("GitHub Student Developer Pack ($2500+ value)", {})


# -------------------------------------------------------------------------
# 3. Category Routing Tests
# -------------------------------------------------------------------------

def test_script_generator_routes_all_three_tracks(monkeypatch):
    """Validates that generate_script dispatches correctly to each workflow engine."""
    # Track 1: Academic Mechanism Deepdive
    academic_paper = {
        "title": "DeepSeek-V3 Technical Report: Multi-head Latent Attention",
        "abstract": "We introduce DeepSeek-V3, a strong Mixture-of-Experts language model.",
        "taxonomy": "efficient_llm",
        "paper_figures": []
    }
    mock_academic_spec = {
        "id": "deepseek_v3_multi_head_latent_attention",
        "title": "DeepSeek-V3 Multi-head Latent Attention",
        "category": "mechanism_deepdive",
        "beats": [{"beat_id": i, "name": f"b{i}", "text": f"Beat {i}"} for i in range(1, 7)]
    }

    def mock_route(*args, **kwargs):
        cat = kwargs.get("category") or "mechanism_deepdive"
        if cat == "tech_news":
            return ({
                "id": "blog_openai_deep_research",
                "title": "OpenAI Introduces Deep Research",
                "category": "tech_news",
                "voice_style": "newsroom_anchor",
                "beats": [{"beat_id": i, "name": f"b{i}", "text": f"News Beat {i}"} for i in range(1, 7)]
            }, "mock_llm")
        elif cat == "developer_perks":
            return ({
                "id": "perk_microsoft_founders_hub",
                "title": "Microsoft for Startups Founders Hub",
                "category": "developer_perks",
                "voice_style": "actionable_insider",
                "beats": [{"beat_id": i, "name": f"b{i}", "text": f"Perk Beat {i}"} for i in range(1, 7)]
            }, "mock_llm")
        return (mock_academic_spec, "mock_llm")

    monkeypatch.setattr(
        "pipeline.llm_router.llm_router.route_script_generation",
        mock_route
    )
    monkeypatch.setattr(
        "pipeline.feynman_dialogue_engine.feynman_socratic_loop.run_socratic_loop",
        lambda *args, **kwargs: (mock_academic_spec, {})
    )

    academic_spec = generate_script(
        topic="DeepSeek-V3 Multi-head Latent Attention",
        category="mechanism_deepdive",
        arxiv_meta=academic_paper
    )
    assert academic_spec["category"] == "mechanism_deepdive"
    assert len(academic_spec["beats"]) == 6

    # Track 2: Official Tech News
    news_item = {
        "title": "OpenAI Introduces Deep Research",
        "summary": "Autonomous web browsing and synthesized reports.",
        "provider": "openai"
    }
    news_spec = generate_script(
        topic="blog_openai_deep_research",
        category="tech_news",
        arxiv_meta=news_item
    )
    assert news_spec["category"] == "tech_news"
    assert news_spec["voice_style"] == "newsroom_anchor"

    # Track 3: Developer Perks
    perk_item = {
        "title": "Microsoft for Startups Founders Hub",
        "value": "$25,000 Azure OpenAI Credits",
        "provider": "microsoft"
    }
    perk_spec = generate_script(
        topic="perk_microsoft_founders_hub",
        category="developer_perks",
        arxiv_meta=perk_item
    )
    assert perk_spec["category"] == "developer_perks"
    assert perk_spec["voice_style"] == "actionable_insider"


def test_category_scene_map_dispatches_dedicated_scenes():
    """Validates that CATEGORY_SCENE_MAP routes each track to its dedicated Manim Scene."""
    assert CATEGORY_SCENE_MAP["tech_news"]["class"] == "TechNewsScene"
    assert CATEGORY_SCENE_MAP["developer_perks"]["class"] == "DeveloperPerksScene"
    assert CATEGORY_SCENE_MAP["mechanism_deepdive"]["class"] == "MechanismDeepDiveScene"
    assert CATEGORY_SCENE_MAP["architecture_breakdown"]["class"] == "ArchitectureBreakdownScene"
    assert CATEGORY_SCENE_MAP["model_showdown"]["class"] == "ModelShowdownScene"
    assert CATEGORY_SCENE_MAP["benchmark_news"]["class"] == "BenchmarkNewsScene"


# -------------------------------------------------------------------------
# 4. Manim Vector Primitives Tests
# -------------------------------------------------------------------------

def test_manim_lab_branding_primitives():
    """Validates creation of procedural vector logos for official AI labs."""
    from manim_engine.primitives.lab_branding import (
        create_openai_logo,
        create_claude_logo,
        create_google_deepmind_logo,
        create_huggingface_logo,
        create_github_logo,
        create_lab_hero_badge
    )

    badge_openai = create_lab_hero_badge("openai", badge_text="OFFICIAL LAUNCH")
    badge_claude = create_lab_hero_badge("anthropic", badge_text="CLAUDE MODEL DROP")
    badge_google = create_lab_hero_badge("google", badge_text="DEEPMIND RESEARCH")
    badge_hf = create_lab_hero_badge("huggingface", badge_text="COMMUNITY DROP")
    badge_github = create_lab_hero_badge("github", badge_text="DEVELOPER PERK")

    assert badge_openai is not None
    assert badge_claude is not None
    assert badge_google is not None
    assert badge_hf is not None
    assert badge_github is not None


def test_manim_cursor_and_browser_primitives():
    """Validates interactive browser mockup, cursor arrow, and click ripple primitives."""
    from manim_engine.primitives.cursor_interaction import (
        create_browser_window_mockup,
        create_input_field,
        create_cursor,
        create_click_ripple
    )

    browser = create_browser_window_mockup(url="console.anthropic.com/startups", title="Anthropic Console")
    input_field = create_input_field(label="Work Email", placeholder="founder@ai-startup.com")
    cursor = create_cursor(size=0.35)
    ripple = create_click_ripple(radius=0.45)

    assert browser is not None
    assert input_field is not None
    assert cursor is not None
    assert ripple is not None


def test_manim_social_proof_primitives():
    """Validates 3D floating social proof receipts and partner app tile primitives."""
    from manim_engine.primitives.social_proof_card import (
        create_social_proof_card,
        create_partner_app_tile
    )

    x_card = create_social_proof_card(
        author_name="Sarah Chen",
        handle="@sarah_ai",
        avatar_letter="S",
        post_text="Got our $1,000 Claude API credits approved within 2 days! Massive boost for our MVP.",
        metric_text="1.2k Likes • 240 Retweets",
        platform="x"
    )

    reddit_card = create_social_proof_card(
        author_name="r/MachineLearning",
        handle="u/dev_founder",
        avatar_letter="r",
        post_text="Can confirm: OpenAI and Anthropic startup credits stack without conflict.",
        metric_text="380 Upvotes • 85 Comments",
        platform="reddit"
    )

    partner_tile = create_partner_app_tile(
        title="Cursor IDE",
        subtitle="1 Year Pro",
        badge="INCLUDED"
    )

    assert x_card is not None
    assert reddit_card is not None
    assert partner_tile is not None


# -------------------------------------------------------------------------
# 5. Scene Instantiation & Typography Tests
# -------------------------------------------------------------------------

def test_tech_news_scene_instantiation_and_typography():
    """Validates TechNewsScene instantiation, provider inference, and typography setup."""
    from manim_engine.scenes.tech_news_scene import TechNewsScene
    scene = TechNewsScene()
    assert scene is not None
    spec = {
        "title": "OpenAI o3-mini Reasoning Breakthrough",
        "category": "tech_news",
        "beats": []
    }
    provider = scene._infer_provider(spec)
    assert provider == "OpenAI"


def test_developer_perks_scene_instantiation_and_typography():
    """Validates DeveloperPerksScene instantiation, provider inference, and typography setup."""
    from manim_engine.scenes.developer_perks_scene import DeveloperPerksScene
    scene = DeveloperPerksScene()
    assert scene is not None
    spec = {
        "title": "Claude for Startups $1,000 Credits",
        "category": "developer_perks",
        "beats": []
    }
    provider = scene._infer_provider(spec)
    assert provider == "Anthropic"

