"""
The Model Verse — Script-Driven Visual Motifs (Visual Engine 3.0)
High-end, bespoke 3Blue1Brown procedural animations for technical and physical analogies:
1. ScriptWaveInterference: Dual Wave Collision & Superposition
2. ScriptRadioTunerDial: Retro-Futuristic Radio Tuner Dial & Static Channel Blending
3. ScriptSubspacePacking: Coordinate Plane & Almost-Orthogonal Vector Packing
4. ScriptPrismDisentangler: Optical Prism Beam Disentangler & Linear Decoder
5. ScriptBranchingOutputs: Single Forward Pass Branching into Dual Output Answers
6. ScriptTreeSearchPruning: MCTS / Reasoning Search Tree with Optimal Chain & Pruning
7. ScriptDiffusionDenoising: Diffusion & Flow Matching Noise-to-Latent Trajectory
8. ScriptAttentionRouting: Multi-Head Attention / MoE Router Laser Dispatch
9. ScriptMemoryKVBuffer: Streaming KV-Cache Buffer with Linear Eviction & Savings
10. ScriptComparativeBenchmarkBars: Horizontal Benchmark Bars replacing generic gauges
11. ScriptCustomFlow: Universal 3-Stage Pipeline for Arbitrary Conceptual Flow
"""

from manim import *
import numpy as np
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import FONT_HELVETICA
from manim_engine.primitives.typography import CleanText

# Alias Text -> CleanText so all procedural script motifs render with flawless subpixel typography
Text = CleanText


class ScriptWaveInterference(VGroup):
    """
    Two distinct traveling sinusoidal waves colliding into an overlapping interference wave.
    """
    def __init__(
        self,
        signal_a_label: str = "THOUGHT 1 (SIGNAL A)",
        signal_b_label: str = "THOUGHT 2 (SIGNAL B)",
        result_label: str = "OVERLAPPING SUPERPOSITION (CHAOTIC BLEND)",
        result_sub: str = "Two thoughts packed into one noisy channel",
        **kwargs
    ):
        super().__init__(**kwargs)

        # Upper container: Stream A (Blue) and Stream B (Orange)
        self.axes_a = Axes(x_range=[0, 4, 1], y_range=[-1.5, 1.5, 1], x_length=3.2, y_length=1.4, axis_config={"color": "#334155", "stroke_width": 1.5}).move_to([-1.8, 2.2, 0])
        self.wave_a = self.axes_a.plot(lambda x: np.sin(2 * PI * x), color="#38BDF8", stroke_width=4.5)
        self.lbl_a = Text(signal_a_label, font=FONT_HELVETICA, font_size=12, color="#38BDF8", weight=BOLD).next_to(self.axes_a, UP, buff=0.15)

        self.axes_b = Axes(x_range=[0, 4, 1], y_range=[-1.5, 1.5, 1], x_length=3.2, y_length=1.4, axis_config={"color": "#334155", "stroke_width": 1.5}).move_to([1.8, 2.2, 0])
        self.wave_b = self.axes_b.plot(lambda x: np.cos(2 * PI * x), color="#F59E0B", stroke_width=4.5)
        self.lbl_b = Text(signal_b_label, font=FONT_HELVETICA, font_size=12, color="#F59E0B", weight=BOLD).next_to(self.axes_b, UP, buff=0.15)

        # Central Collision arrows
        self.arr_left = Arrow(start=[-0.6, 1.2, 0], end=[0, 0.4, 0], color="#38BDF8", buff=0.1, stroke_width=3)
        self.arr_right = Arrow(start=[0.6, 1.2, 0], end=[0, 0.4, 0], color="#F59E0B", buff=0.1, stroke_width=3)

        # Lower container: Chaotic Overlapping Superposition Wave
        self.axes_c = Axes(x_range=[0, 8, 1], y_range=[-2.5, 2.5, 1], x_length=6.4, y_length=2.2, axis_config={"color": "#475569", "stroke_width": 2.0}).move_to([0, -1.0, 0])
        self.wave_c = self.axes_c.plot(lambda x: np.sin(2 * PI * x * 0.7) + 0.8 * np.cos(2 * PI * x * 1.3), color="#EF4444", stroke_width=5.0)
        self.lbl_c = Text(result_label, font=FONT_HELVETICA, font_size=14, color="#EF4444", weight=HEAVY).next_to(self.axes_c, DOWN, buff=0.2)
        self.sub_c = Text(result_sub, font=FONT_HELVETICA, font_size=11, color="#94A3B8").next_to(self.lbl_c, DOWN, buff=0.08)

        self.add(self.axes_a, self.wave_a, self.lbl_a, self.axes_b, self.wave_b, self.lbl_b, self.arr_left, self.arr_right, self.axes_c, self.wave_c, self.lbl_c, self.sub_c)


