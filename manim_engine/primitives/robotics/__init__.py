"""
Robotics & Task and Motion Planning (TAMP) Visual Primitives for Manim CE.
Provides mathematical dual-manifold coordinates, kinematic link chains,
constraint projection sheaves, and AST execution pods.
"""

from .coupled_state_space import CoupledCanvas, CoupledNode, ConstraintProjectionSheaf, GeometricRefinementPulse
from .kinematic_arm import ParametricKinematicArm
from .ast_tree import ASTMorphTree
from .sandbox_pod import SandboxIsolationPod

__all__ = [
    "CoupledCanvas",
    "CoupledNode",
    "ConstraintProjectionSheaf",
    "GeometricRefinementPulse",
    "ParametricKinematicArm",
    "ASTMorphTree",
    "SandboxIsolationPod",
]
