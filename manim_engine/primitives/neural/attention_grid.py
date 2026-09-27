"""
Transformer Attention Heatmap Grid & Dynamic Routing Ribbons.
Visualizes multi-head attention affinity matrices, token routing arcs,
and Value payload transmission.
"""

from manim import *
import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from pipeline.config import FONT_HELVETICA, COLOR_MINT


class TransformerAttentionGrid(VGroup):
    """
    Parametric N x N attention matrix with token sequence labels,
    cell luminance proportional to attention weight, and cell highlight methods.
    """
    def __init__(
        self,
        tokens: list[str] = None,
        matrix_values: np.ndarray = None,
        grid_size: float = 3.6,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.tokens = tokens or ["The", "sparse", "latent", "space"]
        n = len(self.tokens)

        if matrix_values is None:
            # Default mock attention weights
            self.values = np.array([
                [0.70, 0.10, 0.12, 0.08],
                [0.05, 0.75, 0.12, 0.08],
                [0.04, 0.12, 0.72, 0.12],
                [0.08, 0.14, 0.66, 0.12]
            ])
        else:
            self.values = np.array(matrix_values)

        cell_dim = grid_size / n
        self.cells = []
        self.cell_group = VGroup()

        # Build grid cells with colormap interpolation
        for r in range(n):
            row_cells = []
            for c in range(n):
                val = float(self.values[r, c])
                col = interpolate_color(ManimColor("#111827"), ManimColor("#00F0FF"), val)

                sq = RoundedRectangle(
                    width=cell_dim * 0.95,
                    height=cell_dim * 0.95,
                    corner_radius=0.06,
                    color="#334155",
                    fill_color=col,
                    fill_opacity=0.88,
                    stroke_width=1.0
                ).move_to([
                    (c - n / 2 + 0.5) * cell_dim,
                    (n / 2 - r - 0.5) * cell_dim,
                    0
                ])

                num = Text(
                    f"{val:.2f}",
                    font=FONT_HELVETICA,
                    font_size=10,
                    color=WHITE if val > 0.35 else "#64748B"
                ).move_to(sq)

                cell_v = VGroup(sq, num)
                row_cells.append(cell_v)
                self.cell_group.add(cell_v)
            self.cells.append(row_cells)

        # Border
        self.border = RoundedRectangle(
            width=grid_size + 0.15,
            height=grid_size + 0.15,
            corner_radius=0.12,
            color="#475569",
            stroke_width=1.5
        ).move_to(self.cell_group.get_center())

        # Column & Row Token Headers
        self.col_headers = VGroup()
        self.row_headers = VGroup()

        for c, tok in enumerate(self.tokens):
            lbl = Text(tok, font=FONT_HELVETICA, font_size=11, color="#94A3B8")
            lbl.move_to([(c - n / 2 + 0.5) * cell_dim, grid_size / 2 + 0.35, 0])
            self.col_headers.add(lbl)

        for r, tok in enumerate(self.tokens):
            lbl = Text(tok, font=FONT_HELVETICA, font_size=11, color="#94A3B8")
            lbl.move_to([-grid_size / 2 - 0.45, (n / 2 - r - 0.5) * cell_dim, 0])
            self.row_headers.add(lbl)

        self.add(self.border, self.cell_group, self.col_headers, self.row_headers)

    def highlight_attention_cell(self, row: int, col: int, color: str = "#00F0FF") -> Animation:
        """Draws a glowing focus ring around a specific attention cell."""
        cell = self.cells[row][col]
        return Circumscribe(cell, color=color, stroke_width=2.5, time_width=0.6)


class RoutingRibbon(VGroup):
    """
    Curved Bézier ribbon connecting source Key/Value token to target Query token,
    with an animated Value energy packet.
    """
    def __init__(
        self,
        start_point: np.ndarray,
        end_point: np.ndarray,
        weight: float = 0.68,
        color: str = "#00F0FF",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.arc = CurvedArrow(
            start_point=start_point,
            end_point=end_point,
            angle=-np.pi / 2.2,
            color=color,
            stroke_width=max(2.0, weight * 6.5)
        )
        badge_box = RoundedRectangle(
            width=1.1, height=0.35, corner_radius=0.08,
            color=color, fill_color="#082F49", fill_opacity=0.92, stroke_width=1.0
        ).move_to(self.arc.point_from_proportion(0.5) + DOWN * 0.28)

        badge_txt = Text(f"α = {weight:.2f}", font=FONT_HELVETICA, font_size=10, color=WHITE).move_to(badge_box)
        self.badge = VGroup(badge_box, badge_txt)
        self.add(self.arc, self.badge)

    def animate_payload_transmission(self, scene: Scene, color: str = COLOR_MINT, duration: float = 1.0):
        """Animates a luminous Value token traveling along the routing arc."""
        packet = Dot(point=self.arc.get_start(), radius=0.12, color=color)
        scene.play(
            MoveAlongPath(packet, self.arc),
            run_time=duration,
            rate_func=smooth
        )
        scene.play(
            Flash(self.arc.get_end(), color=color, line_length=0.25, num_lines=8),
            FadeOut(packet),
            run_time=0.4
        )
