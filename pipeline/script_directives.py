"""
The Model Verse — Unified Script Directives, Prompts & Quality Validator
Standardized prompts and validation logic across all three content tracks:
- Track 1: Academic Breakdown / Deep Breakdown (paper architecture)
- Track 2: Tech News (official AI lab drops)
- Track 3: Developer Perks (startup credits and developer deals)
"""

import re
from typing import Dict, Any, List, Tuple, Optional

# =============================================================================
# SHARED SCRIPT DIRECTIVE (Prepend to all 3 tracks)
# =============================================================================

SHARED_SCRIPT_PROMPT_DIRECTIVE = """You write voiceover scripts for 'The Model Verse' (themodelverse.in), a YouTube Shorts channel about AI for developers.

FORMAT
- Exactly 6 beats, 115-140 words total (about 50 seconds). Stay inside each beat's word range. Count before answering.
- Spoken words only. No stage directions, emojis, hashtags, markdown or parentheses.
- Write for text-to-speech: spell out numbers and symbols ("four times", "one thousand dollars", "percent"). Common terms like GPU, API, KV cache are fine.
- Max 12 words per sentence. One idea per sentence. Short punches, with at most one longer sentence per beat.
- Each beat = [setup clause] + [trigger clause]. "anchor_word" is one word copied exactly from the trigger clause; an on-screen animation fires on it. Never reuse an anchor_word.

ACCURACY
- Use ONLY facts found in SOURCE. Never invent numbers, benchmarks, prices, dates, names or quotes.
- If a beat's required fact is missing from SOURCE, rewrite that beat around what IS there. Do not fill the gap.
- Analogies and jokes may be invented. Claims may not.

RETENTION
- Beat 1 must be a pattern interrupt: a paradox, a shocking number, or a direct challenge. No greeting, no context-setting.
- Banned phrases: "today we explore", "in this video", "in this paper", "let's dive in", "game-changer", "revolutionary", "buckle up", "researchers have proposed".
- At most one dry joke per script. It must point at a real fact, not filler.
- Every beat must give the viewer a new fact or a new tension. No recap.

OUTPUT: valid JSON only, no text outside it:
{
  "title": "<max 60 chars, no clickbait lies>",
  "beats": [
    {"n": 1, "text": "<spoken text>", "anchor_word": "<word>", "visual_cue": "<5-10 words describing the on-screen visual>"}
  ],
  "word_count": <int>
}"""

# Alias for convenience
SHARED_SCRIPT_PROMPT = SHARED_SCRIPT_PROMPT_DIRECTIVE


# =============================================================================
# TRACK-SPECIFIC PROMPT TEMPLATES
# =============================================================================

TRACK_1_DEEP_BREAKDOWN_PROMPT_TEMPLATE = """ROLE: Technical scriptwriter. Explain one frontier AI architecture paper as an intellectual thriller: a villain (the bottleneck), a clever trick, and a payoff.

SOURCE: {paper_title}
{abstract_or_paper_text}

Read the SOURCE fresh. Do not reuse structure or phrasing from earlier scripts.

BEATS (word range, time):
1. HOOK (8-10 words, 0-3s): An absurd paradox or shocking inefficiency from the paper's domain.
2. VILLAIN (24-28 words, 3-13s): Personify the bottleneck with one physical analogy (e.g. a chef with ten orders and one tiny counter).
3. EUREKA (26-30 words, 13-24s): The core idea in plain language. What changes, in one sentence a non-expert could repeat.
4. SECRET SAUCE (24-28 words, 24-35s): The real mechanism in developer terms (KV cache, SRAM bandwidth, attention, latency), and why it works.
5. PAYOFF (20-24 words, 35-44s): Real numbers from the paper only: speedup, memory saved, accuracy held. If there are no numbers, state the qualitative result.
6. SHIFT + LOOP (14-18 words, 44-52s): What this changes for how models get built. The last line must flow naturally back into Beat 1 so the Short loops."""


TRACK_2_TECH_NEWS_PROMPT_TEMPLATE = """ROLE: Breaking tech news reporter. Fast, authoritative, no hype (MKBHD meets Bloomberg Tech).

Provider: {provider}
Headline: {headline}
SOURCE:
{details}

Focus on what a developer cares about: price, speed, benchmarks, availability. Use only numbers present in SOURCE.

BEATS (word range, time):
1. BREAKING HOOK (8-10 words, 0-3s): The announcement and its single biggest claim.
2. THE OLD CEILING (20-24 words, 3-12s): What the previous model got wrong: cost, latency, limits. Use the predecessor only if SOURCE names it.
3. WHAT'S NEW (24-28 words, 12-24s): How the new model or feature achieves it (distillation, routing, architecture), only as far as SOURCE explains it.
4. BENCHMARKS (24-28 words, 24-35s): Named benchmarks with scores vs baselines (SWE-bench Verified, AIME, GPQA). If SOURCE has no benchmarks, cover the capability changes instead.
5. PRICE + ACCESS (22-26 words, 35-44s): Input/output token pricing, % change vs predecessor, where it ships (API, web, tiers). Skip any item not in SOURCE.
6. TAKEAWAY + CTA (14-18 words, 44-52s): One urgent sentence on what developers should do now, then exactly: "Follow The Model Verse for instant breakdowns of every major AI lab drop.\""""


