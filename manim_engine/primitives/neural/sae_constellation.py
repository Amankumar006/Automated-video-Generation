"""
Sparse Autoencoders (SAEs) & Superposition Visual Primitives.
Visualizes residual stream superposition, overcomplete dictionaries,
Top-K sparsity sieves, and monosemantic feature decomposition.
"""

from manim import *
import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from pipeline.config import FONT_HELVETICA, COLOR_MINT, COLOR_DANGER, COLOR_GOLD


from typing import Union, Optional, List


class FeatureProjectionChip(VGroup):
    """
    HUD chip displaying an isolated monosemantic feature direction,
    its semantic concept label, and quantitative activation intensity.
    """
    def __init__(
        self,
        feature_id: Union[int, str] = 0,
        label: str = "Feature",
        intensity: float = 1.0,
        color: str = COLOR_MINT,
        width: float = 3.0,
        height: float = 0.75,
        **kwargs
    ):
        scale_val = kwargs.pop("scale", None)
        super().__init__(**kwargs)
        if isinstance(feature_id, str) and (label == "Feature" or isinstance(label, (int, float))):
            # Signature was called as (label_str, intensity_float, color_str)
            if isinstance(label, (int, float)):
                intensity = float(label)
                if isinstance(intensity, str):
                    color = intensity
            display_label = feature_id
            tag_str = "MONOSEMANTIC FEATURE"
        else:
            display_label = label
            tag_str = f"FEATURE #{feature_id}"

        self.card = RoundedRectangle(
            width=width,
            height=height,
            corner_radius=0.10,
            stroke_color=color,
            stroke_width=1.5,
            fill_color="#0D1117",
            fill_opacity=0.92
        )
        tag = Text(
            tag_str,
            font=FONT_HELVETICA,
            font_size=10,
            color=color,
            weight=BOLD
        )
        lbl = Text(
            display_label[:24],
            font=FONT_HELVETICA,
            font_size=11,
            color=WHITE,
            weight=SEMIBOLD
        )
        val = Text(
            f"f = {intensity:.2f}",
            font="Courier",
            font_size=10,
            color="#A7F3D0" if color == COLOR_MINT else "#BAE6FD"
        )

        header = VGroup(tag, val).arrange(RIGHT, buff=0.4)
        body = VGroup(header, lbl).arrange(DOWN, buff=0.06).move_to(self.card)
        self.add(self.card, body)
        if scale_val is not None:
            self.scale(scale_val)


class SAEConstellation(VGroup):
    """
    Parametric Sparse Autoencoder dictionary constellation in R^2 projection space.
    Visualizes entangled residual vector x decomposing into sparse monosemantic rays.
    """
    def __init__(
        self,
        num_dictionary_features: int = 8,
        plane_size: float = 5.2,
        active_indices: list[int] = None,
        **kwargs
    ):
        scale_val = kwargs.pop("scale", None)
        super().__init__(**kwargs)
        self.num_features = num_dictionary_features
        self.active_indices = active_indices or [1, 4]

        # 1. Residual Stream Coordinate Plane
        self.plane = NumberPlane(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            x_length=plane_size,
            y_length=plane_size,
            background_line_style={"stroke_color": "#1E293B", "stroke_width": 1.0, "stroke_opacity": 0.5},
            axis_config={"color": "#475569", "stroke_width": 1.2}
        )

        # 2. Overcomplete Dictionary Directions
        self.dict_arrows = []
        self.dict_labels = []
        angles = np.linspace(0, 2 * np.pi, self.num_features, endpoint=False) + np.pi / 8
        self.angles = angles

        for i, theta in enumerate(angles):
            end_pt = self.plane.c2p(2.1 * np.cos(theta), 2.1 * np.sin(theta))
            arr = Arrow(
                start=self.plane.c2p(0, 0),
                end=end_pt,
                buff=0,
                color="#334155",
                stroke_width=2.0
            )
            lbl = Text(
                f"d_{i+1}",
                font=FONT_HELVETICA,
                font_size=10,
                color="#64748B"
            ).next_to(end_pt, end_pt - self.plane.c2p(0, 0), buff=0.08)

            self.dict_arrows.append(arr)
            self.dict_labels.append(lbl)

        self.arrow_group = VGroup(*self.dict_arrows)
        self.label_group = VGroup(*self.dict_labels)

        # 3. Entangled Activation Vector x
        c1, c2 = 1.5, 1.2
        idx1, idx2 = self.active_indices[0], self.active_indices[1]
        x_target = self.plane.c2p(
            c1 * np.cos(angles[idx1]) + c2 * np.cos(angles[idx2]),
            c1 * np.sin(angles[idx1]) + c2 * np.sin(angles[idx2])
        )
        self.entangled_vector = Arrow(
            start=self.plane.c2p(0, 0),
            end=x_target,
            buff=0,
            color=COLOR_GOLD,
            stroke_width=4.0
        )
        self.vector_label = Text(
            "Activation x",
            font=FONT_HELVETICA,
            font_size=12,
            color=COLOR_GOLD,
            weight=BOLD
        ).next_to(self.entangled_vector.get_end(), UR, buff=0.10)

        self.add(self.plane, self.arrow_group, self.label_group, self.entangled_vector, self.vector_label)

    def trigger_sparsity_sieve(self, scene: Scene, duration: float = 1.5):
        """
        Animates Top-K sparsity selection:
        Dormant basis vectors dim to dark slate, active directions illuminate in Mint and Cyan,
        and orthogonal projection dashed lines drop from x onto the active basis.
        """
        idx1, idx2 = self.active_indices[0], self.active_indices[1]
        c1, c2 = 1.5, 1.2
        pt1 = self.plane.c2p(c1 * np.cos(self.angles[idx1]), c1 * np.sin(self.angles[idx1]))
        pt2 = self.plane.c2p(c2 * np.cos(self.angles[idx2]), c2 * np.sin(self.angles[idx2]))
        x_target = self.entangled_vector.get_end()

        proj1 = DashedLine(x_target, pt1, color=COLOR_MINT, stroke_width=1.8, dash_length=0.08)
        proj2 = DashedLine(x_target, pt2, color="#00F0FF", stroke_width=1.8, dash_length=0.08)

        active_a1 = Arrow(self.plane.c2p(0, 0), pt1, buff=0, color=COLOR_MINT, stroke_width=3.8)
        active_a2 = Arrow(self.plane.c2p(0, 0), pt2, buff=0, color="#00F0FF", stroke_width=3.8)

        scene.play(
            Transform(self.dict_arrows[idx1], active_a1),
            Transform(self.dict_arrows[idx2], active_a2),
            self.dict_labels[idx1].animate.set_color(COLOR_MINT).scale(1.2),
            self.dict_labels[idx2].animate.set_color("#00F0FF").scale(1.2),
            *[self.dict_arrows[i].animate.set_color("#1E293B").set_opacity(0.25)
              for i in range(self.num_features) if i not in [idx1, idx2]],
            Create(proj1),
            Create(proj2),
            run_time=duration
        )
        scene.play(
            Flash(pt1, color=COLOR_MINT, num_lines=8, line_length=0.2),
            Flash(pt2, color="#00F0FF", num_lines=8, line_length=0.2),
            run_time=0.6
        )
