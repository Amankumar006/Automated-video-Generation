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
    try:
        import google.generativeai as genai
    except ImportError:
        genai = None

from pipeline.json_utils import robust_json_loads
from pipeline.arxiv_fetcher import fetch_arxiv_paper
from scripts.generate_math_svgs import render_math_to_svg
from pipeline.ollama_client import OllamaClient
from pipeline.script_directives import (
    SHARED_SCRIPT_PROMPT_DIRECTIVE,
    TRACK_1_DEEP_BREAKDOWN_PROMPT_TEMPLATE,
    validate_script_spec,
    get_total_word_count,
)

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-flash-latest")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini" if API_KEY else "ollama").lower()

if API_KEY and genai is not None:
    try:
        genai.configure(api_key=API_KEY)
    except Exception as e:
        print(f"⚠️ Warning: genai.configure failed: {e}")

CATEGORIES = [
    "architecture_breakdown", "model_showdown", "mechanism_deepdive",
    "benchmark_news", "developer_perks", "tech_news"
]

SHARED_SCRIPT_PROMPT = SHARED_SCRIPT_PROMPT_DIRECTIVE
SCRIPT_DIRECTIVES = SHARED_SCRIPT_PROMPT_DIRECTIVE


def _persist_and_finalize_spec(spec: Dict[str, Any], topic: str, default_category: str) -> Dict[str, Any]:
    clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", spec.get("id", topic)).lower()
    spec["id"] = clean_id
    cat_slug = spec.get("category") or default_category
    spec["category"] = cat_slug

    # Auto-generate LaTeX SVGs with topic-scoped unique filenames
    if spec.get("math_formulas"):
        print(f"📐 Auto-synthesizing {len(spec.get('math_formulas', []))} LaTeX mathematical SVGs...")
        for f in spec.get("math_formulas", []):
            latex = f.get("latex", "")
            orig_fname = f.get("filename") or f.get("svg_filename") or ""
            bid = f.get("beat_id", 1)
            generic_names = {"formula.svg", "beat1_scale.svg", "beat2_bottleneck.svg", "beat3_architecture.svg", "beat4_mechanism.svg", "beat5_payoff.svg"}
            if not orig_fname or orig_fname in generic_names or not orig_fname.startswith(clean_id):
                clean_fname = f"{clean_id}_beat{bid}_formula.svg"
            else:
                clean_fname = orig_fname
            f["filename"] = clean_fname
            f["svg_filename"] = clean_fname
            fontsize = f.get("fontsize", 24)
            color = f.get("color", "white")
            if latex and clean_fname:
                try:
                    render_math_to_svg(latex, clean_fname, fontsize=fontsize, color=color)
                except Exception as e:
                    print(f"⚠️ Warning: Could not render math SVG '{clean_fname}': {e}")

    templates_dir = PROJECT_ROOT / "pipeline" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    out_file = templates_dir / f"{cat_slug}_{clean_id}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2)

    print(f"✅ Generated and saved template to: {out_file.relative_to(PROJECT_ROOT)}")
    return spec


