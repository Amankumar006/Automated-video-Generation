"""Focused regression tests for source-aware publishing and thumbnails."""

from pathlib import Path

from PIL import Image

from pipeline.publisher import generate_shorts_metadata
from pipeline.thumbnail_generator import ShortsThumbnailGenerator, _explicit_thumbnail_content


def test_publisher_keeps_current_topic_and_does_not_invent_source_or_old_claims():
    spec = {
        "id": "kimi_k3_1_pro",
        "title": "Kimi K3.1 Pro: one million token context",
        "category": "tech_news",
        "beats": [{"start": 0, "text": "Kimi K3.1 Pro expands the context window."}],
    }

    result = generate_shorts_metadata(spec, "video.mp4")

    assert result["title"].startswith("Kimi K3.1 Pro")
    assert "Kimi" in result["tags"]
    assert "Source Link: https://themodelverse.in" not in result["description"]
    assert "DeepSeek-R1" not in result["title"]
    assert "OpenAI o1" not in result["title"]
    assert "1.2 PFLOPS" not in result["title"]
    assert "source_url" not in result


def test_publisher_preserves_explicit_provenance_and_topic_tags():
    spec = {
        "id": "mercury_3",
        "title": "Mercury 3 diffusion language model",
        "category": "tech_news",
        "canonical_url": "https://example.com/mercury-3",
        "source_provider": "Inception Labs",
        "model_name": "Mercury 3",
        "tts_provider": "pocket",
        "beats": [{"start": 0, "text": "Mercury 3 uses diffusion language modeling."}],
    }

    result = generate_shorts_metadata(spec, "video.mp4")

    assert result["source_url"] == "https://example.com/mercury-3"
    assert result["provider"] == "Inception Labs"
    assert result["model"] == "Mercury 3"
    assert result["tts_provider"] == "pocket"
    assert "https://example.com/mercury-3" in result["description"]
    assert "Inception Labs" in result["description"]
    assert "Mercury 3" in result["description"]
    assert "DiffusionModels" in result["tags"]
    assert "GenerativeAI" in result["tags"]


def test_thumbnail_content_never_uses_historical_metric_defaults():
    content = _explicit_thumbnail_content(
        {"id": "new_topic", "title": "A new model release", "category": "benchmark_news"}
    )

    assert content["badge"] == "TOPIC BREAKDOWN"
    assert content["stat_value_1"] == "NOT PROVIDED"
    assert content["stat_value_2"] == "NOT PROVIDED"
    assert "OpenAI" not in " ".join(content.values())
    assert "79.8" not in " ".join(content.values())
    assert "15.00" not in " ".join(content.values())


def test_thumbnail_content_uses_only_explicit_stats_and_model():
    content = _explicit_thumbnail_content(
        {
            "id": "kimi_k3_1_pro",
            "title": "Kimi K3.1 Pro",
            "model_name": "Kimi K3.1 Pro",
            "provider": "Moonshot AI",
            "metadata": {
                "payoff_label": "CONTEXT",
                "payoff_stat": "1M TOKENS",
            },
        }
    )

    assert content["badge"] == "1M TOKENS CONTEXT"
    assert content["stat_label_1"] == "CONTEXT"
    assert content["stat_value_1"] == "1M TOKENS"
    assert content["stat_label_2"] == "MODEL"
    assert content["stat_value_2"] == "Kimi K3.1 Pro"
    assert content["provider"] == "Moonshot AI"


def test_thumbnail_content_preserves_top_level_source_provenance():
    content = _explicit_thumbnail_content(
        {
            "id": "geniex",
            "title": "GenieX edge-native inference",
            "category": "mechanism_deepdive",
            "source_url": "https://github.com/qualcomm/GenieX",
            "source_provider": "github",
        }
    )

    assert content["source_label"] == "github.com"


def test_thumbnail_generates_without_unrelated_formula_or_metrics(tmp_path):
    output = tmp_path / "poster.png"
    spec = {"id": "new_topic", "title": "A new model release", "category": "benchmark_news"}

    generated = ShortsThumbnailGenerator().generate(spec, output_path=str(output))

    assert Path(generated) == output
    assert output.exists()
    assert Image.open(output).size == (1080, 1920)
    assert output.with_suffix(".jpg").exists()
