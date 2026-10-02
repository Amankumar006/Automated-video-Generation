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


class CleanText(Text):
    """
    Drop-in replacement for Manim's Text that fixes Pango Cairo integer grid-snapping gaps.
    
    When font_size < 36, Pango Cairo on macOS rounds glyph advance widths to 1-pixel integers,
    causing unnatural letter spacing gaps (e.g. 'THE MO DEL', 'Effici ency', 'CAUSAL EL IMINATION').
    CleanText creates the text at a high-precision base size (36) and applies floating-point
    vector scaling, ensuring crisp, proportional typographic kerning at any display scale.
    """
    def __init__(
        self,
        text: str,
        font: str = FONT_HELVETICA,
        font_size: float = 14,
        base_size: float = 36.0,
        **kwargs
    ):
        target_size = font_size
        effective_base = max(base_size, float(target_size))
        scale_factor = float(target_size) / effective_base
        super().__init__(text, font=font, font_size=effective_base, **kwargs)
        if scale_factor != 1.0:
            self.scale(scale_factor)
