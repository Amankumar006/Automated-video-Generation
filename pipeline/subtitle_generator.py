"""
The Model Verse — Kinetic Subtitle & Phrase Chunk Engine
Generates rhythmically synchronized phrase chunks (3-5 words) from acoustic word timings,
providing on-screen kinetic highlighting and exporting standard .srt and styled .ass subtitles.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

COMMON_STOPWORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "by", "from",
    "and", "or", "but", "so", "if", "that", "this", "it", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "as", "can", "could", "will", "would", "shall", "should", "may", "might"
}

HIGHLIGHT_COLORS = ["#FDE047", "#38BDF8", "#34D399", "#A78BFA"]


def pick_highlight_word(words_in_chunk: List[Dict[str, Any]], anchor_hint: Optional[str] = None) -> str:
    """Selects the most impactful, punchy word in a phrase chunk for glowing kinetic highlight."""
    if anchor_hint:
        clean_hint = re.sub(r"[^\w\s]", "", anchor_hint).strip().lower()
        for w in words_in_chunk:
            cw = w.get("clean_word", "").lower()
            if cw and (cw in clean_hint or clean_hint in cw):
                return w.get("word", "")

    # Look for capitalized acronyms / technical terms
    for w in words_in_chunk:
        raw = w.get("word", "").strip(".,!?;:")
        if len(raw) >= 2 and (raw.isupper() or any(char.isdigit() for char in raw)):
            return raw

    # Filter out stopwords and find the most significant word
    candidates = []
    for w in words_in_chunk:
        clean = w.get("clean_word", "").lower().strip()
        if clean and clean not in COMMON_STOPWORDS and len(clean) >= 3:
            candidates.append(w.get("word", "").strip(".,!?;:"))

    if candidates:
        # Pick the longest candidate word
        candidates.sort(key=len, reverse=True)
        return candidates[0]

    # Fallback to middle word
    mid_idx = len(words_in_chunk) // 2
    return words_in_chunk[mid_idx].get("word", "").strip(".,!?;:")


def generate_phrase_chunks(
    beats: List[Dict[str, Any]],
    min_words: int = 3,
    max_words: int = 5,
    max_chunk_dur: float = 1.6
) -> List[Dict[str, Any]]:
    """
    Transforms acoustic word timings across narrative beats into balanced,
    high-retention kinetic phrase chunks (3-5 words each).
    """
    chunks = []
    chunk_global_id = 1

    for b in beats:
        beat_id = b.get("beat_id", 1)
        # Skip outro brand beat if desired, or include it cleanly
        is_outro = (beat_id >= 6 or "Follow The Model Verse" in b.get("text", ""))
        words = b.get("word_timings", [])
        if not words:
            continue

        anchor_hint = b.get("anchor_word") or b.get("action_verb")
        curr_words = []

        for i, w in enumerate(words):
            curr_words.append(w)
            dur = curr_words[-1]["end"] - curr_words[0]["start"]
            is_last = (i == len(words) - 1)
            has_period = bool(re.search(r"[.!?]$", w["word"]))

            if is_last:
                if len(curr_words) > 0:
                    chunks.append(_format_chunk(curr_words, beat_id, chunk_global_id, anchor_hint, is_outro))
                    chunk_global_id += 1
                curr_words = []
            elif len(curr_words) >= min_words and (has_period or len(curr_words) >= max_words or dur >= max_chunk_dur):
                chunks.append(_format_chunk(curr_words, beat_id, chunk_global_id, anchor_hint, is_outro))
                chunk_global_id += 1
                curr_words = []

        # Merge tiny trailing orphan chunks (< 2 words) into the preceding chunk
        if len(chunks) >= 2 and chunks[-1]["beat_id"] == chunks[-2]["beat_id"]:
            prev = chunks[-2]
            last = chunks[-1]
            last_word_count = len(last["text"].split())
            if last_word_count <= 2:
                merged_text = f"{prev['text']} {last['text']}"
                prev["text"] = merged_text
                prev["end"] = last["end"]
                prev["duration"] = round(prev["end"] - prev["start"], 3)
                chunks.pop()

    return chunks


def _format_chunk(
    words_in_chunk: List[Dict[str, Any]],
    beat_id: int,
    chunk_id: int,
    anchor_hint: Optional[str] = None,
    is_outro: bool = False
) -> Dict[str, Any]:
    start_t = round(words_in_chunk[0]["start"], 3)
    end_t = round(words_in_chunk[-1]["end"], 3)
    text = " ".join([item["word"] for item in words_in_chunk])
    highlight = pick_highlight_word(words_in_chunk, anchor_hint=anchor_hint)
    color = "#FDE047" if chunk_id % 2 == 1 else "#38BDF8"
    if is_outro:
        color = "#34D399"

    return {
        "chunk_id": chunk_id,
        "beat_id": beat_id,
        "start": start_t,
        "end": end_t,
        "duration": round(end_t - start_t, 3),
        "text": text,
        "highlight_word": highlight,
        "highlight_color": color,
        "is_outro": is_outro
    }


def _sec_to_srt_time(seconds: float) -> str:
    """Converts seconds float to SRT timestamp format (HH:MM:SS,mmm)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    msec = int(round((seconds - int(seconds)) * 1000))
    if msec >= 1000:
        msec = 999
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{msec:03d}"


