"""
The Model Verse — Benchmark Showdown & Radar Comparison Engine
High-retention, high-dopamine quantitative visualization primitives for 9:16 mobile shorts:
1. BlueprintHorizontalRaceBars: Animated multi-contestant throughput/speed drag-race bars.
2. BlueprintRadarParetoPlot: Multi-axis spider/radar Pareto frontier tradeoff visualizations.
Strictly respects 9:16 chalkboard layout rules and safe zones (zero collision with subtitles at y=-3.45).
"""

import sys
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from manim import *
from manim.utils.rate_functions import ease_out_cubic, ease_out_back

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import FONT_HELVETICA
from manim_engine.primitives.typography import CleanText
from manim_engine.primitives.visual_compositions import BaseBlueprintComposition

# 3b1b Signature Color Palette
COLOR_CYAN = "#38BDF8"
COLOR_MINT = "#10B981"
COLOR_AMBER = "#F59E0B"
COLOR_CORAL = "#EF4444"
COLOR_PURPLE = "#A855F7"
COLOR_SLATE = "#94A3B8"
COLOR_DARK_SLATE = "#1E293B"
COLOR_WHITE = "#F8FAFC"
COLOR_GOLD = "#F59E0B"


class BlueprintHorizontalRaceBars(BaseBlueprintComposition):
    """
    Animated horizontal benchmark race bars comparing 3 to 4 models/kernels side by side.
    Displays dynamic racing fills, rank badges, real units (TFLOPS, tok/s, %), and leading particle tips.
    """
    def __init__(
        self,
        title: str = "BENCHMARK SHOWDOWN",
        sub: str = "Throughput comparison on NVIDIA H100 GPU (FP16)",
        metric_name: str = "THROUGHPUT",
        unit: str = "TFLOPS",
        contestants: Optional[List[Dict[str, Any]]] = None,
        delta_badge: str = "⚡ +78.8% SPEEDUP OVER INCUMBENT SOTA",
        accent_color: str = COLOR_MINT,
        **kwargs
    ):
        super().__init__(title=title, sub=sub, accent_color=accent_color, **kwargs)

        self.metric_name = metric_name
        self.unit = unit
        self.delta_str = delta_badge

        # Default fallback contestants if none provided
        self.contestant_data = contestants or [
            {"name": "FlashAttention-3", "value": 1180.0, "display_val": "1,180 TFLOPS", "is_hero": True, "color": COLOR_MINT},
            {"name": "FlashAttention-2", "value": 660.0, "display_val": "660 TFLOPS", "is_hero": False, "color": COLOR_CYAN},
            {"name": "cuDNN Flash", "value": 610.0, "display_val": "610 TFLOPS", "is_hero": False, "color": COLOR_PURPLE},
            {"name": "Standard PyTorch", "value": 240.0, "display_val": "240 TFLOPS", "is_hero": False, "color": COLOR_CORAL}
        ]
        self.contestant_data = self.contestant_data[:4]

        # Calculate max value for scaling bar lengths
        max_val = max((float(c.get("value", 1.0)) for c in self.contestant_data), default=1.0)
        if max_val <= 0:
            max_val = 1.0

        # Blueprint Carbon Chassis Card
        self.chassis = RoundedRectangle(
            corner_radius=0.18,
            width=7.2,
            height=4.6,
            stroke_color="#1E293B",
            stroke_width=1.5,
            fill_color="#080C14",
            fill_opacity=0.72
        ).move_to([0, 0.85, 0])
        self.content_group.add(self.chassis)

        # Sub-header inside chassis: Metric name badge
        metric_badge_txt = CleanText(
            f"MEASURED METRIC: {self.metric_name.upper()} ({self.unit})",
            font_size=11,
            color=COLOR_CYAN,
            weight=BOLD
        )
        metric_badge_bg = RoundedRectangle(
            corner_radius=0.10,
            width=metric_badge_txt.width + 0.4,
            height=0.32,
            stroke_color="#0284C7",
            stroke_width=1.0,
            fill_color="#082F49",
            fill_opacity=0.6
        )
        metric_badge_txt.move_to(metric_badge_bg)
        metric_badge = Group(metric_badge_bg, metric_badge_txt).move_to([0, 2.65, 0])
        self.content_group.add(metric_badge)

        # Race tracks container
        self.tracks_group = Group()
        self.bars = []
        self.bar_tips = []
        self.hero_row = None

        track_max_width = 3.65
        row_height = 0.72
        y_starts = [1.85, 0.95, 0.05, -0.85]  # Cleanly distributed inside chassis [-1.2, 2.8]

        rank_colors = [COLOR_GOLD, "#CBD5E1", "#D97706", "#64748B"]

        for idx, item in enumerate(self.contestant_data):
            y_pos = y_starts[idx] if idx < len(y_starts) else (y_starts[-1] - idx * 0.9)
            val = float(item.get("value", 0.0))
            is_hero = item.get("is_hero", False)
            bar_color = item.get("color", COLOR_MINT if is_hero else COLOR_CYAN)
            name = item.get("name", f"Model {idx+1}")
            display_val = item.get("display_val") or item.get("raw_str") or f"{val:,.0f} {self.unit}"

            # 1. Rank Badge (#1, #2, #3, #4)
            rank_col = rank_colors[min(idx, len(rank_colors) - 1)]
            rank_txt = CleanText(f"#{idx+1}", font_size=14, color=rank_col, weight=BOLD)
            rank_pill = RoundedRectangle(
                corner_radius=0.08,
                width=0.48,
                height=0.36,
                color=rank_col,
                stroke_width=1.2,
                fill_color="#0F172A",
                fill_opacity=0.85
            ).move_to([-3.1, y_pos + 0.12, 0])
            rank_txt.move_to(rank_pill)
            rank_badge = Group(rank_pill, rank_txt)

            # 2. Model Name
            name_col = COLOR_WHITE if is_hero else "#CBD5E1"
            name_txt = CleanText(name[:18], font_size=13, color=name_col, weight=BOLD if is_hero else MEDIUM)
            name_txt.next_to(rank_pill, RIGHT, buff=0.25).shift(UP * 0.02)
            if name_txt.width > 2.2:
                name_txt.scale_to_fit_width(2.2)

            # 3. Bar Background Slot
            bar_track_bg = RoundedRectangle(
                corner_radius=0.06,
                width=track_max_width,
                height=0.24,
                stroke_color="#1E293B",
                stroke_width=1.0,
                fill_color="#0F172A",
                fill_opacity=0.9
            ).move_to([-0.1, y_pos - 0.20, 0])

            # 4. Racing Fill Bar: explicitly aligned to bar_track_bg on Y, then left-aligned
            target_width = max(0.25, track_max_width * (val / max_val))
            fill_bar = RoundedRectangle(
                corner_radius=0.06,
                width=target_width,
                height=0.24,
                stroke_color=bar_color,
                stroke_width=1.2 if is_hero else 0.8,
                fill_color=bar_color,
                fill_opacity=0.95 if is_hero else 0.80
            ).move_to(bar_track_bg).align_to(bar_track_bg, LEFT)

            # 5. Glowing Leading Tip Particle
            tip = Dot(
                point=fill_bar.get_right() + RIGHT * 0.02,
                radius=0.06 if is_hero else 0.045,
                color=COLOR_WHITE,
                fill_opacity=1.0
            )
            halo = Dot(
                point=tip.get_center(),
                radius=0.12 if is_hero else 0.08,
                color=bar_color,
                fill_opacity=0.45
            )
            tip_group = Group(halo, tip)

            # 6. Value Display
            val_col = COLOR_WHITE if is_hero else COLOR_SLATE
            val_txt = CleanText(display_val[:16], font_size=12, color=val_col, weight=BOLD if is_hero else MEDIUM)
            val_txt.next_to(bar_track_bg, RIGHT, buff=0.22)
            if val_txt.width > 1.3:
                val_txt.scale_to_fit_width(1.3)

            # Assemble Row
            row_group = Group(rank_badge, name_txt, bar_track_bg, fill_bar, tip_group, val_txt)
            self.tracks_group.add(row_group)
            self.bars.append(fill_bar)
            self.bar_tips.append(tip_group)

            if is_hero and not self.hero_row:
                self.hero_row = row_group

        self.content_group.add(self.tracks_group)

        # Bottom Victory Delta Badge at y = -2.1 (strictly above subtitles at y = -3.45)
        badge_txt = CleanText(self.delta_str[:52], font_size=9.5, color="#10B981", weight=BOLD)
        badge_pill = RoundedRectangle(
            corner_radius=0.12,
            width=badge_txt.width + 0.5,
            height=0.34,
            color="#10B981",
            stroke_width=1.3,
            fill_color="#064E3B",
            fill_opacity=0.75
        )
        badge_txt.move_to(badge_pill)
        self.badge = Group(badge_pill, badge_txt).move_to([0, -2.1, 0])
        self.content_group.add(self.badge)

        self.kinetic_elements.add(self.tracks_group, self.badge)
        self.add(self.title, self.sub, self.content_group)

    def get_entrance_animation(self, run_time: float = 1.0) -> Animation:
        """
        Progressive drag-race entrance: Chassis appears, then bars expand horizontally
        from 0 to full target width simultaneously like an animated horsepower race.
        """
        anims = [FadeIn(self.title, shift=DOWN * 0.15), FadeIn(self.sub, shift=DOWN * 0.15), FadeIn(self.chassis, scale=0.98)]
        for bar in self.bars:
            anims.append(GrowFromEdge(bar, LEFT, rate_func=ease_out_cubic))
        for tip in self.bar_tips:
            anims.append(FadeIn(tip, scale=0.5, rate_func=ease_out_cubic))
        anims.append(FadeIn(self.tracks_group, shift=RIGHT * 0.1))
        anims.append(FadeIn(self.badge, shift=UP * 0.15, rate_func=ease_out_back))
        return AnimationGroup(*anims, run_time=run_time)

    def get_kinetic_animation(self, run_time: float = 1.8) -> Animation:
        """Focal kinetic action: Hero bar glows and pulses along its racing length."""
        if self.hero_row:
            return AnimationGroup(
                Indicate(self.hero_row, color=COLOR_MINT, scale_factor=1.02),
                self.badge.animate.scale(1.05).set_color(COLOR_GOLD),
                run_time=run_time
            )
        return AnimationGroup(
            self.badge.animate.scale(1.04),
            run_time=run_time
        )


