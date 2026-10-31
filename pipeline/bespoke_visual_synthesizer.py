"""
The Model Verse — Autonomous Bespoke Visual Synthesizer (Visual Engine 6.0)
Generates 100% bespoke, script-tailored Manim animation code on the fly for each beat:
- Synthesizes unique vector geometry reflecting the paper's actual mechanism
- Strictly avoids monolithic SaaS card chassis, rounded rectangles, and generic templates
- Enforces 3Blue1Brown aesthetics on #0A0D14 carbon background
- Validates code via AST sandbox & headless dry-run with 1-shot self-healing
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=FutureWarning)
    try:
        import google.generativeai as genai
    except ImportError:
        genai = None

from pipeline.config import GEMINI_MODEL_NAME
from pipeline.code_sandbox import validate_synthesized_visual_code, validate_visual_quality_contract
from pipeline.llm_router import llm_router, generate_text_with_cascade
from pipeline.mechanism_visual_library import mechanism_prompt_block, validate_mechanism_semantics
from pipeline.quota_tracker import quota_tracker

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if API_KEY and genai:
    try:
        genai.configure(api_key=API_KEY)
    except Exception:
        pass

GENERATED_VISUALS_DIR = PROJECT_ROOT / "manim_engine" / "generated"
GENERATED_VISUALS_DIR.mkdir(parents=True, exist_ok=True)


def _mechanism_fallback_body(family: str, accent: str) -> Optional[str]:
    """Return a domain-specific causal drawing for the deterministic fallback."""
    bodies = {
        "diffusion_flow": f"""
        self.field = VGroup(*[Arc(radius=1.05 + i * 0.42, start_angle=-1.25, angle=2.45, color={accent!r}, stroke_width=2.0, stroke_opacity=0.42) for i in range(4)])
        self.flow_path = Line([-2.25, -0.6, 0], [1.55, 0.85, 0], color={accent!r}, stroke_width=2.4, stroke_opacity=0.72)
        self.streams = VGroup(*[Line([-2.2, -0.55 + i * 0.38, 0], [1.45, 0.78 + i * 0.22, 0], color={accent!r}, stroke_width=1.3, stroke_opacity=0.48) for i in range(4)])
        self.target = Circle(radius=0.58, color={accent!r}, stroke_width=3).shift(RIGHT * 1.85 + UP * 0.95)
        self.particles = VGroup(*[Dot(point=[-2.0 + i * 0.38, -0.75 + (i % 3) * 0.32, 0], radius=0.085, color={accent!r}) for i in range(6)])
        self.hero = Dot(point=[-2.25, -0.6, 0], radius=0.16, color={accent!r})
        self.accent_group = VGroup(self.field, self.streams, self.target, self.particles)
        """,
        "attention_cache": f"""
        self.query = Circle(radius=0.34, color={accent!r}, stroke_width=3).shift(LEFT * 2.55 + UP * 0.2)
        self.cache_slots = VGroup(*[Circle(radius=0.16, color={accent!r}, stroke_width=1.7).move_to([-0.95 + i * 0.48, 0.72 if i % 2 == 0 else 0.25, 0]) for i in range(6)])
        self.latent = VGroup(Line([-0.25, -0.55, 0], [0.95, -0.55, 0], color={accent!r}, stroke_width=5), Dot(point=[0.35, -0.55, 0], radius=0.13, color={accent!r}))
        self.read_arrows = VGroup(*[Arrow([-2.2, 0.2, 0], [-1.1 + i * 0.48, 0.72 if i % 2 == 0 else 0.25, 0], color={accent!r}, stroke_width=1.2, buff=0.08) for i in range(6)])
        self.rebuild = VGroup(*[Arrow([0.95, -0.55, 0], [1.65, -0.05 + i * 0.45, 0], color={accent!r}, stroke_width=1.25, buff=0.08) for i in range(3)])
        self.heads = VGroup(*[Dot(point=[1.8, -0.05 + i * 0.45, 0], radius=0.15, color={accent!r}) for i in range(3)])
        self.hero = Dot(point=[-2.55, 0.2, 0], radius=0.15, color={accent!r})
        self.motion_path = Line([-2.55, 0.2, 0], [0.35, -0.55, 0], color={accent!r}, stroke_opacity=0)
        self.accent_group = VGroup(self.query, self.cache_slots, self.latent, self.read_arrows, self.rebuild, self.heads)
        """,
        "moe_routing": f"""
        self.router = Circle(radius=0.42, color={accent!r}, stroke_width=3).shift(LEFT * 0.2)
        expert_points = [[1.45, 1.0, 0], [1.8, 0.0, 0], [1.45, -1.0, 0], [2.55, 0.0, 0]]
        self.experts = VGroup(*[Circle(radius=0.28, color={accent!r}, stroke_width=2).move_to(p) for p in expert_points])
        self.route_lines = VGroup(*[Arrow([0.2, 0, 0], p, color={accent!r}, stroke_width=1.5, buff=0.1, max_tip_length_to_length_ratio=0.16) for p in expert_points])
        self.tokens = VGroup(*[Dot(point=[-2.55, -0.55 + i * 0.55, 0], radius=0.13, color={accent!r}) for i in range(3)])
        self.token_lines = VGroup(*[Arrow([-2.35, -0.55 + i * 0.55, 0], [-0.65, 0, 0], color={accent!r}, stroke_width=1.25, buff=0.08) for i in range(3)])
        self.hero = Dot(point=[-2.55, 0, 0], radius=0.16, color={accent!r})
        self.motion_path = Line([-2.55, 0, 0], [1.45, 1.0, 0], color={accent!r}, stroke_opacity=0)
        self.accent_group = VGroup(self.router, self.experts, self.route_lines, self.tokens, self.token_lines)
        """,
        "speculative_decoding": f"""
        draft_points = [[-2.4, 0.25, 0], [-1.45, 0.25, 0], [-0.5, 0.25, 0]]
        self.draft_chain = VGroup(*[Circle(radius=0.25, color={accent!r}, stroke_width=2).move_to(p) for p in draft_points])
        self.draft_links = VGroup(*[Arrow(draft_points[i], draft_points[i + 1], color={accent!r}, stroke_width=1.5, buff=0.12) for i in range(2)])
        self.gate = Polygon([0.25, 0.72, 0], [0.85, 0, 0], [0.25, -0.72, 0], [-0.35, 0, 0], color={accent!r}, stroke_width=3)
        self.accepted = VGroup(*[Line([1.0 + i * 0.48, 0.0, 0], [1.35 + i * 0.48, 0.0, 0], color={accent!r}, stroke_width=5) for i in range(3)])
        self.reject_branch = Line([-0.5, 0.25, 0], [0.65, -1.0, 0], color="#EF4444", stroke_width=2, stroke_opacity=0.7)
        self.hero = Dot(point=draft_points[0], radius=0.15, color={accent!r})
        self.motion_path = Line(draft_points[0], [0.35, 0, 0], color={accent!r}, stroke_opacity=0)
        self.accent_group = VGroup(self.draft_chain, self.draft_links, self.gate, self.accepted, self.reject_branch)
        """,
        "latent_compression": f"""
        source_points = [[-2.5 + j * 0.5, -0.75 + i * 0.5, 0] for i in range(4) for j in range(4)]
        self.source = VGroup(*[Dot(point=p, radius=0.07, color={accent!r}) for p in source_points])
        self.projection = VGroup(*[Line(p, [-0.1 + (p[1] + 0.75) * 0.2, 0.0, 0], color={accent!r}, stroke_width=1.0, stroke_opacity=0.38) for p in source_points])
        self.axis = Line([-0.2, 0, 0], [1.3, 0, 0], color={accent!r}, stroke_width=5)
        self.latent_packet = Dot(point=[0.35, 0, 0], radius=0.18, color={accent!r})
        self.reconstruction = VGroup(*[Line([1.25, 0, 0], [2.35, -0.75 + i * 0.5, 0], color={accent!r}, stroke_width=1.0, stroke_opacity=0.38) for i in range(4)])
        self.output = VGroup(*[Dot(point=[2.45, -0.75 + i * 0.5, 0], radius=0.09, color={accent!r}) for i in range(4)])
        self.hero = Dot(point=[-2.5, -0.75, 0], radius=0.15, color={accent!r})
        self.motion_path = Line([-2.5, -0.75, 0], [0.35, 0, 0], color={accent!r}, stroke_opacity=0)
        self.accent_group = VGroup(self.source, self.projection, self.axis, self.latent_packet, self.reconstruction, self.output)
        """,
    }
    return bodies.get(family)


def _fallback_visual_code(spec: Dict[str, Any], beat: Dict[str, Any], beat_idx: int) -> str:
    """Return a safe, grammar-specific visual when model code cannot validate."""
    from pipeline.visual_generation import visual_grammar_details
    from pipeline.mechanism_visual_library import mechanism_recipe

    grammar, _ = visual_grammar_details(spec, beat_idx)
    recipe = mechanism_recipe(spec, beat)
    accent_by_grammar = {
        "hero_field": "#38BDF8",
        "physical_analogy": "#F59E0B",
        "exploded_mechanism": "#A855F7",
        "live_trace": "#10B981",
        "evidence_plot": "#34D399",
        "synthesis_lockup": "#FB7185",
    }
    accent = accent_by_grammar.get(grammar, "#38BDF8")
    topic = re.sub(r"[^A-Za-z0-9 ]+", "", str(spec.get("title", "AI MECHANISM"))).strip()
    topic = (topic[:24] or "AI MECHANISM").upper()
    label_prefix = (
        f"MEASURED {recipe['label'].split('→', 1)[0].strip()} CONVERGENCE"
        if grammar == "evidence_plot"
        else recipe["label"]
    )
    # Keep topic labels word-complete. Character slicing produced broken
    # labels such as ``GENIEX EDGENATIV`` in vertical renders. Prefer the
    # first complete words and only add an ellipsis when one word itself is
    # unusually long.
    topic_words = topic.split()
    topic_label = ""
    for word in topic_words:
        candidate = f"{topic_label} {word}".strip()
        if len(candidate) <= 16 or not topic_label:
            topic_label = candidate
        else:
            break
    if len(topic_label) > 16:
        topic_label = topic_label[:15].rstrip() + "…"
    label = json.dumps(f"{label_prefix} // {topic_label or 'AI'}")

    bodies = {
        "hero_field": """
        self.rings = VGroup(*[Circle(radius=r, color=accent, stroke_width=2.0, stroke_opacity=0.28) for r in (0.65, 1.25, 1.85)])
        self.rays = VGroup(*[Line(ORIGIN + RIGHT * np.cos(a) * 2.2 + UP * np.sin(a) * 2.2, ORIGIN + RIGHT * np.cos(a) * 0.45 + UP * np.sin(a) * 0.45, color=accent, stroke_width=1.5, stroke_opacity=0.55) for a in np.linspace(0, 2 * PI, 10, endpoint=False)])
        self.hero = Dot(point=ORIGIN, radius=0.24, color=accent)
        self.accent_group = VGroup(self.rings, self.rays)
        """,
        "physical_analogy": """
        self.path = VGroup(*[Arc(radius=1.2 + i * 0.42, start_angle=-1.2, angle=2.4, color=accent, stroke_width=2.0, stroke_opacity=0.55) for i in range(3)])
        self.particles = VGroup(*[Dot(point=[-1.4 + i * 0.7, -0.55 + 0.22 * i, 0], radius=0.09, color=accent) for i in range(5)])
        self.hero = VGroup(Circle(radius=0.42, color=accent, stroke_width=3), Dot(point=ORIGIN, radius=0.13, color=accent))
        self.accent_group = VGroup(self.path, self.particles)
        """,
        "exploded_mechanism": """
        self.layers = VGroup(*[Polygon([-1.8, -0.45, 0], [1.8, -0.45, 0], [1.45, 0.45, 0], [-2.15, 0.45, 0], color=accent, fill_color=accent, fill_opacity=0.12, stroke_width=2).shift(UP * (i * 0.55 - 0.55)) for i in range(3)])
        self.connectors = VGroup(*[Line([-1.2, -0.2 + i * 0.55, 0], [1.2, -0.2 + i * 0.55, 0], color=accent, stroke_width=1.2, stroke_opacity=0.55) for i in range(3)])
        self.hero = Dot(point=[0, 0.25, 0], radius=0.18, color=accent)
        self.accent_group = VGroup(self.layers, self.connectors)
        """,
        "live_trace": """
        self.trace = VMobject()
        self.trace.set_points_as_corners(np.array([[-2.4, -0.4, 0], [-1.2, 0.6, 0], [-0.3, -0.1, 0], [0.8, 1.0, 0], [2.4, 0.15, 0]]))
        self.trace.set_stroke(color=accent, width=4, opacity=0.85)
        self.steps = VGroup(*[Dot(point=p, radius=0.13, color=accent) for p in [[-2.4, -0.4, 0], [-1.2, 0.6, 0], [-0.3, -0.1, 0], [0.8, 1.0, 0], [2.4, 0.15, 0]]])
        self.hero = Dot(point=[-0.3, -0.1, 0], radius=0.16, color=accent)
        self.accent_group = VGroup(self.trace, self.steps)
        """,
        "evidence_plot": """
        self.axis = VGroup(Line([-2.5, -1.2, 0], [2.5, -1.2, 0], color="#94A3B8", stroke_width=1.5), Line([-2.5, -1.2, 0], [-2.5, 1.8, 0], color="#94A3B8", stroke_width=1.5))
        self.bars = VGroup(*[Rectangle(width=0.62, height=h, color=accent, fill_color=accent, fill_opacity=0.75, stroke_width=1.5).move_to([-1.55 + i * 1.05, -1.2 + h / 2, 0]) for i, h in enumerate((1.0, 1.65, 2.35, 2.05))])
        self.hero = self.bars[2]
        self.accent_group = VGroup(self.axis, self.bars)
        """,
        "synthesis_lockup": """
        self.left = Circle(radius=0.72, color=accent, stroke_width=3).shift(LEFT * 1.55)
        self.right = Polygon([0.55, 0.65, 0], [1.55, 0, 0], [0.55, -0.65, 0], [-0.45, 0, 0], color=accent, stroke_width=3)
        self.bridge = Line([-0.83, 0, 0], [-0.47, 0, 0], color=accent, stroke_width=3)
        self.hero = Dot(point=[0.55, 0, 0], radius=0.16, color=accent)
        self.accent_group = VGroup(self.left, self.right, self.bridge)
        """,
    }
    body = bodies.get(grammar) if grammar == "evidence_plot" else None
    body = body or _mechanism_fallback_body(recipe["family"], accent) or bodies.get(grammar, bodies["hero_field"])

    return f'''from manim import *
import numpy as np
from manim_engine.primitives.typography import CleanText

class BespokeBeatVisual(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        accent = {accent!r}
        self.label = CleanText({label}, font_size=13, color=accent, weight=BOLD, max_width=5.8).move_to([0, 2.55, 0])
{body}
        self.add(self.label, self.accent_group, self.hero)
        self.move_to(ORIGIN + UP * 0.75)

    def get_entrance_animation(self, run_time: float = 1.0) -> Animation:
        return AnimationGroup(FadeIn(self.label, shift=UP * 0.12), FadeIn(self.accent_group, scale=0.92), lag_ratio=0.15, run_time=run_time)

    def get_kinetic_animation(self, run_time: float = 1.0) -> Animation:
        animations = [self.hero.animate(rate_func=there_and_back, run_time=run_time).scale(1.12), self.accent_group.animate(rate_func=there_and_back, run_time=run_time).set_stroke(width=3.2)]
        if hasattr(self, "motion_path"):
            animations.insert(0, MoveAlongPath(self.hero, self.motion_path, run_time=run_time, rate_func=there_and_back))
        return AnimationGroup(*animations, run_time=run_time)

    def get_ambient_animation(self, run_time: float = 2.0) -> Animation:
        return self.accent_group.animate(rate_func=there_and_back, run_time=run_time).scale(1.025)
'''


BESPOKE_SYNTHESIZER_SYSTEM_PROMPT = """
You are the Lead Visual Animator and Computational Geometer at 3Blue1Brown and 'The Model Verse'.
Your mission: Write pure, executable Python Manim Community Edition code that builds a HIGH-DENSITY, PUBLICATION-GRADE geometric visual for a short-form video beat explaining an AI/Computer Science breakthrough.

