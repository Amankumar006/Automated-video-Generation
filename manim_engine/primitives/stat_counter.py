"""
Visual Primitives: Dynamic Live Numerical Counter & Metric Gauge
"""

from manim import *
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from pipeline.config import FONT_HELVETICA, COLOR_MINT, COLOR_SLATE

def create_dynamic_counter(
    tracker: ValueTracker,
    unit: str = "B",
    label: str = "TOTAL PARAMETERS",
    font_size: int = 126,
    number_color: str = COLOR_MINT,
    label_color: str = COLOR_SLATE,
    position: np.ndarray = UP * 2.0
) -> tuple[always_redraw, Text]:
    """Returns a dynamic counter mobject and its sublabel."""
    num_mobject = always_redraw(
        lambda: Text(
            f"{int(tracker.get_value())}{unit}",
            font=FONT_HELVETICA,
            font_size=font_size,
            color=number_color,
            weight=HEAVY
        ).move_to(position)
    )
    sublabel = Text(
        label,
        font=FONT_HELVETICA,
        font_size=24,
        color=label_color,
        weight=BOLD
    ).next_to(num_mobject, DOWN, buff=0.35)
    return num_mobject, sublabel

def create_animated_gauge(
    tracker: ValueTracker,
    width: float = 7.4,
    height: float = 0.45,
    max_value: float = 7.4,
    position: np.ndarray = DOWN * 1.5,
    fill_color: str = COLOR_MINT
) -> tuple[RoundedRectangle, always_redraw, Text]:
    """Creates a dynamically filling or shrinking progress/load bar."""
    bg_bar = RoundedRectangle(
        corner_radius=0.12,
        width=width,
        height=height,
        color="#1F2937",
        fill_color="#111827",
        fill_opacity=0.9,
        stroke_width=1.5
    ).move_to(position)

    fill_bar = always_redraw(
        lambda: RoundedRectangle(
            corner_radius=0.12,
            width=max(0.4, tracker.get_value()),
            height=height * 0.9,
            color=fill_color,
            fill_color=fill_color,
            fill_opacity=0.85,
            stroke_width=0
        ).align_to(bg_bar, LEFT)
    )

    label = Text(
        "ACTIVE COMPUTE RETENTION: 5.5%",
        font=FONT_HELVETICA,
        font_size=15,
        color="#A7F3D0",
        weight=BOLD
    ).move_to(bg_bar)

    return bg_bar, fill_bar, label
