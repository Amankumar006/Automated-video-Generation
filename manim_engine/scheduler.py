"""
The Model Verse — Kinetic Pacing & Event Scheduler
Implements the Frame-Ahead Rule (t_trigger = t_anchor - 0.04s) and millisecond-exact
visual-acoustic scheduling for Manim Community Edition scenes.
"""

from typing import Dict, Any, List, Optional

class KineticScheduler:
    """
    Coordinates narrative speech timestamps, word-level acoustic anchors,
    and Manim visual state transitions into a synchronized timeline.
    """

    def __init__(self, spec_data: Dict[str, Any]):
        self.spec = spec_data
        self.beats_map = {}
        for b in spec_data.get("beats", []):
            bid = b.get("beat_id")
            if bid is not None:
                self.beats_map[bid] = b

    def get_beat(self, beat_id: int) -> Dict[str, Any]:
        """Returns the beat dictionary for a given beat ID."""
        return self.beats_map.get(beat_id, {})

    def get_slot_duration(self, beat_id: int, default: float = 6.0) -> float:
        """Returns the total audio slot duration allocated for the beat."""
        b = self.get_beat(beat_id)
        return float(b.get("slot_duration") or b.get("duration") or default)

    def get_speech_duration(self, beat_id: int, default: float = 5.5) -> float:
        """Returns the actual spoken speech duration for the beat."""
        b = self.get_beat(beat_id)
        return float(b.get("audio_duration") or b.get("duration") or default)

    def get_word_timings(self, beat_id: int) -> List[Dict[str, Any]]:
        """Returns word-level acoustic timings for the beat."""
        b = self.get_beat(beat_id)
        return b.get("word_timings", [])

    def get_action_trigger_offset(
        self,
        beat_id: int,
        anchor_word: Optional[str] = None
    ) -> float:
        """
        Calculates the relative offset (seconds from beat start) when the visual action
        should trigger according to the Frame-Ahead Rule (0.04s before anchor word).
        """
        word_timings = self.get_word_timings(beat_id)
        if not word_timings:
            # Default reasonable pacing offsets if word-level data is unavailable
            return 0.15

        beat_start = float(self.get_beat(beat_id).get("start", 0.0))

        if anchor_word:
            import re
            clean_anchor = re.sub(r"[^\w\s]", "", anchor_word).strip().lower()
            for wt in word_timings:
                if wt.get("clean_word") == clean_anchor:
                    global_trigger = float(wt.get("frame_ahead_trigger", wt["start"] - 0.04))
                    return max(0.05, round(global_trigger - beat_start, 3))
            for wt in word_timings:
                cw = wt.get("clean_word", "")
                if clean_anchor in cw or cw in clean_anchor:
                    global_trigger = float(wt.get("frame_ahead_trigger", wt["start"] - 0.04))
                    return max(0.05, round(global_trigger - beat_start, 3))

        # If no specific anchor is found, trigger on the first meaningful word
        idx = min(1, len(word_timings) - 1) if len(word_timings) > 2 else 0
        first_trigger = float(word_timings[idx].get("frame_ahead_trigger", word_timings[idx]["start"] - 0.04))
        return max(0.05, round(first_trigger - beat_start, 3))

    def compute_kinetic_budget(
        self,
        beat_id: int,
        anchor_word: Optional[str] = None,
        desired_action_duration: float = 1.6
    ) -> Dict[str, float]:
        """
        Calculates the exact duration for:
        - `pre_wait`: Silence/holding duration before triggering the action
        - `action_run_time`: Duration of the visual transformation
        - `post_wait`: Observation and comprehension buffer before next beat
        """
        slot_dur = self.get_slot_duration(beat_id)
        trigger_offset = self.get_action_trigger_offset(beat_id, anchor_word)
        
        pre_wait = max(0.05, trigger_offset)
        remaining = max(0.4, slot_dur - pre_wait)
        
        if desired_action_duration + 0.4 <= remaining:
            action_dur = desired_action_duration
            post_wait = remaining - action_dur
        else:
            action_dur = max(0.6, remaining * 0.70)
            post_wait = max(0.2, remaining - action_dur)

        return {
            "slot_duration": round(slot_dur, 3),
            "pre_wait": round(pre_wait, 3),
            "action_run_time": round(action_dur, 3),
            "post_wait": round(post_wait, 3)
        }
