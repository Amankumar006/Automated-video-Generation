"""
Visual Primitives: High-Converting Branded Outro Card
"""

from manim import *
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import FONT_HELVETICA, COLOR_MINT
from manim_engine.primitives.typography import CleanText


def create_chalkboard_brand_outro(
    logo_title: str = "THE MODEL VERSE",
    tagline: str = "Follow for the architecture behind modern AI",
    url: str = "themodelverse.in",
    y_center: float = 0.5
) -> tuple[VGroup, VGroup, VGroup]:
    """Creates the signature 3Blue1Brown mathematical chalkboard brand signature with official logo."""
    # 1. Official Modelverse vector logo
    logo_svg_path = PROJECT_ROOT / "public" / "brand" / "modelverse_logo.svg"
    avatar_png_path = PROJECT_ROOT / "public" / "brand" / "modelverse_avatar.png"

    if logo_svg_path.exists():
        logo_icon = SVGMobject(str(logo_svg_path)).scale_to_fit_height(2.6).move_to([0, y_center + 1.8, 0])
    elif avatar_png_path.exists():
        logo_icon = ImageMobject(str(avatar_png_path)).scale_to_fit_height(2.6).move_to([0, y_center + 1.8, 0])
    else:
        # Fallback procedural icon
        center_pt = np.array([0, y_center + 1.8, 0])
        center_dot = Dot(point=center_pt, radius=0.15, color=COLOR_MINT)
        nodes = [center_dot]
        edges = []
        radius = 0.9
        for i in range(6):
            angle = i * (TAU / 6)
            pt = center_pt + np.array([radius * np.cos(angle), radius * np.sin(angle), 0])
            d = Dot(point=pt, radius=0.08, color="#38BDF8")
            nodes.append(d)
            edges.append(Line(center_pt, pt, stroke_width=2.0, color="#334155"))
            next_angle = (i + 1) * (TAU / 6)
            next_pt = center_pt + np.array([radius * np.cos(next_angle), radius * np.sin(next_angle), 0])
            edges.append(Line(pt, next_pt, stroke_width=1.5, color="#1E293B"))
        logo_icon = VGroup(*edges, *nodes)

    # 2. Brand Name & Website (Clean Typography)
    title = CleanText(logo_title, font=FONT_HELVETICA, font_size=26, color=WHITE, weight=BOLD).next_to(logo_icon, DOWN, buff=0.45)
    site = CleanText(url, font=FONT_HELVETICA, font_size=18, color=COLOR_MINT, weight=BOLD).next_to(title, DOWN, buff=0.22)
    brand_text_group = VGroup(title, site)

    # 3. Call to Action / Subtitle
    sub = CleanText(tagline, font=FONT_HELVETICA, font_size=14, color="#94A3B8", weight=NORMAL).next_to(site, DOWN, buff=0.35)

    return logo_icon, brand_text_group, sub

