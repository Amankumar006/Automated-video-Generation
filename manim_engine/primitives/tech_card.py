"""
Visual Primitives: Tech Cards, Badges, and Formula Containers
"""

from manim import *
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from pipeline.config import FONT_HELVETICA, COLOR_CARD_BG, COLOR_CARD_BORDER, COLOR_MINT

def create_tech_card(
    width: float = 7.4,
    height: float = 1.1,
    border_color: str = COLOR_CARD_BORDER,
    fill_color: str = COLOR_CARD_BG,
    fill_opacity: float = 0.95,
    stroke_width: float = 1.8,
    corner_radius: float = 0.16
) -> RoundedRectangle:
    """Returns a clean tech container card."""
    return RoundedRectangle(
        corner_radius=corner_radius,
        width=width,
        height=height,
        color=border_color,
        fill_color=fill_color,
        fill_opacity=fill_opacity,
        stroke_width=stroke_width
    )

def create_badge(
    text: str,
    border_color: str = COLOR_MINT,
    fill_color: str = "#064E3B",
    text_color: str = "#A7F3D0",
    font_size: int = 16,
    width: float = 3.6,
    height: float = 0.55
) -> VGroup:
    """Returns a status badge pill with text."""
    box = RoundedRectangle(
        corner_radius=0.12,
        width=width,
        height=height,
        color=border_color,
        fill_color=fill_color,
        fill_opacity=0.45,
        stroke_width=1.5
    )
    label = Text(text, font=FONT_HELVETICA, font_size=font_size, color=text_color, weight=BOLD).move_to(box)
    return VGroup(box, label)

def create_formula_card(
    formula_parts: list,
    width: float = 7.0,
    height: float = 0.70,
    border_color: str = COLOR_MINT
) -> VGroup:
    """Creates a color-coded mathematical formula box."""
    card = create_tech_card(width=width, height=height, border_color=border_color, stroke_width=2.0)
    formula_group = VGroup(*formula_parts).arrange(RIGHT, buff=0.06).move_to(card)
    return VGroup(card, formula_group)