CRITICAL DESIGN & QUALITY PRINCIPLES:

1. HIGH-DENSITY VISUAL COMPOSITION & ANTI-SPARSITY INVARIANT (MANDATORY):
   - NEVER DRAW SPARSE 'PROGRAMMER ART': Absolutely DO NOT render 2 bare stick lines, 1 lone square, or empty black voids! A 60fps Short requires high visual production value that commands attention.
   - FULL CANVAS UTILIZATION: Fill the central canvas (width ~6.2 units, height ~5.2 units, centered around ORIGIN + UP * 0.8) with rich, multi-component architectural schematics:
     * Use one clear hero object and one supporting visual relationship. Small labels are allowed only when they explain that relationship.
     * Legacy Header Status Badge chassis are not a required visual; never add one unless the mechanism itself is a status transition.
     * Legacy Technical Context Badges are optional annotations, never the hero visual or a substitute for causal geometry.
     * Multi-Element Mechanical / Neural Entities:
       - Robotics & Control: Multi-joint linkages with metallic gradient limbs, glowing joint bearings, end-effector grippers, sensory ray cones, trajectory arcs, coordinate target axes, and motor torque meters.
       - Neural Networks: Layered 3D-perspective tensor stacks, projection fans with color-coded vector beams, attention weight heatmaps, and pulsing latent nodes.
       - Hardware & Systems: Multi-channel data pipelines with flowing dashed particles, memory banks with highlighted cache blocks, throughput meters, and latency gauges.
     * Technical context is optional and sparse. Never repeat the same status badge, telemetry pill, or lower-third chassis across beats.
     * Rich Visual Polish: Use DashedLine, Arc, Circle with fill, coordinate arrows, bounding brackets, and color-coded components.

