"""
The Model Verse — Chalkboard Code & AST Execution Visualizer
Renders syntax-highlighted code blocks with typewriter typing animations,
active execution line scanning, and live hardware register traces for 9:16 mobile shorts.
Strictly respects safe zones (zero collision with subtitles at y=-3.45).
"""

import sys
import re
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from manim import *
from manim.utils.rate_functions import ease_out_cubic, ease_out_back

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import FONT_HELVETICA
from manim_engine.primitives.typography import CleanText
from manim_engine.primitives.visual_compositions import BaseBlueprintComposition

# 3b1b Code Execution Palette
COLOR_CYAN = "#38BDF8"
COLOR_MINT = "#10B981"
COLOR_AMBER = "#F59E0B"
COLOR_CORAL = "#EF4444"
COLOR_PURPLE = "#C084FC"
COLOR_BLUE = "#60A5FA"
COLOR_SLATE = "#94A3B8"
COLOR_DARK_SLATE = "#1E293B"
COLOR_WHITE = "#F8FAFC"
COLOR_DIM = "#475569"

COLOR_KEYWORD = COLOR_PURPLE
COLOR_DEF = COLOR_BLUE
COLOR_STRING = COLOR_MINT
COLOR_COMMENT = COLOR_SLATE
COLOR_NUMBER = COLOR_AMBER

COMMON_KEYWORDS = {
    "def", "class", "for", "in", "if", "else", "elif", "return", "while",
    "yield", "import", "from", "as", "try", "except", "with", "lambda",
    "self", "torch", "const", "void", "float", "int", "__global__", "__restrict__",
    "struct", "typedef", "auto", "template", "typename", "inline"
}


def tokenize_syntax_line(line: str, language: str = "python") -> List[Tuple[str, str]]:
    """Parses a code line into syntax color tokens (Keywords, Functions, Strings, Numbers, Comments)."""
    tokens: List[Tuple[str, str]] = []
    idx = 0
    n = len(line)

    while idx < n:
        # Check comment
        if line[idx:idx+2] == "//" or line[idx] == "#":
            tokens.append((line[idx:], COLOR_COMMENT))
            break

        # Check string literal
        if line[idx] in ('"', "'"):
            quote = line[idx]
            end_q = line.find(quote, idx + 1)
            if end_q != -1:
                tokens.append((line[idx:end_q+1], COLOR_STRING))
                idx = end_q + 1
                continue
            else:
                tokens.append((line[idx:], COLOR_STRING))
                break

        # Check whitespace
        if line[idx].isspace():
            sp_match = re.match(r"\s+", line[idx:])
            if sp_match:
                tokens.append((sp_match.group(0), COLOR_WHITE))
                idx += len(sp_match.group(0))
                continue

        # Check word / identifier
        word_match = re.match(r"[A-Za-z_][A-Za-z0-9_]*", line[idx:])
        if word_match:
            word = word_match.group(0)
            if word in COMMON_KEYWORDS:
                tokens.append((word, COLOR_KEYWORD))
            elif idx + len(word) < n and line[idx+len(word):].lstrip().startswith("("):
                tokens.append((word, COLOR_DEF))
            else:
                tokens.append((word, COLOR_WHITE))
            idx += len(word)
            continue

        # Check number
        num_match = re.match(r"\b\d+(\.\d+)?\b", line[idx:])
        if num_match:
            num_str = num_match.group(0)
            tokens.append((num_str, COLOR_NUMBER))
            idx += len(num_str)
            continue

        # Operators / punctuation
        tokens.append((line[idx], "#94A3B8"))
        idx += 1

    return tokens


