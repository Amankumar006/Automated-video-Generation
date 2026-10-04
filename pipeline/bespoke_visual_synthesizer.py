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
    import google.generativeai as genai

from pipeline.config import GEMINI_MODEL_NAME
from pipeline.code_sandbox import validate_synthesized_visual_code

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

GENERATED_VISUALS_DIR = PROJECT_ROOT / "manim_engine" / "generated"
GENERATED_VISUALS_DIR.mkdir(parents=True, exist_ok=True)


BESPOKE_SYNTHESIZER_SYSTEM_PROMPT = """
You are the Lead Visual Animator and Computational Geometer at 3Blue1Brown and 'The Model Verse'.
Your mission: Write pure, executable Python Manim Community Edition code that builds a BESPOKE, BRAND-NEW geometric visual for a specific short-form video beat explaining an AI/Computer Science breakthrough.

CRITICAL DESIGN PRINCIPLES:
1. 100% Bespoke Geometric Mechanism:
   - Translate the spoken concept and physical mechanism directly into geometric entities:
     * Memory / KV Cache: Linked address blocks, allocation slots, memory fragmentation vs paging, cache eviction arrows.
     * Transformer Attention: Query/Key/Value projection beams, attention score heatmap grids, token vectors interacting.
     * Hardware / GPUs: SRAM vs HBM memory hierarchy, asynchronous warp copy pipelines, tensor core matrix tiles.
     * Search / Agents / Code: AST branch nodes, state space manifolds, branch-and-bound pruning crosses, optimal path glow.
     * Diffusion / Physics: Continuous vector velocity fields, flow trajectories, denoising steps, manifold curves.
2. STRICTLY FORBIDDEN PATTERNS (DO NOT DO THESE):
   - NO ENCLOSING SAAS CARDS: Absolutely DO NOT wrap your visual inside a RoundedRectangle, dashboard container, or window frame! Let the geometry float freely and breathe on the dark #0A0D14 canvas.
   - NO REPETITIVE 4x4 BUTTON MATRICES: Do NOT draw generic grid buttons unless specifically illustrating 2D matrix multiplication!
   - NO PLACEHOLDER BOXES: Never draw generic "Step 1 -> Step 2 -> Step 3" boxes!
3. Mathematical & Typography Invariants:
   - STRICTLY NO `MathTex` or `Tex`! The host machine lacks pdflatex. Using MathTex will crash the entire renderer.
   - Use `CleanText` for all text and formulas with direct Unicode math symbols:
     e.g., CleanText("O(1) Memory Overhead", font_size=24, color="#38BDF8")
     e.g., CleanText("Attention Weight: α = softmax(Q·Kᵀ / √d)", font_size=20, color="#A7F3D0")
     Unicode math available: α, β, θ, ∑, →, ∇, ×, ∂, √, ᵀ, ·, ⚡
4. Color Palette (3b1b on Carbon #0A0D14):
   - Primary accents: "#00F0FF" (Electric Cyan), "#10B981" (Mint Green), "#F59E0B" (Warm Amber), "#8B5CF6" (Violet), "#EF4444" (Danger Red).
   - Base labels: "#94A3B8" (Slate), "#FFFFFF" (Pure White).
5. 9:16 Vertical Safe-Zone Framing:
   - Screen width is 9.0 units (X from -4.5 to +4.5). Keep visual width <= 6.8 units (X within [-3.4, 3.4]).
   - Screen height is 16.0 units (Y from -8.0 to +8.0). Keep visual height <= 7.0 units.
   - Center your visual around `ORIGIN + UP * 0.8` so bottom subtitles and top headers don't collide.

CODE INTERFACE CONTRACT:
You must return executable Python code defining exactly this class:

```python
from manim import *
import numpy as np
from manim_engine.primitives.typography import CleanText

class BespokeBeatVisual(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 1. Build geometric mobjects and clean labels
        # 2. Add them to self (e.g. self.add(...))
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

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or GEMINI_MODEL_NAME or "gemini-flash-latest"

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
        out_dir = GENERATED_VISUALS_DIR / spec_id
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
        raw_code = self._call_gemini(prompt)
        if not raw_code:
            print(f"   ⚠️ Gemini synthesis returned empty response for Beat {beat_id}.")
            return None

        clean_code = self._extract_python_code(raw_code)

        # Stage 1: Validate through AST & Dry-Run Sandbox
        is_valid, err_msg = validate_synthesized_visual_code(clean_code)

        # Stage 2: 1-Shot Self-Healing if validation failed
        if not is_valid and allow_self_healing:
            print(f"   🔧 [Self-Healing Sandbox] Beat {beat_id} code flagged error: {err_msg[:80]}... Attempting 1-shot repair.")
            clean_code = self._repair_code(clean_code, err_msg, spec, beat)
            is_valid, err_msg = validate_synthesized_visual_code(clean_code)

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

        return f"""
TOPIC: {topic}
CATEGORY: {spec.get('category', 'mechanism_deepdive')}
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

TASK:
Write the complete, self-contained Python Manim class `class BespokeBeatVisual(VGroup):` that builds and animates this exact concept.
Do not use generic SaaS cards. Construct the real geometric mechanism described in the narration.
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
        raw_repaired = self._call_gemini(repair_prompt)
        if raw_repaired:
            return self._extract_python_code(raw_repaired)
        return failing_code

    def _call_gemini(self, prompt: str) -> Optional[str]:
        if not API_KEY:
            return None
        try:
            model = genai.GenerativeModel(
                self.model_name,
                system_instruction=BESPOKE_SYNTHESIZER_SYSTEM_PROMPT
            )
            resp = model.generate_content(prompt)
            if resp and resp.text:
                return resp.text.strip()
        except Exception as e:
            print(f"⚠️ Bespoke synthesizer Gemini call notice: {e}")
        return None

    def _extract_python_code(self, response_text: str) -> str:
        match = re.search(r"```(?:python)?\s*(.*?)\s*```", response_text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response_text.strip()


# Global instance
bespoke_synthesizer = BespokeVisualSynthesizer()
