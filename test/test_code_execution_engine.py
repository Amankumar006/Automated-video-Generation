"""
Test suite for Chalkboard Code & AST Execution Trace Engine.
Verifies:
1. Python and CUDA / C++ syntax tokenization and color mapping.
2. BlueprintChalkboardCodeBlock layout constraints, chassis dimensions, and macOS header.
3. Line truncation and scaling for 9:16 vertical mobile screens.
4. Safe zone clearance relative to kinetic subtitles (y = -3.45) and brand watermark (y = 7.1).
5. Registry resolution in visual_compositions and VisualDirector blueprint synthesis.
6. Headless Manim scene for visual inspection.
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
from manim_engine.primitives.code_execution_engine import (
    BlueprintChalkboardCodeBlock,
    tokenize_syntax_line,
    COLOR_KEYWORD,
    COLOR_DEF,
    COLOR_STRING,
    COLOR_COMMENT,
    COLOR_NUMBER
)
from manim_engine.primitives.visual_compositions import create_blueprint_composition
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

def test_tokenize_syntax_line_python():
    tokens = tokenize_syntax_line("def match_prefix(self, prompt_tokens):", "python")
    assert len(tokens) > 0
    # First token should be def with COLOR_KEYWORD
    assert tokens[0][0] == "def"
    assert tokens[0][1] == COLOR_KEYWORD
    # Function name token
    func_tokens = [t for t in tokens if "match_prefix" in t[0]]
    assert len(func_tokens) > 0
    assert func_tokens[0][1] == COLOR_DEF


def test_tokenize_syntax_line_cuda():
    tokens = tokenize_syntax_line("__global__ void paged_attention_kernel(float* out) {", "cuda")
    assert len(tokens) > 0
    keywords = [t[0] for t in tokens if t[1] == COLOR_KEYWORD]
    assert "__global__" in keywords or "void" in keywords


def test_chalkboard_code_block_structure():
    code_lines = [
        "def match_prefix(self, prompt_tokens):",
        "    node = self.root",
        "    for token in prompt_tokens:",
        "        if token in node.children:",
        "            node = node.children[token]  # Hit",
        "    return node.kv_cache_pointer"
    ]
    block = BlueprintChalkboardCodeBlock(
        filename="radix_cache.py",
        language="python",
        code_lines=code_lines,
        highlight_lines=[4, 5],
        trace_register="⚡ RADIX HIT: +2,048 TOKENS REUSED",
        delta_badge="⚡ 5.4x PREFIX CACHING SPEEDUP"
    )

    assert hasattr(block, "chassis")
    assert hasattr(block, "header")
    assert hasattr(block, "code_group")
    assert hasattr(block, "register_badge")
    assert hasattr(block, "delta_badge")
    assert len(block.code_group) == 6


def test_chalkboard_code_block_916_safe_zones():
    code_lines = [
        "__global__ void paged_attention_kernel(",
        "    const float* __restrict__ Q,",
        "    const int* __restrict__ block_tables,",
        "    float* __restrict__ out) {",
        "  int block_idx = block_tables[seq_id];",
        "  fetch_kv_block(block_idx, shared_kv);",
        "}"
    ]
    block = BlueprintChalkboardCodeBlock(
        filename="paged_attention.cu",
        language="cuda",
        code_lines=code_lines,
        highlight_lines=[5, 6],
        trace_register="⚡ ZERO VRAM FRAGMENTATION (O(1))",
        delta_badge="⚡ +4.8x THROUGHPUT WITH PAGED KV"
    )

    # Chassis dimensions must be contained within safe vertical canvas
    chassis = block.chassis
    assert chassis.width <= 7.4, f"Chassis width {chassis.width} exceeds 7.4 max safe width"
    assert chassis.height <= 4.8, f"Chassis height {chassis.height} exceeds 4.8 max safe height"

    top_y = block.get_critical_point(UP)[1]
    bottom_y = block.get_critical_point(DOWN)[1]

    # Verify vertical bounds for 9:16 mobile canvas
    assert top_y <= 5.5, f"Top y={top_y:.2f} exceeds 5.5 safe ceiling"
    assert bottom_y >= -2.4, f"Bottom y={bottom_y:.2f} breaches -2.4 bottom margin"

    # Subtitles are placed at y = -3.45. Ensure safety buffer > 0.95 units
    safety_buffer = bottom_y - (-3.45)
    assert safety_buffer > 0.95, f"Collision detected! Buffer was {safety_buffer}"


def test_visual_composition_registration():
    comp = create_blueprint_composition(
        "chalkboard_code_block",
        params={
            "filename": "ternary_gemm.py",
            "language": "python",
            "lines": ["def bit_linear(x, w):", "    return sign(w) * x"],
            "highlight_lines": [2],
            "trace_register": "⚡ 1-BIT TERNARY WEIGHTS",
            "delta_badge": "⚡ NATIVE ADDITION WITHOUT MULTIPLY"
        }
    )
    assert isinstance(comp, BlueprintChalkboardCodeBlock)


def test_visual_director_code_routing():
    director = VisualDirector()
    spec = {
        "id": "vllm_paged_attention",
        "title": "vLLM PagedAttention GPU Serving",
        "category": "mechanism_deepdive",
        "beats": [
            {"beat_id": 1, "text": "Serving LLMs wastes half your VRAM in fragmented memory."},
            {"beat_id": 2, "text": "Traditional attention requires continuous memory buffers."},
            {"beat_id": 3, "text": "PagedAttention treats GPU memory like virtual memory pages."},
            {"beat_id": 4, "text": "Each block indexes KV cache on the fly without waste."},
            {"beat_id": 5, "text": "This delivers four times higher serving throughput."},
            {"beat_id": 6, "text": "Follow The Model Verse for clear visual breakdowns."}
        ],
        "code_snippet": {
            "filename": "paged_attention.cu",
            "language": "cuda",
            "lines": [
                "__global__ void paged_attention(",
                "    const int* block_tables) {",
                "  int b = block_tables[seq_id];",
                "}"
            ],
            "highlight_lines": [3],
            "trace_register": "⚡ O(1) VRAM INDEX",
            "explanation": "Virtual memory paging for transformers"
        }
    }

    # prepare_storyboard_for_spec should route Beat 3 or 4 to chalkboard_code_block
    storyboard = director.prepare_storyboard_for_spec(spec)
    code_beats = [
        b for b in storyboard["beats"]
        if b.get("motif_type") == "chalkboard_code_block"
        or (b.get("visual_blueprint") and b["visual_blueprint"].get("layout") == "chalkboard_code_block")
    ]
    assert len(code_beats) > 0
    assert code_beats[0]["visual_blueprint"]["layout"] == "chalkboard_code_block"
    assert code_beats[0]["visual_blueprint"]["params"]["filename"] == "paged_attention.cu"


# -----------------------------------------------------------------------------
# HEADLESS MANIM RENDER SCENE
# -----------------------------------------------------------------------------

class TestChalkboardCodeBlockScene(Scene):
    """Renders a Chalkboard Code Block with AST execution trace in 9:16 vertical mobile format."""
    __test__ = False

    def construct(self):
        # 1. Chalkboard canvas dot grid
        dots = VGroup(*[
            Dot(point=[x, y, 0], radius=0.016, color="#2D3748", fill_opacity=0.35)
            for x in np.arange(-3.6, 3.7, 0.9) for y in np.arange(-6.0, 6.1, 0.9)
        ])
        self.add(dots)

        # 2. Brand Watermark at y = 7.1
        watermark = VGroup(
            CleanText("THE MODEL VERSE", font_size=11, color="#10B981", weight=BOLD),
            CleanText(" // ", font_size=11, color="#475569"),
            CleanText("KERNEL EXECUTION TRACE", font_size=10, color="#94A3B8")
        ).arrange(RIGHT, buff=0.1).move_to([0, 7.1, 0])
        self.add(watermark)

        # 3. Chalkboard Code Block Composition (integrated title and subtitle)
        code_lines = [
            "def match_prefix(self, prompt_tokens):",
            "    node = self.root",
            "    for token in prompt_tokens:",
            "        if token in node.children:",
            "            node = node.children[token]  # Hit",
            "    return node.kv_cache_pointer"
        ]
        comp = BlueprintChalkboardCodeBlock(
            title="RADIX CACHING IN SGLANG",
            sub="Prefix tree KV-cache reuse eliminates redundant token computation",
            filename="radix_cache.py",
            language="python",
            code_lines=code_lines,
            highlight_lines=[4, 5],
            trace_register="⚡ RADIX HIT: +2,048 TOKENS REUSED",
            delta_badge="⚡ 5.4x REUSE LATENCY GAIN"
        )
        self.add(comp)

        # 5. Kinetic Subtitle Pill at y = -3.45 to verify clearance
        sub_txt = CleanText("Reusing cached KV tokens across branching requests.", font_size=17, color=WHITE, weight=BOLD)
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
