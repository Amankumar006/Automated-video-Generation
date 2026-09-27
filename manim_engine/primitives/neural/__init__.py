"""
Deep Learning & Mechanistic Interpretability Visual Primitives for Manim CE.
Provides Sparse Autoencoders (SAE) superposition planes, Transformer Attention heatmaps,
Mixture-of-Experts (MoE) laser lattices, and Diffusion score fields.
"""

from .sae_constellation import SAEConstellation, FeatureProjectionChip
from .attention_grid import TransformerAttentionGrid, RoutingRibbon
from .moe_lattice import SparseMoELattice, LoadBalancingManometer
from .contrastive_diffusion import ContrastiveHypersphere, ScoreBasedDiffusionField

__all__ = [
    "SAEConstellation",
    "FeatureProjectionChip",
    "TransformerAttentionGrid",
    "RoutingRibbon",
    "SparseMoELattice",
    "LoadBalancingManometer",
    "ContrastiveHypersphere",
    "ScoreBasedDiffusionField",
]
