"""
Test suite for Automated Multi-Model Showdown & Radar Comparison Engine.
Verifies:
1. LaTeX table parser and benchmark metric extraction from arXiv source.
2. Fallback synthesis from spec metadata / paper topics.
3. BlueprintHorizontalRaceBars layout constraints and safe zones.
4. BlueprintRadarParetoPlot layout constraints and safe zones.
5. Zero visual collisions with subtitles (y = -3.45) and math formula tray (y = -4.6).
6. Headless rendering scenes for visual inspection.
"""

import os
import sys
import numpy as np
from pathlib import Path
from manim import *

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT, BG_CARBON,
    FONT_HELVETICA
)
from pipeline.benchmark_extractor import BenchmarkExtractor, BenchmarkComparison, BenchmarkContestant
from manim_engine.primitives.showdown_engine import (
    BlueprintHorizontalRaceBars,
    BlueprintRadarParetoPlot
)
from manim_engine.primitives.typography import CleanText
from pipeline.visual_director import VisualDirector

config.pixel_width = VIDEO_WIDTH
config.pixel_height = VIDEO_HEIGHT
config.frame_width = FRAME_WIDTH
config.frame_height = FRAME_HEIGHT
config.background_color = BG_CARBON


# -----------------------------------------------------------------------------
# PYTEST UNIT TESTS
# -----------------------------------------------------------------------------

def test_clean_latex_text():
    extractor = BenchmarkExtractor()
    raw = r"\textbf{FlashAttention-3} & $1,180 \pm 12$ & \cite{dao2024} & 1.8\times"
    cleaned = extractor.clean_latex_text(raw)
    assert "FlashAttention-3" in cleaned
    assert r"\textbf" not in cleaned
    assert r"\cite" not in cleaned


def test_parse_latex_table():
    extractor = BenchmarkExtractor()
    sample_latex = r"""
    \begin{table}[h]
    \centering
    \begin{tabular}{lcccc}
    \toprule
    \textbf{Kernel Implementation} & \textbf{TFLOPS (FP16)} & \textbf{Speedup} & \textbf{Memory (GB)} \\
    \midrule
    FlashAttention-3 (Ours) & 1180.0 & 1.79x & 0.45 \\
    FlashAttention-2 & 660.0 & 1.00x & 0.52 \\
    cuDNN Flash Attention & 610.0 & 0.92x & 0.60 \\
    Standard PyTorch & 240.0 & 0.36x & 1.25 \\
    \bottomrule
    \end{tabular}
    \caption{Throughput comparison on NVIDIA H100 GPU.}
    \end{table}
    """
    comp = extractor.parse_latex_table(sample_latex)
    assert comp is not None
    assert len(comp.contestants) == 4
    assert comp.contestants[0].name.startswith("FlashAttention-3")
    assert comp.contestants[0].value == 1180.0
    assert comp.contestants[0].is_hero is True
    assert "TFLOPS" in comp.unit
    assert "+78.8%" in comp.delta_badge or "SPEEDUP" in comp.delta_badge


def test_extract_or_fallback_synthesis():
    extractor = BenchmarkExtractor()
    spec = {
        "id": "flashattention_3_speed",
        "title": "FlashAttention-3: Fast and Accurate Attention on H100",
        "category": "benchmark_news",
        "metadata": {
            "challenger": "FlashAttention-3",
            "incumbent": "FlashAttention-2",
            "milestone_metric": "Throughput (TFLOPS)"
        }
    }
    comp = extractor.extract_or_fallback(spec)
    assert comp is not None
    assert len(comp.contestants) >= 3
    assert comp.contestants[0].is_hero is True
    assert len(comp.radar_axes) == 5
    assert len(comp.radar_models) == 2
    assert comp.radar_models[0]["is_hero"] is True


