"""
The Model Verse — Intellectual Thriller Narrative Engine & Script Rewrite System (Engine 7.0)
Replaces textbook summaries and academic slide presentations with a high-tempo 4-act dopamine arc:
  Act 1: Absurd Paradox / Pattern Interrupt Hook (Beat 1, 0-3s)
  Act 2: The Villain & Bottleneck (Beat 2, 3-15s)
  Act 3: The Eureka Geometric Mechanism (Beats 3 & 4, 15-40s)
  Act 4: The Paradigm Shift / Open Loop (Beats 5 & 6, 40-50s)

Provides automated rewriting for legacy/academic drafts and strict pedagogical auditing.
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=FutureWarning)
    try:
        import google.generativeai as genai
    except ImportError:
        genai = None

from pipeline.json_utils import robust_json_loads

# Forbidden academic / textbook lecture clichés
TEXTBOOK_LECTURE_CLICHES = [
    "today we explore", "today we'll explore", "today we look at", "today we discuss",
    "in this video", "in this paper", "in this study", "in this research",
    "the authors propose", "the authors present", "the authors introduce",
    "we propose", "we present", "we introduce", "we demonstrate",
    "let's examine", "let's dive in", "let's take a look", "welcome back",
    "this paper presents", "this study investigates", "this video explores",
    "an overview of", "a breakdown of how", "today's topic is"
]

INTELLECTUAL_THRILLER_SYSTEM_PROMPT = """
You are the Lead Creative Director and Principal Scriptwriter for 'The Model Verse' (themodelverse.in).
Your mission is to craft viral, high-retention short scripts that explain frontier AI architectures as an INTELLECTUAL THRILLER.
Style: Fireship's snappy developer realism + 3Blue1Brown's mechanical geometric intuition + Veritasium's high-stakes narrative tension.

STRICT CONSTRAINTS & BANNED PATTERNS:
1. BAN TEXTBOOK SUMMARIES & LECTURE INTROS:
   - NEVER start with "Today we explore...", "In this paper...", "In this video...", or "The authors propose...".
   - Treat those as immediate swipe-aways. Every word in the first 3 seconds must create intense curiosity or high-stakes friction.
2. BAN AI SLOP & BABY-TALK METAPHORS:
   - Strictly forbidden: "smart tool", "safe drawers", "open desk", "magic box", "delve into", "tapestry", "game changer".
   - Name REAL developer tools and hardware: Cursor, Claude 3.5, PyTorch, vLLM, H100, Hopper, CUDA, AST, Git, KV Cache.
3. GROUNDING IN A VISCERAL PHYSICAL ANALOGY:
   - Ground the core bottleneck in ONE tangible, memorable physical analogy (e.g., chef waiting for salt before chopping every onion, relay race baton drop, highway lane closure, TV static, sculpting marble).

THE 4-ACT INTELLECTUAL THRILLER NARRATIVE ARC (EXACTLY 6 BEATS, 125-155 WORDS TOTAL):
- ACT 1: ABSURD PARADOX / PATTERN INTERRUPT HOOK (Beat 1, 0-3s, 12-18 words):
  * State a shocking paradox, counter-intuitive fact, or massive compute waste.
  * Hook the viewer in under 3 seconds before their thumb can swipe.
  * Example: "Every single time Cursor or Claude writes code for you, your GPU wastes up to 70% of its compute doing nothing."
- ACT 2: THE VILLAIN & BOTTLENECK (Beat 2, 3-15s, 20-26 words):
  * Personify the villain / mechanical bottleneck holding back AI.
  * Anchor in a vivid physical analogy.
  * Example: "Why? Because LLMs generate code one single token at a time—like a world-class chef who stops to ask you for salt before chopping every single onion."
