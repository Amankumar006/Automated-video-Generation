"""
The Model Verse — Benchmark & Leaderboard Visual Primitives
High-retention chalkboard leaderboard rows, metric comparison bars, and cost disruption meters.
"""

from manim import *
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from pipeline.config import (
    FONT_HELVETICA, COLOR_MINT, COLOR_DANGER, COLOR_GOLD, COLOR_SLATE,
    COLOR_CARD_BG, COLOR_CARD_BORDER
)

def create_leaderboard_row(
    rank: int,
    model_name: str,
    score_str: str,
    score_pct: float,
    is_hero: bool = False,
    hero_color: str = COLOR_MINT,
    width: float = 7.4,
    height: float = 1.05
) -> VGroup:
    """
    Creates a single leaderboard ranking card on the chalkboard canvas.
    """
    border_col = hero_color if is_hero else "#334155"
    fill_col = "#0B1528" if is_hero else "#0F172A"
    stroke_w = 2.4 if is_hero else 1.4

    card_bg = RoundedRectangle(
        corner_radius=0.14,
        width=width,
        height=height,
        color=border_col,
        fill_color=fill_col,
        fill_opacity=0.92,
        stroke_width=stroke_w
    )

    # Rank Badge
    rank_color = COLOR_GOLD if rank == 1 else ("#94A3B8" if rank == 2 else "#64748B")
    rank_badge = Text(f"#{rank}", font=FONT_HELVETICA, font_size=24, color=rank_color, weight=HEAVY)
    rank_badge.align_to(card_bg, LEFT).shift(RIGHT * 0.4)

    # Model Name: shifted slightly up to prevent overlap with progress bar below
    name_color = WHITE if is_hero else "#CBD5E1"
    name_txt = Text(model_name, font=FONT_HELVETICA, font_size=21, color=name_color, weight=BOLD)
    name_txt.next_to(rank_badge, RIGHT, buff=0.35).shift(UP * 0.16)

    # Score Value
    val_color = hero_color if is_hero else "#94A3B8"
    score_txt = Text(score_str, font=FONT_HELVETICA, font_size=23, color=val_color, weight=HEAVY)
    score_txt.align_to(card_bg, RIGHT).shift(LEFT * 0.4)

    # Progress Sub-bar cleanly placed underneath model name
    bar_width = 3.6
    bar_bg = Rectangle(
        width=bar_width,
        height=0.08,
        color="#1E293B",
        fill_color="#1E293B",
        fill_opacity=0.9,
        stroke_width=0
    ).shift(DOWN * 0.22).align_to(name_txt, LEFT)

    bar_fill = Rectangle(
        width=max(0.2, bar_width * (score_pct / 100.0)),
        height=0.08,
        color=hero_color if is_hero else "#475569",
        fill_color=hero_color if is_hero else "#475569",
        fill_opacity=0.95,
        stroke_width=0
    ).align_to(bar_bg, LEFT)

    grp = VGroup(card_bg, rank_badge, name_txt, score_txt, bar_bg, bar_fill)
    return grp

def create_metric_clash_group(
    benchmark_name: str,
    challenger_name: str,
    challenger_score: float,
    incumbent_name: str,
    incumbent_score: float,
    unit: str = "%",
    width: float = 7.4
) -> VGroup:
    """
    Creates a dual-model comparison bar for a specific benchmark.
    """
    container = RoundedRectangle(
        corner_radius=0.14,
        width=width,
        height=1.55,
        color="#334155",
        fill_color="#0F172A",
        fill_opacity=0.95,
        stroke_width=1.6
    )

    title_txt = Text(benchmark_name.upper(), font=FONT_HELVETICA, font_size=18, color=COLOR_GOLD, weight=HEAVY)
    title_txt.align_to(container, UP).shift(DOWN * 0.22)

    # Challenger row (top)
    c_label = Text(challenger_name, font=FONT_HELVETICA, font_size=18, color=COLOR_MINT, weight=BOLD)
    c_label.align_to(container, LEFT).shift(RIGHT * 0.4 + DOWN * 0.05)

    c_score = Text(f"{challenger_score}{unit}", font=FONT_HELVETICA, font_size=19, color=COLOR_MINT, weight=HEAVY)
    c_score.align_to(container, RIGHT).shift(LEFT * 0.4 + DOWN * 0.05)

    # Incumbent row (bottom)
    i_label = Text(incumbent_name, font=FONT_HELVETICA, font_size=17, color="#94A3B8", weight=MEDIUM)
    i_label.align_to(container, LEFT).shift(RIGHT * 0.4 + DOWN * 0.45)

    i_score = Text(f"{incumbent_score}{unit}", font=FONT_HELVETICA, font_size=18, color="#CBD5E1", weight=BOLD)
    i_score.align_to(container, RIGHT).shift(LEFT * 0.4 + DOWN * 0.45)

    return VGroup(container, title_txt, c_label, c_score, i_label, i_score)

