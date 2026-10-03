"""
Test suite for 2-Agent Socratic Feynman Dialogue Engine
Verifies TechScriptwriterAgent, CuriousNoviceListenerAgent, and FeynmanSocraticLoop.
"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.feynman_dialogue_engine import (
    TechScriptwriterAgent,
    CuriousNoviceListenerAgent,
    FeynmanSocraticLoop,
    AI_SLOP_CLICHES
)
from pipeline.script_critic import ScriptCritic


class TestFeynmanDialogueEngine(unittest.TestCase):

    def setUp(self):
        self.writer = TechScriptwriterAgent()
        self.listener = CuriousNoviceListenerAgent()
        self.socratic_loop = FeynmanSocraticLoop(max_turns=3)
        self.critic = ScriptCritic()

    def test_writer_fallback_schema(self):
        """Verifies the resilient fallback produces a valid 6-beat spec."""
        paper_context = {
            "title": "AgSpec: Speculative Decoding with Code ASTs",
            "category": "mechanism_deepdive",
            "domain": "hardware_efficiency",
            "solution_title": "AgSpec AST Cache"
        }
        script = self.writer._generate_resilient_fallback(paper_context)
        self.assertEqual(len(script["beats"]), 6)
        self.assertIn("analogy_theme", script)
        self.assertIn("beats", script)

        for b in script["beats"]:
            self.assertIn("beat_id", b)
            self.assertIn("text", b)
            self.assertIn("visual_focus", b)
            self.assertIn("highlight_words", b)
            self.assertIn("svo_action", b)
            self.assertIn("visual_blueprint", b)

    def test_listener_rejects_ai_slop(self):
        """CuriousNoviceListener must catch AI slop clichés and reject."""
        slop_script = {
            "title": "AI Slop Test",
            "beats": [
                {
                    "beat_id": 1,
                    "text": "Let's delve into how a smart tool can supercharge your code."
                },
                {
                    "beat_id": 2,
                    "text": "Imagine huge safe drawers keeping your numbers locked on an open desk."
                }
            ]
        }
        audit = self.listener.audit_script(slop_script)
        self.assertFalse(audit["approved"])
        self.assertTrue(audit["ai_slop_detected"])
        self.assertIn("smart tool", audit["confusing_elements"])

    def test_listener_approves_intuitive_technical_script(self):
        """CuriousNoviceListener approves clean dev terms with clear physical analogy."""
        clean_script = {
            "title": "Speculative Decoding Acceleration",
            "category": "mechanism_deepdive",
            "hook_tag": "GPU BOTTLENECK",
            "beats": [
                {
                    "beat_id": 1,
                    "text": "Every single time Cursor or Claude writes code for you, your GPU wastes up to 70% of its compute doing nothing."
                },
                {
                    "beat_id": 2,
                    "text": "Why? Because LLMs generate code one single token at a time—like a chef waiting for salt before chopping every onion."
                },
                {
                    "beat_id": 3,
                    "text": "Enter Speculative Decoding. A tiny draft model guesses five lines ahead, while the giant model verifies all five in one pass."
                },
                {
                    "beat_id": 4,
                    "text": "AgSpec pushes this further. By pulling matching syntax from your repo AST, token acceptance shoots up by 40%."
                },
                {
                    "beat_id": 5,
                    "text": "The result is 4x faster coding agents without losing a single drop of benchmark accuracy."
                },
                {
                    "beat_id": 6,
                    "text": "Follow The Model Verse for daily deep-dives into how AI actually works under the hood."
                }
            ]
        }
        audit = self.listener.audit_script(clean_script)
        self.assertTrue(audit["approved"])
        self.assertFalse(audit["ai_slop_detected"])
        self.assertGreaterEqual(audit["comprehension_score"], 8.5)
        self.assertGreaterEqual(audit["retention_hook_score"], 8.5)

    def test_socratic_loop_convergence(self):
        """Verifies multi-turn debate loop achieves consensus and attaches certification."""
        paper_context = {
            "title": "FlashAttention-3: Fast and Accurate Attention with Asynchrony",
            "category": "hardware_efficiency",
            "domain": "hardware_efficiency",
            "solution_title": "Async Ping-Pong Buffering"
        }
        vetted_script, transcript = self.socratic_loop.run_socratic_loop(paper_context, verbose=False)
        self.assertIsNotNone(vetted_script)
        self.assertIn("feynman_certification", vetted_script)
        cert = vetted_script["feynman_certification"]
        self.assertGreaterEqual(cert["final_comprehension_score"], 8.5)
        self.assertTrue(cert["ai_slop_eliminated"])
        self.assertGreater(len(transcript), 0)

    def test_full_script_critic_pass_on_vetted_script(self):
        """The vetted script from Socratic loop must pass ScriptCritic quality gate."""
        paper_context = {
            "title": "AgSpec: Speculative Decoding with Code ASTs",
            "category": "mechanism_deepdive",
            "domain": "hardware_efficiency"
        }
        vetted_script, _ = self.socratic_loop.run_socratic_loop(paper_context, verbose=False)
        report = self.critic.evaluate_script(vetted_script, use_llm=False)
        self.assertTrue(report.passed, f"Vetted script must pass ScriptCritic: {report.summary_verdict}")
        self.assertEqual(report.total_slop_cliches, 0)
        self.assertEqual(report.total_critical_jargon, 0)


if __name__ == "__main__":
    unittest.main()
