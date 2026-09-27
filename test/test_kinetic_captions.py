from manim import *
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from pipeline.config import (
    FONT_HELVETICA, COLOR_MINT, COLOR_GOLD, VIDEO_WIDTH, VIDEO_HEIGHT,
    FRAME_WIDTH, FRAME_HEIGHT, BG_CARBON
)

config.pixel_width = VIDEO_WIDTH
config.pixel_height = VIDEO_HEIGHT
config.frame_width = FRAME_WIDTH
config.frame_height = FRAME_HEIGHT
config.background_color = BG_CARBON

class TestKineticCaptionsScene(Scene):
    def construct(self):
        bg_dots = [Dot(point=[x * 0.95, y * 0.95, 0], radius=0.02, color="#1E293B", fill_opacity=0.35)
                   for x in range(-4, 5) for y in range(-7, 8)]
        self.add(VGroup(*bg_dots))

        def make_pill(text, t2c=None):
            txt = Text(
                text,
                font=FONT_HELVETICA,
                font_size=24,
                weight=BOLD,
                color=WHITE,
                t2c=t2c or {}
            )
            pill = RoundedRectangle(
                corner_radius=0.22,
                width=txt.width + 0.70,
                height=txt.height + 0.42,
                fill_color="#080C14",
                fill_opacity=0.92,
                stroke_color="#334155",
                stroke_width=1.8
            )
            return VGroup(pill, txt).shift(DOWN * 4.8)

        cap1 = make_pill("DeepSeek-V3 has 671 billion parameters.", {"671 billion": COLOR_MINT, "DeepSeek-V3": "#38BDF8"})
        cap2 = make_pill("But running it costs almost nothing.", {"almost nothing": COLOR_GOLD})
        cap3 = make_pill("How?", {"How?": COLOR_MINT})

        self.play(FadeIn(cap1, shift=UP * 0.15), run_time=0.3)
        self.wait(1.0)
        self.play(ReplacementTransform(cap1, cap2), run_time=0.25)
        self.wait(1.0)
        self.play(ReplacementTransform(cap2, cap3), run_time=0.25)
        self.wait(0.8)
        self.play(FadeOut(cap3, shift=DOWN * 0.15), run_time=0.3)
