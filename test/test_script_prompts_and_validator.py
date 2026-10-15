"""
Test suite for standardized script prompts, schema parsing, and quality validator.
Validates:
- SHARED_SCRIPT_PROMPT_DIRECTIVE content and constraints
- Track 1, 2, and 3 prompt templates
- validate_script_spec rules (beat count, 115-140 words, anchor words, banned phrases)
- Deterministic scripts adherence to word budgets and schema
- Parser normalization for new JSON output format (beats[].n, text, anchor_word, visual_cue)
"""

import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

from pipeline.script_directives import (
    SHARED_SCRIPT_PROMPT_DIRECTIVE,
    TRACK_1_DEEP_BREAKDOWN_PROMPT_TEMPLATE,
    TRACK_2_TECH_NEWS_PROMPT_TEMPLATE,
    TRACK_3_DEVELOPER_PERKS_PROMPT_TEMPLATE,
    validate_script_spec,
    get_total_word_count,
    BANNED_PHRASES,
    TARGET_WORD_COUNT_MIN,
    TARGET_WORD_COUNT_MAX
)
from pipeline.tech_news_script_engine import tech_news_script_engine
from pipeline.developer_perks_script_engine import developer_perks_script_engine


def test_shared_prompt_directive_content():
    """Validates that the shared block matches the user's exact requirements."""
    prompt = SHARED_SCRIPT_PROMPT_DIRECTIVE
    assert "The Model Verse" in prompt
    assert "themodelverse.in" in prompt
    assert "Exactly 6 beats, 115-140 words total" in prompt
    assert "Max 12 words per sentence" in prompt
    assert "anchor_word" in prompt
    assert "visual_cue" in prompt
    assert "Never reuse an anchor_word" in prompt
    for phrase in BANNED_PHRASES:
        assert phrase in prompt
    assert '"word_count": <int>' in prompt


def test_track_prompt_templates():
    """Validates Track 1, 2, and 3 prompt structures."""
    t1 = TRACK_1_DEEP_BREAKDOWN_PROMPT_TEMPLATE.format(
        paper_title="Test Paper",
        abstract_or_paper_text="Test Abstract"
    )
    assert "ROLE: Technical scriptwriter" in t1
    assert "SOURCE: Test Paper" in t1
    assert "HOOK (8-10 words, 0-3s)" in t1
    assert "VILLAIN (24-28 words, 3-13s)" in t1
    assert "EUREKA (26-30 words, 13-24s)" in t1
    assert "SECRET SAUCE (24-28 words, 24-35s)" in t1
    assert "PAYOFF (20-24 words, 35-44s)" in t1
    assert "SHIFT + LOOP (14-18 words, 44-52s)" in t1

    t2 = TRACK_2_TECH_NEWS_PROMPT_TEMPLATE.format(
        provider="OpenAI",
        headline="GPT-4.5 Orion",
        details="10x cheaper"
    )
    assert "ROLE: Breaking tech news reporter" in t2
    assert "Provider: OpenAI" in t2
    assert "Headline: GPT-4.5 Orion" in t2
    assert "BREAKING HOOK (8-10 words, 0-3s)" in t2
    assert "THE OLD CEILING (20-24 words, 3-12s)" in t2
    assert "WHAT'S NEW (24-28 words, 12-24s)" in t2
    assert "BENCHMARKS (24-28 words, 24-35s)" in t2
    assert "PRICE + ACCESS (22-26 words, 35-44s)" in t2
    assert "TAKEAWAY + CTA (14-18 words, 44-52s)" in t2

    t3 = TRACK_3_DEVELOPER_PERKS_PROMPT_TEMPLATE.format(
        provider="Anthropic",
        headline="Claude for Startups",
        val_str="$1,000",
        details="Free team tier"
    )
    assert "ROLE: Host of a developer-deals channel" in t3
    assert "Provider: Anthropic" in t3
    assert "Program: Claude for Startups" in t3
    assert "Total value: $1,000" in t3
    assert "VALUE HOOK (8-10 words, 0-3s)" in t3
    assert "THE DEAL (22-26 words, 3-12s)" in t3
    assert "WHO QUALIFIES (24-28 words, 12-24s)" in t3
    assert "HOW TO APPLY (24-28 words, 24-35s)" in t3
    assert "PROOF + TIMING (20-24 words, 35-44s)" in t3
    assert "SAVE CTA (14-18 words, 44-52s)" in t3


