"""
Abstract Syntax Tree (AST) Visual Primitive for Code Generation & Agentic Synthesis.
Constructs parametric syntax trees with language-specific node morphologies
(Hexagons, Pills, Diamonds, Holes) and test execution traces.
"""

from manim import *
import numpy as np
from typing import Optional, Dict, Any


class ASTMorphTree(VGroup):
    """
    Parametric Abstract Syntax Tree with syntax-specific geometric nodes.
    Supports node-state highlighting, branch pruning, and execution waves.
    """
    def __init__(
        self,
        tree_dict: Optional[dict] = None,
        root_pos: np.ndarray = np.array([0.0, 3.8, 0.0]),
        h_spacing: float = 1.6,
        v_spacing: float = 1.0,
        **kwargs
    ):
        scale_val = kwargs.pop("scale", None)
        super().__init__(**kwargs)
        self.node_groups = {}
        self.edges = VGroup()
        self.nodes = VGroup()

        if tree_dict is None:
            tree_dict = {
                "id": "root", "type": "Function", "label": "plan_sketch()",
                "children": [
                    {"id": "n1", "type": "Condition", "label": "feasible(q)", "children": [
                        {"id": "n11", "type": "Action", "label": "Execute()"}
                    ]},
                    {"id": "n2", "type": "ControlFlow", "label": "Refine()", "children": [
                        {"id": "n21", "type": "SketchHole", "label": "?? C-Space"}
                    ]}
                ]
            }

        self._build_tree(tree_dict, root_pos, h_spacing, v_spacing)
        self.add(self.edges, self.nodes)
        if scale_val is not None:
            self.scale(scale_val)

    def _get_node_shape(self, node_type: str, label: str) -> VGroup:
        """Morphological shape selector based on syntax grammar."""
        if node_type == "ControlFlow":  # Hexagon
            shape = RegularPolygon(
                n=6, radius=0.40, color="#F59E0B", stroke_width=1.5,
                fill_color="#451A03", fill_opacity=0.88
            )
        elif node_type == "Function":   # Rounded Pill
            shape = RoundedRectangle(
                width=1.5, height=0.50, corner_radius=0.10,
                color="#38BDF8", stroke_width=1.5,
                fill_color="#082F49", fill_opacity=0.88
            )
        elif node_type == "Condition":  # Diamond
            shape = RegularPolygon(
                n=4, radius=0.38, color="#A855F7", stroke_width=1.5,
                fill_color="#3B0764", fill_opacity=0.88
            ).rotate(PI / 4)
        elif node_type == "Hole":       # Dashed Circle for Unfilled Spec
            shape = Circle(
                radius=0.35, color="#E2E8F0", stroke_width=1.8,
                fill_color="#0A0D14", fill_opacity=0.95
            )
        else:                           # Default Primitive Block
            shape = RoundedRectangle(
                width=1.3, height=0.45, corner_radius=0.08,
                color="#10B981", stroke_width=1.5,
                fill_color="#064E3B", fill_opacity=0.88
            )

        txt = Text(label, font=FONT_HELVETICA if "FONT_HELVETICA" in globals() else "Helvetica", font_size=11, color=WHITE, weight=BOLD).move_to(shape)
        max_w = shape.width * 0.85
        if txt.width > max_w:
            txt.scale_to_fit_width(max_w)
        return VGroup(shape, txt)

    def _build_tree(self, node_data: dict, curr_pos: np.ndarray, h_spacing: float, v_spacing: float):
        node_id = node_data["id"]
        node_type = node_data.get("type", "Block")
        label = node_data.get("label", node_id)

        node_mobj = self._get_node_shape(node_type, label).move_to(curr_pos)
        self.node_groups[node_id] = node_mobj
        self.nodes.add(node_mobj)

        children = node_data.get("children", [])
        num_children = len(children)
        if num_children > 0:
            total_span = (num_children - 1) * h_spacing
            start_x = curr_pos[0] - total_span / 2.0

            for idx, child in enumerate(children):
                child_x = start_x + idx * h_spacing
                child_y = curr_pos[1] - v_spacing
                child_pos = np.array([child_x, child_y, 0.0])

                edge = Line(
                    curr_pos + DOWN * 0.25, child_pos + UP * 0.22,
                    stroke_color="#475569", stroke_width=1.4
                )
                self.edges.add(edge)

                self._build_tree(child, child_pos, h_spacing * 0.65, v_spacing)

    def highlight_execution_path(self, path_node_ids: list[str], active_color: str = "#00F0FF"):
        """Returns animation wave highlighting active execution path through the AST."""
        anims = []
        for nid in path_node_ids:
            if nid in self.node_groups:
                node = self.node_groups[nid]
                anims.append(node[0].animate.set_stroke(color=active_color, width=3.0))
        return anims

    def prune_node(self, node_id: str):
        """Dims or strikes out a failing AST node."""
        if node_id in self.node_groups:
            node = self.node_groups[node_id]
            slash = Line(
                node.get_corner(DL), node.get_corner(UR),
                color="#EF4444", stroke_width=2.5
            )
            return VGroup(node.animate.set_opacity(0.2), Create(slash))
        return None
