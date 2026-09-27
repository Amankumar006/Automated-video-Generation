"""
The Model Verse — Script-Driven Visual Motifs (Visual Engine 3.0)
High-end, bespoke 3Blue1Brown procedural animations for the most powerful physical analogies:
1. Dual Wave Collision & Interference (Superposition)
2. Retro-Futuristic Radio Tuner Dial (Static & Channel Blending)
3. Coordinate Subspace Packing (Orthogonal Feature Vectors)
4. Optical Prism Beam Disentangler (Peeling Layers Apart)
5. Branching Dual Forward Pass (Parallel Synthesis)
"""

from manim import *
import numpy as np
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import FONT_HELVETICA


class ScriptWaveInterference(VGroup):
    """
    Two distinct traveling sinusoidal waves colliding into an overlapping interference wave.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Upper container: Stream A (Blue) and Stream B (Orange)
        self.axes_a = Axes(x_range=[0, 4, 1], y_range=[-1.5, 1.5, 1], x_length=3.2, y_length=1.4, axis_config={"color": "#334155", "stroke_width": 1.5}).move_to([-1.8, 2.2, 0])
        self.wave_a = self.axes_a.plot(lambda x: np.sin(2 * PI * x), color="#38BDF8", stroke_width=4.5)
        self.lbl_a = Text("THOUGHT 1 (SIGNAL A)", font=FONT_HELVETICA, font_size=13, color="#38BDF8", weight=BOLD).next_to(self.axes_a, UP, buff=0.15)

        self.axes_b = Axes(x_range=[0, 4, 1], y_range=[-1.5, 1.5, 1], x_length=3.2, y_length=1.4, axis_config={"color": "#334155", "stroke_width": 1.5}).move_to([1.8, 2.2, 0])
        self.wave_b = self.axes_b.plot(lambda x: np.cos(2 * PI * x), color="#F59E0B", stroke_width=4.5)
        self.lbl_b = Text("THOUGHT 2 (SIGNAL B)", font=FONT_HELVETICA, font_size=13, color="#F59E0B", weight=BOLD).next_to(self.axes_b, UP, buff=0.15)

        # Central Collision arrows
        self.arr_left = Arrow(start=[-0.6, 1.2, 0], end=[0, 0.4, 0], color="#38BDF8", buff=0.1, stroke_width=3)
        self.arr_right = Arrow(start=[0.6, 1.2, 0], end=[0, 0.4, 0], color="#F59E0B", buff=0.1, stroke_width=3)

        # Lower container: Chaotic Overlapping Superposition Wave
        self.axes_c = Axes(x_range=[0, 8, 1], y_range=[-2.5, 2.5, 1], x_length=6.4, y_length=2.2, axis_config={"color": "#475569", "stroke_width": 2.0}).move_to([0, -1.0, 0])
        self.wave_c = self.axes_c.plot(lambda x: np.sin(2 * PI * x * 0.7) + 0.8 * np.cos(2 * PI * x * 1.3), color="#EF4444", stroke_width=5.0)
        self.lbl_c = Text("OVERLAPPING SUPERPOSITION (CHAOTIC BLEND)", font=FONT_HELVETICA, font_size=15, color="#EF4444", weight=HEAVY).next_to(self.axes_c, DOWN, buff=0.2)
        self.sub_c = Text("Two thoughts packed into one noisy channel", font=FONT_HELVETICA, font_size=12, color="#94A3B8").next_to(self.lbl_c, DOWN, buff=0.08)

        self.add(self.axes_a, self.wave_a, self.lbl_a, self.axes_b, self.wave_b, self.lbl_b, self.arr_left, self.arr_right, self.axes_c, self.wave_c, self.lbl_c, self.sub_c)


class ScriptRadioTunerDial(VGroup):
    """
    Analog retro-futuristic radio dial with station frequencies and sweeping needle.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Outer chassis
        self.box = RoundedRectangle(corner_radius=0.2, width=6.6, height=3.6, color="#475569", fill_color="#1E293B", fill_opacity=0.85, stroke_width=3)
        self.box.move_to([0, 1.5, 0])

        # Frequency Ruler Line
        self.ruler = Line(start=[-2.8, 1.5, 0], end=[2.8, 1.5, 0], color="#64748B", stroke_width=2.5)

        # Station markers
        self.t1 = Line(start=[-1.8, 1.15, 0], end=[-1.8, 1.85, 0], color="#38BDF8", stroke_width=4.5)
        self.lbl1 = Text("98.5 MHz\n[STATION A]", font=FONT_HELVETICA, font_size=12, color="#38BDF8", weight=BOLD).next_to(self.t1, UP, buff=0.15)

        self.t2 = Line(start=[1.8, 1.15, 0], end=[1.8, 1.85, 0], color="#F59E0B", stroke_width=4.5)
        self.lbl2 = Text("104.2 MHz\n[STATION B]", font=FONT_HELVETICA, font_size=12, color="#F59E0B", weight=BOLD).next_to(self.t2, UP, buff=0.15)

        # Sharp Red Tuner Needle
        self.needle = Arrow(start=[0, 0.1, 0], end=[0, 2.9, 0], color="#EF4444", stroke_width=5.5, buff=0, max_tip_length_to_length_ratio=0.12)
        self.needle_pivot = Dot(point=[0, 0.1, 0], radius=0.14, color="#EF4444")
        self.tuner_status = Text("TUNER: BETWEEN STATIONS (STATIC)", font=FONT_HELVETICA, font_size=14, color="#EF4444", weight=HEAVY).next_to(self.box, UP, buff=0.2)

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
        self.scope_lbl = Text("MESSY OVERLAPPING SOUND WAVES", font=FONT_HELVETICA, font_size=13, color="#F8FAFC", weight=BOLD).next_to(self.scope_box, DOWN, buff=0.15)

        self.add(self.box, self.ruler, self.t1, self.lbl1, self.t2, self.lbl2, self.needle, self.needle_pivot, self.tuner_status, self.scope_box, self.static_wave, self.scope_lbl)


