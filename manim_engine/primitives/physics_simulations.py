"""
The Model Verse — Physics & Geometric Simulators (Visual Engine 5.0)
High-end, living mathematical simulations and continuous physical dynamics
for 9:16 mobile YouTube Shorts. Replaces static SaaS cards with authentic
3Blue1Brown-caliber vector fields, neural waves, optical prisms, and landscapes.

Primitives:
1. SimulationVectorField: 2D curved streamlines with flowing glowing particles (Flow matching, latent manifolds).
2. SimulationNeuralActivation: Multi-layer network with propagating synaptic activation wave (Deep learning, SAEs).
3. SimulationAttentionPrism: Translucent prism splitting token beam into Q/K/V vectors and attention matrix.
4. SimulationOptimizationLandscape: 2.5D contour elevation manifold with rolling gradient descent sphere.
"""

import os
import sys
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any
from manim import *
from manim.utils.rate_functions import ease_out_sine, ease_in_sine

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import FONT_HELVETICA
from manim_engine.primitives.typography import CleanText
from manim_engine.primitives.visual_compositions import (
    BaseBlueprintComposition,
    COLOR_CYAN, COLOR_MINT, COLOR_AMBER, COLOR_CORAL,
    COLOR_PURPLE, COLOR_WHITE, COLOR_SLATE, COLOR_DARK_SLATE, COLOR_PANEL_BG
)


