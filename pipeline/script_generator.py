"""
The Model Verse — Autonomous LLM Script & Content Ingestion Engine
Generates broadcast-grade 6-beat educational short specifications using Gemini 2.5 Flash.
Supports topic names, model profiles, and direct arXiv paper URLs / IDs.
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=FutureWarning)
    import google.generativeai as genai

from pipeline.json_utils import robust_json_loads
from pipeline.arxiv_fetcher import fetch_arxiv_paper
from scripts.generate_math_svgs import render_math_to_svg

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-flash-latest")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is not configured in .env")

genai.configure(api_key=API_KEY)

CATEGORIES = ["architecture_breakdown", "model_showdown", "mechanism_deepdive", "benchmark_news"]

SCRIPT_DIRECTIVES = """
You are the Lead AI Research Director and Technical Scriptwriter for 'The Model Verse' (themodelverse.in).
Your job is to craft high-retention, educational short scripts explaining frontier AI architectures and mechanisms.

Aesthetic & Pedagogical Philosophy (Fireship meets 3Blue1Brown & Feynman):
- Ground abstract AI in real developer tools and crisp physical analogies:
  * Name REAL tools, models, frameworks, and hardware: Cursor, Claude 3.5, ChatGPT, PyTorch, vLLM, H100, Hopper, Python, Git.
  * Use standard developer terms that real engineers use: GPU, tokens, RAM, latency, bandwidth, sequential generation, AST, KV cache.
  * NEVER use dumbed-down AI slop or baby-talk metaphors: strictly ban 'smart tool', 'safe drawers', 'open desk', 'magic box'. Real developers and curious students cringe at these!
  * Ground the abstract bottleneck in ONE vivid, relatable physical analogy: (e.g. a chef waiting between ingredients, a relay race baton pass, highway traffic jams, TV static, chipping marble, library card catalog).
- AVOID UNEXPLAINED ACADEMIC JARGON:
  * Don't drop raw unexplained math like 'asynchronous GEMM warp specialization' or 'non-convex loss topology'.
  * Instead, state what it physically does: 'threads run side-by-side without stalling each other'.
- Pacing: Exactly 6 beats. Each beat MUST be 20 to 26 words maximum (around 7-9 seconds of natural, conversational speech).
- DUAL-CADENCE SENTENCE STRUCTURE (Sync with Visual Action):
  * Every beat should follow a dual-cadence rhythm: [Setup Clause] + [Action Trigger Clause].
  * The [Action Trigger Clause] contains the `anchor_word` where on-screen physical action fires.
- Auditory-Visual Complementarity: The voiceover carries relatable intuition and metaphors; the chalkboard screen illustrates the living geometry, physical fields, and mechanical state.

The 6-Beat Narrative Arc:
1. Beat 1 (Hook, 0-5s): Start with a bold, high-stakes curiosity loop or shocking inefficiency.
   Example: 'Every time Cursor or Claude writes code for you, your GPU is wasting up to 70% of its compute doing absolutely nothing.'
2. Beat 2 (The Visceral Problem / Analogy, 5-13s): Explain WHY this bottleneck happens using ONE clear, relatable physical analogy.
   Example: 'Why? Because LLMs generate code one token at a time—like a world-class chef who stops to ask you for salt before chopping every single onion.'
3. Beat 3 (The Core Breakthrough Mechanism, 13-21s): Introduce the actual architectural innovation simply and cleanly.
   Example: 'Enter Speculative Decoding: a tiny draft model guesses five lines ahead in a millisecond, and the giant model verifies all five in a single pass.'
4. Beat 4 (The Technical Deep-Dive / Paper Innovation, 21-29s): Explain the paper's specific secret sauce with real developer terms.
   Example: 'This paper supercharges it by pulling matching syntax directly from your repo\'s AST and git history, shooting draft acceptance up by 40%.'
5. Beat 5 (Empirical Victory / Benchmark Payoff, 29-37s): Deliver the concrete payoff with numbers.
   Example: 'The result? 4x faster coding agents without losing a single drop of benchmark accuracy.'
6. Beat 6 (Takeaway / Seamless Loop, 37-41s): Crisp outro that naturally loops back to Beat 1.
   Example: 'Follow The Model Verse for daily deep-dives into how modern AI actually works under the hood.'

