"""
The Model Verse — High-Precision Typographic Primitives
Eliminates Pango Cairo integer grid-snapping gaps and letter spacing distortions on macOS and Linux.
"""

from manim import *
import sys
import textwrap
from typing import Optional
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import FONT_HELVETICA


def word_safe_truncate(text: str, max_chars: int) -> str:
    """Shorten labels without cutting a word in half."""
    value = " ".join(str(text or "").split())
    if len(value) <= max_chars:
        return value
    clipped = value[: max_chars + 1].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return (clipped or value[:max_chars].rstrip()) + "…"


class CleanText(Text):
    """
    Drop-in replacement for Manim's Text that fixes Pango Cairo integer grid-snapping gaps.
    
    When font_size < 36, Pango Cairo on macOS rounds glyph advance widths to coarse integer coordinates,
    causing unnatural letter spacing gaps (e.g. 'THE MO DEL', 'Effici ency', '1. E ar ly-S tage').
    CleanText creates the text at a high-precision base size (36) and applies floating-point
    vector scaling, ensuring crisp, proportional typographic kerning at any display scale.
    Also supports auto-fitting via max_width, max_height, and line-wrapping via wrap_width.
    """
    def __init__(
        self,
        text: str,
        font: str = FONT_HELVETICA,
        font_size: float = 14,
        base_size: float = 36.0,
        max_width: Optional[float] = None,
        max_height: Optional[float] = None,
        wrap_width: Optional[int] = None,
        **kwargs
    ):
        raw_text = str(text)
        if wrap_width is not None and wrap_width > 0:
            lines = raw_text.split("\n")
            processed_text = "\n".join(textwrap.fill(line, width=wrap_width) for line in lines)
        else:
            processed_text = raw_text

        target_size = font_size
        effective_base = max(base_size, float(target_size))
        scale_factor = float(target_size) / effective_base
        super().__init__(processed_text, font=font, font_size=effective_base, **kwargs)
        if scale_factor != 1.0:
            self.scale(scale_factor)
        if max_width is not None and self.width > max_width and self.width > 0:
            self.scale_to_fit_width(max_width)
        if max_height is not None and self.height > max_height and self.height > 0:
            self.scale_to_fit_height(max_height)


def clean_text(
    text: str,
    font: str = FONT_HELVETICA,
    font_size: float = 14,
    base_size: float = 36.0,
    max_width: Optional[float] = None,
    max_height: Optional[float] = None,
    wrap_width: Optional[int] = None,
    **kwargs
) -> CleanText:
    """
    Centralized typography primitive helper.
    Guarantees 36pt base rendering with subpixel float scaling, auto-wrapping,
    and safe width constraints to eliminate Pango/Cairo kerning artifacts.
    """
    return CleanText(
        text=text,
        font=font,
        font_size=font_size,
        base_size=base_size,
        max_width=max_width,
        max_height=max_height,
        wrap_width=wrap_width,
        **kwargs
    )


def fit_text_to_container(text_mobj: Mobject, container: Mobject, padding: float = 0.25) -> Mobject:
    """Scale and center text inside a container box/card/ellipse if it overflows."""
    avail_w = max(0.1, container.width - 2 * padding)
    avail_h = max(0.1, container.height - 2 * padding)
    if text_mobj.width > avail_w and text_mobj.width > 0:
        text_mobj.scale_to_fit_width(avail_w)
    if text_mobj.height > avail_h and text_mobj.height > 0:
        text_mobj.scale_to_fit_height(avail_h)
    text_mobj.move_to(container.get_center())
    return text_mobj


__all__ = ["CleanText", "clean_text", "fit_text_to_container", "word_safe_truncate"]