class BlueprintRadarParetoPlot(BaseBlueprintComposition):
    """
    Multi-axis Spider / Radar Pareto Tradeoff Plot.
    Plots 4 to 6 performance dimensions (e.g. Throughput, VRAM, Accuracy, Context, Cost)
    with concentric spider-web grids and overlaid challenger vs incumbent polygons.
    """
    def __init__(
        self,
        title: str = "PARETO FRONTIER",
        sub: str = "Multi-dimensional tradeoff across reasoning architectures",
        axes: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
        delta_badge: str = "⚡ DOMINATES PARETO FRONTIER AT 18x LOWER COST",
        accent_color: str = COLOR_MINT,
        **kwargs
    ):
        super().__init__(title=title, sub=sub, accent_color=accent_color, **kwargs)

        self.axis_labels_list = axes or ["Throughput", "VRAM Efficiency", "Accuracy", "Context Length", "Cost Efficiency"]
        self.axis_labels_list = self.axis_labels_list[:6]
        self.num_axes = len(self.axis_labels_list)
        self.delta_str = delta_badge

        # Blueprint Carbon Chassis Card
        self.chassis = RoundedRectangle(
            corner_radius=0.18,
            width=7.2,
            height=4.6,
            stroke_color="#1E293B",
            stroke_width=1.5,
            fill_color="#080C14",
            fill_opacity=0.72
        ).move_to([0, 0.85, 0])
        self.content_group.add(self.chassis)

        # Center of the spider plot inside chassis
        self.center_pt = np.array([0.0, 0.85, 0.0])
        self.max_radius = 1.95  # Comfortably fits within chassis width 7.2 and height 4.6

        # Models comparison data
        self.models_data = models or [
            {
                "name": "Challenger (DeepSeek)",
                "scores": [0.94, 0.88, 0.92, 0.86, 0.98],
                "is_hero": True,
                "color": COLOR_MINT,
                "fill_opacity": 0.35
            },
            {
                "name": "Incumbent (Proprietary)",
                "scores": [0.60, 0.45, 0.95, 0.85, 0.20],
                "is_hero": False,
                "color": COLOR_CORAL,
                "fill_opacity": 0.18
            }
        ]

        # Calculate radial angles
        self.angles = [
            (np.pi / 2.0) - (2.0 * np.pi * i / self.num_axes)
            for i in range(self.num_axes)
        ]

        # 1. Concentric Spider Web Rings (20%, 40%, 60%, 80%, 100%)
        self.grid_group = Group()
        ring_levels = [0.2, 0.4, 0.6, 0.8, 1.0]
        for lvl in ring_levels:
            r = self.max_radius * lvl
            pts = [
                self.center_pt + np.array([r * np.cos(a), r * np.sin(a), 0.0])
                for a in self.angles
            ]
            ring = Polygon(
                *pts,
                stroke_color="#1E293B" if lvl < 1.0 else "#334155",
                stroke_width=1.0 if lvl < 1.0 else 1.4,
                stroke_opacity=0.75,
                fill_opacity=0.0
            )
            self.grid_group.add(ring)

        # 2. Radial Spokes & Axis Labels
        self.spokes_group = Group()
        self.labels_group = Group()

        for i, (angle, label_text) in enumerate(zip(self.angles, self.axis_labels_list)):
            outer_pt = self.center_pt + np.array([self.max_radius * np.cos(angle), self.max_radius * np.sin(angle), 0.0])
            spoke = Line(
                start=self.center_pt,
                end=outer_pt,
                color="#334155",
                stroke_width=1.2,
                stroke_opacity=0.85
            )
            self.spokes_group.add(spoke)

            # Axis Label slightly outside outer point
            label_offset = 0.38
            label_pt = self.center_pt + np.array([(self.max_radius + label_offset) * np.cos(angle), (self.max_radius + label_offset) * np.sin(angle), 0.0])
            lbl = CleanText(label_text.upper()[:16], font_size=9.5, color=COLOR_SLATE, weight=BOLD)
            lbl.move_to(label_pt)
            if lbl.width > 1.8:
                lbl.scale_to_fit_width(1.8)
            self.labels_group.add(lbl)

        self.content_group.add(self.grid_group, self.spokes_group, self.labels_group)

        # 3. Model Polygons
        self.polygon_group = Group()
        self.hero_polygon = None

        for item in self.models_data:
            is_hero = item.get("is_hero", False)
            col = item.get("color", COLOR_MINT if is_hero else COLOR_CORAL)
            op = item.get("fill_opacity", 0.30 if is_hero else 0.15)
            scores = item.get("scores", [0.5] * self.num_axes)

            poly_pts = []
            vertex_dots = []
            for i, angle in enumerate(self.angles):
                s = min(1.0, max(0.05, float(scores[i]) if i < len(scores) else 0.5))
                r = self.max_radius * s
                pt = self.center_pt + np.array([r * np.cos(angle), r * np.sin(angle), 0.0])
                poly_pts.append(pt)

                # Glowing vertex dot
                dot = Dot(point=pt, radius=0.06 if is_hero else 0.04, color=col, fill_opacity=1.0)
                vertex_dots.append(dot)

            poly = Polygon(
                *poly_pts,
                stroke_color=col,
                stroke_width=2.4 if is_hero else 1.6,
                fill_color=col,
                fill_opacity=op
            )
            poly_container = Group(poly, *vertex_dots)
            self.polygon_group.add(poly_container)

            if is_hero and not self.hero_polygon:
                self.hero_polygon = poly_container

        self.content_group.add(self.polygon_group)

        # 4. Top Legend Badges inside chassis (y = 2.75)
        legend_group = Group()
        for idx, item in enumerate(self.models_data[:2]):
            col = item.get("color", COLOR_MINT)
            name = item.get("name", "Model")
            dot = Dot(radius=0.05, color=col)
            txt = CleanText(name[:24], font_size=10, color=col, weight=BOLD)
            leg_item = Group(dot, txt).arrange(RIGHT, buff=0.12)
            legend_group.add(leg_item)

        legend_group.arrange(RIGHT, buff=0.6).move_to([0, 2.75, 0])
        self.content_group.add(legend_group)

        # 5. Bottom Victory Delta Badge at y = -2.1
        badge_txt = CleanText(self.delta_str[:52], font_size=9.5, color="#10B981", weight=BOLD)
        badge_pill = RoundedRectangle(
            corner_radius=0.12,
            width=badge_txt.width + 0.5,
            height=0.34,
            color="#10B981",
            stroke_width=1.3,
            fill_color="#064E3B",
            fill_opacity=0.75
        )
        badge_txt.move_to(badge_pill)
        self.badge = Group(badge_pill, badge_txt).move_to([0, -2.1, 0])
        self.content_group.add(self.badge)

        self.kinetic_elements.add(self.polygon_group, self.badge)
        self.add(self.title, self.sub, self.content_group)

    def get_entrance_animation(self, run_time: float = 1.0) -> Animation:
        """Expanding web entrance: Concentric rings fade in, polygons bloom outward."""
        anims = [
            FadeIn(self.title, shift=DOWN * 0.15),
            FadeIn(self.sub, shift=DOWN * 0.15),
            FadeIn(self.chassis, scale=0.98),
            FadeIn(self.grid_group, scale=0.95),
            FadeIn(self.spokes_group),
            FadeIn(self.labels_group)
        ]
        for poly_cont in self.polygon_group:
            anims.append(GrowFromCenter(poly_cont, rate_func=ease_out_cubic))
        anims.append(FadeIn(self.badge, shift=UP * 0.15, rate_func=ease_out_back))
        return AnimationGroup(*anims, run_time=run_time)

    def get_kinetic_animation(self, run_time: float = 1.8) -> Animation:
        """Focal kinetic action: Hero Pareto polygon gently pulses along its frontier."""
        if self.hero_polygon:
            return AnimationGroup(
                self.hero_polygon.animate.scale(1.04),
                self.badge.animate.scale(1.05).set_color(COLOR_GOLD),
                run_time=run_time
            )
        return AnimationGroup(self.badge.animate.scale(1.04), run_time=run_time)
