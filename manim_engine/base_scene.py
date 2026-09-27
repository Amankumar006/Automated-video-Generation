"""
The Model Verse — Base Manim Scene for 9:16 Vertical Video Production
"""

from manim import *
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from pipeline.config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT,
    BG_CARBON, FONT_HELVETICA, COLOR_MINT
)

# Apply global Manim configuration
config.pixel_width = VIDEO_WIDTH
config.pixel_height = VIDEO_HEIGHT
config.frame_width = FRAME_WIDTH
config.frame_height = FRAME_HEIGHT
config.background_color = BG_CARBON

class BaseShortScene(MovingCameraScene):
    """Base class for all short-form videos across categories."""
    
    def setup_canvas(self, category_label: str = "ARCHITECTURE LAB"):
        """Initializes dot grid matrix and persistent safe-zone brand watermark."""
        bg_dots = []
        for x in range(-4, 5):
            for y in range(-7, 8):
                d = Dot(point=[x * 0.95, y * 0.95, 0], radius=0.02, color="#1E293B", fill_opacity=0.35)
                bg_dots.append(d)
        self.dot_grid = VGroup(*bg_dots)
        self.add(self.dot_grid)

        # Top safe-zone brand watermark (7.1 UP keeps it safely below platform top controls)
        self.brand_tag = VGroup(
            Text("THE MODEL VERSE", font=FONT_HELVETICA, font_size=20, color=COLOR_MINT, weight=BOLD),
            Text(" // ", font=FONT_HELVETICA, font_size=18, color="#475569"),
            Text(category_label, font=FONT_HELVETICA, font_size=18, color="#94A3B8", weight=MEDIUM),
        ).arrange(RIGHT, buff=0.12).shift(UP * 7.1)
        self.add(self.brand_tag)

    def clean_transition(self, mobjects_to_remove: list, run_time: float = 0.5):
        """Cleanly wipes out scene elements to prevent spatial collisions and overlaps."""
        if mobjects_to_remove:
            self.play(*[FadeOut(m) for m in mobjects_to_remove if m is not None], run_time=run_time)

    def camera_push_and_recover(self, target_pos: np.ndarray, scale: float = 0.90, zoom_time: float = 1.0, hold_action=None, pull_time: float = 0.8):
        """Motivated camera movement to highlight key calculations, then return."""
        self.play(self.camera.frame.animate.scale(scale).move_to(target_pos), run_time=zoom_time)
        if hold_action:
            hold_action()
        self.play(self.camera.frame.animate.scale(1 / scale).move_to(ORIGIN), run_time=pull_time)

    def reset_camera(self, run_time: float = 0.4):
        """Cleanly resets camera position and scale back to absolute origin."""
        self.play(self.camera.frame.animate.move_to(ORIGIN).set(width=FRAME_WIDTH, height=FRAME_HEIGHT), run_time=run_time)

