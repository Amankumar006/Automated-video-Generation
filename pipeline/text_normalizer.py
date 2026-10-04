"""
The Model Verse — Speech Text Normalizer & Phonetic Optimization Engine
Implements ElevenLabs & Sarvam TTS best practices:
- Currency, percentage, unit, and multiplier expansion
- Domain-specific AI/Hardware acronym phonetic spacing (GPU -> G P U, LLMs -> L L M's)
- Mathematical expression conversion ($O(N^2)$ -> O of N squared)
- Audio delivery tag filtering based on model capability
- Natural pause cadence normalization
"""

import re
from typing import Optional

# Common unit expansions
UNIT_REPLACEMENTS = [
    (r"\b(\d+(?:\.\d+)?)\s*GB\b", r"\1 gigabytes"),
    (r"\b(\d+(?:\.\d+)?)\s*TB\b", r"\1 terabytes"),
    (r"\b(\d+(?:\.\d+)?)\s*MB\b", r"\1 megabytes"),
    (r"\b(\d+(?:\.\d+)?)\s*ms\b", r"\1 milliseconds"),
    (r"\b(\d+(?:\.\d+)?)\s*ns\b", r"\1 nanoseconds"),
    (r"\b(\d+(?:\.\d+)?)\s*µs\b", r"\1 microseconds"),
    (r"\b(\d+(?:\.\d+)?)\s*us\b", r"\1 microseconds"),
    (r"\b(\d+(?:\.\d+)?)\s*TFLOPS\b", r"\1 teraflops"),
    (r"\b(\d+(?:\.\d+)?)\s*FLOPs\b", r"\1 flops"),
    (r"\b(\d+(?:\.\d+)?)\s*FLOPS\b", r"\1 flops"),
    (r"\b(\d+(?:\.\d+)?)\s*DPI\b", r"\1 D P I"),
    (r"\b(\d+(?:\.\d+)?)\s*fps\b", r"\1 frames per second"),
    (r"\b(\d+(?:\.\d+)?)\s*FPS\b", r"\1 frames per second"),
]

# AI / Hardware acronym phonetic expansions for natural vocalization
ACRONYM_REPLACEMENTS = [
    (r"\bLLMs\b", "L L M's"),
    (r"\bLLM\b", "L L M"),
    (r"\bGPUs\b", "G P U's"),
    (r"\bGPU\b", "G P U"),
    (r"\bCPUs\b", "C P U's"),
    (r"\bCPU\b", "C P U"),
    (r"\bTPUs\b", "T P U's"),
    (r"\bTPU\b", "T P U"),
    (r"\bASTs\b", "A S T's"),
    (r"\bAST\b", "A S T"),
    (r"\bKV\s*cache\b", "K V cache"),
    (r"\bKV\b", "K V"),
    (r"\bMoE\b", "M o E"),
    (r"\bSRAM\b", "S-RAM"),
    (r"\bHBM\b", "H B M"),
    (r"\bHBM3e\b", "H B M three e"),
    (r"\bHBM3\b", "H B M three"),
    (r"\bFP16\b", "F P sixteen"),
    (r"\bFP8\b", "F P eight"),
    (r"\bFP32\b", "F P thirty-two"),
    (r"\bBF16\b", "B F sixteen"),
    (r"\bINT8\b", "int eight"),
    (r"\bINT4\b", "int four"),
    (r"\bAPIs\b", "A P I's"),
    (r"\bAPI\b", "A P I"),
    (r"\bPRs\b", "P R's"),
    (r"\bPR\b", "P R"),
    (r"\bVLMs\b", "V L M's"),
    (r"\bVLM\b", "V L M"),
    (r"\bLoRA\b", "low-ra"),
    (r"\bQoQ\b", "quarter over quarter"),
    (r"\bYoY\b", "year over year"),
]

# Math conversions
MATH_REPLACEMENTS = [
    (r"\$O\(N\^2\)\$", "O of N squared"),
    (r"\$O\(N\)\$", "O of N"),
    (r"\$O\(1\)\$", "O of one"),
    (r"\$O\(N\s*\\log\s*N\)\$", "O of N log N"),
    (r"O\(N\^2\)", "O of N squared"),
    (r"O\(N\)", "O of N"),
    (r"O\(1\)", "O of one"),
    (r"\\alpha", "alpha"),
    (r"\\beta", "beta"),
    (r"\\gamma", "gamma"),
    (r"\\theta", "theta"),
    (r"\\sigma", "sigma"),
    (r"\\times", "times"),
]