2. STRICTLY FORBIDDEN PATTERNS:
   - NO ENCLOSING SAAS CARDS: Do NOT wrap the entire screen inside a single generic website card or SaaS window frame! Instead, build rich modular geometric schematics that fill the canvas.
   - NO REPETITIVE 4x4 BUTTON MATRICES: Do NOT draw generic grid buttons unless specifically illustrating 2D matrix multiplication.
   - NO PLACEHOLDER BOXES: Never draw generic "Step 1 -> Step 2 -> Step 3" boxes without actual mathematical or mechanical details.
   - NO BEAT-TO-BEAT RECYCLING: Every beat has an assigned visual grammar. Do not reuse the same composition, camera framing, object arrangement, or primary primitive as another beat in the same video.

3. Mathematical & Typography Invariants:
   - STRICTLY NO `MathTex` or `Tex`! The host machine lacks pdflatex. Using MathTex will crash the entire renderer.
   - Use `CleanText` for all text and formulas with direct Unicode math symbols:
     e.g., CleanText("O(1) Memory Overhead", font_size=22, color="#38BDF8")
     e.g., CleanText("Attention Weight: α = softmax(Q·Kᵀ / √d)", font_size=18, color="#A7F3D0")
     Unicode math available: α, β, θ, ∑, →, ∇, ×, ∂, √, ᵀ, ·, ⚡, ℝ, τ, π, ϕ, ℒ, ∈, ∩, ≈, ≤, ≥
   - Base labels: "#94A3B8" (Slate), "#FFFFFF" (Pure White).
   - Accents: "#00F0FF" (Electric Cyan), "#10B981" (Mint Green), "#F59E0B" (Warm Amber), "#8B5CF6" (Violet), "#EF4444" (Danger Red).

