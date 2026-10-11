"""
Unit tests for High-Precision Typographic Primitives and Kerning Fixes.
"""

import pytest
from manim import *
from manim_engine.primitives.typography import CleanText, clean_text, fit_text_to_container
from pipeline.config import FONT_HELVETICA


def test_font_helvetica_is_helvetica_neue():
    """Verify default typography token is upgraded to Helvetica Neue."""
    assert FONT_HELVETICA == "Helvetica Neue"


def test_clean_text_initialization_and_scaling():
    """Verify clean_text initializes at base 36 and scales down without distortion."""
    t_small = clean_text("Test Typography", font_size=12, base_size=36.0)
    assert t_small is not None
    # Verify it has dimensions
    assert t_small.width > 0
    assert t_small.height > 0

    t_large = clean_text("Test Typography", font_size=36, base_size=36.0)
    # The 12pt text should have roughly 1/3 the width of 36pt text
    ratio = t_small.width / t_large.width
    assert pytest.approx(ratio, rel=1e-2) == (12.0 / 36.0)


def test_clean_text_max_width_constraint():
    """Verify clean_text automatically clamps text within max_width."""
    max_w = 4.0
    long_str = "A very long headline that definitely exceeds four manim coordinate units"
    t = clean_text(long_str, font_size=20, max_width=max_w)
    assert t.width <= max_w + 1e-4


def test_clean_text_max_height_constraint():
    """Verify clean_text clamps height within max_height."""
    max_h = 1.0
    multi_line = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
    t = clean_text(multi_line, font_size=28, max_height=max_h)
    assert t.height <= max_h + 1e-4


def test_clean_text_auto_wrapping():
    """Verify wrap_width automatically introduces line breaks."""
    raw = "The quick brown fox jumps over the lazy dog repeatedly without stop"
    t = clean_text(raw, font_size=14, wrap_width=20)
    assert t.height > 0.4  # Multi-line text is taller than a single line


def test_clean_text_t2c_coloring():
    """Verify t2c word highlighting works with clean_text."""
    t = clean_text("Attention Is All You Need", font_size=16, t2c={"Attention": RED})
    assert t is not None
    assert len(t.submobjects) > 0


def test_fit_text_to_container():
    """Verify fit_text_to_container resizes text to fit inside container with padding."""
    container = Rectangle(width=4.0, height=2.0)
    t = clean_text("Extremely long text that needs to fit inside the container", font_size=30)
    fitted = fit_text_to_container(t, container, padding=0.25)
    assert fitted.width <= container.width - 2 * 0.25 + 1e-4
    assert fitted.height <= container.height - 2 * 0.25 + 1e-4
