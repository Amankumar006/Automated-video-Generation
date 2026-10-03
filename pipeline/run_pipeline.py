"""
The Model Verse — Unified Multi-Category Video Production CLI
Executes end-to-end automated short video generation across:
  - Architecture Breakdown
  - Model Showdown
  - Mechanism Deep Dive
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import (
    FONT_HELVETICA, FFMPEG_BIN, OUTPUT_DIR,
    BROADCAST_WIDTH, BROADCAST_HEIGHT, BROADCAST_FPS,
    BROADCAST_CRF, BROADCAST_MAXRATE, BROADCAST_BUFSIZE
)
from pipeline.audio_synthesizer import synthesize_audio_for_spec

CATEGORY_SCENE_MAP = {
    "architecture_breakdown": {
        "file": "manim_engine/scenes/architecture_scene.py",
        "class": "ArchitectureBreakdownScene",
        "raw_video": "media/videos/architecture_scene/1920p30/ArchitectureBreakdownScene.mp4"
    },
    "model_showdown": {
        "file": "manim_engine/scenes/showdown_scene.py",
        "class": "ModelShowdownScene",
        "raw_video": "media/videos/showdown_scene/1920p30/ModelShowdownScene.mp4"
    },
    "mechanism_deepdive": {
        "file": "manim_engine/scenes/mechanism_scene.py",
        "class": "MechanismDeepDiveScene",
        "raw_video": "media/videos/mechanism_scene/1920p30/MechanismDeepDiveScene.mp4"
    },
    "benchmark_news": {
        "file": "manim_engine/scenes/benchmark_scene.py",
        "class": "BenchmarkNewsScene",
        "raw_video": "media/videos/benchmark_scene/1920p30/BenchmarkNewsScene.mp4"
    }
}

def load_template(topic: str):
    """Finds and loads the JSON template for the given topic or ID."""
    templates_dir = PROJECT_ROOT / "pipeline" / "templates"
    norm_topic = topic.lower().replace("-", "_")
    for p in sorted(templates_dir.glob("*.json")):
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            d_id = data.get("id", "").lower().replace("-", "_")
            p_stem = p.stem.lower().replace("-", "_")
            if (norm_topic == d_id or norm_topic in d_id or 
                norm_topic == p_stem or norm_topic in p_stem):
                print(f"📄 Loaded template: {p.name} (Category: {data.get('category')})")
                return data, p

    raise FileNotFoundError(f"No template found for topic '{topic}' in {templates_dir}")

def render_scene(scene_file: str, scene_class: str, quality: str = "-qh", spec_path: str = None) -> str:
    """Renders scene with Manim Community and returns the exact path to the output video."""
    import time
    start_time = time.time()
    env = os.environ.copy()
    env["PATH"] = f"/Users/amankumar/bin:{env.get('PATH', '')}"
    if quality in ("draft", "low", "ql", "l", "-l"):
        quality = "-ql"
    elif quality in ("medium", "mid", "qm", "m", "-m"):
        quality = "-qm"
    elif quality in ("high", "qh", "h", "-h"):
        quality = "-qh"
    elif not quality.startswith("-"):
        quality = f"-{quality}"

    if spec_path:
        env["ACTIVE_SPEC_PATH"] = str(spec_path)
    cmd = [
        sys.executable, "-m", "manim",
        quality,
        scene_file,
        scene_class
    ]
    print(f"🎬 Rendering Manim scene {scene_class} from {scene_file} ({quality})...")
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT), env=env, capture_output=True, text=True)
    if res.returncode != 0:
        print("Manim Error:\n", res.stderr)
        raise RuntimeError(f"Manim render failed for {scene_class}")

    rendered_file = None
    output_text = res.stdout + "\n" + res.stderr
    for line in output_text.splitlines():
        if "File ready at" in line or "File written to" in line:
            import re
            m = re.search(r"(?:File ready at|File written to)\s+['\"](.*?)['\"]", line)
            if m:
                cand = Path(m.group(1).strip())
                if not cand.is_absolute():
                    cand = PROJECT_ROOT / cand
                if cand.exists():
                    rendered_file = str(cand)
                    break

    if not rendered_file:
        scene_stem = Path(scene_file).stem
        candidates = list((PROJECT_ROOT / "media" / "videos" / scene_stem).glob(f"**/{scene_class}.mp4"))
        if candidates:
            # Filter candidates modified since render start
            recent = [c for c in candidates if c.stat().st_mtime >= start_time - 2.0]
            if recent:
                recent.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                rendered_file = str(recent[0])
            else:
                candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                rendered_file = str(candidates[0])

    if not rendered_file or not os.path.exists(rendered_file):
        raise FileNotFoundError(f"Could not locate rendered video for {scene_class} in {scene_file}")

    print(f"✅ Scene {scene_class} rendered successfully: {rendered_file}")
    return rendered_file

def mux_final_short(video_path: str, audio_path: str, output_path: str, master_quality: bool = True):
    """
    Muxes visual video and master audio with FFmpeg.
    When master_quality is True:
      - Scales and masters to 1440x2560 (2K QHD vertical) @ 60 FPS
      - Encodes with libx264 high profile, CRF 15, maxrate 25M
      - Sets BT.709 broadcast color tags (preserves chalk contrast & vivid neons)
      - Encodes high-fidelity 320k stereo audio
      - Sets faststart metadata for immediate YouTube playback
      This mandates the YouTube VP09/AV01 premium codec tier, preventing 480p/720p blurriness!
    """
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    if master_quality:
        cmd = [
            FFMPEG_BIN, "-y",
            "-i", video_path,
            "-i", audio_path,
            "-vf", f"scale={BROADCAST_WIDTH}:{BROADCAST_HEIGHT}",
            "-r", str(BROADCAST_FPS),
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", str(BROADCAST_CRF),
            "-maxrate", BROADCAST_MAXRATE,
            "-bufsize", BROADCAST_BUFSIZE,
            "-pix_fmt", "yuv420p",
            "-colorspace", "bt709",
            "-color_primaries", "bt709",
            "-color_trc", "bt709",
            "-color_range", "tv",
            "-c:a", "aac",
            "-b:a", "320k",
            "-movflags", "+faststart",
            "-shortest",
            output_path
        ]
    else:
        cmd = [
            FFMPEG_BIN, "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_path
        ]
    print(f"🚀 Muxing and broadcast mastering final short into: {output_path} ({BROADCAST_WIDTH}x{BROADCAST_HEIGHT} @ {BROADCAST_FPS}fps, CRF {BROADCAST_CRF})...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg Error:\n", res.stderr)
        raise RuntimeError("FFmpeg muxing failed.")
    print(f"🎉 Final broadcast short ready at: {output_path}")

def extract_frames(video_path: str, output_dir: str, category: str = "architecture_breakdown", spec: dict = None):
    """Extracts inspection keyframes across narrative beats."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Clean up old keyframes to prevent stale audits
    for old_png in Path(output_dir).glob("*.png"):
        try:
            old_png.unlink()
        except Exception:
            pass

    timestamps = []
    if spec and "beats" in spec and len(spec["beats"]) > 0 and "start" in spec["beats"][0]:
        for i, b in enumerate(spec["beats"]):
            fname = f"beat_{i+1:02d}.png"
            start = float(b.get("start", 0.0))
            dur = float(b.get("slot_duration", b.get("duration", 5.0)))
            midpoint = start + (dur * 0.52)
            hrs = int(midpoint // 3600)
            mins = int((midpoint % 3600) // 60)
            secs = midpoint % 60
            ts_str = f"{hrs:02d}:{mins:02d}:{secs:06.3f}"
            timestamps.append((ts_str, fname))
    else:
        if category == "model_showdown":
            timestamps = [
                ("00:00:03.000", "01_hook.png"),
                ("00:00:09.500", "02_split_screen.png"),
                ("00:00:18.000", "03_compute_divide.png"),
                ("00:00:26.000", "04_benchmark_race.png"),
                ("00:00:34.000", "05_pricing_shock.png"),
                ("00:00:39.500", "06_chalkboard_outro.png")
            ]
        elif category == "mechanism_deepdive":
            timestamps = [
                ("00:00:03.000", "01_hook.png"),
                ("00:00:10.000", "02_quadratic_trap.png"),
                ("00:00:18.000", "03_kv_cache_storage.png"),
                ("00:00:26.000", "04_o1_query_fetch.png"),
                ("00:00:34.000", "05_payoff_throughput.png"),
                ("00:00:39.500", "06_chalkboard_outro.png")
            ]
        else:
            timestamps = [
                ("00:00:03.500", "01_hook.png"),
                ("00:00:11.000", "02_dense_bottleneck.png"),
                ("00:00:19.500", "03_moe_constellation.png"),
                ("00:00:26.000", "04_shared_expert.png"),
                ("00:00:32.000", "05_top8_lasers.png"),
                ("00:00:41.000", "06_efficiency_synthesis.png"),
                ("00:00:46.000", "07_brand_signature.png")
            ]

    for ts, fname in timestamps:
        out_f = os.path.join(output_dir, fname)
        subprocess.run([
            FFMPEG_BIN, "-y", "-ss", ts, "-i", video_path,
            "-vframes", "1", "-q:v", "2", out_f
        ], capture_output=True)
    print(f"📸 Extracted {len(timestamps)} inspection keyframes to {output_dir}/")


def main():
    parser = argparse.ArgumentParser(description="The Model Verse — Multi-Category Automated Video Engine")
    parser.add_argument("--topic", required=True, help="Topic ID (e.g. deepseek-v3, deepseek_vs_gpt4, kv_cache)")
    parser.add_argument("--category", choices=list(CATEGORY_SCENE_MAP.keys()), help="Optional category override")
    parser.add_argument("--voice", default="am_adam", help="Kokoro TTS voice (default: am_adam)")
    parser.add_argument("--speed", type=float, default=1.12, help="Speech speed (default: 1.12)")
    parser.add_argument("--quality", default="-qm", choices=["-ql", "-qm", "-qh"], help="Manim render quality")
    parser.add_argument("--skip-render", action="store_true", help="Skip Manim rendering if raw video already exists")
    parser.add_argument("--no-music", action="store_true", help="Disable background synth soundtrack")
    parser.add_argument("--legacy-engine", action="store_true", help="Use legacy monolithic scene templates instead of Visual Engine 2.0 DynamicCompositeScene")
    args = parser.parse_args()

    spec, template_path = load_template(args.topic)
    category = args.category or spec.get("category")
    if category not in CATEGORY_SCENE_MAP:
        raise ValueError(f"Unsupported category '{category}'. Available: {list(CATEGORY_SCENE_MAP.keys())}")

    if not args.legacy_engine:
        scene_file = "manim_engine/scenes/script_driven_scene.py"
        scene_class = "ScriptDrivenScene"
        engine_label = "Visual Engine Script-Driven Compiler"
    else:
        scene_info = CATEGORY_SCENE_MAP[category]
        scene_file = scene_info["file"]
        scene_class = scene_info["class"]
        engine_label = f"Legacy Template ({scene_class})"

    print("\n=======================================================")
    print(f"⚡ THE MODEL VERSE — MULTI-CATEGORY PRODUCTION ENGINE")
    print(f"🎯 Topic: {spec.get('title', args.topic)}")
    print(f"📂 Category: {category.upper()}")
    print(f"🧩 Engine: {engine_label}")
    print(f"🎙️ Voice: Kokoro ({args.voice}) + Lo-Fi Ambient Synth + SFX")
    print("=======================================================\n")

    # Step 1: Synthesize Audio & SFX
    audio_results = synthesize_audio_for_spec(
        spec,
        voice=args.voice,
        speed=args.speed,
        enable_music=not args.no_music
    )
    master_audio = audio_results["master_audio"]
    timing_data = audio_results.get("timing_data", [])

    # Enrich spec with millisecond-exact beat durations & acoustic word timings
    for b in spec.get("beats", []):
        for td in timing_data:
            if td["beat_id"] == b.get("beat_id"):
                b["audio_duration"] = td["duration"]
                b["slot_duration"] = td["slot_duration"]
                b["start"] = td["start"]
                b["end"] = td["end"]
                b["word_timings"] = td.get("word_timings", [])

    # Persist the timing-enriched spec so Manim uses exact timestamps
    with open(template_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2)

    # Step 2: Render Manim Scene
    if not args.skip_render:
        raw_video = render_scene(scene_file, scene_class, quality=args.quality, spec_path=template_path)
    else:
        scene_stem = Path(scene_file).stem
        candidates = list((PROJECT_ROOT / "media" / "videos" / scene_stem).glob(f"**/{scene_class}.mp4"))
        if candidates:
            candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            raw_video = str(candidates[0])
        else:
            raw_video = str(PROJECT_ROOT / scene_info["raw_video"])

    # Step 3: Mux Audio & Video
    final_output = str(PROJECT_ROOT / f"final_{spec['id']}_{category}.mp4")
    mux_final_short(raw_video, master_audio, final_output)

    # Step 4: Extract Keyframes
    frames_dir = str(PROJECT_ROOT / f"frames_{spec['id']}")
    extract_frames(final_output, frames_dir, category=category, spec=spec)

if __name__ == "__main__":
    main()