def normalize_currency(text: str) -> str:
    """Expands currency notations like $42.50 or $100M into spoken English."""
    # $10M / $10B
    text = re.sub(r"\$(\d+(?:\.\d+)?)\s*([mM])\b", r"\1 million dollars", text)
    text = re.sub(r"\$(\d+(?:\.\d+)?)\s*([bB])\b", r"\1 billion dollars", text)
    text = re.sub(r"\$(\d+(?:\.\d+)?)\s*([kK])\b", r"\1 thousand dollars", text)
    
    # $42.50 -> 42 dollars and 50 cents
    def _cur_replace(m):
        dollars = m.group(1)
        cents = m.group(2)
        if cents and int(cents) > 0:
            return f"{dollars} dollars and {cents} cents"
        return f"{dollars} dollars"

    text = re.sub(r"\$(\d+)\.(\d{2})\b", _cur_replace, text)
    # $100 -> 100 dollars
    text = re.sub(r"\$(\d+)\b", r"\1 dollars", text)
    return text

def normalize_numbers_and_multipliers(text: str) -> str:
    """Normalizes percentages (70% -> 70 percent) and multipliers (3.5x -> 3.5 times)."""
    # Percentages
    text = re.sub(r"(\d+(?:\.\d+)?)%", r"\1 percent", text)
    # Multiplier ranges: 2x-4x -> 2 to 4 times
    text = re.sub(r"(\d+(?:\.\d+)?)x\s*-\s*(\d+(?:\.\d+)?)x\b", r"\1 to \2 times", text)
    # Multiplier: 3.5x / 10x
    text = re.sub(r"(\d+(?:\.\d+)?)x\b", r"\1 times", text)
    return text

def normalize_narration_text(
    text: str,
    model_id: str = "eleven_multilingual_v2",
    language: str = "en"
) -> str:
    """
    Applies comprehensive text normalization and phonetic optimization
    for ElevenLabs and Sarvam speech engines.
    """
    if not text:
        return ""

    normalized = text.strip()

    # If Hindi language, preserve Devanagari text but format numbers
    if language.lower() in ("hi", "hindi", "hi-in"):
        # Format percentages in Hindi context
        normalized = re.sub(r"(\d+(?:\.\d+)?)%", r"\1 प्रतिशत", normalized)
        # Format multipliers
        normalized = re.sub(r"(\d+(?:\.\d+)?)x\b", r"\1 गुना", normalized)
        # Clean extra spaces
        return re.sub(r"\s+", " ", normalized).strip()

    # 1. Currency Normalization
    normalized = normalize_currency(normalized)

    # 2. Number & Multiplier Normalization
    normalized = normalize_numbers_and_multipliers(normalized)

    # 3. Unit Normalization
    for pattern, replacement in UNIT_REPLACEMENTS:
        normalized = re.sub(pattern, replacement, normalized)

    # 4. Computer Science / AI Acronym Normalization
    for pattern, replacement in ACRONYM_REPLACEMENTS:
        normalized = re.sub(pattern, replacement, normalized)

    # 5. Math LaTeX Normalization
    for pattern, replacement in MATH_REPLACEMENTS:
        normalized = re.sub(pattern, replacement, normalized)

    # Clean leftover dollar signs from math mode
    normalized = re.sub(r"\$([^\$]+)\$", r"\1", normalized)
    normalized = normalized.replace("$", "")

    # 6. Audio Delivery Tag Handling
    # eleven_v4 supports [whispers], [excited], [short pause], [clears throat], etc.
    # Older models (eleven_multilingual_v2, eleven_flash_v2) will speak bracketed tags aloud!
    is_v4 = "eleven_v4" in model_id.lower()
    if not is_v4:
        # Strip square bracket tags e.g. [whispers], [sighs], [excited]
        normalized = re.sub(r"\[(whispers|sighs|excited|happy|sad|short pause|pause|clears throat|laughs|giggles|shouts)\]", "", normalized, flags=re.IGNORECASE)

    # 7. Normalize pauses & cadence
    # Replace double dashes or em-dashes with spaced em-dash for natural pause
    normalized = re.sub(r"\s*--\s*", " — ", normalized)
    normalized = re.sub(r"\s*—\s*", " — ", normalized)
    
    # Clean up redundant spaces
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized
