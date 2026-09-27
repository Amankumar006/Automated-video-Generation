"""
Coupled State-Space Canvas & Constraint Sheaves for Task and Motion Planning (TAMP).
Coordinates discrete symbolic logic (top pane) with continuous geometry (bottom pane)
in 9:16 vertical chalkboard space.
"""

from manim import *
import numpy as np
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# Add project root for config imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from pipeline.config import FONT_HELVETICA, COLOR_MINT, COLOR_DANGER, COLOR_GOLD, COLOR_CARD_BG


class CoupledCanvas(VGroup):
    """
    Vertical 9:16 Dual-Manifold Canvas Coordinator.
    Top Pane: Discrete Task Space / Logic Skeleton / PDDL
    Bottom Pane: Continuous Robot Workspace / C-Space
    """
    def __init__(
        self,
        title: Optional[str] = None,
        top_bounds=(-3.2, 3.2, 0.8, 5.0),
        bottom_bounds=(-3.2, 3.2, -4.6, 0.4),
        **kwargs
    ):
        super().__init__(**kwargs)
        self.title_str = title
        self.top_bounds = top_bounds
        self.bottom_bounds = bottom_bounds

        tx_min, tx_max, ty_min, ty_max = top_bounds
        bx_min, bx_max, by_min, by_max = bottom_bounds

        # Subtle horizontal manifold division line (no card boxes)
        mid_y = (ty_min + by_max) / 2
        self.manifold_divider = DashedLine(
            start=[-3.2, mid_y, 0],
            end=[3.2, mid_y, 0],
            dash_length=0.15,
            dashed_ratio=0.5,
            stroke_color="#334155",
            stroke_width=1.0,
            stroke_opacity=0.6
        )

        # Organic manifold labels floating on chalkboard
        self.discrete_label = Text(
            "S_discrete : Symbolic Task Plan",
            font=FONT_HELVETICA,
            font_size=13,
            color="#94A3B8"
        ).move_to([-0.8, ty_max - 0.25, 0])

        self.continuous_label = Text(
            "C-Space : Continuous Configuration Manifold",
            font=FONT_HELVETICA,
            font_size=13,
            color="#34D399"
        ).move_to([-0.3, mid_y - 0.25, 0])

        # Coordinate Grid inside continuous pane (floating without box)
        self.continuous_axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-2.2, 2.2, 1],
            x_length=(bx_max - bx_min) * 0.88,
            y_length=(by_max - by_min) * 0.72,
            axis_config={"color": "#334155", "stroke_width": 1.0, "include_ticks": True}
        ).move_to([(bx_min + bx_max) / 2, (by_min + by_max) / 2 - 0.2, 0])

        self.add(
            self.manifold_divider,
            self.discrete_label,
            self.continuous_label,
            self.continuous_axes
        )

    def discrete_to_point(self, u: float, v: float) -> np.ndarray:
        """
        Maps normalized discrete pane coordinates (u in [-1, 1], v in [-1, 1])
        to absolute Manim canvas points.
        """
        tx_min, tx_max, ty_min, ty_max = self.top_bounds
        cx = (tx_min + tx_max) / 2
        cy = (ty_min + ty_max) / 2
        w = (tx_max - tx_min) * 0.42
        h = (ty_max - ty_min - 0.5) * 0.40
        return np.array([cx + u * w, cy + v * h - 0.2, 0.0])

    def continuous_to_point(self, x: float, y: float) -> np.ndarray:
        """Maps continuous state coordinates (x, y) to scene points."""
        return self.continuous_axes.c2p(x, y)