4. 9:16 Vertical Safe-Zone Framing:
   - Screen width is 9.0 units (X from -4.5 to +4.5). Keep visual width <= 6.8 units (X within [-3.4, 3.4]).
   - Screen height is 16.0 units (Y from -8.0 to +8.0). Keep visual height <= 6.0 units.
   - Center your visual around `ORIGIN + UP * 0.8` so bottom subtitles and top headers don't collide.

5. ZERO TEXT OVERFLOW & ZERO OVERLAP INVARIANT (MANDATORY):
   - If placing text inside any box, badge, pill, card, or ellipse: The container MUST be strictly wider and taller than the text with at least 0.3 units margin.
   - Always pass `max_width=container.width - 0.4` to `CleanText` or call `text.scale_to_fit_width(container.width - 0.4)`.
   - If a label is wide (e.g. > 15 characters), either use a smaller `font_size` (16-18) or wrap/scale it so it NEVER overflows its parent or container boundaries.
   - ZERO TEXT COLLISION / OVERLAP INVARIANT: NEVER place a numeric value (e.g., "$0.00", "98%", "3.5x") at the exact same spatial coordinates as its text label (e.g., "LIQUID CASH BALANCE"). ALWAYS use vertical stacking: `VGroup(label, number).arrange(DOWN, buff=0.2)` or explicit offsets `.next_to(label, DOWN, buff=0.25)`!
   - COMPARISON BARS / METRICS ZERO OVERLAP: When comparing two or more entities (e.g., Baseline vs New Model, or FP16 vs INT4):
     NEVER place labels for different items at the same vertical position. Stack the metric bars vertically:
     Bar 1 with Label 1 at upper slot (e.g. Y = +0.6), and Bar 2 with Label 2 at lower slot (e.g. Y = -0.7) separated by at least 1.2 units vertically.
     Each label must be placed strictly `UP, buff=0.15` above its own bar, or to its `LEFT, buff=0.3`.