class ScriptRadioTunerDial(VGroup):
    """
    Analog retro-futuristic radio dial with station frequencies and sweeping needle.
    """
    def __init__(
        self,
        station_a_label: str = "98.5 MHz\n[STATION A]",
        station_b_label: str = "104.2 MHz\n[STATION B]",
        tuner_status: str = "TUNER: BETWEEN STATIONS (STATIC)",
        scope_label: str = "MESSY OVERLAPPING SOUND WAVES",
        **kwargs
    ):
        super().__init__(**kwargs)

        # Outer chassis
        self.box = RoundedRectangle(corner_radius=0.2, width=6.6, height=3.6, color="#475569", fill_color="#1E293B", fill_opacity=0.85, stroke_width=3)
        self.box.move_to([0, 1.5, 0])

        # Frequency Ruler Line
        self.ruler = Line(start=[-2.8, 1.5, 0], end=[2.8, 1.5, 0], color="#64748B", stroke_width=2.5)

        # Station markers
        self.t1 = Line(start=[-1.8, 1.15, 0], end=[-1.8, 1.85, 0], color="#38BDF8", stroke_width=4.5)
        self.lbl1 = Text(station_a_label, font=FONT_HELVETICA, font_size=11, color="#38BDF8", weight=BOLD).next_to(self.t1, UP, buff=0.15)

        self.t2 = Line(start=[1.8, 1.15, 0], end=[1.8, 1.85, 0], color="#F59E0B", stroke_width=4.5)
        self.lbl2 = Text(station_b_label, font=FONT_HELVETICA, font_size=11, color="#F59E0B", weight=BOLD).next_to(self.t2, UP, buff=0.15)

        # Sharp Red Tuner Needle
        self.needle = Arrow(start=[0, 0.1, 0], end=[0, 2.9, 0], color="#EF4444", stroke_width=5.5, buff=0, max_tip_length_to_length_ratio=0.12)
        self.needle_pivot = Dot(point=[0, 0.1, 0], radius=0.14, color="#EF4444")
        self.tuner_status = Text(tuner_status, font=FONT_HELVETICA, font_size=13, color="#EF4444", weight=HEAVY).next_to(self.box, UP, buff=0.2)

        # Static Oscilloscope Wave underneath
        self.scope_box = RoundedRectangle(corner_radius=0.15, width=6.6, height=1.8, color="#334155", fill_color="#0F172A", fill_opacity=0.9).move_to([0, -1.5, 0])
        self.static_wave = VMobject(color="#F59E0B", stroke_width=4.0)
        pts = [
            np.array([-2.8, -1.5, 0]), np.array([-2.2, -1.0, 0]), np.array([-1.7, -1.9, 0]),
            np.array([-1.1, -1.1, 0]), np.array([-0.5, -1.9, 0]), np.array([0.0, -0.9, 0]),
            np.array([0.6, -1.9, 0]), np.array([1.2, -1.0, 0]), np.array([1.8, -1.8, 0]),
            np.array([2.3, -1.2, 0]), np.array([2.8, -1.5, 0])
        ]
        self.static_wave.set_points_smoothly(pts)
        self.scope_lbl = Text(scope_label, font=FONT_HELVETICA, font_size=12, color="#F8FAFC", weight=BOLD).next_to(self.scope_box, DOWN, buff=0.15)

        self.add(self.box, self.ruler, self.t1, self.lbl1, self.t2, self.lbl2, self.needle, self.needle_pivot, self.tuner_status, self.scope_box, self.static_wave, self.scope_lbl)


class ScriptSubspacePacking(VGroup):
    """
    Coordinate plane showing almost-orthogonal vectors packed into a single subspace.
    """
    def __init__(
        self,
        title: str = "SUPERPOSITION: PACKING MULTIPLE IDEAS",
        sub: str = "Almost-orthogonal directions allow N > D concepts in D dimensions",
        vec1_label: str = "Concept v₁\n[Thought A]",
        vec2_label: str = "Concept v₂\n[Thought B]",
        angle_label: str = "θ ≈ 90° (Orthogonal)",
        badge_title: str = "IT IS A FEATURE, NOT A BUG",
        badge_sub: str = "The model re-uses latent space to compress memory exponentially.",
        **kwargs
    ):
        super().__init__(**kwargs)

        self.title = Text(title, font=FONT_HELVETICA, font_size=13, color="#34D399", weight=HEAVY).move_to([0, 3.2, 0])
        self.sub = Text(sub, font=FONT_HELVETICA, font_size=11, color="#94A3B8").next_to(self.title, DOWN, buff=0.1)

        # Coordinate Axes
        self.axes = Axes(
            x_range=[-3, 3, 1], y_range=[-1, 3, 1],
            x_length=6.0, y_length=3.5,
            axis_config={"color": "#475569", "stroke_width": 2.5}
        ).move_to([0, 0.8, 0])

        origin = self.axes.c2p(0, 0)

        # Concept Vector 1 (Blue)
        p1 = self.axes.c2p(2.2, 1.8)
        self.vec1 = Arrow(origin, p1, color="#38BDF8", buff=0, stroke_width=6.0, max_tip_length_to_length_ratio=0.14)
        self.lbl1 = Text(vec1_label, font=FONT_HELVETICA, font_size=12, color="#38BDF8", weight=BOLD).next_to(p1, UR, buff=0.1)

        # Concept Vector 2 (Green)
        p2 = self.axes.c2p(-1.8, 2.2)
        self.vec2 = Arrow(origin, p2, color="#34D399", buff=0, stroke_width=6.0, max_tip_length_to_length_ratio=0.14)
        self.lbl2 = Text(vec2_label, font=FONT_HELVETICA, font_size=12, color="#34D399", weight=BOLD).next_to(p2, UL, buff=0.1)

        # Almost Orthogonal Angle Arc
        self.angle_arc = Arc(radius=0.9, start_angle=self.vec1.get_angle(), angle=self.vec2.get_angle() - self.vec1.get_angle(), arc_center=origin, color="#F59E0B", stroke_width=3.0)
        self.angle_lbl = Text(angle_label, font=FONT_HELVETICA, font_size=11, color="#F59E0B", weight=BOLD).next_to(self.angle_arc, UP, buff=0.12)

        # Bottom Capacity Badge
        self.badge_box = RoundedRectangle(corner_radius=0.15, width=6.2, height=1.4, color="#34D399", fill_color="#1E293B", fill_opacity=0.9, stroke_width=2.5).move_to([0, -1.8, 0])
        self.badge_txt = Text(badge_title, font=FONT_HELVETICA, font_size=14, color="#34D399", weight=HEAVY).move_to([0, -1.55, 0])
        self.badge_sub = Text(badge_sub, font=FONT_HELVETICA, font_size=11, color="#F8FAFC").move_to([0, -2.0, 0])

        self.add(self.title, self.sub, self.axes, self.vec1, self.lbl1, self.vec2, self.lbl2, self.angle_arc, self.angle_lbl, self.badge_box, self.badge_txt, self.badge_sub)


