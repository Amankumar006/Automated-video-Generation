"""
Test Scene for Neural & Interpretability Primitives.
Fast headless verification via:
manim -ql -s -r 540,960 --fps 15 test/test_neural_primitives.py TestNeuralPrimitivesScene
"""

from manim import *
import numpy as np
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from manim_engine.primitives.neural import (
    SAEConstellation,
    FeatureProjectionChip,
    TransformerAttentionGrid,
    RoutingRibbon,
    SparseMoELattice,
    LoadBalancingManometer,
    ContrastiveHypersphere,
    ScoreBasedDiffusionField,
)

class TestNeuralPrimitivesScene(Scene):
    def construct(self):
        self.camera.background_color = "#0A0D14"

        # 1. Sparse Autoencoder Constellation (Top)
        sae = SAEConstellation(num_dictionary_features=8, plane_size=4.2)
        sae.shift(UP * 2.2)
        self.add(sae)

        # 2. Feature Projection Chips (Bottom)
        chip1 = FeatureProjectionChip(feature_id=182, label="Python Indentation", intensity=1.60, color="#10B981")
        chip1.move_to([-1.6, -1.8, 0])

        chip2 = FeatureProjectionChip(feature_id=491, label="Indirect Object", intensity=1.30, color="#00F0FF")
        chip2.move_to([1.6, -1.8, 0])

        self.add(chip1, chip2)

        # 3. Load Balancing Manometer (Bottom Edge)
        manometer = LoadBalancingManometer(num_experts=8, width=6.2, height=0.85)
        manometer.shift(DOWN * 3.4)
        self.add(manometer)


class TestAttentionAndMoEScene(Scene):
    def construct(self):
        self.camera.background_color = "#0A0D14"

        # 1. Transformer Attention Heatmap Grid (Top)
        grid = TransformerAttentionGrid(
            tokens=["Deep", "Seek", "Sparse", "MoE"],
            grid_size=3.4
        )
        grid.shift(UP * 2.2)
        self.add(grid)

        # 2. Sparse MoE Lattice (Bottom)
        moe = SparseMoELattice(
            num_experts=8,
            grid_cols=4,
            router_pos=np.array([0.0, -0.6, 0.0]),
            expert_center=np.array([0.0, -2.2, 0.0])
        )
        self.add(moe)
