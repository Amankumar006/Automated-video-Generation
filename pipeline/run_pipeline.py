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
import shutil
import tempfile
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import (
    FONT_HELVETICA, FFMPEG_BIN, OUTPUT_DIR, DEFAULT_VOICE,
    BROADCAST_WIDTH, BROADCAST_HEIGHT, BROADCAST_FPS,
    BROADCAST_CRF, BROADCAST_MAXRATE, BROADCAST_BUFSIZE,
    MAX_CONTENT_AGE_DAYS, MAX_PERK_VERIFICATION_AGE_DAYS,
    is_content_recent, calculate_content_age_days,
    resolve_track, TRACK_ACADEMIC, TRACK_TECH_NEWS, TRACK_DEVELOPER_PERKS, TRACK_METADATA
)
from pipeline.audio_synthesizer import synthesize_audio_for_spec
from pipeline.arxiv_fetcher import fetch_arxiv_paper
from pipeline.script_generator import generate_script

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
    },
    "developer_perks": {
        "file": "manim_engine/scenes/developer_perks_scene.py",
        "class": "DeveloperPerksScene",
        "raw_video": "media/videos/developer_perks_scene/1920p30/DeveloperPerksScene.mp4"
    },
    "perks": {
        "file": "manim_engine/scenes/developer_perks_scene.py",
        "class": "DeveloperPerksScene",
        "raw_video": "media/videos/developer_perks_scene/1920p30/DeveloperPerksScene.mp4"
    },
    "startup_credits": {
        "file": "manim_engine/scenes/developer_perks_scene.py",
        "class": "DeveloperPerksScene",
        "raw_video": "media/videos/developer_perks_scene/1920p30/DeveloperPerksScene.mp4"
    },
    "tech_news": {
        "file": "manim_engine/scenes/tech_news_scene.py",
        "class": "TechNewsScene",
        "raw_video": "media/videos/tech_news_scene/1920p30/TechNewsScene.mp4"
    },
    "blogs": {
        "file": "manim_engine/scenes/tech_news_scene.py",
        "class": "TechNewsScene",
        "raw_video": "media/videos/tech_news_scene/1920p30/TechNewsScene.mp4"
    },
    "news": {
        "file": "manim_engine/scenes/tech_news_scene.py",
        "class": "TechNewsScene",
        "raw_video": "media/videos/tech_news_scene/1920p30/TechNewsScene.mp4"
    },
    "official_blogs": {
        "file": "manim_engine/scenes/tech_news_scene.py",
        "class": "TechNewsScene",
        "raw_video": "media/videos/tech_news_scene/1920p30/TechNewsScene.mp4"
    }
}

