"""
The Model Verse — Manim Engine Visual & Kinetic Controllers (Engine 7.0)
Provides:
  - SpotlightStagingController: Cognitive visual hierarchy via selective 100% focal illumination and 20% background dimming.
  - KineticCameraController: Zero-static-frame dynamic camera breathing, keyword punch-ins, and multi-layer depth coordination.
"""

from manim_engine.controllers.spotlight_staging_controller import SpotlightStagingController
from manim_engine.controllers.kinetic_camera_controller import KineticCameraController

__all__ = ["SpotlightStagingController", "KineticCameraController"]
