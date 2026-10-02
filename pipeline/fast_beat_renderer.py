"""
The Model Verse — High-Speed Headless Beat Keyframe Extractor (Phase 6 Revised)

Strategy:
  Rather than trying to instantiate DynamicCompositeScene in-process (which only
  captures the final empty-screen state after FadeOut), we:
    1. Write the patched spec to a tmp JSON file.
    2. Invoke `manim -ql` as a subprocess (same as the main render_scene call) to
       produce a draft MP4 that correctly reflects the layout overrides.
    3. Use ffmpeg to seek to the beat's midpoint timestamp and extract one PNG frame.

This guarantees the keyframe shows the actual beat content, not an end-of-scene blank.
Typical wall-clock time: ~20-25s per beat on Apple M-series (same as the main -ql render).
We cache the draft MP4 and re-use it across beats within the same repair iteration.
"""

import os
import sys
import json
import subprocess
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import FFMPEG_BIN

DRAFT_CACHE_DIR = PROJECT_ROOT / "pipeline" / ".draft_render_cache"
DRAFT_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _spec_hash(spec: Dict[str, Any]) -> str:
    """Deterministic hash of spec content (layout_overrides included) for cache keying."""
    canonical = json.dumps(spec, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(canonical.encode()).hexdigest()[:12]


def _render_draft_video(
    spec: Dict[str, Any],
    tmp_spec_path: Path,
    scene_file: str = "manim_engine/scenes/script_driven_scene.py",
    scene_class: str = "ScriptDrivenScene"
) -> Optional[str]:
    """
    Renders a -ql draft video from the given spec via a subprocess Manim call.
    Returns path to the rendered MP4, or None on failure.
    """
    scene_file = spec.get("scene_file", scene_file)
    scene_class = spec.get("scene_class", scene_class)

    with open(tmp_spec_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2)

    env = os.environ.copy()
    env["ACTIVE_SPEC_PATH"] = str(tmp_spec_path)
    env["PATH"] = f"/Users/amankumar/bin:{env.get('PATH', '')}"

    cmd = [
        sys.executable, "-m", "manim",
        "-ql",
        "-r", "480,854",
        scene_file,
        scene_class
    ]
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT), env=env, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"⚠️ Draft render error:\n{res.stderr[-800:]}")
        return None

    # Locate the output MP4 from stdout or recursively in media/videos/
    out_text = res.stdout + "\n" + res.stderr
    for line in out_text.splitlines():
        if "File ready at" in line or "File written to" in line:
            import re
            m = re.search(r"(?:File ready at|File written to)\s+['\"](.*?)['\"]", line)
            if m:
                cand = Path(m.group(1).strip())
                if not cand.is_absolute():
                    cand = PROJECT_ROOT / cand
                if cand.exists():
                    return str(cand)

    scene_stem = Path(scene_file).stem
    candidate_dirs = [scene_stem] + [d for d in ["script_driven_scene", "dynamic_scene"] if d != scene_stem]
    all_candidates = []
    for sub_dir in candidate_dirs:
        out_dir = PROJECT_ROOT / "media" / "videos" / sub_dir
        if out_dir.exists():
            for c in out_dir.glob("**/*.mp4"):
                if "partial_movie_files" not in str(c):
                    all_candidates.append(c)
    if all_candidates:
        all_candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return str(all_candidates[0])
    return None


