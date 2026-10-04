"""
The Model Verse — Retention Autopsy Critic (Engine 7.0)
Analyzes second-by-second YouTube Shorts retention curves, cross-references
drop-off timestamps against narration beats, SVO actions, and visual compositions,
and generates granular diagnoses of audience engagement and drop-off causes.
"""

import os
import sys
import json
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))


class RetentionAutopsyCritic:
    """
    Critic that correlates second-by-second viewer retention curves with
    multimodal production specs (script text, SVO actions, visual blueprints).
    """

    def __init__(self, hook_retention_threshold: float = 70.0, drop_spike_threshold: float = 2.5):
        """
        :param hook_retention_threshold: Target retention (%) at t=3.0s. If below, flags Hook Failure.
        :param drop_spike_threshold: Normalized drop rate (% per second) considered a severe spike.
        """
        self.hook_retention_threshold = hook_retention_threshold
        self.drop_spike_threshold = drop_spike_threshold

    def normalize_curve(
        self,
        raw_curve: Union[List[Tuple[float, float]], List[Dict[str, Any]], Dict[str, float]],
        total_duration: float
    ) -> List[Dict[str, float]]:
        """
        Normalizes various retention curve input formats into a standardized
        list of points: [{'time_s': float, 'retention_pct': float}].
        """
        points = []
        if isinstance(raw_curve, list):
            for pt in raw_curve:
                if isinstance(pt, (tuple, list)) and len(pt) >= 2:
                    t, r = float(pt[0]), float(pt[1])
                    points.append({"time_s": t, "retention_pct": r})
                elif isinstance(pt, dict):
                    t = float(pt.get("time_s", pt.get("time", pt.get("second", 0.0))))
                    r = float(pt.get("retention_pct", pt.get("retention", pt.get("value", 100.0))))
                    points.append({"time_s": t, "retention_pct": r})
        elif isinstance(raw_curve, dict):
            for k, v in raw_curve.items():
                try:
                    points.append({"time_s": float(k), "retention_pct": float(v)})
                except ValueError:
                    continue

        if not points:
            # Fallback to linear decay if empty
            points = [
                {"time_s": 0.0, "retention_pct": 100.0},
                {"time_s": 3.0, "retention_pct": 75.0},
                {"time_s": total_duration, "retention_pct": 50.0}
            ]

        points.sort(key=lambda x: x["time_s"])
        return points

    def interpolate_retention(self, curve: List[Dict[str, float]], t: float) -> float:
        """Interpolates retention percentage at arbitrary timestamp t."""
        if not curve:
            return 100.0
        if t <= curve[0]["time_s"]:
            return curve[0]["retention_pct"]
        if t >= curve[-1]["time_s"]:
            return curve[-1]["retention_pct"]

        for i in range(len(curve) - 1):
            p1 = curve[i]
            p2 = curve[i + 1]
            if p1["time_s"] <= t <= p2["time_s"]:
                dt = p2["time_s"] - p1["time_s"]
                if dt <= 0:
                    return p1["retention_pct"]
                fraction = (t - p1["time_s"]) / dt
                return p1["retention_pct"] + fraction * (p2["retention_pct"] - p1["retention_pct"])

        return curve[-1]["retention_pct"]

    def run_autopsy(
        self,
        spec: Dict[str, Any],
        retention_curve: Union[List[Tuple[float, float]], List[Dict[str, Any]], Dict[str, float]],
        video_meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes a comprehensive retention autopsy:
        - Maps curve timestamps to beats.
        - Evaluates Act 1 Hook friction (0-3s).
        - Computes per-beat drop-off and velocity.
        - Flags drop spikes, cognitive overload, and rewind peaks.
        - Outputs actionable evolutionary genes.
        """
        beats = spec.get("beats", [])
        total_duration = float(spec.get("total_duration") or sum(b.get("slot_duration", b.get("audio_duration", 8.0)) for b in beats) or 45.0)

        curve = self.normalize_curve(retention_curve, total_duration)

        # 1. Evaluate Act 1 Pattern Interrupt Hook (0-3s)
        hook_3s_retention = round(self.interpolate_retention(curve, 3.0), 2)
        hook_drop_3s = round(100.0 - hook_3s_retention, 2)
        hook_passed = hook_3s_retention >= self.hook_retention_threshold

        # 2. Per-Beat Autopsy
        beat_diagnoses = []
        overall_drops = []
        current_time = 0.0

        for idx, b in enumerate(beats):
            bid = b.get("beat_id", idx + 1)
            duration = float(b.get("slot_duration") or b.get("audio_duration") or (total_duration / max(len(beats), 1)))
            start_t = float(b.get("start", current_time))
            end_t = float(b.get("end", start_t + duration))
            current_time = end_t

            entry_ret = round(self.interpolate_retention(curve, start_t), 2)
            exit_ret = round(self.interpolate_retention(curve, end_t), 2)
            net_drop = round(entry_ret - exit_ret, 2)
            drop_rate_per_sec = round(net_drop / max(duration, 0.1), 2)
            overall_drops.append(net_drop)

            layout = b.get("visual_blueprint", {}).get("layout") or b.get("motif_params", {}).get("layout") or "bespoke_code"
            svo = b.get("svo_action", {})
            thriller_role = b.get("thriller_role", f"beat_{bid}")
            act = b.get("act", 1 if bid == 1 else (2 if bid == 2 else (3 if bid in (3, 4) else 4)))

            # Detect anomalies (Beat 1 entry drop is evaluated via hook_passed)
            effective_spike_thresh = self.drop_spike_threshold * 1.5 if bid == 1 else self.drop_spike_threshold
            is_spike = drop_rate_per_sec >= effective_spike_thresh
            is_rewind_peak = net_drop <= -0.5  # Viewers rewatched this section!

            diagnosis_label = "NORMAL_PACING"
            actionable_feedback = "Pacing and visual density aligned with audience attention."

            if bid == 1 and not hook_passed:
                diagnosis_label = "HOOK_SWIPE_AWAY"
                actionable_feedback = f"Early swipe-away in first 3s ({hook_drop_3s}% drop). Opening lacked absurdity, high stakes, or pattern interrupt."
            elif is_rewind_peak:
                diagnosis_label = "HIGH_INTEREST_PEAK"
                actionable_feedback = "Viewers replayed or paused on this beat. Strong cognitive resonance or visual showdown."
            elif is_spike and act == 2:
                diagnosis_label = "ANALOGY_DISCONNECT"
                actionable_feedback = "Steep drop in Act 2 villain. The physical analogy may be convoluted or slow to resolve."
            elif is_spike and act == 3:
                diagnosis_label = "COGNITIVE_OVERLOAD"
                actionable_feedback = f"Drop spike in mechanism beat ({drop_rate_per_sec}%/s). Layout '{layout}' or math formula was too dense."
            elif is_spike and act == 4:
                diagnosis_label = "PREMATURE_OUTRO_DROP"
                actionable_feedback = "Audience disengaged before benchmark payoff. Pacing dragged or call-to-action started too early."

            beat_diagnoses.append({
                "beat_id": bid,
                "act": act,
                "thriller_role": thriller_role,
                "start_time_s": round(start_t, 2),
                "end_time_s": round(end_t, 2),
                "duration_s": round(duration, 2),
                "entry_retention_pct": entry_ret,
                "exit_retention_pct": exit_ret,
                "net_drop_pct": net_drop,
                "drop_rate_pct_per_sec": drop_rate_per_sec,
                "visual_layout": layout,
                "svo_anchor": svo.get("anchor_word", ""),
                "is_spike": is_spike,
                "is_rewind_peak": is_rewind_peak,
                "diagnosis": diagnosis_label,
                "feedback": actionable_feedback
            })

        # 3. Aggregate Metrics & Evolutionary Signals
        avg_retention = round(sum(p["retention_pct"] for p in curve) / max(len(curve), 1), 2)
        end_retention = round(curve[-1]["retention_pct"], 2)
        steepest_beat = max(beat_diagnoses, key=lambda x: x["drop_rate_pct_per_sec"])
        best_beat = min(beat_diagnoses, key=lambda x: x["drop_rate_pct_per_sec"])

        # Determine Winning vs Losing Genes
        winning_genes = []
        losing_genes = []

        if hook_passed:
            winning_genes.append({
                "type": "hook_archetype",
                "trait": spec.get("thriller_metadata", {}).get("hook_tag", "pattern_interrupt"),
                "retention_3s": hook_3s_retention
            })
        else:
            losing_genes.append({
                "type": "hook_archetype",
                "trait": spec.get("thriller_metadata", {}).get("hook_tag", "pattern_interrupt"),
                "drop_3s": hook_drop_3s
            })

        for bd in beat_diagnoses:
            if bd["is_rewind_peak"] or bd["drop_rate_pct_per_sec"] < 1.0:
                winning_genes.append({
                    "type": "visual_blueprint",
                    "layout": bd["visual_layout"],
                    "beat_id": bd["beat_id"],
                    "retention_exit": bd["exit_retention_pct"]
                })
            elif bd["is_spike"]:
                losing_genes.append({
                    "type": "visual_blueprint",
                    "layout": bd["visual_layout"],
                    "beat_id": bd["beat_id"],
                    "drop_rate": bd["drop_rate_pct_per_sec"]
                })

        # Calculate Overall Autopsy Score (1.0 to 10.0)
        score = 8.0
        if not hook_passed:
            score -= 2.5
        if end_retention >= 50.0:
            score += 1.5
        elif end_retention < 30.0:
            score -= 2.0
        score -= min(3.0, sum(1.0 for bd in beat_diagnoses if bd["is_spike"]))
        score = max(1.0, min(10.0, round(score, 1)))

        return {
            "video_id": video_meta.get("video_id") if video_meta else spec.get("id", "test_video"),
            "title": spec.get("title", "Untitled Breakdown"),
            "total_duration_s": round(total_duration, 2),
            "autopsy_score": score,
            "hook_3s_retention_pct": hook_3s_retention,
            "hook_passed": hook_passed,
            "average_retention_pct": avg_retention,
            "completion_retention_pct": end_retention,
            "steepest_drop_beat": steepest_beat["beat_id"],
            "steepest_drop_layout": steepest_beat["visual_layout"],
            "best_retention_beat": best_beat["beat_id"],
            "best_retention_layout": best_beat["visual_layout"],
            "beat_diagnoses": beat_diagnoses,
            "evolutionary_signals": {
                "winning_genes": winning_genes,
                "losing_genes": losing_genes
            },
            "summary_verdict": (
                f"HIGH RETENTION EXCELLENCE (Score {score}/10): Maintained {hook_3s_retention}% at hook and {end_retention}% at outro."
                if score >= 7.5 else
                f"RETENTION AUTOPSY FLAGGED ISSUES (Score {score}/10): Drop-off spike at Beat {steepest_beat['beat_id']} ({steepest_beat['visual_layout']})."
            )
        }

    def simulate_retention_curve(
        self,
        duration: float = 45.0,
        hook_quality: float = 8.5,
        avg_view_pct: float = 65.0
    ) -> List[Dict[str, float]]:
        """
        Generates a realistic second-by-second retention curve for offline testing,
        calibrated to empirical YouTube Shorts distributions (steep 0-3s dip, followed by
        stabilized exponential decay with micro-fluctuations).
        """
        points = []
        # Initial 3-second hook drop depends on hook_quality (higher score = gentler drop)
        hook_3s_val = max(55.0, min(88.0, 50.0 + (hook_quality * 4.2)))

        num_seconds = max(10, int(math.ceil(duration)))
        for s in range(num_seconds + 1):
            t = float(s)
            if t == 0.0:
                ret = 100.0
            elif t <= 3.0:
                # Steep pattern-interrupt drop
                ret = 100.0 - ((100.0 - hook_3s_val) * (t / 3.0) ** 0.8)
            else:
                # Exponential decay toward end retention
                progress = (t - 3.0) / max(duration - 3.0, 1.0)
                target_end = max(25.0, avg_view_pct * 0.75)
                decay = hook_3s_val - ((hook_3s_val - target_end) * (progress ** 0.9))
                # Add micro-fluctuation wave
                wave = math.sin(t * 0.7) * 1.2
                ret = max(15.0, min(100.0, decay + wave))

            points.append({"time_s": t, "retention_pct": round(ret, 2)})

        return points


# Singleton instance
retention_autopsy_critic = RetentionAutopsyCritic()
