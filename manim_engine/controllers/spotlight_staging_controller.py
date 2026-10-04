"""
The Model Verse — Cognitive Spotlight Staging Controller (Visual Engine 7.0)
Enforces visual hierarchy and cognitive focus on 9:16 mobile canvases:
  - Active focal element: 100% bright, fully saturated, with ambient accent halo.
  - Inactive / background elements: Dimmed to 20% opacity (stroke/fill).
  - Eliminates visual clutter and flat PowerPoint-style diagrams.
"""

from typing import Optional, List, Dict, Any, Tuple
from manim import *
import numpy as np


class SpotlightStagingController:
    """
    Directs viewer attention by staging visual compositions with cinematic spotlights.
    Dynamically identifies active narrative targets from SVO triples and highlights keywords,
    illuminating the focal mechanism while dimming peripheral geometry to 20% opacity.
    """

    def __init__(self, default_dim_opacity: float = 0.55):
        self.default_dim_opacity = default_dim_opacity
        self.active_halo: Optional[Mobject] = None

    def identify_focal_and_background(
        self,
        motif: Mobject,
        svo_action: Optional[Dict[str, Any]] = None,
        highlight_words: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Mobject], List[Mobject]]:
        """
        Partitions motif submobjects into focal targets and background elements.
        """
        focal_elements: List[Mobject] = []
        background_elements: List[Mobject] = []

        # 1. Blueprint-specific structural introspection
        # Grid Memory
        if hasattr(motif, "active_cell") and motif.active_cell:
            focal_elements.append(motif.active_cell)
            if hasattr(motif, "cells"):
                for c in motif.cells:
                    if c != motif.active_cell:
                        background_elements.append(c)
            return focal_elements, background_elements

        # Split Flow
        if hasattr(motif, "branch_a_group") and hasattr(motif, "branch_b_group"):
            target_obj = (svo_action.get("direct_object", "") if svo_action else "").lower()
            if "semantic" in target_obj or "stream a" in target_obj or "left" in target_obj:
                focal_elements.append(motif.branch_a_group)
                background_elements.append(motif.branch_b_group)
                if hasattr(motif, "router_node"):
                    background_elements.append(motif.router_node)
            elif "geometric" in target_obj or "stream b" in target_obj or "depth" in target_obj:
                focal_elements.append(motif.branch_b_group)
                background_elements.append(motif.branch_a_group)
                if hasattr(motif, "router_node"):
                    background_elements.append(motif.router_node)
            else:
                if hasattr(motif, "router_node"):
                    focal_elements.append(motif.router_node)
                background_elements.extend([motif.branch_a_group, motif.branch_b_group])
            return focal_elements, background_elements

        # Pipeline Stages
        if hasattr(motif, "stage_1_group") and hasattr(motif, "stage_2_group") and hasattr(motif, "stage_3_group"):
            action_verb = (svo_action.get("action_verb", "") if svo_action else "").lower()
            role = (svo_action.get("semantic_role", "") if svo_action else "").lower()
            if "transform" in action_verb or "kernel" in action_verb or "bottleneck" in role:
                focal_elements.append(motif.stage_2_group)
                background_elements.extend([motif.stage_1_group, motif.stage_3_group])
            elif "output" in role or "victory" in role or "reconstruct" in action_verb:
                focal_elements.append(motif.stage_3_group)
                background_elements.extend([motif.stage_1_group, motif.stage_2_group])
            else:
                focal_elements.append(motif.stage_1_group)
                background_elements.extend([motif.stage_2_group, motif.stage_3_group])
            return focal_elements, background_elements

        # Tree Hierarchy / MCTS
        if hasattr(motif, "optimal_group") and hasattr(motif, "pruned_group"):
            focal_elements.append(motif.optimal_group)
            background_elements.append(motif.pruned_group)
            if hasattr(motif, "root_node"):
                background_elements.append(motif.root_node)
            return focal_elements, background_elements

        # Benchmark Drag-Race Bars
        if hasattr(motif, "hero_bar") and motif.hero_bar:
            focal_elements.append(motif.hero_bar)
            if hasattr(motif, "competitor_bars"):
                background_elements.extend(motif.competitor_bars)
            return focal_elements, background_elements

        # Chalkboard Code Block
        if hasattr(motif, "highlighted_lines") and motif.highlighted_lines:
            focal_elements.extend(motif.highlighted_lines)
            if hasattr(motif, "other_lines"):
                background_elements.extend(motif.other_lines)
            return focal_elements, background_elements

        # Generic Composition with kinetic_elements attribute
        if hasattr(motif, "kinetic_elements") and motif.kinetic_elements and len(motif.kinetic_elements) > 0:
            focal_elements.append(motif.kinetic_elements)
            if hasattr(motif, "content_group") and motif.content_group:
                for submob in motif.content_group:
                    if submob != motif.kinetic_elements:
                        background_elements.append(submob)
            return focal_elements, background_elements

        # Fallback: Partition top-level submobjects if group has multiple children
        children = list(motif.submobjects)
        if len(children) > 1:
            focal_elements.append(children[0])
            background_elements.extend(children[1:])
        elif children:
            focal_elements.append(children[0])

        return focal_elements, background_elements

    def create_spotlight_halo(self, focal_mobject: Mobject, color: str = "#38BDF8") -> Mobject:
        """
        Creates an ambient glowing halo outline around the active focal mobject.
        """
        halo = SurroundingRectangle(
            focal_mobject,
            buff=0.15,
            corner_radius=0.14,
            color=color,
            stroke_width=2.5,
            stroke_opacity=0.85
        )
        return halo

    def build_spotlight_animations(
        self,
        focal_elements: List[Mobject],
        background_elements: List[Mobject],
        run_time: float = 0.6,
        dim_opacity: Optional[float] = None
    ) -> List[Animation]:
        """
        Builds the transition animations that spotlight the focal element and dim background elements.
        """
        target_dim = dim_opacity if dim_opacity is not None else self.default_dim_opacity
        anims: List[Animation] = []

        # 1. Dim background elements to target opacity (20%)
        for bg in background_elements:
            if hasattr(bg, "animate"):
                anims.append(
                    bg.animate(run_time=run_time, rate_func=smooth).set_opacity(target_dim)
                )

        # 2. Illuminate focal elements to 100% opacity and subtle scale pulse
        for f in focal_elements:
            if hasattr(f, "animate"):
                anims.append(
                    f.animate(run_time=run_time, rate_func=smooth).set_opacity(1.0)
                )

        return anims

    def apply_spotlight(
        self,
        scene: Scene,
        motif: Mobject,
        svo_action: Optional[Dict[str, Any]] = None,
        highlight_words: Optional[Dict[str, Any]] = None,
        run_time: float = 0.45,
        dim_opacity: Optional[float] = None,
        play_now: bool = True
    ) -> List[Animation]:
        """
        Applies spotlight staging directly on the given scene or returns animations.
        """
        focal, bg = self.identify_focal_and_background(motif, svo_action, highlight_words)
        if not focal or not bg:
            return []

        anims = self.build_spotlight_animations(
            focal_elements=focal,
            background_elements=bg,
            run_time=run_time,
            dim_opacity=dim_opacity
        )

        if anims and play_now:
            scene.play(*anims)
        return anims


# Global singleton instance
spotlight_staging_controller = SpotlightStagingController()
