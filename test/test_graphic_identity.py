"""Tests for the shared topic-seeded broadcast identity layer."""

from manim_engine.primitives.graphic_identity import (
    create_graphic_identity_overlay,
    theme_for_spec,
)


def test_identity_theme_is_stable_for_the_same_video():
    spec = {
        "id": "speculative_decoding",
        "title": "Speculative Decoding",
        "category": "academic_breakdown",
        "domain_taxonomy": "hardware_efficiency",
    }

    first = theme_for_spec(spec)
    second = theme_for_spec(dict(spec))

    assert first == second
    assert first.seed
    assert first.accent.startswith("#")


def test_identity_themes_can_vary_by_topic_without_randomness():
    themes = {
        theme_for_spec(
            {
                "title": f"Topic {idx}",
                "category": "academic_breakdown",
                "domain_taxonomy": "frontier_ai",
            }
        ).name
        for idx in range(12)
    }

    assert len(themes) >= 3


def test_identity_overlay_has_safe_geometry_and_beat_state():
    overlay = create_graphic_identity_overlay(
        {
            "title": "KV Cache Paging",
            "category": "academic_breakdown",
            "domain_taxonomy": "hardware_efficiency",
        },
        total_beats=6,
    )

    assert overlay.width < 8.0
    assert overlay.height < 9.0
    assert overlay.get_z_index() == 2

    overlay.update_beat(3, "grid_memory")

    assert overlay.current_beat == 3
    assert overlay.current_beat_label == "BEAT 03/06"
    assert len(overlay.progress_ticks) == 6


def test_identity_overlay_exposes_seek_safe_motion_hooks():
    overlay = create_graphic_identity_overlay({"title": "A New Topic"}, total_beats=4)

    assert overlay.get_entrance_animation(run_time=0.2) is not None
    assert overlay.get_beat_animation(run_time=0.2) is not None
    assert overlay.get_ambient_animation(run_time=0.2) is not None
