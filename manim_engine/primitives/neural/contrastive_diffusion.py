"""
Contrastive Hypersphere & Score-Based Diffusion Field Visual Primitives.
Visualizes InfoNCE alignment/uniformity and generative diffusion reverse SDEs.
"""

from manim import *
import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from pipeline.config import FONT_HELVETICA, COLOR_MINT, COLOR_DANGER


class ContrastiveHypersphere(VGroup):
    """
    Contrastive embedding unit sphere (S^1 / S^2) showing
    positive pair alignment springs and negative pair Coulomb repulsion forces.
    """
    def __init__(
        self,
        radius: float = 1.6,
        center: np.ndarray = np.array([0.0, 0.0, 0.0]),
        **kwargs
    ):
        super().__init__(**kwargs)
        self.center_pt = center

        # Unit Sphere Perimeter
        self.sphere = Circle(
            radius=radius,
            color="#475569",
            stroke_width=1.5
        ).move_to(center)

        # Anchor, Positive, and Negative Embeddings
        self.pt_anchor = Dot(self.sphere.point_at_angle(0.35 * np.pi), radius=0.11, color="#00F0FF")
        self.pt_pos = Dot(self.sphere.point_at_angle(0.42 * np.pi), radius=0.11, color=COLOR_MINT)
        self.pt_neg1 = Dot(self.sphere.point_at_angle(1.15 * np.pi), radius=0.11, color=COLOR_DANGER)
        self.pt_neg2 = Dot(self.sphere.point_at_angle(1.70 * np.pi), radius=0.11, color=COLOR_DANGER)

        # Spring between Anchor and Positive
        self.spring = Line(
            self.pt_anchor.get_center(),
            self.pt_pos.get_center(),
            stroke_width=3.2,
            color=COLOR_MINT
        )

        # Repulsion Arrows
        self.repulse1 = Arrow(
            start=self.pt_anchor.get_center(),
            end=self.pt_neg1.get_center(),
            buff=0.20,
            stroke_width=1.5,
            color=COLOR_DANGER
        )
        self.repulse2 = Arrow(
            start=self.pt_anchor.get_center(),
            end=self.pt_neg2.get_center(),
            buff=0.20,
            stroke_width=1.5,
            color=COLOR_DANGER
        )

        self.add(self.sphere, self.spring, self.repulse1, self.repulse2,
                 self.pt_anchor, self.pt_pos, self.pt_neg1, self.pt_neg2)


class ScoreBasedDiffusionField(VGroup):
    r"""
    Vector field visualizing learned score vectors \nabla_x \log p_t(x)
    driving noisy Gaussian particles toward data manifold modes.
    """
    def __init__(
        self,
        center: np.ndarray = np.array([0.0, 0.0, 0.0]),
        x_span: float = 5.2,
        y_span: float = 3.6,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Two data modes (targets)
        m1 = np.array([-1.4, -0.6, 0.0]) + center
        m2 = np.array([1.4, -0.6, 0.0]) + center

        def score_func(p):
            x, y, _ = p
            d1 = (x - m1[0])**2 + (y - m1[1])**2 + 0.15
            d2 = (x - m2[0])**2 + (y - m2[1])**2 + 0.15
            v = -(np.array([x, y]) - m1[:2]) / d1 - (np.array([x, y]) - m2[:2]) / d2
            mag = np.linalg.norm(v) + 1e-5
            return np.array([v[0] / mag * 0.30, v[1] / mag * 0.30, 0.0])

        self.field = ArrowVectorField(
            score_func,
            x_range=[-x_span / 2, x_span / 2, 0.7],
            y_range=[-y_span / 2, y_span / 2, 0.7],
            length_func=lambda x: 0.28,
            color="#38BDF8"
        ).move_to(center)

        self.mode1 = Dot(point=m1, radius=0.18, color=COLOR_MINT)
        self.mode2 = Dot(point=m2, radius=0.18, color=COLOR_MINT)

        self.add(self.field, self.mode1, self.mode2)