def test_validator_approves_valid_script():
    """Validates that a compliant 6-beat script passes validation with 0 errors."""
    valid_spec = {
        "title": "FlashAttention 3 Architecture",
        "beats": [
            {
                "n": 1,
                "text": "Hardware memory walls freeze large language models during inference.",
                "anchor_word": "inference",
                "visual_cue": "Hardware memory wall barrier"
            },
            {
                "n": 2,
                "text": "Standard quadratic attention routines force modern server GPUs to constantly shuffle huge matrices back and forth between slow high bandwidth memory and fast on chip SRAM.",
                "anchor_word": "SRAM",
                "visual_cue": "GPU memory bottleneck diagram"
            },
            {
                "n": 3,
                "text": "FlashAttention three rewrites how GPUs operate by completely overlapping asynchronous matrix multiplications with warp specialized software pipelining inside specialized tensor memory accelerator hardware. This keeps processors fully fed.",
                "anchor_word": "accelerator",
                "visual_cue": "Asynchronous pipeline architecture"
            },
            {
                "n": 4,
                "text": "It exploits FP8 low precision tensor cores and ping pong buffers to hide memory latency behind raw arithmetic throughput, achieving zero register stalls.",
                "anchor_word": "throughput",
                "visual_cue": "Ping pong buffer latency hiding"
            },
            {
                "n": 5,
                "text": "The empirical payoff is massive with seven hundred forty TFLOPS measured on Hopper H100 architectures matching eighty percent model FLOPs utilization.",
                "anchor_word": "Hopper",
                "visual_cue": "Hopper benchmark comparison chart"
            },
            {
                "n": 6,
                "text": "This redefines inference economics forever. Follow The Model Verse for daily frontier AI architectural deep dives.",
                "anchor_word": "Model",
                "visual_cue": "The Model Verse outro"
            }
        ]
    }
    total_words = get_total_word_count(valid_spec)
    assert TARGET_WORD_COUNT_MIN <= total_words <= TARGET_WORD_COUNT_MAX
    is_valid, errors = validate_script_spec(valid_spec)
    assert is_valid is True
    assert errors == []


def test_validator_rejects_word_count_below_min():
    """Rejects scripts with fewer than 115 words."""
    short_spec = {
        "title": "Short Script",
        "beats": [
            {"n": i, "text": f"This is beat {i}.", "anchor_word": "beat", "visual_cue": "visual"}
            for i in range(1, 7)
        ]
    }
    is_valid, errors = validate_script_spec(short_spec)
    assert is_valid is False
    assert any("outside required range" in e for e in errors)


def test_validator_rejects_missing_anchor_word_in_text():
    """Rejects a beat when anchor_word does not appear in spoken text."""
    spec = {
        "title": "Mismatch Anchor",
        "beats": [
            {
                "n": 1,
                "text": "Robots drop objects when moving too fast.",
                "anchor_word": "quantum",  # not in text
                "visual_cue": "Robot moving"
            },
            {"n": 2, "text": "A " * 24, "anchor_word": "A", "visual_cue": "cue"},
            {"n": 3, "text": "B " * 26, "anchor_word": "B", "visual_cue": "cue"},
            {"n": 4, "text": "C " * 24, "anchor_word": "C", "visual_cue": "cue"},
            {"n": 5, "text": "D " * 22, "anchor_word": "D", "visual_cue": "cue"},
            {"n": 6, "text": "E " * 16, "anchor_word": "E", "visual_cue": "cue"},
        ]
    }
    is_valid, errors = validate_script_spec(spec)
    assert is_valid is False
    assert any("not found in spoken text" in e for e in errors)


def test_validator_rejects_reused_anchor_word():
    """Rejects scripts that reuse the same anchor word across beats."""
    spec = {
        "title": "Reused Anchor",
        "beats": [
            {"n": 1, "text": "GPU architectures hit walls.", "anchor_word": "GPU", "visual_cue": "cue"},
            {"n": 2, "text": "The GPU bottleneck is severe. " * 3, "anchor_word": "GPU", "visual_cue": "cue"},
            {"n": 3, "text": "Three " * 26, "anchor_word": "Three", "visual_cue": "cue"},
            {"n": 4, "text": "Four " * 24, "anchor_word": "Four", "visual_cue": "cue"},
            {"n": 5, "text": "Five " * 22, "anchor_word": "Five", "visual_cue": "cue"},
            {"n": 6, "text": "Six " * 16, "anchor_word": "Six", "visual_cue": "cue"},
        ]
    }
    is_valid, errors = validate_script_spec(spec)
    assert is_valid is False
    assert any("reused across beats" in e for e in errors)


def test_validator_rejects_banned_phrases():
    """Rejects scripts that use banned clichés."""
    spec = {
        "title": "Banned Phrase",
        "beats": [
            {"n": 1, "text": "In this paper we explore attention.", "anchor_word": "attention", "visual_cue": "cue"},
            {"n": 2, "text": "Two " * 24, "anchor_word": "Two", "visual_cue": "cue"},
            {"n": 3, "text": "Three " * 26, "anchor_word": "Three", "visual_cue": "cue"},
            {"n": 4, "text": "Four " * 24, "anchor_word": "Four", "visual_cue": "cue"},
            {"n": 5, "text": "Five " * 22, "anchor_word": "Five", "visual_cue": "cue"},
            {"n": 6, "text": "Six " * 16, "anchor_word": "Six", "visual_cue": "cue"},
        ]
    }
    is_valid, errors = validate_script_spec(spec)
    assert is_valid is False
    assert any("contains banned phrase" in e for e in errors)


