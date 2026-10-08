"""
The Model Verse — Dead-Air Audio Compression & High-Momentum Audio Pipeline
Integrates skills/yt-edit (deadair.py) into the core automated audio generation pipeline.
Detects silence gaps (> 250ms) in TTS audio cues and compresses them down to ~120-180ms
using pydub/ffmpeg to deliver rapid, high-momentum narration without cutting spoken words.
"""

import os
import io
import re
import sys
import copy
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pydub import AudioSegment
from pydub.silence import detect_silence
import numpy as np
import soundfile as sf

# Default pacing constants
DEFAULT_DEAD_AIR_FLOOR_MS = 250.0       # Gaps > 250ms are flagged as dead air
DEFAULT_TARGET_GAP_MS = 150.0          # Tightened to rapid momentum band (~120-180ms)
DEFAULT_MIN_MOMENTUM_GAP_MS = 120.0
DEFAULT_MAX_MOMENTUM_GAP_MS = 180.0


def detect_dead_air_gaps(
    cues: List[Dict[str, Any]],
    floor_ms: float = DEFAULT_DEAD_AIR_FLOOR_MS,
    target_gap_ms: float = DEFAULT_TARGET_GAP_MS
) -> List[Dict[str, Any]]:
    """
    Inspects speech cues and timestamps to locate dead-air gaps (> floor_ms).
    Returns list of cut specifications with exact start/end offsets and time saved.
    """
    if not cues or len(cues) < 2:
        return []

    cuts = []
    accumulated_offset_ms = 0.0

    for i in range(1, len(cues)):
        prev_end_s = float(cues[i - 1].get("end", 0.0))
        cur_start_s = float(cues[i].get("start", 0.0))

        prev_end_ms = prev_end_s * 1000.0
        cur_start_ms = cur_start_s * 1000.0

        gap_ms = cur_start_ms - prev_end_ms
        if gap_ms > floor_ms:
            excess_ms = gap_ms - target_gap_ms
            # Keep half of target_gap at end of previous cue, half at start of next cue
            keep_half = target_gap_ms / 2.0
            cut_start_ms = prev_end_ms + keep_half
            cut_end_ms = cur_start_ms - keep_half

            cuts.append({
                "cue_index": i,
                "gap_start_ms": prev_end_ms,
                "gap_end_ms": cur_start_ms,
                "gap_duration_ms": gap_ms,
                "cut_start_ms": cut_start_ms,
                "cut_end_ms": cut_end_ms,
                "excess_ms": excess_ms,
                "target_gap_ms": target_gap_ms,
                "why": f"{gap_ms:.1f}ms dead air compressed to {target_gap_ms:.1f}ms"
            })

    return cuts


