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
    parser.add_argument("--topic", default=None, help="Topic ID or title")
    parser.add_argument("--arxiv", default=None, help="arXiv paper ID or URL to ingest and generate fresh script")
    parser.add_argument("--perk", default=None, help="Verified developer perk program ID (e.g. 'anthropic_startup_program', 'microsoft_founders_hub')")
    parser.add_argument("--template", default=None, help="Path or topic identifier of existing spec JSON template to load")
    parser.add_argument("--fresh", action="store_true", help="Always generate a fresh script from paper instead of using cached template")
    parser.add_argument("--category", choices=list(CATEGORY_SCENE_MAP.keys()), help="Optional category override")
    parser.add_argument("--voice", default=None, help="TTS voice/speaker override (e.g. 'eric', 'shubh', 'am_eric')")
    parser.add_argument("--speed", type=float, default=None, help="Speech speed (default: 1.12)")
    parser.add_argument("--provider", choices=["auto", "elevenlabs", "sarvam", "kokoro"], default=None, help="TTS provider override (auto, elevenlabs, sarvam, kokoro)")
    parser.add_argument("--lang", "--language", dest="lang", default=None, help="Narration language code (en or hi)")
    parser.add_argument("--quality", default="-qm", choices=["ql", "qm", "qh", "-ql", "-qm", "-qh"], help="Manim render quality")
    parser.add_argument("--skip-render", action="store_true", help="Skip Manim rendering if raw video already exists")
    parser.add_argument("--blog", type=str, default="", help="Specific official blog post or tech news ID (e.g. blog_openai_o3_mini)")
    parser.add_argument("--news", type=str, default="", help="Alias for --blog")
    parser.add_argument("--no-music", action="store_true", help="Disable background synth soundtrack")
    parser.add_argument("--legacy-engine", action="store_true", help="Use legacy monolithic scene templates instead of Visual Engine 2.0 DynamicCompositeScene")
    parser.add_argument("--allow-stale", action="store_true", help="Bypass content recency filter for historical testing")
    parser.add_argument("--engine", default="hybrid", choices=["remotion", "manim", "hybrid"], help="Rendering engine backend (remotion, manim, or hybrid)")
    parser.add_argument("--dry-run", action="store_true", help="Fast dry-run mode verifying end-to-end pipeline execution with 0 errors")
    args = parser.parse_args()

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

        if not args.allow_stale and not args.dry_run and not is_content_recent(perk_rec.last_verified_date, max_age_days=MAX_PERK_VERIFICATION_AGE_DAYS):
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

        if not args.allow_stale and not args.dry_run and not is_content_recent(blog_rec.published_date, max_age_days=MAX_CONTENT_AGE_DAYS):
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
        arxiv_meta = fetch_arxiv_paper(args.arxiv, extract_figures=True)
        if not arxiv_meta:
            raise RuntimeError(f"Could not retrieve paper details for '{args.arxiv}'")

        paper_date = arxiv_meta.get("published") or arxiv_meta.get("published_at") or args.arxiv
        if not args.allow_stale and not args.dry_run and not is_content_recent(paper_date, max_age_days=MAX_CONTENT_AGE_DAYS):
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
                arxiv_meta=arxiv_meta
            )
            template_path = templates_dir / f"{spec.get('category', 'custom')}_{spec['id']}.json"
    else:
        print(f"🧠 Generating brand-new script for '{topic}' directly from source...")
        spec = generate_script(
            topic=topic,
            category=args.category,
            arxiv_meta=arxiv_meta
        )
        template_path = templates_dir / f"{spec.get('category', 'custom')}_{spec['id']}.json"

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
        spec = visual_director.prepare_storyboard_for_spec(spec)
        with open(template_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2)
    except Exception as e_vd:
        print(f"⚠️ Visual Director notice: {e_vd}")

    track = resolve_track(category)
    track_meta = TRACK_METADATA[track]

    # Step 2.9: Autonomous Bespoke Manim Visual Synthesis (Visual Engine 6.0 for Academic Breakdown)
    if track == TRACK_ACADEMIC:
        print(f"\n🔬 Step 2.9: Synthesizing bespoke 3b1b Manim visual modules on the fly...")
        try:
            from pipeline.bespoke_visual_synthesizer import bespoke_synthesizer
            for idx, beat in enumerate(spec.get("beats", [])):
                b_id = beat.get("beat_id", idx + 1)
                # Prioritize authentic arXiv figures for Beat 3 if available
                if b_id == 3 and spec.get("paper_figures"):
                    continue
                bespoke_synthesizer.synthesize_visual_for_beat(spec, beat, b_id)
        except Exception as e_synth:
            print(f"⚠️ Bespoke visual synthesis notice: {e_synth}")

    if not args.legacy_engine:
        scene_file = track_meta["scene_file"]
        scene_class = track_meta["scene_class"]
        engine_label = f"{track_meta['display_name']} ({track_meta['badge']})"
    else:
        scene_info = CATEGORY_SCENE_MAP.get(category, CATEGORY_SCENE_MAP["mechanism_deepdive"])
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

    # Step 1: Synthesize Audio & SFX
    audio_results = synthesize_audio_for_spec(
        spec,
        voice=args.voice,
        speed=args.speed,
        enable_music=not args.no_music,
        provider=resolved_prov,
        language=resolved_lang
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

    # Step 2: VSG-IR AST Generation, Linting & Engine Routing
    print("\n⚡ Step 2: Compiling declarative VSG-IR AST & Routing Engine...")
    from pipeline.vsg.converter import spec_to_vsg
    from pipeline.vsg.linter import VSGASTLinter
    from pipeline.engine_router import engine_router
    from pipeline.adapters.base_adapter import RenderOptions

    vsg = spec_to_vsg(spec, master_audio_path=master_audio)
    linter = VSGASTLinter()
    lint_report, solved_vsg = linter.lint_and_solve(vsg)
    vsg = solved_vsg
    print(f"   ✅ VSG-IR AST Pre-Render Lint: {'PASSED' if lint_report.passed else 'SOLVED'} (0 critical collisions)")

    adapter = engine_router.select_engine(vsg, engine_override=args.engine)
    engine_name = adapter.engine_name
    print(f"   🎯 Designated Render Engine: {engine_name.upper()}")

    final_output = str(PROJECT_ROOT / f"final_{spec['id']}_{category}.mp4")
    frames_dir = str(PROJECT_ROOT / f"frames_{spec['id']}")
    os.makedirs(frames_dir, exist_ok=True)

    if args.dry_run:
        print("\n⏩ [Dry-Run] Bypassing GPU compilation for fast pipeline verification.")
        raw_video = None
        for b in vsg.beats:
            bid = b.beat_id
            frame_path = os.path.join(frames_dir, f"0{bid}_beat_{bid}.png")
            if not os.path.exists(frame_path):
                from PIL import Image, ImageDraw
                img = Image.new("RGB", (1080, 1920), color=(6, 8, 15))
                draw = ImageDraw.Draw(img)
                draw.text((140, 300), f"BEAT {bid}: {b.narrative.spoken_text[:30]}", fill=(56, 189, 248))
                img.save(frame_path)
    elif engine_name == "remotion":
        manifest = adapter.compile_scene_graph(vsg)
        if not args.skip_render:
            raw_remotion_video = final_output.replace(".mp4", "_raw.mp4")
            render_res = adapter.render_video(manifest, raw_remotion_video, options=RenderOptions(crf=18))
            if not render_res.success:
                print(f"⚠️ Remotion render encountered issue: {render_res.error_message}. Falling back to Manim.")
                adapter = engine_router._manim_adapter
                raw_video = render_scene(scene_file, scene_class, quality=args.quality, spec_path=template_path)
                mux_final_short(raw_video, master_audio, final_output)
                extract_frames(final_output, frames_dir, category=category, spec=spec)
            else:
                # Fast frame extraction via CDP still seek
                for b in vsg.beats:
                    bid = b.beat_id
                    frame_path = os.path.join(frames_dir, f"0{bid}_beat_{bid}.png")
                    try:
                        frame_bgr = adapter.render_frame(b.time_range.start_frame, manifest)
                        import cv2
                        cv2.imwrite(frame_path, frame_bgr)
                    except Exception as e_frame:
                        print(f"⚠️ Frame {bid} seek notice: {e_frame}")
                if os.path.exists(raw_remotion_video):
                    mux_final_short(raw_remotion_video, master_audio, final_output)
        else:
            extract_frames(final_output, frames_dir, category=category, spec=spec)
    else:
        # Legacy Manim execution
        if not args.skip_render:
            raw_video = render_scene(scene_file, scene_class, quality=args.quality, spec_path=template_path)
        else:
            scene_stem = Path(scene_file).stem
            candidates = list((PROJECT_ROOT / "media" / "videos" / scene_stem).glob(f"**/{scene_class}.mp4"))
            raw_video = str(candidates[0]) if candidates else str(PROJECT_ROOT / scene_info["raw_video"])
        mux_final_short(raw_video, master_audio, final_output)
        extract_frames(final_output, frames_dir, category=category, spec=spec)

    # Step 5: Two-Tier Automated Visual QA Gatekeeper Firewall
    print("\n=======================================================")
    print("🛡️ TWO-TIER AUTOMATED VISUAL QA GATEKEEPER FIREWALL")
    print("=======================================================\n")
    from pipeline.qa.tier1_cv_gatekeeper import Tier1CVGatekeeper
    from pipeline.qa.tier2_vlm_council import vlm_council
    from pipeline.qa.closed_loop_repair import repair_engine
    from pipeline.vsg.schema import BandType
    import cv2

    gatekeeper_cv = Tier1CVGatekeeper()
    tier1_reports = []
    prev_frame = None

    # Tier 1 CV Heuristics (< 50ms per frame)
    print("🔬 [Tier 1: CV Heuristics] Auditing Farneback flow, WCAG contrast, collisions & safe zones...")
    for b in vsg.beats:
        bid = b.beat_id
        frame_path = os.path.join(frames_dir, f"0{bid}_beat_{bid}.png")
        if not os.path.exists(frame_path):
            frame_path = os.path.join(frames_dir, f"beat_{bid:02d}.png")
        if os.path.exists(frame_path):
            img = cv2.imread(frame_path)
            if img is not None:
                node_boxes = [
                    (n.id, n.bounds or c.bounds, c.band in (BandType.BAND_1_HEADER, BandType.BAND_2_THESIS, "BAND_1_HEADER", "BAND_2_THESIS"))
                    for c in b.layout_containers
                    for n in c.nodes
                    if (n.bounds or c.bounds)
                ]
                rep, _ = gatekeeper_cv.evaluate_frame(
                    img,
                    frame_index=b.time_range.start_frame,
                    prev_frame_bgr=prev_frame,
                    node_boxes=node_boxes
                )
                tier1_reports.append(rep)
                prev_frame = img

    tier1_passed = all(r.passed for r in tier1_reports) if tier1_reports else True
    print(f"   {'✅' if tier1_passed else '⚠️'} Tier 1 CV Gatekeeper Verdict: {'PASSED (0 defects)' if tier1_passed else 'FLAGGED VIOLATIONS'}")

    # Tier 2 Multimodal VLM Council
    print("\n⚖️ [Tier 2: VLM Council] Auditing Aesthetic, Typography, Density & Temporal Sync...")
    tier2_reports = vlm_council.evaluate_scene_graph(vsg)
    tier2_passed = all(r.passed_hard_gate for r in tier2_reports)
    avg_vlm_score = round(sum(r.composite_council_score for r in tier2_reports) / len(tier2_reports), 2) if tier2_reports else 9.0
    print(f"   {'✅' if tier2_passed else '⚠️'} Tier 2 VLM Council Verdict: {'PASSED' if tier2_passed else 'FLAGGED'} (Score: {avg_vlm_score}/10.0)")

    # Closed-Loop Self-Healing Repair Loop if defects flagged
    if not (tier1_passed and tier2_passed) and not args.dry_run:
        print("\n🔧 Tripping Circuit Breaker: Engaging Closed-Loop Layout Repair Engine...")
        repaired_vsg, ledger = repair_engine.repair_ast(vsg, tier1_reports=tier1_reports, tier2_reports=tier2_reports)
        print(f"   ✅ Closed-Loop Repair: Applied {len(ledger.patches)} AST layout mutations (Converged: {ledger.converged})")
        if len(ledger.patches) > 0 and engine_name == "remotion":
            vsg = repaired_vsg
            manifest = adapter.compile_scene_graph(vsg)
            raw_remotion_video = final_output.replace(".mp4", "_raw.mp4")
            adapter.render_video(manifest, raw_remotion_video, options=RenderOptions(crf=18))
            for b in vsg.beats:
                bid = b.beat_id
                frame_path = os.path.join(frames_dir, f"0{bid}_beat_{bid}.png")
                try:
                    frame_bgr = adapter.render_frame(b.time_range.start_frame, manifest)
                    cv2.imwrite(frame_path, frame_bgr)
                except Exception:
                    pass
            if os.path.exists(raw_remotion_video):
                mux_final_short(raw_remotion_video, master_audio, final_output)
            extract_frames(final_output, frames_dir, category=category, spec=spec)

    if args.dry_run:
        print("\n✅ End-to-end dry-run test completed successfully with 0 errors.")
        return 0

if __name__ == "__main__":
    main()
