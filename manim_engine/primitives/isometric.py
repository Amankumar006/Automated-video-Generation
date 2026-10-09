"""
The Model Verse — 2.5D Isometric Perspective & Axonometric Engine (Engine 8.0)
Provides genuine 2.5D depth and spatial staging for architectural diagrams,
stacked latent representations, memory matrices, and neural pipelines.
Replaces flat 2D zooming with authentic axonometric perspective tilts.
"""

from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from manim import *

from pipeline.config import FONT_HELVETICA
from manim_engine.primitives.typography import CleanText

# Standard Palette
COLOR_CYAN = "#38BDF8"
COLOR_MINT = "#34D399"
COLOR_AMBER = "#F59E0B"
COLOR_PURPLE = "#A855F7"
COLOR_WHITE = "#F8FAFC"
COLOR_SLATE = "#94A3B8"
COLOR_DARK_SLATE = "#334155"
COLOR_PANEL_BG = "#0D1117"


def get_isometric_matrix(shear: float = 0.38, tilt: float = 0.62) -> np.ndarray:
    """
    Returns a 3x3 axonometric/isometric projection matrix in 2.5D space:
      x' = x - shear * y
      y' = (shear * 0.4) * x + tilt * y
      z' = z
    """
    return np.array([
        [1.0, -shear, 0.0],
        [shear * 0.42, tilt, 0.0],
        [0.0, 0.0, 1.0]
    ])


def apply_isometric_tilt(
    mobject: Mobject,
    shear: float = 0.38,
    tilt: float = 0.62,
    in_place: bool = True
) -> Mobject:
    """
    Applies 2.5D isometric projection matrix to any Mobject or VGroup,
    tilting flat 2D diagrams into an angled architectural plane.
    """
    mat = get_isometric_matrix(shear=shear, tilt=tilt)
    center = mobject.get_center() if in_place else ORIGIN
    mobject.shift(-center)
    mobject.apply_matrix(mat)
    if in_place:
        mobject.shift(center)
    return mobject


def create_isometric_slab(
    width: float = 4.8,
    height: float = 2.0,
    thickness: float = 0.35,
    face_color: str = "#0F172A",
    rim_color: str = "#1E293B",
    stroke_color: str = COLOR_CYAN,
    stroke_width: float = 2.0,
    face_opacity: float = 0.92,
    shear: float = 0.38,
    tilt: float = 0.62
) -> VGroup:
    """
    Creates an extruded 2.5D axonometric slab with top surface and depth rim.
    """
    w2, h2 = width / 2.0, height / 2.0
    pts_2d = np.array([
        [-w2, -h2, 0.0],
        [ w2, -h2, 0.0],
        [ w2,  h2, 0.0],
        [-w2,  h2, 0.0]
    ])
    mat = get_isometric_matrix(shear=shear, tilt=tilt)
    top_pts = pts_2d @ mat.T

    # Top face
    top_face = Polygon(
        *top_pts,
        fill_color=face_color,
        fill_opacity=face_opacity,
        stroke_color=stroke_color,
        stroke_width=stroke_width
    )

    # Front extrusion rim
    front_pts = [
        top_pts[0],
        top_pts[1],
        top_pts[1] + np.array([0, -thickness, 0]),
        top_pts[0] + np.array([0, -thickness, 0]),
    ]
    front_rim = Polygon(
        *front_pts,
        fill_color=rim_color,
        fill_opacity=0.96,
        stroke_color=stroke_color,
        stroke_width=stroke_width * 0.75
    )

    # Right side extrusion rim
    side_pts = [
        top_pts[1],
        top_pts[2],
        top_pts[2] + np.array([0, -thickness, 0]),
        top_pts[1] + np.array([0, -thickness, 0]),
    ]
    side_rim = Polygon(
        *side_pts,
        fill_color=rim_color,
        fill_opacity=0.88,
        stroke_color=stroke_color,
        stroke_width=stroke_width * 0.75
    )

    slab_group = VGroup(side_rim, front_rim, top_face)
    return slab_group


def create_isometric_layer_stack(
    layers_data: List[Tuple[str, str, float]],
    width: float = 4.6,
    height: float = 1.6,
    thickness: float = 0.28,
    spacing: float = 1.65,
    base_y: float = -1.6
) -> Tuple[VGroup, VGroup]:
    """
    Builds stacked 2.5D isometric tiers (e.g. Input Tokens, Latent Space, Synthesized Output)
    with glowing vertical projection rays connecting corresponding nodes across tiers.
    """
    stack_group = VGroup()
    projection_rays = VGroup()

    slab_centers = []
    for idx, (label, accent_col, y_offset) in enumerate(layers_data):
        curr_y = base_y + idx * spacing + y_offset
        slab = create_isometric_slab(
            width=width - idx * 0.2,
            height=height,
            thickness=thickness,
            face_color="#090D16",
            rim_color="#131B2E",
            stroke_color=accent_col,
            stroke_width=2.2
        ).move_to([0, curr_y, 0])

        lbl = CleanText(
            label[:26].upper(),
            font=FONT_HELVETICA,
            font_size=11,
            color=accent_col,
            weight=BOLD
        ).move_to(slab[2].get_center())  # Centered on top face

        badge = RoundedRectangle(
            corner_radius=0.08,
            width=1.0,
            height=0.32,
            color=accent_col,
            fill_color=accent_col,
            fill_opacity=0.25,
            stroke_width=1.2
        ).move_to(slab[2].get_left() + RIGHT * 0.9)
        badge_txt = CleanText(f"L{idx+1}", font=FONT_HELVETICA, font_size=9, color=accent_col, weight=BOLD).move_to(badge)

        tier = VGroup(slab, badge, badge_txt, lbl)
        stack_group.add(tier)
        slab_centers.append(slab[2].get_center())

    # Vertical projection rays connecting stacked tiers
    for i in range(len(slab_centers) - 1):
        c_low = slab_centers[i]
        c_high = slab_centers[i+1]
        for dx in [-1.5, 0.0, 1.5]:
            p1 = c_low + np.array([dx, 0.2, 0])
            p2 = c_high + np.array([dx, -0.3, 0])
            ray = DashedLine(
                start=p1,
                end=p2,
                color=COLOR_CYAN,
                stroke_width=1.8,
                dash_length=0.1,
                stroke_opacity=0.75
            )
            projection_rays.add(ray)

    return stack_group, projection_rays