def create_cost_disruption_meter(
    incumbent_name: str = "OpenAI o1",
    incumbent_price: str = "$15.00 / 1M",
    challenger_name: str = "DeepSeek-R1",
    challenger_price: str = "$0.55 / 1M",
    multiplier_str: str = "27x CHEAPER",
    width: float = 7.4
) -> VGroup:
    """
    Creates an economic disruption chalkboard display.
    """
    card = RoundedRectangle(
        corner_radius=0.18,
        width=width,
        height=2.3,
        color=COLOR_MINT,
        fill_color="#0A1628",
        fill_opacity=0.96,
        stroke_width=2.2
    )

    header = Text("API INFERENCE COST DISRUPTION", font=FONT_HELVETICA, font_size=17, color=COLOR_GOLD, weight=HEAVY)
    header.align_to(card, UP).shift(DOWN * 0.25)

    # Split-column comparison
    left_col = VGroup(
        Text(incumbent_name, font=FONT_HELVETICA, font_size=18, color="#94A3B8", weight=BOLD),
        Text(incumbent_price, font=FONT_HELVETICA, font_size=24, color=COLOR_DANGER, weight=HEAVY)
    ).arrange(DOWN, buff=0.15).shift(LEFT * 1.8 + DOWN * 0.15)

    divider = Line(UP * 0.6, DOWN * 0.6, color="#334155", stroke_width=1.5).shift(DOWN * 0.15)

    right_col = VGroup(
        Text(challenger_name, font=FONT_HELVETICA, font_size=18, color=WHITE, weight=BOLD),
        Text(challenger_price, font=FONT_HELVETICA, font_size=26, color=COLOR_MINT, weight=HEAVY)
    ).arrange(DOWN, buff=0.15).shift(RIGHT * 1.8 + DOWN * 0.15)

    banner = RoundedRectangle(
        corner_radius=0.10,
        width=width * 0.85,
        height=0.48,
        color=COLOR_GOLD,
        fill_color="#1E293B",
        fill_opacity=0.9,
        stroke_width=1.5
    ).align_to(card, DOWN).shift(UP * 0.20)

    banner_txt = Text(f"⚡ {multiplier_str} • 100% OPEN WEIGHTS", font=FONT_HELVETICA, font_size=16, color="#FDE68A", weight=HEAVY).move_to(banner)

    return VGroup(card, header, left_col, divider, right_col, banner, banner_txt)

def create_dual_accuracy_bar_chart(
    hero_label: str = "SAE Latents",
    hero_val: float = 98.2,
    base_label: str = "Dense Baseline",
    base_val: float = 41.5,
    unit: str = "%",
    delta_label: str = "+56.7% RECOVERY GAIN",
    chart_width: float = 6.8,
    max_height: float = 2.4,
    y_base: float = 0.6
):
    """
    Creates an authentic 3Blue1Brown chalkboard dual bar comparison chart
    with glowing hero bar, muted baseline, and delta gain badge.
    """
    axis_line = Line(
        start=[-chart_width / 2.0, y_base, 0],
        end=[chart_width / 2.0, y_base, 0],
        color="#475569",
        stroke_width=2.0
    )

    # 1. Baseline Bar (Left)
    base_h = max(0.4, (base_val / 100.0) * max_height)
    base_x = -1.5
    base_bar = Rectangle(
        width=1.5,
        height=base_h,
        color="#EF4444",
        fill_color="#450A0A",
        fill_opacity=0.75,
        stroke_width=1.8
    ).move_to([base_x, y_base + base_h / 2.0, 0])

    base_val_txt = Text(
        f"{base_val}{unit}",
        font=FONT_HELVETICA,
        font_size=20,
        color="#EF4444",
        weight=HEAVY
    ).next_to(base_bar, UP, buff=0.14)

    base_sub_txt = Text(
        base_label,
        font=FONT_HELVETICA,
        font_size=13,
        color="#94A3B8"
    ).next_to(base_bar, DOWN, buff=0.18)
    if base_sub_txt.width > 2.6:
        base_sub_txt.scale_to_fit_width(2.6)

    # 2. Hero Bar (Right)
    hero_h = max(0.6, (hero_val / 100.0) * max_height)
    hero_x = 1.5
    hero_bar = Rectangle(
        width=1.5,
        height=hero_h,
        color="#10B981",
        fill_color="#064E3B",
        fill_opacity=0.88,
        stroke_width=2.5
    ).move_to([hero_x, y_base + hero_h / 2.0, 0])

    hero_val_txt = Text(
        f"{hero_val}{unit}",
        font=FONT_HELVETICA,
        font_size=24,
        color="#34D399",
        weight=HEAVY
    ).next_to(hero_bar, UP, buff=0.14)

    hero_sub_txt = Text(
        hero_label,
        font=FONT_HELVETICA,
        font_size=13,
        color="#34D399",
        weight=BOLD
    ).next_to(hero_bar, DOWN, buff=0.18)
    if hero_sub_txt.width > 2.6:
        hero_sub_txt.scale_to_fit_width(2.6)

    # 3. Delta Gain Badge
    delta_pill = RoundedRectangle(
        corner_radius=0.12,
        width=3.6,
        height=0.48,
        color=COLOR_GOLD,
        fill_color="#0A0D14",
        fill_opacity=0.92,
        stroke_width=1.4
    ).move_to([0.0, y_base + max_height + 0.65, 0])

    delta_txt = Text(
        delta_label,
        font=FONT_HELVETICA,
        font_size=13,
        color="#FDE68A",
        weight=HEAVY
    ).move_to(delta_pill)
    if delta_txt.width > 3.4:
        delta_txt.scale_to_fit_width(3.4)

    delta_grp = VGroup(delta_pill, delta_txt)

    static_elements = VGroup(axis_line, base_sub_txt, hero_sub_txt, delta_grp)
    return {
        "axis": axis_line,
        "base_bar": base_bar,
        "base_val": base_val_txt,
        "base_sub": base_sub_txt,
        "hero_bar": hero_bar,
        "hero_val": hero_val_txt,
        "hero_sub": hero_sub_txt,
        "delta": delta_grp,
        "full_group": VGroup(axis_line, base_bar, base_val_txt, base_sub_txt, hero_bar, hero_val_txt, hero_sub_txt, delta_grp)
    }

