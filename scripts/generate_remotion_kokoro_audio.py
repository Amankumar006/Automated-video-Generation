#!/usr/bin/env python3
"""Generate the Remotion preview narration with the local Kokoro ONNX model."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import soundfile as sf

# Allow direct execution via `python3 scripts/...py` from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.voice_engine import UnifiedVoiceRouter


DEFAULT_TEXT = (
    "DeepSeek V3 activates only 37 billion parameters per token across "
    "256 routed experts."
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", default=DEFAULT_TEXT)
    parser.add_argument("--voice", default="am_eric")
    parser.add_argument("--speed", type=float, default=1.05)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("public/audio/kokoro_narration.wav"),
    )
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    router = UnifiedVoiceRouter(cache_dir="public/audio_cache")
    audio, sample_rate, meta = router.synthesize_beat(
        text=args.text,
        voice=args.voice,
        speed=args.speed,
        language="en",
        provider="kokoro",
    )
    sf.write(args.output, audio, sample_rate)
    print(
        f"Generated {args.output} with {meta['provider']} / {meta['model']} / "
        f"{meta['voice']} ({len(audio) / sample_rate:.2f}s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