class ScriptPrismDisentangler(VGroup):
    """
    Laser prism taking chaotic mixed beams and peeling them into two clean parallel streams.
    """
    def __init__(
        self,
        title: str = "PEELING LAYERS APART (DISENTANGLEMENT)",
        sub: str = "Gentle model tuning turns noise into two distinct thought streams",
        in_label: str = "TANGLED\nSUPERPOSITION",
        prism_label: str = "LINEAR\nDECODER",
        out1_label: str = "CLEAN THOUGHT 1 (SIGNAL A)",
        out2_label: str = "CLEAN THOUGHT 2 (SIGNAL B)",
        **kwargs
    ):
        super().__init__(**kwargs)

        # Incoming Tangled Beam
        self.in_beam = Line(start=[-3.2, 0.4, 0], end=[-0.7, 0.4, 0], color="#EF4444", stroke_width=7.0)
        self.in_label = Text(in_label, font=FONT_HELVETICA, font_size=11, color="#EF4444", weight=BOLD).next_to(self.in_beam, UP, buff=0.15)

        # Optical Prism
        self.prism = Polygon(
            [-0.7, -1.2, 0], [0.7, -1.2, 0], [0.0, 1.6, 0],
            color="#38BDF8", stroke_width=4.0, fill_color="#1E293B", fill_opacity=0.85
        )
        self.prism_label = Text(prism_label, font=FONT_HELVETICA, font_size=11, color="#38BDF8", weight=HEAVY).move_to([0, 0.0, 0])

        # Peeling Apart Outgoing Beams
        self.out_beam1 = Line(start=[0.5, 0.6, 0], end=[3.2, 1.8, 0], color="#38BDF8", stroke_width=6.0)
        self.out_lbl1 = Text(out1_label, font=FONT_HELVETICA, font_size=12, color="#38BDF8", weight=BOLD).next_to(self.out_beam1.get_end(), RIGHT, buff=0.15)

        self.out_beam2 = Line(start=[0.5, 0.2, 0], end=[3.2, -1.0, 0], color="#34D399", stroke_width=6.0)
        self.out_lbl2 = Text(out2_label, font=FONT_HELVETICA, font_size=12, color="#34D399", weight=BOLD).next_to(self.out_beam2.get_end(), RIGHT, buff=0.15)

        self.title_badge = Text(title, font=FONT_HELVETICA, font_size=13, color="#34D399", weight=HEAVY).move_to([0, 2.7, 0])
        self.sub_badge = Text(sub, font=FONT_HELVETICA, font_size=11, color="#94A3B8").next_to(self.title_badge, DOWN, buff=0.1)

        self.add(self.in_beam, self.in_label, self.prism, self.prism_label, self.out_beam1, self.out_lbl1, self.out_beam2, self.out_lbl2, self.title_badge, self.sub_badge)


class ScriptBranchingOutputs(VGroup):
    """
    1 Forward pass branching into two crystal-clear answers.
    """
    def __init__(
        self,
        in_label: str = "DUAL PROMPT CONTEXT",
        core_title: str = "1 FORWARD PASS",
        core_sub: str = "Shared Latent Linear Map",
        card1_title: str = "ANSWER 1",
        card1_body: str = "Reasoning Flow\nAccuracy: 99.4%",
        card2_title: str = "ANSWER 2",
        card2_body: str = "Creative Synthesis\nAccuracy: 98.9%",
        **kwargs
    ):
        super().__init__(**kwargs)

        # Central Forward Pass Core
        self.core = RoundedRectangle(corner_radius=0.2, width=4.8, height=1.8, color="#A855F7", fill_color="#1E293B", fill_opacity=0.9, stroke_width=3.5).move_to([0, 1.0, 0])
        self.core_title = Text(core_title, font=FONT_HELVETICA, font_size=16, color="#A855F7", weight=HEAVY).move_to([0, 1.25, 0])
        self.core_sub = Text(core_sub, font=FONT_HELVETICA, font_size=11, color="#E2E8F0").move_to([0, 0.85, 0])

        # Dual Input Arrow
        self.in_arrow = Arrow(start=[0, 3.2, 0], end=[0, 2.0, 0], color="#38BDF8", stroke_width=5.0)
        self.in_lbl = Text(in_label, font=FONT_HELVETICA, font_size=12, color="#38BDF8", weight=BOLD).next_to(self.in_arrow, UP, buff=0.1)

        # Output Arrow 1 (Left: Thought 1)
        self.out_arr1 = Arrow(start=[-1.2, 0.05, 0], end=[-2.0, -1.2, 0], color="#38BDF8", stroke_width=5.0)
        self.card1 = RoundedRectangle(corner_radius=0.15, width=2.8, height=1.6, color="#38BDF8", fill_color="#0F172A", fill_opacity=0.95, stroke_width=2.5).move_to([-2.0, -2.2, 0])
        self.c1_title = Text(card1_title, font=FONT_HELVETICA, font_size=13, color="#38BDF8", weight=BOLD).move_to([-2.0, -1.8, 0])
        self.c1_body = Text(card1_body, font=FONT_HELVETICA, font_size=10, color="#F8FAFC").move_to([-2.0, -2.3, 0])

        # Output Arrow 2 (Right: Thought 2)
        self.out_arr2 = Arrow(start=[1.2, 0.05, 0], end=[2.0, -1.2, 0], color="#34D399", stroke_width=5.0)
        self.card2 = RoundedRectangle(corner_radius=0.15, width=2.8, height=1.6, color="#34D399", fill_color="#0F172A", fill_opacity=0.95, stroke_width=2.5).move_to([2.0, -2.2, 0])
        self.c2_title = Text(card2_title, font=FONT_HELVETICA, font_size=13, color="#34D399", weight=BOLD).move_to([2.0, -1.8, 0])
        self.c2_body = Text(card2_body, font=FONT_HELVETICA, font_size=10, color="#F8FAFC").move_to([2.0, -2.3, 0])

        self.add(self.core, self.core_title, self.core_sub, self.in_arrow, self.in_lbl, self.out_arr1, self.card1, self.c1_title, self.c1_body, self.out_arr2, self.card2, self.c2_title, self.c2_body)


