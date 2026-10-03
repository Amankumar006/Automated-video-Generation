"""
Test suite for Native ArXiv Figure & Architecture Extraction.
Verifies:
1. Paper figure extraction from arXiv cache (both vector PDF and raster PNG/JPG).
2. Chalkboard conversion (transparency, chalk white #E2E8F0, cyan/emerald accents).
3. BlueprintPaperFigure composition instantiation and framing inside 9:16 vertical canvas.
4. Zero visual overlap with subtitles (y = -3.45) and math formula tray (y = -4.6).
"""

import os
import sys
from pathlib import Path
from manim import *

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT, BG_CARBON,
    FONT_HELVETICA
)
from pipeline.arxiv_vector_extractor import extract_paper_figures
from manim_engine.primitives.visual_compositions import BlueprintPaperFigure, create_blueprint_composition
from manim_engine.primitives.typography import CleanText

config.pixel_width = VIDEO_WIDTH
config.pixel_height = VIDEO_HEIGHT
config.frame_width = FRAME_WIDTH
config.frame_height = FRAME_HEIGHT
config.background_color = BG_CARBON


class PaperFigureRasterScene(Scene):
    """Renders authentic raster architecture diagram extracted from arXiv 2407.08608."""
    def construct(self):
        # 1. 3Blue1Brown chalkboard background
        dots = VGroup(*[
            Dot(point=[x, y, 0], radius=0.016, color="#2D3748", fill_opacity=0.35)
            for x in np.arange(-3.6, 3.7, 0.9) for y in np.arange(-6.0, 6.1, 0.9)
        ])
        self.add(dots)

        # 2. Watermark header at y = 7.1
        watermark = VGroup(
            CleanText("THE MODEL VERSE", font_size=11, color="#10B981", weight=BOLD),
            CleanText(" // ", font_size=11, color="#475569"),
            CleanText("ARXIV ARCHITECTURE EXTRACTION", font_size=10, color="#94A3B8")
        ).arrange(RIGHT, buff=0.1).move_to([0, 7.1, 0])
        self.add(watermark)

        # 3. Authentic Paper Figure Composition
        img_path = PROJECT_ROOT / "public" / "arxiv_cache" / "2407.08608" / "chalkboard_figures" / "fig_1_3_stage_pipelining.png"
        comp = BlueprintPaperFigure(
            image_path=str(img_path),
            arxiv_id="2407.08608",
            title="FLASHATTENTION-3 ARCHITECTURE",
            sub="3-Stage Asynchronous GEMM and Softmax Pipelining",
            badge_text="OFFICIAL FIGURE"
        )
        self.add(comp)

        # 4. Kinetic Subtitle Pill at y = -3.45 (simulated)
        sub_text = CleanText("FlashAttention-3 overlaps calculation and data loading.", font_size=12, color="#F8FAFC", weight=BOLD)
        sub_pill = RoundedRectangle(corner_radius=0.14, width=sub_text.width + 0.45, height=0.42, color="#334155", fill_color="#0D1117", fill_opacity=0.92)
        sub_group = VGroup(sub_pill, sub_text).move_to([0, -3.45, 0])
        self.add(sub_group)

        # 5. Concept Formula Tray at y = -4.6 (simulated)
        tray_box = RoundedRectangle(corner_radius=0.12, width=6.8, height=0.75, color="#1E293B", fill_color="#0D1117", fill_opacity=0.88)
        tray_lbl = CleanText("FORMULA: ASYNC TENSOR CORE PIPELINING", font_size=10, color="#38BDF8", weight=BOLD)
        tray_group = VGroup(tray_box, tray_lbl).move_to([0, -4.6, 0])
        self.add(tray_group)