Highlight Words Rules:
- For each beat, select 1 to 3 critical technical keywords from the beat text to highlight.
- Map them to one of these exact hex colors:
  * Mint (efficiency/success/The Model Verse): "#34D399"
  * Danger Red (bottlenecks/explosions/costs): "#EF4444"
  * Cyan (routing/queries/weights): "#38BDF8"
  * Gold (key metrics/numbers/shared): "#F59E0B"
  * White (standard bold emphasis): "#FFFFFF"

DEDICATED 5-BEAT MATHEMATICAL FORMULAS (STRICT REQUIREMENT):
- You MUST provide EXACTLY 5 distinct, beat-tailored mathematical formulas in `math_formulas` (one for each beat from Beat 1 to Beat 5).
- NEVER reuse or repeat a formula. Every beat must have its own fresh equation directly matching the spoken narrative:
  * Formula 0 (Beat 1): Foundational scale / dimensionality / hypothesis (e.g. '$d_{\\mathrm{model}} = 4096 \\to d_{\\mathrm{SAE}} = 32{,}768$' or '$N = 671 \\times 10^9$').
  * Formula 1 (Beat 2): The Bottleneck / Superposition / Complexity equation (e.g. '$\\mathbf{x} = \\sum_{i=1}^M \\alpha_i \\mathbf{v}_i$' or '$\\mathcal{O}(N^2)$').
  * Formula 2 (Beat 3): The Architectural Decomposition / Dictionary / Projection equation (e.g. '$\\mathbf{f}(x) = \\mathrm{ReLU}(\\mathbf{W}_e x + b_e)$' or '$W \\to \\{E_1, \\dots, E_{256}\\}$').
  * Formula 3 (Beat 4): The Operational Mechanism / Gating / Latent Partition equation (e.g. '$\\mathcal{C}_{\\mathrm{POS}} = \\{k \\mid f_k(x) > \\tau\\}$' or '$\\mathrm{Top8}(\\sigma(W_g x))$').
  * Formula 4 (Beat 5): The Quantitative Proof / Metric / Accuracy equation (e.g. '$\\mathrm{Accuracy}_{\\mathrm{POS}} = 98.2\\%$' or '$94.5\\% \\text{ Compute Saved}$').
- Compatibility constraint: Use valid Matplotlib math mode (wrapped in $). Use `\\mathrm{...}` for words (do NOT use `\\text{...}` inside math). DO NOT use `\\underbrace`, `\\overbrace`, or undefined packages.
- For each formula, provide 1 to 2 `term_annotations` explaining the variables (e.g. `[{"term": "f(x)", "label": "Sparse Latents"}, {"term": "W_e", "label": "32k Dictionary"}]`).

DYNAMIC VISUAL METAPHOR, SVO TRIPLES & ENTITIES (STRICT REQUIREMENT):
- `domain_taxonomy`: Choose exactly one matching domain from:
  * "multimodal_diffusion" (Diffusion denoising, flow matching, latent trajectories, visual generation, video dynamics)
  * "hardware_efficiency" (KV cache compression, FlashAttention, quantization FP8/FP4, SRAM/VRAM bandwidth, latency)
  * "robotics_tamp" (Task & Motion Planning, robotic kinematics, C-space manifolds, code synthesis ASTs)
  * "neural_sae" (Sparse Autoencoders, dictionary expansion, polysemantic latents)
  * "neural_attention" (Transformer multi-head Q/K/V routing, attention heatmaps, KV cache)
  * "neural_moe" (Mixture of Experts, router gate, load balancing)
  * "algorithmic_search" (MCTS, tree search, branch-and-bound pruning, A*)
  * "quantitative_benchmark" (Model vs Model showdown, accuracy metrics, speedups)
- In EACH of the 6 beats, you MUST provide an `svo_action` triple linking the spoken narration to on-screen physical action:
  * `subject`: The agent or system component executing the action (e.g. "Kinematic Planner", "Router Gate", "SAE Dictionary").
  * `action_verb`: The concrete physical/mechanical action (e.g. "prunes", "dispatches", "projects", "synthesizes", "bounds").
  * `direct_object`: The geometric entity being acted upon (e.g. "Collision Trajectory", "Top-8 Experts", "Latent Activation Vector").
  * `anchor_word`: The exact word in the beat text whose vocalization triggers the visual action.