class ScriptTreeSearchPruning(VGroup):
    """
    Reasoning / MCTS search tree showing exploration of candidate reasoning branches
    with optimal path highlighted (green check) and invalid paths pruned (red cross).
    """
    def __init__(
        self,
        title: str = "REASONING SEARCH & BRANCH PRUNING",
        sub: str = "Exploring parallel thoughts and pruning invalid logic paths",
        root_label: str = "ROOT QUERY / PROBLEM",
        optimal_label: str = "OPTIMAL CHAIN",
        optimal_sub: str = "Verified logic path\nConfidence: 98.4%",
        pruned_label: str = "PRUNED DEAD END",
        pruned_sub: str = "Hallucination detected\nBranch terminated",
        badge_title: str = "SEARCH GUIDANCE HEURISTIC",
        badge_sub: str = "Focuses 90% compute on promising reasoning paths",
        **kwargs
    ):
        super().__init__(**kwargs)

        self.title = Text(title, font=FONT_HELVETICA, font_size=14, color="#38BDF8", weight=BOLD).move_to([0, 3.4, 0])
        self.sub = Text(sub, font=FONT_HELVETICA, font_size=11, color="#94A3B8").next_to(self.title, DOWN, buff=0.1)

        # Root Node
        self.root = RoundedRectangle(corner_radius=0.12, width=3.6, height=0.9, color="#A855F7", fill_color="#1E293B", fill_opacity=0.9, stroke_width=2.5).move_to([0, 1.8, 0])
        self.root_txt = Text(root_label, font=FONT_HELVETICA, font_size=12, color="#A855F7", weight=BOLD).move_to(self.root.get_center())

        # Branch 1 (Optimal - Left)
        self.arr1 = Arrow(start=[-0.5, 1.35, 0], end=[-1.8, 0.45, 0], color="#34D399", stroke_width=4.0)
        self.c1 = RoundedRectangle(corner_radius=0.12, width=3.2, height=1.3, color="#34D399", fill_color="#0F172A", fill_opacity=0.95, stroke_width=2.5).move_to([-1.8, -0.4, 0])
        self.c1_t = Text(optimal_label, font=FONT_HELVETICA, font_size=12, color="#34D399", weight=BOLD).move_to([-1.8, -0.15, 0])
        self.c1_s = Text(optimal_sub, font=FONT_HELVETICA, font_size=10, color="#F8FAFC").move_to([-1.8, -0.55, 0])

        # Branch 2 (Pruned - Right)
        self.arr2 = Arrow(start=[0.5, 1.35, 0], end=[1.8, 0.45, 0], color="#EF4444", stroke_width=4.0)
        self.c2 = RoundedRectangle(corner_radius=0.12, width=3.2, height=1.3, color="#EF4444", fill_color="#0F172A", fill_opacity=0.95, stroke_width=2.5).move_to([1.8, -0.4, 0])
        self.c2_t = Text(pruned_label, font=FONT_HELVETICA, font_size=12, color="#EF4444", weight=BOLD).move_to([1.8, -0.15, 0])
        self.c2_s = Text(pruned_sub, font=FONT_HELVETICA, font_size=10, color="#94A3B8").move_to([1.8, -0.55, 0])

        # Bottom Summary Badge
        self.badge = RoundedRectangle(corner_radius=0.15, width=6.2, height=1.3, color="#34D399", fill_color="#1E293B", fill_opacity=0.9, stroke_width=2.5).move_to([0, -2.0, 0])
        self.b_txt = Text(badge_title, font=FONT_HELVETICA, font_size=13, color="#34D399", weight=HEAVY).move_to([0, -1.8, 0])
        self.b_sub = Text(badge_sub, font=FONT_HELVETICA, font_size=11, color="#F8FAFC").move_to([0, -2.2, 0])

        self.add(self.title, self.sub, self.root, self.root_txt, self.arr1, self.c1, self.c1_t, self.c1_s, self.arr2, self.c2, self.c2_t, self.c2_s, self.badge, self.b_txt, self.b_sub)


