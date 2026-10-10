"""
The Model Verse — X (Twitter) Technical Thread Generator
Crafts high-engagement, viral 4-tweet technical threads tailored for the X algorithm.
Optimized for:
  - Tweet 1: Video lead with contrarian hook and zero external links (to protect reach)
  - Tweet 2: Deep architectural / mathematical mechanism breakdown
  - Tweet 3: Quantitative benchmarks, latency, VRAM reduction, and throughput
  - Tweet 4: Primary sources (arXiv/official lab link), TheModelverse interactive link, and CTA
"""

import re
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.llm_router import llm_router
from pipeline.json_utils import robust_json_loads

# X (Twitter) Character Limits & Weights
TWITTER_MAX_CHARS = 280
TWITTER_URL_LENGTH = 23  # All URLs count as 23 characters on X via t.co

URL_REGEX = re.compile(r"https?://\S+")

X_THREAD_SYSTEM_PROMPT = """You are the Principal AI Research Scientist & Lead Technical Writer for The Model Verse (@themodelverrse).
Your audience consists of senior ML engineers, research scientists, and AI founders on X (Twitter).

You craft high-signal, punchy, 4-tweet technical breakdown threads accompanying 60-second animated video explainers.

### X ALGORITHM & WRITING RULES:
1. TWEET 1 (THE HOOK & VIDEO LEAD):
   - Contrarian, high-curiosity hook highlighting the core breakthrough or counter-intuitive insight.
   - NO AI buzzwords or fluff ("In the ever-evolving world of AI...", "Excited to share...").
   - ZERO EXTERNAL LINKS IN TWEET 1! External links are heavily penalized by X's algorithm. End with "Watch the 60-second mechanism breakdown below 🧵👇"
   - STRICT LIMIT: <= 270 characters.

2. TWEET 2 (THE CORE MECHANISM):
   - The mathematical or architectural trick that makes it work.
   - Precise technical terms (e.g., Hadamard rotations, KV-cache compression, recurrent states).
   - Use concise bullet points (•) or numbered steps.
   - STRICT LIMIT: <= 270 characters.

3. TWEET 3 (BENCHMARKS & HARD NUMBERS):
   - Concrete numbers: VRAM footprint, tokens/sec, perplexity drop vs FP16, latency speedup.
   - What this unlocks in practice (e.g. running 70B models on a single consumer GPU).
   - STRICT LIMIT: <= 270 characters.

4. TWEET 4 (PRIMARY SOURCES & CTA):
   - Direct link to paper/source and interactive model card on TheModelVerse.
   - Clear call to action: "Follow @themodelverrse for daily breakdowns of frontier AI papers."
   - STRICT LIMIT: <= 270 characters (accounting for 23 chars per link).

OUTPUT FORMAT:
Output ONLY a valid JSON object matching this schema:
{
  "tweets": [
    "Tweet 1 text...",
    "Tweet 2 text...",
    "Tweet 3 text...",
    "Tweet 4 text..."
  ]
}
"""

X_USER_PROMPT_TEMPLATE = """Generate a 4-tweet technical thread for this breakthrough:

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

Output the JSON object with the "tweets" list containing exactly 4 tweets. Each tweet MUST be <= 270 characters.
"""


def calculate_tweet_length(text: str) -> int:
    """
    Calculates the effective character length of a tweet on X.
    Any URL is normalized to 23 characters (standard t.co wrapping).
    """
    if not text:
        return 0

    urls = URL_REGEX.findall(text)
    effective_text = URL_REGEX.sub("", text)
    url_chars = len(urls) * TWITTER_URL_LENGTH
    return len(effective_text) + url_chars


def truncate_to_tweet_limit(text: str, max_chars: int = TWITTER_MAX_CHARS) -> str:
    """
    Safely trims a tweet to stay strictly within max_chars while preserving URLs.
    """
    text = text.strip()
    if calculate_tweet_length(text) <= max_chars:
        return text

    urls = list(URL_REGEX.finditer(text))
    if not urls:
        # Simple text truncation at word boundary
        trimmed = text[:max_chars - 3].rsplit(" ", 1)[0]
        return f"{trimmed}..."

    # If there are URLs, preserve them and trim surrounding prose
    # If the text still exceeds limit, do a clean cut
    words = text.split()
    while words and calculate_tweet_length(" ".join(words) + "...") > max_chars:
        words.pop()

    return " ".join(words) + "..." if words else text[:max_chars]


