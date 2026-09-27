"""
Test suite for Script Pedagogy & Comprehensibility Critic
"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.script_critic import (
    ScriptCritic,
    count_syllables,
    compute_flesch_metrics,
    HIGH_DENSITY_JARGON
)


class TestScriptCritic(unittest.TestCase):

    def setUp(self):
        self.critic = ScriptCritic(target_grade_level=8.0, min_score=8.0)

    def test_syllable_counter(self):
        self.assertEqual(count_syllables("cat"), 1)
        self.assertEqual(count_syllables("mirror"), 2)
        self.assertEqual(count_syllables("sculptor"), 2)
        self.assertEqual(count_syllables("chaos"), 2)
        self.assertEqual(count_syllables("transformation"), 4)

    def test_jargon_heavy_script_rejected(self):
        jargony_spec = {
            "title": "Jargon Overload",
            "beats": [
                {
                    "beat_id": 1,
                    "text": "Tokens are shattered into coordinate vectors across twelve thousand dimensions in the embedding matrix."
                },
                {
                    "beat_id": 2,
                    "text": "Every token must calculate a dot product creating a quadratic matrix explosion."
                },
                {
                    "beat_id": 3,
                    "text": "FlashAttention tiles computation directly inside SRAM, streaming KV-cache states."
                },
                {
                    "beat_id": 4,
                    "text": "SwiGLU gating networks route activations across deep conceptual knowledge manifolds."
                }
            ]
        }
        report = self.critic.evaluate_script(jargony_spec, use_llm=False)
        self.assertFalse(report.passed, "Jargon-heavy script should be rejected")
        self.assertGreater(report.total_critical_jargon, 3, "Should detect multiple critical jargon terms")
        self.assertGreater(report.grade_level, 9.0, "Academic script should have high grade level")
        self.assertLess(report.overall_score, 6.0, "Academic script score should be penalized below 6.0")

    def test_example_driven_script_approved(self):
        simple_spec = {
            "title": "How AI Creates Images From TV Static",
            "beats": [
                {
                    "beat_id": 1,
                    "text": "When an AI paints a picture, it doesn't search a library. It starts with something bizarre: a screen filled with pure, random TV static."
                },
                {
                    "beat_id": 2,
                    "text": "Ever stare at clouds until you spot a rabbit? That is how AI works. It stares at pure chaos until it imagines a faint outline."
                },
                {
                    "beat_id": 3,
                    "text": "Scientists taught it this by taking clear photos and slowly adding noise—like steam fogging up a mirror until the reflection vanishes."
                },
                {
                    "beat_id": 4,
                    "text": "Then they asked the AI to do the reverse. Like a sculptor chipping away marble, it wipes off one thin layer of noise at a time."
                },
                {
                    "beat_id": 5,
                    "text": "It repeats this cleaning step fifty times in two seconds. What was meaningless fuzz suddenly sharpens into art carved out of chaos."
                },
                {
                    "beat_id": 6,
                    "text": "Follow The Model Verse for simple explanations of how modern AI actually works."
                }
            ]
        }
        report = self.critic.evaluate_script(simple_spec, use_llm=False)
        self.assertTrue(report.passed, "Simple example-driven script should be approved")
        self.assertEqual(report.total_critical_jargon, 0, "Should have zero critical jargon terms")
        self.assertGreaterEqual(report.total_analogies, 5, "Should have rich everyday analogies")
        self.assertLessEqual(report.grade_level, 8.0, "Should be at or below middle school grade level")
        self.assertGreaterEqual(report.overall_score, 8.5, "Should score >= 8.5")


if __name__ == "__main__":
    unittest.main()