class ScriptDiffusionDenoising(VGroup):
    """
    Diffusion / Flow Matching generative sequence showing noisy lattice
    transforming into structured latent representations and sharp output.
    """
    def __init__(
        self,
        title: str = "DIFFUSION DENOISING TRAJECTORY",
        sub: str = "Iterative reverse trajectory peels noise into clear signals",
        step1_label: str = "STEP 1: NOISE",
        step2_label: str = "STEP 2: LATENTS",
        step3_label: str = "STEP 3: OUTPUT",
        badge_title: str = "FLOW MATCHING VELOCITY FIELD",
        badge_sub: str = "Deterministic straight paths achieve 10x faster inference",
        **kwargs
    ):
        super().__init__(**kwargs)

        self.title = Text(title, font=FONT_HELVETICA, font_size=14, color="#38BDF8", weight=BOLD).move_to([0, 3.4, 0])
        self.sub = Text(sub, font=FONT_HELVETICA, font_size=11, color="#94A3B8").next_to(self.title, DOWN, buff=0.1)

        # Stage 1: Noise
        self.b1 = RoundedRectangle(corner_radius=0.12, width=1.9, height=2.4, color="#EF4444", fill_color="#1E293B", fill_opacity=0.9).move_to([-2.3, 1.0, 0])
        self.t1 = Text(step1_label, font=FONT_HELVETICA, font_size=10, color="#EF4444", weight=BOLD).next_to(self.b1, UP, buff=0.1)
        self.dots1 = VGroup()
        np.random.seed(42)
        for _ in range(35):
            rx = np.random.uniform(-0.7, 0.7)
            ry = np.random.uniform(-0.9, 0.9)
            self.dots1.add(Dot(point=[-2.3 + rx, 1.0 + ry, 0], radius=0.03, color="#EF4444", fill_opacity=0.8))

        # Arrow 1
        self.arr1 = Arrow(start=[-1.2, 1.0, 0], end=[-0.8, 1.0, 0], color="#F59E0B", stroke_width=3.5)

        # Stage 2: Latent Structure
        self.b2 = RoundedRectangle(corner_radius=0.12, width=1.9, height=2.4, color="#F59E0B", fill_color="#1E293B", fill_opacity=0.9).move_to([0.0, 1.0, 0])
        self.t2 = Text(step2_label, font=FONT_HELVETICA, font_size=10, color="#F59E0B", weight=BOLD).next_to(self.b2, UP, buff=0.1)
        self.shape2 = VGroup(
            Circle(radius=0.4, color="#F59E0B", stroke_width=3).move_to([0, 1.3, 0]),
            Line(start=[-0.5, 0.5, 0], end=[0.5, 0.5, 0], color="#F59E0B", stroke_width=3)
        )

        # Arrow 2
        self.arr2 = Arrow(start=[1.1, 1.0, 0], end=[1.5, 1.0, 0], color="#34D399", stroke_width=3.5)

        # Stage 3: Clean Output
        self.b3 = RoundedRectangle(corner_radius=0.12, width=1.9, height=2.4, color="#34D399", fill_color="#1E293B", fill_opacity=0.9).move_to([2.3, 1.0, 0])
        self.t3 = Text(step3_label, font=FONT_HELVETICA, font_size=10, color="#34D399", weight=BOLD).next_to(self.b3, UP, buff=0.1)
        self.shape3 = VGroup(
            Star(color="#34D399", fill_color="#34D399", fill_opacity=0.7).scale(0.5).move_to([2.3, 1.0, 0])
        )

        # Bottom Summary Badge
        self.badge = RoundedRectangle(corner_radius=0.15, width=6.2, height=1.3, color="#34D399", fill_color="#1E293B", fill_opacity=0.9, stroke_width=2.5).move_to([0, -1.8, 0])
        self.b_txt = Text(badge_title, font=FONT_HELVETICA, font_size=13, color="#34D399", weight=HEAVY).move_to([0, -1.6, 0])
        self.b_sub = Text(badge_sub, font=FONT_HELVETICA, font_size=11, color="#F8FAFC").move_to([0, -2.0, 0])

        self.add(self.title, self.sub, self.b1, self.t1, self.dots1, self.arr1, self.b2, self.t2, self.shape2, self.arr2, self.b3, self.t3, self.shape3, self.badge, self.b_txt, self.b_sub)


class ScriptAttentionRouting(VGroup):
    """
    Attention mechanism / MoE router showing input tokens routing to key heads.
    """
    def __init__(
        self,
        title: str = "MULTI-HEAD ATTENTION ROUTING",
        sub: str = "Dynamic routing aligns queries with key memory slots",
        token_labels: Optional[List[str]] = None,
        head_labels: Optional[List[str]] = None,
        badge_title: str = "SPARSE EXPERT ACTIVATION",
        badge_sub: str = "Only 2 of 16 heads fire per token, slashing compute by 85%",
        **kwargs
    ):
        super().__init__(**kwargs)

        self.title = Text(title, font=FONT_HELVETICA, font_size=14, color="#38BDF8", weight=BOLD).move_to([0, 3.4, 0])
        self.sub = Text(sub, font=FONT_HELVETICA, font_size=11, color="#94A3B8").next_to(self.title, DOWN, buff=0.1)

        # Upper Attention Heads / Experts
        heads = head_labels or ["HEAD 1 (SYNTAX)", "HEAD 2 (LOGIC)", "HEAD 3 (SEMANTICS)"]
        self.head_boxes = VGroup()
        x_positions = [-2.2, 0.0, 2.2]
        colors = ["#38BDF8", "#34D399", "#F59E0B"]

        for i, h_text in enumerate(heads[:3]):
            h_box = RoundedRectangle(corner_radius=0.1, width=2.1, height=1.1, color=colors[i], fill_color="#1E293B", fill_opacity=0.9).move_to([x_positions[i], 1.8, 0])
            h_lbl = Text(h_text, font=FONT_HELVETICA, font_size=9, color=colors[i], weight=BOLD).move_to(h_box.get_center())
            self.head_boxes.add(VGroup(h_box, h_lbl))

        # Lower Token Pills
        tokens = token_labels or ["Token: 'Thinking'", "Token: 'In'", "Token: 'Superposition'"]
        self.token_pills = VGroup()
        for i, t_text in enumerate(tokens[:3]):
            t_box = RoundedRectangle(corner_radius=0.1, width=2.1, height=0.7, color="#64748B", fill_color="#0F172A", fill_opacity=0.9).move_to([x_positions[i], -0.2, 0])
            t_lbl = Text(t_text, font=FONT_HELVETICA, font_size=9, color="#E2E8F0").move_to(t_box.get_center())
            self.token_pills.add(VGroup(t_box, t_lbl))

        # Connecting Laser Routing Beams
        self.lasers = VGroup(
            Line(start=[-2.2, 0.15, 0], end=[-2.2, 1.25, 0], color="#38BDF8", stroke_width=4.0),
            Line(start=[0.0, 0.15, 0], end=[0.0, 1.25, 0], color="#34D399", stroke_width=4.0),
            Line(start=[2.2, 0.15, 0], end=[0.0, 1.25, 0], color="#F59E0B", stroke_width=3.0, stroke_opacity=0.6)
        )

        # Bottom Summary Badge
        self.badge = RoundedRectangle(corner_radius=0.15, width=6.2, height=1.3, color="#34D399", fill_color="#1E293B", fill_opacity=0.9, stroke_width=2.5).move_to([0, -1.8, 0])
        self.b_txt = Text(badge_title, font=FONT_HELVETICA, font_size=13, color="#34D399", weight=HEAVY).move_to([0, -1.6, 0])
        self.b_sub = Text(badge_sub, font=FONT_HELVETICA, font_size=11, color="#F8FAFC").move_to([0, -2.0, 0])

        self.add(self.title, self.sub, self.head_boxes, self.token_pills, self.lasers, self.badge, self.b_txt, self.b_sub)