def _sec_to_ass_time(seconds: float) -> str:
    """Converts seconds float to ASS timestamp format (H:MM:SS.cc)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    csec = int(round((seconds - int(seconds)) * 100))
    if csec >= 100:
        csec = 99
    return f"{hrs:d}:{mins:02d}:{secs:02d}.{csec:02d}"


def export_srt(chunks: List[Dict[str, Any]], output_path: str) -> str:
    """Exports kinetic phrase chunks to a standard .srt subtitle file."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    lines = []
    for idx, c in enumerate(chunks, start=1):
        s_time = _sec_to_srt_time(c["start"])
        e_time = _sec_to_srt_time(c["end"])
        lines.append(f"{idx}\n{s_time} --> {e_time}\n{c['text']}\n")

    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"📄 Exported standard SRT subtitles: {output_path} ({len(chunks)} chunks)")
    return output_path


def export_ass(chunks: List[Dict[str, Any]], output_path: str, title: str = "The Model Verse") -> str:
    """
    Exports kinetic phrase chunks to a styled Advanced SubStation Alpha (.ass) file,
    optimized specifically for 9:16 mobile vertical Shorts (1440x2560 canvas).
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    header = f"""[Script Info]
Title: {title} Kinetic Captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1440
PlayResY: 2560

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: KineticPill, Montserrat, 58, &H00FFFFFF, &H0047E0FD, &H00140C08, &HCC080C14, 1, 0, 0, 0, 100, 100, 0, 0, 3, 14, 0, 2, 80, 80, 560, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for c in chunks:
        s_time = _sec_to_ass_time(c["start"])
        e_time = _sec_to_ass_time(c["end"])
        raw_text = c["text"]
        highlight = c.get("highlight_word", "")

        if highlight and highlight in raw_text:
            # Highlight word with glowing yellow/cyan BGR code
            # Yellow: &H47E0FD& (BGR for #FDE047)
            bgr_highlight = "&H47E0FD&" if c.get("highlight_color") == "#FDE047" else "&HF8BD38&"
            formatted_text = raw_text.replace(highlight, f"{{\\c{bgr_highlight}}}{highlight}{{\\c&HFFFFFF&}}")
        else:
            formatted_text = raw_text

        events.append(f"Dialogue: 0,{s_time},{e_time},KineticPill,,0,0,0,,{formatted_text}")

    full_ass = header + "\n".join(events) + "\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_ass)
    print(f"📄 Exported styled ASS kinetic subtitles: {output_path} ({len(chunks)} events)")
    return output_path
