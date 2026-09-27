"""
Visual Primitives: Split-Screen Comparison for Model Showdown
"""

from manim import *
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from pipeline.config import FONT_HELVETICA, COLOR_MINT, COLOR_DANGER, COLOR_CARD_BG, COLOR_GOLD

def create_model_showdown_panels(
    model_a_name: str = "DeepSeek-V3",
    model_a_specs: list = None,
    model_b_name: str = "GPT-4o",
    model_b_specs: list = None,
    y_shift: float = 1.0
) -> tuple[VGroup, VGroup, VGroup]:
    """
    Creates side-by-side or stacked contender panels with a central VS badge.
    Optimized for 9:16 vertical view.
    """
    if model_a_specs is None:
        model_a_specs = ["671B Total", "37B Active", "$0.14 / 1M Tokens"]
    if model_b_specs is None:
        model_b_specs = ["~1.8T Dense", "All Weights Fire", "$2.50 / 1M Tokens"]

    # Panel A (Left/Top Contender - e.g. Open Weights / DeepSeek)
    panel_a_box = RoundedRectangle(
        corner_radius=0.18, width=3.8, height=4.2,
        color=COLOR_MINT, fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_width=2.0
    ).shift(LEFT * 2.1 + UP * y_shift)
    title_a = Text(model_a_name, font=FONT_HELVETICA, font_size=24, color=COLOR_MINT, weight=HEAVY).shift(LEFT * 2.1 + UP * (y_shift + 1.4))
    if title_a.width > 3.4:
        title_a.scale_to_fit_width(3.4)
    tag_a = Text("SPARSE MoE", font=FONT_HELVETICA, font_size=15, color="#A7F3D0", weight=BOLD).next_to(title_a, DOWN, buff=0.18)
    if tag_a.width > 3.4:
        tag_a.scale_to_fit_width(3.4)
    
    rows_a_list = []
    for spec in model_a_specs:
        row = Text(spec, font=FONT_HELVETICA, font_size=16, color=WHITE, weight=SEMIBOLD)
        if row.width > 3.4:
            row.scale_to_fit_width(3.4)
        rows_a_list.append(row)
    rows_a = VGroup(*rows_a_list).arrange(DOWN, buff=0.35).next_to(tag_a, DOWN, buff=0.4)
    panel_a = VGroup(panel_a_box, title_a, tag_a, rows_a)

    # Panel B (Right/Bottom Contender - e.g. Proprietary / Dense)
    panel_b_box = RoundedRectangle(
        corner_radius=0.18, width=3.8, height=4.2,
        color="#38BDF8", fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_width=2.0
    ).shift(RIGHT * 2.1 + UP * y_shift)
    title_b = Text(model_b_name, font=FONT_HELVETICA, font_size=24, color="#38BDF8", weight=HEAVY).shift(RIGHT * 2.1 + UP * (y_shift + 1.4))
    if title_b.width > 3.4:
        title_b.scale_to_fit_width(3.4)
    tag_b = Text("MONOLITHIC DENSE", font=FONT_HELVETICA, font_size=15, color="#BAE6FD", weight=BOLD).next_to(title_b, DOWN, buff=0.18)
    if tag_b.width > 3.4:
        tag_b.scale_to_fit_width(3.4)
    
    rows_b_list = []
    for spec in model_b_specs:
        row = Text(spec, font=FONT_HELVETICA, font_size=16, color=WHITE, weight=SEMIBOLD)
        if row.width > 3.4:
            row.scale_to_fit_width(3.4)
        rows_b_list.append(row)
    rows_b = VGroup(*rows_b_list).arrange(DOWN, buff=0.35).next_to(tag_b, DOWN, buff=0.4)
    panel_b = VGroup(panel_b_box, title_b, tag_b, rows_b)

    # VS Divider Badge
    vs_circle = Circle(radius=0.48, color=COLOR_GOLD, fill_color="#0F172A", fill_opacity=1.0, stroke_width=2.5).shift(UP * y_shift)
    vs_text = Text("VS", font=FONT_HELVETICA, font_size=22, color=COLOR_GOLD, weight=HEAVY).move_to(vs_circle)
    vs_badge = VGroup(vs_circle, vs_text)

    return panel_a, panel_b, vs_badge