- ACT 3: THE EUREKA GEOMETRIC MECHANISM (Beats 3 & 4, 15-40s):
  * Beat 3 (The Eureka Pivot, 20-25 words): The clean architectural breakthrough that shatters the bottleneck.
    Example: "Enter Speculative Decoding: a tiny draft model guesses five lines ahead in a millisecond, and the giant model verifies all five in a single forward pass."
  * Beat 4 (The Technical Deep-Dive / Secret Sauce, 20-25 words): The paper's specific algorithmic trick using real engineering terms.
    Example: "This paper supercharges it by pulling matching syntax directly from your repo's AST and git history, shooting draft acceptance up by 40%."
- ACT 4: THE PARADIGM SHIFT / OPEN LOOP (Beats 5 & 6, 40-50s):
  * Beat 5 (Empirical Victory Payoff, 18-24 words): Hard benchmark numbers proving the paradigm shift.
    Example: "The result? 4x faster coding agents without losing a single drop of benchmark accuracy."
  * Beat 6 (The Paradigm Shift & Seamless Loop, 15-20 words): Mind-expanding takeaway that naturally loops back to Beat 1.
    Example: "Follow The Model Verse for daily deep-dives into how modern AI actually works under the hood."

JSON OUTPUT SCHEMA:
Return ONLY valid JSON matching this specification:
{
  "id": "slug_id",
  "title": "Display Title",
  "category": "mechanism_deepdive | benchmark_news | architecture_breakdown | model_showdown",
  "domain_taxonomy": "hardware_efficiency | multimodal_diffusion | robotics_tamp | neural_sae | neural_attention | neural_moe | algorithmic_search",
  "hook_tag": "SHORT PUNCHY BADGE",
  "thriller_metadata": {
    "engine_version": "7.0",
    "narrative_style": "intellectual_thriller",
    "villain_entity": "Name of villain bottleneck (e.g. Sequential Token Serialization)",
    "physical_analogy": "Description of analogy (e.g. chef waiting for salt)",
    "eureka_mechanism": "Name of architectural breakthrough",
    "paradigm_shift": "The new reality established by this breakthrough"
  },
  "beats": [
    {
      "beat_id": 1,
      "act": 1,
      "thriller_role": "pattern_interrupt_hook",
      "text": "spoken voiceover text under 18 words",
      "visual_focus": "chalkboard visual description",
      "highlight_words": {"key phrase": "#EF4444"},
      "svo_action": {
        "subject": "GPU Chip",
        "action_verb": "wastes",
        "direct_object": "70% compute",
        "anchor_word": "wastes",
        "semantic_role": "state_transition"
      },
      "visual_blueprint": {
        "layout": "grid_memory | split_flow | vector_flow_field | neural_activation_wave | chalkboard_code_block | horizontal_race_bars | etc",
        "title": "UPPERCASE TITLE",
        "sub": "Subtext",
        "accent_color": "#EF4444",
        "params": {}
      }
    }
    // beats 2 to 6...
  ]
}
"""


class IntellectualThrillerEngine:
    """
    Next-Generation Narrative Engine (Engine 7.0).
    Enforces the 4-act intellectual thriller storytelling arc and provides
    both LLM-based and deterministic script rewriting for educational AI shorts.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def audit_thriller_compliance(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audits a candidate script against the 4-Act Intellectual Thriller standard.
        Checks for:
          1. Absence of textbook lecture clichés (Beat 1 & overall)
          2. Pattern interrupt hook quality in Beat 1 (first 3 seconds)
          3. Identification of a concrete villain & physical analogy (Beat 2)
          4. Eureka mechanism & secret sauce (Beats 3 & 4)
          5. Concrete payoff numbers & open loop (Beats 5 & 6)
          6. Overall pacing and word count
        """
        beats = spec.get("beats", [])
        total_beats = len(beats)
        full_text = " ".join([b.get("text", "") for b in beats]).lower()
        
        detected_textbook_phrases = []
        for cliche in TEXTBOOK_LECTURE_CLICHES:
            if cliche in full_text:
                detected_textbook_phrases.append(cliche)

        b1_text = beats[0].get("text", "").lower() if beats else ""
        b2_text = beats[1].get("text", "").lower() if len(beats) > 1 else ""
        b5_text = beats[4].get("text", "").lower() if len(beats) > 4 else ""
        b6_text = beats[5].get("text", "").lower() if len(beats) > 5 else ""

        # Check Beat 1: Pattern Interrupt Hook
        b1_words = len(b1_text.split())
        b1_has_textbook = any(cl in b1_text for cl in TEXTBOOK_LECTURE_CLICHES)
        b1_has_curiosity = any(w in b1_text for w in [
            "waste", "wasting", "every", "nobody", "wrong", "trap", "stalling", "lying",
            "broke", "dying", "70%", "80%", "90%", "secret", "why", "shocking", "million",
            "gpu", "cursor", "claude", "chatgpt", "ai", "your"
        ])
        hook_passed = (b1_words <= 22) and (not b1_has_textbook) and b1_has_curiosity

        # Check Beat 2: The Villain & Physical Analogy
        analogy_keywords = ["like a", "like an", "chef", "onion", "salt", "traffic", "highway", "baton", "relay", "static", "marble", "waiter", "cashier", "sponge"]
        has_analogy = any(ak in b2_text for ak in analogy_keywords) or bool(spec.get("thriller_metadata", {}).get("physical_analogy"))
        has_villain = any(w in b2_text for w in ["bottleneck", "why?", "because", "wait", "stall", "sequential", "memory", "wall", "stuck"]) or bool(spec.get("thriller_metadata", {}).get("villain_entity"))
        act2_passed = has_analogy or has_villain

        # Check Beat 5: Empirical Payoff Numbers
        has_payoff_numbers = any(c in b5_text for c in ["x", "%", "faster", "speedup", "tflops", "benchmark", "accuracy", "zero"])

        # Check Beat 6: Loop / Follow Outro
        has_outro_loop = any(w in b6_text for w in ["follow", "the model verse", "daily", "under the hood", "next"])

        # Compute Thriller Score
        score = 8.5
        if detected_textbook_phrases:
            score -= 3.0 * len(detected_textbook_phrases)
        if not hook_passed:
            score -= 2.0
        if not act2_passed:
            score -= 1.5
        if not has_payoff_numbers:
            score -= 1.0
        if not has_outro_loop:
            score -= 0.5
        if total_beats == 6:
            score += 0.5

        score = max(1.0, min(10.0, round(score, 1)))
        passed = score >= 8.0 and not detected_textbook_phrases and hook_passed

        return {
            "score": score,
            "passed": passed,
            "detected_textbook_phrases": detected_textbook_phrases,
            "hook_passed": hook_passed,
            "act2_villain_passed": act2_passed,
            "act4_payoff_passed": has_payoff_numbers,
            "b1_word_count": b1_words,
            "total_beats": total_beats,
            "verdict": "APPROVED: High-tempo Intellectual Thriller" if passed else f"REJECTED: Needs thriller rewrite (Score {score}/10)"
        }

    def rewrite_script_to_thriller(
        self,
        spec: Dict[str, Any],
        paper_meta: Optional[Dict[str, Any]] = None,
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        Rewrites a script spec into the 4-Act Intellectual Thriller narrative model.
        Uses Gemini if available; otherwise applies deterministic heuristic transformation.
        """
        title = spec.get("title", "AI Architecture Breakdown")
        topic = title
        category = spec.get("category", "mechanism_deepdive")
        domain = spec.get("domain_taxonomy", "hardware_efficiency")

        # 1. Try Gemini LLM Rewrite if API key is present
        if use_llm and self.api_key and genai:
            candidate_models = [
                os.getenv("GEMINI_MODEL_NAME", "gemini-flash-latest"),
                "gemini-3.1-flash-lite",
                "gemini-flash-latest",
                "gemini-2.5-flash",
                "gemini-2.0-flash"
            ]
            
            prompt_input = {
                "current_title": title,
                "category": category,
                "domain": domain,
                "existing_beats": [b.get("text", "") for b in spec.get("beats", [])],
                "paper_title": paper_meta.get("title") if paper_meta else None,
                "abstract": paper_meta.get("abstract") if paper_meta else None,
            }

            user_prompt = f"""
REWRITE THIS SCRIPT AS A HIGH-TEMPO 4-ACT INTELLECTUAL THRILLER:
Input Specification:
{json.dumps(prompt_input, indent=2)}

STRICT RULES:
1. Eradicate all textbook summaries and lecture introductions ("Today we explore...").
2. Beat 1 MUST be a 0-3s (under 18 words) absurd paradox or pattern interrupt hook.
3. Beat 2 MUST establish the villain & bottleneck with ONE vivid physical analogy (chef, relay race, etc.).
4. Beats 3 & 4 MUST reveal the eureka mechanism and technical secret sauce.
5. Beat 5 MUST deliver concrete payoff numbers.
6. Beat 6 MUST be a crisp outro looping back to Beat 1.
7. Return exactly 6 beats adhering to the required JSON schema.
"""
            for m_name in candidate_models:
                try:
                    model = genai.GenerativeModel(
                        m_name,
                        system_instruction=INTELLECTUAL_THRILLER_SYSTEM_PROMPT,
                        generation_config={"response_mime_type": "application/json", "temperature": 0.3}
                    )
                    resp = model.generate_content(user_prompt)
                    if resp and resp.text:
                        parsed = robust_json_loads(resp.text)
                        if parsed and "beats" in parsed and len(parsed["beats"]) >= 5:
                            return self._merge_thriller_updates(spec, parsed)
                except Exception:
                    continue

        # 2. Resilient Deterministic Rewrite
        return self._apply_deterministic_thriller_rewrite(spec, paper_meta)

    def _merge_thriller_updates(self, original_spec: Dict[str, Any], rewritten: Dict[str, Any]) -> Dict[str, Any]:
        """Merges rewritten thriller beats while preserving custom layouts, code snippets, and SVGs."""
        new_spec = dict(original_spec)
        new_spec["thriller_metadata"] = rewritten.get("thriller_metadata", {
            "engine_version": "7.0",
            "narrative_style": "intellectual_thriller"
        })

        if "hook_tag" in rewritten:
            new_spec["hook_tag"] = rewritten["hook_tag"]

        orig_beats = new_spec.get("beats", [])
        new_beats = rewritten.get("beats", [])

        # Ensure exactly 6 beats
        merged_beats = []
        for i in range(min(len(orig_beats), len(new_beats))):
            ob = dict(orig_beats[i])
            nb = new_beats[i]

            ob["text"] = nb.get("text", ob.get("text", ""))
            ob["thriller_role"] = nb.get("thriller_role", self._get_default_thriller_role(i + 1))
            ob["act"] = self._get_act_number(i + 1)
            
            if nb.get("visual_focus"):
                ob["visual_focus"] = nb["visual_focus"]
            if nb.get("highlight_words"):
                ob["highlight_words"] = nb["highlight_words"]
            if nb.get("svo_action"):
                ob["svo_action"] = nb["svo_action"]

            # Merge blueprint titles if available
            if nb.get("visual_blueprint") and ob.get("visual_blueprint"):
                nb_bp = nb["visual_blueprint"]
                if nb_bp.get("title"):
                    ob["visual_blueprint"]["title"] = nb_bp["title"]
                if nb_bp.get("sub"):
                    ob["visual_blueprint"]["sub"] = nb_bp["sub"]
            elif nb.get("visual_blueprint") and not ob.get("visual_blueprint"):
                ob["visual_blueprint"] = nb["visual_blueprint"]

            merged_beats.append(ob)

        # Pad up to 6 beats if needed
        while len(merged_beats) < 6:
            bid = len(merged_beats) + 1
            merged_beats.append(self._generate_fallback_beat(bid, new_spec.get("title", "AI Architecture")))

        new_spec["beats"] = merged_beats
        return new_spec

    def _apply_deterministic_thriller_rewrite(
        self,
        spec: Dict[str, Any],
        paper_meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Deterministic, rule-based transformation:
        Eliminates textbook openings, injects high-stakes curiosity into Beat 1,
        structures the villain and analogy in Beat 2, and validates thriller roles.
        """
        updated = dict(spec)
        topic = updated.get("title", "Modern AI Architecture")
        clean_topic = re.sub(r'[^a-zA-Z0-9\s]', '', topic).strip()
        beats = updated.get("beats", [])

        # If beats empty or incomplete, initialize standard 6-beat template
        if len(beats) < 6:
            beats = [self._generate_fallback_beat(i + 1, clean_topic) for i in range(6)]

        # --- ACT 1: Transform Beat 1 into Absurd Paradox / Pattern Interrupt Hook ---
        b1 = beats[0]
        b1_raw = b1.get("text", "")
        # Remove any textbook prefixes
        for cl in TEXTBOOK_LECTURE_CLICHES:
            if b1_raw.lower().startswith(cl):
                b1_raw = b1_raw[len(cl):].lstrip(" :,.-")

        # If Beat 1 was a dry summary, inject pattern interrupt hook
        if not any(w in b1_raw.lower() for w in ["waste", "70%", "wasting", "every single time", "bottleneck", "paradox"]):
            b1["text"] = f"Every single time Cursor or Claude writes code for you, your GPU wastes up to 70% of its compute doing nothing."
            b1["highlight_words"] = {"wastes up to 70%": "#EF4444", "compute": "#38BDF8"}
        else:
            b1["text"] = b1_raw

        b1["thriller_role"] = "pattern_interrupt_hook"
        b1["act"] = 1
        b1["svo_action"] = b1.get("svo_action", {
            "subject": "GPU Chip",
            "action_verb": "wastes",
            "direct_object": "Compute Cycles",
            "anchor_word": "wastes",
            "semantic_role": "state_transition"
        })

        # --- ACT 2: Transform Beat 2 into Villain & Bottleneck with Physical Analogy ---
        b2 = beats[1]
        b2_raw = b2.get("text", "")
        if not any(w in b2_raw.lower() for w in ["like a", "like an", "chef", "onion", "salt", "traffic", "relay"]):
            b2["text"] = f"Why? Because LLMs generate code one single token at a time—like a world-class chef who stops to ask you for salt before chopping every onion."
            b2["highlight_words"] = {"one single token": "#F59E0B", "stops to ask": "#EF4444"}
        b2["thriller_role"] = "villain_bottleneck"
        b2["act"] = 2
        b2["svo_action"] = b2.get("svo_action", {
            "subject": "Sequential Serialization",
            "action_verb": "stalls",
            "direct_object": "Token Generation",
            "anchor_word": "stops",
            "semantic_role": "bottleneck"
        })

        # --- ACT 3: Transform Beats 3 & 4 into Eureka Mechanism & Secret Sauce ---
        b3 = beats[2]
        b3_raw = b3.get("text", "")
        for cl in TEXTBOOK_LECTURE_CLICHES:
            if cl in b3_raw.lower():
                pattern = re.compile(re.escape(cl), re.IGNORECASE)
                b3_raw = pattern.sub(f"Enter {clean_topic}:", b3_raw)
        b3["text"] = b3_raw.strip()
        b3["thriller_role"] = "eureka_mechanism"
        b3["act"] = 3

        b4 = beats[3]
        b4_raw = b4.get("text", "")
        for cl in TEXTBOOK_LECTURE_CLICHES:
            if cl in b4_raw.lower():
                pattern = re.compile(re.escape(cl), re.IGNORECASE)
                b4_raw = pattern.sub("Under the hood,", b4_raw)
        b4["text"] = b4_raw.strip()
        b4["thriller_role"] = "technical_secret_sauce"
        b4["act"] = 3

        # --- ACT 4: Transform Beats 5 & 6 into Paradigm Shift Payoff & Open Loop ---
        b5 = beats[4]
        b5["thriller_role"] = "empirical_payoff"
        b5["act"] = 4
        if not any(c in b5.get("text", "").lower() for c in ["x", "%", "faster", "speedup"]):
            b5["text"] = f"The result? 4x faster coding agents without losing a single drop of benchmark accuracy."
            b5["highlight_words"] = {"4x faster": "#10B981", "benchmark accuracy": "#38BDF8"}

        b6 = beats[5]
        b6["thriller_role"] = "open_loop_outro"
        b6["act"] = 4
        if not any(w in b6.get("text", "").lower() for w in ["follow", "the model verse"]):
            b6["text"] = "Follow The Model Verse for daily deep-dives into how modern AI actually works under the hood."
            b6["highlight_words"] = {"The Model Verse": "#34D399"}

        # --- Sanitize any lingering textbook clichés across all beats ---
        for b in beats:
            b_text = b.get("text", "")
            for cl in TEXTBOOK_LECTURE_CLICHES:
                if cl in b_text.lower():
                    pattern = re.compile(re.escape(cl), re.IGNORECASE)
                    b_text = pattern.sub("this breakthrough introduces", b_text)
            b["text"] = b_text.strip()

        updated["beats"] = beats
        updated["thriller_metadata"] = {
            "engine_version": "7.0",
            "narrative_style": "intellectual_thriller",
            "acts": {
                "act_1_hook": {"beat": 1, "role": "pattern_interrupt_hook"},
                "act_2_villain": {"beat": 2, "role": "villain_bottleneck", "analogy": "chef waiting for salt"},
                "act_3_eureka": {"beats": [3, 4], "role": "eureka_mechanism"},
                "act_4_paradigm_shift": {"beats": [5, 6], "role": "paradigm_shift_open_loop"}
            }
        }
        return updated

    def _get_act_number(self, beat_id: int) -> int:
        if beat_id == 1:
            return 1
        elif beat_id == 2:
            return 2
        elif beat_id in (3, 4):
            return 3
        return 4

    def _get_default_thriller_role(self, beat_id: int) -> str:
        roles = {
            1: "pattern_interrupt_hook",
            2: "villain_bottleneck",
            3: "eureka_mechanism",
            4: "technical_secret_sauce",
            5: "empirical_payoff",
            6: "open_loop_outro"
        }
        return roles.get(beat_id, "narrative_beat")

    def _generate_fallback_beat(self, beat_id: int, topic: str) -> Dict[str, Any]:
        defaults = {
            1: {
                "beat_id": 1, "act": 1, "thriller_role": "pattern_interrupt_hook",
                "text": "Every single time you run modern AI models, your GPU wastes up to 70% of its compute doing nothing.",
                "visual_focus": "Pulsing GPU memory bus stalling on memory latency.",
                "highlight_words": {"wastes up to 70%": "#EF4444", "compute": "#38BDF8"},
                "svo_action": {"subject": "GPU Memory", "action_verb": "wastes", "direct_object": "Compute Cycles", "anchor_word": "wastes", "semantic_role": "state_transition"},
                "visual_blueprint": {"layout": "grid_memory", "title": "HARDWARE BOTTLENECK", "sub": "Compute units idle waiting for VRAM", "accent_color": "#EF4444", "params": {}}
            },
            2: {
                "beat_id": 2, "act": 2, "thriller_role": "villain_bottleneck",
                "text": "Why? Because LLMs generate code one token at a time—like a chef who stops to ask you for salt before chopping every onion.",
                "visual_focus": "Sequential token generation ladder showing single word emits followed by long idle wait states.",
                "highlight_words": {"one token at a time": "#F59E0B", "stops to ask": "#EF4444"},
                "svo_action": {"subject": "LLM Decoder", "action_verb": "delays", "direct_object": "Token Generation", "anchor_word": "stops", "semantic_role": "bottleneck"},
                "visual_blueprint": {"layout": "vector_flow_field", "title": "SEQUENTIAL BOTTLENECK", "sub": "Autoregressive serialization stalls throughput", "accent_color": "#F59E0B", "params": {}}
            },
            3: {
                "beat_id": 3, "act": 3, "thriller_role": "eureka_mechanism",
                "text": f"Enter {topic[:24]}. A tiny draft model guesses five lines ahead, while the giant model verifies all five in one single pass.",
                "visual_focus": "Dual parallel pipelines showing fast speculative draft branch feeding a single verification pass.",
                "highlight_words": {"verifies all five": "#38BDF8", "single pass": "#10B981"},
                "svo_action": {"subject": "Draft Engine", "action_verb": "speculates", "direct_object": "Token Stream", "anchor_word": "verifies", "semantic_role": "mechanism"},
                "visual_blueprint": {"layout": "split_flow", "title": "PARALLEL DRAFT PIPELINE", "sub": "Multi-token speculative verification", "accent_color": "#10B981", "params": {}}
            },
            4: {
                "beat_id": 4, "act": 3, "thriller_role": "technical_secret_sauce",
                "text": "This paper pushes it further by pulling matching syntax directly from your repo's AST, shooting draft acceptance up by 40%.",
                "visual_focus": "Syntax code block extracting AST subtrees and auto-filling speculative candidate tokens.",
                "highlight_words": {"repo's AST": "#38BDF8", "up by 40%": "#10B981"},
                "svo_action": {"subject": "AST Kernel", "action_verb": "retrieves", "direct_object": "Syntax Tree", "anchor_word": "shooting", "semantic_role": "innovation"},
                "visual_blueprint": {"layout": "chalkboard_code_block", "title": "AST SYNTAX RETRIEVAL", "sub": "Live syntax tree speculative cache", "accent_color": "#38BDF8", "params": {}}
            },
            5: {
                "beat_id": 5, "act": 4, "thriller_role": "empirical_payoff",
                "text": "The result? 4x faster coding agents without losing a single drop of benchmark accuracy.",
                "visual_focus": "Horizontal benchmark race bars showing 4x latency reduction and identical accuracy.",
                "highlight_words": {"4x faster": "#10B981", "benchmark accuracy": "#38BDF8"},
                "svo_action": {"subject": "Benchmark Metric", "action_verb": "accelerates", "direct_object": "Throughput", "anchor_word": "faster", "semantic_role": "victory"},
                "visual_blueprint": {"layout": "horizontal_race_bars", "title": "BENCHMARK SPEEDUP", "sub": "4x latency drop with zero accuracy loss", "accent_color": "#10B981", "params": {}}
            },
            6: {
                "beat_id": 6, "act": 4, "thriller_role": "open_loop_outro",
                "text": "Follow The Model Verse for daily deep-dives into how modern AI actually works under the hood.",
                "visual_focus": "Chalkboard brand logo with glowing cyan rings, subscribe badge, and loop transition.",
                "highlight_words": {"The Model Verse": "#34D399"},
                "svo_action": {"subject": "Viewer", "action_verb": "follows", "direct_object": "The Model Verse", "anchor_word": "daily", "semantic_role": "loop"},
                "visual_blueprint": {"layout": "neural_activation_wave", "title": "THE MODEL VERSE", "sub": "Daily AI Architecture & Research Breakdowns", "accent_color": "#34D399", "params": {}}
            }
        }
        return defaults.get(beat_id, defaults[1])


# Global Singleton Instance
intellectual_thriller_engine = IntellectualThrillerEngine()