def generate_script(
    topic: str,
    category: Optional[str] = None,
    context: Optional[str] = None,
    arxiv_meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Unified multi-track script generation dispatch:
    - Track 1 (Academic Mechanism Deep Dive): Feynman / Intellectual Thriller Manim engine
    - Track 2 (Official Tech News): Breaking newsroom reporter engine
    - Track 3 (Developer Perks & Credits): Actionable deal guide engine
    """
    from pipeline.config import resolve_track, TRACK_ACADEMIC, TRACK_TECH_NEWS, TRACK_DEVELOPER_PERKS
    track = resolve_track(category)
    topic_str = str(topic).lower()
    is_perk = (
        track == TRACK_DEVELOPER_PERKS
        or topic_str.startswith("perk_")
        or (arxiv_meta and isinstance(arxiv_meta, dict) and bool(arxiv_meta.get("perk_metadata")))
    )
    is_news = (
        track == TRACK_TECH_NEWS
        or topic_str.startswith(("blog_", "news_"))
        or (arxiv_meta and isinstance(arxiv_meta, dict) and bool(arxiv_meta.get("tech_news_metadata") or arxiv_meta.get("key_facts")))
    )

    if is_perk:
        from pipeline.developer_perks_script_engine import developer_perks_script_engine
        print(f"🎁 [Track 3] Routing to Developer Perks Script Engine: '{topic}'...")
        spec = developer_perks_script_engine.generate_perks_script(topic=topic, perk_meta=arxiv_meta, context=context)
        return _persist_and_finalize_spec(spec, topic, "developer_perks")

    if is_news:
        from pipeline.tech_news_script_engine import tech_news_script_engine
        print(f"📰 [Track 2] Routing to Tech News Script Engine: '{topic}'...")
        spec = tech_news_script_engine.generate_news_script(topic=topic, blog_meta=arxiv_meta, context=context)
        return _persist_and_finalize_spec(spec, topic, "tech_news")

    paper_title = (arxiv_meta.get("title") if arxiv_meta else None) or topic
    abstract_or_paper_text = (
        (arxiv_meta.get("abstract") if arxiv_meta else None)
        or context
        or topic
    )

    track_prompt = TRACK_1_DEEP_BREAKDOWN_PROMPT_TEMPLATE.format(
        paper_title=paper_title,
        abstract_or_paper_text=abstract_or_paper_text
    )

    prompt = f"""{SHARED_SCRIPT_PROMPT_DIRECTIVE}

{track_prompt}"""

    from pipeline.llm_router import llm_router

    spec, provider_used = llm_router.route_script_generation(
        prompt=prompt,
        topic=topic,
        category=category,
        arxiv_meta=arxiv_meta
    )
    print(f"✅ Script generated successfully via provider '{provider_used}'")

    # Ensure ID slug is filesystem safe
    clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", spec.get("id", topic)).lower()
    spec["id"] = clean_id
    spec["title"] = spec.get("title") or paper_title
    cat_slug = spec.get("category") or category or "architecture_breakdown"
    spec["category"] = cat_slug
    spec["domain_taxonomy"] = spec.get("domain_taxonomy") or "hardware_efficiency"

    default_blueprints = [
        {"layout": "vector_flow_field", "title": "SYSTEM ARCHITECTURE", "sub": "Latent dynamics"},
        {"layout": "barrier_separation", "title": "BOTTLENECK ISOLATION", "sub": "Bottleneck barrier"},
        {"layout": "attention_prism_refraction", "title": "ARCHITECTURAL INNOVATION", "sub": "Core mechanism"},
        {"layout": "optimization_landscape", "title": "SECRET SAUCE", "sub": "Technical mechanism"},
        {"layout": "horizontal_race_bars", "title": "EMPIRICAL PAYOFF", "sub": "Empirical results", "params": {"metric_name": "Performance", "unit": "%", "contestants": [{"name": "Our Model", "value": 95.0, "is_hero": True, "color": "#34D399"}, {"name": "Baseline", "value": 50.0, "is_hero": False, "color": "#EF4444"}]}},
        {"layout": "brand_outro", "title": "THE MODEL VERSE", "sub": "Follow for daily deep-dives"}
    ]

    normalized_beats = []
    for idx, b in enumerate(spec.get("beats", [])):
        b_id = b.get("n") or b.get("beat_id", idx + 1)
        text = (b.get("text") or "").strip()
        anchor_word = (b.get("anchor_word") or "").strip()
        visual_cue = (b.get("visual_cue") or b.get("visual_focus") or "").strip()

        if not anchor_word and text:
            words = [re.sub(r"[^\w]", "", w) for w in text.split()]
            anchor_word = words[-1] if words else "AI"

        b["beat_id"] = b_id
        b["n"] = b_id
        b["text"] = text
        b["anchor_word"] = anchor_word
        b["visual_cue"] = visual_cue
        b["visual_focus"] = visual_cue or b.get("visual_focus", f"Beat {b_id} visual")
        b["name"] = b.get("name") or f"b{b_id}"

        if not b.get("svo_action"):
            b["svo_action"] = {
                "subject": "System",
                "action_verb": "triggers",
                "direct_object": anchor_word or "Action",
                "anchor_word": anchor_word,
                "semantic_role": "state_transition"
            }
        else:
            b["svo_action"]["anchor_word"] = anchor_word

        if not b.get("highlight_words"):
            b["highlight_words"] = {anchor_word: "#38BDF8"} if anchor_word else {}

        if not b.get("visual_blueprint"):
            bp_idx = min(max(0, b_id - 1), len(default_blueprints) - 1)
            bp = default_blueprints[bp_idx].copy()
            if visual_cue:
                bp["sub"] = visual_cue
            b["visual_blueprint"] = bp

        normalized_beats.append(b)

    spec["beats"] = normalized_beats

    # Guarantee exactly 6 beats (auto-append Beat 6 brand outro if omitted by LLM)
    if len(spec["beats"]) == 5:
        spec["beats"].append({
            "n": 6,
            "beat_id": 6,
            "name": "b6",
            "text": "Follow The Model Verse for simple explanations of how modern AI actually works.",
            "anchor_word": "Model",
            "visual_cue": "Minimalist chalkboard outro with The Model Verse branding.",
            "visual_focus": "Minimalist chalkboard outro with The Model Verse branding.",
            "highlight_words": {"The Model Verse": "#34D399"},
            "svo_action": {
                "subject": "The Model Verse",
                "action_verb": "demystifies",
                "direct_object": "Modern AI",
                "anchor_word": "Model",
                "semantic_role": "metric_evaluation"
            },
            "visual_blueprint": {"layout": "brand_outro", "title": "THE MODEL VERSE", "sub": "Follow for daily deep-dives"}
        })

    spec["word_count"] = get_total_word_count(spec)

    # Validate against Model Verse script quality rules
    is_valid, validation_errors = validate_script_spec(spec)
    if is_valid:
        print(f"✅ Deep breakdown script passed validation ({spec['word_count']} words, all anchor words verified).")
    else:
        print(f"⚠️ Deep breakdown script validation notices ({spec['word_count']} words):\n" + "\n".join(f"   - {e}" for e in validation_errors))

    # Ingest arXiv ID and extract/preserve paper figures
    arxiv_id = None
    if arxiv_meta and isinstance(arxiv_meta, dict):
        arxiv_id = arxiv_meta.get("arxiv_id") or arxiv_meta.get("id")
    if not arxiv_id and spec.get("arxiv_id"):
        arxiv_id = spec.get("arxiv_id")

    if arxiv_id:
        from pipeline.arxiv_vector_extractor import clean_arxiv_id, extract_paper_figures
        clean_arxiv = clean_arxiv_id(str(arxiv_id))
        spec["arxiv_id"] = clean_arxiv
        if arxiv_meta and arxiv_meta.get("paper_figures"):
            spec["paper_figures"] = arxiv_meta["paper_figures"]
            print(f"📊 Transferred {len(spec['paper_figures'])} paper figures from arxiv_meta into spec['paper_figures']")
        elif not spec.get("paper_figures"):
            try:
                print(f"📊 Ingesting paper figures for arXiv '{clean_arxiv}' into script spec...")
                figs = extract_paper_figures(clean_arxiv, max_figures=5)
                if figs:
                    spec["paper_figures"] = figs
                    print(f"   ✅ Successfully extracted {len(figs)} paper figures into spec['paper_figures']")
            except Exception as e_figs:
                print(f"⚠️ Figure extraction notice in script_generator: {e_figs}")

    # Preserve curated code kernel and repo metadata if supplied by GitHub ingest
    if arxiv_meta and isinstance(arxiv_meta, dict):
        if arxiv_meta.get("code_snippet") and (not spec.get("code_snippet") or arxiv_meta.get("repo_metadata")):
            spec["code_snippet"] = arxiv_meta["code_snippet"]
        if arxiv_meta.get("repo_metadata"):
            spec["repo_metadata"] = arxiv_meta["repo_metadata"]

    # Pedagogical Audit with ScriptCritic (telemetry only, preserving script words)
    try:
        from pipeline.script_critic import ScriptCritic
        critic = ScriptCritic(target_grade_level=8.5, min_score=8.0)
        final_audit = critic.evaluate_script(spec, use_llm=False)
        print(f"📋 Final Pedagogical Audit: Score {final_audit.overall_score}/10 | Grade {final_audit.grade_level} | Slop Cliches: {final_audit.total_slop_cliches} | Passed: {final_audit.passed}")
    except Exception as e:
        print(f"⚠️ Warning: Pedagogical critic notice: {e}")

    # Intellectual Thriller Narrative Compliance Audit (telemetry only)
    try:
        from pipeline.intellectual_thriller_engine import intellectual_thriller_engine
        thriller_audit = intellectual_thriller_engine.audit_thriller_compliance(spec)
        print(f"   ⚡ Thriller Compliance Score: {thriller_audit['score']}/10 | Hook Passed: {thriller_audit['hook_passed']} | {thriller_audit['verdict']}")
    except Exception as e:
        print(f"⚠️ Warning: Intellectual Thriller Engine notice: {e}")

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
    cat_slug = spec.get("category") or category or "mechanism_deepdive"
    spec["category"] = cat_slug
    out_file = templates_dir / f"{cat_slug}_{clean_id}.json"
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