6. ZERO GRAPH & CONNECTED NODES MISALIGNMENT INVARIANT (MANDATORY):
   - When animating trees, networks, graphs, circular loops, or coordinate axes:
     - NEVER animate `self.nodes.animate.scale(...)` across a VGroup of multiple dots! Scaling a group of dots shifts their positions outward, disconnecting them from their branch lines!
     - To pulse dots in place without moving them, pulse each dot individually: `AnimationGroup(*[d.animate.scale(1.2) for d in self.nodes])`.
     - If transforming or scaling a connected graph/tree, scale BOTH the lines and dots together: `self.tree_group.animate.scale(1.05)`.
     - When rotating or moving connected nodes along a curve, circular loop, or path: ALWAYS animate BOTH the path line and the nodes together (`VGroup(self.loop_path, self.loop_nodes).animate...`), or move dots strictly along the path with `point_from_proportion`.
     - When scaling a radar or radial plot, ALWAYS pass `about_point=self.center_point` so vertices stay pinned to the axis spokes.

7. ON-DEMAND VISUAL GRAMMAR:
   - Treat the assigned grammar in the beat brief as a hard art-direction constraint. The beat must look materially different from the other beats.
   - Prefer geometry, paths, particles, rays, fields, layers, timelines, and transformations over panels.
   - Do not add a title card, footer badge, or decorative HUD merely to fill space. The mechanism should carry the scene.

