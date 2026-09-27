"""
Test Scene for Search & Metric Primitives.
Fast headless verification via:
manim -ql -s -r 540,960 --fps 15 test/test_search_metrics_primitives.py TestSearchMetricsPrimitivesScene
"""

from manim import *
import numpy as np
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from manim_engine.primitives.search import DynamicSearchTree, BranchAndBoundLaser
from manim_engine.primitives.metrics import DualMetricGauge

class TestSearchMetricsPrimitivesScene(Scene):
    def construct(self):
        self.camera.background_color = "#0A0D14"

        # 1. Dynamic Search Tree at the top
        tree = DynamicSearchTree(root_pos=np.array([0.0, 3.4, 0.0]), h_spacing=2.2, v_spacing=1.1)
        self.add(tree)

        # 2. Dual Metric Gauge at the bottom
        gauge = DualMetricGauge(
            label_a="Coding Agent",
            val_a=0.95,
            text_a="95%",
            label_b="Classical TAMP",
            val_b=0.47,
            text_b="47%",
            delta_text="+48% SUCCESS RATE",
            y_shift=-1.8
        )
        self.add(gauge)
