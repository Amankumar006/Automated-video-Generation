"""
The Model Verse — Unit Tests for Code Sandbox Programmatic Collision Gate & Safe-Zone Enforcement
Verifies that:
1. Known overlapping code snippets (e.g. from Heretic beats 2, 4, 5) are deterministically rejected.
2. Direct text-text collisions and label-shape clashes trigger detailed diagnostics.
3. 9:16 safe-zone intrusions (subtitles y < -2.45, top bar y > 6.00) are caught.
4. Clean, atomic-paired Manim visual code and all 6 grammar fallbacks pass cleanly.
"""

import pytest
from pathlib import Path
from pipeline.code_sandbox import (
    validate_synthesized_visual_code,
    check_mobject_collisions_and_bounds,
)
from pipeline.bespoke_visual_synthesizer import _fallback_visual_code

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_heretic_beat2_caught_by_collision_gate():
    """Verify that Beat 2 (where .arrange() detached bars from labels) is rejected."""
    beat2_path = (
        PROJECT_ROOT
        / "manim_engine"
        / "generated"
        / "heretic_model_modification"
        / "544b1a52eab2"
        / "beat_2.py"
    )
    if not beat2_path.exists():
        pytest.skip("beat_2.py fixture not found")

    with open(beat2_path, "r", encoding="utf-8") as f:
        code = f.read()

    is_valid, err = validate_synthesized_visual_code(code)
    assert not is_valid, "Beat 2 with detached labels should be rejected by collision gate"
    assert "Collision" in err or "collides" in err
    assert "StandardLLM" in err or "Rectangle" in err


def test_heretic_beat4_caught_by_collision_gate():
    """Verify that Beat 4 (lattice line passing directly through text) is rejected."""
    beat4_path = (
        PROJECT_ROOT
        / "manim_engine"
        / "generated"
        / "heretic_model_modification"
        / "544b1a52eab2"
        / "beat_4.py"
    )
    if not beat4_path.exists():
        pytest.skip("beat_4.py fixture not found")

    with open(beat4_path, "r", encoding="utf-8") as f:
        code = f.read()

    is_valid, err = validate_synthesized_visual_code(code)
    assert not is_valid, "Beat 4 with line-text collision should be rejected"
    assert "Collision" in err or "collides" in err


def test_heretic_beat5_caught_by_collision_gate():
    """Verify that Beat 5 (circle perimeter cutting through text) is rejected."""
    beat5_path = (
        PROJECT_ROOT
        / "manim_engine"
        / "generated"
        / "heretic_model_modification"
        / "544b1a52eab2"
        / "beat_5.py"
    )
    if not beat5_path.exists():
        pytest.skip("beat_5.py fixture not found")

    with open(beat5_path, "r", encoding="utf-8") as f:
        code = f.read()

    is_valid, err = validate_synthesized_visual_code(code)
    assert not is_valid, "Beat 5 with circle-text collision should be rejected"
    assert "Collision" in err or "collides" in err


def test_clean_atomic_grouped_bars_pass():
    """Verify that properly atomic-paired grouped bars pass collision validation."""
    clean_code = """
from manim import *
import numpy as np
from manim_engine.primitives.typography import CleanText

class BespokeBeatVisual(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Bar 1 with atomic label
        bar_base = Rectangle(width=0.6, height=1.8, fill_opacity=0.6, color="#475569")
        lbl_base = CleanText("Standard LLM", font_size=16, color="#94A3B8").next_to(bar_base, UP, buff=0.15)
        col_base = VGroup(bar_base, lbl_base)

        # Bar 2 with atomic label
        bar_hero = Rectangle(width=0.6, height=3.6, fill_opacity=0.8, color="#3B82F6")
        lbl_hero = CleanText("Heretic-Enabled", font_size=16, color="#3B82F6").next_to(bar_hero, UP, buff=0.15)
        col_hero = VGroup(bar_hero, lbl_hero)

        # Safely arrange paired columns
        self.plot_group = VGroup(col_base, col_hero).arrange(RIGHT, buff=1.4, aligned_edge=DOWN)
        self.plot_group.move_to(ORIGIN + UP * 0.8)

        self.add(self.plot_group)

    def get_entrance_animation(self, run_time: float = 1.0) -> Animation:
        return FadeIn(self.plot_group, run_time=run_time)

    def get_kinetic_animation(self, run_time: float = 1.0) -> Animation:
        return self.plot_group[1][0].animate.set_fill(opacity=1.0).set_color("#FFFFFF")
"""
    is_valid, err = validate_synthesized_visual_code(clean_code)
    assert is_valid, f"Clean atomic bars should pass, but failed with: {err}"
    assert err is None


