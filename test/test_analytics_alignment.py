"""
The Model Verse — Tests for YouTube Analytics Retention Alignment & Daemon Calibration
Validates taxonomy classification, multiplier weighting, and slot-aware candidate ranking.
"""

import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.analytics_feedback import (
    classify_content_taxonomy,
    get_performance_category_bias,
    TAXONOMY_KEYWORDS
)
from pipeline.batch_digest import score_and_classify_paper
from pipeline.daily_shorts_daemon import (
    SLOT_SCHEDULE,
    evaluate_pedagogical_viability
)


def test_classify_content_taxonomy():
    """Validates that titles and abstracts correctly map to research taxonomies."""
    # Multimodal Diffusion
    assert classify_content_taxonomy(
        title="Multimodal Flow: Unified Flow Modeling of Language and Vision",
        text="A generative diffusion framework for video synthesis and flow matching."
    ) == "multimodal_diffusion"

    assert classify_content_taxonomy(
        title="FlashForward: Ultra-Fast Video Generation with Diffusion Transformers",
        text="Generates high-resolution video frames using latent diffusion."
    ) == "multimodal_diffusion"

    # Hardware Efficiency
    assert classify_content_taxonomy(
        title="Prefill-Free Cross-Family KV Cache Transfer for LLMs",
        text="Reduces VRAM bandwidth and latency with speculative decoding and cache compression."
    ) == "hardware_efficiency"

    assert classify_content_taxonomy(
        title="FP4 Quantization for CUDA Kernels on Modern GPUs",
        text="Accelerates throughput and eliminates memory bottlenecks."
    ) == "hardware_efficiency"

    # Robotics TAMP
    assert classify_content_taxonomy(
        title="Kinematic Motion Planning for Humanoid Robot Manipulation",
        text="Solving C-space trajectories using embodied TAMP planners."
    ) == "robotics_tamp"

    # Mechanistic Interpretability
    assert classify_content_taxonomy(
        title="Sparse Autoencoders Reveal Monosemantic Circuits in Transformer Residual Streams",
        text="Extracting interpretable features and steering vectors."
    ) == "mechanistic_interpretability"

    # Reasoning Models
    assert classify_content_taxonomy(
        title="DeepSeek-R1: Reinforcement Learning for Mathematical Reasoning",
        text="Incentivizing chain-of-thought proofs with GRPO rewards."
    ) == "reasoning_models"

    # Fallback
    assert classify_content_taxonomy(
        title="A Survey of Academic Literature Indexing",
        text="Discussion of historical citation practices."
    ) == "general_breakthroughs"


def test_score_and_classify_paper_multiplier_scaling(monkeypatch):
    """Validates that category multipliers scale impact_score mathematically."""
    fake_biases = {
        "multimodal_diffusion": 1.29,
        "hardware_efficiency": 1.19,
        "reasoning_models": 0.60
    }
    monkeypatch.setattr("pipeline.batch_digest.get_performance_category_bias", lambda: fake_biases)

    diffusion_paper = {
        "id": "2610.99991",
        "title": "Diffusion Transformer Flow Matching",
        "abstract": "Novel video generation and image synthesis model.",
        "upvotes": 5
    }
    scored_diff = score_and_classify_paper(diffusion_paper)
    assert scored_diff["taxonomy"] == "multimodal_diffusion"
    assert scored_diff["analytics_multiplier"] == 1.29
    assert scored_diff["impact_score"] == round(scored_diff["raw_impact_score"] * 1.29, 1)

    reasoning_paper = {
        "id": "2610.99992",
        "title": "DeepSeek-R1 Reasoning Benchmark Benchmark News",
        "abstract": "Chain of thought reinforcement learning with math reasoning.",
        "upvotes": 5
    }
    scored_reas = score_and_classify_paper(reasoning_paper)
    assert scored_reas["taxonomy"] == "reasoning_models"
    assert scored_reas["analytics_multiplier"] == 0.60
    assert scored_reas["impact_score"] == round(scored_reas["raw_impact_score"] * 0.60, 1)


def test_slot_schedule_calibration():
    """Ensures the 5 automated daily upload windows are properly configured."""
    assert len(SLOT_SCHEDULE) == 5
    expected_hours = [1, 5, 9, 12, 16]
    assert sorted(list(SLOT_SCHEDULE.keys())) == expected_hours

    # Window 1 and 3 favor multimodal_diffusion
    assert SLOT_SCHEDULE[1]["preferred_taxonomy"] == "multimodal_diffusion"
    assert SLOT_SCHEDULE[9]["preferred_taxonomy"] == "multimodal_diffusion"

    # Window 2 and 4 favor hardware_efficiency
    assert SLOT_SCHEDULE[5]["preferred_taxonomy"] == "hardware_efficiency"
    assert SLOT_SCHEDULE[12]["preferred_taxonomy"] == "hardware_efficiency"


def test_evaluate_pedagogical_viability_fallback_prioritization(monkeypatch):
    """Validates that candidate fallback selects preferred taxonomy and high-multiplier candidates."""
    # Force fallback by clearing GEMINI_API_KEY
    monkeypatch.setenv("GEMINI_API_KEY", "")

    candidates = [
        {
            "id": "cand_reas",
            "title": "Lagging Reasoning Paper",
            "taxonomy": "reasoning_models",
            "analytics_multiplier": 0.60,
            "raw_impact_score": 70.0,
            "impact_score": 42.0,
            "abstract": "..."
        },
        {
            "id": "cand_diff",
            "title": "Viral Diffusion Paper",
            "taxonomy": "multimodal_diffusion",
            "analytics_multiplier": 1.29,
            "raw_impact_score": 40.0,
            "impact_score": 51.6,
            "abstract": "..."
        },
        {
            "id": "cand_hw",
            "title": "KV Cache Compression Paper",
            "taxonomy": "hardware_efficiency",
            "analytics_multiplier": 1.19,
            "raw_impact_score": 45.0,
            "impact_score": 53.5,
            "abstract": "..."
        }
    ]

    # Without preferred_taxonomy: high-velocity candidates outrank lagging paper
    selected = evaluate_pedagogical_viability(candidates, count=2)
    selected_ids = [c["id"] for c in selected]
    assert selected_ids == ["cand_hw", "cand_diff"]
    assert "cand_reas" not in selected_ids

    # With preferred_taxonomy="multimodal_diffusion": cand_diff prioritized first
    selected_slot1 = evaluate_pedagogical_viability(candidates, count=1, preferred_taxonomy="multimodal_diffusion")
    assert selected_slot1[0]["id"] == "cand_diff"

    # With preferred_taxonomy="hardware_efficiency": cand_hw prioritized first
    selected_slot2 = evaluate_pedagogical_viability(candidates, count=1, preferred_taxonomy="hardware_efficiency")
    assert selected_slot2[0]["id"] == "cand_hw"