class ScriptMemoryKVBuffer(VGroup):
    """
    KV-Cache / Context window buffer showing memory blocks and compression ratio.
    """
    def __init__(
        self,
        title: str = "KV-CACHE CONTEXT COMPRESSION",
        sub: str = "Streaming long horizons without quadratic memory explosion",
        in_stream_label: str = "INCOMING CONTEXT STREAM",
        cache_status_label: str = "ACTIVE KV CACHE BUFFER",
        gain_badge_title: str = "75% MEMORY REDUCTION",
        gain_badge_sub: str = "Constant inference latency sustained across 128k context",
        **kwargs
    ):
        super().__init__(**kwargs)

        self.title = Text(title, font=FONT_HELVETICA, font_size=14, color="#38BDF8", weight=BOLD).move_to([0, 3.4, 0])
        self.sub = Text(sub, font=FONT_HELVETICA, font_size=11, color="#94A3B8").next_to(self.title, DOWN, buff=0.1)

        # Stream arrow
        self.in_arrow = Arrow(start=[-3.2, 1.2, 0], end=[-1.5, 1.2, 0], color="#38BDF8", stroke_width=4.5)
        self.in_lbl = Text(in_stream_label, font=FONT_HELVETICA, font_size=11, color="#38BDF8", weight=BOLD).next_to(self.in_arrow, UP, buff=0.1)

        # Cache Buffer Grid
        self.cache_box = RoundedRectangle(corner_radius=0.15, width=4.5, height=2.4, color="#475569", fill_color="#1E293B", fill_opacity=0.85).move_to([1.0, 1.2, 0])
        self.cache_title = Text(cache_status_label, font=FONT_HELVETICA, font_size=11, color="#E2E8F0", weight=BOLD).next_to(self.cache_box, UP, buff=0.1)

        self.slots = VGroup()
        for row in range(2):
            for col in range(4):
                slot_col = "#34D399" if (row == 0 and col < 3) else "#334155"
                slot = RoundedRectangle(corner_radius=0.08, width=0.85, height=0.85, color=slot_col, fill_color=slot_col, fill_opacity=0.4 if slot_col != "#334155" else 0.2)
                slot.move_to([self.cache_box.get_left()[0] + 0.6 + col * 1.05, self.cache_box.get_top()[1] - 0.65 - row * 1.1, 0])
                self.slots.add(slot)

        # Bottom Summary Badge
        self.badge = RoundedRectangle(corner_radius=0.15, width=6.2, height=1.3, color="#34D399", fill_color="#1E293B", fill_opacity=0.9, stroke_width=2.5).move_to([0, -1.8, 0])
        self.b_txt = Text(gain_badge_title, font=FONT_HELVETICA, font_size=13, color="#34D399", weight=HEAVY).move_to([0, -1.6, 0])
        self.b_sub = Text(gain_badge_sub, font=FONT_HELVETICA, font_size=11, color="#F8FAFC").move_to([0, -2.0, 0])

        self.add(self.title, self.sub, self.in_arrow, self.in_lbl, self.cache_box, self.cache_title, self.slots, self.badge, self.b_txt, self.b_sub)


class ScriptComparativeBenchmarkBars(VGroup):
    """
    High-end 3Blue1Brown comparative benchmark visualization.
    Replaces generic circular dials with clear, labeled horizontal metric bars.
    """
    def __init__(
        self,
        title: str = "EMPIRICAL BENCHMARK EVALUATION",
        sub: str = "Multi-step reasoning accuracy vs prior state-of-the-art baselines",
        contender_a_name: str = "NEW ARCHITECTURE (OURS)",
        contender_a_score: float = 0.94,
        contender_a_text: str = "94.0%",
        contender_b_name: str = "CONVENTIONAL BASELINE",
        contender_b_score: float = 0.52,
        contender_b_text: str = "52.0%",
        delta_badge_text: str = "⚡ +42.0% REASONING IMPROVEMENT",
        delta_badge_sub: str = "Zero performance degradation with 2.4x speedup",
        **kwargs
    ):
        super().__init__(**kwargs)

        self.title = Text(title, font=FONT_HELVETICA, font_size=15, color="#38BDF8", weight=MEDIUM).move_to([0, 3.4, 0])
        self.sub = Text(sub, font=FONT_HELVETICA, font_size=11, color="#94A3B8", weight=NORMAL).next_to(self.title, DOWN, buff=0.12)

        # Bar 1: Contender A (Red/Orange if baseline, Mint if ours)
        col_a = "#34D399" if "ours" in contender_a_name.lower() or contender_a_score > contender_b_score else "#94A3B8"
        self.lbl_a = Text(contender_a_name, font=FONT_HELVETICA, font_size=12, color=col_a, weight=MEDIUM).move_to([-3.0, 1.9, 0], aligned_edge=LEFT)
        self.bg_bar_a = RoundedRectangle(corner_radius=0.08, width=4.0, height=0.45, color="#334155", fill_color="#1E293B", fill_opacity=0.85).move_to([-0.9, 1.4, 0])
        w_a = max(0.4, 4.0 * min(1.0, contender_a_score))
        self.fill_bar_a = RoundedRectangle(corner_radius=0.08, width=w_a, height=0.45, color=col_a, fill_color=col_a, fill_opacity=0.85).move_to(self.bg_bar_a.get_left() + RIGHT * (w_a / 2))
        self.val_a = Text(contender_a_text, font=FONT_HELVETICA, font_size=11, color=col_a, weight=MEDIUM).next_to(self.bg_bar_a, RIGHT, buff=0.18)
        if self.val_a.width > 1.8:
            self.val_a.scale_to_fit_width(1.8)

        # Bar 2: Contender B (Mint if ours, Slate if baseline)
        col_b = "#34D399" if "ours" in contender_b_name.lower() or contender_b_score >= contender_a_score else "#94A3B8"
        self.lbl_b = Text(contender_b_name, font=FONT_HELVETICA, font_size=12, color=col_b, weight=MEDIUM).move_to([-3.0, 0.4, 0], aligned_edge=LEFT)
        self.bg_bar_b = RoundedRectangle(corner_radius=0.08, width=4.0, height=0.45, color="#334155", fill_color="#1E293B", fill_opacity=0.85).move_to([-0.9, -0.1, 0])
        w_b = max(0.4, 4.0 * min(1.0, contender_b_score))
        self.fill_bar_b = RoundedRectangle(corner_radius=0.08, width=w_b, height=0.45, color=col_b, fill_color=col_b, fill_opacity=0.9).move_to(self.bg_bar_b.get_left() + RIGHT * (w_b / 2))
        self.val_b = Text(contender_b_text, font=FONT_HELVETICA, font_size=11, color=col_b, weight=MEDIUM).next_to(self.bg_bar_b, RIGHT, buff=0.18)
        if self.val_b.width > 1.8:
            self.val_b.scale_to_fit_width(1.8)

        # Central Delta Badge
        self.badge = RoundedRectangle(corner_radius=0.15, width=6.2, height=1.3, color="#F59E0B", fill_color="#1E293B", fill_opacity=0.9, stroke_width=2.5).move_to([0, -1.8, 0])
        self.b_txt = Text(delta_badge_text, font=FONT_HELVETICA, font_size=13, color="#F59E0B", weight=NORMAL).move_to([0, -1.6, 0])
        self.b_sub = Text(delta_badge_sub, font=FONT_HELVETICA, font_size=10, color="#F8FAFC", weight=NORMAL).move_to([0, -2.0, 0])

        self.add(self.title, self.sub, self.lbl_a, self.bg_bar_a, self.fill_bar_a, self.val_a, self.lbl_b, self.bg_bar_b, self.fill_bar_b, self.val_b, self.badge, self.b_txt, self.b_sub)