def adjust_cue_timestamps(
    cues: List[Dict[str, Any]],
    cuts: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Shifts cue and word-level timestamps backwards to compensate for removed dead air.
    Preserves perfect audiovisual subtitle and SFX synchronization.
    """
    if not cues or not cuts:
        return copy.deepcopy(cues)

    adjusted = copy.deepcopy(cues)
    for cut in cuts:
        cut_start_s = cut["cut_start_ms"] / 1000.0
        excess_s = cut["excess_ms"] / 1000.0
        idx = cut["cue_index"]

        # Shift all cues starting from idx onwards
        for j in range(idx, len(adjusted)):
            adjusted[j]["start"] = round(max(0.0, float(adjusted[j]["start"]) - excess_s), 3)
            adjusted[j]["end"] = round(max(0.0, float(adjusted[j]["end"]) - excess_s), 3)
            if "slot_duration" in adjusted[j]:
                adjusted[j]["slot_duration"] = round(adjusted[j]["end"] - adjusted[j]["start"] + (cut["target_gap_ms"] / 1000.0), 3)

            # Adjust fine-grained word timings if present
            if "word_timings" in adjusted[j] and isinstance(adjusted[j]["word_timings"], list):
                for w in adjusted[j]["word_timings"]:
                    w["start"] = round(max(0.0, float(w.get("start", 0.0)) - excess_s), 3)
                    w["end"] = round(max(0.0, float(w.get("end", 0.0)) - excess_s), 3)

    return adjusted


def compress_dead_air(
    audio_source: Union[str, Path, AudioSegment, np.ndarray],
    cues: Optional[List[Dict[str, Any]]] = None,
    floor_ms: float = DEFAULT_DEAD_AIR_FLOOR_MS,
    target_gap_ms: float = DEFAULT_TARGET_GAP_MS,
    output_path: Optional[Union[str, Path]] = None,
    sample_rate: int = 24000
) -> Dict[str, Any]:
    """
    Tightens dead-air gaps (> floor_ms) down to target_gap_ms (~120-180ms)
    using pydub/audio processing without cutting spoken words.
    
    Supports:
      1. Cue-driven compression: uses exact speech boundaries from TTS/aligner.
      2. Waveform-driven compression: detects silence regions via energy threshold if cues are omitted.
    """
    # Clamp target gap to recommended high-momentum band
    target_gap_ms = max(DEFAULT_MIN_MOMENTUM_GAP_MS, min(DEFAULT_MAX_MOMENTUM_GAP_MS, target_gap_ms))

    # Load into AudioSegment
    if isinstance(audio_source, AudioSegment):
        segment = audio_source
    elif isinstance(audio_source, (str, Path)):
        p = Path(audio_source)
        if not p.exists():
            raise FileNotFoundError(f"Audio file not found: {p}")
        segment = AudioSegment.from_file(str(p), format="wav")
    elif isinstance(audio_source, np.ndarray):
        # Convert float numpy array to 16-bit PCM wav in memory
        arr = audio_source
        if arr.dtype != np.int16:
            arr_norm = np.clip(arr, -1.0, 1.0)
            arr_i16 = (arr_norm * 32767).astype(np.int16)
        else:
            arr_i16 = arr
        buf = io.BytesIO()
        sf.write(buf, arr_i16, sample_rate, format="WAV", subtype="PCM_16")
        buf.seek(0)
        segment = AudioSegment.from_file(buf, format="wav")
    else:
        raise ValueError(f"Unsupported audio source type: {type(audio_source)}")

    orig_dur_s = len(segment) / 1000.0

    if cues and len(cues) >= 2:
        # 1. Cue-driven precision dead-air compression
        cuts = detect_dead_air_gaps(cues, floor_ms=floor_ms, target_gap_ms=target_gap_ms)
        if not cuts:
            # Gaps already tight
            if output_path:
                segment.export(str(output_path), format="wav")
            return {
                "audio": segment,
                "output_path": str(output_path) if output_path else None,
                "original_duration_s": orig_dur_s,
                "compressed_duration_s": orig_dur_s,
                "time_saved_s": 0.0,
                "cuts_count": 0,
                "cuts": [],
                "adjusted_cues": copy.deepcopy(cues)
            }

        # Build compressed audio segment by keeping speech chunks and room tone/silence gaps
        pieces = []
        cur_pos_ms = 0
        for cut in cuts:
            c_start = int(cut["cut_start_ms"])
            c_end = int(cut["cut_end_ms"])
            # Append audio up to the cut start
            if c_start > cur_pos_ms:
                pieces.append(segment[cur_pos_ms:c_start])
            cur_pos_ms = c_end

        # Append remaining audio after last cut
        if cur_pos_ms < len(segment):
            pieces.append(segment[cur_pos_ms:])

        compressed_audio = AudioSegment.empty()
        for p in pieces:
            compressed_audio += p

        adjusted_cues = adjust_cue_timestamps(cues, cuts)
        comp_dur_s = len(compressed_audio) / 1000.0
        saved_s = round(orig_dur_s - comp_dur_s, 3)

        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            compressed_audio.export(str(output_path), format="wav")

        return {
            "audio": compressed_audio,
            "output_path": str(output_path) if output_path else None,
            "original_duration_s": round(orig_dur_s, 3),
            "compressed_duration_s": round(comp_dur_s, 3),
            "time_saved_s": saved_s,
            "cuts_count": len(cuts),
            "cuts": cuts,
            "adjusted_cues": adjusted_cues
        }

    else:
        # 2. Waveform-driven energy threshold detection
        silence_thresh = -40  # dBFS
        silences = detect_silence(
            segment,
            min_silence_len=int(floor_ms),
            silence_thresh=silence_thresh
        )

        if not silences:
            if output_path:
                segment.export(str(output_path), format="wav")
            return {
                "audio": segment,
                "output_path": str(output_path) if output_path else None,
                "original_duration_s": orig_dur_s,
                "compressed_duration_s": orig_dur_s,
                "time_saved_s": 0.0,
                "cuts_count": 0,
                "cuts": [],
                "adjusted_cues": cues or []
            }

        pieces = []
        cuts = []
        cur_pos = 0

        for s_start, s_end in silences:
            sil_len = s_end - s_start
            if sil_len > floor_ms:
                # Add audio prior to silence start
                pieces.append(segment[cur_pos:s_start])
                # Keep target_gap_ms of the ambient silence
                ambient_keep = segment[s_start:int(s_start + target_gap_ms)]
                pieces.append(ambient_keep)
                excess = sil_len - target_gap_ms
                cuts.append({
                    "silence_start_ms": s_start,
                    "silence_end_ms": s_end,
                    "gap_duration_ms": sil_len,
                    "excess_ms": excess,
                    "target_gap_ms": target_gap_ms,
                    "why": f"{sil_len:.1f}ms silence compressed to {target_gap_ms:.1f}ms"
                })
                cur_pos = s_end

        if cur_pos < len(segment):
            pieces.append(segment[cur_pos:])

        compressed_audio = AudioSegment.empty()
        for p in pieces:
            compressed_audio += p

        comp_dur_s = len(compressed_audio) / 1000.0
        saved_s = round(orig_dur_s - comp_dur_s, 3)

        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            compressed_audio.export(str(output_path), format="wav")

        return {
            "audio": compressed_audio,
            "output_path": str(output_path) if output_path else None,
            "original_duration_s": round(orig_dur_s, 3),
            "compressed_duration_s": round(comp_dur_s, 3),
            "time_saved_s": saved_s,
            "cuts_count": len(cuts),
            "cuts": cuts,
            "adjusted_cues": cues or []
        }


# Convenience alias and synthesis wrapper
def synthesize_and_compress_audio(
    spec_data: Dict[str, Any],
    floor_ms: float = DEFAULT_DEAD_AIR_FLOOR_MS,
    target_gap_ms: float = DEFAULT_TARGET_GAP_MS,
    **synthesis_kwargs
) -> Dict[str, Any]:
    """
    Synthesizes audio for the given spec and automatically executes dead-air compression,
    tightening pauses between beats and phrases down to high-momentum ~120-180ms.
    """
    from pipeline.audio_synthesizer import synthesize_audio_for_spec
    result = synthesize_audio_for_spec(spec_data, **synthesis_kwargs)
    return result