class CoupledNode(VGroup):
    """
    A discrete action or predicate node that can project a constraint sheaf
    downward into the continuous configuration space.
    """
    def __init__(
        self,
        title: str,
        symbol: str,
        status: str = "idle",
        width: float = 2.4,
        height: float = 0.7,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.status = status

        border_col = {
            "idle": "#38BDF8",
            "active": COLOR_MINT,
            "failed": COLOR_DANGER
        }.get(status, "#38BDF8")

        fill_col = {
            "idle": "#0F172A",
            "active": "#064E3B",
            "failed": "#450A0A"
        }.get(status, "#0F172A")

        self.core = Circle(
            radius=0.32,
            color=border_col,
            stroke_width=2.0,
            fill_color="#0A0D14",
            fill_opacity=0.8
        )
        self.halo = Circle(
            radius=0.40,
            color=border_col,
            stroke_width=1.0,
            stroke_opacity=0.35
        )
        self.sym_text = Text(symbol, font=FONT_HELVETICA, font_size=13, color=WHITE, weight=BOLD).move_to(self.core)
        self.title_text = Text(title, font=FONT_HELVETICA, font_size=11, color="#E2E8F0").next_to(self.halo, UP, buff=0.10)

        self.add(self.halo, self.core, self.sym_text, self.title_text)

    @property
    def anchor_point(self) -> np.ndarray:
        return self.core.get_bottom()


class ConstraintProjectionSheaf(VGroup):
    """
    Parametric volumetric beam connecting a discrete action node (top)
    to a continuous target region or obstacle slice (bottom).
    """
    def __init__(
        self,
        coupled_node: CoupledNode,
        continuous_target: Mobject,
        color: str = "#38BDF8",
        opacity: float = 0.18,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.coupled_node = coupled_node
        self.continuous_target = continuous_target
        self.sheaf_color = color
        self.base_opacity = opacity

        p_src = getattr(coupled_node, "anchor_point", coupled_node.get_bottom())
        p_top = continuous_target.get_top()
        p_bot = continuous_target.get_bottom()

        self.sheaf_polygon = Polygon(
            p_src + LEFT * 0.15,
            p_src + RIGHT * 0.15,
            p_top + RIGHT * 0.1,
            p_bot + LEFT * 0.1,
            stroke_width=1.2,
            stroke_color=color,
            fill_color=color,
            fill_opacity=opacity
        )
        self.add(self.sheaf_polygon)

    def pulse_beam(self, run_time: float = 1.2):
        """Returns animation pulsing the constraint beam."""
        return AnimationGroup(
            self.sheaf_polygon.animate(run_time=run_time * 0.5).set_opacity(0.40).set_stroke(width=2.2),
            self.sheaf_polygon.animate(run_time=run_time * 0.5).set_opacity(self.base_opacity).set_stroke(width=1.2)
        )


class GeometricRefinementPulse:
    """
    Animated sequence coordinating forward continuous trajectory probe,
    collision contact flash, backward invalidation shockwave, and discrete pruning.
    """
    @staticmethod
    def trigger_failure(
        scene: Scene,
        coupled_node: CoupledNode,
        sheaf: ConstraintProjectionSheaf,
        collision_point: np.ndarray,
        duration: float = 2.0
    ):
        # 1. Forward probe along projection sheaf
        probe = Dot(point=coupled_node.anchor_point, color="#38BDF8", radius=0.1)
        scene.play(
            FadeIn(probe),
            probe.animate.move_to(collision_point),
            run_time=duration * 0.30,
            rate_func=linear
        )

        # 2. Collision Contact Explosion & Witness Badge
        contact_ring = Circle(radius=0.12, color=COLOR_DANGER, stroke_width=4.0).move_to(collision_point)
        flash = Flash(collision_point, color=COLOR_DANGER, line_length=0.25, num_lines=8)
        witness_badge = Text("q_coll: INFEASIBLE", font=FONT_HELVETICA, font_size=10, color="#FECDD3", weight=BOLD)
        witness_card = RoundedRectangle(
            width=1.9, height=0.35, corner_radius=0.08,
            color=COLOR_DANGER, fill_color="#450A0A", fill_opacity=0.9
        ).move_to(collision_point + UP * 0.38)
        witness_badge.move_to(witness_card)
        witness = VGroup(witness_card, witness_badge)

        scene.play(
            FadeOut(probe),
            contact_ring.animate.scale(4.0).set_opacity(0),
            flash,
            FadeIn(witness, shift=UP * 0.1),
            run_time=duration * 0.25
        )

        # 3. Backward Invalidation Shockwave
        shockwave = Dot(point=collision_point, color=COLOR_DANGER, radius=0.12)
        sheaf.sheaf_polygon.set_color(COLOR_DANGER)
        scene.play(
            shockwave.animate.move_to(coupled_node.anchor_point),
            run_time=duration * 0.25,
            rate_func=rush_into
        )

        # 4. Prune Discrete Node (Red Cross / Slash)
        c_center = coupled_node.core.get_center()
        r = coupled_node.core.radius
        slash1 = Line(
            c_center + np.array([-r, -r, 0]) * 0.85,
            c_center + np.array([r, r, 0]) * 0.85,
            color=COLOR_DANGER,
            stroke_width=3.0
        )
        slash2 = Line(
            c_center + np.array([-r, r, 0]) * 0.85,
            c_center + np.array([r, -r, 0]) * 0.85,
            color=COLOR_DANGER,
            stroke_width=3.0
        )
        cross = VGroup(slash1, slash2)
        scene.play(
            FadeOut(shockwave),
            coupled_node.core.animate.set_stroke(color=COLOR_DANGER).set_fill("#450A0A", opacity=0.92),
            Create(cross),
            sheaf.animate.set_opacity(0.06),
            run_time=duration * 0.20
        )
        return witness, cross