def build_fallback_thread(spec: Dict[str, Any]) -> List[str]:
    """
    Constructs a deterministic, high-impact 4-tweet thread directly from the production spec.
    Used when offline or as an instantaneous, resilient fallback.
    """
    title = spec.get("title", "Frontier AI Architecture Deep Dive")
    spec_id = spec.get("id", "model_deepdive")
    beats = spec.get("beats", [])

    def _get_beat_text(beat_idx: int) -> str:
        if 0 <= beat_idx < len(beats):
            b = beats[beat_idx]
            return b.get("text") or b.get("narration") or b.get("script") or ""
        return ""

    b1_clean = re.sub(r"\s+", " ", _get_beat_text(0)).strip()
    b2_clean = re.sub(r"\s+", " ", _get_beat_text(1)).strip()
    b3_clean = re.sub(r"\s+", " ", _get_beat_text(2)).strip()
    b4_clean = re.sub(r"\s+", " ", _get_beat_text(3)).strip()
    b5_clean = re.sub(r"\s+", " ", _get_beat_text(4)).strip()


    # Model / Clean Title
    clean_title = title.split(":", 1)[0].strip() if ":" in title else title.replace("#Shorts", "").strip()

    # ArXiv or Canonical URL
    arxiv_id = spec.get("arxiv_id")
    canonical_url = spec.get("canonical_url")
    if arxiv_id:
        source_url = f"https://arxiv.org/abs/{arxiv_id}"
    elif canonical_url:
        source_url = canonical_url
    else:
        source_url = "https://themodelverse.in"

    modelverse_url = f"https://themodelverse.in/models/{spec_id}"

    # Tweet 1: Hook + Core Question + Video Lead (ZERO external URLs!)
    hook_lead = b1_clean if b1_clean else f"Why current approaches to {clean_title} fail at scale."
    t1_content = f"{clean_title}: {hook_lead}"
    t1_cta = "\n\nWatch the 60-second mechanism breakdown below 🧵👇"
    max_t1_body = TWITTER_MAX_CHARS - calculate_tweet_length(t1_cta)
    t1 = truncate_to_tweet_limit(t1_content, max_chars=max_t1_body) + t1_cta

    # Tweet 2: Mechanism breakdown
    t2_body = f"The Core Mechanism:\n\n{b3_clean}"
    if b4_clean and len(t2_body) + len(b4_clean) < 250:
        t2_body += f"\n\n• {b4_clean}"
    t2 = truncate_to_tweet_limit(t2_body, max_chars=TWITTER_MAX_CHARS)

    # Tweet 3: Benchmarks & Impact
    t3_body = f"The Benchmarks & Performance:\n\n{b5_clean}" if b5_clean else f"Results: State-of-the-art efficiency with zero degradation across standard LLM evaluation suites."
    t3 = truncate_to_tweet_limit(t3_body, max_chars=TWITTER_MAX_CHARS)

    # Tweet 4: Sources & Follow CTA
    t4 = (
        f"Dive deeper into {clean_title}:\n\n"
        f"📄 Paper: {source_url}\n"
        f"⚡ Interactive: {modelverse_url}\n\n"
        f"Follow @themodelverrse for daily frontier AI papers turned into code."
    )
    t4 = truncate_to_tweet_limit(t4, max_chars=TWITTER_MAX_CHARS)

    return [t1, t2, t3, t4]


def generate_x_thread(spec: Dict[str, Any], use_llm: bool = True) -> List[str]:
    """
    Generates a 4-tweet thread from a video specification.
    Attempts OmniRoute LLM cascading first; falls back to deterministic heuristic thread.
    Guarantees that every tweet strictly complies with X's 280-character limit.
    """
    title = spec.get("title", "AI Architecture Deep Dive")
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
        beat_texts = [b.get("text") or b.get("narration") or b.get("script") or "" for b in beats]
        while len(beat_texts) < 6:
            beat_texts.append("")


        user_prompt = X_USER_PROMPT_TEMPLATE.format(
            title=title,
            category=category,
            id=spec_id,
            source_url=source_url,
            modelverse_url=modelverse_url,
            beat_1=beat_texts[0],
            beat_2=beat_texts[1],
            beat_3=beat_texts[2],
            beat_4=beat_texts[3],
            beat_5=beat_texts[4],
            beat_6=beat_texts[5],
        )

        try:
            response_text = llm_router.generate_text_with_cascade(
                prompt=user_prompt,
                system_instruction=X_THREAD_SYSTEM_PROMPT
            )
            if response_text:
                parsed = robust_json_loads(response_text)

            if isinstance(parsed, dict) and "tweets" in parsed and isinstance(parsed["tweets"], list):
                raw_tweets = parsed["tweets"]
                if len(raw_tweets) >= 4:
                    # Sanitize and enforce limits
                    validated_tweets = []
                    for i, tw in enumerate(raw_tweets[:4]):
                        # For Tweet 1, ensure NO external links
                        if i == 0:
                            tw = URL_REGEX.sub("", tw).strip()
                            if "🧵" not in tw:
                                tw += " 🧵👇"
                        tw_safe = truncate_to_tweet_limit(tw, max_chars=TWITTER_MAX_CHARS)
                        validated_tweets.append(tw_safe)
                    return validated_tweets
        except Exception as e:
            print(f"ℹ️ LLM thread generation failed or fell back: {e}. Using deterministic thread generator.")

    # Fallback heuristic
    return build_fallback_thread(spec)