def _extract_frame_at(video_path: str, timestamp_sec: float, output_png: str) -> bool:
    """Uses ffmpeg to extract a single frame at the given timestamp from a video."""
    hrs = int(timestamp_sec // 3600)
    mins = int((timestamp_sec % 3600) // 60)
    secs = timestamp_sec % 60
    ts_str = f"{hrs:02d}:{mins:02d}:{secs:06.3f}"

    cmd = [
        FFMPEG_BIN, "-y",
        "-ss", ts_str,
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",
        output_png
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode == 0 and Path(output_png).exists()


def render_beat_keyframe(
    spec: Dict[str, Any],
    beat_id: int,
    output_png_path: str,
    layout_patches: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Renders a correctly-populated keyframe for a single beat.

    Algorithm:
      1. Clone spec; inject layout_patches into layout_overrides[beat_id].
      2. Compute a content-hash; check DRAFT_CACHE_DIR for an already-rendered draft MP4.
      3. If cache miss: render a new -ql draft video via subprocess.
      4. Compute the beat's midpoint timestamp from spec["beats"][beat_id-1]["start"] + slot/2.
      5. Use ffmpeg -ss to extract the frame at that timestamp.
      6. Return the PNG path.
    """
    # Step 1: Clone spec and inject patches
    active_spec = json.loads(json.dumps(spec))
    if layout_patches:
        if "layout_overrides" not in active_spec:
            active_spec["layout_overrides"] = {}
        if str(beat_id) not in active_spec["layout_overrides"]:
            active_spec["layout_overrides"][str(beat_id)] = {}
        for ent_id, patch in layout_patches.items():
            active_spec["layout_overrides"][str(beat_id)][ent_id] = patch

    # Step 2: Cache lookup
    spec_h = _spec_hash(active_spec)
    cached_video = DRAFT_CACHE_DIR / f"draft_{spec_h}.mp4"

    tmp_spec_path = DRAFT_CACHE_DIR / f".tmp_spec_{spec_h}.json"

    if not cached_video.exists():
        # Step 3: Render draft video
        print(f"      🎬 Rendering draft video for beat {beat_id} (hash={spec_h})...")
        t0 = time.time()
        rendered = _render_draft_video(active_spec, tmp_spec_path)
        if not rendered:
            return None
        # Move to cache slot
        import shutil
        shutil.copy2(rendered, str(cached_video))
        print(f"      ✅ Draft rendered in {time.time()-t0:.1f}s → cached as draft_{spec_h}.mp4")
    else:
        print(f"      ♻️ Reusing cached draft video for beat {beat_id} (hash={spec_h})")

    # Cleanup tmp spec
    if tmp_spec_path.exists():
        try:
            tmp_spec_path.unlink()
        except Exception:
            pass

    # Step 4: Compute beat midpoint timestamp
    timestamp_sec = _get_beat_midpoint(active_spec, beat_id)

    # Step 5: Extract frame with ffmpeg
    out_path = Path(output_png_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    success = _extract_frame_at(str(cached_video), timestamp_sec, str(out_path))
    if not success:
        print(f"⚠️ ffmpeg frame extraction failed for beat {beat_id} at t={timestamp_sec:.2f}s")
        return None

    return str(out_path)


def _get_beat_midpoint(spec: Dict[str, Any], beat_id: int) -> float:
    """
    Returns the midpoint timestamp (seconds) for a given beat_id.
    Uses spec["beats"][i]["start"] + slot_duration * 0.52 if available,
    otherwise falls back to even partitioning of a 60s video.
    """
    beats = spec.get("beats", [])
    for b in beats:
        if b.get("beat_id") == beat_id:
            start = float(b.get("start", 0.0))
            slot = float(b.get("slot_duration", b.get("duration", 8.0)))
            return start + slot * 0.52
    # Fallback: divide 60s evenly
    total = 60.0
    slot = total / max(len(beats), 6)
    return slot * (beat_id - 1) + slot * 0.52


def extract_all_draft_keyframes(
    spec: Dict[str, Any],
    output_dir: str,
    layout_overrides: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Extracts draft keyframes for all beats in the spec into output_dir.
    Renders a single -ql draft video (shared cache) and seeks per-beat timestamps.
    Returns list of saved PNG paths.
    """
    p_dir = Path(output_dir)
    p_dir.mkdir(parents=True, exist_ok=True)

    active_spec = json.loads(json.dumps(spec))
    if layout_overrides:
        active_spec["layout_overrides"] = layout_overrides

    # Render one shared draft video
    spec_h = _spec_hash(active_spec)
    cached_video = DRAFT_CACHE_DIR / f"draft_{spec_h}.mp4"
    tmp_spec_path = DRAFT_CACHE_DIR / f".tmp_spec_{spec_h}.json"

    if not cached_video.exists():
        rendered = _render_draft_video(active_spec, tmp_spec_path)
        if not rendered:
            return []
        import shutil
        shutil.copy2(rendered, str(cached_video))
        if tmp_spec_path.exists():
            try:
                tmp_spec_path.unlink()
            except Exception:
                pass

    beats = active_spec.get("beats", [])
    saved_frames = []
    for b in beats:
        b_id = b.get("beat_id", 1)
        ts = _get_beat_midpoint(active_spec, b_id)
        out_f = str(p_dir / f"beat_{b_id:02d}.png")
        if _extract_frame_at(str(cached_video), ts, out_f):
            saved_frames.append(out_f)

    return saved_frames