class BlueprintChalkboardCodeBlock(BaseBlueprintComposition):
    """
    Chalkboard Code Block with syntax-highlighted tokens, line numbering,
    active execution line sweeping, and live hardware memory register updates.
    """

    PYTHON_KEYWORDS = COMMON_KEYWORDS

    def __init__(
        self,
        title: str = "ALGORITHM IMPLEMENTATION",
        sub: str = "Core execution kernel running inside GPU memory",
        filename: str = "radix_cache.py",
        language: str = "python",
        lines: Optional[List[str]] = None,
        code_lines: Optional[List[str]] = None,
        highlight_lines: Optional[List[int]] = None,
        trace_register: str = "⚡ RADIX HIT: +2,048 TOKENS REUSED",
        delta_badge: str = "⚡ 5.2x INFERENCE THROUGHPUT MULTIPLIER",
        accent_color: str = COLOR_CYAN,
        **kwargs
    ):
        super().__init__(title=title, sub=sub, accent_color=accent_color, **kwargs)

        self.filename = filename
        self.language = language.upper()
        self.raw_lines = lines or code_lines or [
            "def match_prefix(self, prompt_tokens):",
            "    node = self.root",
            "    for token in prompt_tokens:",
            "        if token in node.children:",
            "            node = node.children[token]  # Hit",
            "    return node.kv_cache_pointer"
        ]
        self.raw_lines = self.raw_lines[:7]  # Limit to 7 lines for clean 9:16 layout
        self.highlight_lines = highlight_lines or [4, 5]
        self.trace_register = trace_register
        self.delta_str = delta_badge

        # 1. Blueprint Carbon Chassis Card
        self.chassis = RoundedRectangle(
            corner_radius=0.18,
            width=7.2,
            height=4.6,
            stroke_color="#1E293B",
            stroke_width=1.5,
            fill_color="#080C14",
            fill_opacity=0.75
        ).move_to([0, 0.85, 0])
        self.content_group.add(self.chassis)

        # 2. macOS Window Top Header Bar at y = 2.80
        dot_red = Dot(point=[-3.1, 2.80, 0], radius=0.055, color="#EF4444")
        dot_yellow = Dot(point=[-2.92, 2.80, 0], radius=0.055, color="#F59E0B")
        dot_green = Dot(point=[-2.74, 2.80, 0], radius=0.055, color="#10B981")
        window_dots = Group(dot_red, dot_yellow, dot_green)

        file_label = CleanText(f"📄 {self.filename[:24]}", font_size=11, color=COLOR_SLATE, weight=MEDIUM).move_to([-0.8, 2.80, 0])

        lang_col = COLOR_MINT if "CUDA" in self.language or "C" in self.language else COLOR_CYAN
        lang_bg_col = "#064E3B" if "CUDA" in self.language or "C" in self.language else "#082F49"
        lang_txt = CleanText(self.language[:8], font_size=9.5, color=lang_col, weight=BOLD)
        lang_pill = RoundedRectangle(
            corner_radius=0.08,
            width=lang_txt.width + 0.35,
            height=0.28,
            color=lang_col,
            stroke_width=1.0,
            fill_color=lang_bg_col,
            fill_opacity=0.6
        ).move_to([2.75, 2.80, 0])
        lang_txt.move_to(lang_pill)
        lang_badge = Group(lang_pill, lang_txt)

        divider_line = Line(start=[-3.3, 2.55, 0], end=[3.3, 2.55, 0], color="#1E293B", stroke_width=1.0)
        self.window_header = Group(window_dots, file_label, lang_badge, divider_line)
        self.content_group.add(self.window_header)

        # 3. Syntax-Highlighted Code Lines Container
        self.code_group = Group()
        self.line_mobjects = []
        self.active_line_highlights = Group()

        y_top = 2.20
        line_spacing = 0.42

        for idx, line_str in enumerate(self.raw_lines):
            line_num = idx + 1
            y_pos = y_top - idx * line_spacing

            # Line number
            num_txt = CleanText(f"{line_num:2d}", font_size=11.5, color=COLOR_DIM, weight=MEDIUM).move_to([-3.0, y_pos, 0])

            # Syntax tokenize line
            tokens = self._tokenize_line(line_str)
            token_group = Group()
            cur_x = -2.6

            for tok_text, tok_color in tokens:
                if not tok_text.strip():
                    cur_x += len(tok_text) * 0.08
                    continue
                t_mobj = CleanText(
                    tok_text,
                    font_size=12,
                    color=tok_color,
                    weight=BOLD if tok_color in [COLOR_PURPLE, COLOR_BLUE] else NORMAL
                )
                t_mobj.move_to([cur_x + t_mobj.width / 2.0, y_pos, 0])
                token_group.add(t_mobj)
                cur_x += t_mobj.width + 0.04

            if len(token_group) > 0 and token_group.width > 5.4:
                token_group.scale_to_fit_width(5.4)
                token_group.set_y(y_pos)
                token_group.set_x(-2.6 + token_group.width / 2.0)

            row_container = Group(num_txt, token_group)
            self.code_group.add(row_container)
            self.line_mobjects.append(row_container)

            # Check if this line is in highlight_lines
            if line_num in self.highlight_lines:
                hl_bar = RoundedRectangle(
                    corner_radius=0.06,
                    width=6.6,
                    height=0.34,
                    stroke_color="#38BDF8",
                    stroke_width=1.2,
                    fill_color="#0284C7",
                    fill_opacity=0.18
                ).move_to([0, y_pos, 0])
                # Left indicator notch aligned to bar's left edge
                notch = Rectangle(
                    width=0.08,
                    height=0.34,
                    color="#38BDF8",
                    fill_color="#38BDF8",
                    fill_opacity=1.0,
                    stroke_width=0
                ).move_to([hl_bar.get_left()[0] + 0.04, y_pos, 0])
                hl_group = Group(hl_bar, notch)
                self.active_line_highlights.add(hl_group)

        self.content_group.add(self.active_line_highlights, self.code_group)

        # 4. Live Memory / Hardware State Register at y = -1.15
        reg_txt = CleanText(self.trace_register[:44], font_size=10.5, color=COLOR_AMBER, weight=BOLD)
        reg_pill = RoundedRectangle(
            corner_radius=0.10,
            width=min(6.8, reg_txt.width + 0.6),
            height=0.36,
            color="#D97706",
            stroke_width=1.2,
            fill_color="#451A03",
            fill_opacity=0.75
        ).move_to([0, -1.15, 0])
        reg_txt.move_to(reg_pill)
        self.register_group = Group(reg_pill, reg_txt)
        self.content_group.add(self.register_group)

        # 5. Bottom Victory Delta Badge at y = -2.1
        badge_txt = CleanText(self.delta_str[:52], font_size=9.5, color="#10B981", weight=BOLD)
        badge_pill = RoundedRectangle(
            corner_radius=0.12,
            width=badge_txt.width + 0.5,
            height=0.34,
            color="#10B981",
            stroke_width=1.3,
            fill_color="#064E3B",
            fill_opacity=0.75
        )
        badge_txt.move_to(badge_pill)
        self.badge = Group(badge_pill, badge_txt).move_to([0, -2.1, 0])
        self.content_group.add(self.badge)

        # Aliases for convenience
        self.header = self.window_header
        self.register_badge = self.register_group
        self.delta_badge = self.badge

        self.kinetic_elements.add(self.active_line_highlights, self.register_group, self.badge)
        self.add(self.title, self.sub, self.content_group)

    def _tokenize_line(self, line: str) -> List[Tuple[str, str]]:
        """Parses a code line into syntax color tokens (Keywords, Functions, Strings, Numbers, Comments)."""
        tokens: List[Tuple[str, str]] = []
        idx = 0
        n = len(line)

        while idx < n:
            # Check comment
            if line[idx:idx+2] == "//" or line[idx] == "#":
                tokens.append((line[idx:], COLOR_SLATE))
                break

            # Check string literal
            if line[idx] in ('"', "'"):
                quote = line[idx]
                end_q = line.find(quote, idx + 1)
                if end_q != -1:
                    tokens.append((line[idx:end_q+1], COLOR_MINT))
                    idx = end_q + 1
                    continue
                else:
                    tokens.append((line[idx:], COLOR_MINT))
                    break

            # Check whitespace
            if line[idx].isspace():
                sp_match = re.match(r"\s+", line[idx:])
                if sp_match:
                    tokens.append((sp_match.group(0), COLOR_WHITE))
                    idx += len(sp_match.group(0))
                    continue

            # Check word / identifier
            word_match = re.match(r"[A-Za-z_][A-Za-z0-9_]*", line[idx:])
            if word_match:
                word = word_match.group(0)
                # Check if keyword
                if word in self.PYTHON_KEYWORDS:
                    tokens.append((word, COLOR_PURPLE))
                # Check if function call (next non-space char is '(')
                elif idx + len(word) < n and line[idx+len(word):].lstrip().startswith("("):
                    tokens.append((word, COLOR_BLUE))
                else:
                    tokens.append((word, COLOR_WHITE))
                idx += len(word)
                continue

            # Check number
            num_match = re.match(r"\b\d+(\.\d+)?\b", line[idx:])
            if num_match:
                num_str = num_match.group(0)
                tokens.append((num_str, COLOR_AMBER))
                idx += len(num_str)
                continue

            # Operators / punctuation
            tokens.append((line[idx], "#94A3B8"))
            idx += 1

        return tokens

    def get_entrance_animation(self, run_time: float = 1.0) -> Animation:
        """Typewriter progressive entrance: Chassis appears, code lines reveal with typewriter pacing."""
        anims = [
            FadeIn(self.title, shift=DOWN * 0.15),
            FadeIn(self.sub, shift=DOWN * 0.15),
            FadeIn(self.chassis, scale=0.98),
            FadeIn(self.window_header, shift=DOWN * 0.1)
        ]
        # Progressive line reveals
        for line_mob in self.line_mobjects:
            anims.append(GrowFromEdge(line_mob, LEFT, rate_func=ease_out_cubic))
        if self.active_line_highlights:
            anims.append(FadeIn(self.active_line_highlights, scale=0.95))
        anims.append(FadeIn(self.register_group, shift=UP * 0.15))
        anims.append(FadeIn(self.badge, shift=UP * 0.15, rate_func=ease_out_back))
        return AnimationGroup(*anims, run_time=run_time)

    def get_kinetic_animation(self, run_time: float = 1.8) -> Animation:
        """Focal kinetic action: Active execution line pulses and register updates."""
        anims = []
        if self.active_line_highlights:
            anims.append(Indicate(self.active_line_highlights, color=COLOR_CYAN, scale_factor=1.02))
        anims.append(Indicate(self.register_group, color=COLOR_GOLD, scale_factor=1.04))
        anims.append(self.badge.animate.scale(1.04).set_color(COLOR_GOLD))
        return AnimationGroup(*anims, run_time=run_time)
