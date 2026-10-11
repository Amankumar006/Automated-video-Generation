"""
The Model Verse — Simulated Console Portal & Cursor Interaction Primitives
Provides vector browser chrome, console form mockups, animated cursor pointer,
and click ripple effects matching top-tier developer walkthrough Shorts.
"""

from typing import Optional, List, Dict, Any
from manim import *
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import FONT_HELVETICA
from manim_engine.primitives.typography import clean_text

COLOR_PORTAL_BG = "#0B0F19"
COLOR_PORTAL_BORDER = "#1E293B"
COLOR_PORTAL_HEADER = "#131C2E"
COLOR_ACCENT = "#38BDF8"
COLOR_MINT = "#34D399"
COLOR_FIELD_BG = "#080C14"
COLOR_FIELD_BORDER = "#334155"


def create_cursor(
    scale: float = 0.35,
    color: str = WHITE,
    stroke_color: str = "#0F172A",
    size: Optional[float] = None
) -> VGroup:
    """
    Constructs a sharp, authentic OS mouse pointer arrow polygon.
    """
    if size is not None:
        scale = size
    # Standard 7-vertex mouse pointer arrow coordinates relative to tip at (0,0)
    points = [
        [0, 0, 0],
        [0, -1.8, 0],
        [0.45, -1.4, 0],
        [0.9, -2.2, 0],
        [1.3, -2.0, 0],
        [0.85, -1.2, 0],
        [1.4, -1.2, 0],
    ]
    cursor_poly = Polygon(
        *points,
        color=stroke_color,
        fill_color=color,
        fill_opacity=1.0,
        stroke_width=2.5,
        stroke_color=stroke_color
    ).scale(scale)
    
    # Align the tip of the arrow to (0,0)
    cursor_poly.shift(-cursor_poly.get_vertices()[0])
    return VGroup(cursor_poly)


def create_click_ripple(point=ORIGIN, radius: float = 0.55, color: str = COLOR_MINT) -> Circle:
    """
    Creates an expanding glowing circular ripple ring for cursor click animations.
    """
    return Circle(
        radius=radius,
        color=color,
        stroke_width=3.0,
        stroke_opacity=0.9
    ).move_to(point)


def create_input_field(
    label: str,
    value: str = "",
    width: float = 6.4,
    height: float = 0.72,
    active: bool = False,
    accent_color: str = COLOR_ACCENT,
    placeholder: Optional[str] = None
) -> VGroup:
    """
    Constructs a stylized developer console input field.
    """
    if placeholder and not value:
        value = placeholder
    box_border = accent_color if active else COLOR_FIELD_BORDER
    box = RoundedRectangle(
        corner_radius=0.12,
        width=width,
        height=height,
        color=box_border,
        fill_color=COLOR_FIELD_BG,
        fill_opacity=0.92,
        stroke_width=1.8 if active else 1.2
    )

    lbl = clean_text(
        label,
        font=FONT_HELVETICA,
        font_size=11,
        color="#CBD5E1",
        weight=BOLD,
        max_width=width - 0.9
    )
    lbl.align_to(box, LEFT).shift(RIGHT * 0.35 + UP * 0.16)

    val = clean_text(
        value,
        font=FONT_HELVETICA,
        font_size=14,
        color=WHITE if not active else accent_color,
        weight=SEMIBOLD,
        max_width=width - 0.9
    )
    val.align_to(box, LEFT).shift(RIGHT * 0.35 + DOWN * 0.14)

    return VGroup(box, lbl, val)


def create_browser_window_mockup(
    url: str = "console.anthropic.com/startups",
    width: float = 7.4,
    height: float = 6.0,
    accent_color: str = COLOR_ACCENT,
    title: Optional[str] = None
) -> VGroup:
    """
    Constructs a sleek browser / developer console frame with traffic lights and URL bar.
    """
    window_frame = RoundedRectangle(
        corner_radius=0.18,
        width=width,
        height=height,
        color=COLOR_PORTAL_BORDER,
        fill_color=COLOR_PORTAL_BG,
        fill_opacity=0.98,
        stroke_width=1.8
    )

    # Header bar
    header_height = 0.65
    header_bar = RoundedRectangle(
        corner_radius=0.18,
        width=width,
        height=header_height,
        color=COLOR_PORTAL_BORDER,
        fill_color=COLOR_PORTAL_HEADER,
        fill_opacity=1.0,
        stroke_width=1.2
    ).align_to(window_frame, UP)

    # Traffic light window dots
    dot_red = Dot(radius=0.065, color="#EF4444").shift(LEFT * (width / 2 - 0.45))
    dot_yellow = Dot(radius=0.065, color="#F59E0B").next_to(dot_red, RIGHT, buff=0.12)
    dot_green = Dot(radius=0.065, color="#10B981").next_to(dot_yellow, RIGHT, buff=0.12)
    traffic_lights = VGroup(dot_red, dot_yellow, dot_green).move_to(header_bar).align_to(header_bar, LEFT).shift(RIGHT * 0.35)

    # URL Pill
    url_bg = RoundedRectangle(
        corner_radius=0.08,
        width=width - 2.4,
        height=0.38,
        color="#334155",
        fill_color="#080C14",
        fill_opacity=0.95,
        stroke_width=1.0
    ).move_to(header_bar).shift(RIGHT * 0.5)

    # Procedural lock icon (crisp vector HTTPS padlock)
    lock_body = RoundedRectangle(corner_radius=0.02, width=0.14, height=0.11, color="#10B981", fill_color="#10B981", fill_opacity=0.9, stroke_width=0.8)
    lock_shackle = Arc(radius=0.05, start_angle=0, angle=PI, color="#10B981", stroke_width=1.2).next_to(lock_body, UP, buff=0.01)
    lock_icon = VGroup(lock_body, lock_shackle).move_to(url_bg).align_to(url_bg, LEFT).shift(RIGHT * 0.18)

    url_txt = clean_text(url, font=FONT_HELVETICA, font_size=11, color="#CBD5E1", weight=MEDIUM, max_width=url_bg.width - 0.7)
    url_txt.next_to(lock_icon, RIGHT, buff=0.12)
    url_txt.match_y(url_bg)

    url_bar = VGroup(url_bg, lock_icon, url_txt)
    return VGroup(window_frame, header_bar, traffic_lights, url_bar)
