import pytest
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.config import (
    TRACK_ACADEMIC,
    TRACK_TECH_NEWS,
    TRACK_DEVELOPER_PERKS,
    CANONICAL_TRACKS,
    TRACK_ALIASES,
    TRACK_METADATA,
    resolve_track,
)
from pipeline.publisher import generate_shorts_metadata
from pipeline.bespoke_visual_synthesizer import (
    BespokeVisualSynthesizer,
    BESPOKE_SYNTHESIZER_SYSTEM_PROMPT,
)


def test_canonical_tracks_constants():
    assert TRACK_ACADEMIC == "academic_breakdown"
    assert TRACK_TECH_NEWS == "tech_news"
    assert TRACK_DEVELOPER_PERKS == "developer_perks"
    assert len(CANONICAL_TRACKS) == 3
    for track in CANONICAL_TRACKS:
        assert track in TRACK_METADATA
        meta = TRACK_METADATA[track]
        assert "display_name" in meta
        assert "badge" in meta
        assert "scene_file" in meta
        assert "scene_class" in meta
        assert "default_tags" in meta
        assert "pinned_comment" in meta


def test_resolve_track_aliases():
    # Academic aliases
    assert resolve_track("academic_breakdown") == TRACK_ACADEMIC
    assert resolve_track("architecture_breakdown") == TRACK_ACADEMIC
    assert resolve_track("mechanism_deepdive") == TRACK_ACADEMIC
    assert resolve_track("model_showdown") == TRACK_ACADEMIC
    assert resolve_track("benchmark_news") == TRACK_ACADEMIC
    assert resolve_track("arxiv") == TRACK_ACADEMIC
    assert resolve_track("paper") == TRACK_ACADEMIC

    # Tech News aliases
    assert resolve_track("tech_news") == TRACK_TECH_NEWS
    assert resolve_track("news") == TRACK_TECH_NEWS
    assert resolve_track("blogs") == TRACK_TECH_NEWS
    assert resolve_track("official_blogs") == TRACK_TECH_NEWS

    # Developer Perks aliases
    assert resolve_track("developer_perks") == TRACK_DEVELOPER_PERKS
    assert resolve_track("perks") == TRACK_DEVELOPER_PERKS
    assert resolve_track("startup_credits") == TRACK_DEVELOPER_PERKS
    assert resolve_track("credits") == TRACK_DEVELOPER_PERKS

    # Fallbacks and None
    assert resolve_track(None) == TRACK_ACADEMIC
    assert resolve_track("") == TRACK_ACADEMIC
    assert resolve_track("unknown_category") == TRACK_ACADEMIC


def test_publisher_metadata_academic_track():
    spec = {
        "id": "2610.12772_reflex_humanoid",
        "title": "Reflex: Reactive Humanoid Control",
        "category": "architecture_breakdown",
        "arxiv_id": "2610.12772",
        "beats": [
            {"start": 0.0, "text": "Hook line about robotics"},
            {"start": 10.0, "text": "Beat 2"},
            {"start": 20.0, "text": "Beat 3"},
            {"start": 30.0, "text": "Beat 4"},
            {"start": 40.0, "text": "Summary line"},
            {"start": 50.0, "text": "Outro line"},
        ]
    }
    meta = generate_shorts_metadata(spec, "video.mp4")

    # Verify track badge / series in description
    assert "Academic Breakdown // PAPER BREAKDOWN" in meta["description"]
    assert "https://arxiv.org/abs/2610.12772" in meta["description"]
    # Verify no rogue DeepSeek hashtag on robotics
    assert "DeepSeek" not in meta["tags"]
    assert "#DeepSeek" not in meta["description"]
    # Verify robotics tags are present
    assert "Robotics" in meta["tags"]
    assert "Humanoid" in meta["tags"]
    assert "PaperBreakdown" in meta["tags"]
    # Verify engagement pinned comment
    assert "Will reactive visual reflex loops replace traditional trajectory planning" in meta["pinned_comment"]