DEDICATED FULL-SCREEN VISUAL BLUEPRINTS (CRITICAL ARCHITECTURAL DIRECTIVE):
- For EACH beat (Beats 1 to 5), you MUST specify a structured `visual_blueprint` dict that dictates what Manim composable layout to render on screen.
- Choose the layout that DIRECTLY visualizes the spoken analogy and mechanism.
- VISUAL ENGINE 5.0 LIVING PHYSICS & GEOMETRIC SIMULATORS (PREFER THESE FOR FRONTIER PAPERS):
  * "vector_flow_field": For continuous latent trajectories, diffusion denoising drift, flow matching velocity fields, or smooth state-space transitions.
    params: {"field_title": "...", "source_label": "...", "target_label": "...", "stream_formula": "..."}
  * "neural_activation_wave": For multi-layer deep network forward passes, cascading synaptic firing, electrical feature propagation, or deep layer activations.
    params: {"input_label": "...", "hidden_label": "...", "output_label": "..."}
  * "attention_prism_refraction": For optical token splitting, refracting a dense input embedding into Query/Key/Value vectors, and projecting onto an attention heatmap.
    params: {"token_label": "...", "matrix_title": "..."}
  * "optimization_landscape": For 2.5D loss surfaces, energy basins, gradient descent optimization paths, or ball rolling into the global minimum.
    params: {"landscape_title": "...", "optima_label": "..."}
- STRUCTURAL & FLOW COMPOSITIONS:
  * "split_flow": For bifurcated paths, dual decoders, splitting high-level semantics from low-level geometry/depth, or 2-way routing.
    params: {"input_label": "...", "router_label": "...", "branch_a_label": "...", "branch_a_sub": "...", "branch_b_label": "...", "branch_b_sub": "..."}
  * "pipeline_stages": For multi-step processing, sequential pipelines, or ingestion -> transformation -> reconstruction.
    params: {"stage_1_label": "...", "stage_1_sub": "...", "stage_2_label": "...", "stage_2_sub": "...", "stage_3_label": "...", "stage_3_sub": "..."}
  * "grid_memory": For spatial memory, KV-cache buffers, coordinate matrices, voxel arrays, or O(1) latency lookup.
    params: {"grid_title": "...", "active_cell_label": "...", "efficiency_label": "..."}
  * "projection_rays": For camera math, perspective ray-casting, world coordinates, sightline intersections, or 3D localization.
    params: {"camera_label": "...", "focal_plane_label": "...", "target_label": "..."}
  * "barrier_separation": For orthogonal penalties, isolating representations, preventing cross-talk, or walls between streams.
    params: {"stream_a_label": "...", "stream_b_label": "...", "barrier_label": "...", "barrier_sub": "..."}
  * "tree_hierarchy": For decision trees, MCTS search paths, exploration vs pruning, or reasoning chains.
    params: {"root_label": "...", "optimal_label": "...", "pruned_label": "..."}
  * "layer_stack": For hierarchical representations, stacking judgment layers, or deep latent abstractions.
    params: {"bottom_layer": "...", "mid_layer": "...", "top_layer": "..."}
  * "convergence_funnel": For multimodal fusion, combining text/vision/audio, or condensing multiple streams into one core.
    params: {"input_1_label": "...", "input_2_label": "...", "input_3_label": "...", "fused_label": "..."}
  * "catalog_routing": For library card catalogs, indexing desks, hash map lookups, or dispatching to specialized drawers.
    params: {"index_label": "...", "drawer_a_label": "...", "drawer_b_label": "...", "drawer_c_label": "..."}
  * "comparison_side_by_side": For contrasting two opposing approaches side-by-side (e.g. Traditional Flawed vs Breakthrough).
    params: {"col_a_title": "...", "col_a_stat": "...", "col_b_title": "...", "col_b_stat": "..."}
