"""Reusable broadcast identity graphics for every Model Verse short.

The mechanism visual remains the hero.  This layer supplies the repeatable
brand grammar around it: a topic-seeded accent treatment, quiet technical
rails, a beat index, and a small deterministic signal motif.  It is designed
to make the channel feel authored without forcing every topic into the same
diagram template.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np
from manim import (
    Animation,
    AnimationGroup,
    Arc,
    DashedLine,
    Dot,
    FadeIn,
    Line,
    RIGHT,
    UP,
    VGroup,
    VMobject,
    there_and_back,
)

from pipeline.config import FONT_HELVETICA
from manim_engine.primitives.typography import CleanText, word_safe_truncate


@dataclass(frozen=True)
class GraphicIdentityTheme:
    """Stable visual treatment selected from the video identity input."""

    name: str
    accent: str
    secondary: str
    dim: str
    motif: str
    seed: str


_THEMES: tuple[GraphicIdentityTheme, ...] = (
    GraphicIdentityTheme("CYAN SIGNAL", "#00F0FF", "#34D399", "#164E63", "signal", ""),
    GraphicIdentityTheme("VIOLET ORBIT", "#A855F7", "#38BDF8", "#4C1D95", "orbit", ""),
    GraphicIdentityTheme("AMBER TRACE", "#F59E0B", "#FDE68A", "#78350F", "trace", ""),
    GraphicIdentityTheme("MINT CONSTELLATION", "#10B981", "#A7F3D0", "#064E3B", "constellation", ""),
    GraphicIdentityTheme("CORAL MATRIX", "#FB7185", "#F59E0B", "#881337", "matrix", ""),
)


def _identity_key(spec: Optional[Dict[str, Any]]) -> str:
    spec = spec or {}
    title = " ".join(str(spec.get("title") or spec.get("id") or "AI").split()).lower()
    category = str(spec.get("category") or "academic_breakdown").strip().lower()
    domain = str(spec.get("domain_taxonomy") or "frontier_ai").strip().lower()
    return f"{title}|{category}|{domain}"


def theme_for_spec(spec: Optional[Dict[str, Any]]) -> GraphicIdentityTheme:
    """Return the same theme for the same topic, across machines and runs."""
    digest = hashlib.sha256(_identity_key(spec).encode("utf-8")).hexdigest()
    base = _THEMES[int(digest[:8], 16) % len(_THEMES)]
    return GraphicIdentityTheme(
        name=base.name,
        accent=base.accent,
        secondary=base.secondary,
        dim=base.dim,
        motif=base.motif,
        seed=digest[:10],
    )


def _slug(value: str, limit: int = 20) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", " ", str(value or "")).strip().upper()
    return word_safe_truncate(value, limit) if value else "FRONTIER AI"


def _trace_points(theme: GraphicIdentityTheme) -> np.ndarray:
    """Build a small deterministic trace used as a visual signature."""
    seed_value = int(theme.seed[:6], 16)
    phase = (seed_value % 31) / 31.0
    amplitude = 0.07 + ((seed_value >> 4) % 7) * 0.012
    points = []
    for idx in range(25):
        x = -1.0 + idx * (2.0 / 24.0)
        y = 5.88 + amplitude * np.sin((idx / 24.0) * 4.0 * np.pi + phase)
        points.append([x, y, 0])
    return np.array(points)


class GraphicIdentityOverlay(VGroup):
    """A persistent, low-contrast broadcast frame for the hero visual."""

    def __init__(
        self,
        spec: Optional[Dict[str, Any]] = None,
        total_beats: int = 6,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.spec = spec or {}
        self.theme = theme_for_spec(self.spec)
        self.total_beats = max(1, int(total_beats or 1))
        self.current_beat = 0
        self.current_beat_label = f"BEAT 00/{self.total_beats:02d}"
        self._build()

    def _build(self) -> None:
        theme = self.theme

        # The frame lives around the hero zone, leaving the existing title,
        # formula tray, and subtitles clear.  It is deliberately not a card.
        frame = VGroup()
        x_left, x_right = -3.78, 3.78
        y_bottom, y_top = -2.20, 4.92
        corner = 0.22
        for x, horizontal in ((x_left, RIGHT), (x_right, -RIGHT)):
            for y, vertical in ((y_top, -UP), (y_bottom, UP)):
                frame.add(
                    Line([x, y, 0], [x + horizontal[0] * corner, y, 0], color=theme.accent, stroke_width=1.2, stroke_opacity=0.23),
                    Line([x, y, 0], [x, y + vertical[1] * corner, 0], color=theme.accent, stroke_width=1.2, stroke_opacity=0.23),
                )
        self.hero_frame = frame

        rails = VGroup(
            Line([x_left, y_bottom, 0], [x_left, y_top, 0], color=theme.secondary, stroke_width=0.7, stroke_opacity=0.15),
            Line([x_right, y_bottom, 0], [x_right, y_top, 0], color=theme.secondary, stroke_width=0.7, stroke_opacity=0.15),
            DashedLine([-3.78, 5.72, 0], [3.78, 5.72, 0], dash_length=0.08, color=theme.secondary, stroke_width=0.7, stroke_opacity=0.22),
        )
        self.rails = rails

        category = _slug(self.spec.get("category", "academic_breakdown"), 18)
        self.channel_label = CleanText(
            f"SIGNAL / {category}",
            font=FONT_HELVETICA,
            font_size=8.5,
            color=theme.secondary,
            weight="BOLD",
            max_width=2.25,
        ).move_to([-2.65, 5.88, 0])
        self.seed_label = CleanText(
            f"ID {theme.seed[:6].upper()} // {theme.name}",
            font=FONT_HELVETICA,
            font_size=7.5,
            color="#64748B",
            weight="BOLD",
            max_width=2.5,
        ).move_to([2.55, 5.88, 0])

        trace = VMobject()
        trace.set_points_as_corners(_trace_points(theme))
        trace.set_stroke(color=theme.accent, width=2.0, opacity=0.52)
        self.signal_trace = trace
        self.signal_dot = Dot(point=[1.02, 5.88, 0], radius=0.045, color=theme.accent, fill_opacity=0.9)

        # A tiny mark changes by topic family while staying visually quiet.
        self.signature = self._build_signature()

        self.beat_readout = CleanText(
            f"BEAT 00/{self.total_beats:02d}",
            font=FONT_HELVETICA,
            font_size=8.5,
            color=theme.accent,
            weight="BOLD",
            max_width=1.15,
        ).move_to([3.28, 4.55, 0])
        self.focus_readout = CleanText(
            "READY",
            font=FONT_HELVETICA,
            font_size=7.5,
            color="#64748B",
            weight="BOLD",
            max_width=1.2,
        ).move_to([3.20, 4.28, 0])

        ticks = []
        for idx in range(self.total_beats):
            tick = Line(
                [3.78, 4.15 - idx * 0.18, 0],
                [3.61, 4.15 - idx * 0.18, 0],
                color="#334155",
                stroke_width=1.3,
                stroke_opacity=0.75,
            )
            ticks.append(tick)
        self.progress_ticks = ticks
        progress = VGroup(*ticks)

        self.add(
            self.hero_frame,
            self.rails,
            self.channel_label,
            self.seed_label,
            self.signal_trace,
            self.signal_dot,
            self.signature,
            self.beat_readout,
            self.focus_readout,
            progress,
        )
        self.set_z_index(2)
        self.set_opacity(0.0)

    def _build_signature(self) -> VGroup:
        theme = self.theme
        if theme.motif == "orbit":
            ring = Arc(radius=0.22, start_angle=0.3, angle=5.2, color=theme.secondary, stroke_width=1.5, stroke_opacity=0.55).move_to([3.42, 5.06, 0])
            dot = Dot(point=[3.58, 5.15, 0], radius=0.035, color=theme.accent)
            return VGroup(ring, dot)
        if theme.motif == "constellation":
            pts = [np.array([3.25, 5.08, 0]), np.array([3.50, 5.22, 0]), np.array([3.68, 4.98, 0])]
            links = VGroup(*[Line(pts[i], pts[(i + 1) % 3], color=theme.secondary, stroke_width=1.1, stroke_opacity=0.45) for i in range(3)])
            nodes = VGroup(*[Dot(point=p, radius=0.035, color=theme.accent) for p in pts])
            return VGroup(links, nodes)
        if theme.motif == "matrix":
            cells = []
            for row in range(3):
                for col in range(3):
                    cells.append(
                        Line(
                            [3.22 + col * 0.12, 4.96 + row * 0.12, 0],
                            [3.30 + col * 0.12, 4.96 + row * 0.12, 0],
                            color=theme.accent if (row + col) % 2 == 0 else theme.secondary,
                            stroke_width=2.0,
                            stroke_opacity=0.7,
                        )
                    )
            return VGroup(*cells)
        # Signal and trace treatments use a compact waveform mark.
        return VGroup(
            Line([3.18, 5.02, 0], [3.30, 5.18, 0], color=theme.accent, stroke_width=1.8, stroke_opacity=0.65),
            Line([3.30, 5.18, 0], [3.44, 4.98, 0], color=theme.secondary, stroke_width=1.8, stroke_opacity=0.65),
            Line([3.44, 4.98, 0], [3.62, 5.16, 0], color=theme.accent, stroke_width=1.8, stroke_opacity=0.65),
        )

    def update_beat(self, beat_id: int, focus: str = "MECHANISM") -> None:
        """Update the small readouts without changing the hero composition."""
        self.current_beat = max(0, int(beat_id or 0))
        self.current_beat_label = f"BEAT {self.current_beat:02d}/{self.total_beats:02d}"
        self.beat_readout.become(
            CleanText(
                self.current_beat_label,
                font=FONT_HELVETICA,
                font_size=8.5,
                color=self.theme.accent,
                weight="BOLD",
                max_width=1.15,
            ).move_to(self.beat_readout.get_center())
        )
        self.focus_readout.become(
            CleanText(
                _slug(focus, 13),
                font=FONT_HELVETICA,
                font_size=7.5,
                color="#94A3B8",
                weight="BOLD",
                max_width=1.2,
            ).move_to(self.focus_readout.get_center())
        )
        for idx, tick in enumerate(self.progress_ticks, start=1):
            tick.set_stroke(
                color=self.theme.accent if idx <= self.current_beat else "#334155",
                width=2.4 if idx == self.current_beat else 1.3,
                opacity=0.95 if idx <= self.current_beat else 0.75,
            )

    def get_entrance_animation(self, run_time: float = 0.65) -> Animation:
        """Reveal the identity as a quiet signal lock, not a title card."""
        return AnimationGroup(
            FadeIn(self, shift=RIGHT * 0.04, run_time=run_time),
            lag_ratio=0.0,
            run_time=run_time,
        )

    def get_beat_animation(self, run_time: float = 0.45) -> Animation:
        """Provide a small topic-specific signal response at beat changes."""
        return AnimationGroup(
            self.signal_dot.animate(rate_func=there_and_back, run_time=run_time).scale(1.55),
            self.signal_trace.animate(rate_func=there_and_back, run_time=run_time).set_stroke(width=3.0, opacity=0.9),
            self.signature.animate(rate_func=there_and_back, run_time=run_time).scale(1.12),
            lag_ratio=0.0,
            run_time=run_time,
        )

    def get_ambient_animation(self, run_time: float = 3.0) -> Animation:
        """Keep the frame alive with bounded, drift-free micro-motion."""
        return AnimationGroup(
            self.signal_dot.animate(rate_func=there_and_back, run_time=run_time).scale(1.18),
            self.signal_trace.animate(rate_func=there_and_back, run_time=run_time).set_stroke(opacity=0.68),
            lag_ratio=0.0,
            run_time=run_time,
        )


def create_graphic_identity_overlay(spec: Optional[Dict[str, Any]], total_beats: int = 6) -> GraphicIdentityOverlay:
    """Factory used by the scene so the identity remains easy to test and replace."""
    return GraphicIdentityOverlay(spec=spec, total_beats=total_beats)


__all__ = [
    "GraphicIdentityTheme",
    "GraphicIdentityOverlay",
    "theme_for_spec",
    "create_graphic_identity_overlay",
]