class SimulationVectorField(BaseBlueprintComposition):
    """
    Living 2D continuous vector flow field with curved streamlines and
    illuminated particles traveling along latent trajectories.
    Ideal for diffusion models, flow matching, continuous dynamics, and robotics.
    """
    def __init__(
        self,
        field_title: str = "CONTINUOUS LATENT FLOW",
        source_label: str = "Source Distribution",
        target_label: str = "Target Manifold",
        stream_formula: str = "dx/dt = v_theta(x, t)",
        accent_color: str = COLOR_CYAN,
        **kwargs
    ):
        super().__init__(accent_color=accent_color, **kwargs)

        # 1. Coordinate Grid Backdrop (subtle 3b1b mathematical plane)
        grid_plane = NumberPlane(
            x_range=[-3.2, 3.2, 0.8],
            y_range=[-3.4, 3.4, 0.8],
            x_length=6.4,
            y_length=6.8,
            background_line_style={
                "stroke_color": COLOR_DARK_SLATE,
                "stroke_width": 1.2,
                "stroke_opacity": 0.35
            },
            axis_config={"stroke_color": "#475569", "stroke_width": 1.6}
        ).move_to([0, 0.3, 0])

        # 2. Curved Streamlines with organic S-curve flow
        self.streamlines = VGroup()
        stream_configs = [
            ([-2.8, -2.0, 0], [-1.2, -0.6, 0], [0.6, 0.6, 0], [2.6, 2.2, 0], COLOR_CYAN),
            ([-2.8, -0.8, 0], [-0.8, 0.6, 0], [0.8, 1.8, 0], [2.6, 3.0, 0], COLOR_MINT),
            ([-2.8, 0.4, 0], [-0.6, 1.8, 0], [0.8, 2.4, 0], [2.6, 3.4, 0], COLOR_PURPLE),
            ([-2.8, -2.6, 0], [-1.2, -1.8, 0], [0.4, -0.8, 0], [2.6, 0.6, 0], COLOR_AMBER),
            ([-2.8, -1.4, 0], [-1.0, -0.2, 0], [0.5, 1.2, 0], [2.6, 1.6, 0], COLOR_CYAN)
        ]

        for s, c1, c2, e, col in stream_configs:
            curve = CubicBezier(s, c1, c2, e, color=col, stroke_width=3.2, stroke_opacity=0.75)
            arr = Arrow(
                start=curve.point_from_proportion(0.68),
                end=curve.point_from_proportion(0.76),
                color=col,
                buff=0,
                stroke_width=2.5,
                max_tip_length_to_length_ratio=0.35
            )
            self.streamlines.add(VGroup(curve, arr))

        # 3. Luminous Data Particles along streamlines
        self.particles = VGroup()
        for i, (s, c1, c2, e, col) in enumerate(stream_configs):
            pt = CubicBezier(s, c1, c2, e).point_from_proportion(0.20 + (i * 0.15))
            glow_halo = Dot(point=pt, radius=0.18, color=col, fill_opacity=0.25)
            core_dot = Dot(point=pt, radius=0.08, color=COLOR_WHITE, fill_opacity=1.0)
            self.particles.add(VGroup(glow_halo, core_dot))

        # 4. Source & Target Domain Boundaries
        src_capsule = RoundedRectangle(
            corner_radius=0.12, width=2.4, height=0.55,
            color=COLOR_CORAL, fill_color=COLOR_PANEL_BG, fill_opacity=0.92, stroke_width=1.8
        ).move_to([-1.8, -2.8, 0])
        src_lbl = CleanText(source_label[:20].upper(), font=FONT_HELVETICA, font_size=9, color=COLOR_CORAL, weight=BOLD).move_to(src_capsule)
        src_grp = VGroup(src_capsule, src_lbl)

        tgt_capsule = RoundedRectangle(
            corner_radius=0.12, width=2.4, height=0.55,
            color=COLOR_MINT, fill_color=COLOR_PANEL_BG, fill_opacity=0.92, stroke_width=1.8
        ).move_to([1.8, 3.4, 0])
        tgt_lbl = CleanText(target_label[:20].upper(), font=FONT_HELVETICA, font_size=9, color=COLOR_MINT, weight=BOLD).move_to(tgt_capsule)
        tgt_grp = VGroup(tgt_capsule, tgt_lbl)

        # 5. Math Vector Velocity Chip (Placed cleanly below grid)
        vel_chip = RoundedRectangle(
            corner_radius=0.1, width=3.4, height=0.5,
            color=COLOR_SLATE, fill_color=COLOR_PANEL_BG, fill_opacity=0.92, stroke_width=1.5
        ).move_to([0, -3.8, 0])
        vel_txt = CleanText(stream_formula[:28], font=FONT_HELVETICA, font_size=11, color=COLOR_WHITE, weight=BOLD).move_to(vel_chip)
        vel_grp = VGroup(vel_chip, vel_txt)
        self.grid_plane = grid_plane
        self.src_grp = src_grp
        self.tgt_grp = tgt_grp
        self.vel_grp = vel_grp

        self.content_group.add(grid_plane, self.streamlines, self.particles, src_grp, tgt_grp, vel_grp)
        self.kinetic_elements.add(self.streamlines, self.particles)
        self.add(self.title, self.sub, self.content_group)

    def get_entrance_animation(self, run_time: float = 1.0) -> Animation:
        """Progressive build: plane and capsules appear, streamlines draw into view."""
        curve_anims = [Create(s[0], rate_func=ease_out_sine) for s in self.streamlines]
        part_anims = [FadeIn(p, scale=0.5) for p in self.particles]
        return AnimationGroup(
            FadeIn(self.title, shift=DOWN * 0.1),
            FadeIn(self.sub, shift=DOWN * 0.1),
            FadeIn(self.grid_plane),
            FadeIn(self.src_grp),
            FadeIn(self.tgt_grp),
            FadeIn(self.vel_grp),
            *curve_anims,
            *part_anims,
            run_time=run_time
        )

    def get_kinetic_animation(self, run_time: float = 1.8) -> Animation:
        """Accelerates flow along streamlines with glowing particle expansion."""
        anims = []
        for p in self.particles:
            anims.append(p.animate.scale(1.4))
        for s in self.streamlines:
            anims.append(s[0].animate.set_stroke(width=5.0, opacity=1.0))
        return Succession(
            AnimationGroup(*anims, run_time=run_time * 0.6, rate_func=ease_out_sine),
            AnimationGroup(
                *[p.animate.scale(1.0 / 1.4) for p in self.particles] +
                [s[0].animate.set_stroke(width=3.2, opacity=0.75) for s in self.streamlines],
                run_time=run_time * 0.4, rate_func=ease_in_sine
            )
        )

    def get_ambient_animation(self, run_time: float = 3.0) -> Animation:
        """Continuous micro-drift of particles and subtle shimmer."""
        return AnimationGroup(
            self.particles.animate(rate_func=there_and_back, run_time=run_time).shift(RIGHT * 0.35 + UP * 0.25),
            self.streamlines.animate(rate_func=there_and_back, run_time=run_time).set_stroke(opacity=0.9)
        )