CODE INTERFACE CONTRACT:
You must return executable Python code defining exactly this class:

```python
from manim import *
import numpy as np
from manim_engine.primitives.typography import CleanText

class BespokeBeatVisual(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 1. Build rich geometric entities, multi-layer schematics, and clean labels
        # 2. Add all components to self (e.g. self.add(...))
        # 3. Position centrally around ORIGIN + UP * 0.8

    def get_entrance_animation(self, run_time: float = 1.0) -> Animation:
        # Returns entrance animation revealing the mechanism progressively
        # e.g. AnimationGroup(Create(...), FadeIn(...), lag_ratio=0.2, run_time=run_time)

    def get_kinetic_animation(self, run_time: float = 1.0) -> Animation:
        # Returns the core dynamic transformation fired at the anchor word
        # e.g. token vectors routing, memory blocks evicting, matrix highlighting
        # e.g. AnimationGroup(Transform(...), ..., run_time=run_time)

    def get_ambient_animation(self, run_time: float = 2.0) -> Animation:
        # Returns gentle micro-motion (pulse, gentle oscillation, or wave) during speech
        # e.g. self.pulse_target.animate(rate_func=there_and_back, run_time=run_time).scale(1.05)
```

Return ONLY valid python code enclosed in ```python ... ```.
"""


class BespokeVisualSynthesizer:
    """Autonomous Engine that synthesizes bespoke Manim visual code per beat."""

    def __init__(self, model_name: Optional[str] = None, router: Optional[Any] = None):
        self.model_name = model_name or GEMINI_MODEL_NAME or "gemini-flash-latest"
        self.router = router or llm_router

    def synthesize_visual_for_beat(
        self,
        spec: Dict[str, Any],
        beat: Dict[str, Any],
        beat_idx: int,
        allow_self_healing: bool = True
    ) -> Optional[str]:
        """
        Synthesizes a bespoke Manim visual module for a specific beat.
        Returns the path to the verified .py file, or None if synthesis failed.
        """
        spec_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", spec.get("id", "short")).lower()
        beat_id = beat.get("beat_id", beat_idx)
        generation_key = str(spec.get("visual_generation_key") or "").strip()
        out_dir = GENERATED_VISUALS_DIR / spec_id
        if generation_key:
            out_dir = out_dir / generation_key
        out_dir.mkdir(parents=True, exist_ok=True)
        target_py_path = out_dir / f"beat_{beat_id}.py"

        # Check if already synthesized and valid
        if target_py_path.exists():
            with open(target_py_path, "r", encoding="utf-8") as f:
                existing_code = f.read()
            is_valid, _ = validate_synthesized_visual_code(existing_code)
            if is_valid:
                print(f"   ✨ [Bespoke Visual Synthesizer] Reusing verified visual for Beat {beat_id}: {target_py_path.name}")
                return str(target_py_path)

        prompt = self._construct_synthesis_prompt(spec, beat, beat_idx)

        print(f"\n🎨 [Bespoke Visual Synthesizer] Generating custom Manim visual for Beat {beat_id} ('{spec.get('title', spec_id)}')...")
        raw_code = self._generate_code(prompt)
        if not raw_code:
            print(f"   ⚠️ Visual synthesis returned empty response for Beat {beat_id}.")
            return None

        clean_code = self._extract_python_code(raw_code)

        # Stage 1: Validate through AST & Dry-Run Sandbox
        is_valid, err_msg = validate_synthesized_visual_code(clean_code)
        if is_valid:
            quality_valid, quality_err = validate_visual_quality_contract(clean_code)
            if not quality_valid:
                is_valid, err_msg = False, quality_err
        if is_valid:
            semantic_valid, semantic_err = validate_mechanism_semantics(clean_code, spec, beat)
            if not semantic_valid:
                is_valid, err_msg = False, semantic_err

        # Stage 2: 1-Shot Self-Healing if validation failed
        if not is_valid and allow_self_healing:
            print(f"   🔧 [Self-Healing Sandbox] Beat {beat_id} code flagged error: {err_msg[:80]}... Attempting 1-shot repair.")
            clean_code = self._repair_code(clean_code, err_msg, spec, beat)
            is_valid, err_msg = validate_synthesized_visual_code(clean_code)
            if is_valid:
                quality_valid, quality_err = validate_visual_quality_contract(clean_code)
                if not quality_valid:
                    is_valid, err_msg = False, quality_err
            if is_valid:
                semantic_valid, semantic_err = validate_mechanism_semantics(clean_code, spec, beat)
                if not semantic_valid:
                    is_valid, err_msg = False, semantic_err

        # On-demand mode must never leave a beat without a bespoke visual or
        # silently reuse a repetitive blueprint. Keep a grammar-specific,
        # deterministic safety module for malformed model responses.
        if not is_valid:
            fallback_code = _fallback_visual_code(spec, beat, beat_idx)
            fallback_valid, fallback_err = validate_synthesized_visual_code(fallback_code)
            if fallback_valid:
                fallback_valid, fallback_err = validate_visual_quality_contract(fallback_code)
            if fallback_valid:
                fallback_valid, fallback_err = validate_mechanism_semantics(fallback_code, spec, beat)
            if fallback_valid:
                clean_code = fallback_code
                is_valid = True
                print(f"   🧩 [On-Demand Visual Fallback] Beat {beat_id} uses a grammar-specific safety module after model validation failed.")
            else:
                err_msg = f"model: {err_msg}; fallback: {fallback_err}"

        if is_valid:
            with open(target_py_path, "w", encoding="utf-8") as f:
                f.write(clean_code)
            print(f"   ✅ [Bespoke Visual Synthesizer] Successfully synthesized & verified: {target_py_path.name}")
            return str(target_py_path)
        else:
            print(f"   ⚠️ [Bespoke Visual Synthesizer] Beat {beat_id} failed verification after repair: {err_msg[:120]}")
            return None

    def _construct_synthesis_prompt(
        self,
        spec: Dict[str, Any],
        beat: Dict[str, Any],
        beat_idx: int
    ) -> str:
        topic = spec.get("title", spec.get("id", "AI Deep Dive"))
        text = beat.get("text", "")
        v_focus = beat.get("visual_focus", "")
        analogy = beat.get("everyday_analogy", "")
        svo = beat.get("svo_action", {})
        highlights = beat.get("highlight_words", {})
        formula = beat.get("math_formula", "")
        code_data = spec.get("code_snippet", {})
        try:
            from pipeline.visual_generation import visual_grammar_details
            grammar_id, grammar_description = visual_grammar_details(spec, beat_idx)
        except Exception:
            grammar_id, grammar_description = (
                "bespoke_mechanism",
                "Invent a unique mechanism-first geometric composition.",
            )
        mechanism_direction = mechanism_prompt_block(spec, beat)

        grammar_plan = "; ".join(
            f"Beat {planned.get('beat_id', index + 1)}: {planned.get('visual_grammar')}"
            for index, planned in enumerate(spec.get("beats", []))
            if planned.get("visual_grammar")
        )

        return f"""
