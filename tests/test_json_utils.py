"""
Unit tests for pipeline/json_utils.py robust JSON sanitizer & parser.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from pipeline.json_utils import sanitize_llm_json, robust_json_loads


class TestJSONUtils(unittest.TestCase):

    def test_direct_valid_json(self):
        data = '{"name": "test", "val": 42}'
        res = robust_json_loads(data)
        self.assertEqual(res["name"], "test")
        self.assertEqual(res["val"], 42)

    def test_markdown_codeblock_stripping(self):
        data = """```json
        {
            "id": "my_topic",
            "number": 100
        }
        ```"""
        res = robust_json_loads(data)
        self.assertEqual(res["id"], "my_topic")
        self.assertEqual(res["number"], 100)

    def test_latex_unescaped_backslashes(self):
        # Unescaped \mathrm, \frac, \tau, \alpha, \sum, \approx
        data = r"""{
            "math_formulas": [
                {"beat_id": 1, "latex": "$W_{\mathrm{FP8}} = \mathrm{quantize}(W_{\mathrm{FP16}})$"},
                {"beat_id": 2, "latex": "$\frac{1}{T} \sum_{t=1}^T \ell(y_t, \hat{y}_t)$"},
                {"beat_id": 3, "latex": "$y_{t+1} \approx \tau \cdot S_t$"}
            ]
        }"""
        res = robust_json_loads(data)
        formulas = res["math_formulas"]
        self.assertEqual(len(formulas), 3)
        self.assertIn(r"\mathrm{FP8}", formulas[0]["latex"])
        self.assertIn(r"\frac{1}{T}", formulas[1]["latex"])
        self.assertIn(r"\tau", formulas[2]["latex"])

    def test_problematic_u_escapes(self):
        # \utilization, \uparrow, \underline which cause invalid \uXXXX crashes
        data = r"""{
            "formula": "\utilization < 0.35",
            "arrow": "\uparrow",
            "line": "\underline{text}"
        }"""
        res = robust_json_loads(data)
        self.assertIn(r"\utilization", res["formula"])
        self.assertIn(r"\uparrow", res["arrow"])
        self.assertIn(r"\underline", res["line"])

    def test_valid_unicode_retained(self):
        # \u03c0 should decode to π
        data = r'{"symbol": "\u03c0"}'
        res = robust_json_loads(data)
        self.assertEqual(res["symbol"], "π")

    def test_control_chars_vs_latex(self):
        # \n should remain newline, but \nabla should remain \nabla
        data = r"""{
            "text": "Line 1\nLine 2\tTabbed",
            "equation": "\nabla \cdot E = \frac{\rho}{\epsilon_0}"
        }"""
        res = robust_json_loads(data)
        self.assertEqual(res["text"], "Line 1\nLine 2\tTabbed")
        self.assertIn(r"\nabla", res["equation"])
        self.assertIn(r"\frac", res["equation"])
        self.assertIn(r"\rho", res["equation"])

    def test_trailing_commas_and_auto_close(self):
        data = r"""{
            "list": [1, 2, 3,],
            "dict": {"a": "b",},
        """
        res = robust_json_loads(data)
        self.assertEqual(res["list"], [1, 2, 3])
        self.assertEqual(res["dict"]["a"], "b")

    def test_looped_transformers_exact_failure_case(self):
        # The exact paper case that crashed GitHub Actions
        data = r"""```json
{
  "id": "decoding_looped_transformers_free",
  "title": "Decoding Looped Transformers Better for (Almost) Free",
  "category": "benchmark_news",
  "beats": [
    {
      "beat_id": 1,
      "text": "Every single time your AI runs a loop, it throws away half its best work.",
      "svo_action": {
        "subject": "Recurrent Loop",
        "action_verb": "discards",
        "direct_object": "Intermediate States"
      }
    }
  ],
  "math_formulas": [
    {
      "beat_id": 1,
      "latex": "$\mathcal{L}_{\mathrm{loop}} = \frac{1}{T} \sum_{t=1}^T \ell(y_t, \hat{y}_t)$",
      "filename": "loop_beat1.svg"
    },
    {
      "beat_id": 2,
      "latex": "$y_{t+1} = \mathrm{LoopCD}(x_t, \tau) \approx \alpha \cdot S_t$",
      "filename": "loop_beat2.svg"
    }
  ],
  "metadata": {
    "payoff_base_label": "Unguided Baseline",
    "payoff_delta_badge": "⚡ +11.45% AIME ACCURACY GAIN",
    "challenger": "LoopCD",
    "incumbent": "Standard Decoding",
  }
}
```"""
        res = robust_json_loads(data)
        self.assertEqual(res["id"], "decoding_looped_transformers_free")
        self.assertEqual(len(res["math_formulas"]), 2)
        self.assertEqual(res["metadata"]["challenger"], "LoopCD")
        self.assertEqual(res["metadata"]["payoff_delta_badge"], "⚡ +11.45% AIME ACCURACY GAIN")


if __name__ == "__main__":
    unittest.main()