class SimulationNeuralActivation(BaseBlueprintComposition):
    """
    Multi-layer deep neural network with visible glowing synapses and
    a forward-propagating electrical activation wave.
    Ideal for Transformer representations, Sparse Autoencoders, and deep networks.
    """
    def __init__(
        self,
        input_label: str = "Input Latents",
        hidden_label: str = "Sparse Features",
        output_label: str = "Target Output",
        accent_color: str = COLOR_PURPLE,
        **kwargs
    ):
        super().__init__(accent_color=accent_color, **kwargs)

        # 3 Vertical Layers of Neurons (Taller vertical span for 9:16)
        self.layers = []
        layer_x = [-2.2, 0.0, 2.2]
        layer_counts = [4, 6, 4]
        layer_colors = [COLOR_CYAN, accent_color, COLOR_MINT]

        self.neurons = VGroup()
        self.neuron_groups = []

        for lx, count, col in zip(layer_x, layer_counts, layer_colors):
            y_span = 5.0
            ys = np.linspace(-y_span / 2, y_span / 2, count) + 0.2
            grp = VGroup()
            for y in ys:
                glow = Dot(point=[lx, y, 0], radius=0.22, color=col, fill_opacity=0.22)
                core = Dot(point=[lx, y, 0], radius=0.11, color=COLOR_WHITE, fill_opacity=0.95)
                n_mobj = VGroup(glow, core)
                grp.add(n_mobj)
                self.neurons.add(n_mobj)
            self.neuron_groups.append(grp)

        # Synaptic connections (L0 -> L1, L1 -> L2)
        self.synapses = VGroup()
        for i in range(len(self.neuron_groups) - 1):
            curr_layer = self.neuron_groups[i]
            next_layer = self.neuron_groups[i + 1]
            for n1 in curr_layer:
                for n2 in next_layer:
                    syn = Line(
                        start=n1[1].get_center(),
                        end=n2[1].get_center(),
                        color=COLOR_SLATE,
                        stroke_width=1.1,
                        stroke_opacity=0.28
                    )
                    self.synapses.add(syn)

        # Active high-weight conduits (highlighted synapses)
        self.active_synapses = VGroup()
        active_pairs = [(0, 1), (1, 2), (2, 3), (3, 4), (1, 3)]
        for i in range(len(self.neuron_groups) - 1):
            curr_layer = self.neuron_groups[i]
            next_layer = self.neuron_groups[i + 1]
            for idx1, idx2 in active_pairs:
                if idx1 < len(curr_layer) and idx2 < len(next_layer):
                    glow_syn = Line(
                        start=curr_layer[idx1][1].get_center(),
                        end=next_layer[idx2][1].get_center(),
                        color=accent_color,
                        stroke_width=2.8,
                        stroke_opacity=0.85
                    )
                    self.active_synapses.add(glow_syn)

        # Layer Labels at Top
        lbl_in = CleanText(input_label[:18].upper(), font=FONT_HELVETICA, font_size=10, color=COLOR_CYAN, weight=BOLD).move_to([-2.2, 3.4, 0])
        lbl_hid = CleanText(hidden_label[:18].upper(), font=FONT_HELVETICA, font_size=10, color=accent_color, weight=BOLD).move_to([0.0, 3.4, 0])
        lbl_out = CleanText(output_label[:18].upper(), font=FONT_HELVETICA, font_size=10, color=COLOR_MINT, weight=BOLD).move_to([2.2, 3.4, 0])

        self.layer_labels = VGroup(lbl_in, lbl_hid, lbl_out)

        self.content_group.add(self.synapses, self.active_synapses, self.neurons, lbl_in, lbl_hid, lbl_out)
        self.kinetic_elements.add(self.active_synapses, self.neurons)
        self.add(self.title, self.sub, self.content_group)

    def get_entrance_animation(self, run_time: float = 1.0) -> Animation:
        """Progressive build: layers grow from center and synapses draw."""
        neuron_anims = [GrowFromCenter(n) for n in self.neurons]
        synapse_anims = [Create(s) for s in self.active_synapses]
        return AnimationGroup(
            FadeIn(self.title, shift=DOWN * 0.1),
            FadeIn(self.sub, shift=DOWN * 0.1),
            FadeIn(self.synapses),
            FadeIn(self.layer_labels),
            *synapse_anims,
            *neuron_anims,
            run_time=run_time
        )

    def get_kinetic_animation(self, run_time: float = 1.8) -> Animation:
        """Cascading electrical pulse propagating from left to right."""
        t_step = run_time / 3.0
        return Succession(
            AnimationGroup(
                self.neuron_groups[0].animate.scale(1.25),
                rate_func=there_and_back, run_time=t_step
            ),
            AnimationGroup(
                self.active_synapses.animate.set_stroke(width=4.5, color=COLOR_WHITE),
                self.neuron_groups[1].animate.scale(1.3),
                rate_func=there_and_back, run_time=t_step
            ),
            AnimationGroup(
                self.neuron_groups[2].animate.scale(1.25),
                rate_func=there_and_back, run_time=t_step
            )
        )

    def get_ambient_animation(self, run_time: float = 3.0) -> Animation:
        """Gentle synaptic breathing."""
        return AnimationGroup(
            self.active_synapses.animate(rate_func=there_and_back, run_time=run_time).set_stroke(opacity=0.5),
            self.neuron_groups[1].animate(rate_func=there_and_back, run_time=run_time).scale(1.05)
        )


