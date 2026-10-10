"""
The Model Verse — LinkedIn Copy & Technical Post Generator
Crafts high-converting, authoritative LinkedIn posts optimized for the LinkedIn algorithm.

Key Optimization Rules:
  1. Arresting 2-line hook before the fold to drive the "...see more" click (Dwell Time multiplier)
  2. Clear architectural breakdown with bulleted mechanism details and hard benchmarks
  3. Strict zero external links in the main post body to prevent the 50-70% outbound reach penalty
  4. Auto-generated first comment with paper and TheModelVerse links + Socratic discussion prompt
  5. 3-5 high-relevance technical hashtags
"""

import re
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.llm_router import llm_router
from pipeline.json_utils import robust_json_loads

LINKEDIN_SYSTEM_PROMPT = """You are the Principal AI Research Scientist & Lead Technical Architect for The Model Verse (https://www.themodelverse.in).
Your audience on LinkedIn consists of senior ML engineers, research scientists, AI founders, and engineering leaders.

Craft an authoritative, technically rigorous LinkedIn post breaking down a breakthrough foundation model or AI architecture.

### LINKEDIN ALGORITHM & FORMATTING RULES:
1. THE HOOK (First 2-3 lines):
   - Arresting, contrarian problem statement or counter-intuitive insight.
   - Do NOT use greeting fluff ("Hope you're having a great week!", "Excited to share!").
   - Must force the user to click "...see more" to maximize dwell time.
2. THE TECHNICAL MECHANISM:
   - Break down how the architecture works with concise bullet points (•).
   - Use precise technical terminology (e.g., KV-cache eviction, Hadamard rotations, sensitivity profiling).
3. HARD BENCHMARKS & NUMBERS:
   - Quantitative impact: VRAM savings, tokens/second speedup, perplexity drop vs FP16.
4. OUTBOUND LINK RULE (STRICT):
   - NEVER place URLs in the commentary text! LinkedIn's algorithm cuts post reach by 50-70% if outbound links are present in the body.
   - Conclude the post with: "📄 Primary paper and interactive model card linked in the comments below ⬇️"
5. HASHTAGS:
   - Exactly 3 to 5 high-signal technical hashtags at the very end (e.g. #MachineLearning #ArtificialIntelligence #SystemML #LLMs).

OUTPUT FORMAT:
Output ONLY a valid JSON object matching this schema:
{
  "hook": "First 1-2 lines before the fold",
  "commentary": "Full post text without external URLs",
  "first_comment": "First comment containing paper link, TheModelverse link, and an engaging technical discussion prompt",
  "hashtags": ["#MachineLearning", "#LLMs", "#DeepLearning"]
}
"""

LINKEDIN_USER_PROMPT_TEMPLATE = """Generate an authoritative technical LinkedIn post for this breakthrough:

=== BREAKTHROUGH DATA ===
Title: {title}
Category: {category}
ID: {id}
Source / Paper: {source_url}
ModelVerse URL: {modelverse_url}
Beat 1 (The Hook): {beat_1}
Beat 2 (The Flaw): {beat_2}
Beat 3 (The Core Mechanism): {beat_3}
Beat 4 (The Mathematics): {beat_4}
Beat 5 (The Benchmark): {beat_5}
Beat 6 (The Takeaway): {beat_6}
=========================

Output the JSON object with "hook", "commentary", "first_comment", and "hashtags".
"""


