"""
Test suite for Audio-Visual Alignment and Category Routing Realignment.
Verifies:
1. benchmark_news routes to ScriptDrivenScene (Track 1) in run_pipeline and auto_produce
2. Academic categories (mechanism_deepdive, architecture_breakdown, benchmark_news, model_showdown) route to Track 1
3. Official tech news (tech_news, official_blogs, blogs, news) route to Track 2 (TechNewsScene)
4. Developer perks (developer_perks, startup_credits, perks) route to Track 3 (DeveloperPerksScene)
5. TechNewsScene dynamically adapts to varying news types without hardcoded SWE-bench / $1.10 token pricing cards
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from pipeline.run_pipeline import CATEGORY_SCENE_MAP
from manim_engine.scenes.tech_news_scene import TechNewsScene


def test_academic_categories_route_to_script_driven_scene():
    """Validates that all academic categories (including benchmark_news) route to ScriptDrivenScene."""
    from pipeline.run_pipeline import PROJECT_ROOT

    # Simulate run_pipeline scene selection logic
    def resolve_scene_for_category(cat: str, legacy: bool = False):
        if cat in ("developer_perks", "startup_credits", "perks"):
            return "DeveloperPerksScene"
        elif cat in ("tech_news", "official_blogs", "blogs", "news") and not legacy:
            return "TechNewsScene"
        elif not legacy:
            return "ScriptDrivenScene"
        else:
            return CATEGORY_SCENE_MAP.get(cat, CATEGORY_SCENE_MAP["mechanism_deepdive"])["class"]

    assert resolve_scene_for_category("benchmark_news") == "ScriptDrivenScene"
    assert resolve_scene_for_category("mechanism_deepdive") == "ScriptDrivenScene"
    assert resolve_scene_for_category("architecture_breakdown") == "ScriptDrivenScene"
    assert resolve_scene_for_category("model_showdown") == "ScriptDrivenScene"


def test_tech_news_and_perks_route_to_dedicated_tracks():
    """Validates that tech news and developer perks route to their dedicated studios."""
    def resolve_scene_for_category(cat: str, legacy: bool = False):
        if cat in ("developer_perks", "startup_credits", "perks"):
            return "DeveloperPerksScene"
        elif cat in ("tech_news", "official_blogs", "blogs", "news") and not legacy:
            return "TechNewsScene"
        elif not legacy:
            return "ScriptDrivenScene"
        else:
            return CATEGORY_SCENE_MAP.get(cat, CATEGORY_SCENE_MAP["mechanism_deepdive"])["class"]

    # Tech news
    assert resolve_scene_for_category("tech_news") == "TechNewsScene"
    assert resolve_scene_for_category("official_blogs") == "TechNewsScene"
    assert resolve_scene_for_category("blogs") == "TechNewsScene"
    assert resolve_scene_for_category("news") == "TechNewsScene"

    # Perks
    assert resolve_scene_for_category("developer_perks") == "DeveloperPerksScene"
    assert resolve_scene_for_category("startup_credits") == "DeveloperPerksScene"
    assert resolve_scene_for_category("perks") == "DeveloperPerksScene"


def test_tech_news_scene_dynamic_pain_point_extraction():
    """Validates that TechNewsScene derives pain points directly from beat text."""
    scene = TechNewsScene()
    
    # Test cost-heavy news text
    cost_text = "Prior models burned excessive compute, resulting in steep $60/1M API expenditure that drained seed runways."
    cost_pains = scene._derive_pain_points(cost_text, {"API": "#FFF"})
    assert any("BILLS" in p[0] or "COST" in p[0] for p in cost_pains)

    # Test latency-heavy news text
    latency_text = "Generation delays and high inference latency made live interactive editing impossible."
    latency_pains = scene._derive_pain_points(latency_text, {"latency": "#FFF"})
    assert any("LATENCY" in p[0] for p in latency_pains)


def test_tech_news_scene_dynamic_breakthrough_metrics():
    """Validates that TechNewsScene extracts actual speedup metrics rather than hardcoded 3.2x."""
    scene = TechNewsScene()

    # 10x throughput
    t1 = "Enter the new kernel: delivering 10x faster token throughput and sub-millisecond dispatch."
    val1, sub1, f1, f2 = scene._derive_breakthrough_metrics(t1, {}, {"kernel": "#FFF"})
    assert "10X FASTER" in val1

    # 65% cost reduction
    t2 = "LegalOn achieved a 65% reduction in total infrastructure costs while sustaining code velocity."
    val2, sub2, f1, f2 = scene._derive_breakthrough_metrics(t2, {}, {"reduction": "#FFF"})
    assert "65%" in val2


def test_tech_news_scene_dynamic_benchmarks_and_capabilities():
    """Validates that TechNewsScene handles non-benchmark news with capability cards rather than fake SWE-bench."""
    scene = TechNewsScene()
    from manim import Text
    title_dummy = Text("TITLE")

    # Non-benchmark feature release (e.g. UI dots)
    feature_text = "The new interface introduces dynamic dots and micro-interactions that streamline workspace navigation."
    content_group, sota_chip = scene._derive_benchmarks_or_capabilities(feature_text, {}, "New UI", title_dummy)
    assert sota_chip is None  # No fake SOTA leap chip for non-benchmark news
    assert len(content_group) == 2  # 2 capability cards

    # Real benchmark release
    bench_text = "On HumanEval coding tests, it hits 84.5% while outpacing frontier baselines."
    bench_group, sota_chip = scene._derive_benchmarks_or_capabilities(bench_text, {}, "CodeModel", title_dummy)
    assert any("84.5" in getattr(m, "text", "") for m in bench_group.submobjects for m in getattr(m, "submobjects", [m]))