class SimulationAttentionPrism(BaseBlueprintComposition):
    """
    Translucent optical prism splitting a concentrated token beam into
    Query, Key, and Value rays that project onto a 3x3 attention correlation matrix.
    Ideal for Attention mechanisms, Multi-Head projections, and routing.
    """
    def __init__(
        self,
        token_label: str = "Input Token Vector",
        matrix_title: str = "Attention Correlation",
        accent_color: str = COLOR_AMBER,
        **kwargs
    ):
        super().__init__(accent_color=accent_color, **kwargs)

        # 1. Incoming Token Laser Beam (top-down)
        self.in_beam = Line(
            start=[0, 3.6, 0], end=[0, 1.8, 0],
            color=COLOR_WHITE, stroke_width=6.0
        )
        in_lbl = CleanText(token_label[:20].upper(), font=FONT_HELVETICA, font_size=10, color=COLOR_WHITE, weight=BOLD).next_to(self.in_beam, UP, buff=0.12)

        # 2. Translucent Optical Prism (Hexagonal Glass Core)
        self.prism = RegularPolygon(
            n=6, radius=0.85, color=COLOR_CYAN,
            fill_color="#0F172A", fill_opacity=0.90, stroke_width=2.5
        ).move_to([0, 1.0, 0])
        prism_lbl = CleanText("Q/K/V", font=FONT_HELVETICA, font_size=12, color=COLOR_CYAN, weight=BOLD).move_to(self.prism)

        # 3. Attention Correlation Heatmap (3x3 grid, centered at y = -1.6)
        self.heatmap = VGroup()
        grid_start_x = -0.9
        grid_start_y = -0.8
        cell_size = 0.9
        heat_vals = [
            [0.9, 0.2, 0.4],
            [0.1, 0.85, 0.3],
            [0.3, 0.1, 0.95]
        ]
        col_centers = []
        for c in range(3):
            col_centers.append(grid_start_x + c * cell_size)

        for r in range(3):
            for c in range(3):
                val = heat_vals[r][c]
                col = interpolate_color(ManimColor("#1E293B"), ManimColor(COLOR_AMBER), val)
                cell = Square(side_length=cell_size, color=COLOR_DARK_SLATE, stroke_width=1.2, fill_color=col, fill_opacity=0.88).move_to(
                    [col_centers[c], grid_start_y - r * cell_size, 0]
                )
                txt = CleanText(f"{val:.1f}", font=FONT_HELVETICA, font_size=10, color=COLOR_WHITE if val > 0.5 else COLOR_SLATE).move_to(cell)
                self.heatmap.add(VGroup(cell, txt))

        # Refracted Output Beams landing directly on top of each heatmap column
        self.beam_q = Line(start=[0, 0.8, 0], end=[col_centers[0], grid_start_y + 0.5, 0], color=COLOR_CYAN, stroke_width=4.0)
        self.beam_k = Line(start=[0, 0.8, 0], end=[col_centers[1], grid_start_y + 0.5, 0], color=COLOR_AMBER, stroke_width=4.0)
        self.beam_v = Line(start=[0, 0.8, 0], end=[col_centers[2], grid_start_y + 0.5, 0], color=COLOR_MINT, stroke_width=4.0)
        self.refracted_beams = VGroup(self.beam_q, self.beam_k, self.beam_v)

        # Clean bottom title badge
        mat_badge = RoundedRectangle(corner_radius=0.1, width=3.4, height=0.45, color=COLOR_AMBER, fill_color=COLOR_PANEL_BG, fill_opacity=0.92, stroke_width=1.5).move_to([0, -3.45, 0])
        mat_txt = CleanText(matrix_title[:24].upper(), font=FONT_HELVETICA, font_size=10, color=COLOR_AMBER, weight=BOLD).move_to(mat_badge)
        mat_grp = VGroup(mat_badge, mat_txt)
        self.in_lbl = in_lbl
        self.prism_lbl = prism_lbl
        self.mat_grp = mat_grp

        self.content_group.add(self.in_beam, in_lbl, self.prism, prism_lbl, self.refracted_beams, self.heatmap, mat_grp)
        self.kinetic_elements.add(self.in_beam, self.refracted_beams, self.heatmap)
        self.add(self.title, self.sub, self.content_group)

    def get_entrance_animation(self, run_time: float = 1.0) -> Animation:
        """Progressive build: incoming beam hits prism and splits into heatmap."""
        beam_anims = [Create(b) for b in self.refracted_beams]
        return AnimationGroup(
            FadeIn(self.title, shift=DOWN * 0.1),
            FadeIn(self.sub, shift=DOWN * 0.1),
            Create(self.in_beam),
            FadeIn(self.in_lbl),
            FadeIn(self.prism, scale=0.8),
            FadeIn(self.prism_lbl),
            *beam_anims,
            FadeIn(self.heatmap, scale=0.9),
            FadeIn(self.mat_grp),
            run_time=run_time
        )

    def get_kinetic_animation(self, run_time: float = 1.8) -> Animation:
        """Laser strike through prism illuminating heatmap diagonal."""
        return Succession(
            AnimationGroup(
                self.in_beam.animate.set_stroke(width=9.0, color="#67E8F9"),
                self.prism.animate.scale(1.1).set_stroke(color=COLOR_WHITE),
                run_time=run_time * 0.4
            ),
            AnimationGroup(
                self.refracted_beams.animate.set_stroke(width=6.0),
                self.heatmap[0].animate.scale(1.15),
                self.heatmap[4].animate.scale(1.15),
                self.heatmap[8].animate.scale(1.15),
                run_time=run_time * 0.6,
                rate_func=there_and_back
            )
        )

    def get_ambient_animation(self, run_time: float = 3.0) -> Animation:
        """Gentle laser beam pulsation."""
        return self.refracted_beams.animate(rate_func=there_and_back, run_time=run_time).set_stroke(opacity=0.6)


class SimulationOptimizationLandscape(BaseBlueprintComposition):
    """
    2.5D contour elevation landscape with gradient descent vector arrows
    and an illuminated optimization ball descending into the global minimum.
    Ideal for optimization, loss functions, benchmarks, and training breakthroughs.
    """
    def __init__(
        self,
        landscape_title: str = "LOSS SURFACE CONVERGENCE",
        optima_label: str = "Global Minimum Basin",
        accent_color: str = COLOR_MINT,
        **kwargs
    ):
        super().__init__(accent_color=accent_color, **kwargs)

        # Center positioned vertically in the main viewport
        center_pt = [0.2, 0.2, 0]

        # 1. Concentric Contour Ellipses (Elevation levels)
        self.contours = VGroup()
        radii_x = [3.4, 2.7, 2.0, 1.3, 0.6]
        radii_y = [2.2, 1.7, 1.25, 0.8, 0.38]
        alphas = [0.25, 0.40, 0.55, 0.75, 0.95]

        for rx, ry, al in zip(radii_x, radii_y, alphas):
            col = interpolate_color(ManimColor(COLOR_CORAL), ManimColor(COLOR_MINT), al)
            ellipse = Ellipse(
                width=rx * 2, height=ry * 2,
                color=col, stroke_width=2.0, stroke_opacity=0.7,
                fill_color=col, fill_opacity=0.08
            ).move_to(center_pt)
            self.contours.add(ellipse)

        # 2. Gradient Descent Trajectory Path
        traj_points = [
            [-2.2, 2.0, 0],
            [-1.4, 1.4, 0],
            [-0.6, 0.8, 0],
            [-0.1, 0.4, 0],
            center_pt
        ]
        self.trajectory_line = VMobject(color=COLOR_WHITE, stroke_width=2.5, stroke_opacity=0.7)
        self.trajectory_line.set_points_smoothly([np.array(p) for p in traj_points])

        # 3. Optimization Sphere (Ball rolling down gradient)
        ball_glow = Dot(point=center_pt, radius=0.25, color=COLOR_MINT, fill_opacity=0.3)
        ball_core = Dot(point=center_pt, radius=0.12, color=COLOR_WHITE, fill_opacity=1.0)
        self.opt_ball = VGroup(ball_glow, ball_core)

        # 4. Global Minimum Target Pin & Badge
        min_flag = VGroup(
            Line(start=center_pt, end=[center_pt[0], center_pt[1] + 0.9, 0], color=COLOR_MINT, stroke_width=2.2),
            Polygon([center_pt[0], center_pt[1] + 0.9, 0], [center_pt[0] + 0.8, center_pt[1] + 0.65, 0], [center_pt[0], center_pt[1] + 0.4, 0], color=COLOR_MINT, fill_color=COLOR_MINT, fill_opacity=0.85)
        )
        min_badge = RoundedRectangle(corner_radius=0.1, width=2.8, height=0.45, color=COLOR_MINT, fill_color=COLOR_PANEL_BG, fill_opacity=0.92, stroke_width=1.5).move_to([center_pt[0] + 1.8, center_pt[1] + 0.9, 0])
        min_txt = CleanText(optima_label[:20].upper(), font=FONT_HELVETICA, font_size=9, color=COLOR_MINT, weight=BOLD).move_to(min_badge)
        min_grp = VGroup(min_flag, min_badge, min_txt)

        # 5. Gradient Descent Vectors (Arrows pointing inward)
        self.grad_arrows = VGroup()
        arrow_starts = [
            [-2.4, -1.0, 0],
            [2.6, 1.4, 0],
            [-1.8, 2.4, 0],
            [2.2, -1.2, 0]
        ]
        for start_pos in arrow_starts:
            arr = Arrow(
                start=start_pos,
                end=center_pt,
                color=COLOR_SLATE,
                buff=0.3,
                stroke_width=1.8,
                max_tip_length_to_length_ratio=0.25
            )
            self.grad_arrows.add(arr)

        self.min_grp = min_grp

        self.content_group.add(self.contours, self.grad_arrows, self.trajectory_line, min_grp, self.opt_ball)
        self.kinetic_elements.add(self.opt_ball, self.trajectory_line, self.contours)
        self.add(self.title, self.sub, self.content_group)

    def get_entrance_animation(self, run_time: float = 1.0) -> Animation:
        """Progressive build: contour rings expand and optimization sphere descends."""
        return AnimationGroup(
            FadeIn(self.title, shift=DOWN * 0.1),
            FadeIn(self.sub, shift=DOWN * 0.1),
            *[GrowFromCenter(c) for c in self.contours],
            Create(self.trajectory_line),
            FadeIn(self.grad_arrows),
            FadeIn(self.min_grp),
            GrowFromCenter(self.opt_ball),
            run_time=run_time
        )

    def get_kinetic_animation(self, run_time: float = 1.8) -> Animation:
        """Optimization ball rolling down trajectory to basin with pulsing contours."""
        return Succession(
            AnimationGroup(
                self.opt_ball.animate.scale(1.3).set_color(COLOR_WHITE),
                self.contours.animate.set_stroke(width=3.5),
                run_time=run_time * 0.5
            ),
            AnimationGroup(
                self.opt_ball.animate.scale(1.0 / 1.3).set_color(COLOR_MINT),
                self.contours.animate.set_stroke(width=2.0),
                run_time=run_time * 0.5
            )
        )

    def get_ambient_animation(self, run_time: float = 3.0) -> Animation:
        """Gentle pulsing ripples across contour lines."""
        return self.contours.animate(rate_func=there_and_back, run_time=run_time).set_stroke(opacity=0.35)


