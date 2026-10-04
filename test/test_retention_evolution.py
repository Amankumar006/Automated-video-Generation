"""
The Model Verse — Test Suite for Retention Autopsy Critic & Genome Memory Ledger (Engine 7.0)
Validates second-by-second retention curve analysis, hook failure diagnosis,
evolutionary genome multiplier adaptation, and director biasing.
"""

import sys
import unittest
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.retention_autopsy_critic import RetentionAutopsyCritic, retention_autopsy_critic
from pipeline.retention_genome import RetentionGenomeLedger, DEFAULT_GENOME
from pipeline.visual_director import VisualDirector


class TestRetentionEvolution(unittest.TestCase):

    def setUp(self):
        self.critic = RetentionAutopsyCritic(hook_retention_threshold=70.0, drop_spike_threshold=2.5)
        # Use an isolated test genome path
        self.test_genome_path = PROJECT_ROOT / "test" / "fixtures" / "test_retention_genome.json"
        self.test_genome_path.parent.mkdir(parents=True, exist_ok=True)
        if self.test_genome_path.exists():
            self.test_genome_path.unlink()
        self.genome = RetentionGenomeLedger(ledger_path=self.test_genome_path)

        self.mock_spec = {
            "id": "speculative_decoding_test",
            "title": "Speculative Decoding Acceleration",
            "hook_tag": "absurd_paradox",
            "total_duration": 48.0,
            "beats": [
                {
                    "beat_id": 1,
                    "act": 1,
                    "text": "Every time Claude writes code, your GPU wastes up to 70% of compute.",
                    "audio_duration": 8.0,
                    "slot_duration": 8.0,
                    "start": 0.0,
                    "end": 8.0,
                    "visual_blueprint": {"layout": "BlueprintGridMemory"},
                    "svo_action": {"anchor_word": "wastes"}
                },
                {
                    "beat_id": 2,
                    "act": 2,
                    "text": "Like a chef waiting for salt before chopping every onion.",
                    "audio_duration": 8.0,
                    "slot_duration": 8.0,
                    "start": 8.0,
                    "end": 16.0,
                    "visual_blueprint": {"layout": "BlueprintSplitFlow"},
                    "svo_action": {"anchor_word": "waiting"}
                },
                {
                    "beat_id": 3,
                    "act": 3,
                    "text": "Enter Speculative Decoding verifying 5 tokens in parallel.",
                    "audio_duration": 8.0,
                    "slot_duration": 8.0,
                    "start": 16.0,
                    "end": 24.0,
                    "visual_blueprint": {"layout": "BlueprintTreeHierarchy"},
                    "svo_action": {"anchor_word": "verifying"}
                },
                {
                    "beat_id": 4,
                    "act": 3,
                    "text": "AST syntax prediction skips memory bandwidth bottlenecks.",
                    "audio_duration": 8.0,
                    "slot_duration": 8.0,
                    "start": 24.0,
                    "end": 32.0,
                    "visual_blueprint": {"layout": "BlueprintPipelineStages"},
                    "svo_action": {"anchor_word": "bandwidth"}
                },
                {
                    "beat_id": 5,
                    "act": 4,
                    "text": "The result is 4x speedup with zero loss in benchmark accuracy.",
                    "audio_duration": 8.0,
                    "slot_duration": 8.0,
                    "start": 32.0,
                    "end": 40.0,
                    "visual_blueprint": {"layout": "BlueprintHorizontalRaceBars"},
                    "svo_action": {"anchor_word": "speedup"}
                },
                {
                    "beat_id": 6,
                    "act": 4,
                    "text": "Follow The Model Verse for daily deep-dives into modern AI.",
                    "audio_duration": 8.0,
                    "slot_duration": 8.0,
                    "start": 40.0,
                    "end": 48.0,
                    "visual_blueprint": {"layout": "BlueprintChalkboardCodeBlock"},
                    "svo_action": {"anchor_word": "Model"}
                }
            ]
        }

    def tearDown(self):
        if self.test_genome_path.exists():
            self.test_genome_path.unlink()

    def test_normalize_and_interpolate_curve(self):
        """Validates normalization from tuple pairs and linear interpolation."""
        raw_tuples = [(0.0, 100.0), (3.0, 85.0), (10.0, 70.0), (48.0, 50.0)]
        norm = self.critic.normalize_curve(raw_tuples, total_duration=48.0)
        self.assertEqual(len(norm), 4)
        self.assertEqual(norm[0]["retention_pct"], 100.0)

        # Exact points
        self.assertAlmostEqual(self.critic.interpolate_retention(norm, 3.0), 85.0, places=1)
        # Interpolated point at 6.5s (midway between 3s=85 and 10s=70)
        interp = self.critic.interpolate_retention(norm, 6.5)
        self.assertAlmostEqual(interp, 77.5, places=1)

    def test_autopsy_approves_high_retention_video(self):
        """A video with gentle 3s drop (>70%) and steady completion must pass autopsy."""
        high_curve = [
            (0.0, 100.0),
            (3.0, 82.0),
            (8.0, 78.0),
            (16.0, 74.0),
            (24.0, 71.0),
            (32.0, 68.0),
            (40.0, 65.0),
            (48.0, 60.0)
        ]
        report = self.critic.run_autopsy(self.mock_spec, high_curve)
        self.assertTrue(report["hook_passed"])
        self.assertGreaterEqual(report["hook_3s_retention_pct"], 70.0)
        self.assertGreaterEqual(report["autopsy_score"], 8.0)
        self.assertIn("HIGH RETENTION EXCELLENCE", report["summary_verdict"])

        # Check beat diagnoses
        b1_diag = report["beat_diagnoses"][0]
        self.assertEqual(b1_diag["diagnosis"], "NORMAL_PACING")
        self.assertFalse(b1_diag["is_spike"])

    def test_autopsy_detects_hook_failure_swipe_away(self):
        """A steep drop in the first 3s (<70% retention) must flag HOOK_SWIPE_AWAY."""
        failing_hook_curve = [
            (0.0, 100.0),
            (3.0, 52.0),  # 48% drop in first 3 seconds!
            (8.0, 48.0),
            (16.0, 42.0),
            (48.0, 25.0)
        ]
        report = self.critic.run_autopsy(self.mock_spec, failing_hook_curve)
        self.assertFalse(report["hook_passed"])
        self.assertLess(report["hook_3s_retention_pct"], 70.0)
        self.assertLessEqual(report["autopsy_score"], 6.0)

        b1_diag = report["beat_diagnoses"][0]
        self.assertEqual(b1_diag["diagnosis"], "HOOK_SWIPE_AWAY")
        self.assertIn("Early swipe-away in first 3s", b1_diag["feedback"])

    def test_autopsy_detects_cognitive_overload_and_rewind_peaks(self):
        """Detects drop spikes in Act 3 mechanism and rewind peaks when viewers replay a beat."""
        spiky_curve = [
            (0.0, 100.0),
            (3.0, 80.0),
            (8.0, 76.0),
            (16.0, 74.0),
            (24.0, 45.0),  # Steep drop of 29% between 16s and 24s (Act 3 Beat 3)
            (32.0, 48.0),  # Rewind peak! Retention goes from 45% back up to 48%
            (48.0, 42.0)
        ]
        report = self.critic.run_autopsy(self.mock_spec, spiky_curve)

        # Beat 3 (16-24s) must be diagnosed as COGNITIVE_OVERLOAD
        b3_diag = report["beat_diagnoses"][2]
        self.assertTrue(b3_diag["is_spike"])
        self.assertEqual(b3_diag["diagnosis"], "COGNITIVE_OVERLOAD")

        # Beat 4 (24-32s) must be diagnosed as HIGH_INTEREST_PEAK (rewind peak)
        b4_diag = report["beat_diagnoses"][3]
        self.assertTrue(b4_diag["is_rewind_peak"])
        self.assertEqual(b4_diag["diagnosis"], "HIGH_INTEREST_PEAK")

    def test_genome_ledger_records_autopsy_and_evolves(self):
        """Incorporating autopsy reports updates blueprint multipliers and hook scores."""
        # Initial multiplier for BlueprintHorizontalRaceBars
        init_mult = self.genome.get_blueprint_multiplier("BlueprintHorizontalRaceBars")
        self.assertAlmostEqual(init_mult, 1.30, places=2)

        # Simulated autopsy where race bars won and grid memory suffered a spike
        autopsy_report = {
            "hook_3s_retention_pct": 84.0,
            "hook_passed": True,
            "evolutionary_signals": {
                "winning_genes": [
                    {"type": "visual_blueprint", "layout": "BlueprintHorizontalRaceBars", "retention_exit": 79.0}
                ],
                "losing_genes": [
                    {"type": "visual_blueprint", "layout": "BlueprintGridMemory", "drop_rate": 3.2}
                ]
            }
        }

        evolve_res = self.genome.record_autopsy(autopsy_report, self.mock_spec)
        self.assertEqual(evolve_res["total_autopsies"], 1)

        # Winner multiplier increased
        new_race_mult = self.genome.get_blueprint_multiplier("BlueprintHorizontalRaceBars")
        self.assertGreater(new_race_mult, init_mult)

        # Loser multiplier decreased
        new_grid_mult = self.genome.get_blueprint_multiplier("BlueprintGridMemory")
        self.assertLess(new_grid_mult, 1.20)

    def test_genome_directives_generation(self):
        """Genome must produce rich prompt injection directives including generation count."""
        directives = self.genome.get_evolutionary_directives()
        self.assertIn("generation", directives)
        self.assertIn("top_hook_archetype", directives)
        self.assertIn("prioritized_blueprints", directives)
        self.assertIn("RETENTION GENOME MEMORY DIRECTIVES", directives["directives_prompt_injection"])

    def test_visual_director_sorts_by_genome_multipliers(self):
        """VisualDirector must prioritize blueprints that have higher retention multipliers."""
        director = VisualDirector()
        beat_showdown = {
            "text": "The model achieved explosive throughput and faster execution speed on the benchmark leaderboard.",
            "visual_focus": "Horizontal bars comparing throughput",
            "svo_action": {"subject": "Hardware", "action_verb": "races", "direct_object": "Throughput"}
        }
        bp = director.synthesize_visual_blueprint(beat_showdown, topic="CUDA Attention", beat_id=5)
        from pipeline.retention_genome import retention_genome
        chosen_mult = retention_genome.get_blueprint_multiplier(bp["layout"])
        self.assertGreaterEqual(chosen_mult, 1.25)
        self.assertIn(bp["layout"], ["chalkboard_code_block", "horizontal_race_bars"])

        # When top layout is already used, chooses next highest
        bp_next = director.synthesize_visual_blueprint(beat_showdown, topic="CUDA Attention", beat_id=5, used_layouts={bp["layout"]})
        next_mult = retention_genome.get_blueprint_multiplier(bp_next["layout"])
        self.assertGreaterEqual(next_mult, 1.20)


if __name__ == "__main__":
    unittest.main()
