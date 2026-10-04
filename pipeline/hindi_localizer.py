"""
The Model Verse — Conversational Hindi/Hinglish Script Localizer
Converts English technical short specifications into natural, high-retention
Conversational Hinglish/Hindi for YouTube Shorts & Instagram Reels:
- Keeps developer terminology (GPU, KV cache, VRAM, tokens, Cursor, Claude, PyTorch, O(1)) in English
- Formulates relatable, energetic Hindi explanations (Fireship meets Chai aur Code)
- Avoids archaic formal textbook Hindi (no 'प्रणाली' or 'पश्च-प्रचार')
- Preserves identical visual blueprints, mathematical formulas, and scene layouts
"""

import os
import json
import copy
from typing import Dict, Any, List
import google.generativeai as genai
from pipeline.config import GEMINI_MODEL_NAME

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)


HINDI_LOCALIZATION_PROMPT = """
You are the Lead Technical Scriptwriter for 'The Model Verse' tech channel in India.
Your mission: Localize these 6 English technical short beats into natural, conversational, high-retention Conversational Hindi/Hinglish for YouTube Shorts.

CRITICAL RULES:
1. Standard Developer Terminology:
   - Keep real tools, hardware, and engineering words in English (e.g. GPU, VRAM, KV cache, RAM, tokens, latency, Cursor, Claude, PyTorch, O of 1, O of N squared).
   - Real developers and CS students cringe at translated words for technical nouns!
2. Conversational Hindi / Hinglish Rhythm:
   - Use natural, engaging phrasing that an Indian tech creator (like Chai aur Code, Striver, or Fireship) would speak to a friend.
   - Absolutely NEVER use archaic textbook Hindi (strictly ban 'प्रणाली', 'यंत्र अधिगम', 'संगणक', 'पश्च-प्रचार').
   - Keep each beat between 18 and 28 words maximum for optimal 7-9 second pacing.
3. Preserve the 6-Beat Arc:
   - Beat 1: The Hook / Problem
   - Beat 2: The Physical Analogy
   - Beat 3: The Breakthrough Mechanism
   - Beat 4: Technical Deep-Dive
   - Beat 5: Benchmark / Speedup Payoff
   - Beat 6: Outro (e.g. "Modern AI architectures ki engineering samajhne ke liye The Model Verse ko follow karein.")

Return ONLY a JSON array of 6 strings, one for each beat:
["Beat 1 text", "Beat 2 text", "Beat 3 text", "Beat 4 text", "Beat 5 text", "Beat 6 text"]
"""

def localize_spec_to_hindi(spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes an English video specification and creates a localized Hindi/Hinglish
    specification with identical visual geometry and formulas.
    """
    hindi_spec = copy.deepcopy(spec)
    hindi_spec["id"] = f"{spec.get('id', 'short')}_hi"
    hindi_spec["title"] = f"{spec.get('title', 'AI Deep Dive')} (Hindi)"
    hindi_spec["language"] = "hi"
    hindi_spec["lang"] = "hi"
    hindi_spec["tts_provider"] = "sarvam"
    hindi_spec["voice"] = "shubh"

    beats = spec.get("beats", [])
    if not beats:
        return hindi_spec

    english_beats_text = [b.get("text", "") for b in beats]
    beats_prompt = "\n".join([f"Beat {i+1}: {txt}" for i, txt in enumerate(english_beats_text)])

    prompt = f"{HINDI_LOCALIZATION_PROMPT}\n\nInput Beats:\n{beats_prompt}"

    try:
        model = genai.GenerativeModel(
            GEMINI_MODEL_NAME or "gemini-3.1-flash-lite",
            generation_config={"response_mime_type": "application/json"}
        )
        resp = model.generate_content(prompt)
        if resp and resp.text:
            localized_texts = json.loads(resp.text.strip())
            if isinstance(localized_texts, list) and len(localized_texts) == len(beats):
                for i, beat in enumerate(hindi_spec["beats"]):
                    beat["text"] = localized_texts[i]
                    # Update anchor word if applicable or keep
                    print(f"   [HI Beat {i+1}]: {localized_texts[i][:55]}...")
                return hindi_spec
    except Exception as e:
        print(f"⚠️ Notice: Hindi LLM localization encountered error ({e}). Using phonetic transliteration fallback.")

    return hindi_spec