# Register Physics & Geometric Simulation layouts
PHYSICS_SIMULATION_REGISTRY = {
    "vector_flow_field": SimulationVectorField,
    "flow_field": SimulationVectorField,
    "latent_manifold": SimulationVectorField,
    "continuous_dynamics": SimulationVectorField,
    "neural_activation_wave": SimulationNeuralActivation,
    "synaptic_network": SimulationNeuralActivation,
    "deep_network": SimulationNeuralActivation,
    "sparse_autoencoder": SimulationNeuralActivation,
    "attention_prism_refraction": SimulationAttentionPrism,
    "prism_refraction": SimulationAttentionPrism,
    "optical_routing": SimulationAttentionPrism,
    "qkv_projection": SimulationAttentionPrism,
    "optimization_landscape": SimulationOptimizationLandscape,
    "loss_landscape": SimulationOptimizationLandscape,
    "gradient_descent": SimulationOptimizationLandscape,
    "convergence_basin": SimulationOptimizationLandscape
}

# Auto-register into blueprint composition registry
try:
    from manim_engine.primitives.visual_compositions import BLUEPRINT_COMPOSITION_REGISTRY
    BLUEPRINT_COMPOSITION_REGISTRY.update(PHYSICS_SIMULATION_REGISTRY)
except Exception:
    pass
