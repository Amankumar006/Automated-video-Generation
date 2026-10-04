"""
The Model Verse — Kinetic Camera Controller & Multi-Layer Depth Coordinator (Engine 7.0)
Eliminates static frames via:
  1. Continuous 3Blue1Brown-style camera breathing and ambient drift.
  2. Dynamic punch-in zooms on high-impact anchor words (e.g. 70% compute waste, 4x speedup).
  3. Multi-Layer Depth Sandwich coordination (Ambient Backdrop, Geometric Core, Kinetic Typography HUD).
"""

from typing import Optional, List, Dict, Any, Tuple
from manim import *
import numpy as np

from pipeline.config import FRAME_WIDTH, FRAME_HEIGHT


class KineticCameraController:
    """
    Kinetic Camera Controller that choreographs camera motion and multi-layer depth.
    Ensures zero static dead screens by orchestrating micro-motion, punch-in zooms,
    and fluid camera breathing throughout narrations.
    """

    def __init__(
        self,
        default_zoom_factor: float = 0.975,
        punch_in_factor: float = 0.94,
        drift_vector: np.ndarray = np.array([0.0, 0.08, 0.0])
    ):
        self.default_zoom_factor = default_zoom_factor
        self.punch_in_factor = punch_in_factor
        self.drift_vector = drift_vector

    def get_ambient_drift_animation(
        self,
        camera_frame: Mobject,
        duration: float,
        scale_factor: Optional[float] = None,
        shift_vector: Optional[np.ndarray] = None
    ) -> Animation:
        """
        Creates continuous cinematic micro-push-in and subtle vertical drift
        over the entire remaining narration window.
        """
        s_factor = scale_factor if scale_factor is not None else self.default_zoom_factor
        s_vec = shift_vector if shift_vector is not None else self.drift_vector

        return camera_frame.animate(rate_func=linear, run_time=duration).scale(s_factor).shift(s_vec)

    def get_punch_in_animation(
        self,
        camera_frame: Mobject,
        target_point: Optional[np.ndarray] = None,
        zoom_factor: Optional[float] = None,
        run_time: float = 0.45
    ) -> Animation:
        """
        Returns dynamic punch-in camera zoom animation to be played concurrently with focal actions.
        """
        z_factor = zoom_factor if zoom_factor is not None else self.punch_in_factor
        t_pt = target_point if target_point is not None else ORIGIN
        return camera_frame.animate(rate_func=smooth, run_time=run_time).scale(z_factor).move_to(t_pt * 0.4)

    def get_reset_animation(
        self,
        camera_frame: Mobject,
        run_time: float = 0.35
    ) -> Animation:
        """
        Returns framing reset animation to be played concurrently with motif exit.
        """
        return camera_frame.animate(rate_func=smooth, run_time=run_time).set(width=FRAME_WIDTH, height=FRAME_HEIGHT).move_to(ORIGIN)

    def punch_in_zoom(
        self,
        scene: MovingCameraScene,
        target_point: Optional[np.ndarray] = None,
        zoom_factor: Optional[float] = None,
        run_time: float = 0.45
    ):
        """
        Performs a dynamic punch-in camera zoom towards a focal target point
        when a high-impact narrative anchor word fires.
        """
        scene.play(
            self.get_punch_in_animation(
                camera_frame=scene.camera.frame,
                target_point=target_point,
                zoom_factor=zoom_factor,
                run_time=run_time
            ),
            run_time=run_time
        )

    def reset_framing(
        self,
        scene: MovingCameraScene,
        run_time: float = 0.35
    ):
        """
        Smoothly restores camera framing to the standard 9:16 mobile canvas dimensions.
        """
        scene.play(
            self.get_reset_animation(
                camera_frame=scene.camera.frame,
                run_time=run_time
            ),
            run_time=run_time
        )

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
