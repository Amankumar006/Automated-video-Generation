"""
The Model Verse — Unified Multi-Provider LLM Fallback Router
Cascades across healthy providers:
1. Gemini (Primary: gemini-3.1-flash-lite, gemini-2.5-flash, gemini-flash-latest)
2. Mercury 3 (Fast OpenAI-compatible fallback when configured)
3. Groq (Secondary cloud: llama-3.3-70b-versatile, llama-3.1-8b-instant)
4. OpenRouter (Tertiary cloud free tier: meta-llama/llama-3.3-70b-instruct:free, google/gemini-2.0-flash-exp:free)
5. Ollama Cloud (gpt-oss:120b:cloud, gemma4:31b:cloud)
6. Deterministic Architectural Fallback (Zero-failure guarantee for offline / test environments)

Features:
- Catches ResourceExhausted, 429 Too Many Requests, and quota errors
- In-memory QuotaHealthTracker integration (immediately skips exhausted providers)
- Automatic thinking token stripping (<think>...</think>, <thought>...</thought>)
- Markdown code block sanitization (```json ... ```)
- Identical 6-beat JSON schema enforcement across all providers
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

import requests

from pipeline.json_utils import robust_json_loads
from pipeline.ollama_client import OllamaClient, strip_thinking_tags
from pipeline.quota_tracker import is_quota_error, quota_tracker

logger = logging.getLogger("llm_router")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [LLMRouter] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Optional genai import
try:
    import google.generativeai as genai
except ImportError:
    genai = None


def sanitize_markdown_json(text: str) -> str:
    """
    Strips markdown code blocks, think tags, and returns the raw JSON string.
    """
    if not text:
        return ""
    cleaned = strip_thinking_tags(text).strip()

    # Extract JSON inside ```json ... ``` or ``` ... ```
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    matches = re.findall(fence_pattern, cleaned)
    if matches:
        for m in matches:
            if ("{" in m and "}" in m) or ("[" in m and "]"):
                return m.strip()
        return matches[0].strip()

    # If no fences, find the outermost { ... }
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return cleaned[first_brace : last_brace + 1].strip()

    return cleaned


def strip_all_thinking_tokens(data: Any) -> Any:
    """
    Recursively strips thinking tokens from all string values in a dictionary or list.
    """
    if isinstance(data, str):
        return strip_thinking_tags(data)
    elif isinstance(data, dict):
        return {k: strip_all_thinking_tokens(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [strip_all_thinking_tokens(v) for v in data]
    return data


def enforce_script_schema(
    spec: Dict[str, Any],
    topic: str,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enforces identical, strictly compliant 6-beat JSON schema across all LLM providers.
    Ensures correct beats, math formulas, SVO triples, blueprints, and clean slugs.
    """
    if not isinstance(spec, dict):
        spec = {}

    clean_spec = strip_all_thinking_tokens(spec)

    raw_id = clean_spec.get("id") or topic or "short_topic"
    clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", str(raw_id)).lower()
    clean_id = re.sub(r"_+", "_", clean_id).strip("_")
    if not clean_id:
        clean_id = "short_topic"
    clean_spec["id"] = clean_id

    cat = category or clean_spec.get("category") or "mechanism_deepdive"
    valid_categories = ["architecture_breakdown", "model_showdown", "mechanism_deepdive", "benchmark_news"]
    if cat not in valid_categories:
        cat = "mechanism_deepdive"
    clean_spec["category"] = cat

    if not clean_spec.get("title"):
        clean_spec["title"] = topic or "Technical Deepdive"

    if not clean_spec.get("domain_taxonomy"):
        clean_spec["domain_taxonomy"] = "hardware_efficiency"

    if not clean_spec.get("hook_tag"):
        clean_spec["hook_tag"] = cat.upper().replace("_", " ")

    # Ensure beats array exists and has valid items
    raw_beats = clean_spec.get("beats")
    if not isinstance(raw_beats, list):
        raw_beats = []

    # Canonical templates for default beats if missing
    default_beat_blueprints = [
        ("horizontal_race_bars", "HARDWARE EFFICIENCY BREAKDOWN", "Baseline vs Frontier"),
        ("vector_flow_field", "LATENT TRAJECTORY BOTTLENECK", "Memory Bandwidth Limits"),
        ("split_flow", "EUREKA ARCHITECTURAL DECOMPOSITION", "Dual-Decoupled Routing"),
        ("grid_memory", "MECHANICAL SECRET SAUCE", "Zero-Copy State Pruning"),
        ("horizontal_race_bars", "EMPIRICAL PERFORMANCE PAYOFF", "Throughput & Latency SOTA"),
        ("paper_figure", "THE PARADIGM SHIFT", "Closing Outro & Continuity")
    ]

    beats: List[Dict[str, Any]] = []
    for i in range(1, 7):
        b_match = None
        for rb in raw_beats:
            if isinstance(rb, dict) and rb.get("beat_id") == i:
                b_match = rb
                break

        if b_match:
            beat_item = dict(b_match)
        elif i - 1 < len(raw_beats) and isinstance(raw_beats[i - 1], dict):
            beat_item = dict(raw_beats[i - 1])
            beat_item["beat_id"] = i
        else:
            bp_layout, bp_title, bp_sub = default_beat_blueprints[i - 1]
            beat_item = {
                "beat_id": i,
                "text": f"Beat {i} explaining {topic} with high retention and technical precision.",
                "visual_focus": f"Detailed chalkboard visual illustrating beat {i}.",
                "highlight_words": {topic[:15]: "#38BDF8"},
                "svo_action": {
                    "subject": "System Core",
                    "action_verb": "accelerates",
                    "direct_object": "Computation",
                    "anchor_word": "explaining",
                    "semantic_role": "state_transition"
                },
                "visual_blueprint": {
                    "layout": bp_layout,
                    "title": bp_title,
                    "sub": bp_sub,
                    "accent_color": "#38BDF8",
                    "params": {"param_key_1": "metric_a", "param_key_2": "metric_b"}
                }
            }

        # Backfill any missing inner fields for this beat
        if "text" not in beat_item or not beat_item["text"]:
            beat_item["text"] = f"Beat {i} core mechanism of {topic}."
        if "visual_focus" not in beat_item or not beat_item["visual_focus"]:
            beat_item["visual_focus"] = f"Blackboard visual representation for Beat {i}."

        words = beat_item["text"].split()
        first_word = words[0] if words else "System"

        hw = beat_item.get("highlight_words")
        if not isinstance(hw, dict) or not hw:
            beat_item["highlight_words"] = {first_word: "#34D399"}

        svo = beat_item.get("svo_action")
        if not isinstance(svo, dict):
            svo = {}
        bp_layout, bp_title, bp_sub = default_beat_blueprints[i - 1]
        beat_item["svo_action"] = {
            "subject": svo.get("subject") or "Neural Kernel",
            "action_verb": svo.get("action_verb") or "optimizes",
            "direct_object": svo.get("direct_object") or "Hardware Latency",
            "anchor_word": svo.get("anchor_word") or first_word,
            "semantic_role": svo.get("semantic_role") or "state_transition",
        }

        vb = beat_item.get("visual_blueprint")
        if not isinstance(vb, dict):
            vb = {}
        beat_item["visual_blueprint"] = {
            "layout": vb.get("layout") or bp_layout,
            "title": vb.get("title") or bp_title,
            "sub": vb.get("sub") or bp_sub,
            "accent_color": vb.get("accent_color") or "#38BDF8",
            "params": vb.get("params") if isinstance(vb.get("params"), dict) else {"label": "Active Component"},
        }

        beat_item["beat_id"] = i
        beats.append(beat_item)

    # If beat 6 was an empty outro, enforce crisp brand outro
    if beats[5]["text"].startswith("Beat 6"):
        beats[5]["text"] = "Follow The Model Verse for daily deep-dives into how modern AI actually works under the hood."
        beats[5]["highlight_words"] = {"The Model Verse": "#34D399"}

    clean_spec["beats"] = beats

    # Ensure math_formulas has exactly 5 formulas (Beats 1..5)
    raw_formulas = clean_spec.get("math_formulas")
    if not isinstance(raw_formulas, list):
        raw_formulas = []

    default_latex = [
        r"$\mathcal{O}(N) \ll \mathcal{O}(N^2)$",
        r"$\mathbf{L}_{\mathrm{bottleneck}} = \sum_{i=1}^M \alpha_i \mathbf{v}_i$",
        r"$\mathbf{y} = \mathrm{LayerNorm}(\mathbf{W}_p \mathbf{x} + \mathbf{b})$",
        r"$\mathrm{TopK}(\sigma(\mathbf{W}_g \mathbf{x})) = \mathbf{e}^*$",
        r"$\mathrm{Throughput}_{\mathrm{SOTA}} \ge 2.5\times$"
    ]

    math_formulas = []
    for i in range(1, 6):
        mf_match = None
        for mf in raw_formulas:
            if isinstance(mf, dict) and mf.get("beat_id") == i:
                mf_match = mf
                break

        if mf_match:
            f_item = dict(mf_match)
        elif i - 1 < len(raw_formulas) and isinstance(raw_formulas[i - 1], dict):
            f_item = dict(raw_formulas[i - 1])
            f_item["beat_id"] = i
        else:
            f_item = {
                "beat_id": i,
                "latex": default_latex[i - 1],
                "filename": f"{clean_id}_beat{i}_formula.svg",
                "fontsize": 24,
                "color": "#38BDF8",
                "term_annotations": [{"term": "x", "label": "Feature Vector"}]
            }

        if "latex" not in f_item or not f_item["latex"]:
            f_item["latex"] = default_latex[i - 1]
        if "filename" not in f_item or not f_item["filename"]:
            f_item["filename"] = f"{clean_id}_beat{i}_formula.svg"
        if "fontsize" not in f_item:
            f_item["fontsize"] = 24
        if "color" not in f_item:
            f_item["color"] = "#38BDF8"
        if not isinstance(f_item.get("term_annotations"), list):
            f_item["term_annotations"] = [{"term": "x", "label": "Feature Vector"}]
        f_item["svg_filename"] = f_item["filename"]
        f_item["beat_id"] = i
        math_formulas.append(f_item)

    clean_spec["math_formulas"] = math_formulas

    # Ensure sfx_cues
    if not isinstance(clean_spec.get("sfx_cues"), list) or len(clean_spec.get("sfx_cues", [])) < 3:
        clean_spec["sfx_cues"] = [
            {"timestamp": 0.8, "sound_type": "sub_impact", "volume": 0.45},
            {"timestamp": 5.2, "sound_type": "whoosh", "volume": 0.35},
            {"timestamp": 15.0, "sound_type": "laser", "volume": 0.40},
            {"timestamp": 25.0, "sound_type": "sub_impact", "volume": 0.50},
            {"timestamp": 38.0, "sound_type": "chime", "volume": 0.40}
        ]

    # Ensure metadata
    if not isinstance(clean_spec.get("metadata"), dict):
        clean_spec["metadata"] = {}
    meta = clean_spec["metadata"]
    if "visual_metaphor" not in meta:
        meta["visual_metaphor"] = "hardware_memory_hierarchy"
    if "scale_metric" not in meta:
        meta["scale_metric"] = "10x"
    if "scale_label" not in meta:
        meta["scale_label"] = "Speedup"
    if "payoff_stat" not in meta:
        meta["payoff_stat"] = "98.2%"
    if "payoff_label" not in meta:
        meta["payoff_label"] = "Efficiency SOTA"

    # Ensure benchmark comparison
    if not isinstance(clean_spec.get("benchmark_comparison"), dict):
        clean_spec["benchmark_comparison"] = {
            "title": "BENCHMARK PERFORMANCE COMPARISON",
            "metric_name": "Throughput",
            "unit": "TFLOPS",
            "contestants": [
                {"name": topic[:20], "value": 1180.0, "display_val": "1,180 TFLOPS", "is_hero": True, "color": "#10B981"},
                {"name": "Standard Baseline", "value": 450.0, "display_val": "450 TFLOPS", "is_hero": False, "color": "#EF4444"}
            ],
            "delta_badge": "⚡ +2.6x SPEEDUP",
            "radar_axes": ["Throughput", "VRAM Efficiency", "Accuracy", "Context Length", "Cost Efficiency"]
        }

    # Ensure code snippet
    if not isinstance(clean_spec.get("code_snippet"), dict):
        clean_spec["code_snippet"] = {
            "filename": "kernel.py",
            "language": "python",
            "lines": [
                "def forward_pass(input_tensor):",
                "    return fused_kernel_op(input_tensor)"
            ],
            "highlight_lines": [1],
            "trace_register": "⚡ HARDWARE FUSED DISPATCH",
            "explanation": "Zero-latency pipeline operation"
        }

    return clean_spec


