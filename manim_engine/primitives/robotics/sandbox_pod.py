"""
Sandbox Isolation Pod & Test Suite Ledger for Code Synthesis Evaluation.
Provides a containment chamber showing isolated policy execution,
assertion telemetry, and runtime tracebacks.
"""

from manim import *
import sys
from pathlib import Path

# Add project root for config imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from pipeline.config import FONT_HELVETICA, COLOR_MINT, COLOR_DANGER


from typing import Optional, List, Dict, Any


class SandboxIsolationPod(VGroup):
    """
    Parametric containment chamber for sandboxed code execution
    with test assertion telemetry.
    """
    def __init__(
        self,
        width: float = 4.2,
        height: float = 2.4,
        pod_id: str = "sbx_env_01",
        title: Optional[str] = None,
        **kwargs
    ):
        scale_val = kwargs.pop("scale", None)
        super().__init__(**kwargs)
        self.pod_width = width
        self.pod_height = height

        # Floating Terminal Header (Pure 3b1b Floating Typography)
        display_title = title if title else f">>> sandbox.assert_invariants([{pod_id}])"
        header_tag = Text(
            display_title,
            font="Courier",
            font_size=11,
            color="#38BDF8",
            weight=BOLD
        )
        self.status_led = Dot(color=COLOR_MINT, radius=0.07)
        header_grp = VGroup(self.status_led, header_tag).arrange(RIGHT, buff=0.12)

        # Subtle dashed underline rule
        self.div = DashedLine(
            LEFT * 2.2, RIGHT * 2.2,
            dash_length=0.10,
            stroke_color="#334155",
            stroke_width=1.2
        ).next_to(header_grp, DOWN, buff=0.15)

        # Assertion Ledger Container
        self.test_rows = VGroup()
        self.add(header_grp, self.div, self.test_rows)
        if scale_val is not None:
            self.scale(scale_val)

    def set_test_results(self, test_list: list[dict]):
        """
        Populates assertion checklist.
        Format: [{'name': 'test_reachability', 'status': 'PASS', 'latency': '1.2ms'}]
        """
        self.test_rows.submobjects.clear()
        rows = []
        for t in test_list:
            is_pass = t["status"].upper() == "PASS"
            icon = Text(
                "✔" if is_pass else "✘",
                font=FONT_HELVETICA,
                font_size=12,
                color=COLOR_MINT if is_pass else COLOR_DANGER,
                weight=HEAVY
            )
            name = Text(
                t["name"][:26],
                font="Courier",
                font_size=11,
                color="#E2E8F0"
            )
            lat = Text(
                t.get("latency", ""),
                font="Courier",
                font_size=10,
                color="#64748B"
            )

            row = VGroup(icon, name, lat).arrange(RIGHT, buff=0.20)
            rows.append(row)

        if rows:
            self.test_rows.add(*rows).arrange(DOWN, buff=0.16, aligned_edge=LEFT)
            self.test_rows.next_to(self.div, DOWN, buff=0.16).align_to(self.div, LEFT).shift(RIGHT * 0.12)
        return self

    def run_assertions(self, run_time: float = 2.0):
        """Populates passing test suite results and returns a FadeIn animation."""
        default_tests = [
            {"name": "test_collision_free", "status": "PASS", "latency": "0.8ms"},
            {"name": "test_goal_reachability", "status": "PASS", "latency": "1.4ms"},
            {"name": "test_torque_limits", "status": "PASS", "latency": "0.5ms"}
        ]
        self.set_test_results(default_tests)
        return FadeIn(self.test_rows, shift=UP * 0.15, run_time=run_time)