class ScriptSubspacePacking(VGroup):
    """
    Coordinate plane showing almost-orthogonal vectors packed into a single subspace.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.title = Text("SUPERPOSITION: PACKING MULTIPLE IDEAS", font=FONT_HELVETICA, font_size=14, color="#34D399", weight=HEAVY).move_to([0, 3.2, 0])
        self.sub = Text("Almost-orthogonal directions allow N > D concepts in D dimensions", font=FONT_HELVETICA, font_size=11, color="#94A3B8").next_to(self.title, DOWN, buff=0.1)

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
        self.lbl1 = Text("Concept v₁\n[Thought A]", font=FONT_HELVETICA, font_size=13, color="#38BDF8", weight=BOLD).next_to(p1, UR, buff=0.1)

        # Concept Vector 2 (Green)
        p2 = self.axes.c2p(-1.8, 2.2)
        self.vec2 = Arrow(origin, p2, color="#34D399", buff=0, stroke_width=6.0, max_tip_length_to_length_ratio=0.14)
        self.lbl2 = Text("Concept v₂\n[Thought B]", font=FONT_HELVETICA, font_size=13, color="#34D399", weight=BOLD).next_to(p2, UL, buff=0.1)

        # Almost Orthogonal Angle Arc
        self.angle_arc = Arc(radius=0.9, start_angle=self.vec1.get_angle(), angle=self.vec2.get_angle() - self.vec1.get_angle(), arc_center=origin, color="#F59E0B", stroke_width=3.0)
        self.angle_lbl = Text("θ ≈ 90° (Orthogonal)", font=FONT_HELVETICA, font_size=12, color="#F59E0B", weight=BOLD).next_to(self.angle_arc, UP, buff=0.12)

        # Bottom Capacity Badge
        self.badge_box = RoundedRectangle(corner_radius=0.15, width=6.2, height=1.5, color="#34D399", fill_color="#1E293B", fill_opacity=0.9, stroke_width=2.5).move_to([0, -1.8, 0])
        self.badge_txt = Text("IT IS A FEATURE, NOT A BUG", font=FONT_HELVETICA, font_size=15, color="#34D399", weight=HEAVY).move_to([0, -1.55, 0])
        self.badge_sub = Text("The model re-uses latent space to compress memory exponentially.", font=FONT_HELVETICA, font_size=11, color="#F8FAFC").move_to([0, -2.0, 0])

        self.add(self.title, self.sub, self.axes, self.vec1, self.lbl1, self.vec2, self.lbl2, self.angle_arc, self.angle_lbl, self.badge_box, self.badge_txt, self.badge_sub)


class ScriptPrismDisentangler(VGroup):
    """
    Laser prism taking chaotic mixed beams and peeling them into two clean parallel streams.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Incoming Tangled Beam
        self.in_beam = Line(start=[-3.2, 0.4, 0], end=[-0.7, 0.4, 0], color="#EF4444", stroke_width=7.0)
        self.in_label = Text("TANGLED\nSUPERPOSITION", font=FONT_HELVETICA, font_size=12, color="#EF4444", weight=BOLD).next_to(self.in_beam, UP, buff=0.15)

        # Optical Prism
        self.prism = Polygon(
            [-0.7, -1.2, 0], [0.7, -1.2, 0], [0.0, 1.6, 0],
            color="#38BDF8", stroke_width=4.0, fill_color="#1E293B", fill_opacity=0.85
        )
        self.prism_label = Text("LINEAR\nDECODER", font=FONT_HELVETICA, font_size=12, color="#38BDF8", weight=HEAVY).move_to([0, 0.0, 0])

        # Peeling Apart Outgoing Beams
        self.out_beam1 = Line(start=[0.5, 0.6, 0], end=[3.2, 1.8, 0], color="#38BDF8", stroke_width=6.0)
        self.out_lbl1 = Text("CLEAN THOUGHT 1 (SIGNAL A)", font=FONT_HELVETICA, font_size=13, color="#38BDF8", weight=BOLD).next_to(self.out_beam1.get_end(), RIGHT, buff=0.15)

        self.out_beam2 = Line(start=[0.5, 0.2, 0], end=[3.2, -1.0, 0], color="#34D399", stroke_width=6.0)
        self.out_lbl2 = Text("CLEAN THOUGHT 2 (SIGNAL B)", font=FONT_HELVETICA, font_size=13, color="#34D399", weight=BOLD).next_to(self.out_beam2.get_end(), RIGHT, buff=0.15)

        self.title_badge = Text("PEELING LAYERS APART (DISENTANGLEMENT)", font=FONT_HELVETICA, font_size=14, color="#34D399", weight=HEAVY).move_to([0, 2.7, 0])
        self.sub_badge = Text("Gentle model tuning turns noise into two distinct thought streams", font=FONT_HELVETICA, font_size=11, color="#94A3B8").next_to(self.title_badge, DOWN, buff=0.1)

        self.add(self.in_beam, self.in_label, self.prism, self.prism_label, self.out_beam1, self.out_lbl1, self.out_beam2, self.out_lbl2, self.title_badge, self.sub_badge)


