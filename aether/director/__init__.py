"""Project Aether Autonomous Director Integration (Phase 10 / WBS 1.11).

Unifies all 6 virtual studio pillars:
1. Narrative World Modeling (State Graph & Prop Tracking)
2. Complexity Planning & Shot Compilation (Veo 3.1, Kling 3.0, Runway Gen-4.5, ComfyUI)
3. Candidate Generation with Speculative Draft Gating (480p -> 1080p)
4. Critic Council Binary Hard Quality Gates (Anatomy, Identity, Prop Continuity, Lip-Sync)
5. Surgical Repair Engine (Regional Inpainting & Audio Remastering)
6. Multi-Shot Continuity Auditing & Assembly
7. Dream-RSI Teacher Engine Episode Logging (ReplaySimulatorPool)
"""

from __future__ import annotations

from aether.director.cli import build_arg_parser, main
from aether.director.orchestrator import AetherDirector, generate_production_brief
from aether.director.schemas import (
    DirectorProductionBrief,
    DirectorProductionStatus,
    FilmScene,
    MasteredFilm,
    ProductionState,
    ShotTimelineRecord,
)

__all__ = [
    # Schemas
    "DirectorProductionBrief",
    "FilmScene",
    "ProductionState",
    "DirectorProductionStatus",
    "ShotTimelineRecord",
    "MasteredFilm",
    # Orchestrator
    "AetherDirector",
    "generate_production_brief",
    # CLI
    "build_arg_parser",
    "main",
]
