"""
The Model Verse — Script-Driven Visual Director (Visual Engine 3.0)
Reads the voiceover script, conceptual shifts, and physical analogies for each beat,
and dynamically generates bespoke, high-fidelity 3Blue1Brown storyboard specifications
and visual parameters. Eliminates generic templates and repetitive circular score gauges.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import WORKSPACE_ROOT
from manim_engine.primitives.script_motifs import MOTIF_REGISTRY

VISUAL_ASSETS_DIR = PROJECT_ROOT / "public" / "visual_assets"
VISUAL_ASSETS_DIR.mkdir(parents=True, exist_ok=True)


class VisualDirector:
    """
    AI Visual Director that designs bespoke graphic scenes for every beat of a video script.
    Directly aligns voiceover beats to intuitive 3Blue1Brown mathematical and physical motifs.
    """

    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
            except Exception:
                pass
        self.candidate_models = ["gemini-3.8-flash", "gemini-3.1-flash-lite", "gemini-2.0-flash", "gemini-flash-latest"]

    def _call_gemini_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Calls Gemini with model fallback cascade and JSON parsing."""
        if not self.api_key:
            return None

        import google.generativeai as genai
        for model_name in self.candidate_models:
            try:
                model = genai.GenerativeModel(
                    model_name,
                    generation_config={"response_mime_type": "application/json"}
                )
                response = model.generate_content(prompt)
                if response and response.text:
                    clean_text = response.text.strip()
                    return json.loads(clean_text)
            except Exception as e:
                continue
        return None

    def plan_script_storyboard(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Reads the full video script beat-by-beat and uses Gemini (or heuristic fallback)
        to assign each beat an authentic, explanatory 3b1b visual motif and custom labels.
        """
        topic = spec.get("title", spec.get("id", "AI Breakthrough"))
        beats = spec.get("beats", [])
        num_beats = min(5, len(beats))

        beat_summaries = []
        for i in range(num_beats):
            b = beats[i]
            beat_summaries.append(
                f"Beat {b.get('beat_id', i+1)}: Voiceover: \"{b.get('text', '')}\"\n"
                f"   Visual Focus: \"{b.get('visual_focus', '')}\"\n"
                f"   Action: {b.get('svo_action', {})}"
            )

        prompt = f"""You are the Executive Visual Director for 'The Model Verse', an elite 3Blue1Brown-style educational channel explaining cutting-edge AI breakthroughs.

Read the 5 narrative beats for our video: '{topic}'
{chr(10).join(beat_summaries)}

Your mission: For EACH of the 5 beats, select the SINGLE BEST explanatory visual motif from our 3b1b primitive library, and customize its exact text labels, titles, and parameters to directly explain what the voiceover is narrating.

AVAILABLE MOTIFS IN THE LIBRARY:
1. "wave_collision": For colliding signals, wave interference, noise vs signal, or superposition.
   params: signal_a_label, signal_b_label, result_label, result_sub
2. "radio_tuner": For analog dials, frequency tuning, picking channels, or channel static.
   params: station_a_label, station_b_label, tuner_status, scope_label
3. "subspace_vectors": For packing concepts into vector spaces, coordinate grids, or orthogonal angles.
   params: title, sub, vec1_label, vec2_label, angle_label, badge_title, badge_sub
4. "prism_disentangler": For separating tangled thoughts, linear decoders, filtering noise, or peeling layers.
   params: title, sub, in_label, prism_label, out1_label, out2_label
5. "branching_outputs": For a single model / forward pass yielding dual answers or parallel decisions.
   params: in_label, core_title, core_sub, card1_title, card1_body, card2_title, card2_body
6. "tree_search": For reasoning models, MCTS, search paths, candidate exploration, and pruning dead ends.
   params: title, sub, root_label, optimal_label, optimal_sub, pruned_label, pruned_sub, badge_title, badge_sub
7. "diffusion_denoise": For diffusion, image/video generation, noise trajectories, or flow matching.
   params: title, sub, step1_label, step2_label, step3_label, badge_title, badge_sub
8. "attention_routing": For transformer attention, token dispatch, multi-head routing, or sparse MoE.
   params: title, sub, token_labels (list of 3), head_labels (list of 3), badge_title, badge_sub
9. "memory_buffer": For KV-cache, context windows, RAM, compression, or streaming buffers.
   params: title, sub, in_stream_label, cache_status_label, gain_badge_title, gain_badge_sub
10. "comparative_bars": For quantitative payoffs, benchmark comparisons, speedups, or accuracy deltas. (NEVER USE CIRCLES).
   params: title, sub, contender_a_name, contender_a_score (0.0-1.0), contender_a_text, contender_b_name, contender_b_score (0.0-1.0), contender_b_text, delta_badge_text, delta_badge_sub
11. "custom_flow": Universal 3-stage pipeline (Input -> Engine -> Result) for any bespoke mechanism.
   params: title, sub, step1_title, step1_sub, step2_title, step2_sub, step3_title, step3_sub

CRITICAL GUIDELINES:
- NEVER use generic progress circles or repetitive gauges.
- Every label MUST be meaningful technical typography (e.g. "98.5 MHz [STATION A]", "REASONING FLOW: 99.4%", "THOUGHT 1 (SIGNAL A)").
- Ensure the selected motif directly depicts the exact physical metaphor spoken in that beat.

Return ONLY a valid JSON object matching this schema:
{{
  "storyboard": [
    {{
      "beat_id": 1,
      "motif_type": "wave_collision",
      "motif_params": {{ ... }},
      "kinetic_action": "wave_pulse",
      "reasoning": "Directly matches the voiceover description of two signals colliding"
    }}
  ]
}}
"""
        plan_data = self._call_gemini_json(prompt)
        storyboard = []
        if plan_data and "storyboard" in plan_data:
            storyboard = plan_data["storyboard"]

        if not storyboard or len(storyboard) < num_beats:
            print("   ℹ️ Using intelligent semantic fallback for storyboard assignment...")
            storyboard = self._fallback_storyboard_plan(spec)

        return storyboard

    def _fallback_storyboard_plan(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Deterministic, semantic keyword matcher to select and parameterize motifs
        when LLM is unavailable.
        """
        beats = spec.get("beats", [])
        storyboard = []

        for i, b in enumerate(beats):
            b_id = b.get("beat_id", i + 1)
            if b_id > 5:
                continue

            text = (b.get("text", "") + " " + b.get("visual_focus", "")).lower()

            if any(k in text for k in ["radio", "dial", "tuner", "station"]):
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "radio_tuner",
                    "motif_params": {
                        "station_a_label": "98.5 MHz\n[STATION A]",
                        "station_b_label": "104.2 MHz\n[STATION B]",
                        "tuner_status": "TUNER: BETWEEN STATIONS (STATIC)",
                        "scope_label": "MESSY OVERLAPPING SOUND WAVES"
                    },
                    "kinetic_action": "needle_sweep"
                })
            elif any(k in text for k in ["prism", "peel", "disentangl", "separate streams", "decoder"]):
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "prism_disentangler",
                    "motif_params": {
                        "title": "PEELING LAYERS APART (DISENTANGLEMENT)",
                        "sub": "Gentle model tuning turns noise into two distinct thought streams",
                        "in_label": "TANGLED\nSUPERPOSITION",
                        "prism_label": "LINEAR\nDECODER",
                        "out1_label": "CLEAN THOUGHT 1 (SIGNAL A)",
                        "out2_label": "CLEAN THOUGHT 2 (SIGNAL B)"
                    },
                    "kinetic_action": "beam_glow"
                })
            elif any(k in text for k in ["branch", "two clear answers", "simultaneous", "forward pass"]):
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "branching_outputs",
                    "motif_params": {
                        "in_label": "DUAL PROMPT CONTEXT",
                        "core_title": "1 FORWARD PASS",
                        "core_sub": "Shared Latent Linear Map",
                        "card1_title": "ANSWER 1",
                        "card1_body": "Reasoning Flow\nAccuracy: 99.4%",
                        "card2_title": "ANSWER 2",
                        "card2_body": "Creative Synthesis\nAccuracy: 98.9%"
                    },
                    "kinetic_action": "branch_pop"
                })
            elif any(k in text for k in ["space", "save room", "vector", "dimension", "orthogonal", "coordinate", "bookshelf"]):
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "subspace_vectors",
                    "motif_params": {
                        "title": "SUPERPOSITION: PACKING MULTIPLE IDEAS",
                        "sub": "Almost-orthogonal directions allow N > D concepts in D dimensions",
                        "vec1_label": "Concept v₁\n[Thought A]",
                        "vec2_label": "Concept v₂\n[Thought B]",
                        "angle_label": "θ ≈ 90° (Orthogonal)",
                        "badge_title": "IT IS A FEATURE, NOT A BUG",
                        "badge_sub": "The model re-uses latent space to compress memory exponentially."
                    },
                    "kinetic_action": "vector_scale"
                })
            elif any(k in text for k in ["wave", "signal", "interference", "sound wave", "collid", "two distinct thoughts", "crowded room"]):
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "wave_collision",
                    "motif_params": {
                        "signal_a_label": "THOUGHT 1 (SIGNAL A)",
                        "signal_b_label": "THOUGHT 2 (SIGNAL B)",
                        "result_label": "OVERLAPPING SUPERPOSITION",
                        "result_sub": "Two independent concepts packed into one channel"
                    },
                    "kinetic_action": "wave_pulse"
                })

            elif any(k in text for k in ["tree", "search", "mcts", "reason", "logic", "prun"]):
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "tree_search",
                    "motif_params": {
                        "title": "REASONING SEARCH & BRANCH PRUNING",
                        "sub": "Exploring parallel thoughts and pruning invalid logic paths",
                        "root_label": "ROOT QUERY / PROBLEM",
                        "optimal_label": "OPTIMAL CHAIN",
                        "optimal_sub": "Verified logic path\nConfidence: 98.4%",
                        "pruned_label": "PRUNED DEAD END",
                        "pruned_sub": "Hallucination detected\nBranch terminated",
                        "badge_title": "SEARCH GUIDANCE HEURISTIC",
                        "badge_sub": "Focuses 90% compute on promising reasoning paths"
                    },
                    "kinetic_action": "tree_prune"
                })
            elif any(k in text for k in ["diffus", "noise", "denois", "image", "video", "latent"]):
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "diffusion_denoise",
                    "motif_params": {
                        "title": "DIFFUSION DENOISING TRAJECTORY",
                        "sub": "Iterative reverse trajectory peels noise into clear signals",
                        "step1_label": "STEP 1: NOISE",
                        "step2_label": "STEP 2: LATENTS",
                        "step3_label": "STEP 3: OUTPUT",
                        "badge_title": "FLOW MATCHING VELOCITY FIELD",
                        "badge_sub": "Deterministic straight paths achieve 10x faster inference"
                    },
                    "kinetic_action": "denoise_step"
                })
            elif any(k in text for k in ["attention", "head", "expert", "moe", "rout", "token"]):
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "attention_routing",
                    "motif_params": {
                        "title": "MULTI-HEAD ATTENTION ROUTING",
                        "sub": "Dynamic routing aligns queries with key memory slots",
                        "token_labels": ["Token: 'Input'", "Token: 'Attention'", "Token: 'Routing'"],
                        "head_labels": ["HEAD 1 (SYNTAX)", "HEAD 2 (LOGIC)", "HEAD 3 (SEMANTICS)"],
                        "badge_title": "SPARSE EXPERT ACTIVATION",
                        "badge_sub": "Only top heads fire, slashing latency by 80%"
                    },
                    "kinetic_action": "laser_route"
                })
            elif any(k in text for k in ["cache", "kv", "memory", "buffer", "context", "window"]):
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "memory_buffer",
                    "motif_params": {
                        "title": "KV-CACHE CONTEXT COMPRESSION",
                        "sub": "Streaming long horizons without quadratic memory explosion",
                        "in_stream_label": "INCOMING CONTEXT STREAM",
                        "cache_status_label": "ACTIVE KV CACHE BUFFER",
                        "gain_badge_title": "75% MEMORY REDUCTION",
                        "gain_badge_sub": "Constant inference latency sustained across 128k context"
                    },
                    "kinetic_action": "buffer_stream"
                })
            elif b_id == 5 or any(k in text for k in ["benchmark", "accuracy", "speedup", "gain", "percent", "faster"]):
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "comparative_bars",
                    "motif_params": {
                        "title": "EMPIRICAL BENCHMARK EVALUATION",
                        "sub": "Multi-step reasoning accuracy vs prior state-of-the-art baselines",
                        "contender_a_name": "NEW ARCHITECTURE (OURS)",
                        "contender_a_score": 0.94,
                        "contender_a_text": "94.0%",
                        "contender_b_name": "CONVENTIONAL BASELINE",
                        "contender_b_score": 0.52,
                        "contender_b_text": "52.0%",
                        "delta_badge_text": "⚡ +42.0% REASONING IMPROVEMENT",
                        "delta_badge_sub": "Zero performance degradation with 2.4x speedup"
                    },
                    "kinetic_action": "bar_fill"
                })
            else:
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "custom_flow",
                    "motif_params": {
                        "title": "ARCHITECTURAL PIPELINE",
                        "sub": "Step-by-step mechanism flow",
                        "step1_title": "INPUT STATE",
                        "step1_sub": "Raw context stream",
                        "step2_title": "TRANSFORMATION ENGINE",
                        "step2_sub": "Nonlinear latent routing",
                        "step3_title": "FINAL PREDICTION",
                        "step3_sub": "High-confidence target"
                    },
                    "kinetic_action": "flow_pulse"
                })

        return storyboard

    def prepare_storyboard_for_spec(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Plans the visual choreography for each beat based on the voiceover script,
        and annotates the spec beats with rich motif directives.
        """
        clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", spec.get("id", "short_topic")).lower()
        topic = spec.get("title", clean_id)
        beats = spec.get("beats", [])

        print(f"\n🎬 [VisualDirector] Designing Script-Driven Visual Storyboard for '{topic}'...")

        storyboard = self.plan_script_storyboard(spec)
        sb_by_id = {item.get("beat_id"): item for item in storyboard}

        for i, b in enumerate(beats):
            b_id = b.get("beat_id", i + 1)
            if b_id in sb_by_id:
                plan_item = sb_by_id[b_id]
                b["motif_type"] = plan_item.get("motif_type", "custom_flow")
                b["motif_params"] = plan_item.get("motif_params", {})
                b["kinetic_action"] = plan_item.get("kinetic_action", "pulse")
                print(f"   ✨ Beat {b_id}: Assigned Motif '{b['motif_type']}' ({b.get('kinetic_action')})")

        spec["script_driven_visuals"] = True
        return spec
