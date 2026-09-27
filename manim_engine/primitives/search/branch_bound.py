"""
Branch-and-Bound Pruning & Guillotine Laser Visual Primitives.
Visualizes incumbent objective ceilings, lower bound bounds,
laser severance slices, and subtree crystallization.
"""

from manim import *
import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from pipeline.config import FONT_HELVETICA, COLOR_MINT, COLOR_DANGER, COLOR_GOLD


class BranchAndBoundLaser(VGroup):
    """
    Parametric Branch-and-Bound Pruning Manager:
    - Global Incumbent Bound Bar: Horizontal golden ceiling line.
    - Local Lower Bound Badges: Display continuous relaxation bounds.
    - Guillotine Laser Blade: Slices branch when lower_bound >= incumbent.
    """
    def __init__(
        self,
        incumbent_value: float = 38.0,
        y_ceiling: float = 1.8,
        x_span: float = 6.4,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.incumbent_val = incumbent_value

        # Global Incumbent Ceiling Line
        self.ceiling_line = DashedLine(
            start=[-x_span / 2, y_ceiling, 0],
            end=[x_span / 2, y_ceiling, 0],
            color=COLOR_GOLD,
            stroke_width=2.0,
            dash_length=0.08
        )
        self.incumbent_badge = RoundedRectangle(
            width=2.4, height=0.45, corner_radius=0.08,
            color=COLOR_GOLD, fill_color="#3D2900", fill_opacity=0.92, stroke_width=1.2
        ).move_to([x_span / 2 - 1.2, y_ceiling + 0.32, 0])

        self.incumbent_txt = Text(
            f"INCUMBENT: z* = {incumbent_value:.1f}",
            font=FONT_HELVETICA,
            font_size=10,
            color=WHITE,
            weight=BOLD
        ).move_to(self.incumbent_badge)

        self.add(self.ceiling_line, self.incumbent_badge, self.incumbent_txt)

    def trigger_guillotine_prune(
        self,
        scene: Scene,
        branch_edge: Line,
        target_subtree: VGroup,
        lower_bound: float = 42.5,
        duration: float = 1.4
    ):
        """
        Executes guillotine laser slice across the branch,
        stamps PRUNED certificate, and crystallizes the subtree into a 15% ghost state.
        """
        mid_pt = branch_edge.get_center()

        # 1. Lower Bound Callout Badge
        badge_box = RoundedRectangle(
            width=2.2, height=0.40, corner_radius=0.08,
            color=COLOR_DANGER, fill_color="#450A0A", fill_opacity=0.95, stroke_width=1.4
        ).move_to(mid_pt + RIGHT * 1.2)
        badge_txt = Text(
            f"z_low = {lower_bound:.1f} ≥ z*",
            font=FONT_HELVETICA,
            font_size=10,
            color="#FECDD3",
            weight=BOLD
        ).move_to(badge_box)
        badge = VGroup(badge_box, badge_txt)

        scene.play(FadeIn(badge, shift=LEFT * 0.15), run_time=duration * 0.30)

        # 2. Guillotine Laser Slice Line
        laser = Line(
            mid_pt + UL * 0.45,
            mid_pt + DR * 0.45,
            color=COLOR_DANGER,
            stroke_width=4.0
        )
        scene.play(
            Create(laser),
            Flash(mid_pt, color=COLOR_DANGER, line_length=0.25, num_lines=8),
            run_time=duration * 0.35
        )

        # 3. Crystallize Subtree into Frosted Ghost (15% opacity)
        scene.play(
            target_subtree.animate.set_opacity(0.15),
            branch_edge.animate.set_opacity(0.15),
            laser.animate.set_stroke(width=1.5, opacity=0.4),
            run_time=duration * 0.35
        )