class ScriptCustomFlow(VGroup):
    """
    Flexible 3-stage flow diagram (Input -> Engine Core -> Output/Resolution)
    parameterized for any custom concept or analogy.
    """
    def __init__(
        self,
        title: str = "ARCHITECTURAL PIPELINE",
        sub: str = "Step-by-step mechanism flow",
        step1_title: str = "INPUT STATE",
        step1_sub: str = "Raw context stream",
        step2_title: str = "TRANSFORMATION ENGINE",
        step2_sub: str = "Nonlinear latent routing",
        step3_title: str = "FINAL PREDICTION",
        step3_sub: str = "High-confidence target",
        **kwargs
    ):
        super().__init__(**kwargs)

        self.title = Text(title, font=FONT_HELVETICA, font_size=14, color="#38BDF8", weight=BOLD).move_to([0, 3.4, 0])
        self.sub = Text(sub, font=FONT_HELVETICA, font_size=11, color="#94A3B8").next_to(self.title, DOWN, buff=0.1)

        # Step 1: Input Box
        self.box1 = RoundedRectangle(corner_radius=0.12, width=4.6, height=1.1, color="#38BDF8", fill_color="#1E293B", fill_opacity=0.9).move_to([0, 1.8, 0])
        self.b1_t = Text(step1_title, font=FONT_HELVETICA, font_size=12, color="#38BDF8", weight=BOLD).move_to([0, 2.0, 0])
        self.b1_s = Text(step1_sub, font=FONT_HELVETICA, font_size=10, color="#E2E8F0").move_to([0, 1.6, 0])

        self.arr1 = Arrow(start=[0, 1.2, 0], end=[0, 0.6, 0], color="#F59E0B", stroke_width=4.0)

        # Step 2: Engine Core
        self.box2 = RoundedRectangle(corner_radius=0.15, width=5.2, height=1.3, color="#A855F7", fill_color="#1E293B", fill_opacity=0.95, stroke_width=3).move_to([0, -0.1, 0])
        self.b2_t = Text(step2_title, font=FONT_HELVETICA, font_size=13, color="#A855F7", weight=HEAVY).move_to([0, 0.15, 0])
        self.b2_s = Text(step2_sub, font=FONT_HELVETICA, font_size=10, color="#E2E8F0").move_to([0, -0.35, 0])

        self.arr2 = Arrow(start=[0, -0.8, 0], end=[0, -1.4, 0], color="#34D399", stroke_width=4.0)

        # Step 3: Final Output
        self.box3 = RoundedRectangle(corner_radius=0.12, width=4.6, height=1.1, color="#34D399", fill_color="#0F172A", fill_opacity=0.95).move_to([0, -2.0, 0])
        self.b3_t = Text(step3_title, font=FONT_HELVETICA, font_size=12, color="#34D399", weight=BOLD).move_to([0, -1.8, 0])
        self.b3_s = Text(step3_sub, font=FONT_HELVETICA, font_size=10, color="#F8FAFC").move_to([0, -2.2, 0])

        self.add(self.title, self.sub, self.box1, self.b1_t, self.b1_s, self.arr1, self.box2, self.b2_t, self.b2_s, self.arr2, self.box3, self.b3_t, self.b3_s)