def test_publisher_metadata_tech_news_track():
    spec = {
        "id": "blog_openai_dots",
        "title": "OpenAI Releases Dots System",
        "category": "tech_news",
        "canonical_url": "https://openai.com/index/introducing-dots",
        "beats": [
            {"start": 0.0, "text": "OpenAI just dropped Dots"},
            {"start": 10.0, "text": "Beat 2"},
            {"start": 20.0, "text": "Beat 3"},
            {"start": 30.0, "text": "Beat 4"},
            {"start": 40.0, "text": "Summary line"},
            {"start": 50.0, "text": "Outro line"},
        ]
    }
    meta = generate_shorts_metadata(spec, "video.mp4")

    assert "Official Tech News // TECH NEWS DISPATCH" in meta["description"]
    assert "https://openai.com/index/introducing-dots" in meta["description"]
    assert "AITechNews" in meta["tags"]
    assert "OpenAI" in meta["tags"]
    assert "DeepSeek" not in meta["tags"]
    assert "Are you testing this new release" in meta["pinned_comment"]


def test_publisher_metadata_developer_perks_track():
    spec = {
        "id": "perk_claude_startups",
        "title": "Anthropic $1,000 Claude Startup Grant",
        "category": "developer_perks",
        "claim_url": "https://anthropic.com/startups",
        "beats": [
            {"start": 0.0, "text": "Get $1,000 free Claude credits"},
            {"start": 10.0, "text": "Beat 2"},
            {"start": 20.0, "text": "Beat 3"},
            {"start": 30.0, "text": "Beat 4"},
            {"start": 40.0, "text": "Summary line"},
            {"start": 50.0, "text": "Outro line"},
        ]
    }
    meta = generate_shorts_metadata(spec, "video.mp4")

    assert "Developer Perks & Credits // DEVELOPER PERKS" in meta["description"]
    assert "https://anthropic.com/startups" in meta["description"]
    assert "DeveloperPerks" in meta["tags"]
    assert "StartupCredits" in meta["tags"]
    assert "DeepSeek" not in meta["tags"]
    assert "Did you claim this grant?" in meta["pinned_comment"]


def test_bespoke_visual_synthesizer_anti_sparsity_rules():
    synthesizer = BespokeVisualSynthesizer()
    prompt = synthesizer._construct_synthesis_prompt(
        spec={"id": "test_spec", "title": "Test Title"},
        beat={"text": "Visualizing transformer attention", "visual_focus": "attention_heads"},
        beat_idx=1
    )

    # Enforce that anti-sparsity and high-density rules are embedded
    assert "ANTI-SPARSITY INVARIANT" in BESPOKE_SYNTHESIZER_SYSTEM_PROMPT
    assert "PROGRAMMER ART" in BESPOKE_SYNTHESIZER_SYSTEM_PROMPT
    assert "Header Status Badge" in BESPOKE_SYNTHESIZER_SYSTEM_PROMPT
    assert "Technical Context Badges" in BESPOKE_SYNTHESIZER_SYSTEM_PROMPT
    assert len(prompt) > 50


def test_blueprint_paper_figure_lightbox_structure():
    from manim_engine.primitives.visual_compositions import BlueprintPaperFigure

    fig = BlueprintPaperFigure(
        title="TEST SCHEMATIC",
        sub="Testing lightbox chassis",
        arxiv_id="2610.12772",
        badge_text="FIGURE 2"
    )

    # Verify lightbox structural components
    assert hasattr(fig, "glow_chassis")
    assert hasattr(fig, "chassis")
    assert hasattr(fig, "corner_brackets")
    assert hasattr(fig, "lightbox_header")
    assert hasattr(fig, "laser_line")
    assert hasattr(fig, "badge")

    # Corner brackets should have 8 lines (4 corners x 2 lines)
    assert len(fig.corner_brackets) == 8


def test_script_driven_scene_background_and_header():
    from manim_engine.scenes.script_driven_scene import ScriptDrivenScene

    scene = ScriptDrivenScene()
    scene.spec = {
        "id": "test_spec",
        "category": "architecture_breakdown",
        "title": "Reflex Reactive Humanoid"
    }
    scene.setup_chalkboard()
    assert hasattr(scene, "dots")
    # Multi-layered background should contain coordinate grid lines, dots, and corner crosshairs
    assert len(scene.dots) >= 3

    scene.setup_header()
    assert hasattr(scene, "header_group")
    all_texts = []
    def extract_texts(mobj):
        if hasattr(mobj, "text"):
            all_texts.append(mobj.text)
        for sub in getattr(mobj, "submobjects", []):
            extract_texts(sub)
    extract_texts(scene.header_group)
    joined_text = " ".join(all_texts).upper()
    assert "MODEL" in joined_text or "VERSE" in joined_text
    assert "PAPER" in joined_text or "BREAKDOWN" in joined_text
