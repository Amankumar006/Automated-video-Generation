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

import google.generativeai as genai
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

Aesthetic & Pedagogical Philosophy (The Feynman & 3Blue1Brown Standard):
- Explain complex AI through everyday physical intuition: use simple, relatable words that a curious 14-year-old immediately understands.
- STRICTLY ZERO ACADEMIC JARGON in spoken narration: Never speak words like 'Softmax', 'SwiGLU', 'eigenvectors', 'quadratic matrix explosion', 'residual manifolds', or 'loss landscape'.
- MANDATORY EVERYDAY ANALOGIES: Ground every abstract mechanism in a tangible real-world comparison (e.g. TV static, a foggy mirror clearing up, spotting shapes in clouds, a sculptor chipping marble, an autocomplete guessing game, a library card catalog).
- READABILITY & SIMPLICITY (Strict Grade 6-8 Standard):
  * Use simple 1-to-2 syllable conversational words (e.g. cut, build, test, fix, learn, shape, pick, clean, map, trace).
  * Ban multi-syllable buzzwords: NEVER say 'orchestration', 'competence-aware', 'effectively', 'subsequently', 'multimodal optimization', or 'bootstrapping'.
  * Keep sentences short (average 10-14 words).
- Auditory-Visual Complementarity: The voiceover carries relatable intuition and metaphors; the chalkboard screen illustrates the clean geometry and mechanical state.
- Pacing: Exactly 6 beats. Each beat MUST be 20 to 26 words maximum (around 7-9 seconds of natural, conversational speech).

The 6-Beat Narrative Arc:
1. Beat 1 (Hook / The Everyday Mystery, 0-5s): A curious question or surprising everyday paradox (e.g., why AI starts with pure TV static, or why it lies with 100% confidence).
2. Beat 2 (The Relatable Analogy, 5-13s): Anchor the mechanism in a daily-life experience (e.g., staring at clouds to spot a rabbit, or an autocomplete game).
3. Beat 3 (The Behind-the-Scenes Trick, 13-21s): How scientists taught it this skill using an everyday process (e.g., slowly fogging up a mirror, or practicing on millions of examples).
4. Beat 4 (The Physical Mechanism, 21-29s): The concrete step-by-step action (e.g., like a sculptor chipping away dust, scraping off unwanted noise layer by layer).
5. Beat 5 (The Payoff / Creation, 29-37s): The final reveal or performance triumph (e.g., 50 tiny cleaning steps carving stunning art out of chaos).
6. Beat 6 (Minimalist Brand Outro, 37-41s): 'Follow The Model Verse for simple explanations of how modern AI actually works.' (Always promote The Model Verse).

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
  * `semantic_role`: One of "agent_action" | "state_transition" | "causal_elimination" | "metric_evaluation".
- In `metadata`, specify `visual_metaphor` and concrete `visual_entities` customized to the paper/topic.
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
        spec = json.loads(raw_text, strict=False)
    except json.JSONDecodeError:
        # Auto-heal unescaped LaTeX backslashes (e.g. \alpha, \sum, \tau, \implies)
        fixed_text = re.sub(r'\\(?![/"\\bfnrtu]|u[0-9a-fA-F]{4})', r'\\\\', raw_text)
        try:
            spec = json.loads(fixed_text, strict=False)
        except json.JSONDecodeError as e:
            print("Raw LLM output:\n", raw_text)
            raise RuntimeError(f"Failed to parse LLM JSON: {e}")

    # Ensure ID slug is filesystem safe
    clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", spec.get("id", "short_topic")).lower()
    spec["id"] = clean_id

    # Autonomous Pedagogy & Simplicity Self-Refinement Loop
    try:
        from pipeline.script_critic import ScriptCritic
        critic = ScriptCritic(target_grade_level=8.0, min_score=8.0)
        audit = critic.evaluate_script(spec, use_llm=False)
        if not audit.passed or audit.grade_level > 8.5:
            print(f"🔄 Script Grade Level ({audit.grade_level}) exceeds Grade 8.0 or score ({audit.overall_score}) below threshold. Self-refining beats...")
            refine_prompt = f"""You are the Lead Scriptwriter for 'The Model Verse'.
The current script scored Grade {audit.grade_level} reading level (target: Grade 6.0 to 8.0).
Audit verdict: {audit.summary_verdict}

Current beats:
{json.dumps([{"beat_id": b["beat_id"], "text": b["text"]} for b in spec.get("beats", [])], indent=2)}

Rewrite the 'text' for each beat to make it MUCH SIMPLER:
1. Use short 1-to-2 syllable conversational words (e.g. cut, build, test, fix, learn, shape, pick, clean, map, trace).
2. Keep sentences short and direct (average 10-14 words).
3. Strictly keep every everyday physical analogy (e.g. sculptor, marble, library, cloud, mirror).
4. Strictly ZERO academic jargon or buzzwords (no 'orchestration', 'competence-aware', 'effectively', 'bootstrap', 'optimization').
5. 20-25 words per beat.

Return ONLY valid JSON matching this schema:
{{
  "beats": [
    {{"beat_id": 1, "text": "..."}},
    {{"beat_id": 2, "text": "..."}},
    {{"beat_id": 3, "text": "..."}},
    {{"beat_id": 4, "text": "..."}},
    {{"beat_id": 5, "text": "..."}},
    {{"beat_id": 6, "text": "..."}}
  ]
}}
"""
            for m_name in candidate_models:
                try:
                    ref_model = genai.GenerativeModel(m_name, generation_config={"response_mime_type": "application/json"})
                    ref_resp = ref_model.generate_content(refine_prompt)
                    if ref_resp and ref_resp.text:
                        ref_json = json.loads(ref_resp.text.strip())
                        new_beats = {b["beat_id"]: b["text"] for b in ref_json.get("beats", [])}
                        for b in spec.get("beats", []):
                            bid = b.get("beat_id")
                            if bid in new_beats:
                                b["text"] = new_beats[bid]
                        audit_new = critic.evaluate_script(spec, use_llm=False)
                        print(f"✅ Auto-Refinement Successful: Grade Level {audit_new.grade_level} | Pedagogical Score: {audit_new.overall_score}/10 | Passed: {audit_new.passed}")
                        break
                except Exception as ref_err:
                    continue
    except Exception as e:
        print(f"⚠️ Warning: Script self-refinement skipped: {e}")

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