TOPIC: {topic}
CATEGORY: {spec.get('category', 'academic_breakdown')}
DOMAIN TAXONOMY: {spec.get('domain_taxonomy', 'deep_learning')}

CURRENT BEAT TO ANIMATE:
- Beat Index: {beat_idx} of {len(spec.get('beats', []))}
- Spoken Narration: "{text}"
- Visual Focus Concept: "{v_focus}"
- Physical Analogy: "{analogy}"
- SVO Action: Subject="{svo.get('subject', '')}", Action="{svo.get('action_verb', '')}", Object="{svo.get('direct_object', '')}", Anchor Word="{svo.get('anchor_word', '')}"
- Highlight Words: {json.dumps(highlights)}
- Math Formula / Concept: "{formula}"
- Kernel Code Snippet Available: {bool(code_data)}
- Assigned Visual Grammar (hard constraint): {grammar_id}
- Grammar Direction: {grammar_description}
- Topic Mechanism Recipe (hard constraint):
{mechanism_direction}
- Full Beat Grammar Plan (do not duplicate another beat): {grammar_plan}

MANDATORY VISUAL QUALITY REQUIREMENTS:
1. HIGH DENSITY & COMPOSITION: Build a multi-element mechanism visual that fills the center canvas without becoming a grid of generic cards.
2. GRAMMAR FIDELITY: Make the assigned grammar the dominant structure. A radial field must read as a field; an exploded mechanism must read as separated depth layers; an execution trace must read as time and state.
3. NO REPETITION: Do not use a repeated title/subtitle/badge chassis. Use at most one or two short labels, only where they clarify the mechanism.
4. ZERO OVERLAP: Use vertical stacking (.arrange(DOWN, buff=0.25)) for numbers and labels.