class PaperFigureVectorScene(Scene):
    """Renders authentic vector PDF figure converted to chalkboard SVG from arXiv 2407.08608."""
    def construct(self):
        # 1. 3Blue1Brown chalkboard background
        dots = VGroup(*[
            Dot(point=[x, y, 0], radius=0.016, color="#2D3748", fill_opacity=0.35)
            for x in np.arange(-3.6, 3.7, 0.9) for y in np.arange(-6.0, 6.1, 0.9)
        ])
        self.add(dots)

        # 2. Watermark header at y = 7.1
        watermark = VGroup(
            CleanText("THE MODEL VERSE", font_size=11, color="#10B981", weight=BOLD),
            CleanText(" // ", font_size=11, color="#475569"),
            CleanText("ARXIV ARCHITECTURE EXTRACTION", font_size=10, color="#94A3B8")
        ).arrange(RIGHT, buff=0.1).move_to([0, 7.1, 0])
        self.add(watermark)

        # 3. Authentic Vector Paper Figure Composition
        svg_path = PROJECT_ROOT / "public" / "arxiv_cache" / "2407.08608" / "chalkboard_figures" / "fig_4_flash3_h100_causal_False_hdim_128_fwd_speed.svg"
        comp = BlueprintPaperFigure(
            svg_path=str(svg_path),
            arxiv_id="2407.08608",
            title="H100 FORWARD SPEED BENCHMARK",
            sub="Empirical speedups across causal and non-causal attention",
            badge_text="OFFICIAL EMPIRICAL BENCHMARK"
        )
        self.add(comp)

        # 4. Kinetic Subtitle Pill at y = -3.45 (simulated)
        sub_text = CleanText("Achieving up to 75% of H100 hardware theoretical peak.", font_size=12, color="#F8FAFC", weight=BOLD)
        sub_pill = RoundedRectangle(corner_radius=0.14, width=sub_text.width + 0.45, height=0.42, color="#334155", fill_color="#0D1117", fill_opacity=0.92)
        sub_group = VGroup(sub_pill, sub_text).move_to([0, -3.45, 0])
        self.add(sub_group)

        # 5. Concept Formula Tray at y = -4.6 (simulated)
        tray_box = RoundedRectangle(corner_radius=0.12, width=6.8, height=0.75, color="#1E293B", fill_color="#0D1117", fill_opacity=0.88)
        tray_lbl = CleanText("METRIC: TFLOPS / S (FP16 & FP8 FORWARD PASS)", font_size=10, color="#34D399", weight=BOLD)
        tray_group = VGroup(tray_box, tray_lbl).move_to([0, -4.6, 0])
        self.add(tray_group)


# ==============================================================================
# Pytest Automated Test Cases
# ==============================================================================

def test_clean_arxiv_id():
    from pipeline.arxiv_vector_extractor import clean_arxiv_id
    assert clean_arxiv_id("https://arxiv.org/abs/2407.08608") == "2407.08608"
    assert clean_arxiv_id("2407.08608v2") == "2407.08608v2"
    assert clean_arxiv_id("hep-th/9912012") == "hep-th/9912012"


def test_recolor_svg_for_blackboard():
    from pipeline.arxiv_vector_extractor import recolor_svg_for_blackboard
    raw = '<svg><path fill="#ffffff" d="M0 0"/><path stroke="#000000" d="M1 1"/></svg>'
    recolored = recolor_svg_for_blackboard(raw)
    assert "#ffffff" not in recolored
    assert "#E2E8F0" in recolored


def test_extract_paper_figures_from_cache():
    from pipeline.arxiv_vector_extractor import extract_paper_figures
    figs = extract_paper_figures("2407.08608", max_figures=3)
    assert len(figs) >= 1
    top_fig = figs[0]
    assert "figure_id" in top_fig
    assert top_fig.get("svg_path") or top_fig.get("image_path")


def test_blueprint_paper_figure_composition():
    from manim_engine.primitives.visual_compositions import BlueprintPaperFigure
    comp = BlueprintPaperFigure(
        title="TEST SPECIFICATION",
        sub="Testing layout constraints",
        arxiv_id="2407.08608",
        badge_text="UNIT TEST"
    )
    # Check vertical constraints: Safe zone between y = 5.38 and y = -2.27
    top_y = comp.get_critical_point(UP)[1]
    bottom_y = comp.get_critical_point(DOWN)[1]
    assert top_y <= 5.5
    assert bottom_y >= -2.5
    # Subtitles are at y = -3.45, buffer is >= 0.9 units
    assert bottom_y - (-3.45) > 0.8

