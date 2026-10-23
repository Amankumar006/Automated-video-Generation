#!/usr/bin/env python3
"""Report whether the local repository is ready for development or rendering.

This module intentionally uses only the Python standard library so it can be
run before the project virtual environment has been created.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str
    required: bool = True


REQUIRED_FILES = (
    "requirements.txt",
    "package.json",
    "package-lock.json",
    "pytest.ini",
    ".env.example",
)

# These are needed for the complete pipeline, but a contributor may still
# inspect Python or TypeScript code before installing the native render stack.
COMMANDS = {
    "git": "version control",
    "node": "frontend tooling",
    "npm": "frontend dependency installation",
    "ffmpeg": "video encoding",
    "manim": "scene rendering",
    "latex": "formula rendering",
    "dvisvgm": "formula-to-SVG conversion",
    "espeak-ng": "fallback speech/audio tooling",
}


def check_python() -> Check:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    supported = (sys.version_info.major, sys.version_info.minor) in {(3, 11), (3, 12)}
    return Check(
        "python",
        supported,
        f"{version} (supported: 3.11 or 3.12)",
    )


def check_commands() -> list[Check]:
    checks = []
    for command, purpose in COMMANDS.items():
        location = shutil.which(command)
        checks.append(
            Check(
                command,
                location is not None,
                f"{location or 'not found'} — {purpose}",
                required=command in {"git", "node", "npm", "ffmpeg"},
            )
        )
    return checks


def check_repository(root: Path = ROOT) -> list[Check]:
    checks = [
        Check(
            f"file:{relative}",
            (root / relative).is_file(),
            str(root / relative),
        )
        for relative in REQUIRED_FILES
    ]

    for relative in (".", "public"):
        path = root / relative
        checks.append(
            Check(
                f"writable:{relative}",
                path.is_dir() and os.access(path, os.W_OK),
                str(path),
            )
        )

    env_path = root / ".env"
    checks.append(
        Check(
            ".env",
            env_path.is_file(),
            "present (values not inspected)" if env_path.is_file() else "not found; copy .env.example to .env",
            required=False,
        )
    )
    return checks


def collect_checks(root: Path = ROOT) -> list[Check]:
    return [check_python(), *check_commands(), *check_repository(root)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="fail when any development or rendering prerequisite is missing",
    )
    args = parser.parse_args(argv)

    checks = collect_checks()
    for check in checks:
        label = "OK" if check.ok else ("MISSING" if check.required else "INFO")
        print(f"[{label:7}] {check.name}: {check.detail}")

    failures = [check for check in checks if not check.ok and (args.strict or check.required)]
    print()
    if failures:
        print(f"Doctor found {len(failures)} blocking issue(s).")
        print("Install the missing prerequisite(s), then run `make doctor` again.")
        return 1

    missing_optional = [check for check in checks if not check.ok]
    if missing_optional:
        print("Development prerequisites are present; rendering prerequisites are still missing.")
    else:
        print("Environment is ready for development and rendering.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