def test_tech_news_deterministic_script_passes_validation():
    """Validates that tech news deterministic generation satisfies word budgets and schema."""
    spec = tech_news_script_engine.generate_news_script(
        topic="OpenAI Launches o3-mini Reasoning Model",
        blog_meta={"provider": "OpenAI", "title": "OpenAI Launches o3-mini Reasoning Model"},
        use_llm=False
    )
    assert spec["category"] == "tech_news"
    assert len(spec["beats"]) == 6
    for b in spec["beats"]:
        assert "text" in b
        assert "anchor_word" in b
        assert "visual_cue" in b
        assert b["anchor_word"].lower() in b["text"].lower()

    is_valid, errors = validate_script_spec(spec)
    assert is_valid is True, f"Validation errors: {errors}"
    assert TARGET_WORD_COUNT_MIN <= spec["word_count"] <= TARGET_WORD_COUNT_MAX


def test_developer_perks_deterministic_script_passes_validation():
    """Validates that developer perks deterministic generation satisfies word budgets and schema."""
    spec = developer_perks_script_engine.generate_perks_script(
        topic="Anthropic Claude Startups Program",
        perk_meta={"provider": "Anthropic", "title": "Claude Startups Program", "value_usd": 2800},
        use_llm=False
    )
    assert spec["category"] == "developer_perks"
    assert len(spec["beats"]) == 6
    for b in spec["beats"]:
        assert "text" in b
        assert "anchor_word" in b
        assert "visual_cue" in b
        assert b["anchor_word"].lower() in b["text"].lower()

    is_valid, errors = validate_script_spec(spec)
    assert is_valid is True, f"Validation errors: {errors}"
    assert TARGET_WORD_COUNT_MIN <= spec["word_count"] <= TARGET_WORD_COUNT_MAX


def test_parser_normalizes_llm_json_output():
    """Validates that _finalize_spec correctly normalizes an LLM JSON payload with n, anchor_word, and visual_cue."""
    raw_llm_spec = {
        "title": "Google DeepMind Flash Thinking",
        "beats": [
            {
                "n": 1,
                "text": "Google DeepMind just dropped Gemini Flash with instant reasoning.",
                "anchor_word": "dropped",
                "visual_cue": "Google DeepMind logo hero card"
            },
            {
                "n": 2,
                "text": "Earlier reasoning models were notoriously slow and expensive, burning precious startup cash on high latency token loops while developers waited for simple answers.",
                "anchor_word": "expensive",
                "visual_cue": "Latency bottlenecks visualization"
            },
            {
                "n": 3,
                "text": "Gemini Flash delivers an architectural leap, using distilled step-by-step reasoning tokens to achieve three times lower latency without compromising benchmark accuracy.",
                "anchor_word": "distilled",
                "visual_cue": "Distilled reasoning architecture diagram"
            },
            {
                "n": 4,
                "text": "On verified benchmarks it leads the entire industry, dominating SWE-bench Verified while consistently outperforming prior frontier reasoning baselines across coding evaluations.",
                "anchor_word": "benchmarks",
                "visual_cue": "Verified benchmarks bar chart comparison"
            },
            {
                "n": 5,
                "text": "The pricing drops dramatically to ten cents per million tokens, available right now across API production dashboards with immediate deployment access for developers.",
                "anchor_word": "pricing",
                "visual_cue": "Pricing comparison table"
            },
            {
                "n": 6,
                "text": "Deploy this into your stack today. Follow The Model Verse for instant breakdowns of every major AI lab drop.",
                "anchor_word": "Model",
                "visual_cue": "The Model Verse outro screen"
            }
        ]
    }

    finalized = tech_news_script_engine._finalize_spec(
        raw_llm_spec,
        topic="Google DeepMind Flash Thinking",
        blog_meta={"provider": "Google DeepMind"}
    )

    assert finalized["category"] == "tech_news"
    assert finalized["voice_style"] == "newsroom_anchor"
    assert len(finalized["beats"]) == 6
    assert finalized["beats"][0]["beat_id"] == 1
    assert finalized["beats"][0]["anchor_word"] == "dropped"
    assert finalized["beats"][0]["visual_cue"] == "Google DeepMind logo hero card"
    assert finalized["beats"][0]["visual_focus"] == "Google DeepMind logo hero card"
    assert finalized["beats"][0]["svo_action"]["anchor_word"] == "dropped"
    assert "manim_blueprints" in finalized
    assert TARGET_WORD_COUNT_MIN <= finalized["word_count"] <= TARGET_WORD_COUNT_MAX
