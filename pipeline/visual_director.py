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

Your mission: For EACH of the 5 beats, select the SINGLE BEST explanatory visual motif and customize its exact text labels, titles, and parameters to directly explain what the voiceover is narrating.

PRIMARY ARCHITECTURAL ENGINES:
1. "bespoke_svg" (PRIMARY ENGINE FOR NARRATIVE BEATS 1, 2, 4, AND BEAT 3):
   Our dynamic vector synthesizer generates an exact, bespoke chalkboard vector illustration directly explaining the physical analogy or technical mechanism narrated in this beat.
   params: title, sub, badge_text, accent_color (#38BDF8, #34D399, #F59E0B, #A855F7)
2. "paper_figure" (FOR BEAT 3 IF OFFICIAL ARXIV DIAGRAM EXISTS):
   Displays the official publication architecture vector diagram extracted directly from the paper's LaTeX/PDF source.
   params: title, sub, badge_text
3. "comparative_bars" (MANDATORY FOR BEAT 5):
   Clean horizontal metric comparison bars comparing the new breakthrough vs prior baselines.
   params: title, sub, contender_a_name, contender_a_score (0.0-1.0), contender_a_text, contender_b_name, contender_b_score (0.0-1.0), contender_b_text, delta_badge_text, delta_badge_sub

CRITICAL DIRECTIVES:
- NEVER use generic progress circles or repetitive canned diagrams.
- Narrative beats (Beats 1 to 4) MUST use "bespoke_svg" (or "paper_figure" if official vector figures exist).
- Payoff beat (Beat 5) MUST use "comparative_bars".
{"- NOTE: Official vector figures are extracted for this paper. Use 'paper_figure' for Beat 3 to showcase the authentic publication diagram!" if spec.get("paper_figures") else ""}

Return ONLY a valid JSON object matching this schema:
{{
  "storyboard": [
    {{
      "beat_id": 1,
      "motif_type": "bespoke_svg",
      "motif_params": {{
        "title": "SPECIFIC CONCEPT TITLE",
        "sub": "Explanation of visual analogy",
        "badge_text": "TECHNICAL ROLE",
        "accent_color": "#38BDF8"
      }},
      "kinetic_action": "figure_scan",
      "reasoning": "Directly matches the voiceover description"
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
        when LLM is unavailable. Dynamically derives labels from topic title,
        SVO actions, highlight words, and extracted paper figures.
        """
        beats = spec.get("beats", [])
        topic_title = spec.get("title", "AI Breakthrough")
        paper_figures = spec.get("paper_figures", [])
        storyboard = []

        for i, b in enumerate(beats):
            b_id = b.get("beat_id", i + 1)
            if b_id > 5:
                continue

            text = (b.get("text", "") + " " + b.get("visual_focus", "")).lower()
            hl_keys = list(b.get("highlight_words", {}).keys())
            svo = b.get("svo_action", {})
            subj = svo.get("subject", hl_keys[0] if hl_keys else "Signal A")
            obj = svo.get("direct_object", hl_keys[1] if len(hl_keys) > 1 else "Signal B")
            v_focus = b.get("visual_focus", "")

            # If paper vector figures were extracted, prioritize paper_figure for core mechanism (Beat 3)
            if paper_figures and b_id == 3:
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "paper_figure",
                    "motif_params": {
                        "svg_path": paper_figures[0].get("svg_path"),
                        "title": f"{topic_title.upper()[:28]} ARCHITECTURE",
                        "sub": v_focus[:55] or "Official architectural diagram from arXiv source",
                        "badge_text": f"PRIMARY MECHANISM: {subj.upper()[:20]}"
                    },
                    "kinetic_action": "figure_scan"
                })
            # Rich Physical Analogy Detection -> Bespoke Dynamic Vector SVG
            elif any(k in text for k in ["smoothie", "blend", "fruit", "strawberr", "puree"]):
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "bespoke_svg",
                    "motif_params": {
                        "title": f"DESTRUCTIVE BLENDING VS PRESERVATION",
                        "sub": v_focus[:55] or "Preserving discrete structural boundaries vs uniform puree",
                        "badge_text": f"ANALYSIS: {subj.upper()[:20]}"
                    },
                    "kinetic_action": "figure_scan"
                })
            elif any(k in text for k in ["flicker", "portrait", "sketch", "outline", "contour", "wireframe", "dots"]):
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "bespoke_svg",
                    "motif_params": {
                        "title": f"CRISP BOUNDARY RESOLUTION",
                        "sub": v_focus[:55] or "Resolving sharp structural contours from flickering noise",
                        "badge_text": f"STRUCTURE: {subj.upper()[:20]}"
                    },
                    "kinetic_action": "figure_scan"
                })
            elif any(k in text for k in ["split", "dual", "track", "bifurcat", "two path", "semantic and geometric"]):
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "bespoke_svg",
                    "motif_params": {
                        "title": f"BIFURCATED DUAL-TRACK ARCHITECTURE",
                        "sub": v_focus[:55] or "Decoupling high-level semantics from low-level geometric depth",
                        "badge_text": f"DUAL ROUTING: {subj.upper()[:20]}"
                    },
                    "kinetic_action": "figure_scan"
                })
            elif any(k in text for k in ["barrier", "penalty", "bleed", "prevent", "isolate", "separate paths", "forcefield"]):
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "bespoke_svg",
                    "motif_params": {
                        "title": f"ORTHOGONAL ANTI-BLEED BARRIER",
                        "sub": v_focus[:55] or "Strict penalty prevents cross-talk between latent streams",
                        "badge_text": f"ISOLATION: {subj.upper()[:20]}"
                    },
                    "kinetic_action": "figure_scan"
                })
            elif any(k in text for k in ["lego", "voxel", "quantiz", "block", "grid", "pixelat", "chunk"]):
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "bespoke_svg",
                    "motif_params": {
                        "title": f"CONTINUOUS VS DISCRETE QUANTIZATION",
                        "sub": v_focus[:55] or "Stepping continuous signals into discrete computational blocks",
                        "badge_text": f"QUANTIZATION: {subj.upper()[:20]}"
                    },
                    "kinetic_action": "figure_scan"
                })
            elif any(k in text for k in ["puzzle", "jigsaw", "snap", "broken", "interlock"]):
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "bespoke_svg",
                    "motif_params": {
                        "title": f"JIGSAW ASSEMBLY TRAJECTORY",
                        "sub": v_focus[:55] or "Interlocking fragmented latents into a unified path",
                        "badge_text": f"ASSEMBLY: {subj.upper()[:20]}"
                    },
                    "kinetic_action": "figure_scan"
                })
            elif any(k in text for k in ["bottleneck", "highway", "toll", "choke", "narrow", "express"]):
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "bespoke_svg",
                    "motif_params": {
                        "title": f"HIGHWAY BOTTLENECK & EXPRESS BYPASS",
                        "sub": v_focus[:55] or "Bypassing serialization bottlenecks with parallel express lanes",
                        "badge_text": f"THROUGHPUT: {subj.upper()[:20]}"
                    },
                    "kinetic_action": "figure_scan"
                })
            elif b_id == 5 or any(k in text for k in ["benchmark", "accuracy", "speedup", "gain", "percent", "faster"]):
                payoff_stat = spec.get("metadata", {}).get("payoff_hero_stat", 94.0)
                payoff_base = spec.get("metadata", {}).get("payoff_base_stat", 54.0)
                score_a = float(payoff_stat) / 100.0 if payoff_stat > 1.0 else float(payoff_stat)
                score_b = float(payoff_base) / 100.0 if payoff_base > 1.0 else float(payoff_base)
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "comparative_bars",
                    "motif_params": {
                        "title": f"BENCHMARK RESULTS: {topic_title.upper()[:20]}",
                        "sub": v_focus[:55] or "Empirical evaluation against prior frontier models",
                        "contender_a_name": f"{topic_title.upper()[:18]} (OURS)",
                        "contender_a_score": score_a,
                        "contender_a_text": f"{payoff_stat}%" if isinstance(payoff_stat, (int, float)) else str(payoff_stat),
                        "contender_b_name": "PRIOR BASELINE",
                        "contender_b_score": score_b,
                        "contender_b_text": f"{payoff_base}%" if isinstance(payoff_base, (int, float)) else str(payoff_base),
                        "delta_badge_text": "⚡ SOTA PERFORMANCE ADVANTAGE",
                        "delta_badge_sub": "Significant efficiency and accuracy milestone"
                    },
                    "kinetic_action": "bar_fill"
                })
            else:
                s1_t = hl_keys[0].upper() if hl_keys else "INPUT STATE"
                s2_t = svo.get("action_verb", "TRANSFORMATION").upper() + " MECHANISM"
                storyboard.append({
                    "beat_id": b_id,
                    "motif_type": "bespoke_svg",
                    "motif_params": {
                        "title": f"{topic_title.upper()[:22]}: {subj.upper()[:16]}",
                        "sub": v_focus[:55] or f"Visualizing {subj.lower()} and {obj.lower()}",
                        "badge_text": f"CORE: {subj.upper()[:18]}",
                        "accent_color": "#38BDF8"
                    },
                    "kinetic_action": "figure_scan"
                })

        return storyboard

    def prepare_storyboard_for_spec(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Plans the visual choreography for each beat based on the voiceover script,
        and annotates the spec beats with rich motif directives.
        Guarantees that narrative beats 1-4 use bespoke vector diagrams (or authentic paper figures)
        and eliminates repetitive canned diagrams.
        """
        clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", spec.get("id", "short_topic")).lower()
        topic = spec.get("title", clean_id)
        beats = spec.get("beats", [])
        paper_figures = spec.get("paper_figures", [])

        print(f"\n🎬 [VisualDirector] Designing Script-Driven Visual Storyboard for '{topic}'...")

        storyboard = self.plan_script_storyboard(spec)
        sb_by_id = {item.get("beat_id"): item for item in storyboard}

        from pipeline.svg_synthesizer import SVGSynthesizer
        svg_synthesizer = SVGSynthesizer()

        canned_motifs = [
            "prism_disentangler", "attention_routing", "tree_search",
            "memory_buffer", "custom_flow", "branching_outputs",
            "wave_collision", "radio_tuner", "subspace_vectors", "diffusion_denoise"
        ]

        for i, b in enumerate(beats):
            b_id = b.get("beat_id", i + 1)
            if b_id > 5:
                continue

            if b_id in sb_by_id:
                plan_item = sb_by_id[b_id]
                b["motif_type"] = plan_item.get("motif_type", "bespoke_svg")
                b["motif_params"] = plan_item.get("motif_params", {})
                b["kinetic_action"] = plan_item.get("kinetic_action", "figure_scan")

            # Beat 5: Empirical benchmark evaluation bars
            if b_id == 5:
                b["motif_type"] = "comparative_bars"
                b["kinetic_action"] = "bar_fill"
                if not b.get("motif_params"):
                    payoff_stat = spec.get("metadata", {}).get("payoff_hero_stat", 94.0)
                    payoff_base = spec.get("metadata", {}).get("payoff_base_stat", 54.0)
                    score_a = float(payoff_stat) / 100.0 if payoff_stat > 1.0 else float(payoff_stat)
                    score_b = float(payoff_base) / 100.0 if payoff_base > 1.0 else float(payoff_base)
                    b["motif_params"] = {
                        "title": f"BENCHMARK RESULTS: {topic.upper()[:20]}",
                        "sub": b.get("visual_focus", "")[:55] or "Empirical evaluation against prior frontier models",
                        "contender_a_name": f"{topic.upper()[:18]} (OURS)",
                        "contender_a_score": score_a,
                        "contender_a_text": f"{payoff_stat}%" if isinstance(payoff_stat, (int, float)) else str(payoff_stat),
                        "contender_b_name": "PRIOR BASELINE",
                        "contender_b_score": score_b,
                        "contender_b_text": f"{payoff_base}%" if isinstance(payoff_base, (int, float)) else str(payoff_base),
                        "delta_badge_text": "⚡ SOTA PERFORMANCE ADVANTAGE",
                        "delta_badge_sub": "Significant efficiency and accuracy milestone"
                    }
                print(f"   ✨ Beat 5: Assigned Motif 'comparative_bars' (bar_fill)")
                continue

            # Beat 3: Authentic paper diagram if extracted from arXiv
            if paper_figures and b_id == 3:
                fig_svg = paper_figures[0].get("svg_path")
                if fig_svg and not os.path.exists(fig_svg):
                    rel_match = re.search(r"(public/arxiv_cache/.*)", fig_svg)
                    if rel_match:
                        local_fig = str(PROJECT_ROOT / rel_match.group(1))
                        if os.path.exists(local_fig):
                            fig_svg = local_fig
                        else:
                            fig_svg = None
                    else:
                        fig_svg = None

                if fig_svg and os.path.exists(fig_svg):
                    b["motif_type"] = "paper_figure"
                    b["motif_params"] = {
                        "svg_path": fig_svg,
                        "title": f"{topic.upper()[:28]} ARCHITECTURE",
                        "sub": b.get("visual_focus", "")[:55] or "Official architectural diagram from arXiv source",
                        "badge_text": "PRIMARY ARCHITECTURE SPECIFICATION"
                    }
                    b["kinetic_action"] = "figure_scan"
                    print(f"   ✨ Beat 3: Assigned Authentic arXiv Paper Diagram '{os.path.basename(fig_svg)}'")
                    continue

            # Narrative Beats (1, 2, 4, and 3 without paper figure):
            # MANDATE bespoke_svg! Overwrite any legacy canned motif!
            if b.get("motif_type") in canned_motifs or not b.get("motif_type") or b.get("motif_type") in ["bespoke_svg", "dynamic_svg"]:
                b["motif_type"] = "bespoke_svg"
                b["kinetic_action"] = "figure_scan"
                try:
                    svg_path = svg_synthesizer.synthesize_beat_svg(b, topic, clean_id, b_id)
                    if svg_path and svg_path.exists():
                        if not b.get("motif_params"):
                            b["motif_params"] = {}
                        b["motif_params"]["svg_path"] = str(svg_path)
                        if not b["motif_params"].get("title"):
                            b["motif_params"]["title"] = f"{topic.upper()[:22]}: BEAT {b_id}"
                        if not b["motif_params"].get("sub"):
                            b["motif_params"]["sub"] = b.get("visual_focus", "")[:55] or "Dynamic vector diagram tailored to narrative beat"
                        if not b["motif_params"].get("badge_text"):
                            svo = b.get("svo_action", {})
                            b["motif_params"]["badge_text"] = f"MECHANISM: {svo.get('subject', 'CORE').upper()[:18]}"
                except Exception as e:
                    print(f"⚠️ Error synthesizing SVG for beat {b_id}: {e}")

            print(f"   ✨ Beat {b_id}: Assigned Motif '{b.get('motif_type')}' ({b.get('kinetic_action')})")

        spec["script_driven_visuals"] = True
        return spec
