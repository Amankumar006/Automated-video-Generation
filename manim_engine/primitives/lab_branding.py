"""
The Model Verse — Official AI Lab Branding & Vector Logos
Clean procedural vector emblems for leading frontier research labs:
- OpenAI
- Anthropic (Claude)
- Google DeepMind
- Hugging Face
- GitHub
"""

import math
from typing import Optional
from manim import *
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import FONT_HELVETICA
from manim_engine.primitives.typography import clean_text

COLOR_OPENAI = "#10A37F"
COLOR_ANTHROPIC = "#D97706"
COLOR_DEEPMIND = "#4285F4"
COLOR_HUGGINGFACE = "#FFD21E"
COLOR_GITHUB = "#E2E8F0"
COLOR_BG_CARD = "#0B101B"
COLOR_BORDER = "#1E293B"


def create_openai_logo(size: float = 1.0, color: str = COLOR_OPENAI) -> VGroup:
    """
    Creates a clean geometric vector representation of the OpenAI emblem.
    Constructed using interlocking rounded segments radiating from center.
    """
    spokes = []
    num_petals = 6
    radius = size * 0.45
    for i in range(num_petals):
        angle = i * (2 * math.pi / num_petals)
        start = np.array([math.cos(angle) * (radius * 0.35), math.sin(angle) * (radius * 0.35), 0])
        end = np.array([math.cos(angle + 0.5) * radius, math.sin(angle + 0.5) * radius, 0])
        spoke = Line(start, end, stroke_color=color, stroke_width=3.5 * size)
        
        # Interlocking bend
        bend_angle = angle + 0.95
        bend_end = np.array([math.cos(bend_angle) * (radius * 0.8), math.sin(bend_angle) * (radius * 0.8), 0])
        sub_spoke = Line(end, bend_end, stroke_color=color, stroke_width=3.5 * size)
        spokes.extend([spoke, sub_spoke])

    outer_ring = Circle(radius=size * 0.52, color=color, stroke_width=1.5 * size, stroke_opacity=0.4)
    return VGroup(outer_ring, *spokes)


def create_anthropic_logo(size: float = 1.0, color: str = COLOR_ANTHROPIC) -> VGroup:
    """
    Creates a clean vector representation of the Anthropic / Claude spark emblem.
    Constructed using an 8-pointed star burst with weighted vertical/horizontal rays.
    """
    rays = []
    r_long = size * 0.55
    r_short = size * 0.30
    for i in range(8):
        angle = i * (math.pi / 4)
        is_cardinal = (i % 2 == 0)
        r = r_long if is_cardinal else r_short
        p1 = np.array([0, 0, 0])
        p2 = np.array([math.cos(angle) * r, math.sin(angle) * r, 0])
        ray = Line(p1, p2, stroke_color=color, stroke_width=4.0 * size if is_cardinal else 2.5 * size)
        rays.append(ray)

    center_dot = Dot(point=ORIGIN, radius=0.08 * size, color=color)
    glow_halo = Circle(radius=size * 0.56, color=color, stroke_width=1.2 * size, stroke_opacity=0.35)
    return VGroup(glow_halo, *rays, center_dot)


create_claude_logo = create_anthropic_logo


def create_google_deepmind_logo(size: float = 1.0, color: str = COLOR_DEEPMIND) -> VGroup:
    """
    Creates a clean vector representation of the Google DeepMind spark/star.
    Constructed using a four-pointed curved diamond spark with color gradients.
    """
    spark = Polygon(
        [0, size * 0.55, 0],
        [size * 0.12, size * 0.12, 0],
        [size * 0.55, 0, 0],
        [size * 0.12, -size * 0.12, 0],
        [0, -size * 0.55, 0],
        [-size * 0.12, -size * 0.12, 0],
        [-size * 0.55, 0, 0],
        [-size * 0.12, size * 0.12, 0],
        color=color,
        fill_color=color,
        fill_opacity=0.85,
        stroke_width=2.0 * size
    )
    center_sparkle = Dot(point=ORIGIN, radius=0.06 * size, color=WHITE)
    ring = Circle(radius=size * 0.58, color="#38BDF8", stroke_width=1.2 * size, stroke_opacity=0.3)
    return VGroup(ring, spark, center_sparkle)


