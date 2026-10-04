"""
The Model Verse — High-Precision Typographic Primitives
Eliminates Pango Cairo integer grid-snapping gaps and letter spacing distortions on macOS and Linux.
"""

from manim import *
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import FONT_HELVETICA


from typing import Optional

class CleanText(Text):
    """
    Drop-in replacement for Manim's Text that fixes Pango Cairo integer grid-snapping gaps.
    
    When font_size < 36, Pango Cairo on macOS rounds glyph advance widths to 1-pixel integers,
    causing unnatural letter spacing gaps (e.g. 'THE MO DEL', 'Effici ency', 'CAUSAL EL IMINATION').
    CleanText creates the text at a high-precision base size (36) and applies floating-point
    vector scaling, ensuring crisp, proportional typographic kerning at any display scale.
    Also supports auto-fitting via max_width and max_height to guarantee zero container overflow.
    """
    def __init__(
        self,
        text: str,
        font: str = FONT_HELVETICA,
        font_size: float = 14,
        base_size: float = 36.0,
        max_width: Optional[float] = None,
        max_height: Optional[float] = None,
        **kwargs
    ):
        target_size = font_size
        effective_base = max(base_size, float(target_size))
        scale_factor = float(target_size) / effective_base
        super().__init__(text, font=font, font_size=effective_base, **kwargs)
        if scale_factor != 1.0:
            self.scale(scale_factor)
        if max_width is not None and self.width > max_width:
            self.scale_to_fit_width(max_width)
        if max_height is not None and self.height > max_height:
            self.scale_to_fit_height(max_height)


def fit_text_to_container(text_mobj: Mobject, container: Mobject, padding: float = 0.2) -> Mobject:
    """Scale and center text inside a container box/card/ellipse if it overflows."""
    avail_w = max(0.1, container.width - 2 * padding)
    avail_h = max(0.1, container.height - 2 * padding)
    if text_mobj.width > avail_w:
        text_mobj.scale_to_fit_width(avail_w)
    if text_mobj.height > avail_h:
        text_mobj.scale_to_fit_height(avail_h)
    text_mobj.move_to(container.get_center())
    return text_mobj
