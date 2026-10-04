"""
The Model Verse — Test Suite for Intellectual Thriller Narrative Engine & Script Rewrite System (Engine 7.0)
Validates 4-Act Dopamine Arc, Textbook Cliché Eradication, and ScriptCritic Thriller Compliance.
"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.intellectual_thriller_engine import (
    IntellectualThrillerEngine,
    TEXTBOOK_LECTURE_CLICHES,
    intellectual_thriller_engine
)
from pipeline.feynman_dialogue_engine import CuriousNoviceListenerAgent
from pipeline.script_critic import ScriptCritic


class TestIntellectualThrillerEngine(unittest.TestCase):

    def setUp(self):
        self.engine = IntellectualThrillerEngine()
        self.listener = CuriousNoviceListenerAgent()
        self.critic = ScriptCritic()

    def test_audit_rejects_textbook_lecture_cliches(self):
        """Scripts starting with academic/textbook phrases must fail audit with low score."""
        textbook_spec = {
            "title": "Textbook Summary Paper",
            "beats": [
                {
                    "beat_id": 1,
                    "text": "Today we explore a novel paper on attention acceleration and memory bandwidth."
                },
                {
                    "beat_id": 2,
                    "text": "In this paper, the authors propose a faster method to compute matrix operations."
                },
                {
                    "beat_id": 3,
                    "text": "We present speculative decoding to verify candidate tokens in parallel."
                },
                {
                    "beat_id": 4,
                    "text": "This study investigates AST syntax trees for fast speculative candidate drafting."
                },
                {
                    "beat_id": 5,
                    "text": "The authors demonstrate 3x speedup on coding benchmarks with identical accuracy."
                },
                {
                    "beat_id": 6,
                    "text": "Follow The Model Verse for daily deep-dives into modern AI."
                }
            ]
        }

        audit = self.engine.audit_thriller_compliance(textbook_spec)
        self.assertFalse(audit["passed"])
        self.assertGreater(len(audit["detected_textbook_phrases"]), 0)
        self.assertIn("today we explore", audit["detected_textbook_phrases"])
        self.assertIn("in this paper", audit["detected_textbook_phrases"])

        # ScriptCritic must also fail it
        crit_report = self.critic.evaluate_script(textbook_spec, use_llm=False)
        self.assertFalse(crit_report.passed)
        self.assertGreater(crit_report.total_textbook_cliches, 0)

        # Curious Novice Listener must reject it
        listener_audit = self.listener.audit_script(textbook_spec)
        self.assertFalse(listener_audit["approved"])
        self.assertTrue(listener_audit["textbook_intro_detected"])

    def test_audit_approves_compliant_intellectual_thriller(self):
        """A properly formatted 4-Act Intellectual Thriller must pass audit with high score."""
        thriller_spec = {
            "title": "Speculative Decoding Acceleration",
            "category": "mechanism_deepdive",
            "domain_taxonomy": "hardware_efficiency",
            "hook_tag": "GPU BOTTLENECK",
            "thriller_metadata": {
                "engine_version": "7.0",
                "narrative_style": "intellectual_thriller",
                "villain_entity": "Sequential Token Serialization",
                "physical_analogy": "chef waiting for salt before chopping onion"
            },
            "beats": [
                {
                    "beat_id": 1,
                    "act": 1,
                    "thriller_role": "pattern_interrupt_hook",
                    "text": "Every single time Cursor or Claude writes code for you, your GPU wastes up to 70% of its compute doing nothing."
                },
                {
                    "beat_id": 2,
                    "act": 2,
                    "thriller_role": "villain_bottleneck",
                    "text": "Why? Because LLMs generate code one single token at a time—like a world-class chef who stops to ask you for salt before chopping every onion."
                },
                {
                    "beat_id": 3,
                    "act": 3,
                    "thriller_role": "eureka_mechanism",
                    "text": "Enter Speculative Decoding: a tiny draft model guesses five lines ahead, and the giant model verifies all five in one single forward pass."
                },
                {
                    "beat_id": 4,
                    "act": 3,
                    "thriller_role": "technical_secret_sauce",
                    "text": "AgSpec pushes this further by pulling matching syntax directly from your repo AST, shooting draft acceptance up by 40%."
                },
                {
                    "beat_id": 5,
                    "act": 4,
                    "thriller_role": "empirical_payoff",
                    "text": "The result? 4x faster coding agents without losing a single drop of benchmark accuracy."
                },
                {
                    "beat_id": 6,
                    "act": 4,
                    "thriller_role": "open_loop_outro",
                    "text": "Follow The Model Verse for daily deep-dives into how modern AI actually works under the hood."
                }
            ]
        }

        audit = self.engine.audit_thriller_compliance(thriller_spec)
        self.assertTrue(audit["passed"])
        self.assertGreaterEqual(audit["score"], 8.0)
        self.assertTrue(audit["hook_passed"])
        self.assertTrue(audit["act2_villain_passed"])
        self.assertTrue(audit["act4_payoff_passed"])
        self.assertEqual(len(audit["detected_textbook_phrases"]), 0)

        crit_report = self.critic.evaluate_script(thriller_spec, use_llm=False)
        self.assertTrue(crit_report.passed)
        self.assertEqual(crit_report.total_textbook_cliches, 0)
        self.assertEqual(crit_report.total_slop_cliches, 0)

    def test_rewrite_script_transforms_textbook_to_thriller(self):
        """The rewrite engine must successfully transmute dry academic drafts into thrilling scripts."""
        dry_academic_spec = {
            "title": "FlashAttention: Fast Attention with Tiling",
            "category": "mechanism_deepdive",
            "domain_taxonomy": "hardware_efficiency",
            "beats": [
                {
                    "beat_id": 1,
                    "text": "Today we explore FlashAttention, an algorithm that optimizes GPU memory."
                },
                {
                    "beat_id": 2,
                    "text": "Standard attention is slow because quadratic memory accesses cause IO bottlenecks."
                },
                {
                    "beat_id": 3,
                    "text": "The authors propose computing softmax in tiles directly in SRAM."
                },
                {
                    "beat_id": 4,
                    "text": "Online softmax scaling avoids materializing the massive N-by-N attention matrix."
                },
                {
                    "beat_id": 5,
                    "text": "The model runs significantly faster on language modeling benchmarks."
                },
                {
                    "beat_id": 6,
                    "text": "Thanks for watching this summary of FlashAttention."
                }
            ]
        }

        rewritten = self.engine.rewrite_script_to_thriller(dry_academic_spec, use_llm=False)
        self.assertIn("thriller_metadata", rewritten)
        self.assertEqual(rewritten["thriller_metadata"]["narrative_style"], "intellectual_thriller")

        # Beat 1 must now have a pattern interrupt hook (no 'Today we explore')
        b1_text = rewritten["beats"][0]["text"]
        self.assertNotIn("today we explore", b1_text.lower())
        self.assertIn(rewritten["beats"][0]["thriller_role"], "pattern_interrupt_hook")
        self.assertEqual(rewritten["beats"][0]["act"], 1)

        # Beat 2 must have a physical analogy
        b2_text = rewritten["beats"][1]["text"]
        self.assertTrue(any(w in b2_text.lower() for w in ["like a", "chef", "onion", "salt"]))
        self.assertEqual(rewritten["beats"][1]["thriller_role"], "villain_bottleneck")
        self.assertEqual(rewritten["beats"][1]["act"], 2)

        # Compliance audit must pass
        audit = self.engine.audit_thriller_compliance(rewritten)
        self.assertTrue(audit["passed"])
        self.assertGreaterEqual(audit["score"], 8.0)


if __name__ == "__main__":
    unittest.main()