class ScriptBranchingOutputs(VGroup):
    """
    1 Forward pass branching into two crystal-clear answers.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Central Forward Pass Core
        self.core = RoundedRectangle(corner_radius=0.2, width=4.8, height=1.8, color="#A855F7", fill_color="#1E293B", fill_opacity=0.9, stroke_width=3.5).move_to([0, 1.0, 0])
        self.core_title = Text("1 FORWARD PASS", font=FONT_HELVETICA, font_size=18, color="#A855F7", weight=HEAVY).move_to([0, 1.25, 0])
        self.core_sub = Text("Shared Latent Linear Map", font=FONT_HELVETICA, font_size=12, color="#E2E8F0").move_to([0, 0.85, 0])

        # Dual Input Arrow
        self.in_arrow = Arrow(start=[0, 3.2, 0], end=[0, 2.0, 0], color="#38BDF8", stroke_width=5.0)
        self.in_lbl = Text("DUAL PROMPT CONTEXT", font=FONT_HELVETICA, font_size=13, color="#38BDF8", weight=BOLD).next_to(self.in_arrow, UP, buff=0.1)

        # Output Arrow 1 (Left: Thought 1)
        self.out_arr1 = Arrow(start=[-1.2, 0.05, 0], end=[-2.0, -1.2, 0], color="#38BDF8", stroke_width=5.0)
        self.card1 = RoundedRectangle(corner_radius=0.15, width=2.8, height=1.6, color="#38BDF8", fill_color="#0F172A", fill_opacity=0.95, stroke_width=2.5).move_to([-2.0, -2.2, 0])
        self.c1_title = Text("ANSWER 1", font=FONT_HELVETICA, font_size=14, color="#38BDF8", weight=BOLD).move_to([-2.0, -1.8, 0])
        self.c1_body = Text("Reasoning Flow\nAccuracy: 99.4%", font=FONT_HELVETICA, font_size=11, color="#F8FAFC").move_to([-2.0, -2.3, 0])

        # Output Arrow 2 (Right: Thought 2)
        self.out_arr2 = Arrow(start=[1.2, 0.05, 0], end=[2.0, -1.2, 0], color="#34D399", stroke_width=5.0)
        self.card2 = RoundedRectangle(corner_radius=0.15, width=2.8, height=1.6, color="#34D399", fill_color="#0F172A", fill_opacity=0.95, stroke_width=2.5).move_to([2.0, -2.2, 0])
        self.c2_title = Text("ANSWER 2", font=FONT_HELVETICA, font_size=14, color="#34D399", weight=BOLD).move_to([2.0, -1.8, 0])
        self.c2_body = Text("Creative Synthesis\nAccuracy: 98.9%", font=FONT_HELVETICA, font_size=11, color="#F8FAFC").move_to([2.0, -2.3, 0])

        self.add(self.core, self.core_title, self.core_sub, self.in_arrow, self.in_lbl, self.out_arr1, self.card1, self.c1_title, self.c1_body, self.out_arr2, self.card2, self.c2_title, self.c2_body)