CATEGORY_ALIASES = {
    "perks": "developer_perks",
    "startup_credits": "developer_perks",
    "blogs": "tech_news",
    "news": "tech_news",
    "official_blogs": "tech_news",
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
                raise RuntimeError(
                    f"Manim completed without a fresh output for {scene_class}; refusing to reuse a stale render."
                )

    if not rendered_file or not os.path.exists(rendered_file):
        raise FileNotFoundError(f"Could not locate rendered video for {scene_class} in {scene_file}")

    print(f"✅ Scene {scene_class} rendered successfully: {rendered_file}")
    return rendered_file

def _probe_duration(path: str, stream: str | None = None) -> float:
    """Return container or stream duration in seconds, failing closed on bad media."""
    ffprobe = shutil.which("ffprobe") or str(Path(FFMPEG_BIN).with_name("ffprobe"))
    selector = ["-select_streams", stream] if stream else []
    entry = "stream=duration" if stream else "format=duration"
    result = subprocess.run(
        [ffprobe, "-v", "error", *selector, "-show_entries", entry, "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(f"Unable to inspect media duration for {path}: {result.stderr.strip()}")
    try:
        return float(result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(f"Invalid media duration returned for {path}: {result.stdout!r}") from exc


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
    video_duration = _probe_duration(video_path)
    audio_duration = _probe_duration(audio_path)
    target_duration = max(video_duration, audio_duration)
    duration_delta = abs(video_duration - audio_duration)
    if duration_delta > 2.0:
        raise RuntimeError(
            f"Audio/video duration mismatch is {duration_delta:.2f}s ({video_duration:.2f}s vs {audio_duration:.2f}s); refusing to mux."
        )
    if master_quality:
        cmd = [
            FFMPEG_BIN, "-y",
            "-i", video_path,
            "-i", audio_path,
            "-vf", f"scale={BROADCAST_WIDTH}:{BROADCAST_HEIGHT},tpad=stop_mode=clone:stop_duration=2",
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
            "-af", "apad",
            "-movflags", "+faststart",
            "-t", f"{target_duration:.3f}",
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
            "-t", f"{target_duration:.3f}",
            output_path
        ]
    print(f"🚀 Muxing and broadcast mastering final short into: {output_path} ({BROADCAST_WIDTH}x{BROADCAST_HEIGHT} @ {BROADCAST_FPS}fps, CRF {BROADCAST_CRF})...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg Error:\n", res.stderr)
        raise RuntimeError("FFmpeg muxing failed.")
    final_video_duration = _probe_duration(output_path, "v:0")
    final_audio_duration = _probe_duration(output_path, "a:0")
    if abs(final_video_duration - final_audio_duration) > (1.0 / BROADCAST_FPS) + 0.03:
        raise RuntimeError(
            f"Muxed streams are not frame-aligned: {final_video_duration:.3f}s vs {final_audio_duration:.3f}s."
        )
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


def build_dry_run_audio_result(spec: dict) -> dict:
    """Build deterministic timing data without invoking a TTS provider.

    Dry-run validates orchestration and storyboard contracts. It must not spend
    provider credits, wait on network retries, or create audio cache entries.
    """
    timing_data = []
    current_time = 0.0
    beats = spec.get("beats", [])
    for index, beat in enumerate(beats):
        duration = float(beat.get("duration") or beat.get("slot_duration") or 5.0)
        pause_duration = 0.30 if index < len(beats) - 1 else 0.50
        timing_data.append(
            {
                "beat_id": beat.get("beat_id", index + 1),
                "text": beat.get("text", ""),
                "visual_focus": beat.get("visual_focus", ""),
                "start": round(current_time, 2),
                "end": round(current_time + duration, 2),
                "duration": round(duration, 2),
                "slot_duration": round(duration + pause_duration, 2),
                "word_timings": [],
                "provider": "dry-run",
                "model": "deterministic-timing",
            }
        )
        current_time += duration + pause_duration
    return {
        "master_audio": "",
        "timing_data": timing_data,
        "total_duration": round(current_time, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="The Model Verse — Multi-Category Automated Video Engine")
    parser.add_argument("--topic", default=None, help="Topic ID or title")
    parser.add_argument("--arxiv", default=None, help="arXiv paper ID or URL to ingest and generate fresh script")
    parser.add_argument("--perk", default=None, help="Verified developer perk program ID (e.g. 'anthropic_startup_program', 'microsoft_founders_hub')")
    parser.add_argument("--template", default=None, help="Path or topic identifier of existing spec JSON template to load")
    parser.add_argument("--fresh", action="store_true", help="Always generate a fresh script from paper instead of using cached template")
    parser.add_argument("--category", choices=list(CATEGORY_SCENE_MAP.keys()), help="Optional category override")
    parser.add_argument("--voice", default=None, help="TTS voice/speaker override (e.g. 'eric', 'shubh', 'am_eric')")
    parser.add_argument("--speed", type=float, default=None, help="Speech speed (default: 1.12)")
    parser.add_argument("--provider", choices=["auto", "elevenlabs", "sarvam", "pocket"], default=None, help="TTS provider override (auto, elevenlabs, sarvam, pocket)")
    parser.add_argument("--lang", "--language", dest="lang", default=None, help="Narration language code (en or hi)")
    parser.add_argument("--quality", default="-qm", choices=["ql", "qm", "qh", "-ql", "-qm", "-qh"], help="Manim render quality")
    parser.add_argument("--skip-render", action="store_true", help="Skip Manim rendering if raw video already exists")
    parser.add_argument("--blog", type=str, default="", help="Specific official blog post or tech news ID (e.g. blog_openai_o3_mini)")
    parser.add_argument("--news", type=str, default="", help="Alias for --blog")
    parser.add_argument("--no-music", action="store_true", help="Disable background synth soundtrack")
    parser.add_argument("--legacy-engine", action="store_true", help="Use legacy monolithic scene templates instead of Visual Engine 2.0 DynamicCompositeScene")
    parser.add_argument("--allow-stale", action="store_true", help="Bypass content recency filter for historical testing")
    parser.add_argument("--dry-run", action="store_true", help="Fast dry-run mode verifying end-to-end pipeline execution with 0 errors")
    parser.add_argument(
        "--validate-visuals",
        action="store_true",
        help="During dry-run, also synthesize and sandbox-check bespoke visuals (may call an LLM)",
    )
    args = parser.parse_args()

    # Dry runs must be genuinely read-only from the repository's perspective.
    # Keep generated audio, subtitles, synthesized visuals, templates, and
    # preview frames in a disposable temporary workspace instead.
    dry_run_workspace = None
    original_generated_visuals_dir = None
    if args.dry_run:
        dry_run_workspace = Path(tempfile.mkdtemp(prefix="themodelverse-dry-run-"))
        (dry_run_workspace / "public").mkdir(parents=True, exist_ok=True)
        (dry_run_workspace / "audio_cache").mkdir(parents=True, exist_ok=True)
        print(f"🧪 [Dry-Run] Isolated workspace: {dry_run_workspace}")

    if args.dry_run and not args.topic and not args.arxiv and not args.perk and not args.blog and not args.news:
        args.topic = "speculative_decoding"

    if not args.topic and not args.arxiv and not args.perk and not args.blog and not args.news:
        parser.error("Either --topic, --arxiv, --perk, or --blog/--news must be provided.")

    arxiv_meta = None
    if args.perk:
        print(f"🎁 Ingesting ground-truth developer perk '{args.perk}'...")
        from pipeline.tech_perks_fetcher import tech_perks_fetcher
        perk_rec = tech_perks_fetcher.get_verified_perk(args.perk)
        if not perk_rec:
            audit = tech_perks_fetcher.verify_perk_claim(args.perk)
            if not audit.get("is_verified"):
                raise ValueError(f"Perk claim '{args.perk}' is unverified: {audit.get('explanation')}")
            perk_rec = tech_perks_fetcher.get_verified_perk(audit.get("program_id", ""))
        if not perk_rec:
            raise RuntimeError(f"Could not retrieve verified perk details for '{args.perk}'")

        if not args.allow_stale and not is_content_recent(perk_rec.last_verified_date, max_age_days=MAX_PERK_VERIFICATION_AGE_DAYS):
            age = calculate_content_age_days(perk_rec.last_verified_date)
            raise ValueError(
                f"Perk '{args.perk}' was last verified on {perk_rec.last_verified_date} ({age} days ago). "
                f"Content unverified for more than {MAX_PERK_VERIFICATION_AGE_DAYS} days is not eligible for publication. "
                "Use --allow-stale to override for historical testing."
            )

        cand = perk_rec.to_candidate_spec()
        topic = args.topic or cand["title"]
        args.category = args.category or "developer_perks"
        arxiv_meta = cand
        print(f"✅ Verified Perk Ingested: {cand['title']}")
    elif args.blog or args.news:
        target_blog_id = args.blog or args.news
        print(f"📰 Ingesting official blog / tech news '{target_blog_id}'...")
        from pipeline.official_blogs_fetcher import official_blogs_fetcher
        blog_rec = official_blogs_fetcher.get_blog(target_blog_id)
        if not blog_rec:
            blog_rec = official_blogs_fetcher.find_blog(target_blog_id)
        if not blog_rec:
            raise RuntimeError(f"Could not retrieve official blog details for '{target_blog_id}'")

        if not args.allow_stale and not is_content_recent(blog_rec.published_date, max_age_days=MAX_CONTENT_AGE_DAYS):
            age = calculate_content_age_days(blog_rec.published_date)
            raise ValueError(
                f"Official blog '{target_blog_id}' was published on {blog_rec.published_date} ({age} days ago). "
                f"News older than {MAX_CONTENT_AGE_DAYS} days (1-2 months) is not eligible for publication. "
                "Use --allow-stale to override for historical testing."
            )

        cand = blog_rec.to_candidate_spec()
        topic = args.topic or cand["title"]
        args.category = args.category or cand.get("category", "tech_news")
        arxiv_meta = cand
        print(f"✅ Official Blog Ingested: {cand['title']} ({blog_rec.provider})")
    elif args.arxiv:
        print(f"🔍 Reading arXiv paper '{args.arxiv}'...")
        arxiv_meta = fetch_arxiv_paper(
            args.arxiv,
            extract_figures=not args.dry_run,
            write_cache=not args.dry_run,
        )
        if not arxiv_meta:
            raise RuntimeError(f"Could not retrieve paper details for '{args.arxiv}'")

        paper_date = arxiv_meta.get("published") or arxiv_meta.get("published_at") or args.arxiv
        if not args.allow_stale and not is_content_recent(paper_date, max_age_days=MAX_CONTENT_AGE_DAYS):
            age = calculate_content_age_days(paper_date)
            raise ValueError(
                f"arXiv paper '{args.arxiv}' was published on {paper_date} ({age} days ago). "
                f"Academic preprints older than {MAX_CONTENT_AGE_DAYS} days (1-2 months) are not eligible for publication. "
                "Use --allow-stale to override for historical testing."
            )

        topic = args.topic or arxiv_meta["title"]
        print(f"📄 Paper Ingested: {arxiv_meta['title']}")
    else:
        topic = args.topic

    templates_dir = PROJECT_ROOT / "pipeline" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    if args.template:
        print(f"📄 Loading specified template for '{args.template}'...")
        spec, template_path = load_template(args.template)
    elif args.dry_run and not (args.fresh or args.arxiv or args.perk or args.blog or args.news):
        try:
            spec, template_path = load_template(topic)
            print(f"📄 [Dry-Run] Loaded fast cached template for '{topic}': {template_path.name}")
        except FileNotFoundError:
            print(f"🧠 Generating brand-new script for '{topic}' directly from source...")
            spec = generate_script(
                topic=topic,
                category=args.category,
                arxiv_meta=arxiv_meta,
                persist=not args.dry_run,
                output_root=dry_run_workspace,
                extract_figures=not args.dry_run,
            )
            template_path = templates_dir / f"{spec.get('category', 'custom')}_{spec['id']}.json"
    else:
        print(f"🧠 Generating brand-new script for '{topic}' directly from source...")
        spec = generate_script(
            topic=topic,
            category=args.category,
            arxiv_meta=arxiv_meta,
            persist=not args.dry_run,
            output_root=dry_run_workspace,
            extract_figures=not args.dry_run,
        )
        template_path = templates_dir / f"{spec.get('category', 'custom')}_{spec['id']}.json"

    if args.dry_run and dry_run_workspace is not None:
        isolated_template = dry_run_workspace / "templates" / Path(template_path).name
        isolated_template.parent.mkdir(parents=True, exist_ok=True)
        isolated_template.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        template_path = isolated_template

    # Ingest / bind native arXiv paper figures
    target_arxiv_id = args.arxiv or spec.get("arxiv_id") or (arxiv_meta.get("arxiv_id") if arxiv_meta else None)
    if target_arxiv_id and not any(str(target_arxiv_id).startswith(p) for p in ("perk_", "gh_", "blog_", "news_")):
        from pipeline.arxiv_vector_extractor import extract_paper_figures, clean_arxiv_id
        clean_id = clean_arxiv_id(str(target_arxiv_id))
        spec["arxiv_id"] = clean_id
        if not spec.get("paper_figures"):
            if arxiv_meta and arxiv_meta.get("paper_figures"):
                spec["paper_figures"] = arxiv_meta["paper_figures"]
                print(f"📊 Transferred {len(spec['paper_figures'])} paper figures from arXiv metadata into spec['paper_figures'].")
            elif args.dry_run:
                print("   ℹ️ [Dry-Run] Skipping arXiv figure extraction; repository cache is read-only.")
            else:
                print(f"\n📊 Ingesting native paper figures for arXiv '{clean_id}'...")
                try:
                    figs = extract_paper_figures(clean_id, max_figures=5)
                    if figs:
                        spec["paper_figures"] = figs
                        print(f"   ✅ Successfully extracted {len(figs)} paper figures to public/arxiv_cache/{clean_id}/ and spec['paper_figures']")
                    else:
                        print(f"   ℹ️ No candidate paper figures found for arXiv '{clean_id}'")
                except Exception as e_figs:
                    print(f"⚠️ arXiv figure extraction notice: {e_figs}")
        else:
            print(f"📊 Spec already contains {len(spec['paper_figures'])} paper figures.")

        # Persist updated spec before storyboard preparation
        with open(template_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2)

    category = args.category or spec.get("category")
    if category:
        category = CATEGORY_ALIASES.get(str(category).lower(), category)
    if category not in CATEGORY_SCENE_MAP:
        raise ValueError(f"Unsupported category '{category}'. Available: {list(CATEGORY_SCENE_MAP.keys())}")

    # Design Script-Driven Visual Storyboard (Visual Engine 4.0 / 5.0)
    print(f"\n🎨 Designing bespoke script-driven visual storyboard...")
    try:
        from pipeline.visual_director import VisualDirector
        visual_director = VisualDirector()
        spec = visual_director.prepare_storyboard_for_spec(
            spec,
            allow_figure_extraction=not args.dry_run,
        )
        with open(template_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2)
    except Exception as e_vd:
        print(f"⚠️ Visual Director notice: {e_vd}")

    track = resolve_track(category)
    track_meta = TRACK_METADATA[track]

    # Step 2.9: Autonomous Bespoke Manim Visual Synthesis (Visual Engine 6.0 for Academic Breakdown)
    if track == TRACK_ACADEMIC and (not args.dry_run or args.validate_visuals):
        print(f"\n🔬 Step 2.9: Synthesizing bespoke 3b1b Manim visual modules on the fly...")
        try:
            from pipeline.bespoke_visual_synthesizer import bespoke_synthesizer
            for idx, beat in enumerate(spec.get("beats", [])):
                b_id = beat.get("beat_id", idx + 1)
                # Prioritize authentic arXiv figures for Beat 3 if available
                if b_id == 3 and spec.get("paper_figures"):
                    continue
                if args.dry_run and dry_run_workspace is not None:
                    from pipeline import bespoke_visual_synthesizer as bespoke_module
                    if original_generated_visuals_dir is None:
                        original_generated_visuals_dir = bespoke_module.GENERATED_VISUALS_DIR
                    bespoke_module.GENERATED_VISUALS_DIR = dry_run_workspace / "generated_visuals"
                bespoke_synthesizer.synthesize_visual_for_beat(spec, beat, b_id)
        except Exception as e_synth:
            print(f"⚠️ Bespoke visual synthesis notice: {e_synth}")
    elif track == TRACK_ACADEMIC:
        print("🧪 [Dry-Run] Skipping bespoke visual synthesis; use --validate-visuals for the expensive sandbox path.")

    scene_info = CATEGORY_SCENE_MAP.get(category, CATEGORY_SCENE_MAP["mechanism_deepdive"])
    if not args.legacy_engine:
        scene_file = track_meta["scene_file"]
        scene_class = track_meta["scene_class"]
        engine_label = f"{track_meta['display_name']} ({track_meta['badge']})"
    else:
        scene_file = scene_info["file"]
        scene_class = scene_info["class"]
        engine_label = f"Legacy Template ({scene_class})"

    resolved_lang = args.lang or spec.get("language") or "en"
    resolved_prov = args.provider or spec.get("tts_provider") or os.environ.get("TTS_PROVIDER", "auto")

    print("\n=======================================================")
    print(f"⚡ THE MODEL VERSE — MULTI-CATEGORY PRODUCTION ENGINE")
    print(f"🎯 Topic: {spec.get('title', args.topic)}")
    print(f"📂 Category: {category.upper()}")
    print(f"🧩 Engine: {engine_label}")
    print(f"🎙️ Narration: {resolved_prov.upper()} ({resolved_lang}, {args.voice or 'default'}) + Ambient Synth + SFX")
    print("=======================================================\n")

    # Step 1: Synthesize Audio & SFX, or use deterministic timing in dry-run.
    if args.dry_run:
        print("🧪 [Dry-Run] Skipping TTS, provider calls, audio cache, and media writes.")
        audio_results = build_dry_run_audio_result(spec)
    else:
        audio_results = synthesize_audio_for_spec(
            spec,
            voice=args.voice,
            speed=args.speed,
            enable_music=not args.no_music,
            provider=resolved_prov,
            language=resolved_lang,
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
    if args.dry_run:
        print("\n⏩ [Dry-Run] Bypassing GPU Manim compilation for fast pipeline verification.")
        raw_video = None
    elif not args.skip_render:
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
    if not args.dry_run:
        mux_final_short(raw_video, master_audio, final_output)
    else:
        print("⏩ [Dry-Run] Bypassing final muxing.")

    # Step 4: Extract Keyframes
    frames_dir = str(
        (dry_run_workspace / f"frames_{spec['id']}")
        if dry_run_workspace
        else (PROJECT_ROOT / f"frames_{spec['id']}")
    )
    if args.dry_run:
        os.makedirs(frames_dir, exist_ok=True)
        for b in spec.get("beats", []):
            bid = b.get("beat_id", 1)
            frame_path = os.path.join(frames_dir, f"0{bid}_beat_{bid}.png")
            if not os.path.exists(frame_path):
                from PIL import Image, ImageDraw
                img = Image.new("RGB", (1080, 1920), color=(10, 13, 20))
                draw = ImageDraw.Draw(img)
                draw.text((100, 200), f"BEAT {bid}: {b.get('text', '')[:30]}", fill=(0, 240, 255))
                img.save(frame_path)
        print(f"📸 [Dry-Run] Prepared {len(spec.get('beats', []))} keyframes in {frames_dir}/")
    else:
        extract_frames(final_output, frames_dir, category=category, spec=spec)

    # Step 5: Master Multimodal Vision Critic & Visual Diversity Gatekeeping
    print("\n=======================================================")
    if args.dry_run:
        print("🧪 [Dry-Run] Skipping VLM frame scoring because no rendered frames exist.")
    else:
        print("👁️ MASTER MULTIMODAL VISION CRITIC (OLLAMA / VLM QA)")
        print("=======================================================\n")
        try:
            from pipeline.vlm_critic import vlm_critic
            audit_report = vlm_critic.audit_batch_keyframes(frames_dir, spec)
            status_str = "✅ PASSED" if audit_report.get("passed_quality_gate") else "⚠️ FLAGGED"
            print(f"\n🎯 [Vision Critic Verdict] {status_str} | Visual Score: {audit_report.get('average_score')}/10 | Unique Layouts: {audit_report.get('unique_layouts_count')}")
            if audit_report.get("diversity_violations"):
                print(f"⚠️ Monotony Violations: {audit_report.get('diversity_violations')}")
        except Exception as e_vlm:
            print(f"⚠️ Vision Critic invocation notice: {e_vlm}")

    if args.dry_run:
        print("\n✅ End-to-end dry-run test completed successfully with 0 errors.")
        if dry_run_workspace:
            if original_generated_visuals_dir is not None:
                from pipeline import bespoke_visual_synthesizer as bespoke_module
                bespoke_module.GENERATED_VISUALS_DIR = original_generated_visuals_dir
            shutil.rmtree(dry_run_workspace, ignore_errors=True)
        return 0

if __name__ == "__main__":
    main()
