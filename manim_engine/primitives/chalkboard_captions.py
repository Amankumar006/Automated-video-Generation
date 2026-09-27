"""
The Model Verse — Chalkboard Kinetic Captions Component
Provides sleek, floating chalkboard caption pills with kinetic word highlighting
designed specifically for vertical 9:16 short-form video.
"""

from manim import *
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from pipeline.config import (
    FONT_HELVETICA, COLOR_MINT, COLOR_GOLD, COLOR_DANGER,
    FRAME_WIDTH, FRAME_HEIGHT
)

class ChalkboardCaptions:
    def __init__(self, scene: Scene, y_pos: float = -4.8, default_font_size: int = 24):
        self.scene = scene
        self.y_pos = y_pos
        self.default_font_size = default_font_size
        self.current_pill = None
        self.max_width = 6.4

    def _create_pill(self, text: str, highlights: dict = None) -> VGroup:
        """Constructs a beautifully styled chalkboard caption pill."""
        t2c = {}
        if highlights:
            for word, color in highlights.items():
                t2c[word] = color

        import textwrap
        display_text = textwrap.fill(text, width=34) if len(text) > 36 else text

        # Start with default font size
        txt = Text(
            display_text,
            font=FONT_HELVETICA,
            font_size=self.default_font_size,
            weight=BOLD,
            color=WHITE,
            t2c=t2c
        )
        
        # Scale text if it exceeds maximum safe horizontal width
        if txt.width > self.max_width - 0.70:
            txt.scale_to_fit_width(self.max_width - 0.70)

        pill_width = min(txt.width + 0.65, self.max_width)
        pill_height = txt.height + 0.40

        bg = RoundedRectangle(
            corner_radius=0.20,
            width=pill_width,
            height=pill_height,
            fill_color="#080C14",
            fill_opacity=0.92,
            stroke_color="#334155",
            stroke_width=1.6
        )

        group = VGroup(bg, txt).move_to([0, self.y_pos, 0])
        return group

    def show(self, text: str, highlights: dict = None, run_time: float = 0.25) -> Animation:
        """Initial appearance of the caption pill."""
        new_pill = self._create_pill(text, highlights)
        if self.current_pill is None:
            self.current_pill = new_pill
            return FadeIn(
                new_pill,
                shift=UP * 0.15,
                rate_func=lambda t: min(1.0, t / 0.20) if t < 0.20 else 1.0,
                run_time=run_time
            )
        else:
            old_pill = self.current_pill
            self.current_pill = new_pill
            # Fast, crisp cross-fade without glyph warping or letter collision
            return FadeTransform(
                old_pill,
                new_pill,
                stretch=False,
                rate_func=lambda t: min(1.0, t / 0.18) if t < 0.18 else 1.0,
                run_time=run_time
            )

    def morph_to(self, text: str, highlights: dict = None, run_time: float = 0.25) -> Animation:
        """Morphs the current caption into a new phrase cleanly."""
        return self.show(text, highlights, run_time=run_time)

    def hide(self, run_time: float = 0.25) -> Animation:
        """Fades out and removes the current caption."""
        if self.current_pill is not None:
            anim = FadeOut(
                self.current_pill,
                shift=DOWN * 0.15,
                rate_func=lambda t: min(1.0, t / 0.20) if t < 0.20 else 1.0,
                run_time=run_time
            )
            self.current_pill = None
            return anim
        return Wait(0.01)
