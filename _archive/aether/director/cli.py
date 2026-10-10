"""Project Aether Autonomous Director Master CLI & Daemon Entrypoint.

Provides the master command-line interface for Project Aether v2 (Phase 10 / WBS 1.11.1):
`python3 -m aether.director --brief "Cyberpunk noir thriller" --duration 30 --aspect-ratio 9:16 --output ./output`
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import List, Optional

from aether.director.orchestrator import AetherDirector
from aether.director.schemas import DirectorProductionBrief, MasteredFilm


def build_arg_parser() -> argparse.ArgumentParser:
    """Builds the comprehensive command-line argument parser for AetherDirector."""
    parser = argparse.ArgumentParser(
        prog="aether.director",
        description="Project Aether v2: Autonomous End-to-End Virtual Studio Director",
    )
    parser.add_argument(
        "--brief",
        type=str,
        default="Cyberpunk noir thriller in abandoned cleanroom",
        help="Production concept prompt or film title (default: 'Cyberpunk noir thriller in abandoned cleanroom')",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=30.0,
        help="Target film duration in seconds (e.g. 30 or 60, default: 30.0)",
    )
    parser.add_argument(
        "--aspect-ratio",
        type=str,
        default="9:16",
        choices=["9:16", "16:9", "vertical", "horizontal"],
        help="Target cinematic aspect ratio ('9:16' or '16:9', default: '9:16')",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./output/aether_films",
        help="Target output directory for artifacts and manifests (default: ./output/aether_films)",
    )
    parser.add_argument(
        "--budget-limit",
        type=float,
        default=100.0,
        help="Maximum generation and repair compute budget in USD (default: 100.0)",
    )
    parser.add_argument(
        "--speculative",
        dest="speculative",
        action="store_true",
        default=True,
        help="Enable rapid 480p speculative draft gating before full 1080p latent upscale (default: True)",
    )
    parser.add_argument(
        "--no-speculative",
        dest="speculative",
        action="store_false",
        help="Disable speculative draft gating and generate directly at full resolution",
    )
    parser.add_argument(
        "--max-repairs",
        type=int,
        default=2,
        help="Maximum surgical repair attempts per shot before escalation (default: 2)",
    )
    parser.add_argument(
        "--style",
        type=str,
        default="cinematic photorealistic",
        help="Visual aesthetic style descriptor (default: 'cinematic photorealistic')",
    )
    parser.add_argument(
        "--run-now",
        dest="run_now",
        action="store_true",
        default=True,
        help="Immediately launch autonomous production run (default: True)",
    )
    parser.add_argument(
        "--no-run-now",
        dest="run_now",
        action="store_false",
        help="Stage production plan and world model without immediately running generative rendering",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Execute production simulation without making external API or rendering calls",
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        default=False,
        help="Print final output strictly as JSON",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Master CLI execution entrypoint."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    brief = DirectorProductionBrief(
        title=args.brief[:50].strip() or "Cinematic Production",
        logline=args.brief,
        target_duration=args.duration,
        aspect_ratio=args.aspect_ratio,
        visual_style=args.style,
        budget_limit=args.budget_limit,
        speculative_draft=args.speculative,
        max_repair_attempts=args.max_repairs,
    )

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    director = AetherDirector(output_dir=output_dir)

    try:
        mastered_film: MasteredFilm = director.produce(
            brief=brief,
            dry_run=args.dry_run,
            run_now=args.run_now,
        )

        if args.json_output:
            print(json.dumps(mastered_film.model_dump(mode="json"), indent=2))
        else:
            print("\n" + "=" * 60)
            print("🎬 AETHER AUTONOMOUS DIRECTOR PRODUCTION COMPLETE")
            print("=" * 60)
            print(mastered_film.summary())
            print("=" * 60 + "\n")
        return 0

    except Exception as exc:
        sys.stderr.write(f"❌ Production Failed: {str(exc)}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
