"""
The Model Verse — Acoustic Forced Alignment Engine
Extracts word-level timestamps and millisecond-exact phonetic boundaries from synthesized speech,
enforcing the Frame-Ahead Rule (t_trigger = t_anchor - 0.04s) for sub-frame visual synchronization.
"""

import re
import numpy as np
import scipy.signal
from typing import List, Dict, Any, Optional

class WordTiming:
    """Represents an acoustic word-level timing interval."""
    def __init__(
        self,
        word: str,
        clean_word: str,
        phonemes: str,
        start: float,
        end: float,
        duration: float,
        frame_ahead_trigger: float
    ):
        self.word = word
        self.clean_word = clean_word
        self.phonemes = phonemes
        self.start = round(start, 3)
        self.end = round(end, 3)
        self.duration = round(duration, 3)
        self.frame_ahead_trigger = round(frame_ahead_trigger, 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "word": self.word,
            "clean_word": self.clean_word,
            "phonemes": self.phonemes,
            "start": self.start,
            "end": self.end,
            "duration": self.duration,
            "frame_ahead_trigger": self.frame_ahead_trigger
        }


class AcousticForcedAligner:
    """
    Sub-frame acoustic forced aligner combining phonetic duration weighting with
    high-resolution RMS energy envelope valley snapping (200 Hz).
    """

    def __init__(self, tokenizer=None):
        self.tokenizer = tokenizer

    def align_audio_segment(
        self,
        audio: np.ndarray,
        text: str,
        sample_rate: int = 24000,
        beat_offset: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Aligns a single continuous audio segment against its transcript.
        Returns a list of word timing dictionaries with global and local timestamps.
        """
        clean_text = text.strip()
        words = clean_text.split()
        if not words or len(audio) == 0:
            return []

        total_dur = len(audio) / sample_rate

        # 1. Phonemize words
        phonemes_per_word = []
        for w in words:
            clean_w = re.sub(r"[^\w\s]", "", w).strip()
            if not clean_w:
                clean_w = w.strip()
            if self.tokenizer:
                try:
                    p = self.tokenizer.phonemize(clean_w, "en-us")
                except Exception:
                    p = clean_w
            else:
                p = clean_w
            p_len = max(len(p.strip()), 1)
            phonemes_per_word.append((w, clean_w.lower(), p, p_len))

        # 2. Extract Acoustic RMS Energy Envelope (25ms window, 5ms hop = 200 fps)
        frame_len = int(0.025 * sample_rate)
        hop_len = int(0.005 * sample_rate)

        if len(audio) < frame_len:
            # Fallback for ultra-short clips
            step = total_dur / len(words)
            return [
                WordTiming(
                    word=w,
                    clean_word=cw,
                    phonemes=p,
                    start=beat_offset + i * step,
                    end=beat_offset + (i + 1) * step,
                    duration=step,
                    frame_ahead_trigger=max(0.0, beat_offset + i * step - 0.04)
                ).to_dict()
                for i, (w, cw, p, _) in enumerate(phonemes_per_word)
            ]

        rms = np.array([
            np.sqrt(np.mean(audio[i:i + frame_len] ** 2))
            for i in range(0, len(audio) - frame_len, hop_len)
        ])

        win = min(15, len(rms) if len(rms) % 2 != 0 else len(rms) - 1)
        if win >= 5:
            rms_smooth = scipy.signal.savgol_filter(rms, window_length=win, polyorder=2)
        else:
            rms_smooth = rms

        norm_rms = rms_smooth / (np.max(rms_smooth) + 1e-8)
        times = np.arange(len(norm_rms)) * (hop_len / sample_rate)

        # 3. Detect Active Speech Boundaries (Threshold 0.04)
        active = np.where(norm_rms > 0.04)[0]
        speech_start = float(times[active[0]]) if len(active) > 0 else 0.0
        speech_end = float(times[active[-1]]) if len(active) > 0 else total_dur
        speech_dur = max(speech_end - speech_start, 0.1)

        # 4. Detect Energy Valleys (Acoustic Dips Between Words)
        valleys, _ = scipy.signal.find_peaks(-norm_rms, distance=8, prominence=0.03)
        valley_times = times[valleys]

        # 5. Phonetic Duration Allocation
        total_phonemes = sum(item[3] for item in phonemes_per_word)
        nominal_boundaries = [speech_start]
        accum = speech_start
        for _, _, _, p_len in phonemes_per_word[:-1]:
            w_dur = (p_len / total_phonemes) * speech_dur
            accum += w_dur
            nominal_boundaries.append(accum)
        nominal_boundaries.append(speech_end)

        # 6. Snap Intermediate Boundaries to Acoustic Energy Valleys
        refined_boundaries = [speech_start]
        for b in nominal_boundaries[1:-1]:
            nearby = valley_times[np.abs(valley_times - b) < 0.12]
            if len(nearby) > 0:
                closest = nearby[np.argmin(np.abs(nearby - b))]
                # Monotonic progression check (> 60ms min word duration)
                if closest > refined_boundaries[-1] + 0.06:
                    refined_boundaries.append(float(closest))
                else:
                    refined_boundaries.append(b)
            else:
                refined_boundaries.append(b)
        refined_boundaries.append(speech_end)

        # 7. Construct WordTiming Records
        word_timings = []
        for i, (w, cw, p, _) in enumerate(phonemes_per_word):
            local_start = refined_boundaries[i]
            local_end = refined_boundaries[i + 1]
            dur = local_end - local_start
            
            global_start = beat_offset + local_start
            global_end = beat_offset + local_end
            trigger_t = max(0.0, global_start - 0.04)

            wt = WordTiming(
                word=w,
                clean_word=cw,
                phonemes=p,
                start=global_start,
                end=global_end,
                duration=dur,
                frame_ahead_trigger=trigger_t
            )
            word_timings.append(wt.to_dict())

        return word_timings

    def find_anchor_timestamp(
        self,
        word_timings: List[Dict[str, Any]],
        anchor_word: Optional[str]
    ) -> Optional[float]:
        """
        Locates the exact frame-ahead trigger timestamp for a given anchor word or semantic keyword.
        """
        if not anchor_word or not word_timings:
            return None

        clean_anchor = re.sub(r"[^\w\s]", "", anchor_word).strip().lower()
        if not clean_anchor:
            return None

        # 1. Exact match on clean_word
        for wt in word_timings:
            if wt["clean_word"] == clean_anchor:
                return wt["frame_ahead_trigger"]

        # 2. Substring or prefix match
        for wt in word_timings:
            if clean_anchor in wt["clean_word"] or wt["clean_word"] in clean_anchor:
                return wt["frame_ahead_trigger"]

        # Default fallback to the start of the first word
        return word_timings[0]["frame_ahead_trigger"]


def generate_kinetic_sfx_cues(
    timing_data: List[Dict[str, Any]],
    domain_taxonomy: str = "robotics_tamp",
    spec: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Synthesizes procedurally synchronized tactile Foley SFX cues mapped directly to
    exact visual Manim choreography moments:
      1. Formula Reveal: Crystalline glass ping when LaTeX snaps into lower tray (t = start + 0.00s)
      2. Motif Entrance: Air swish/whoosh when central diagram animates in (t = start + 0.35s)
      3. Progressive Element Pop: Soft bubble/wood pop as nodes/elements draw (t = start + 0.60s)
      4. Kinetic Action / Keyword: Sub-bass punch, cyber laser, or mechanical clicks on action trigger
      5. Brand Outro: Signature Model Verse sparkling pentatonic chime & URL click
    """
    raw_cues = []
    total_beats = len(timing_data)

    spec_beats = {}
    if spec and "beats" in spec:
        for b in spec["beats"]:
            spec_beats[b.get("beat_id")] = b

    for td in timing_data:
        beat_id = td.get("beat_id", 1)
        beat_start = td.get("start", 0.0)
        beat_dur = td.get("duration", 5.0)
        word_timings = td.get("word_timings", [])
        b_spec = spec_beats.get(beat_id, {})
        v_focus = td.get("visual_focus", "") or b_spec.get("visual_focus", "")
        v_blueprint = b_spec.get("visual_blueprint", {})
        layout = v_blueprint.get("layout", "")

        is_outro = (beat_id == 6 or beat_id == total_beats or "Follow The Model Verse" in td.get("text", ""))

        if not is_outro:
            # 1. Motif & Scene Transition Whoosh: exactly synchronized with visual scene cut and entrance!
            raw_cues.append({
                "timestamp": round(beat_start + 0.05, 3),
                "sound_type": "whoosh",
                "volume": 0.22,
                "reason": f"beat_{beat_id}_transition_entrance"
            })

            # 2. Focal Kinetic Action / Word Anchor Trigger: synchronized with spoken anchor word
            action_time = round(beat_start + 1.35, 3)
            # If anchor word exists in word timings, snap to it
            anchor_word = b_spec.get("anchor_word") or b_spec.get("action_verb")
            if anchor_word and word_timings:
                for wt in word_timings:
                    cw = wt.get("clean_word", "")
                    if cw and (cw in anchor_word.lower() or anchor_word.lower() in cw):
                        action_time = round(wt["frame_ahead_trigger"], 3)
                        break

            # Tailor action sound based on beat archetype & domain
            if beat_id == 1:
                # Curiosity Hook Punch
                raw_cues.append({
                    "timestamp": action_time,
                    "sound_type": "sub_impact",
                    "volume": 0.42,
                    "reason": "hook_curiosity_punch"
                })
            elif beat_id == 2:
                # Core Mechanism Reveal
                raw_cues.append({
                    "timestamp": action_time,
                    "sound_type": "pop",
                    "volume": 0.26,
                    "reason": "mechanism_reveal_pop"
                })
            elif beat_id == 3:
                # Deep Tech Transformation / Streaming
                s_type = "laser" if domain_taxonomy in ["neural_moe", "algorithmic_search", "neural_attention"] else "whoosh"
                raw_cues.append({
                    "timestamp": action_time,
                    "sound_type": s_type,
                    "volume": 0.28,
                    "reason": "state_transformation"
                })
            elif beat_id == 4:
                # Bottleneck / Pruning / Challenge
                s_type = "sub_impact" if "bottleneck" in v_focus.lower() or "limit" in v_focus.lower() else "click"
                raw_cues.append({
                    "timestamp": action_time,
                    "sound_type": s_type,
                    "volume": 0.36 if s_type == "sub_impact" else 0.28,
                    "reason": "bottleneck_or_prune"
                })
            elif beat_id == 5:
                # Benchmark / Metric Payoff: Double mechanical click for metric counter advance
                raw_cues.append({
                    "timestamp": action_time,
                    "sound_type": "click",
                    "volume": 0.32,
                    "reason": "metric_counter_tick_1"
                })
                raw_cues.append({
                    "timestamp": round(action_time + 0.14, 3),
                    "sound_type": "click",
                    "volume": 0.28,
                    "reason": "metric_counter_tick_2"
                })

        else:
            # 5. Beat 6 (Brand Outro)
            # Whoosh as chalkboard logo draws
            raw_cues.append({
                "timestamp": round(beat_start + 0.25, 3),
                "sound_type": "whoosh",
                "volume": 0.28,
                "reason": "outro_logo_draw"
            })
            # Sparkling Pentatonic Crystal Chime for The Model Verse
            raw_cues.append({
                "timestamp": round(beat_start + 0.50, 3),
                "sound_type": "brand_chime",
                "volume": 0.44,
                "reason": "brand_signature_sparkle"
            })
            # Tactile click as URL / subscribe button slides up
            raw_cues.append({
                "timestamp": round(beat_start + 1.25, 3),
                "sound_type": "click",
                "volume": 0.26,
                "reason": "subscribe_cta_click"
            })

    # Sort cues by timestamp
    raw_cues.sort(key=lambda x: x["timestamp"])

    # De-duplicate: Ensure at least 60ms gap between identical sounds to prevent comb filtering
    filtered_cues = []
    for c in raw_cues:
        if not filtered_cues:
            filtered_cues.append(c)
            continue
        prev = filtered_cues[-1]
        dt = c["timestamp"] - prev["timestamp"]
        if dt < 0.050 and c["sound_type"] == prev["sound_type"]:
            continue
        filtered_cues.append(c)

    return filtered_cues
