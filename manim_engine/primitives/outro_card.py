"""
Visual Primitives: High-Converting Branded Outro Card
"""

from manim import *
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from pipeline.config import FONT_HELVETICA, COLOR_MINT, COLOR_CARD_BG, COLOR_CARD_BORDER

def create_chalkboard_brand_outro(
    logo_title: str = "THE MODEL VERSE",
    tagline: str = "Follow for the architecture behind modern AI",
    url: str = "themodelverse.in",
    y_center: float = 0.5
) -> tuple[VGroup, VGroup, VGroup]:
    """Creates a pure 3b1b mathematical chalkboard brand signature (zero cards, zero buttons)."""
    # 1. Geometric neural icon: A hexagon of 6 nodes connected to a central node
    nodes = []
    edges = []
    center_pt = np.array([0, y_center + 2.2, 0])
    center_dot = Dot(point=center_pt, radius=0.12, color=COLOR_MINT)
    nodes.append(center_dot)
    
    radius = 0.9
    for i in range(6):
        angle = i * (TAU / 6)
        pt = center_pt + np.array([radius * np.cos(angle), radius * np.sin(angle), 0])
        d = Dot(point=pt, radius=0.08, color="#38BDF8")
        nodes.append(d)
        edges.append(Line(center_pt, pt, stroke_width=2.0, color="#334155"))
        # connect adjacent
        next_angle = (i + 1) * (TAU / 6)
        next_pt = center_pt + np.array([radius * np.cos(next_angle), radius * np.sin(next_angle), 0])
        edges.append(Line(pt, next_pt, stroke_width=1.5, color="#1E293B"))
    
    logo_icon = VGroup(*edges, *nodes)
    
    # 2. Brand Name & Website
    title = Text(logo_title, font=FONT_HELVETICA, font_size=48, color=WHITE, weight=HEAVY).shift(UP * (y_center + 0.5))
    site = Text(url, font=FONT_HELVETICA, font_size=32, color=COLOR_MINT, weight=BOLD).next_to(title, DOWN, buff=0.3)
    brand_text_group = VGroup(title, site)
    
    # 3. Call to Action / Subtitle
    sub = Text(tagline, font=FONT_HELVETICA, font_size=20, color="#94A3B8", weight=MEDIUM).next_to(site, DOWN, buff=0.45)
    
    return logo_icon, brand_text_group, sub

