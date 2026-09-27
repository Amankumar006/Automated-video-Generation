"""
Sparse Mixture-of-Experts (MoE) Lattice & Load-Balancing Manometers.
Visualizes router gating, top-k laser dispatch to expert pools,
and auxiliary load-balancing capacity buffers.
"""

from manim import *
import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from pipeline.config import FONT_HELVETICA, COLOR_MINT, COLOR_GOLD, COLOR_DANGER


class LoadBalancingManometer(VGroup):
    """
    Capacity buffer reservoir bar showing token queue allocation per expert.
    """
    def __init__(
        self,
        num_experts: int = 8,
        width: float = 6.4,
        height: float = 0.9,
        active_indices: list[int] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.num_experts = num_experts
        active_indices = active_indices or [2, 5]

        self.box = RoundedRectangle(
            width=width,
            height=height,
            corner_radius=0.10,
            stroke_color="#475569",
            stroke_width=1.2,
            fill_color="#0A0D14",
            fill_opacity=0.92
        )

        header = Text("EXPERT LOAD CAPACITY [AUX LOSS]", font=FONT_HELVETICA, font_size=9, color="#94A3B8")
        header.next_to(self.box.get_top(), DOWN, buff=0.10).align_to(self.box, LEFT).shift(RIGHT * 0.20)

        # Build reservoir bars
        bar_w = (width - 0.8) / num_experts
        self.bars = VGroup()

        for i in range(num_experts):
            is_active = i in active_indices
            h_val = 0.38 if is_active else 0.16 + np.random.uniform(0.02, 0.08)
            col = COLOR_MINT if is_active else "#64748B"

            bar = Rectangle(
                width=bar_w * 0.75,
                height=h_val,
                stroke_width=0,
                fill_color=col,
                fill_opacity=0.85
            ).move_to([
                self.box.get_left()[0] + 0.4 + (i + 0.5) * bar_w,
                self.box.get_bottom()[1] + 0.12 + h_val / 2,
                0
            ])
            self.bars.add(bar)

        # Capacity Limit Line
        limit_y = self.box.get_bottom()[1] + 0.48
        limit_line = DashedLine(
            start=[self.box.get_left()[0] + 0.2, limit_y, 0],
            end=[self.box.get_right()[0] - 0.2, limit_y, 0],
            color=COLOR_DANGER,
            stroke_width=1.2,
            dash_length=0.06
        )
        self.add(self.box, header, self.bars, limit_line)


class SparseMoELattice(VGroup):
    """
    Mixture-of-Experts (MoE) lattice with central router,
    expert constellation, and top-k laser dispatch.
    """
    def __init__(
        self,
        num_experts: int = 16,
        grid_cols: int = 4,
        router_pos: np.ndarray = np.array([0.0, 2.2, 0.0]),
        expert_center: np.ndarray = np.array([0.0, -0.4, 0.0]),
        **kwargs
    ):
        super().__init__(**kwargs)
        self.num_experts = num_experts
        self.grid_cols = grid_cols

        # 1. Router Core Node
        self.router_core = Dot(point=router_pos, radius=0.20, color="#00F0FF")
        self.router_aura = Circle(radius=0.34, color="#00F0FF", stroke_width=1.4, stroke_opacity=0.5).move_to(router_pos)
        self.router_lbl = Text("ROUTER GATE", font=FONT_HELVETICA, font_size=11, color="#00F0FF", weight=BOLD).next_to(self.router_aura, UP, buff=0.14)
        self.router_group = VGroup(self.router_core, self.router_aura, self.router_lbl)

        # 2. Shared Expert Node (Foundation)
        shared_pos = expert_center + DOWN * 2.2
        self.shared_core = Dot(point=shared_pos, radius=0.22, color=COLOR_GOLD)
        self.shared_lbl = Text("SHARED EXPERT", font=FONT_HELVETICA, font_size=11, color=COLOR_GOLD, weight=BOLD).next_to(self.shared_core, DOWN, buff=0.20)
        self.shared_group = VGroup(self.shared_core, self.shared_lbl)

        # 3. Expert Pool Constellation
        self.expert_nodes = []
        rows = int(np.ceil(num_experts / grid_cols))
        x_spacing = 1.45
        y_spacing = 0.85

        for i in range(num_experts):
            r = i // grid_cols
            c = i % grid_cols
            x = (c - (grid_cols - 1) / 2) * x_spacing + expert_center[0]
            y = ((rows - 1) / 2 - r) * y_spacing + expert_center[1]

            d = Dot(point=[x, y, 0], radius=0.15, color="#334155")
            lbl = Text(f"E{i+1}", font=FONT_HELVETICA, font_size=9, color="#64748B").next_to([x, y, 0], DOWN, buff=0.06)
            self.expert_nodes.append(VGroup(d, lbl))

        self.expert_group = VGroup(*self.expert_nodes)
        self.add(self.router_group, self.shared_group, self.expert_group)

    def dispatch_top_k(self, scene: Scene, top_indices: list[int] = None, duration: float = 1.2):
        """Fires neon laser beams from router into top-k selected experts."""
        top_indices = top_indices or [2, 9]
        lasers = VGroup()

        for idx in top_indices:
            target_pt = self.expert_nodes[idx][0].get_center()
            line = Line(
                self.router_core.get_center(),
                target_pt,
                stroke_width=3.2,
                color=COLOR_MINT
            )
            lasers.add(line)

        # Shared path
        shared_beam = Line(
            self.router_core.get_center(),
            self.shared_core.get_center(),
            stroke_width=2.5,
            color=COLOR_GOLD
        )

        scene.play(
            Create(lasers),
            Create(shared_beam),
            *[self.expert_nodes[idx][0].animate.set_color(COLOR_MINT).scale(1.3) for idx in top_indices],
            *[self.expert_nodes[idx][1].animate.set_color(COLOR_MINT) for idx in top_indices],
            *[self.expert_nodes[i].animate.set_opacity(0.2) for i in range(self.num_experts) if i not in top_indices],
            run_time=duration
        )
        scene.play(
            *[Flash(self.expert_nodes[idx][0].get_center(), color=COLOR_MINT, line_length=0.2) for idx in top_indices],
            run_time=0.5
        )
