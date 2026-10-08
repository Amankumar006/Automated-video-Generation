"""Project Aether Compiler Package (Pillar 3 & Pillar 4 / WBS 1.4).

Provides Complexity Planner and Shot Compiler modules translating high-level
scene state graphs into deterministic spatial representation requirements and
provider-specific generative video payloads (Veo 3.1, Kling 3.0, Runway Gen-4.5,
and open-weights CogVideoX / HunyuanVideo via ComfyUI).
"""

from __future__ import annotations

from aether.compiler.complexity import ComplexityPlanner
from aether.compiler.compiler import ShotCompiler
from aether.compiler.schemas import (
    AudioRequirement,
    ComplexityLevel,
    ComplexityPlan,
    CompiledModelPayload,
    ComputeTier,
    ProviderTarget,
    ShotRequirement,
    ShotSlice,
    SpatialRepresentationPackage,
)

__all__ = [
    # Schemas
    "ComplexityLevel",
    "ProviderTarget",
    "ComputeTier",
    "AudioRequirement",
    "ShotRequirement",
    "ShotSlice",
    "SpatialRepresentationPackage",
    "ComplexityPlan",
    "CompiledModelPayload",
    # Planner & Compiler
    "ComplexityPlanner",
    "ShotCompiler",
]
