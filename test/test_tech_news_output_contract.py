"""End-to-end QA contracts for tech-news video packages.

These tests intentionally stay at the artifact boundary.  They do not call
external services and do not change production code.  A tech-news package is
not ready to publish unless its narrated claims, structured evidence,
provider/thumbnail metadata, and rendered media agree.
"""

from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable

import pytest

from pipeline.config import BROADCAST_FPS, BROADCAST_HEIGHT, BROADCAST_WIDTH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
KIMI_SPEC_PATH = PROJECT_ROOT / "pipeline" / "templates" / "tech_news_kimi-k3-1-pro-launch.json"
KIMI_VIDEO_PATH = PROJECT_ROOT / "final_kimi-k3-1-pro-launch_tech_news.mp4"
KIMI_POSTER_PATH = PROJECT_ROOT / "public" / "thumbnails" / "kimi-k3-1-pro-launch_poster.png"

_PERCENT_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*%")
_DECIMAL_CLAIM_RE = re.compile(
    r"\b(?:scores?|at|vs\.?|versus)\s+"
    r"(\d+\.\d+)(?!\w)",
    re.IGNORECASE,
)
_STALE_MARKERS = ("kokoro", "kokoro-onnx", "thumbnail_old", "poster_old")


def _load_kimi_spec() -> dict[str, Any]:
    with KIMI_SPEC_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, str):
        yield value


def _script_text(spec: dict[str, Any]) -> str:
    return " ".join(str(beat.get("text", "")) for beat in spec.get("beats", []))


def _benchmark_script_text(spec: dict[str, Any]) -> str:
    return " ".join(
        str(beat.get("text", ""))
        for beat in spec.get("beats", [])
        if any(
            marker in str(beat.get("text", "")).lower()
            for marker in ("benchmark", "score", "percent", "%")
        )
    )


def _benchmark_values(spec: dict[str, Any]) -> set[float]:
    comparison = spec.get("benchmark_comparison") or {}
    values = {
        float(contestant["value"])
        for contestant in comparison.get("contestants", [])
        if isinstance(contestant, dict) and isinstance(contestant.get("value"), (int, float))
    }
    metadata = spec.get("metadata") or {}
    if isinstance(metadata.get("payoff_stat"), str):
        values.update(float(match) for match in _PERCENT_RE.findall(metadata["payoff_stat"]))
    return values


def _assert_supported_tech_news_claims(spec: dict[str, Any]) -> None:
    """Reject narrated percentage claims that have no structured evidence."""
    supported = _benchmark_values(spec)
    benchmark_text = _benchmark_script_text(spec)
    claimed = {
        float(match)
        for match in (
            *_PERCENT_RE.findall(benchmark_text),
            *_DECIMAL_CLAIM_RE.findall(benchmark_text),
        )
    }
    unsupported = sorted(claimed - supported)
    assert not unsupported, (
        "Narrated percentage claims lack structured benchmark evidence: "
        + ", ".join(f"{value:g}%" for value in unsupported)
    )


def test_tech_news_fixture_has_one_auditable_official_source() -> None:
    spec = _load_kimi_spec()
    metadata = spec["tech_news_metadata"]

    assert spec["category"] == "tech_news"
    assert spec["canonical_url"] == metadata["official_url"]
    assert spec["canonical_url"].startswith("https://")
    assert spec["canonical_url"].split("/", 3)[2] == "www.kimi.ai"
    assert spec["beats"], "A tech-news package must contain narration beats"


def test_narrated_percentage_claims_are_backed_by_benchmark_evidence() -> None:
    """Catch a script/benchmark drift before it reaches a published video."""
    _assert_supported_tech_news_claims(_load_kimi_spec())


def test_unsupported_metric_claim_is_rejected() -> None:
    spec = _load_kimi_spec()
    adversarial = copy.deepcopy(spec)
    adversarial["beats"][3]["text"] += " An unverified run also reached 98.2%."

    with pytest.raises(AssertionError, match=r"98\.2%"):
        _assert_supported_tech_news_claims(adversarial)


def test_no_stale_provider_or_thumbnail_metadata_is_packaged() -> None:
    spec = _load_kimi_spec()
    artifact_strings = list(_walk_strings(spec))

    # Include generated YouTube metadata when a prior production run emitted it.
    # Read the artifact directly so this QA test remains independent of the
    # publisher's external/API-adjacent code paths.
    metadata_path = KIMI_VIDEO_PATH.with_suffix(".youtube_metadata.json")
    if metadata_path.exists():
        with metadata_path.open(encoding="utf-8") as handle:
            artifact_strings.extend(_walk_strings(json.load(handle)))

    stale = [
        value
        for value in artifact_strings
        if any(marker in value.lower() for marker in _STALE_MARKERS)
    ]
    assert not stale, f"Stale provider/thumbnail metadata found: {stale[:5]}"


def test_generated_thumbnail_matches_current_topic_and_vertical_canvas() -> None:
    from PIL import Image

    assert KIMI_POSTER_PATH.exists(), f"Missing topic poster: {KIMI_POSTER_PATH}"
    assert KIMI_POSTER_PATH.stem == "kimi-k3-1-pro-launch_poster"
    with Image.open(KIMI_POSTER_PATH) as poster:
        assert poster.size == (1080, 1920)
        assert poster.height / poster.width == pytest.approx(16 / 9)


@pytest.mark.skipif(
    not KIMI_VIDEO_PATH.exists(),
    reason="Generated Kimi video is an optional local release artifact",
)
def test_rendered_short_has_valid_broadcast_916_metadata() -> None:
    """Inspect the real rendered artifact when it is present in the workspace."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        pytest.skip("ffprobe is required for rendered-media metadata QA")

    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type,width,height,r_frame_rate,duration",
            "-of",
            "json",
            str(KIMI_VIDEO_PATH),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    streams = json.loads(result.stdout)["streams"]
    video = next(stream for stream in streams if stream["codec_type"] == "video")
    audio = next(stream for stream in streams if stream["codec_type"] == "audio")

    assert (video["width"], video["height"]) == (BROADCAST_WIDTH, BROADCAST_HEIGHT)
    assert video["height"] / video["width"] == pytest.approx(16 / 9)
    numerator, denominator = (int(part) for part in video["r_frame_rate"].split("/"))
    assert numerator / denominator == pytest.approx(BROADCAST_FPS)
    assert float(video["duration"]) > 0
    assert float(audio["duration"]) > 0

