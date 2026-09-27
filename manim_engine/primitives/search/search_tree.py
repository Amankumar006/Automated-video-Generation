"""
Dynamic Search Tree & MCTS (Monte Carlo Tree Search) Visual Primitives.
Visualizes state-space branching, A* cost decomposition, MCTS 4-beat cycles,
and reward backpropagation shockwaves.
"""

from manim import *
import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from pipeline.config import FONT_HELVETICA, COLOR_MINT, COLOR_DANGER, COLOR_GOLD


class MCTSNodeGauge(VGroup):
    """
    Dual-Ring Node Gauge for Monte Carlo Tree Search:
    - Inner Core: Color gradient from Deep Red (loss, Q=0) to Emerald (win, Q=1).
    - Outer Ring: Radial progress arc indicating visit count N.
    """
    def __init__(
        self,
        node_id: str,
        n_visits: int = 12,
        q_value: float = 0.85,
        radius: float = 0.28,
        center: np.ndarray = ORIGIN,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.node_id = node_id
        self.n_visits = n_visits
        self.q_value = q_value
        self.gauge_radius = radius

        # Inner Core Value Color
        core_col = interpolate_color(ManimColor(COLOR_DANGER), ManimColor(COLOR_MINT), q_value)
        self.core = Circle(
            radius=radius,
            color=core_col,
            fill_color=core_col,
            fill_opacity=0.88,
            stroke_width=1.5
        ).move_to(center)

        # Outer Visit Arc
        sweep_angle = min(TAU, (n_visits / 20.0) * TAU)
        self.outer_arc = Arc(
            radius=radius * 1.25,
            start_angle=PI / 2,
            angle=-sweep_angle,
            color=COLOR_GOLD,
            stroke_width=2.5
        ).move_to(center)

        # Label
        self.label = Text(
            f"{q_value:.2f}",
            font=FONT_HELVETICA,
            font_size=9,
            color=WHITE,
            weight=BOLD
        ).move_to(center)

        self.add(self.core, self.outer_arc, self.label)


class DynamicSearchTree(VGroup):
    """
    Parametric search tree with frontier queues, cost vector decomposition,
    and MCTS rollout animations.
    """
    def __init__(
        self,
        tree_dict: dict = None,
        root_pos: np.ndarray = np.array([0.0, 3.2, 0.0]),
        h_spacing: float = 2.0,
        v_spacing: float = 1.2,
        **kwargs
    ):
        kwargs.pop("levels", None)
        kwargs.pop("branch_factor", None)
        kwargs.pop("root_label", None)
        super().__init__(**kwargs)
        self.nodes = {}
        self.edges = VGroup()
        self.node_group = VGroup()

        if tree_dict is None:
            # Default mock search tree
            tree_dict = {
                "id": "s0", "val": "Start", "q": 0.5, "n": 20,
                "children": [
                    {
                        "id": "s1_win", "val": "Action A", "q": 0.85, "n": 14,
                        "children": [
                            {"id": "s11", "val": "Sub A1", "q": 0.90, "n": 10},
                            {"id": "s12", "val": "Sub A2", "q": 0.40, "n": 4}
                        ]
                    },
                    {
                        "id": "s2_fail", "val": "Action B", "q": 0.20, "n": 6,
                        "children": [
                            {"id": "s21_coll", "val": "Collision", "q": 0.05, "n": 4}
                        ]
                    }
                ]
            }

        self._build_tree(tree_dict, root_pos, h_spacing, v_spacing)
        self.add(self.edges, self.node_group)

    def _build_tree(self, data: dict, curr_pos: np.ndarray, h_spacing: float, v_spacing: float):
        nid = data["id"]
        q = data.get("q", 0.5)
        n = data.get("n", 5)

        gauge = MCTSNodeGauge(node_id=nid, n_visits=n, q_value=q, center=curr_pos)
        self.nodes[nid] = gauge
        self.node_group.add(gauge)

        children = data.get("children", [])
        num_c = len(children)
        if num_c > 0:
            x_start = curr_pos[0] - (num_c - 1) * h_spacing / 2.0
            for idx, child in enumerate(children):
                c_pos = np.array([x_start + idx * h_spacing, curr_pos[1] - v_spacing, 0.0])
                edge = Line(
                    curr_pos + DOWN * 0.35,
                    c_pos + UP * 0.35,
                    stroke_color="#475569",
                    stroke_width=1.8
                )
                self.edges.add(edge)
                self._build_tree(child, c_pos, h_spacing * 0.65, v_spacing)

    def animate_mcts_cycle(
        self,
        scene: Scene,
        selected_path: list[str] = ("s0", "s1_win", "s11"),
        reward_color: str = COLOR_MINT,
        duration: float = 2.4
    ):
        """
        Executes the canonical 4-beat MCTS visual cycle:
        1. Selection: Golden halo cascades down the tree policy path.
        2. Simulation: Lightweight dashed ghost trace springs forward.
        3. Backpropagation: Energetic reward wave ascends back to root.
        """
        # 1. Selection Path Glow
        path_anims = []
        for nid in selected_path:
            if nid in self.nodes:
                node = self.nodes[nid]
                path_anims.append(node.outer_arc.animate.set_color("#00F0FF").set_stroke(width=3.5))

        scene.play(*path_anims, run_time=duration * 0.30)

        # 2. Simulation Ghost Path
        leaf_node = self.nodes[selected_path[-1]]
        leaf_pt = leaf_node.get_center()
        terminal_pt = leaf_pt + DOWN * 1.2 + RIGHT * 0.4

        ghost_path = DashedLine(
            leaf_pt + DOWN * 0.35,
            terminal_pt,
            color="#94A3B8",
            stroke_width=1.5,
            dash_length=0.08
        )
        sim_dot = Dot(terminal_pt, radius=0.10, color=reward_color)
        reward_badge = Text("+1 WIN", font=FONT_HELVETICA, font_size=10, color=reward_color, weight=BOLD).next_to(terminal_pt, RIGHT, buff=0.12)

        scene.play(
            Create(ghost_path),
            FadeIn(sim_dot),
            FadeIn(reward_badge),
            run_time=duration * 0.25
        )

        # 3. Backpropagation Reward Pulse Ascending
        pulse = Dot(point=terminal_pt, radius=0.16, color=reward_color)
        scene.play(
            FadeOut(sim_dot),
            FadeOut(ghost_path),
            FadeOut(reward_badge),
            pulse.animate.move_to(self.nodes[selected_path[0]].get_center()),
            run_time=duration * 0.30,
            rate_func=rush_into
        )

        # 4. Value Gauge Increment Flash
        scene.play(
            Flash(self.nodes[selected_path[0]].get_center(), color=reward_color, line_length=0.25),
            FadeOut(pulse),
            run_time=duration * 0.15
        )
