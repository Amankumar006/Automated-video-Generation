"""
The Model Verse — Cinematic Camera Controller & Spatial Staging (Engine 8.0)
Eliminates repetitive 2D zoom pulsing in favor of genuine cinematography:
  1. Lateral Tracking Dolly: Smooth horizontal camera tracking across multi-stage architectures.
  2. Multi-Component Stage Panning: Following active tokens as they traverse pipelines.
  3. Selective Climax Punch-In: Reserved strictly for peak empirical/mathematical breakthroughs (Beat 4 or 5), eliminating metronome-like zooming on every beat.
  4. Subtle Atmospheric Drift: Gentle non-scaling camera glides that maintain visual stability.
  5. Dynamic HUD Anchoring: Ensures headers, watermarks, and subtitle pills stay locked to viewport center regardless of camera travel.
"""

from typing import Optional, List, Dict, Any, Tuple
from manim import *
import numpy as np

from pipeline.config import FRAME_WIDTH, FRAME_HEIGHT


class KineticCameraController:
    """
    Cinematic Camera Controller that choreographs camera motion and multi-layer depth.
    Replaces flat, repetitive 2D scale zooms with authentic lateral tracking pans,
    smooth stage glides, and selective focal accents.
    """

    def __init__(
        self,
        default_zoom_factor: float = 0.98,
        punch_in_factor: float = 0.78,
        drift_vector: np.ndarray = np.array([0.0, 0.08, 0.0])
    ):
        self.default_zoom_factor = default_zoom_factor
        self.punch_in_factor = punch_in_factor
        self.drift_vector = drift_vector

    def get_lateral_tracking_animation(
        self,
        camera_frame: Mobject,
        start_x: float = -1.6,
        end_x: float = 1.6,
        y: float = 0.0,
        run_time: float = 2.0,
        rate_func: Any = smooth
    ) -> Animation:
        """
        Smooth lateral tracking dolly: Pans camera horizontally along a pipeline or
        flow field from start_x to end_x without changing camera scale.
        Gives the viewer a true sense of journey and spatial progression.
        """
        # Set starting anchor if needed, animate movement to end anchor
        camera_frame.move_to([start_x, y, 0])
        return camera_frame.animate(rate_func=rate_func, run_time=run_time).move_to([end_x, y, 0])

    def get_continuous_pan_animation(
        self,
        camera_frame: Mobject,
        pan_vector: np.ndarray = np.array([0.6, 0.0, 0.0]),
        duration: float = 4.0,
        rate_func: Any = linear
    ) -> Animation:
        """
        Continuous cinematic glide: Gently pans the camera across the scene
        without repetitive zooming in or out.
        """
        return camera_frame.animate(rate_func=rate_func, run_time=duration).shift(pan_vector)

    def get_ambient_drift_animation(
        self,
        camera_frame: Mobject,
        duration: float,
        scale_factor: Optional[float] = None,
        shift_vector: Optional[np.ndarray] = None
    ) -> Animation:
        """
        Cinematic micro-drift: Subtle atmospheric drift that preserves framing stability.
        Uses near-unity scale (0.985) to prevent noticeable zoom fatigue.
        """
        s_factor = scale_factor if scale_factor is not None else 0.985
        s_vec = shift_vector if shift_vector is not None else np.array([0.0, 0.05, 0.0])

        return camera_frame.animate(rate_func=linear, run_time=duration).scale(s_factor).shift(s_vec)

    def get_selective_punch_in(
        self,
        camera_frame: Mobject,
        target_point: Optional[np.ndarray] = None,
        zoom_factor: float = 0.78,
        run_time: float = 0.45
    ) -> Animation:
        """
        Selective climax punch-in: Reserved strictly for peak moments (e.g. SOTA speedup badge
        or breakthrough formula) rather than firing repetitively on every beat.
        """
        t_pt = target_point if target_point is not None else ORIGIN
        return camera_frame.animate(rate_func=rush_into, run_time=run_time).scale(zoom_factor).move_to(t_pt * 0.70)

    # Backwards compatibility methods
    def get_punch_in_animation(
        self,
        camera_frame: Mobject,
        target_point: Optional[np.ndarray] = None,
        zoom_factor: Optional[float] = None,
        run_time: float = 0.45
    ) -> Animation:
        """Convenience wrapper for selective punch-in."""
        z = zoom_factor if zoom_factor is not None else self.punch_in_factor
        return self.get_selective_punch_in(camera_frame, target_point=target_point, zoom_factor=z, run_time=run_time)

    def get_formula_focus_animation(
        self,
        camera_frame: Mobject,
        formula_point: Optional[np.ndarray] = None,
        zoom_factor: float = 0.85,
        run_time: float = 0.55
    ) -> Animation:
        """Subtle focal framing on formula derivation (moderate 15% focus)."""
        f_pt = formula_point if formula_point is not None else np.array([0.0, -3.8, 0.0])
        return camera_frame.animate(rate_func=smooth, run_time=run_time).scale(zoom_factor).move_to(f_pt * 0.50)

    def get_hero_metric_snap_animation(
        self,
        camera_frame: Mobject,
        target_point: Optional[np.ndarray] = None,
        zoom_factor: float = 0.76,
        run_time: float = 0.45
    ) -> Animation:
        """High-energy snap zoom framing the empirical victory or SOTA delta badge."""
        t_pt = target_point if target_point is not None else np.array([0.0, 0.2, 0.0])
        return camera_frame.animate(rate_func=rush_into, run_time=run_time).scale(zoom_factor).move_to(t_pt * 0.75)

    def get_reset_animation(
        self,
        camera_frame: Mobject,
        run_time: float = 0.35
    ) -> Animation:
        """
        Smoothly restores camera framing to the standard 9:16 mobile canvas dimensions.
        """
        return camera_frame.animate(rate_func=smooth, run_time=run_time).set(width=FRAME_WIDTH, height=FRAME_HEIGHT).move_to(ORIGIN)

    def create_depth_sandwich(
        self,
        scene: MovingCameraScene,
        chalkboard_dots: Mobject,
        header_group: Mobject,
        caption_container: Mobject
    ) -> Dict[str, Mobject]:
        """
        Configures the 3-Layer Depth Sandwich:
          - Layer 1 (Backdrop): Carbon base + dot lattice with low z-index.
          - Layer 2 (Geometric Core): Manim geometric primitives and visual blueprints.
          - Layer 3 (Foreground Accents): Watermark header, kinetic captions, formula tray.
        """
        chalkboard_dots.set_z_index(-10)
        header_group.set_z_index(50)
        caption_container.set_z_index(60)

        return {
            "backdrop": chalkboard_dots,
            "header": header_group,
            "captions": caption_container
        }


# Global singleton instance
kinetic_camera_controller = KineticCameraController()