class ScriptPaperFigure(VGroup):
    """
    Renders an authentic vector diagram extracted from the arXiv paper e-print.
    Uses the FULL 9:16 mobile canvas — no tiny caged box. The diagram dominates
    the screen for maximum readability and visual impact.
    """
    def __init__(
        self,
        svg_path: Optional[str] = None,
        title: str = "OFFICIAL PAPER ARCHITECTURE",
        sub: str = "Authentic vector specification from arXiv source",
        badge_text: str = "PRIMARY ARCHITECTURE",
        max_width: float = 7.4,
        max_height: float = 8.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.title = Text(title, font=FONT_HELVETICA, font_size=16, color="#38BDF8", weight=BOLD).move_to([0, 5.3, 0])
        if self.title.width > 7.2:
            self.title.scale_to_fit_width(7.2)
        self.sub = Text(sub, font=FONT_HELVETICA, font_size=11, color="#94A3B8", weight=NORMAL).next_to(self.title, DOWN, buff=0.15)
        if self.sub.width > 7.2:
            self.sub.scale_to_fit_width(7.2)

        # Vector diagram — fills the hero zone without enclosing frame
        self.fig_mobj = None
        if svg_path and os.path.exists(svg_path):
            try:
                m = SVGMobject(str(svg_path))
                # Clamp to safe bounds
                if m.width > max_width:
                    m.scale_to_fit_width(max_width)
                if m.height > max_height:
                    m.scale_to_fit_height(max_height)
                # Scale UP small diagrams so they're clearly visible
                if m.width < 5.0 and m.height < 4.0:
                    scale_up = min(max_width / max(m.width, 0.1), max_height / max(m.height, 0.1), 1.5)
                    m.scale(scale_up)
                m.move_to([0, 0.0, 0])
                self.fig_mobj = m
            except Exception as e:
                print(f"⚠️ Error loading paper figure SVG: {e}")

        if not self.fig_mobj:
            fallback_box = Rectangle(width=6.0, height=3.5, color="#38BDF8", stroke_width=2.0).move_to([0, 0.0, 0])
            lbl = Text(title, font=FONT_HELVETICA, font_size=14, color="#38BDF8", weight=BOLD).move_to(fallback_box)
            self.fig_mobj = VGroup(fallback_box, lbl)

        # Compatibility stubs — no frame or badge chrome wasting screen space
        self.frame = VGroup()
        self.badge = VGroup()

        self.add(self.title, self.sub, self.fig_mobj)


class ScriptDynamicBespokeSVG(VGroup):
    """
    Renders a bespoke, beat-specific vector diagram synthesized for the exact
    narrative script and physical analogy of a beat.
    Uses the FULL 9:16 mobile canvas — no tiny caged box. The diagram dominates
    the screen for maximum readability and visual impact.
    """
    def __init__(
        self,
        svg_path: Optional[str] = None,
        title: str = "BESPOKE CONCEPT DIAGRAM",
        sub: str = "Procedural vector visualization tailored to narrative beat",
        badge_text: str = "",
        accent_color: str = "#38BDF8",
        max_width: float = 7.4,
        max_height: float = 8.0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.accent_color = accent_color

        self.title = Text(title, font=FONT_HELVETICA, font_size=16, color=accent_color, weight=BOLD).move_to([0, 5.3, 0])
        if self.title.width > 7.2:
            self.title.scale_to_fit_width(7.2)
        self.sub = Text(sub, font=FONT_HELVETICA, font_size=11, color="#94A3B8", weight=NORMAL).next_to(self.title, DOWN, buff=0.15)
        if self.sub.width > 7.2:
            self.sub.scale_to_fit_width(7.2)

        # Vector diagram — fills the hero zone without enclosing frame
        self.fig_mobj = None
        if svg_path and os.path.exists(svg_path):
            try:
                m = SVGMobject(str(svg_path))
                # Clamp to safe bounds
                if m.width > max_width:
                    m.scale_to_fit_width(max_width)
                if m.height > max_height:
                    m.scale_to_fit_height(max_height)
                # Scale UP small diagrams so they're clearly visible
                if m.width < 5.0 and m.height < 4.0:
                    scale_up = min(max_width / max(m.width, 0.1), max_height / max(m.height, 0.1), 1.5)
                    m.scale(scale_up)
                m.move_to([0, 0.0, 0])
                self.fig_mobj = m
            except Exception as e:
                print(f"⚠️ Error loading bespoke SVG: {e}")

        if not self.fig_mobj:
            fallback_box = Rectangle(width=6.0, height=3.5, color=accent_color, stroke_width=2.0).move_to([0, 0.0, 0])
            lbl = Text(title, font=FONT_HELVETICA, font_size=14, color=accent_color, weight=BOLD).move_to(fallback_box)
            self.fig_mobj = VGroup(fallback_box, lbl)

        # Compatibility stubs — no frame or badge chrome wasting screen space
        self.frame = VGroup()
        self.badge = VGroup()

        self.add(self.title, self.sub, self.fig_mobj)


MOTIF_REGISTRY = {
    "wave_collision": ScriptWaveInterference,
    "radio_tuner": ScriptRadioTunerDial,
    "subspace_vectors": ScriptSubspacePacking,
    "prism_disentangler": ScriptPrismDisentangler,
    "branching_outputs": ScriptBranchingOutputs,
    "tree_search": ScriptTreeSearchPruning,
    "diffusion_denoise": ScriptDiffusionDenoising,
    "attention_routing": ScriptAttentionRouting,
    "memory_buffer": ScriptMemoryKVBuffer,
    "comparative_bars": ScriptComparativeBenchmarkBars,
    "custom_flow": ScriptCustomFlow,
    "paper_figure": ScriptPaperFigure,
    "bespoke_svg": ScriptDynamicBespokeSVG,
    "dynamic_svg": ScriptDynamicBespokeSVG
}


def create_script_motif(motif_type: str, params: Optional[Dict[str, Any]] = None) -> VGroup:
    """
    Factory function to instantiate any script motif with provided parameters.
    Seamlessly routes visual blueprint layouts to composable Manim primitives.
    """
    from manim_engine.primitives.visual_compositions import (
        BLUEPRINT_COMPOSITION_REGISTRY,
        create_blueprint_composition
    )

    clean_params = params or {}

    # 1. Composable Visual Blueprint Routing (Visual Engine 4.0)
    if motif_type == "visual_composition":
        layout = clean_params.get("layout", "pipeline_stages")
        return create_blueprint_composition(layout, clean_params)
    elif motif_type in BLUEPRINT_COMPOSITION_REGISTRY:
        return create_blueprint_composition(motif_type, clean_params)

    # 2. Legacy / Standard Motifs (Paper Figure, Comparative Bars, etc.)
    cls = MOTIF_REGISTRY.get(motif_type, ScriptCustomFlow)
    try:
        return cls(**clean_params)
    except Exception as e:
        print(f"⚠️ Error creating motif '{motif_type}': {e}. Falling back to composable pipeline.")
        try:
            return create_blueprint_composition("pipeline_stages", clean_params)
        except Exception:
            return ScriptCustomFlow()

