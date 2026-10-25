"""Focused tests for tech-news mechanism-to-blueprint routing."""

from pipeline.visual_director import VisualDirector


def _tech_news_spec():
    return {
        "category": "tech_news",
        "title": "Introducing Kimi K3.1 Pro",
        "beats": [
            {
                "beat_id": 1,
                "text": "The release is live: the lab dropped a new model.",
                "visual_focus": "Official release and production availability.",
                "svo_action": {"subject": "Moonshot AI", "action_verb": "launches", "direct_object": "Kimi K3.1 Pro"},
                "visual_blueprint": {"layout": "news_hero_announcement", "title": "MODEL IS LIVE"},
            },
            {
                "beat_id": 2,
                "text": "Earlier models hit latency and price ceilings.",
                "visual_focus": "The predecessor bottleneck.",
                "svo_action": {"subject": "Predecessors", "action_verb": "hit", "direct_object": "latency ceilings"},
                "visual_blueprint": {"layout": "news_predecessor_ceiling", "title": "THE OLD CEILING"},
            },
            {
                "beat_id": 3,
                "text": "The new stack uses post-training compute and agent loops.",
                "visual_focus": "The architectural breakthrough.",
                "svo_action": {"subject": "Kimi", "action_verb": "delivers", "direct_object": "frontier intelligence"},
                "visual_blueprint": {"layout": "news_breakthrough_architecture", "title": "THE NEW ENGINE"},
            },
            {
                "beat_id": 4,
                "text": "Verified benchmarks show the new model ahead of baselines.",
                "visual_focus": "Measured benchmark comparison.",
                "svo_action": {"subject": "Kimi", "action_verb": "beats", "direct_object": "frontier baselines"},
                "visual_blueprint": {"layout": "news_benchmark_clash", "title": "VERIFIED RESULTS"},
            },
            {
                "beat_id": 5,
                "text": "Pricing is lower and the API is available now.",
                "visual_focus": "Pricing and access tiers.",
                "svo_action": {"subject": "Moonshot AI", "action_verb": "slashes", "direct_object": "token prices"},
                "visual_blueprint": {"layout": "news_pricing_table", "title": "ACCESS NOW"},
            },
        ],
    }


def test_tech_news_beats_use_distinct_mechanism_blueprints():
    spec = VisualDirector().prepare_storyboard_for_spec(_tech_news_spec(), allow_figure_extraction=False)

    layouts = [beat["visual_blueprint"]["layout"] for beat in spec["beats"]]

    assert layouts == [
        "pipeline_stages",
        "comparison_side_by_side",
        "layer_stack",
        "horizontal_race_bars",
        "catalog_routing",
    ]
    assert len(layouts) == len(set(layouts))
    assert all(beat["motif_params"]["layout"] == beat["visual_blueprint"]["layout"] for beat in spec["beats"])


def test_tech_news_pricing_beat_does_not_become_benchmark():
    spec = VisualDirector().prepare_storyboard_for_spec(_tech_news_spec(), allow_figure_extraction=False)
    pricing_beat = spec["beats"][-1]

    assert pricing_beat["visual_blueprint"]["layout"] == "catalog_routing"
    assert pricing_beat["motif_params"]["drawer_c_label"] == "AVAILABLE NOW"


def test_tech_news_blueprints_expose_semantic_roles():
    spec = VisualDirector().prepare_storyboard_for_spec(_tech_news_spec(), allow_figure_extraction=False)

    roles = [beat["visual_blueprint"]["semantic_role"] for beat in spec["beats"]]

    assert roles == ["launch", "context_speed", "training_loop", "benchmark", "availability"]