def test_text_text_collision_detected():
    """Verify that two overlapping text labels at the same coordinates are rejected."""
    overlapping_texts = """
from manim import *
import numpy as np
from manim_engine.primitives.typography import CleanText

class BespokeBeatVisual(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Two text labels at the exact same location
        self.txt1 = CleanText("Standard Model", font_size=20, color="#FFFFFF").move_to(ORIGIN + UP * 0.8)
        self.txt2 = CleanText("Heretic Model", font_size=20, color="#38BDF8").move_to(ORIGIN + UP * 0.8)
        self.rect = Rectangle(width=2.0, height=1.0).move_to(ORIGIN + DOWN * 0.5)

        self.add(self.txt1, self.txt2, self.rect)

    def get_entrance_animation(self, run_time: float = 1.0) -> Animation:
        return FadeIn(self.txt1, run_time=run_time)

    def get_kinetic_animation(self, run_time: float = 1.0) -> Animation:
        return FadeIn(self.txt2, run_time=run_time)
"""
    is_valid, err = validate_synthesized_visual_code(overlapping_texts)
    assert not is_valid, "Overlapping text labels should be rejected"
    assert "Text Collision" in err


def test_subtitle_safe_zone_breach_detected():
    """Verify that visual mobjects dropping into the kinetic subtitle safe zone (y < -2.45) are rejected."""
    breaching_code = """
from manim import *
import numpy as np
from manim_engine.primitives.typography import CleanText

class BespokeBeatVisual(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Positioned too low, colliding with subtitles at y = -3.45
        self.box = Rectangle(width=3.0, height=2.0, color="#38BDF8").move_to(ORIGIN + DOWN * 2.5)
        self.lbl = CleanText("Low Card", font_size=18, color="#FFFFFF").move_to(self.box.get_center())

        self.add(self.box, self.lbl)

    def get_entrance_animation(self, run_time: float = 1.0) -> Animation:
        return FadeIn(self.box, run_time=run_time)

    def get_kinetic_animation(self, run_time: float = 1.0) -> Animation:
        return self.box.animate.scale(1.1)
"""
    is_valid, err = validate_synthesized_visual_code(breaching_code)
    assert not is_valid, "Visual dropping below -2.45 should be rejected"
    assert "Safe-Zone Breach" in err
    assert "subtitles" in err.lower()


def test_top_bar_safe_zone_breach_detected():
    """Verify that visual mobjects pushing above y = 6.00 are rejected."""
    breaching_code = """
from manim import *
import numpy as np
from manim_engine.primitives.typography import CleanText

class BespokeBeatVisual(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Positioned too high, colliding with top header watermark
        self.box = Rectangle(width=3.0, height=2.0, color="#38BDF8").move_to(ORIGIN + UP * 5.5)
        self.lbl = CleanText("High Card", font_size=18, color="#FFFFFF").move_to(self.box.get_center())

        self.add(self.box, self.lbl)

    def get_entrance_animation(self, run_time: float = 1.0) -> Animation:
        return FadeIn(self.box, run_time=run_time)

    def get_kinetic_animation(self, run_time: float = 1.0) -> Animation:
        return self.box.animate.scale(1.1)
"""
    is_valid, err = validate_synthesized_visual_code(breaching_code)
    assert not is_valid, "Visual rising above 6.00 should be rejected"
    assert "Safe-Zone Breach" in err
    assert "top header" in err.lower()


def test_container_overflow_detected():
    """Verify that text wider than its container box is rejected."""
    overflow_code = """
from manim import *
import numpy as np
from manim_engine.primitives.typography import CleanText

class BespokeBeatVisual(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Tiny container with huge text
        self.box = RoundedRectangle(width=1.0, height=0.5, color="#38BDF8").move_to(ORIGIN + UP * 0.8)
        self.lbl = CleanText("Extremely Wide Explanation Label", font_size=24, color="#FFFFFF").move_to(self.box.get_center())

        self.add(self.box, self.lbl)

    def get_entrance_animation(self, run_time: float = 1.0) -> Animation:
        return FadeIn(self.box, run_time=run_time)

    def get_kinetic_animation(self, run_time: float = 1.0) -> Animation:
        return self.box.animate.scale(1.1)
"""
    is_valid, err = validate_synthesized_visual_code(overflow_code)
    assert not is_valid, "Container overflow should be rejected"
    assert "Container Overflow" in err or "overflow" in err.lower()


def test_all_six_fallback_grammars_pass_collision_and_bounds_gate():
    """Verify that all 6 grammar-specific fallback safety modules pass collision & safe-zone checks."""
    spec = {
        "title": "Heretic AI Model Modification",
        "beats": [{"text": f"Beat {i}"} for i in range(6)],
    }
    for grammar_idx in range(6):
        beat = {"text": "Hello world", "visual_focus": "surgical edit"}
        code = _fallback_visual_code(spec, beat, grammar_idx)
        is_valid, err = validate_synthesized_visual_code(code)
        assert is_valid, f"Grammar {grammar_idx} fallback failed validation: {err}"
        assert err is None
