"""
Dual Metric Gauge & Radial Score Meters for Quantitative Payoffs.
Visualizes performance comparisons, efficiency ratios, and benchmark deltas.
"""

from manim import *
import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from pipeline.config import FONT_HELVETICA, COLOR_MINT, COLOR_DANGER, COLOR_GOLD


class RadialScoreMeter(VGroup):
    """
    Circular gauge with radial progress arc and central percentage / score metric.
    """
    def __init__(
        self,
        label: str,
        value_pct: float = 0.95,
        display_text: str = "95%",
        color: str = COLOR_MINT,
        radius: float = 1.1,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.value_pct = value_pct
        self.meter_color = color

        # Background Track
        self.bg_track = Circle(
            radius=radius,
            color="#1E293B",
            stroke_width=4.0
        )

        # Active Progress Arc
        sweep = min(TAU * 0.999, value_pct * TAU)
        self.active_arc = Arc(
            radius=radius,
            start_angle=PI / 2,
            angle=-sweep,
            color=color,
            stroke_width=5.5
        )

        # Central Number
        self.num_txt = Text(
            display_text,
            font=FONT_HELVETICA,
            font_size=28,
            color=WHITE,
            weight=HEAVY
        ).move_to(self.bg_track.get_center() + UP * 0.08)

        # Label underneath
        if isinstance(label, dict):
            label_str = str(label.get("name", "Model"))
        else:
            label_str = str(label)

        self.lbl_txt = Text(
            label_str.upper()[:24],
            font=FONT_HELVETICA,
            font_size=10,
            color=color,
            weight=BOLD
        ).next_to(self.bg_track.get_bottom(), DOWN, buff=0.15)

        self.add(self.bg_track, self.active_arc, self.num_txt, self.lbl_txt)


from typing import Optional


class DualMetricGauge(VGroup):
    """
    Comparative dual gauge comparing Contender A vs Contender B with a central delta badge.
    """
    def __init__(
        self,
        label_a: str = "Coding Agent",
        val_a: float = 0.95,
        text_a: str = "95%",
        label_b: str = "Classical TAMP",
        val_b: float = 0.47,
        text_b: str = "47%",
        delta_text: str = "+48% SUCCESS RATE",
        y_shift: float = 0.0,
        model_a_name: Optional[str] = None,
        model_a_score: Optional[str] = None,
        model_b_name: Optional[str] = None,
        model_b_score: Optional[str] = None,
        delta_label: Optional[str] = None,
        **kwargs
    ):
        if model_a_name is not None:
            label_a = model_a_name
        if model_a_score is not None:
            text_a = str(model_a_score)
        if model_b_name is not None:
            label_b = model_b_name
        if model_b_score is not None:
            text_b = str(model_b_score)
        if delta_label is not None:
            delta_text = delta_label

        scale_val = kwargs.pop("scale", None)
        super().__init__(**kwargs)

        self.meter_a = RadialScoreMeter(
            label=label_a,
            value_pct=val_a,
            display_text=text_a,
            color=COLOR_MINT,
            radius=1.15
        ).shift(LEFT * 1.8 + UP * y_shift)

        self.meter_b = RadialScoreMeter(
            label=label_b,
            value_pct=val_b,
            display_text=text_b,
            color="#38BDF8",
            radius=1.15
        ).shift(RIGHT * 1.8 + UP * y_shift)

        # Central Delta Badge (Chalkboard Technical Badge)
        delta_box = RoundedRectangle(
            width=5.0, height=0.55, corner_radius=0.10,
            color=COLOR_MINT, fill_color="#06281E", fill_opacity=0.6, stroke_width=1.2
        ).shift(DOWN * (1.8 - y_shift))

        delta_lbl = Text(
            delta_text,
            font=FONT_HELVETICA,
            font_size=12,
            color="#A7F3D0",
            weight=HEAVY
        ).move_to(delta_box)
        if delta_lbl.width > delta_box.width * 0.88:
            delta_lbl.scale_to_fit_width(delta_box.width * 0.88)

        self.delta_badge = VGroup(delta_box, delta_lbl)
        self.add(self.meter_a, self.meter_b, self.delta_badge)
        if scale_val is not None:
            self.scale(scale_val)

    def animate_count_up(self, run_time: float = 2.0):
        """Animates radial arcs drawing and delta badge pulsing."""
        return AnimationGroup(
            Create(self.meter_a.active_arc, run_time=run_time * 0.7),
            Create(self.meter_b.active_arc, run_time=run_time * 0.7),
            Indicate(self.delta_badge, color="#34D399", scale_factor=1.05, run_time=run_time * 0.6)
        )

    def highlight_bottleneck(self, run_time: float = 1.5):
        """Emphasizes baseline model bottleneck."""
        return Indicate(self.meter_b, color="#EF4444", scale_factor=1.05, run_time=run_time)

    def activate_contender_a(self, run_time: float = 1.5):
        """Emphasizes contender model."""
        return Indicate(self.meter_a, color="#34D399", scale_factor=1.08, run_time=run_time)

    def flash_victory_state(self, run_time: float = 2.0):
        """Celebrates contender outperforming baseline."""
        return AnimationGroup(
            Circumscribe(self.meter_a, color="#34D399", run_time=run_time * 0.6),
            Flash(self.delta_badge.get_center(), color="#34D399", num_lines=12, line_length=0.3, run_time=run_time * 0.5)
        )


class ComparativeCoordinateManifold(VGroup):
    """
    Mathematical comparative coordinate manifold for quantitative payoffs.
    Displays dual parametric coordinate bars on a calibrated axis with an analytical delta bracket.
    Zero SaaS cards, 100% 3Blue1Brown geometric data visualization.
    """
    def __init__(
        self,
        model_a_name: str = "Coding Agents",
        model_a_score: str = "95%",
        val_a: float = 0.95,
        model_b_name: str = "Classical TAMP",
        model_b_score: str = "47%",
        val_b: float = 0.47,
        delta_label: str = "⚡ +48.0% GENERALIZATION GAIN",
        **kwargs
    ):
        scale_val = kwargs.pop("scale", None)
        super().__init__(**kwargs)

        # 1. Calibrated Coordinate Axes (Zero LaTeX dependency)
        self.axes = Axes(
            x_range=[0, 3, 1],
            y_range=[0, 100, 25],
            x_length=4.6,
            y_length=3.4,
            axis_config={
                "color": "#334155",
                "stroke_width": 1.5,
                "include_ticks": True,
                "tick_size": 0.08
            }
        )

        # Clean custom Text labels for Y-axis without calling LaTeX
        self.y_labels = VGroup()
        for y_val in [0, 50, 100]:
            pt = self.axes.c2p(0, y_val)
            lbl = Text(f"{y_val}%", font=FONT_HELVETICA, font_size=8, color="#64748B").next_to(pt, LEFT, buff=0.08)
            self.y_labels.add(lbl)

        # 2. Glowing Parametric Columns
        # Column B (Classical Baseline)
        p_b_origin = self.axes.c2p(0.8, 0)
        p_b_top = self.axes.c2p(0.8, val_b * 100)
        h_b = p_b_top[1] - p_b_origin[1]
        self.bar_b = Rectangle(
            width=1.1, height=h_b,
            stroke_color="#38BDF8", stroke_width=1.8,
            fill_color="#082F49", fill_opacity=0.65
        ).move_to([p_b_origin[0], p_b_origin[1] + h_b / 2, 0])

        self.val_b_txt = Text(model_b_score, font=FONT_HELVETICA, font_size=18, color=WHITE, weight=BOLD).next_to(self.bar_b, UP, buff=0.12)
        self.name_b_txt = Text(model_b_name.upper()[:14], font=FONT_HELVETICA, font_size=9, color="#38BDF8", weight=BOLD).next_to(self.bar_b, DOWN, buff=0.15)

        # Column A (Contender Model)
        p_a_origin = self.axes.c2p(2.2, 0)
        p_a_top = self.axes.c2p(2.2, val_a * 100)
        h_a = p_a_top[1] - p_a_origin[1]
        self.bar_a = Rectangle(
            width=1.1, height=h_a,
            stroke_color=COLOR_MINT, stroke_width=2.2,
            fill_color="#064E3B", fill_opacity=0.75
        ).move_to([p_a_origin[0], p_a_origin[1] + h_a / 2, 0])

        self.val_a_txt = Text(model_a_score, font=FONT_HELVETICA, font_size=20, color=COLOR_MINT, weight=HEAVY).next_to(self.bar_a, UP, buff=0.12)
        self.name_a_txt = Text(model_a_name.upper()[:14], font=FONT_HELVETICA, font_size=9, color=COLOR_MINT, weight=BOLD).next_to(self.bar_a, DOWN, buff=0.15)

        # 3. Analytical Delta Line & Label
        top_b_y = self.bar_b.get_top()[1]
        top_a_y = self.bar_a.get_top()[1]
        self.delta_line = DashedLine(
            [self.bar_b.get_center()[0], top_b_y, 0],
            [self.bar_a.get_center()[0], top_b_y, 0],
            dash_length=0.08, stroke_color="#64748B", stroke_width=1.2
        )
        self.gain_arrow = DoubleArrow(
            [self.bar_a.get_right()[0] + 0.18, top_b_y, 0],
            [self.bar_a.get_right()[0] + 0.18, top_a_y, 0],
            color=COLOR_MINT, stroke_width=2.0, tip_length=0.12
        )
        self.delta_label = Text(
            delta_label,
            font=FONT_HELVETICA, font_size=12, color="#34D399", weight=HEAVY
        ).next_to(self.axes, DOWN, buff=0.35)
        if self.delta_label.width > 5.2:
            self.delta_label.scale_to_fit_width(5.2)

        self.add(
            self.axes, self.y_labels, self.bar_b, self.val_b_txt, self.name_b_txt,
            self.bar_a, self.val_a_txt, self.name_a_txt,
            self.delta_line, self.gain_arrow, self.delta_label
        )
        if scale_val is not None:
            self.scale(scale_val)

    def animate_draw(self, run_time: float = 2.5):
        """Draws axes, grows bars, and highlights differential gap."""
        return AnimationGroup(
            Create(self.axes, run_time=run_time * 0.4),
            FadeIn(self.y_labels, run_time=run_time * 0.3),
            GrowFromEdge(self.bar_b, DOWN, run_time=run_time * 0.5),
            GrowFromEdge(self.bar_a, DOWN, run_time=run_time * 0.6),
            FadeIn(self.val_b_txt, shift=UP * 0.1, run_time=run_time * 0.3),
            FadeIn(self.val_a_txt, shift=UP * 0.1, run_time=run_time * 0.3),
            FadeIn(self.name_b_txt, run_time=run_time * 0.3),
            FadeIn(self.name_a_txt, run_time=run_time * 0.3),
            Create(self.delta_line, run_time=run_time * 0.4),
            Create(self.gain_arrow, run_time=run_time * 0.4),
            FadeIn(self.delta_label, shift=UP * 0.1, run_time=run_time * 0.4),
            Indicate(self.delta_label, color="#A7F3D0", scale_factor=1.05, run_time=run_time * 0.4)
        )
