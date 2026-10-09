"""
The Model Verse — Kinetic Particle Radiance & Luminous Dynamics Engine (Visual Engine 7.5)
Adds authentic 3Blue1Brown-caliber living particles, glowing formula ripples, and photon streams
to eliminate static frames and make technical formulas and benchmarks feel physically alive.
"""

import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from manim import *
from manim.utils.rate_functions import ease_out_cubic, ease_in_out_sine, there_and_back

from pipeline.config import FONT_HELVETICA


def create_formula_sparkle_burst(
    target_mobject: Mobject,
    color: str = "#38BDF8",
    particle_count: int = 14,
    radius: float = 0.55,
    run_time: float = 0.55
) -> Tuple[VGroup, Animation]:
    """
    Creates an explosive radial particle burst around a newly revealed formula or metric badge.
    Returns (particle_group, burst_animation).
    """
    center = target_mobject.get_center()
    particles = VGroup()
    target_points = []

    angles = np.linspace(0, 2 * np.pi, particle_count, endpoint=False)
    for i, theta in enumerate(angles):
        # Slightly jitter radius for organic physical burst
        jitter_r = radius * (0.85 + 0.35 * np.sin(i * 3.5))
        start_pt = center + np.array([np.cos(theta) * 0.12, np.sin(theta) * 0.12, 0])
        end_pt = center + np.array([np.cos(theta) * jitter_r, np.sin(theta) * jitter_r, 0])

        dot = Dot(
            point=start_pt,
            radius=0.035 if i % 2 == 0 else 0.024,
            color=color if i % 2 == 0 else "#FFFFFF",
            fill_opacity=1.0
        )
        dot.set_z_index(target_mobject.z_index + 2)
        particles.add(dot)
        target_points.append(end_pt)

    def update_burst(mob, alpha):
        for dot, end_pt in zip(mob, target_points):
            cur_pt = interpolate(center, end_pt, ease_out_cubic(alpha))
            dot.move_to(cur_pt)
            dot.set_opacity(1.0 - ease_out_cubic(alpha) ** 1.8)

    burst_anim = UpdateFromAlphaFunc(particles, update_burst, run_time=run_time)
    return particles, burst_anim


def create_formula_halo_pulse(
    target_mobject: Mobject,
    color: str = "#38BDF8",
    buff: float = 0.16,
    stroke_width: float = 2.4,
    run_time: float = 0.65
) -> Tuple[RoundedRectangle, Animation]:
    """
    Creates an expanding, glowing neon ripple ring that pulses outwards from a math formula or badge.
    """
    width = target_mobject.width + (buff * 2)
    height = target_mobject.height + (buff * 1.5)
    
    halo = RoundedRectangle(
        corner_radius=0.14,
        width=width,
        height=height,
        stroke_color=color,
        stroke_width=stroke_width,
        fill_opacity=0.0
    ).move_to(target_mobject.get_center())
    halo.set_z_index(target_mobject.z_index + 1)

    pulse_anim = halo.animate(rate_func=ease_out_cubic, run_time=run_time).scale(1.22).set_stroke(opacity=0.0, width=0.5).build()
    return halo, pulse_anim


def create_traveling_photon_stream(
    start_point: np.ndarray,
    end_point: np.ndarray,
    color: str = "#34D399",
    particle_count: int = 5,
    run_time: float = 1.2
) -> Tuple[VGroup, Animation]:
    """
    Generates a stream of glowing energy photons flowing from start_point to end_point along a vector path.
    """
    photons = VGroup()
    for i in range(particle_count):
        dot = Dot(
            point=start_point,
            radius=0.038,
            color=color,
            fill_opacity=0.85
        )
        dot.set_z_index(45)
        photons.add(dot)

    def update_stream(mob, alpha):
        for i, dot in enumerate(mob):
            # Phase offset each photon evenly
            phase = (alpha + (i / particle_count)) % 1.0
            cur_pt = interpolate(start_point, end_point, phase)
            dot.move_to(cur_pt)
            # Fade in at start, fade out at target
            opacity = np.sin(phase * np.pi)
            dot.set_opacity(opacity * 0.9)

    stream_anim = UpdateFromAlphaFunc(photons, update_stream, run_time=run_time)
    return photons, stream_anim