def test_blueprint_horizontal_race_bars_layout():
    comp = BlueprintHorizontalRaceBars(
        title="BENCHMARK SHOWDOWN: THROUGHPUT",
        sub="Hardware throughput on NVIDIA H100 (FP16)",
        metric_name="Throughput",
        unit="TFLOPS",
        contestants=[
            {"name": "FlashAttention-3", "value": 1180.0, "display_val": "1,180 TFLOPS", "is_hero": True, "color": "#10B981"},
            {"name": "FlashAttention-2", "value": 660.0, "display_val": "660 TFLOPS", "is_hero": False, "color": "#38BDF8"},
            {"name": "cuDNN Flash", "value": 610.0, "display_val": "610 TFLOPS", "is_hero": False, "color": "#A855F7"},
            {"name": "Standard PyTorch", "value": 240.0, "display_val": "240 TFLOPS", "is_hero": False, "color": "#EF4444"}
        ],
        delta_badge="⚡ +78.8% SPEEDUP OVER FA-2"
    )

    top_y = comp.get_critical_point(UP)[1]
    bottom_y = comp.get_critical_point(DOWN)[1]

    # Verify vertical bounds
    assert top_y <= 5.5
    assert bottom_y >= -2.4

    # Subtitles are placed at y = -3.45. Ensure safety buffer > 0.95 units
    safety_buffer = bottom_y - (-3.45)
    assert safety_buffer > 0.95, f"Collision detected! Buffer was {safety_buffer}"

    # Verify chassis contains 4 tracks
    assert len(comp.bars) == 4
    assert len(comp.bar_tips) == 4
    assert comp.hero_row is not None


def test_blueprint_radar_pareto_plot_layout():
    comp = BlueprintRadarParetoPlot(
        title="PARETO FRONTIER",
        sub="Multi-dimensional efficiency tradeoff across frontier architectures",
        axes=["Throughput", "VRAM Efficiency", "Accuracy", "Context Length", "Cost Efficiency"],
        models=[
            {"name": "Challenger (Ours)", "scores": [0.94, 0.90, 0.92, 0.88, 0.96], "is_hero": True, "color": "#10B981"},
            {"name": "Incumbent (Proprietary)", "scores": [0.62, 0.48, 0.95, 0.85, 0.22], "is_hero": False, "color": "#EF4444"}
        ],
        delta_badge="⚡ DOMINATES PARETO FRONTIER AT 18x LOWER COST"
    )

    top_y = comp.get_critical_point(UP)[1]
    bottom_y = comp.get_critical_point(DOWN)[1]

    # Verify vertical bounds
    assert top_y <= 5.5
    assert bottom_y >= -2.4

    safety_buffer = bottom_y - (-3.45)
    assert safety_buffer > 0.95, f"Collision detected! Buffer was {safety_buffer}"

    # Verify radar geometry: 5 axes, concentric rings, and 2 models
    assert comp.num_axes == 5
    assert len(comp.polygon_group) == 2
    assert comp.hero_polygon is not None


def test_visual_director_beat_5_showdown_assignment():
    vd = VisualDirector()
    spec = {
        "id": "deepseek_r1_benchmark",
        "title": "DeepSeek-R1 Shocks Frontier AI",
        "category": "benchmark_news",
        "beats": [
            {"beat_id": 1, "text": "The AI leaderboard just had its biggest upset.", "visual_focus": "Leaderboard upset"},
            {"beat_id": 2, "text": "Proprietary models held the monopoly.", "visual_focus": "Enterprise wall"},
            {"beat_id": 3, "text": "DeepSeek R1 introduces large-scale reinforcement learning.", "visual_focus": "RL mechanism"},
            {"beat_id": 4, "text": "Cold start reasoning chains self-evolve.", "visual_focus": "Chain evolution"},
            {"beat_id": 5, "text": "Empirical math benchmarks show parity at eighteen times lower cost.", "visual_focus": "AIME 2024 benchmark showdown"}
        ],
        "metadata": {
            "challenger": "DeepSeek-R1",
            "incumbent": "OpenAI o1"
        }
    }
    storyboard = vd.prepare_storyboard_for_spec(spec)
    b5 = next(b for b in storyboard["beats"] if b["beat_id"] == 5)
    assert b5["motif_type"] in ["horizontal_race_bars", "radar_pareto_plot"]
    assert "params" in b5["visual_blueprint"]
    assert "delta_badge" in b5["motif_params"]


# -----------------------------------------------------------------------------
# HEADLESS VISUAL VERIFICATION SCENES
# -----------------------------------------------------------------------------