def build_fallback_linkedin_post(spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constructs a deterministic, high-impact LinkedIn post directly from the spec.
    Ensures zero external links in the commentary, placing them safely in the first comment.
    """
    title = spec.get("title", "Frontier AI Architecture Deep Dive")
    spec_id = spec.get("id", "ai_breakthrough")
    beats = spec.get("beats", [])

    def _get_beat(idx: int) -> str:
        if 0 <= idx < len(beats):
            b = beats[idx]
            return b.get("text") or b.get("narration") or b.get("script") or ""
        return ""

    b1 = re.sub(r"\s+", " ", _get_beat(0)).strip()
    b2 = re.sub(r"\s+", " ", _get_beat(1)).strip()
    b3 = re.sub(r"\s+", " ", _get_beat(2)).strip()
    b4 = re.sub(r"\s+", " ", _get_beat(3)).strip()
    b5 = re.sub(r"\s+", " ", _get_beat(4)).strip()
    b6 = re.sub(r"\s+", " ", _get_beat(5)).strip()

    clean_title = title.split(":", 1)[0].strip() if ":" in title else title.replace("#Shorts", "").strip()

    arxiv_id = spec.get("arxiv_id")
    canonical_url = spec.get("canonical_url")
    if arxiv_id:
        source_url = f"https://arxiv.org/abs/{arxiv_id}"
    elif canonical_url:
        source_url = canonical_url
    else:
        source_url = "https://themodelverse.in"

    modelverse_url = f"https://themodelverse.in/models/{spec_id}"

    hook = b1 if b1 else f"Why conventional approaches to {clean_title} fail when scaling to production."

    commentary_parts = [
        f"{hook}\n",
        f"Most implementations hit a wall when scaling inference:\n",
        f"• The Bottleneck: {b2 if b2 else 'Uniform quantization treats all states equally, causing catastrophic accuracy drift.'}",
        f"• The Architecture: {b3 if b3 else 'Sensitivity analysis isolates which rows and parameters dominate propagation error.'}",
        f"• The Math: {b4 if b4 else 'Jointly optimizing row-level scaling factors keeps state updates bounded in cache.'}",
        f"• The Benchmark: {b5 if b5 else 'Delivers massive memory reductions while preserving full FP16 perplexity.'}\n",
        f"Key Engineering Takeaway:\n{b6 if b6 else 'Selective precision allocation outperforms uniform quantization across large context windows.'}\n",
        f"Watch the full 60-second animated mechanism walkthrough attached above.\n",
        f"📄 Paper & interactive architecture model card are linked in the comments below ⬇️\n",
        f"#MachineLearning #ArtificialIntelligence #DeepLearning #LLMs #SystemML"
    ]

    commentary = "\n".join(commentary_parts)

    first_comment = (
        f"🔗 Links & Primary Research:\n\n"
        f"📄 arXiv Paper: {source_url}\n"
        f"⚡ Interactive Architecture Card: {modelverse_url}\n\n"
        f"Have you tested state compression or low-bit quantization in your production pipelines? "
        f"What is your tolerance threshold for perplexity drift?"
    )

    return {
        "hook": hook,
        "commentary": commentary,
        "first_comment": first_comment,
        "hashtags": ["#MachineLearning", "#ArtificialIntelligence", "#DeepLearning", "#LLMs", "#SystemML"]
    }


def generate_linkedin_post(spec: Dict[str, Any], use_llm: bool = True) -> Dict[str, Any]:
    """
    Generates an authoritative LinkedIn post from a video specification.
    Attempts OmniRoute LLM cascading first, falling back to deterministic heuristic post.
    Guarantees zero outbound URLs in commentary to protect algorithm reach.
    """
    title = spec.get("title", "Frontier AI Architecture Deep Dive")
    spec_id = spec.get("id", "ai_breakthrough")
    category = spec.get("category", "mechanism_deepdive")
    beats = spec.get("beats", [])

    arxiv_id = spec.get("arxiv_id")
    canonical_url = spec.get("canonical_url")
    if arxiv_id:
        source_url = f"https://arxiv.org/abs/{arxiv_id}"
    elif canonical_url:
        source_url = canonical_url
    else:
        source_url = "https://themodelverse.in"

    modelverse_url = f"https://themodelverse.in/models/{spec_id}"

    if use_llm:
        def _get_text(idx: int) -> str:
            if idx < len(beats):
                b = beats[idx]
                return b.get("text") or b.get("narration") or b.get("script") or ""
            return ""

        user_prompt = LINKEDIN_USER_PROMPT_TEMPLATE.format(
            title=title,
            category=category,
            id=spec_id,
            source_url=source_url,
            modelverse_url=modelverse_url,
            beat_1=_get_text(0),
            beat_2=_get_text(1),
            beat_3=_get_text(2),
            beat_4=_get_text(3),
            beat_5=_get_text(4),
            beat_6=_get_text(5),
        )

        try:
            response_text = llm_router.generate_text_with_cascade(
                prompt=user_prompt,
                system_instruction=LINKEDIN_SYSTEM_PROMPT
            )
            if response_text:
                parsed = robust_json_loads(response_text)
                if isinstance(parsed, dict) and "commentary" in parsed:
                    commentary = parsed["commentary"]
                    # Safety check: Strip any external URLs that LLM might have placed in commentary
                    commentary_clean = re.sub(r"https?://\S+", "", commentary).strip()
                    if "linked in the comments" not in commentary_clean.lower():
                        commentary_clean += "\n\n📄 Paper & interactive model card linked in the comments below ⬇️"

                    parsed["commentary"] = commentary_clean
                    return parsed
        except Exception as e:
            print(f"ℹ️ LLM LinkedIn post generation failed or fell back: {e}. Using deterministic post generator.")

    return build_fallback_linkedin_post(spec)