def create_huggingface_logo(size: float = 1.0, color: str = COLOR_HUGGINGFACE) -> VGroup:
    """
    Creates a clean vector representation of the Hugging Face badge.
    Constructed using a smiling face contour with animated blush dots.
    """
    face_circle = Circle(radius=size * 0.48, color=color, fill_color="#1E1B4B", fill_opacity=0.7, stroke_width=3.0 * size)
    eye_left = Dot(point=[-size * 0.18, size * 0.12, 0], radius=0.07 * size, color=color)
    eye_right = Dot(point=[size * 0.18, size * 0.12, 0], radius=0.07 * size, color=color)
    smile = Arc(radius=size * 0.22, start_angle=math.pi * 1.15, angle=math.pi * 0.7, stroke_color=color, stroke_width=3.0 * size).shift(DOWN * (size * 0.08))
    hug_arm_left = Arc(radius=size * 0.25, start_angle=math.pi * 0.6, angle=math.pi * 0.5, stroke_color=color, stroke_width=2.5 * size).shift(LEFT * (size * 0.42))
    hug_arm_right = Arc(radius=size * 0.25, start_angle=-math.pi * 0.1, angle=math.pi * 0.5, stroke_color=color, stroke_width=2.5 * size).shift(RIGHT * (size * 0.42))
    return VGroup(face_circle, eye_left, eye_right, smile, hug_arm_left, hug_arm_right)


def create_github_logo(size: float = 1.0, color: str = COLOR_GITHUB) -> VGroup:
    """
    Creates a clean vector representation of GitHub's octocat silhouette / git graph node.
    """
    outer_circle = Circle(radius=size * 0.48, color=color, stroke_width=2.8 * size, fill_color="#0D1117", fill_opacity=0.85)
    ear_left = Polygon([-size * 0.28, size * 0.25, 0], [-size * 0.38, size * 0.42, 0], [-size * 0.18, size * 0.38, 0], color=color, fill_color=color, fill_opacity=1.0)
    ear_right = Polygon([size * 0.28, size * 0.25, 0], [size * 0.38, size * 0.42, 0], [size * 0.18, size * 0.38, 0], color=color, fill_color=color, fill_opacity=1.0)
    body = Arc(radius=size * 0.32, start_angle=math.pi * 0.15, angle=math.pi * 0.7, stroke_color=color, stroke_width=2.5 * size).shift(DOWN * (size * 0.15))
    return VGroup(outer_circle, ear_left, ear_right, body)


def get_lab_logo(provider_name: str, size: float = 1.0, color: Optional[str] = None) -> VGroup:
    """
    Resolves official research lab vector logo by name.
    """
    prov = (provider_name or "").lower().strip()
    if "openai" in prov or "o3" in prov or "gpt" in prov:
        return create_openai_logo(size=size, color=color or COLOR_OPENAI)
    elif "anthropic" in prov or "claude" in prov:
        return create_anthropic_logo(size=size, color=color or COLOR_ANTHROPIC)
    elif "deepmind" in prov or "google" in prov or "gemini" in prov:
        return create_google_deepmind_logo(size=size, color=color or COLOR_DEEPMIND)
    elif "hugging" in prov or "hf" in prov:
        return create_huggingface_logo(size=size, color=color or COLOR_HUGGINGFACE)
    elif "github" in prov:
        return create_github_logo(size=size, color=color or COLOR_GITHUB)
    else:
        return create_anthropic_logo(size=size, color=color or "#38BDF8")


def create_lab_hero_badge(
    provider_name: str,
    status_text: str = "OFFICIAL LAB RELEASE",
    model_name: str = "FRONTIER MODEL",
    width: float = 7.4,
    badge_text: Optional[str] = None
) -> VGroup:
    """
    Constructs a high-impact announcement card header combining
    official lab emblem, glowing status pill, and model name.
    """
    if badge_text:
        status_text = badge_text
    container = RoundedRectangle(
        corner_radius=0.18,
        width=width,
        height=1.75,
        color="#334155",
        fill_color=COLOR_BG_CARD,
        fill_opacity=0.95,
        stroke_width=1.8
    )

    logo = get_lab_logo(provider_name, size=0.95)
    logo.align_to(container, LEFT).shift(RIGHT * 0.45)

    pill_bg = RoundedRectangle(
        corner_radius=0.10,
        width=3.6,
        height=0.38,
        color="#EF4444",
        fill_color="#7F1D1D",
        fill_opacity=0.5,
        stroke_width=1.2
    )
    pill_txt = clean_text(
        status_text.upper(),
        font=FONT_HELVETICA,
        font_size=12,
        color="#FCA5A5",
        weight=BOLD,
        max_width=3.4
    ).move_to(pill_bg)
    status_pill = VGroup(pill_bg, pill_txt).next_to(logo, RIGHT, buff=0.35).shift(UP * 0.28)

    title_txt = clean_text(
        model_name,
        font=FONT_HELVETICA,
        font_size=23,
        color=WHITE,
        weight=HEAVY,
        max_width=width - 2.2
    )
    title_txt.next_to(status_pill, DOWN, buff=0.15).align_to(status_pill, LEFT)

    return VGroup(container, logo, status_pill, title_txt)
