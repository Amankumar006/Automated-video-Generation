"""Backwards-compatible pipeline orchestration wrapper for Project Aether Autonomous Director.

Integrates Project Aether Phase 10 (WBS 1.11) with the broader modelverse-shorts pipeline,
allowing automated script-to-video runs, pipeline imports, and legacy orchestration hooks.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Union

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from aether.director import (
    AetherDirector,
    DirectorProductionBrief,
    DirectorProductionStatus,
    FilmScene,
    MasteredFilm,
    ProductionState,
    ShotTimelineRecord,
    build_arg_parser,
    main as cli_main,
)


class AetherDirectorPipeline:
    """Pipeline orchestration wrapper around AetherDirector."""

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        budget_limit: float = 100.0,
        speculative_draft: bool = True,
        max_repair_attempts: int = 2,
    ) -> None:
        self.output_dir = Path(output_dir) if output_dir else Path("./output/aether_films")
        self.budget_limit = budget_limit
        self.speculative_draft = speculative_draft
        self.max_repair_attempts = max_repair_attempts
        self.director = AetherDirector(output_dir=self.output_dir)

    def run(
        self,
        brief: Union[DirectorProductionBrief, str, Dict[str, Any]],
        duration: Optional[float] = None,
        aspect_ratio: Optional[str] = None,
        dry_run: bool = False,
        run_now: bool = True,
    ) -> MasteredFilm:
        """Runs the autonomous virtual studio pipeline."""
        if isinstance(brief, str):
            prod_brief = DirectorProductionBrief(
                title=brief[:40].strip() or "Cinematic Short",
                logline=brief,
                target_duration=duration or 30.0,
                aspect_ratio=aspect_ratio or "9:16",
                budget_limit=self.budget_limit,
                speculative_draft=self.speculative_draft,
                max_repair_attempts=self.max_repair_attempts,
            )
        elif isinstance(brief, dict):
            d = dict(brief)
            if duration:
                d["target_duration"] = duration
            if aspect_ratio:
                d["aspect_ratio"] = aspect_ratio
            prod_brief = DirectorProductionBrief.model_validate(d)
        else:
            prod_brief = brief

        return self.director.produce(brief=prod_brief, dry_run=dry_run, run_now=run_now)


def produce_aether_film(
    brief: Union[DirectorProductionBrief, str, Dict[str, Any]],
    duration: float = 30.0,
    aspect_ratio: str = "9:16",
    output_dir: Optional[str] = None,
    budget_limit: float = 100.0,
    speculative: bool = True,
    dry_run: bool = False,
    run_now: bool = True,
) -> MasteredFilm:
    """Convenience function to run autonomous Aether film production."""
    pipeline = AetherDirectorPipeline(
        output_dir=output_dir,
        budget_limit=budget_limit,
        speculative_draft=speculative,
    )
    return pipeline.run(
        brief=brief,
        duration=duration,
        aspect_ratio=aspect_ratio,
        dry_run=dry_run,
        run_now=run_now,
    )


def run_director_pipeline(
    topic: str,
    duration: float = 30.0,
    aspect_ratio: str = "9:16",
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Compatibility entrypoint matching pipeline convention (returning serializable dict)."""
    mastered = produce_aether_film(
        brief=topic,
        duration=duration,
        aspect_ratio=aspect_ratio,
        dry_run=dry_run,
    )
    return mastered.model_dump(mode="json")


if __name__ == "__main__":
    sys.exit(cli_main())
