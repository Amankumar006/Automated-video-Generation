"""
The Model Verse — Hybrid Engine Router
Dynamically routes video scenes between Remotion (React 19 / TypeScript) and Manim (Python / Cairo)
based on scene narrative taxonomy and hardware capabilities.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Union

from pipeline.adapters.base_adapter import RenderAdapter
from pipeline.adapters.remotion_adapter import RemotionBroadcastAdapter
from pipeline.adapters.manim_adapter import ManimLegacyAdapter
from pipeline.vsg.schema import VideoSceneGraphIR

logger = logging.getLogger("engine_router")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [EngineRouter] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class HybridEngineRouter:
    """
    Directs scene rendering jobs to the optimal backend engine:
    - Remotion: Systems architecture, tech news, benchmark showdowns, HUD cards, MoE matrices
    - Manim: Continuous calculus, Riemannian manifolds, pure mathematical derivations
    """

    def __init__(self):
        self._remotion_adapter = RemotionBroadcastAdapter()
        self._manim_adapter = ManimLegacyAdapter()

    def select_engine(
        self,
        vsg: Union[VideoSceneGraphIR, Dict[str, Any]],
        engine_override: Optional[str] = "hybrid"
    ) -> RenderAdapter:
        """
        Selects rendering adapter based on engine preference and VSG-IR metadata.
        Options for engine_override: 'remotion', 'manim', 'hybrid'
        """
        override = (engine_override or "hybrid").lower()

        if override == "remotion":
            logger.info("🎯 Engine Override: Remotion Broadcast Engine designated.")
            return self._remotion_adapter

        if override == "manim":
            logger.info("🎯 Engine Override: Manim Legacy Adapter designated.")
            return self._manim_adapter

        # Hybrid routing heuristic
        if isinstance(vsg, VideoSceneGraphIR):
            taxonomy = vsg.metadata.domain_taxonomy.lower()
            beats = vsg.beats
        else:
            taxonomy = vsg.get("metadata", {}).get("domain_taxonomy", "").lower()
            beats = vsg.get("beats", [])

        # Pure mathematical taxonomy exceptions routed to Manim
        math_taxonomies = ["calculus", "differential_geometry", "pure_math", "topological_manifold"]
        if any(m in taxonomy for m in math_taxonomies):
            logger.info(f"📐 Routing to Manim Legacy Adapter for mathematical taxonomy '{taxonomy}'")
            return self._manim_adapter

        # Default master broadcast engine is Remotion
        logger.info(f"⚡ Routing to Remotion Broadcast Engine for taxonomy '{taxonomy}'")
        return self._remotion_adapter


engine_router = HybridEngineRouter()