TRACK_3_DEVELOPER_PERKS_PROMPT_TEMPLATE = """ROLE: Host of a developer-deals channel. High energy, direct, zero fluff (Alex Bowers meets Starter Story). Speak to indie hackers and early-stage founders as "you".

Provider: {provider}
Program: {headline}
Total value: {val_str}
SOURCE:
{details}

No academic language. Dollar amounts and concrete steps only.

BEATS (word range, time):
1. VALUE HOOK (8-10 words, 0-3s): The exact total dollar value, stated as free.
2. THE DEAL (22-26 words, 3-12s): Exactly what you get: credit amounts, seats, duration, tools.
3. WHO QUALIFIES (24-28 words, 12-24s): Eligibility in three parts, only as listed in SOURCE (stage, domain, funding, GitHub).
4. HOW TO APPLY (24-28 words, 24-35s): Exact steps in order: URL or console name, what to link, which fields to fill.
5. PROOF + TIMING (20-24 words, 35-44s): Approval time or community reports ONLY if in SOURCE. Otherwise cover the catch: limits, expiry, restrictions.
6. SAVE CTA (14-18 words, 44-52s): "Save this video" plus "follow The Model Verse for daily developer perks". Mention a deadline or cap only if SOURCE states one."""


# =============================================================================
# SCRIPT VALIDATOR
# =============================================================================

BANNED_PHRASES = [
    "today we explore",
    "in this video",
    "in this paper",
    "let's dive in",
    "game-changer",
    "revolutionary",
    "buckle up",
    "researchers have proposed"
]

TARGET_WORD_COUNT_MIN = 115
TARGET_WORD_COUNT_MAX = 140


def count_words(text: str) -> int:
    """Counts spoken words in text, ignoring punctuation."""
    if not text:
        return 0
    return len(text.strip().split())


def get_total_word_count(spec: Dict[str, Any]) -> int:
    """Computes total spoken word count across all beats in a script specification."""
    beats = spec.get("beats", [])
    return sum(count_words(b.get("text", "")) for b in beats)


def validate_script_spec(spec: Dict[str, Any], raise_on_error: bool = False) -> Tuple[bool, List[str]]:
    """
    Validates a script specification against The Model Verse quality guidelines:
    1. Exactly 6 beats.
    2. Total word count within 115-140 words (~2.7 words/sec for 50s TTS).
    3. Each beat must contain non-empty spoken text, an anchor_word, and visual_cue.
    4. The anchor_word must be present in the beat's spoken text.
    5. Anchor words must be unique across all 6 beats (never reused).
    6. No banned phrases present in any beat text.

    Returns:
        (is_valid: bool, errors: List[str])
    """
    errors: List[str] = []
    beats = spec.get("beats", [])

    # 1. Beat count check
    if len(beats) != 6:
        errors.append(f"Script must contain exactly 6 beats; found {len(beats)}.")

    # 2. Total word count check
    total_words = get_total_word_count(spec)
    if total_words < TARGET_WORD_COUNT_MIN or total_words > TARGET_WORD_COUNT_MAX:
        errors.append(
            f"Total word count {total_words} is outside required range "
            f"[{TARGET_WORD_COUNT_MIN}, {TARGET_WORD_COUNT_MAX}]."
        )

    # 3. Individual beat checks
    seen_anchors = set()
    for idx, beat in enumerate(beats):
        b_num = beat.get("n") or beat.get("beat_id", idx + 1)
        text = (beat.get("text") or "").strip()
        anchor_word = (beat.get("anchor_word") or "").strip()
        visual_cue = (beat.get("visual_cue") or beat.get("visual_focus") or "").strip()

        if not text:
            errors.append(f"Beat {b_num}: spoken text is empty.")
            continue

        if not anchor_word:
            errors.append(f"Beat {b_num}: missing required 'anchor_word'.")
        else:
            # Check presence of anchor_word in text (case-insensitive token or substring match)
            clean_anchor = re.sub(r"[^\w]", "", anchor_word).lower()
            text_tokens = [re.sub(r"[^\w]", "", w).lower() for w in text.split()]
            if clean_anchor not in text_tokens and clean_anchor not in text.lower():
                errors.append(
                    f"Beat {b_num}: anchor_word '{anchor_word}' not found in spoken text: \"{text}\""
                )

            # Check uniqueness of anchor_word
            if clean_anchor in seen_anchors:
                errors.append(f"Beat {b_num}: anchor_word '{anchor_word}' is reused across beats.")
            seen_anchors.add(clean_anchor)

        if not visual_cue:
            errors.append(f"Beat {b_num}: missing required 'visual_cue'.")

        # 4. Check banned phrases
        text_lower = text.lower()
        for phrase in BANNED_PHRASES:
            if phrase in text_lower:
                errors.append(f"Beat {b_num}: contains banned phrase '{phrase}'.")

    is_valid = len(errors) == 0
    if raise_on_error and not is_valid:
        raise ValueError("Script validation failed:\n" + "\n".join(f" - {e}" for e in errors))

    return is_valid, errors
