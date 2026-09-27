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
    domain_taxonomy: str = "robotics_tamp"
) -> List[Dict[str, Any]]:
    """
    Synthesizes procedurally synchronized SFX cues directly mapped to
    acoustic word boundaries and kinetic action triggers.
    """
    cues = []
    
    # Sound type mapping based on domain and semantic roles
    for td in timing_data:
        beat_id = td.get("beat_id", 1)
        beat_start = td.get("start", 0.0)
        word_timings = td.get("word_timings", [])
        
        # Beat 1: Hook Impact
        if beat_id == 1:
            impact_t = beat_start + 0.40
            if word_timings and len(word_timings) > 1:
                impact_t = word_timings[min(1, len(word_timings) - 1)]["frame_ahead_trigger"]
            cues.append({
                "timestamp": round(impact_t, 2),
                "sound_type": "sub_impact",
                "volume": 0.50,
                "reason": "hook_impact"
            })
            
        # Beat 2: Core Mechanism Reveal / Whoosh
        elif beat_id == 2:
            whoosh_t = beat_start + 0.05
            cues.append({
                "timestamp": round(whoosh_t, 2),
                "sound_type": "whoosh",
                "volume": 0.35,
                "reason": "mechanism_reveal"
            })
            
        # Beat 3: Transformation / Laser or Projection
        elif beat_id == 3:
            laser_t = beat_start + 0.10
            # If domain is MoE or Search, use laser
            s_type = "laser" if domain_taxonomy in ["neural_moe", "algorithmic_search"] else "whoosh"
            cues.append({
                "timestamp": round(laser_t, 2),
                "sound_type": s_type,
                "volume": 0.38,
                "reason": "state_transition"
            })
            
        # Beat 4: Collision / Pruning / Bottleneck Strike
        elif beat_id == 4:
            cues.append({
                "timestamp": round(beat_start + 0.08, 2),
                "sound_type": "sub_impact" if domain_taxonomy == "robotics_tamp" else "laser",
                "volume": 0.42,
                "reason": "pruning_or_collision_strike"
            })
            
        # Beat 5: Benchmark / Synthesis Resolution
        elif beat_id == 5:
            cues.append({
                "timestamp": round(beat_start + 0.12, 2),
                "sound_type": "click",
                "volume": 0.40,
                "reason": "metric_counter_advance"
            })
            
        # Beat 6: Brand Outro & Chime
        elif beat_id == 6:
            cues.append({
                "timestamp": round(beat_start + 0.05, 2),
                "sound_type": "whoosh",
                "volume": 0.35,
                "reason": "outro_transition"
            })
            cues.append({
                "timestamp": round(beat_start + 1.15, 2),
                "sound_type": "chime",
                "volume": 0.45,
                "reason": "brand_signature_sparkle"
            })
            
    return cues
