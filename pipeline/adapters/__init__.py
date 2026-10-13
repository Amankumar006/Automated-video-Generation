"""
The Model Verse — Pluggable Render Adapters Interface
Defines standard contracts for rendering engines (Remotion, Manim, Motion Canvas).
"""

from pipeline.adapters.base_adapter import (
    RenderAdapter,
    RenderOptions,
    RenderResult,
    CompiledSceneManifest
)
from pipeline.adapters.remotion_adapter import RemotionBroadcastAdapter
from pipeline.adapters.manim_adapter import ManimLegacyAdapter

__all__ = [
    "RenderAdapter",
    "RenderOptions",
    "RenderResult",
    "CompiledSceneManifest",
    "RemotionBroadcastAdapter",
    "ManimLegacyAdapter"
]
