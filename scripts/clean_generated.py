#!/usr/bin/env python3
"""Safely identify and quarantine generated artifacts.

The default mode is a report only. ``--apply`` moves exact generated paths to
an external quarantine directory and preserves their repository-relative paths.
No source files are selected by this module and nothing is permanently deleted.
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def discover_generated_paths(root: Path = ROOT) -> list[Path]:
    """Return only known generated paths, in stable relative-path order."""

    root = root.resolve()
    candidates: set[Path] = set()

    # Root-level render and inspection outputs.
    for path in root.glob("final_*.mp4"):
        if path.is_file() and not path.is_symlink():
            candidates.add(path)
    for pattern in (
        "frames_*",
        "media",
        "output",
        "evidence_frames",
        "tmp_inspect_frames",
        ".remotion_cache",
        ".pytest_cache",
        "node_modules",
    ):
        for path in root.glob(pattern):
            if path.exists() and not path.is_symlink():
                candidates.add(path)

    # Generated caches and test media beneath known public/pipeline locations.
    for relative in (
        "public/arxiv_cache",
        "public/audio_cache",
        "public/rendered_videos",
        "pipeline/.draft_render_cache",
    ):
        path = root / relative
        if path.exists() and not path.is_symlink():
            candidates.add(path)

    public = root / "public"
    if public.is_dir():
        candidates.update(
            path
            for path in public.glob("test_*")
            if not path.is_symlink() and (path.is_file() or path.is_dir())
        )

    # Python bytecode caches are safe to regenerate. Do not traverse .git or
    # a quarantine directory supplied by a caller.
    for path in root.rglob("__pycache__"):
        if path.is_dir() and not path.is_symlink() and ".git" not in path.parts:
            candidates.add(path)

    ordered = sorted(
        (path for path in candidates if _within(path.resolve(), root)),
        key=lambda path: (len(path.parts), path.relative_to(root).as_posix()),
    )
    # If a broad generated directory contains a nested bytecode cache, moving
    # the parent is sufficient and prevents a second move from failing.
    selected: list[Path] = []
    for path in ordered:
        if not any(_within(path.resolve(), parent.resolve()) for parent in selected):
            selected.append(path)
    return sorted(selected, key=lambda path: path.relative_to(root).as_posix())


def format_size(path: Path) -> str:
    if path.is_file():
        size = path.stat().st_size
    else:
        size = sum(child.stat().st_size for child in path.rglob("*") if child.is_file())
    units = ("B", "KiB", "MiB", "GiB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def choose_quarantine(root: Path, requested: Path | None = None) -> Path:
    if requested is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        requested = Path(tempfile.gettempdir()) / f"themodelverse-cleanup-{stamp}"
    quarantine = requested.expanduser().resolve()
    if _within(quarantine, root.resolve()):
        raise ValueError("quarantine directory must be outside the repository root")
    quarantine.mkdir(parents=True, exist_ok=True)
    return quarantine


def move_to_quarantine(root: Path, paths: list[Path], quarantine: Path) -> list[Path]:
    """Move paths into quarantine, preserving relative paths."""

    root = root.resolve()
    quarantine = quarantine.resolve()
    if _within(quarantine, root):
        raise ValueError("quarantine directory must be outside the repository root")

    moved: list[Path] = []
    for source in paths:
        source = source.resolve()
        if not _within(source, root) or not source.exists() or source.is_symlink():
            raise ValueError(f"refusing unsafe generated path: {source}")
        destination = quarantine / source.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            raise FileExistsError(f"quarantine destination already exists: {destination}")
        shutil.move(str(source), str(destination))
        moved.append(destination)
    return moved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="move artifacts to quarantine")
    parser.add_argument(
        "--quarantine-dir",
        type=Path,
        help="external quarantine directory (defaults to the system temporary directory)",
    )
    args = parser.parse_args(argv)

    paths = discover_generated_paths()
    if not paths:
        print("No known generated artifacts found.")
        return 0

    print(f"Found {len(paths)} generated artifact path(s):")
    for path in paths:
        print(f"  {path.relative_to(ROOT)} ({format_size(path)})")

    if not args.apply:
        print("Dry run only. Re-run with --apply to move these paths to quarantine.")
        return 0

    quarantine = choose_quarantine(ROOT, args.quarantine_dir)
    moved = move_to_quarantine(ROOT, paths, quarantine)
    print(f"Moved {len(moved)} path(s) to recoverable quarantine: {quarantine}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
