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

class TestCaptionScene(Scene):
    __test__ = False

    def construct(self):
        # Background coordinate grid for context
        bg_dots = [Dot(point=[x * 0.95, y * 0.95, 0], radius=0.02, color="#1E293B", fill_opacity=0.35)
                   for x in range(-4, 5) for y in range(-7, 8)]
        self.add(VGroup(*bg_dots))

        # Sample math formula in background
        formula = SVGMobject("public/math_svgs/param_scale.svg").scale_to_fit_width(6.2).shift(UP * 0.5)
        self.add(formula)

        # Kinetic chalkboard caption pill
        txt = Text(
            "DeepSeek-V3 has 671 billion parameters.",
            font=FONT_HELVETICA,
            font_size=24,
            weight=BOLD,
            color=WHITE,
            t2c={"671 billion": COLOR_MINT, "DeepSeek-V3": "#38BDF8"}
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
        caption_group = VGroup(pill, txt).shift(DOWN * 4.8)
        self.add(caption_group)