- NEVER reuse the same blueprint layout across beats in the same video. Every beat must have its own distinct visual layout!
"""

def generate_script(
    topic: str,
    category: Optional[str] = None,
    context: Optional[str] = None,
    arxiv_meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Invokes Gemini 2.5 Flash to generate a 6-beat JSON template with SVO alignment.
    """
    model = genai.GenerativeModel(
        MODEL_NAME,
        generation_config={"response_mime_type": "application/json"}
    )

    cat_hint = f"Target Category: {category}" if category else "Choose the best matching category from: architecture_breakdown, model_showdown, mechanism_deepdive, benchmark_news."

    paper_context = ""
    if arxiv_meta:
        paper_context = f"""
ArXiv Paper Details:
Title: {arxiv_meta['title']}
Authors: {', '.join(arxiv_meta.get('authors', []))}
Abstract: {arxiv_meta['abstract']}
"""

    prompt = f"""
{SCRIPT_DIRECTIVES}

Topic Request: {topic}
{cat_hint}
{paper_context}
{f'Extra Context: {context}' if context else ''}

Generate the complete JSON specification strictly adhering to this structure:
{{
  "id": "slug_topic_name",
  "title": "Clean Display Title",
  "category": "architecture_breakdown | model_showdown | mechanism_deepdive | benchmark_news",
  "domain_taxonomy": "multimodal_diffusion | hardware_efficiency | robotics_tamp | neural_sae | neural_attention | neural_moe | algorithmic_search | quantitative_benchmark",
  "hook_tag": "CATEGORY BADGE TITLE (UPPERCASE)",
  "beats": [
    {{
      "beat_id": 1,
      "text": "spoken voiceover text under 25 words",
      "visual_focus": "description of blackboard visual",
      "highlight_words": {{"word or phrase": "#HEX_COLOR"}},
      "svo_action": {{
        "subject": "Agent/Component Name",
        "action_verb": "physical_action_verb",
        "direct_object": "visual_geometric_target",
        "anchor_word": "trigger_word_in_text",
        "semantic_role": "agent_action | state_transition | causal_elimination | metric_evaluation"
      }},
      "visual_blueprint": {{
        "layout": "vector_flow_field | neural_activation_wave | attention_prism_refraction | optimization_landscape | split_flow | pipeline_stages | grid_memory | projection_rays | barrier_separation | tree_hierarchy | layer_stack | convergence_funnel | catalog_routing | comparison_side_by_side",
        "title": "CLEAR UPPERCASE CONCEPT TITLE",
        "sub": "Concise 1-line description of visual structure",
        "accent_color": "#38BDF8",
        "params": {{
          "param_key_1": "specific descriptive label",
          "param_key_2": "specific descriptive label"
        }}
      }}
    }}
  ],
  "math_formulas": [
    {{
      "beat_id": 1,
      "latex": "$LaTeX formula for Beat 1$",
      "filename": "slug_beat1_scale.svg",
      "fontsize": 24,
      "color": "#38BDF8",
      "term_annotations": [
        {{"term": "variable_1", "label": "Short Explanation"}},
        {{"term": "variable_2", "label": "Short Explanation"}}
      ]
    }},
    {{
      "beat_id": 2,
      "latex": "$LaTeX formula for Beat 2$",
      "filename": "slug_beat2_bottleneck.svg",
      "fontsize": 24,
      "color": "#EF4444",
      "term_annotations": [
        {{"term": "variable_1", "label": "Short Explanation"}}
      ]
    }},
    {{
      "beat_id": 3,
      "latex": "$LaTeX formula for Beat 3$",
      "filename": "slug_beat3_architecture.svg",
      "fontsize": 24,
      "color": "#34D399",
      "term_annotations": [
        {{"term": "variable_1", "label": "Short Explanation"}}
      ]
    }},
    {{
      "beat_id": 4,
      "latex": "$LaTeX formula for Beat 4$",
      "filename": "slug_beat4_mechanism.svg",
      "fontsize": 24,
      "color": "#F59E0B",
      "term_annotations": [
        {{"term": "variable_1", "label": "Short Explanation"}}
      ]
    }},
    {{
      "beat_id": 5,
      "latex": "$LaTeX formula for Beat 5$",
      "filename": "slug_beat5_payoff.svg",
      "fontsize": 24,
      "color": "#34D399",
      "term_annotations": [
        {{"term": "variable_1", "label": "Short Explanation"}}
      ]
    }}
  ],
  "sfx_cues": [
    {{ "timestamp": 0.8, "sound_type": "sub_impact", "volume": 0.45 }},
    {{ "timestamp": 5.2, "sound_type": "whoosh", "volume": 0.35 }},
    {{ "timestamp": 13.5, "sound_type": "whoosh", "volume": 0.35 }},
    {{ "timestamp": 21.5, "sound_type": "sub_impact", "volume": 0.40 }},
    {{ "timestamp": 29.5, "sound_type": "sub_impact", "volume": 0.50 }},
    {{ "timestamp": 37.0, "sound_type": "whoosh", "volume": 0.35 }},
    {{ "timestamp": 38.0, "sound_type": "chime", "volume": 0.40 }}
  ],
  "metadata": {{
    "visual_metaphor": "semantic_clusters | overcomplete_dictionary | neural_routing | attention_flow | hardware_memory_hierarchy | reasoning_tree",
    "visual_entities": {{
      "clusters": [
        {{"name": "[CATEGORY_A]", "color": "#38BDF8", "items": ["word1", "word2", "word3"]}},
        {{"name": "[CATEGORY_B]", "color": "#10B981", "items": ["word4", "word5", "word6"]}},
        {{"name": "[CATEGORY_C]", "color": "#F59E0B", "items": ["word7", "word8", "word9"]}}
      ],
      "incoming_token": {{
        "label": "Token: \\"sample_word\\"",
        "target_cluster": "CATEGORY_B",
        "token": "\\"sample_word\\""
      }},
      "bottleneck_tokens": [
        {{"word": "Token 'poly1'", "color": "#EF4444"}},
        {{"word": "Token 'poly2'", "color": "#F59E0B"}}
      ]
    }},
    "model_a": "Contender 1 Name (e.g. Coding Agents, Claude 3.7)",
    "model_a_specs": ["Short spec 1", "Short spec 2", "Short spec 3"],
    "model_b": "Contender 2 Name (e.g. Classical TAMP, GPT-4o)",
    "model_b_specs": ["Short spec 1", "Short spec 2", "Short spec 3"],
    "divide_title": "Short uppercase divide title (e.g. SEARCH VS POLICY DIVIDE)",
    "model_a_stat": "Contender 1 stat (e.g. 95%, 37B, 10x)",
    "model_a_stat_label": "Label under metric (e.g. TASK SUCCESS, ACTIVE PARAMS)",
    "model_b_stat": "Contender 2 stat (e.g. 47%, 1.8T, 1x)",
    "model_b_stat_label": "Label under metric (e.g. BASELINE SUCCESS, FULL WEIGHTS)",
    "efficiency_badge": "Badge text with emoji (e.g. ⚡ 10x COMPUTE REDUCTION)",
    "benchmarks": [
      {{"name": "Benchmark 1", "score_a": "95%", "score_b": "47%"}},
      {{"name": "Benchmark 2", "score_a": "10x", "score_b": "1x"}},
      {{"name": "Benchmark 3", "score_a": "High", "score_b": "Baseline"}}
    ],
    "scale_metric": "Hero number for Beat 1 (e.g. 16k, 671B, 100M)",
    "scale_label": "Label under hero number (e.g. Latent Features, Total Parameters)",
    "bottleneck_title": "Uppercase title for Beat 2 (e.g. MONOLITHIC BRUTE-FORCE BOTTLENECK)",
    "bottleneck_desc": "Short description for Beat 2 (e.g. Entangled Superposition)",
    "solution_title": "Uppercase title for Beat 3 (e.g. SPARSE AUTOENCODER PROJECTION)",
    "solution_components": "Components label for Beat 3 (e.g. Monosemantic Dictionary)",
    "mechanism_title": "Uppercase title for Beat 4 (e.g. STRUCTURED LATENT ACTIVATION)",
    "payoff_stat": "Hero stat for Beat 5 (e.g. 95%, 10x, 94.5%)",
    "payoff_label": "Uppercase label for Beat 5 (e.g. SUCCESS RATE, SPEEDUP)",
    "payoff_sub": "Subtext for Beat 5 (e.g. Outperforming Traditional Hand-Crafted Models)",
    "payoff_hero_stat": 98.2,
    "payoff_hero_label": "Sparse SAE Latents",
    "payoff_base_stat": 41.5,
    "payoff_base_label": "Dense Baseline",
    "payoff_delta_badge": "⚡ +56.7% SYNTACTIC RECOVERY GAIN",
    "challenger": "Challenger Name (for benchmark_news)",
    "incumbent": "Incumbent Name (for benchmark_news)"
  }},
  "benchmark_comparison": {{
    "title": "BENCHMARK SHOWDOWN: PRIMARY METRIC",
    "metric_name": "Throughput or Accuracy",
    "unit": "TFLOPS | % | tok/s | ms",
    "contestants": [
      {{"name": "Our Model", "value": 1180.0, "display_val": "1,180 TFLOPS", "is_hero": true, "color": "#10B981"}},
      {{"name": "Incumbent SOTA", "value": 660.0, "display_val": "660 TFLOPS", "is_hero": false, "color": "#38BDF8"}},
      {{"name": "Alternative Baselines", "value": 610.0, "display_val": "610 TFLOPS", "is_hero": false, "color": "#A855F7"}},
      {{"name": "Standard PyTorch", "value": 240.0, "display_val": "240 TFLOPS", "is_hero": false, "color": "#EF4444"}}
    ],
    "delta_badge": "⚡ +78.8% SOTA EFFICIENCY GAIN",
    "radar_axes": ["Throughput", "VRAM Efficiency", "Accuracy", "Context Length", "Cost Efficiency"]
  }},
  "code_snippet": {{
    "filename": "core_kernel.py",
    "language": "python",
    "lines": [
      "def execute_step(tensor_in):",
      "    node = self.root_cache",
      "    out = fused_forward_pass(tensor_in)",
      "    return synchronize(node, out)"
    ],
    "highlight_lines": [2, 3],
    "trace_register": "⚡ FUSED HARDWARE KERNEL EXECUTION",
    "explanation": "Zero memory-copy hardware acceleration"
  }}
}}
"""

    import time
    candidate_models = [
        MODEL_NAME,
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite-preview",
        "gemma-4-31b-it"
    ]
    # Remove duplicates preserving order
    seen = set()
    candidate_models = [m for m in candidate_models if not (m in seen or seen.add(m))]

    response = None
    last_err = None

    for m_idx, current_model_name in enumerate(candidate_models):
        print(f"🧠 Attempting script generation with model: '{current_model_name}'...")
        try:
            curr_model = genai.GenerativeModel(
                current_model_name,
                generation_config={"response_mime_type": "application/json"}
            )
            response = curr_model.generate_content(prompt)
            if response and response.text:
                print(f"✅ Script generated successfully using '{current_model_name}'")
                break
        except Exception as e:
            last_err = e
            err_msg = str(e)
            if "ResourceExhausted" in err_msg or "429" in err_msg or "404" in err_msg or "limit: 20" in err_msg:
                print(f"⚠️ Quota/Availability limit on '{current_model_name}'. Falling back to next available model...")
                time.sleep(2)
                continue
            else:
                print(f"⚠️ Error on '{current_model_name}': {e}. Trying fallback...")
                time.sleep(2)
                continue

    if not response or not response.text:
        raise RuntimeError(f"Failed to generate script from Gemini across all candidate models. Last error: {last_err}")

    raw_text = response.text.strip()

    try:
        spec = robust_json_loads(raw_text)
    except Exception as e:
        print("Raw LLM output:\n", raw_text)
        raise RuntimeError(f"Failed to parse LLM JSON: {e}")

    # Ensure ID slug is filesystem safe
    clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", spec.get("id", "short_topic")).lower()
    spec["id"] = clean_id

    # Guarantee exactly 6 beats (auto-append Beat 6 brand outro if omitted by LLM)
    if len(spec.get("beats", [])) == 5:
        spec["beats"].append({
            "beat_id": 6,
            "text": "Follow The Model Verse for simple explanations of how modern AI actually works.",
            "visual_focus": "Minimalist chalkboard outro with The Model Verse branding.",
            "highlight_words": {"The Model Verse": "#34D399"},
            "svo_action": {
                "subject": "The Model Verse",
                "action_verb": "demystifies",
                "direct_object": "Modern AI",
                "anchor_word": "Model",
                "semantic_role": "metric_evaluation"
            }
        })

    # Preserve curated code kernel and repo metadata if supplied by GitHub ingest
    if arxiv_meta and isinstance(arxiv_meta, dict):
        if arxiv_meta.get("code_snippet") and (not spec.get("code_snippet") or arxiv_meta.get("repo_metadata")):
            spec["code_snippet"] = arxiv_meta["code_snippet"]
        if arxiv_meta.get("repo_metadata"):
            spec["repo_metadata"] = arxiv_meta["repo_metadata"]

    # 2-Agent Socratic Feynman Dialogue Engine (TechScriptwriter + Curious Novice Listener)
    try:
        from pipeline.feynman_dialogue_engine import feynman_socratic_loop
        from pipeline.script_critic import ScriptCritic
        
        print("\n🎓 Launching 2-Agent Socratic Feynman Dialogue Engine (Writer + Novice Listener)...")
        paper_context_data = {
            "title": spec.get("title", topic),
            "summary": spec.get("beats", [{}])[0].get("text", "") if spec.get("beats") else topic,
            "abstract": (arxiv_meta.get("abstract", "") if arxiv_meta else "") or context or topic,
            "arxiv_id": (arxiv_meta.get("arxiv_id", "") if arxiv_meta else "") or (arxiv_meta.get("id", "") if arxiv_meta else ""),
            "category": spec.get("category", category or "mechanism_deepdive"),
            "domain": spec.get("domain_taxonomy", "hardware_efficiency"),
            "solution_title": spec.get("metadata", {}).get("solution_title", ""),
            "benchmark_stats": spec.get("benchmark_comparison", {}),
            "code_snippet": spec.get("code_snippet", {}).get("lines", []) if spec.get("code_snippet") else ""
        }
        if isinstance(paper_context_data["code_snippet"], list):
            paper_context_data["code_snippet"] = "\n".join(paper_context_data["code_snippet"])

        vetted_script, socratic_transcript = feynman_socratic_loop.run_socratic_loop(
            paper_data=paper_context_data,
            verbose=True
        )

        if vetted_script and vetted_script.get("beats"):
            vetted_beats = vetted_script["beats"]
            for idx, approved_beat in enumerate(vetted_beats):
                if idx < len(spec["beats"]):
                    spec["beats"][idx]["text"] = approved_beat.get("text", spec["beats"][idx]["text"])
                    if approved_beat.get("visual_focus"):
                        spec["beats"][idx]["visual_focus"] = approved_beat["visual_focus"]
                    if approved_beat.get("highlight_words"):
                        spec["beats"][idx]["highlight_words"] = approved_beat["highlight_words"]
                    if approved_beat.get("svo_action"):
                        spec["beats"][idx]["svo_action"] = approved_beat["svo_action"]
                    if approved_beat.get("visual_blueprint"):
                        existing_bp = spec["beats"][idx].get("visual_blueprint")
                        if not existing_bp or existing_bp.get("layout") in ("pipeline_stages", "default", None):
                            spec["beats"][idx]["visual_blueprint"] = approved_beat["visual_blueprint"]
                        else:
                            # Preserve rich existing layout, updating titles/subs if available
                            if approved_beat["visual_blueprint"].get("title"):
                                spec["beats"][idx]["visual_blueprint"]["title"] = approved_beat["visual_blueprint"]["title"]
                            if approved_beat["visual_blueprint"].get("sub"):
                                spec["beats"][idx]["visual_blueprint"]["sub"] = approved_beat["visual_blueprint"]["sub"]

            spec["feynman_certification"] = vetted_script.get("feynman_certification", {})
            cert = spec["feynman_certification"]
            print(f"🎉 Socratic Consensus Applied: Comprehension {cert.get('final_comprehension_score')}/10 | Hook {cert.get('final_retention_hook_score')}/10 | Slop Eliminated: {cert.get('ai_slop_eliminated')}")

        # Final safety audit with ScriptCritic
        critic = ScriptCritic(target_grade_level=8.5, min_score=8.0)
        final_audit = critic.evaluate_script(spec, use_llm=False)
        print(f"📋 Final Pedagogical Audit: Score {final_audit.overall_score}/10 | Grade {final_audit.grade_level} | Slop Cliches: {final_audit.total_slop_cliches} | Passed: {final_audit.passed}")
    except Exception as e:
        print(f"⚠️ Warning: Socratic Feynman loop encountered an issue, falling back: {e}")

    # Enrich with Declarative Visual Scene Graph (VSG)
    try:
        from pipeline.vsg_schema import convert_legacy_spec_to_vsg
        vsg = convert_legacy_spec_to_vsg(spec)
        spec["domain_taxonomy"] = vsg.domain_taxonomy.value
        spec["entity_registry"] = [e.model_dump() for e in vsg.entity_registry]
        print(f"🧩 Visual Scene Graph compiled: taxonomy='{vsg.domain_taxonomy.value}', {len(vsg.entity_registry)} canvas entities.")
    except Exception as e:
        print(f"⚠️ Warning: Could not enrich spec with VSG schema: {e}")

    # Auto-generate LaTeX SVGs with topic-scoped unique filenames
    print(f"📐 Auto-synthesizing {len(spec.get('math_formulas', []))} LaTeX mathematical SVGs...")
    for f in spec.get("math_formulas", []):
        latex = f.get("latex", "")
        orig_fname = f.get("filename") or f.get("svg_filename") or ""
        bid = f.get("beat_id", 1)
        # Ensure filename is uniquely scoped to this paper ID to prevent cross-paper collisions
        generic_names = {"formula.svg", "beat1_scale.svg", "beat2_bottleneck.svg", "beat3_architecture.svg", "beat4_mechanism.svg", "beat5_payoff.svg"}
        if not orig_fname or orig_fname in generic_names or not orig_fname.startswith(clean_id):
            clean_fname = f"{clean_id}_beat{bid}_formula.svg"
        else:
            clean_fname = orig_fname

        # Set BOTH keys so every consumer resolves the file unambiguously
        f["filename"] = clean_fname
        f["svg_filename"] = clean_fname

        fontsize = f.get("fontsize", 26)
        color = f.get("color", "white")
        if latex and clean_fname:
            try:
                render_math_to_svg(latex, clean_fname, fontsize=fontsize, color=color)
            except Exception as e:
                print(f"⚠️ Warning: Could not render math SVG '{clean_fname}': {e}")

    # Save to templates directory
    templates_dir = PROJECT_ROOT / "pipeline" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    out_file = templates_dir / f"{spec['category']}_{clean_id}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2)

    print(f"✅ Generated and saved template to: {out_file.relative_to(PROJECT_ROOT)}")
    return spec