class TestHorizontalRaceBarsScene(Scene):
    """Renders high-CTR Horizontal Benchmark Drag-Race Bars."""
    __test__ = False

    def construct(self):
        # 1. Chalkboard canvas
        dots = VGroup(*[
            Dot(point=[x, y, 0], radius=0.016, color="#2D3748", fill_opacity=0.35)
            for x in np.arange(-3.6, 3.7, 0.9) for y in np.arange(-6.0, 6.1, 0.9)
        ])
        self.add(dots)

        # 2. Brand Watermark at y = 7.1
        watermark = VGroup(
            CleanText("THE MODEL VERSE", font_size=11, color="#10B981", weight=BOLD),
            CleanText(" // ", font_size=11, color="#475569"),
            CleanText("BENCHMARK SHOWDOWN ENGINE", font_size=10, color="#94A3B8")
        ).arrange(RIGHT, buff=0.1).move_to([0, 7.1, 0])
        self.add(watermark)

        # 3. Horizontal Race Bars Composition
        comp = BlueprintHorizontalRaceBars(
            title="BENCHMARK SHOWDOWN: THROUGHPUT",
            sub="Hardware throughput scaling on NVIDIA H100 (FP16)",
            metric_name="Throughput",
            unit="TFLOPS",
            contestants=[
                {"name": "FlashAttention-3", "value": 1180.0, "display_val": "1,180 TFLOPS", "is_hero": True, "color": "#10B981"},
                {"name": "FlashAttention-2", "value": 660.0, "display_val": "660 TFLOPS", "is_hero": False, "color": "#38BDF8"},
                {"name": "cuDNN Flash", "value": 610.0, "display_val": "610 TFLOPS", "is_hero": False, "color": "#A855F7"},
                {"name": "Standard PyTorch", "value": 240.0, "display_val": "240 TFLOPS", "is_hero": False, "color": "#EF4444"}
            ],
            delta_badge="⚡ +78.8% SPEEDUP OVER FLASHATTENTION-2"
        )
        self.add(comp)

        # 4. Kinetic Subtitle Pill at y = -3.45 to verify clearance
        sub_txt = CleanText("FlashAttention-3 smashes the theoretical limit.", font_size=17, color=WHITE, weight=BOLD)
        sub_bg = RoundedRectangle(
            corner_radius=0.18,
            width=sub_txt.width + 0.6,
            height=0.72,
            fill_color="#080C14",
            fill_opacity=0.92,
            stroke_color="#334155",
            stroke_width=1.4
        )
        sub_pill = Group(sub_bg, sub_txt).move_to([0, -3.45, 0])
        self.add(sub_pill)


class TestRadarParetoPlotScene(Scene):
    """Renders Multi-Axis Radar / Spider Pareto Frontier Plot."""
    __test__ = False

    def construct(self):
        # 1. Chalkboard canvas
        dots = VGroup(*[
            Dot(point=[x, y, 0], radius=0.016, color="#2D3748", fill_opacity=0.35)
            for x in np.arange(-3.6, 3.7, 0.9) for y in np.arange(-6.0, 6.1, 0.9)
        ])
        self.add(dots)

        # 2. Brand Watermark at y = 7.1
        watermark = VGroup(
            CleanText("THE MODEL VERSE", font_size=11, color="#10B981", weight=BOLD),
            CleanText(" // ", font_size=11, color="#475569"),
            CleanText("PARETO RADAR ENGINE", font_size=10, color="#94A3B8")
        ).arrange(RIGHT, buff=0.1).move_to([0, 7.1, 0])
        self.add(watermark)

        # 3. Radar Pareto Plot Composition
        comp = BlueprintRadarParetoPlot(
            title="PARETO FRONTIER: EFFICIENCY VS QUALITY",
            sub="Multi-dimensional tradeoff across frontier reasoning architectures",
            axes=["Throughput", "VRAM Efficiency", "Math Accuracy", "Context Length", "Cost Efficiency"],
            models=[
                {
                    "name": "DeepSeek-R1 (Ours)",
                    "scores": [0.94, 0.90, 0.92, 0.88, 0.98],
                    "is_hero": True,
                    "color": "#10B981",
                    "fill_opacity": 0.35
                },
                {
                    "name": "OpenAI o1 (Proprietary)",
                    "scores": [0.62, 0.48, 0.95, 0.85, 0.22],
                    "is_hero": False,
                    "color": "#EF4444",
                    "fill_opacity": 0.18
                }
            ],
            delta_badge="⚡ DOMINATES PARETO FRONTIER AT 18x LOWER COST"
        )
        self.add(comp)

        # 4. Kinetic Subtitle Pill at y = -3.45 to verify clearance
        sub_txt = CleanText("Matching proprietary frontier math at a fraction of the cost.", font_size=17, color=WHITE, weight=BOLD)
        sub_bg = RoundedRectangle(
            corner_radius=0.18,
            width=sub_txt.width + 0.6,
            height=0.72,
            fill_color="#080C14",
            fill_opacity=0.92,
            stroke_color="#334155",
            stroke_width=1.4
        )
        sub_pill = Group(sub_bg, sub_txt).move_to([0, -3.45, 0])
        self.add(sub_pill)