RESEARCHED DRAWING RULES:
5. DRAW THE CAUSE, NOT A UI SUMMARY: Follow the Topic Mechanism Recipe above. First choose the physical mechanism in one sentence: what moves, what pushes it, what changes, and what proves the change. Draw those anchors and their relationship. Do not substitute a dashboard, progress bar, card, or metric badge for the mechanism.
6. DETERMINISTIC GEOMETRY: Never use `random`, `np.random`, time, or noise sampling. Use fixed coordinates, seeded formulas, or explicit point arrays so every render is identical.
7. MEANINGFUL MOTION: Use a transformation, path-following particle, field/streamline, trace, reassembly, or causal highlight. Every connector must join two real objects and explain routing, force, comparison, or validation.
8. TEXT RESTRAINT: Use at most three `CleanText` objects. The narration and geometry carry the explanation; labels identify only objects that would otherwise be ambiguous.
9. VISUAL LAYERS: Compose a background treatment, one hero mechanism, and one supporting relationship. Give the eye two anchors and an intentional left/right or foreground/background path.

TASK:
Write the complete, self-contained Python Manim class `class BespokeBeatVisual(VGroup):` that builds and animates this exact concept.
"""

    def _repair_code(
        self,
        failing_code: str,
        error_msg: str,
        spec: Dict[str, Any],
        beat: Dict[str, Any]
    ) -> str:
        repair_prompt = f"""
The Python Manim code you generated for BespokeBeatVisual failed validation in our execution sandbox.

ERROR MESSAGE:
{error_msg}

FAILING CODE:
```python
{failing_code}
```

REPAIR INSTRUCTIONS:
1. Fix the exact syntax error, bounding box violation, or runtime animation crash shown above.
2. Remember: STRICTLY NO `MathTex` or `Tex`. Use `CleanText` with Unicode symbols (O(N^2), α, β, ∑, →).
3. Keep visual width <= 6.8 and height <= 7.0 centered around `ORIGIN + UP * 0.8`.
4. Ensure `get_entrance_animation()` and `get_kinetic_animation()` return valid Manim Animation objects (e.g. Create, Transform, FadeIn, or .animate).

Return ONLY the corrected Python code enclosed in ```python ... ```.
"""
        raw_repaired = self._generate_code(repair_prompt)
        if raw_repaired:
            return self._extract_python_code(raw_repaired)
        return failing_code

    def _call_gemini(self, prompt: str) -> Optional[str]:
        """Backward-compatible alias for OmniRoute code generation."""
        return self._generate_code(prompt)

    def _generate_code(self, prompt: str) -> Optional[str]:
        """
        Synthesizes visual code via OmniRoute cascade across Gemini, Groq, OpenRouter, and Ollama.
        Catches 429 quota exhaustion and seamlessly falls over to healthy models/providers.
        """
        active_router = getattr(self, "router", None) or llm_router
        return active_router.generate_text_with_cascade(
            prompt=prompt,
            system_instruction=BESPOKE_SYNTHESIZER_SYSTEM_PROMPT,
            preferred_model=getattr(self, "model_name", None)
        )

    def _extract_python_code(self, response_text: str) -> str:
        match = re.search(r"```(?:python)?\s*(.*?)\s*```", response_text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response_text.strip()


# Global instance
bespoke_synthesizer = BespokeVisualSynthesizer()
