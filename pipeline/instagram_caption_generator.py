"""
The Model Verse — Instagram Caption & Viral Post Generator
Generates high-converting, viral, technical Instagram captions and post metadata
using the official TheModelverse prompt guidelines and OmniRoute LLM cascading.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.llm_router import llm_router
from pipeline.json_utils import robust_json_loads

INSTAGRAM_SYSTEM_PROMPT = """You are the Lead Social Media Strategist & Technical AI Content Creator for TheModelverse (https://www.themodelverse.in), the definitive foundation model benchmark catalog and technical database.
Your task is to take structured technical model metadata and turn it into high-converting, viral, technical Instagram captions.

### INSTAGRAM POSTING RULES:
1. THE HOOK: The first 1-2 lines must immediately stop the scroll (mention the model name, creator, and its biggest breakthrough or milestone). Do not use boring intros like "Introducing..." or "Check out...".
2. TECHNICAL SPECS: Break down parameters, context window, benchmark scores, and pricing into clean, bulleted, visually separated emoji points.
3. THE TAKEAWAY: Explain in 1-2 sentences who this model is best for (e.g., agentic workflows, low-latency reasoning, edge devices, enterprise coding).
4. CALL TO ACTION (CTA): Direct users to inspect full benchmarks, latency charts, and live comparisons at TheModelverse via the link in bio.
5. HASHTAGS: Provide 15-20 highly targeted AI, developer, and machine learning hashtags appended at the end with proper spacing.
6. FORMATTING: Use clean paragraph line breaks. Never output markdown bold asterisks (**) inside the caption text, as Instagram does not parse markdown syntax—use unicode styling or clear uppercase headers instead.
7. OUTPUT: Output ONLY a valid JSON object matching the requested schema. No surrounding chat or markdown code fence blocks if JSON mode is active.
"""

INSTAGRAM_USER_PROMPT_TEMPLATE = """Generate a viral, technically authoritative Instagram post for the following foundation model on TheModelverse:
=== INPUT DATA ===
Model Name: {model_name}
Provider / Creator: {provider}
Category: {category}
Context Window: {context_window}
Active / Total Parameters: {parameters}
Key Benchmarks: {top_benchmarks}
Pricing: {pricing}
Key Highlights / Architecture: {key_highlights}
TheModelverse URL: {model_url}
==================
Output a JSON object with the following exact keys:
{{
  "hook": "Single line high-impact hook for preview thumbnails or reels",
  "caption": "The complete formatted Instagram caption including hook, technical specs, takeaway, and CTA (without hashtags)",
  "hashtags": "Space-separated block of 15-20 high-reach hashtags",
  "first_comment": "A follow-up engagement question + link-in-bio reminder for the first comment",
  "alt_text": "Clean accessibility alt text describing the model card poster"
}}
"""


def strip_markdown_bold(text: str) -> str:
    """Removes all markdown bold asterisks (**) from text as Instagram doesn't parse markdown."""
    if not text:
        return ""
    # Strip double asterisks
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    # Strip remaining stray single or double asterisks used for emphasis
    cleaned = re.sub(r"(?<!\*)\*(?!\*)", "", cleaned)
    return cleaned.strip()


def extract_template_variables_from_spec(spec: Dict[str, Any]) -> Dict[str, str]:
    """Extracts and normalizes dynamic automation keys from a video specification."""
    title = spec.get("title", "AI Architecture Deep Dive")
    category = spec.get("category", "mechanism_deepdive")
    meta = spec.get("metadata", {})
    beats = spec.get("beats", [])

    # Infer Model / Paper Name
    model_name = meta.get("model_name")
    if not model_name:
        if ":" in title:
            model_name = title.split(":")[0].strip()
        elif " - " in title:
            model_name = title.split(" - ")[0].strip()
        else:
            model_name = title.replace("#Shorts", "").strip()

    # Provider / Lab
    provider = (
        meta.get("provider") or
        meta.get("authors") or
        meta.get("lab") or
        "Open-Source AI Research"
    )

    # Context window & Parameters
    context_window = (
        meta.get("context_window") or
        meta.get("context") or
        "Infinite Context via Recurrent State"
    )
    parameters = (
        meta.get("parameters") or
        meta.get("model_size") or
        meta.get("quantization", "Multi-bit Quantized Weights & Activations")
    )

    # Benchmarks & Metrics
    b5_text = beats[-2].get("text", "") if len(beats) >= 2 else ""
    raw_bench = (
        meta.get("top_benchmarks") or
        meta.get("benchmarks") or
        meta.get("payoff_stat") or
        (b5_text if b5_text else "State-of-the-art inference efficiency")
    )
    if isinstance(raw_bench, list):
        bench_items = []
        for item in raw_bench:
            if isinstance(item, dict):
                name = item.get("name", "Metric")
                score_a = item.get("score_a", "")
                bench_items.append(f"{name}: {score_a}")
            else:
                bench_items.append(str(item))
        top_benchmarks = " | ".join(bench_items)
    elif isinstance(raw_bench, dict):
        top_benchmarks = " | ".join(f"{k}: {v}" for k, v in raw_bench.items())
    else:
        top_benchmarks = str(raw_bench)

    # Pricing or compute efficiency
    pricing = (
        meta.get("pricing") or
        meta.get("compute_reduction") or
        "68.7% Memory Reduction vs FP32"
    )

    # Key highlights
    b1_text = beats[0].get("text", "") if beats else ""
    key_highlights = (
        meta.get("key_highlights") or
        f"{b1_text} {b5_text}".strip() or
        title
    )

    # Model canonical URL
    slug = re.sub(r"[^a-z0-9]+", "-", model_name.lower()).strip("-")
    model_url = (
        meta.get("model_url") or
        meta.get("canonical_url") or
        f"https://www.themodelverse.in/models/{slug}"
    )

    return {
        "model_name": model_name,
        "provider": provider,
        "category": category.replace("_", " ").title(),
        "context_window": context_window,
        "parameters": str(parameters),
        "top_benchmarks": str(top_benchmarks),
        "pricing": str(pricing),
        "key_highlights": str(key_highlights),
        "model_url": model_url,
    }


def generate_fallback_caption(vars_dict: Dict[str, str]) -> Dict[str, str]:
    """Generates a high-quality deterministic Instagram post if LLM is offline."""
    m_name = vars_dict["model_name"]
    prov = vars_dict["provider"]
    bench = vars_dict["top_benchmarks"]
    highlights = vars_dict["key_highlights"]
    url = vars_dict["model_url"]

    hook = f"{m_name} from {prov} is redefining state-of-the-art AI efficiency."

    caption = (
        f"{m_name} just solved one of the hardest engineering bottlenecks in modern AI.\n\n"
        f"Here are the critical technical specs you need to know:\n\n"
        f"⚡️ CORE INNOVATION: {highlights}\n"
        f"🧠 ARCHITECTURE: {vars_dict['parameters']}\n"
        f"📊 BENCHMARK PAYOFF: {bench}\n"
        f"💰 HARDWARE EFFICIENCY: {vars_dict['pricing']}\n"
        f"🌐 CONTEXT CAPABILITY: {vars_dict['context_window']}\n\n"
        f"THE TAKEAWAY:\n"
        f"This completely shifts the cost-to-performance curve for enterprise inference and high-throughput production models.\n\n"
        f"Compare {m_name} and inspect complete benchmark teardowns at TheModelverse.\n\n"
        f"🔗 Full benchmark teardown & live comparisons: link in bio!"
    )

    hashtags = (
        f"#TheModelverse #{re.sub(r'[^a-zA-Z0-9]', '', m_name)} #ArtificialIntelligence "
        f"#MachineLearning #DeepLearning #LLM #GPUOptimization #InferenceEfficiency "
        f"#AIResearch #arXiv #ComputerScience #SoftwareEngineering #DataScience #AIBenchmarks #TechReels"
    )

    first_comment = (
        f"What AI architecture or model breakthrough should we tear down next? Drop your thoughts below 👇\n\n"
        f"Full technical breakdown & interactive benchmarks at {url}"
    )

    alt_text = (
        f"TheModelverse technical architecture card for {m_name} highlighting "
        f"{bench} and core design specifications."
    )

    return {
        "hook": hook,
        "caption": strip_markdown_bold(caption),
        "hashtags": hashtags,
        "first_comment": strip_markdown_bold(first_comment),
        "alt_text": alt_text,
    }


def generate_instagram_post(
    spec: Dict[str, Any],
    model_override: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Generates a viral, technically authoritative Instagram post JSON payload
    using the official system prompt and OmniRoute cascade.
    """
    vars_dict = extract_template_variables_from_spec(spec)
    if model_override:
        vars_dict.update(model_override)

    user_prompt = INSTAGRAM_USER_PROMPT_TEMPLATE.format(**vars_dict)

    try:
        raw_response = llm_router.generate_text_with_cascade(
            prompt=user_prompt,
            system_instruction=INSTAGRAM_SYSTEM_PROMPT
        )
        if raw_response:
            data = robust_json_loads(raw_response)
            if isinstance(data, dict) and "caption" in data and "hashtags" in data:
                # Enforce rule 6 (No markdown bold in caption)
                data["caption"] = strip_markdown_bold(data["caption"])
                if "first_comment" in data:
                    data["first_comment"] = strip_markdown_bold(data["first_comment"])
                if "hook" not in data:
                    data["hook"] = vars_dict["model_name"]
                if "alt_text" not in data:
                    data["alt_text"] = f"Technical architecture card for {vars_dict['model_name']}"
                return data
    except Exception as e:
        print(f"⚠️ Instagram caption LLM generation encountered error ({e}). Using deterministic fallback.")

    return generate_fallback_caption(vars_dict)


def format_full_caption_with_hashtags(post_data: Dict[str, str]) -> str:
    """Formats the final text passed to Meta Graph API caption parameter with clean dots spacing."""
    caption = post_data.get("caption", "").strip()
    hashtags = post_data.get("hashtags", "").strip()

    if hashtags:
        return f"{caption}\n\n.\n.\n.\n{hashtags}"
    return caption