def generate_deterministic_fallback_script(
    topic: str,
    category: Optional[str] = None,
    arxiv_meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Constructs a structurally complete, domain-accurate 6-beat script spec
    when all external LLM providers are down, exhausted, or offline.
    Dynamically extracts authentic sentences from arxiv_meta or synthesizes
    category-accurate beats without canned repetitive templates.
    """
    clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", topic).lower()
    clean_id = re.sub(r"_+", "_", clean_id).strip("_")
    if not clean_id:
        clean_id = "short_topic"
    cat = (category or (arxiv_meta.get("category") if arxiv_meta else None) or "mechanism_deepdive").lower()
    title = (arxiv_meta.get("title") if arxiv_meta else None) or topic

    # Clean display topic
    clean_topic = topic.split(":")[0].strip()
    for prefix in (
        "mechanism_deepdive_", "architecture_breakdown_", "model_showdown_",
        "benchmark_news_", "developer_perks_", "tech_news_", "perk_", "blog_", "news_", "gh_"
    ):
        if clean_topic.startswith(prefix):
            clean_topic = clean_topic[len(prefix):]
    clean_topic = clean_topic.replace("_", " ").strip()
    if clean_topic.islower():
        clean_topic = clean_topic.title()
    clean_topic = clean_topic or "Frontier AI"

    # Infer domain taxonomy
    dom = (arxiv_meta.get("domain_taxonomy") if arxiv_meta else None) or "hardware_efficiency"
    if cat == "developer_perks":
        dom = "developer_perks"
    elif cat in ("tech_news", "blogs", "news"):
        dom = "tech_news"
    elif cat in ("model_showdown", "benchmark_news"):
        dom = "model_showdown"
    elif "robot" in topic.lower():
        dom = "robotics_tamp"
    elif any(w in topic.lower() for w in ("diffusion", "video gen", "3d")):
        dom = "multimodal_diffusion"

    abstract_text = ""
    if arxiv_meta and isinstance(arxiv_meta, dict):
        abstract_text = arxiv_meta.get("abstract", "") or arxiv_meta.get("summary", "")

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", abstract_text) if len(s.strip()) > 15]

    beats: List[Dict[str, Any]] = []

    if len(sentences) >= 4:
        # Dynamic extraction directly from paper/article abstract
        s0 = sentences[0].rstrip(".?! ")
        t1 = f"Why is {clean_topic} a major breakthrough? Because {s0[0].lower() + s0[1:]}." if not any(w in s0.lower() for w in ("you", "your")) else s0 + "."
        s1 = sentences[1].rstrip(".?! ")
        t2 = f"The core challenge? {s1}."
        s2 = sentences[2].rstrip(".?! ")
        t3 = f"Enter {clean_topic}: {s2[0].lower() + s2[1:]}."
        s3 = sentences[3].rstrip(".?! ")
        t4 = f"Under the hood, {s3[0].lower() + s3[1:]}."
        if len(sentences) >= 5:
            s4 = sentences[4].rstrip(".?! ")
            t5 = f"The result? {s4}."
        else:
            t5 = f"The result? Proven empirical gains and state-of-the-art benchmarks on {clean_topic}."

        beats = [
            {
                "beat_id": 1,
                "text": t1,
                "visual_focus": f"System architecture schematic introducing {clean_topic}.",
                "highlight_words": {clean_topic: "#38BDF8"},
                "svo_action": {"subject": clean_topic, "action_verb": "disrupts", "direct_object": "Baseline Systems", "anchor_word": clean_topic.split()[0], "semantic_role": "state_transition"},
                "visual_blueprint": {"layout": "grid_memory", "title": clean_topic.upper(), "sub": "Core Architectural Premise", "accent_color": "#38BDF8", "params": {}}
            },
            {
                "beat_id": 2,
                "text": t2,
                "visual_focus": "Bottleneck diagram illustrating resource contention and latency walls.",
                "highlight_words": {"challenge": "#EF4444"},
                "svo_action": {"subject": "System Bottleneck", "action_verb": "throttles", "direct_object": "Throughput", "anchor_word": "challenge", "semantic_role": "causal_elimination"},
                "visual_blueprint": {"layout": "vector_flow_field", "title": "BOTTLENECK ANALYSIS", "sub": "Resource & Latency Pressure", "accent_color": "#EF4444", "params": {}}
            },
            {
                "beat_id": 3,
                "text": t3,
                "visual_focus": f"Split-screen contrasting traditional approaches with {clean_topic}.",
                "highlight_words": {clean_topic: "#34D399"},
                "svo_action": {"subject": clean_topic, "action_verb": "restructures", "direct_object": "Pipeline Flow", "anchor_word": clean_topic.split()[0], "semantic_role": "agent_action"},
                "visual_blueprint": {"layout": "split_flow", "title": "ARCHITECTURAL INNOVATION", "sub": "Decoupled Processing Pipeline", "accent_color": "#34D399", "params": {}}
            },
            {
                "beat_id": 4,
                "text": t4,
                "visual_focus": "Low-level execution diagram detailing algorithmic coordination.",
                "highlight_words": {"Under the hood": "#38BDF8"},
                "svo_action": {"subject": "Execution Engine", "action_verb": "coordinates", "direct_object": "Workload Stream", "anchor_word": "hood", "semantic_role": "agent_action"},
                "visual_blueprint": {"layout": "chalkboard_code_block", "title": "EXECUTION MECHANICS", "sub": "Algorithmic Coordination", "accent_color": "#38BDF8", "params": {}}
            },
            {
                "beat_id": 5,
                "text": t5,
                "visual_focus": "Benchmark bar chart showing empirical speedups and efficiency gains.",
                "highlight_words": {"empirical gains": "#34D399"},
                "svo_action": {"subject": clean_topic, "action_verb": "delivers", "direct_object": "SOTA Performance", "anchor_word": "gains", "semantic_role": "metric_evaluation"},
                "visual_blueprint": {"layout": "horizontal_race_bars", "title": "EMPIRICAL PERFORMANCE", "sub": "Wall-Clock Benchmark Results", "accent_color": "#34D399", "params": {}}
            },
            {
                "beat_id": 6,
                "text": "Follow The Model Verse for daily deep-dives into how modern AI actually works under the hood.",
                "visual_focus": "Minimalist chalkboard outro with The Model Verse branding.",
                "highlight_words": {"The Model Verse": "#34D399"},
                "svo_action": {"subject": "The Model Verse", "action_verb": "demystifies", "direct_object": "Modern AI", "anchor_word": "Model", "semantic_role": "metric_evaluation"},
                "visual_blueprint": {"layout": "paper_figure", "title": "THE MODEL VERSE", "sub": "Autonomous Architectural Analysis", "accent_color": "#34D399", "params": {"title": "Outro"}}
            }
        ]
    elif cat == "developer_perks":
        beats = [
            {
                "beat_id": 1,
                "text": f"Stop paying full price for AI tokens before checking out {clean_topic}.",
                "visual_focus": f"Credit allotment badge and API grant tier for {clean_topic}.",
                "highlight_words": {clean_topic: "#38BDF8", "full price": "#EF4444"},
                "svo_action": {"subject": "Developer Team", "action_verb": "claims", "direct_object": "API Credits", "anchor_word": "tokens", "semantic_role": "agent_action"},
                "visual_blueprint": {"layout": "catalog_routing", "title": "DEVELOPER PROGRAM ACCESS", "sub": "Grant Tier & Token Subsidies", "accent_color": "#38BDF8", "params": {}}
            },
            {
                "beat_id": 2,
                "text": "The problem? Skyrocketing API and compute expenses drain engineering runways before launch.",
                "visual_focus": "Expense burn graph showing rapid budget exhaustion across model calls.",
                "highlight_words": {"Skyrocketing": "#EF4444", "drain": "#F59E0B"},
                "svo_action": {"subject": "Inference Costs", "action_verb": "burns", "direct_object": "Startup Capital", "anchor_word": "expenses", "semantic_role": "causal_elimination"},
                "visual_blueprint": {"layout": "barrier_separation", "title": "API INFRASTRUCTURE COSTS", "sub": "Token Consumption Burn Rate", "accent_color": "#EF4444", "params": {}}
            },
            {
                "beat_id": 3,
                "text": f"Enter {clean_topic}. It unlocks dedicated credits, subsidized endpoints, and startup grants.",
                "visual_focus": f"Resource allocation split-screen showing subsidized compute via {clean_topic}.",
                "highlight_words": {clean_topic: "#34D399", "dedicated credits": "#38BDF8"},
                "svo_action": {"subject": clean_topic, "action_verb": "provides", "direct_object": "Subsidized Compute", "anchor_word": "credits", "semantic_role": "agent_action"},
                "visual_blueprint": {"layout": "split_flow", "title": "PROGRAM TIERS & COMPUTE", "sub": "Direct Foundation Model Subsidies", "accent_color": "#34D399", "params": {}}
            },
            {
                "beat_id": 4,
                "text": "Under the hood, qualifying teams bypass costly bills by applying with their verified GitHub or domain.",
                "visual_focus": "Application step-by-step checklist showing instant verification criteria.",
                "highlight_words": {"verified GitHub": "#38BDF8", "bypass": "#34D399"},
                "svo_action": {"subject": "Application Portal", "action_verb": "verifies", "direct_object": "Developer Credentials", "anchor_word": "qualifying", "semantic_role": "agent_action"},
                "visual_blueprint": {"layout": "pipeline_stages", "title": "VERIFICATION STEPS", "sub": "Application & Approval Path", "accent_color": "#38BDF8", "params": {}}
            },
            {
                "beat_id": 5,
                "text": f"The result? Massive cost savings and extended compute capacity to ship production models faster.",
                "visual_focus": "Comparison bars contrasting self-funded costs with grant-subsidized runway.",
                "highlight_words": {"Massive cost savings": "#34D399", "ship faster": "#38BDF8"},
                "svo_action": {"subject": clean_topic, "action_verb": "extends", "direct_object": "Engineering Runway", "anchor_word": "savings", "semantic_role": "metric_evaluation"},
                "visual_blueprint": {"layout": "horizontal_race_bars", "title": "CAPITAL & COMPUTE SAVINGS", "sub": "Direct Dollar Value Unlocked", "accent_color": "#34D399", "params": {}}
            },
            {
                "beat_id": 6,
                "text": "Follow The Model Verse for daily updates on free developer perks, tools, and frontier AI research.",
                "visual_focus": "Chalkboard brand signature with subscribe indicator.",
                "highlight_words": {"The Model Verse": "#34D399"},
                "svo_action": {"subject": "The Model Verse", "action_verb": "curates", "direct_object": "Developer Perks", "anchor_word": "Model", "semantic_role": "metric_evaluation"},
                "visual_blueprint": {"layout": "paper_figure", "title": "THE MODEL VERSE", "sub": "Daily Developer Perks & Research", "accent_color": "#34D399", "params": {"title": "Outro"}}
            }
        ]
    elif cat in ("tech_news", "blogs", "news"):
        beats = [
            {
                "beat_id": 1,
                "text": f"Before you update your production stack, see what just dropped with {clean_topic}.",
                "visual_focus": f"Headline banner announcing official launch details for {clean_topic}.",
                "highlight_words": {clean_topic: "#38BDF8"},
                "svo_action": {"subject": clean_topic, "action_verb": "launches", "direct_object": "New Capabilities", "anchor_word": "dropped", "semantic_role": "state_transition"},
                "visual_blueprint": {"layout": "grid_memory", "title": clean_topic.upper(), "sub": "Official Lab Release", "accent_color": "#38BDF8", "params": {}}
            },
            {
                "beat_id": 2,
                "text": "The villain? Prior models struggled with latency, steep pricing, and reasoning instability.",
                "visual_focus": "Latency and pricing chart illustrating performance ceilings of predecessor models.",
                "highlight_words": {"latency": "#EF4444", "steep pricing": "#F59E0B"},
                "svo_action": {"subject": "Predecessor Models", "action_verb": "incurs", "direct_object": "Inference Latency", "anchor_word": "pricing", "semantic_role": "causal_elimination"},
                "visual_blueprint": {"layout": "vector_flow_field", "title": "PREDECESSOR LIMITATIONS", "sub": "Cost & Reasoning Constraints", "accent_color": "#EF4444", "params": {}}
            },
            {
                "beat_id": 3,
                "text": f"Enter {clean_topic}. It addresses these limitations with an upgraded architecture and optimized inference.",
                "visual_focus": f"Architectural schema showcasing key upgrades in {clean_topic}.",
                "highlight_words": {clean_topic: "#34D399", "optimized inference": "#38BDF8"},
                "svo_action": {"subject": clean_topic, "action_verb": "upgrades", "direct_object": "Inference Engine", "anchor_word": "addresses", "semantic_role": "agent_action"},
                "visual_blueprint": {"layout": "split_flow", "title": "ARCHITECTURAL ADVANCEMENT", "sub": "Distilled Reasoning & Routing", "accent_color": "#34D399", "params": {}}
            },
            {
                "beat_id": 4,
                "text": "Under the hood, enhanced token routing and distilled execution deliver faster responses at lower cost.",
                "visual_focus": "Execution pipeline illustrating token throughput and optimized KV-cache management.",
                "highlight_words": {"faster responses": "#34D399", "lower cost": "#38BDF8"},
                "svo_action": {"subject": "Routing Layer", "action_verb": "dispatches", "direct_object": "Tokens", "anchor_word": "routing", "semantic_role": "agent_action"},
                "visual_blueprint": {"layout": "chalkboard_code_block", "title": "INFERENCE ENGINE", "sub": "Optimized Token Routing", "accent_color": "#38BDF8", "params": {}}
            },
            {
                "beat_id": 5,
                "text": f"The payoff? Verified benchmark leaps across reasoning, coding, and cost-efficiency metrics.",
                "visual_focus": "Comparative benchmark race bars showing gains across industry standards.",
                "highlight_words": {"benchmark leaps": "#34D399"},
                "svo_action": {"subject": clean_topic, "action_verb": "beats", "direct_object": "Frontier Baselines", "anchor_word": "leaps", "semantic_role": "metric_evaluation"},
                "visual_blueprint": {"layout": "horizontal_race_bars", "title": "BENCHMARK PERFORMANCE", "sub": "Coding & Reasoning Gains", "accent_color": "#34D399", "params": {}}
            },
            {
                "beat_id": 6,
                "text": "Follow The Model Verse for daily breakdowns of major AI drops and architectural breakthroughs.",
                "visual_focus": "Minimalist chalkboard outro with The Model Verse branding.",
                "highlight_words": {"The Model Verse": "#34D399"},
                "svo_action": {"subject": "The Model Verse", "action_verb": "breaks down", "direct_object": "AI Drops", "anchor_word": "Model", "semantic_role": "metric_evaluation"},
                "visual_blueprint": {"layout": "paper_figure", "title": "THE MODEL VERSE", "sub": "Daily AI News & Analysis", "accent_color": "#34D399", "params": {"title": "Outro"}}
            }
        ]
    elif cat in ("model_showdown", "benchmark_news"):
        beats = [
            {
                "beat_id": 1,
                "text": f"Does {clean_topic} actually beat the reigning champion, or is it just benchmark hype?",
                "visual_focus": f"Split contender card comparing head-to-head metrics in {clean_topic}.",
                "highlight_words": {clean_topic: "#38BDF8", "reigning champion": "#F59E0B"},
                "svo_action": {"subject": clean_topic, "action_verb": "challenges", "direct_object": "Incumbent SOTA", "anchor_word": "beat", "semantic_role": "state_transition"},
                "visual_blueprint": {"layout": "split_flow", "title": "HEAD-TO-HEAD SHOWDOWN", "sub": "Contender Comparison", "accent_color": "#38BDF8", "params": {}}
            },
            {
                "beat_id": 2,
                "text": "The tension? Leading models often claim top leaderboard spots through cherry-picked metrics.",
                "visual_focus": "Dissected leaderboard radar plot highlighting evaluation discrepancies.",
                "highlight_words": {"cherry-picked": "#EF4444"},
                "svo_action": {"subject": "Leaderboard Bias", "action_verb": "distorts", "direct_object": "Model Comparison", "anchor_word": "tension", "semantic_role": "causal_elimination"},
                "visual_blueprint": {"layout": "radar_pareto_plot", "title": "LEADERBOARD EVALUATION", "sub": "Reported vs Verified Performance", "accent_color": "#EF4444", "params": {}}
            },
            {
                "beat_id": 3,
                "text": f"Enter {clean_topic}. It challenges the incumbent with a radically different architectural trade-off.",
                "visual_focus": "Architectural contrast showing routing divergence between the two models.",
                "highlight_words": {clean_topic: "#34D399", "radically different": "#38BDF8"},
                "svo_action": {"subject": clean_topic, "action_verb": "diverges", "direct_object": "Standard Paradigms", "anchor_word": "challenges", "semantic_role": "agent_action"},
                "visual_blueprint": {"layout": "split_flow", "title": "ARCHITECTURAL DIVERGENCE", "sub": "Contrasting Design Trade-Offs", "accent_color": "#34D399", "params": {}}
            },
            {
                "beat_id": 4,
                "text": "Under the hood, comparative benchmarks reveal dramatic differences in reasoning speed and token cost.",
                "visual_focus": "Throughput vs latency trade-off curve across varied prompt lengths.",
                "highlight_words": {"reasoning speed": "#34D399", "token cost": "#38BDF8"},
                "svo_action": {"subject": "Benchmark Runner", "action_verb": "evaluates", "direct_object": "Token Cost", "anchor_word": "speed", "semantic_role": "agent_action"},
                "visual_blueprint": {"layout": "chalkboard_code_block", "title": "COST & LATENCY PROFILE", "sub": "Empirical Inference Efficiency", "accent_color": "#38BDF8", "params": {}}
            },
            {
                "beat_id": 5,
                "text": f"The verdict? A decisive shift in Pareto efficiency, setting a new bar for real-world tasks.",
                "visual_focus": "Pareto frontier plot highlighting the winning model's dominance.",
                "highlight_words": {"Pareto efficiency": "#34D399", "new bar": "#38BDF8"},
                "svo_action": {"subject": clean_topic, "action_verb": "wins", "direct_object": "Pareto Frontier", "anchor_word": "verdict", "semantic_role": "metric_evaluation"},
                "visual_blueprint": {"layout": "horizontal_race_bars", "title": "FINAL SCORECARD", "sub": "Decisive Benchmark Advantage", "accent_color": "#34D399", "params": {}}
            },
            {
                "beat_id": 6,
                "text": "Follow The Model Verse for daily head-to-head model showdowns and engineering deep-dives.",
                "visual_focus": "Minimalist chalkboard outro with The Model Verse branding.",
                "highlight_words": {"The Model Verse": "#34D399"},
                "svo_action": {"subject": "The Model Verse", "action_verb": "evaluates", "direct_object": "Model Showdowns", "anchor_word": "Model", "semantic_role": "metric_evaluation"},
                "visual_blueprint": {"layout": "paper_figure", "title": "THE MODEL VERSE", "sub": "Daily AI Benchmark Showdowns", "accent_color": "#34D399", "params": {"title": "Outro"}}
            }
        ]
    else:
        # Default: Mechanism deep-dive / hardware efficiency / architecture
        beats = [
            {
                "beat_id": 1,
                "text": f"Why are top AI researchers watching {clean_topic}? Because standard models hit a scaling bottleneck.",
                "visual_focus": f"System architecture schematic illustrating {clean_topic} core concept.",
                "highlight_words": {clean_topic: "#38BDF8", "scaling bottleneck": "#EF4444"},
                "svo_action": {"subject": clean_topic, "action_verb": "disrupts", "direct_object": "Standard Architecture", "anchor_word": clean_topic.split()[0], "semantic_role": "state_transition"},
                "visual_blueprint": {"layout": "grid_memory", "title": clean_topic.upper(), "sub": "Architectural Premise", "accent_color": "#38BDF8", "params": {}}
            },
            {
                "beat_id": 2,
                "text": "The bottleneck? Conventional architectures hit severe resource walls when processing large workloads.",
                "visual_focus": "Bottleneck diagram highlighting resource contention and execution stall.",
                "highlight_words": {"resource walls": "#EF4444"},
                "svo_action": {"subject": "Resource Wall", "action_verb": "stalls", "direct_object": "Pipeline Execution", "anchor_word": "bottleneck", "semantic_role": "causal_elimination"},
                "visual_blueprint": {"layout": "vector_flow_field", "title": "SYSTEM BOTTLENECK", "sub": "Contention & Resource Constraints", "accent_color": "#EF4444", "params": {}}
            },
            {
                "beat_id": 3,
                "text": f"Enter {clean_topic}. It bypasses traditional constraints with a decoupled, high-throughput pipeline.",
                "visual_focus": "Parallel pipeline separating heavy stages from critical latency paths.",
                "highlight_words": {clean_topic: "#34D399", "decoupled": "#38BDF8"},
                "svo_action": {"subject": clean_topic, "action_verb": "bypasses", "direct_object": "Execution Bottleneck", "anchor_word": "decoupled", "semantic_role": "agent_action"},
                "visual_blueprint": {"layout": "split_flow", "title": "PARALLEL PIPELINE", "sub": "Decoupled Processing Architecture", "accent_color": "#34D399", "params": {}}
            },
            {
                "beat_id": 4,
                "text": "Under the hood, asynchronous stage coordination eliminates idle wait states entirely.",
                "visual_focus": "Asynchronous coordinate graph demonstrating continuous throughput with zero idle cycles.",
                "highlight_words": {"asynchronous": "#38BDF8", "zero idle": "#34D399"},
                "svo_action": {"subject": "Coordination Layer", "action_verb": "synchronizes", "direct_object": "Compute Stages", "anchor_word": "asynchronous", "semantic_role": "agent_action"},
                "visual_blueprint": {"layout": "chalkboard_code_block", "title": "EXECUTION COORDINATION", "sub": "Zero-Stall Asynchronous Kernel", "accent_color": "#38BDF8", "params": {}}
            },
            {
                "beat_id": 5,
                "text": f"The result? Substantial throughput acceleration with zero sacrifice in mathematical fidelity.",
                "visual_focus": "Comparative benchmark race bars showing massive speedups.",
                "highlight_words": {"throughput acceleration": "#34D399"},
                "svo_action": {"subject": clean_topic, "action_verb": "accelerates", "direct_object": "Throughput", "anchor_word": "acceleration", "semantic_role": "metric_evaluation"},
                "visual_blueprint": {"layout": "horizontal_race_bars", "title": "BENCHMARK PERFORMANCE", "sub": "Wall-Clock Speedup & Efficiency", "accent_color": "#34D399", "params": {}}
            },
            {
                "beat_id": 6,
                "text": "Follow The Model Verse for daily deep-dives into how modern AI actually works under the hood.",
                "visual_focus": "Minimalist chalkboard outro with The Model Verse branding.",
                "highlight_words": {"The Model Verse": "#34D399"},
                "svo_action": {"subject": "The Model Verse", "action_verb": "demystifies", "direct_object": "Modern AI", "anchor_word": "Model", "semantic_role": "metric_evaluation"},
                "visual_blueprint": {"layout": "paper_figure", "title": "THE MODEL VERSE", "sub": "Autonomous Architectural Analysis", "accent_color": "#34D399", "params": {"title": "Outro"}}
            }
        ]

    spec = {
        "id": clean_id,
        "title": title,
        "category": cat,
        "domain_taxonomy": dom,
        "hook_tag": cat.upper().replace("_", " "),
        "beats": beats
    }
    return enforce_script_schema(spec, topic, category=cat)


class LLMRouter:
    """
    Unified multi-provider fallback router for script generation.
    Cascades across: Gemini -> Groq -> OpenRouter -> Ollama Cloud -> Deterministic Fallback.
    """

    def __init__(self) -> None:
        self.inception_models = [
            os.getenv("INCEPTION_MODEL", "mercury-3"),
        ]
        self.gemini_models = [
            os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash"),
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-flash-latest",
            "gemini-3.1-flash-lite",
        ]
        self.groq_models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
        ]
        self.openrouter_models = [
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemini-2.0-flash-exp:free",
            "mistralai/mistral-7b-instruct:free",
        ]
        self.ollama_models = [
            "gpt-oss:120b:cloud",
            "gemma4:31b:cloud",
            "gpt-oss:20b:cloud",
        ]

    def _inception_request(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_tokens: int = 8192,
    ) -> Optional[str]:
        """Call Inception's OpenAI-compatible Mercury API and return text."""
        if not quota_tracker.is_healthy("inception"):
            logger.info("⏩ [LLMRouter] Inception is marked EXHAUSTED in QuotaTracker. Skipping immediately.")
            return None

        api_key = os.getenv("INCEPTION_API_KEY")
        if not api_key:
            return None

        base_url = os.getenv("INCEPTION_BASE_URL", "https://api.inceptionlabs.ai/v1").rstrip("/")
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        for model_name in self.inception_models:
            try:
                logger.info(f"🧠 [LLMRouter] Attempting Inception model '{model_name}'...")
                response = requests.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model_name,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": 0.2,
                        "reasoning_effort": os.getenv("INCEPTION_REASONING_EFFORT", "low"),
                    },
                    timeout=float(os.getenv("INCEPTION_TIMEOUT_SECONDS", "45")),
                )

                if is_quota_error(response.status_code) or is_quota_error(response.text):
                    quota_tracker.record_exhausted("inception", f"Status {response.status_code}: {response.text[:500]}")
                    break

                if response.status_code != 200:
                    logger.warning(f"⚠️ [LLMRouter] Inception HTTP {response.status_code}: {response.text[:200]}")
                    continue

                data = response.json()
                choices = data.get("choices") if isinstance(data, dict) else None
                content = (
                    choices[0].get("message", {}).get("content", "")
                    if choices and isinstance(choices[0], dict)
                    else ""
                )
                if content and str(content).strip():
                    quota_tracker.record_success("inception")
                    logger.info(f"✅ [LLMRouter] Inception generation succeeded via '{model_name}'")
                    return str(content).strip()

                logger.warning("⚠️ [LLMRouter] Inception returned no visible content; trying the next provider.")
            except Exception as exc:
                if is_quota_error(exc):
                    quota_tracker.record_exhausted("inception", str(exc))
                    break
                logger.warning(f"⚠️ [LLMRouter] Inception error on '{model_name}': {exc}")

        quota_tracker.record_exhausted("inception", "All Inception models failed or returned empty content")
        return None

    def call_inception(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Generate a strict JSON script through Mercury, then parse it safely."""
        content = self._inception_request(
            prompt,
            system_instruction="You are a professional educational video director. Respond strictly with valid JSON.",
        )
        if not content:
            return None
        try:
            return robust_json_loads(sanitize_markdown_json(content))
        except Exception as exc:
            logger.warning(f"⚠️ [LLMRouter] Inception JSON parsing failed: {exc}")
            return None

    def call_inception_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> Optional[str]:
        """Generate raw text/code through Mercury."""
        return self._inception_request(prompt, system_instruction=system_instruction, max_tokens=4096)

    @staticmethod
    def _inception_enabled(provider_pref: str) -> bool:
        """Keep Mercury opt-in so merely storing a key never changes default routing."""
        return provider_pref == "inception" or os.getenv("ENABLE_INCEPTION_FALLBACK", "false").lower() in {
            "1", "true", "yes"
        }

    def call_gemini(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Invokes primary Gemini API, respecting QuotaHealthTracker and active mock hooks."""
        sg_mod = sys.modules.get("pipeline.script_generator")
        active_genai = getattr(sg_mod, "genai", None) if sg_mod is not None else None
        if active_genai is None and (sg_mod is None or not hasattr(sg_mod, "genai")):
            active_genai = genai

        if not quota_tracker.is_healthy("gemini"):
            logger.info("⏩ [LLMRouter] Gemini is marked EXHAUSTED in QuotaTracker. Skipping immediately.")
            return None

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key or active_genai is None:
            logger.info("ℹ️ [LLMRouter] Gemini API key not present or genai not installed. Skipping.")
            return None

        try:
            if hasattr(active_genai, "configure"):
                active_genai.configure(api_key=api_key)
        except Exception as e:
            logger.warning(f"⚠️ [LLMRouter] genai.configure failed: {e}")
            return None

        # Remove duplicate models while preserving preference order
        unique_models: List[str] = []
        for m in self.gemini_models:
            if m not in unique_models:
                unique_models.append(m)

        for model_name in unique_models:
            try:
                logger.info(f"🧠 [LLMRouter] Attempting Gemini model '{model_name}'...")
                model = active_genai.GenerativeModel(
                    model_name,
                    generation_config={"response_mime_type": "application/json"}
                )
                resp = model.generate_content(prompt)
                if resp and resp.text:
                    sanitized = sanitize_markdown_json(resp.text)
                    parsed = robust_json_loads(sanitized)
                    if parsed:
                        quota_tracker.record_success("gemini")
                        quota_tracker.record_success("gemini_vision")
                        logger.info(f"✅ [LLMRouter] Gemini script generation succeeded via '{model_name}'")
                        return parsed
            except Exception as e:
                err_msg = str(e)
                msg_lower = err_msg.lower()
                is_model_specific = (
                    "model:" in msg_lower
                    or "quota_dimensions" in msg_lower
                    or "limit: 500" in msg_lower
                    or "limit: 20" in msg_lower
                    or "404" in msg_lower
                )
                if is_model_specific:
                    logger.warning(
                        f"⚠️ [LLMRouter] Model-specific quota exceeded on '{model_name}'. "
                        f"Cascading to next available Gemini model..."
                    )
                    continue
                elif is_quota_error(e) or "resourceexhausted" in msg_lower or "429" in err_msg:
                    quota_tracker.record_exhausted("gemini", f"Quota error on {model_name}: {err_msg}")
                    quota_tracker.record_exhausted("gemini_vision", f"Quota error on {model_name}: {err_msg}")
                    logger.warning(f"🚫 [LLMRouter] Gemini quota exhausted on '{model_name}'. Breaking Gemini cascade.")
                    break
                else:
                    logger.warning(f"⚠️ [LLMRouter] Gemini error on '{model_name}': {e}. Trying next model...")

        # If all Gemini models failed or were exhausted in this attempt, mark exhausted
        quota_tracker.record_exhausted("gemini", "All Gemini models failed or exhausted")
        quota_tracker.record_exhausted("gemini_vision", "All Gemini models failed or exhausted")
        return None

    def call_groq(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Invokes secondary Groq free-tier / API endpoint."""
        if not quota_tracker.is_healthy("groq"):
            logger.info("⏩ [LLMRouter] Groq is marked EXHAUSTED in QuotaTracker. Skipping immediately.")
            return None

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        for model_name in self.groq_models:
            try:
                logger.info(f"🧠 [LLMRouter] Attempting Groq model '{model_name}'...")
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": "You are a professional educational video director. Respond strictly with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.2
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=25.0)
                if is_quota_error(resp.status_code) or is_quota_error(resp.text):
                    quota_tracker.record_exhausted("groq", f"Status {resp.status_code}: {resp.text}")
                    break

                if resp.status_code == 200:
                    try:
                        data = resp.json()
                    except Exception:
                        data = {}
                    choices = data.get("choices") if isinstance(data, dict) else None
                    content = choices[0].get("message", {}).get("content", "") if choices and isinstance(choices[0], dict) else ""
                    if content:
                        sanitized = sanitize_markdown_json(content)
                        try:
                            parsed = robust_json_loads(sanitized)
                        except Exception:
                            parsed = None
                        if parsed:
                            quota_tracker.record_success("groq")
                            logger.info(f"✅ [LLMRouter] Groq script generation succeeded via '{model_name}'")
                            return parsed
                else:
                    logger.warning(f"⚠️ [LLMRouter] Groq HTTP {resp.status_code}: {resp.text[:120]}")
            except Exception as e:
                if is_quota_error(e):
                    quota_tracker.record_exhausted("groq", str(e))
                    break
                logger.warning(f"⚠️ [LLMRouter] Groq exception on '{model_name}': {e}")

        quota_tracker.record_exhausted("groq", "All Groq models failed or unavailable")
        return None

    def call_openrouter(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Invokes tertiary OpenRouter free-tier endpoint."""
        if not quota_tracker.is_healthy("openrouter"):
            logger.info("⏩ [LLMRouter] OpenRouter is marked EXHAUSTED in QuotaTracker. Skipping immediately.")
            return None

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return None

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://themodelverse.in",
            "X-Title": "The Model Verse Shorts"
        }

        for model_name in self.openrouter_models:
            try:
                logger.info(f"🧠 [LLMRouter] Attempting OpenRouter model '{model_name}'...")
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": "You are a professional educational video director. Respond strictly with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"}
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=30.0)
                if is_quota_error(resp.status_code) or is_quota_error(resp.text):
                    quota_tracker.record_exhausted("openrouter", f"Status {resp.status_code}: {resp.text}")
                    break

                if resp.status_code == 200:
                    try:
                        data = resp.json()
                    except Exception:
                        data = {}
                    choices = data.get("choices") if isinstance(data, dict) else None
                    content = choices[0].get("message", {}).get("content", "") if choices and isinstance(choices[0], dict) else ""
                    if content:
                        sanitized = sanitize_markdown_json(content)
                        try:
                            parsed = robust_json_loads(sanitized)
                        except Exception:
                            parsed = None
                        if parsed:
                            quota_tracker.record_success("openrouter")
                            logger.info(f"✅ [LLMRouter] OpenRouter script generation succeeded via '{model_name}'")
                            return parsed
                else:
                    logger.warning(f"⚠️ [LLMRouter] OpenRouter HTTP {resp.status_code}: {resp.text[:120]}")
            except Exception as e:
                if is_quota_error(e):
                    quota_tracker.record_exhausted("openrouter", str(e))
                    break
                logger.warning(f"⚠️ [LLMRouter] OpenRouter exception on '{model_name}': {e}")

        quota_tracker.record_exhausted("openrouter", "All OpenRouter models failed or unavailable")
        return None

    def call_ollama(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Invokes Ollama Cloud models (gpt-oss:120b:cloud, gemma4:31b:cloud)."""
        active_ollama_cls = OllamaClient
        if not hasattr(active_ollama_cls, "mock_calls"):
            sg_mod = sys.modules.get("pipeline.script_generator")
            if sg_mod is not None and hasattr(sg_mod, "OllamaClient"):
                active_ollama_cls = getattr(sg_mod, "OllamaClient")

        if not quota_tracker.is_healthy("ollama"):
            logger.info("⏩ [LLMRouter] Ollama is marked EXHAUSTED in QuotaTracker. Skipping immediately.")
            return None

        ollama = active_ollama_cls(models=self.ollama_models)

        for candidate_model in self.ollama_models:
            try:
                logger.info(f"🧠 [LLMRouter] Attempting Ollama Cloud model '{candidate_model}'...")
                res = ollama.generate_completion(
                    prompt=prompt,
                    model=candidate_model,
                    format="json",
                    fallback_on_error=False,
                )
                if res:
                    data = res.to_dict() if hasattr(res, "to_dict") else dict(res)
                    if data:
                        quota_tracker.record_success("ollama")
                        logger.info(f"✅ [LLMRouter] Ollama Cloud script generation succeeded via '{candidate_model}'")
                        return data
            except Exception as e:
                if is_quota_error(e):
                    logger.warning(f"🚫 [LLMRouter] Ollama quota error on '{candidate_model}': {e}")
                    quota_tracker.record_exhausted("ollama", str(e))
                    break
                if isinstance(e, requests.exceptions.ConnectionError):
                    logger.warning(f"⚠️ [LLMRouter] Ollama host connection error ({e}). Breaking candidate cascade.")
                    quota_tracker.record_exhausted("ollama", f"Ollama connection refused: {e}")
                    break
                logger.warning(f"⚠️ [LLMRouter] Ollama Cloud candidate '{candidate_model}' error: {e}. Trying next...")

        quota_tracker.record_exhausted("ollama", "All Ollama models failed or unavailable")
        return None

    def route_script_generation(
        self,
        prompt: str,
        topic: str,
        category: Optional[str] = None,
        arxiv_meta: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], str]:
        """
        Executes cascading fallback across all available providers.
        Guarantees a valid, strictly enforced 6-beat JSON schema is returned.
        Returns (spec_dict, provider_name).
        """
        provider_pref = os.getenv("LLM_PROVIDER", "").lower()
        inception_enabled = self._inception_enabled(provider_pref)

        # If user explicitly requested a specific provider, try it first
        if provider_pref == "inception":
            raw_spec = self.call_inception(prompt)
            if raw_spec:
                return enforce_script_schema(raw_spec, topic, category), "inception"
        elif provider_pref == "ollama":
            raw_spec = self.call_ollama(prompt)
            if raw_spec:
                return enforce_script_schema(raw_spec, topic, category), "ollama"
        elif provider_pref == "groq":
            raw_spec = self.call_groq(prompt)
            if raw_spec:
                return enforce_script_schema(raw_spec, topic, category), "groq"
        elif provider_pref == "openrouter":
            raw_spec = self.call_openrouter(prompt)
            if raw_spec:
                return enforce_script_schema(raw_spec, topic, category), "openrouter"

        # 1. Primary: Gemini (if not already tried via provider_pref)
        if provider_pref not in ("ollama", "groq", "openrouter", "inception"):
            raw_spec = self.call_gemini(prompt)
            if raw_spec:
                return enforce_script_schema(raw_spec, topic, category), "gemini"

        # 2. Fast OpenAI-compatible fallback: Mercury 3
        if inception_enabled and provider_pref != "inception":
            raw_spec = self.call_inception(prompt)
            if raw_spec:
                return enforce_script_schema(raw_spec, topic, category), "inception"

        # 3. Secondary: Groq (if not already tried)
        if provider_pref != "groq":
            raw_spec = self.call_groq(prompt)
            if raw_spec:
                return enforce_script_schema(raw_spec, topic, category), "groq"

        # 4. Tertiary: OpenRouter Free Tier (if not already tried)
        if provider_pref != "openrouter":
            raw_spec = self.call_openrouter(prompt)
            if raw_spec:
                return enforce_script_schema(raw_spec, topic, category), "openrouter"

        # 5. Quaternary: Ollama Cloud (if not already tried)
        if provider_pref != "ollama":
            raw_spec = self.call_ollama(prompt)
            if raw_spec:
                return enforce_script_schema(raw_spec, topic, category), "ollama"

        # 5. Deterministic Zero-Failure Architectural Fallback
        logger.warning(
            f"⚡ [LLMRouter] All cloud/local LLM providers unavailable or quota exhausted. "
            f"Seamlessly applying deterministic 6-beat architectural generator for '{topic}'."
        )
        fallback_spec = generate_deterministic_fallback_script(
            topic=topic,
            category=category,
            arxiv_meta=arxiv_meta
        )
        return fallback_spec, "deterministic_fallback"

    def call_gemini_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        preferred_model: Optional[str] = None
    ) -> Optional[str]:
        """Invokes primary Gemini API for raw text/code generation, cascading across models."""
        sg_mod = sys.modules.get("pipeline.script_generator")
        active_genai = getattr(sg_mod, "genai", None) if sg_mod is not None else None
        if active_genai is None and (sg_mod is None or not hasattr(sg_mod, "genai")):
            active_genai = genai

        if not quota_tracker.is_healthy("gemini"):
            logger.info("⏩ [LLMRouter] Gemini is marked EXHAUSTED in QuotaTracker. Skipping immediately.")
            return None

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key or active_genai is None:
            logger.info("ℹ️ [LLMRouter] Gemini API key not present or genai not installed. Skipping.")
            return None

        try:
            if hasattr(active_genai, "configure"):
                active_genai.configure(api_key=api_key)
        except Exception as e:
            logger.warning(f"⚠️ [LLMRouter] genai.configure failed: {e}")
            return None

        models_to_try: List[str] = []
        if preferred_model:
            models_to_try.append(preferred_model)
        models_to_try.extend(getattr(self, "gemini_models", []))
        models_to_try.extend([
            os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash"),
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-flash-latest",
        ])
        unique_models: List[str] = []
        for m in models_to_try:
            if m and m not in unique_models:
                unique_models.append(m)

        for model_name in unique_models:
            try:
                logger.info(f"🧠 [LLMRouter] Attempting Gemini text generation model '{model_name}'...")
                if system_instruction:
                    model = active_genai.GenerativeModel(
                        model_name,
                        system_instruction=system_instruction
                    )
                else:
                    model = active_genai.GenerativeModel(model_name)
                resp = model.generate_content(prompt)
                if resp and resp.text:
                    quota_tracker.record_success("gemini")
                    quota_tracker.record_success("gemini_vision")
                    logger.info(f"✅ [LLMRouter] Gemini text generation succeeded via '{model_name}'")
                    return resp.text.strip()
            except Exception as e:
                err_msg = str(e)
                msg_lower = err_msg.lower()
                is_model_specific = (
                    "model:" in msg_lower
                    or "quota_dimensions" in msg_lower
                    or "limit: 500" in msg_lower
                    or "limit: 20" in msg_lower
                    or "404" in msg_lower
                )
                if is_model_specific:
                    logger.warning(
                        f"⚠️ [LLMRouter] Model-specific quota exceeded on '{model_name}'. "
                        f"Cascading to next available Gemini model..."
                    )
                    continue
                elif is_quota_error(e) or "resourceexhausted" in msg_lower or "429" in err_msg:
                    logger.warning(
                        f"⚠️ [LLMRouter] Gemini quota error on '{model_name}': {err_msg}. "
                        f"Trying next Gemini model..."
                    )
                    continue
                else:
                    logger.warning(f"⚠️ [LLMRouter] Gemini error on '{model_name}': {e}. Trying next model...")
                    continue

        quota_tracker.record_exhausted("gemini", "All Gemini models failed or exhausted")
        quota_tracker.record_exhausted("gemini_vision", "All Gemini models failed or exhausted")
        return None

    def call_groq_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> Optional[str]:
        """Invokes secondary Groq endpoint for raw text/code generation."""
        if not quota_tracker.is_healthy("groq"):
            logger.info("⏩ [LLMRouter] Groq is marked EXHAUSTED in QuotaTracker. Skipping immediately.")
            return None

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        for model_name in self.groq_models:
            try:
                logger.info(f"🧠 [LLMRouter] Attempting Groq text generation model '{model_name}'...")
                payload = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": 0.2
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=25.0)
                if is_quota_error(resp.status_code) or is_quota_error(resp.text):
                    quota_tracker.record_exhausted("groq", f"Status {resp.status_code}: {resp.text}")
                    break

                if resp.status_code == 200:
                    try:
                        data = resp.json()
                    except Exception:
                        data = {}
                    choices = data.get("choices") if isinstance(data, dict) else None
                    content = choices[0].get("message", {}).get("content", "") if choices and isinstance(choices[0], dict) else ""
                    if content:
                        quota_tracker.record_success("groq")
                        logger.info(f"✅ [LLMRouter] Groq text generation succeeded via '{model_name}'")
                        return content.strip()
                else:
                    logger.warning(f"⚠️ [LLMRouter] Groq HTTP {resp.status_code}: {resp.text[:120]}")
            except Exception as e:
                if is_quota_error(e):
                    quota_tracker.record_exhausted("groq", str(e))
                    break
                logger.warning(f"⚠️ [LLMRouter] Groq exception on '{model_name}': {e}")

        quota_tracker.record_exhausted("groq", "All Groq models failed or unavailable")
        return None

    def call_openrouter_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> Optional[str]:
        """Invokes tertiary OpenRouter endpoint for raw text/code generation."""
        if not quota_tracker.is_healthy("openrouter"):
            logger.info("⏩ [LLMRouter] OpenRouter is marked EXHAUSTED in QuotaTracker. Skipping immediately.")
            return None

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return None

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://themodelverse.in",
            "X-Title": "The Model Verse Shorts"
        }

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        for model_name in self.openrouter_models:
            try:
                logger.info(f"🧠 [LLMRouter] Attempting OpenRouter text generation model '{model_name}'...")
                payload = {
                    "model": model_name,
                    "messages": messages
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=30.0)
                if is_quota_error(resp.status_code) or is_quota_error(resp.text):
                    quota_tracker.record_exhausted("openrouter", f"Status {resp.status_code}: {resp.text}")
                    break

                if resp.status_code == 200:
                    try:
                        data = resp.json()
                    except Exception:
                        data = {}
                    choices = data.get("choices") if isinstance(data, dict) else None
                    content = choices[0].get("message", {}).get("content", "") if choices and isinstance(choices[0], dict) else ""
                    if content:
                        quota_tracker.record_success("openrouter")
                        logger.info(f"✅ [LLMRouter] OpenRouter text generation succeeded via '{model_name}'")
                        return content.strip()
                else:
                    logger.warning(f"⚠️ [LLMRouter] OpenRouter HTTP {resp.status_code}: {resp.text[:120]}")
            except Exception as e:
                if is_quota_error(e):
                    quota_tracker.record_exhausted("openrouter", str(e))
                    break
                logger.warning(f"⚠️ [LLMRouter] OpenRouter exception on '{model_name}': {e}")

        quota_tracker.record_exhausted("openrouter", "All OpenRouter models failed or unavailable")
        return None

    def call_ollama_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> Optional[str]:
        """Invokes Ollama Cloud models for raw text/code generation."""
        active_ollama_cls = OllamaClient
        if not hasattr(active_ollama_cls, "mock_calls"):
            sg_mod = sys.modules.get("pipeline.script_generator")
            if sg_mod is not None and hasattr(sg_mod, "OllamaClient"):
                active_ollama_cls = getattr(sg_mod, "OllamaClient")

        if not quota_tracker.is_healthy("ollama"):
            logger.info("⏩ [LLMRouter] Ollama is marked EXHAUSTED in QuotaTracker. Skipping immediately.")
            return None

        ollama = active_ollama_cls(models=self.ollama_models)

        for candidate_model in self.ollama_models:
            try:
                logger.info(f"🧠 [LLMRouter] Attempting Ollama Cloud text generation model '{candidate_model}'...")
                res = ollama.generate_completion(
                    prompt=prompt,
                    model=candidate_model,
                    system=system_instruction,
                    format=None,
                    fallback_on_error=False,
                )
                if res:
                    txt = getattr(res, "text", None) or (res.get("response") if isinstance(res, dict) else str(res))
                    if txt and str(txt).strip():
                        quota_tracker.record_success("ollama")
                        logger.info(f"✅ [LLMRouter] Ollama Cloud text generation succeeded via '{candidate_model}'")
                        return str(txt).strip()
            except Exception as e:
                if is_quota_error(e):
                    logger.warning(f"🚫 [LLMRouter] Ollama quota error on '{candidate_model}': {e}")
                    quota_tracker.record_exhausted("ollama", str(e))
                    break
                if isinstance(e, requests.exceptions.ConnectionError):
                    logger.warning(f"⚠️ [LLMRouter] Ollama host connection error ({e}). Breaking candidate cascade.")
                    quota_tracker.record_exhausted("ollama", f"Ollama connection refused: {e}")
                    break
                logger.warning(f"⚠️ [LLMRouter] Ollama Cloud candidate '{candidate_model}' error: {e}. Trying next...")

        quota_tracker.record_exhausted("ollama", "All Ollama models failed or unavailable")
        return None

    def generate_text_with_cascade(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        preferred_model: Optional[str] = None
    ) -> Optional[str]:
        """
        Cascades text/code generation across:
        Gemini -> Groq -> OpenRouter -> Ollama Cloud.
        Catches 429 and quota exhaustion and seamlessly fails over to healthy providers.
        """
        provider_pref = os.getenv("LLM_PROVIDER", "").lower()
        inception_enabled = self._inception_enabled(provider_pref)

        # If user explicitly specified a provider preference, try it first
        if provider_pref == "inception":
            res = self.call_inception_text(prompt, system_instruction)
            if res:
                return res
        elif provider_pref == "ollama":
            res = self.call_ollama_text(prompt, system_instruction)
            if res:
                return res
        elif provider_pref == "groq":
            res = self.call_groq_text(prompt, system_instruction)
            if res:
                return res
        elif provider_pref == "openrouter":
            res = self.call_openrouter_text(prompt, system_instruction)
            if res:
                return res

        # 1. Primary: Gemini (if not already tried)
        if provider_pref not in ("ollama", "groq", "openrouter", "inception"):
            res = self.call_gemini_text(prompt, system_instruction, preferred_model=preferred_model)
            if res:
                return res

        # 2. Fast OpenAI-compatible fallback: Mercury 3
        if inception_enabled and provider_pref != "inception":
            res = self.call_inception_text(prompt, system_instruction)
            if res:
                return res

        # 3. Secondary: Groq (if not already tried)
        if provider_pref != "groq":
            res = self.call_groq_text(prompt, system_instruction)
            if res:
                return res

        # 4. Tertiary: OpenRouter (if not already tried)
        if provider_pref != "openrouter":
            res = self.call_openrouter_text(prompt, system_instruction)
            if res:
                return res

        # 5. Quaternary: Ollama Cloud (if not already tried)
        if provider_pref != "ollama":
            res = self.call_ollama_text(prompt, system_instruction)
            if res:
                return res

        logger.warning("⚡ [LLMRouter] All providers failed or quota exhausted for text/code generation.")
        return None


llm_router = LLMRouter()


def generate_text_with_cascade(
    prompt: str,
    system_instruction: Optional[str] = None,
    preferred_model: Optional[str] = None
) -> Optional[str]:
    """Module-level function forwarding to llm_router.generate_text_with_cascade."""
    return llm_router.generate_text_with_cascade(
        prompt,
        system_instruction=system_instruction,
        preferred_model=preferred_model
    )