def main():
    parser = argparse.ArgumentParser(description="The Model Verse — Autonomous Script Generator")
    parser.add_argument("--topic", help="Topic name or prompt (e.g. 'FlashAttention-3', 'Llama-3.3')")
    parser.add_argument("--arxiv", help="arXiv paper ID or URL (e.g. '2407.08608' or 'https://arxiv.org/abs/2407.08608')")
    parser.add_argument("--category", choices=CATEGORIES, help="Optional category override")
    parser.add_argument("--context", help="Additional notes or specifications")
    args = parser.parse_args()

    arxiv_meta = None
    topic = args.topic

    if args.arxiv:
        print(f"🔍 Fetching arXiv paper '{args.arxiv}'...")
        arxiv_meta = fetch_arxiv_paper(args.arxiv)
        if not arxiv_meta:
            print(f"❌ Failed to fetch paper '{args.arxiv}'")
            sys.exit(1)
        if not topic:
            topic = arxiv_meta["title"]
        print(f"📄 Paper found: {arxiv_meta['title']}")

    if not topic:
        parser.error("Either --topic or --arxiv must be provided.")

    spec = generate_script(
        topic=topic,
        category=args.category,
        context=args.context,
        arxiv_meta=arxiv_meta
    )

    print("\n-------------------------------------------------------")
    print(f"🎯 Title: {spec['title']}")
    print(f"📂 Category: {spec['category']}")
    print(f"📝 Beats: {len(spec['beats'])}")
    for b in spec["beats"]:
        print(f"   Beat {b['beat_id']}: \"{b['text']}\"")
    print("-------------------------------------------------------\n")

if __name__ == "__main__":
    main()
