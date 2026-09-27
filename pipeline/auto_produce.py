"""
The Model Verse — Autonomous End-to-End Short Video Producer
Executes full-pipeline video generation from a single topic name, model profile, or arXiv URL:
  1. Ingests topic or arXiv metadata
  2. Generates 6-beat narrative script via Gemini 2.5 Flash
  3. Auto-synthesizes Computer Modern LaTeX vector SVGs
  4. Synthesizes Kokoro neural audio narration + procedural SFX
  5. Renders 3Blue1Brown chalkboard Manim scene with kinetic captions
  6. Muxes broadcast MP4 with FFmpeg and extracts verification keyframes
"""

import os
import sys
import json
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import OUTPUT_DIR, FFMPEG_BIN
from pipeline.arxiv_fetcher import fetch_arxiv_paper
from pipeline.script_generator import generate_script
from pipeline.audio_synthesizer import synthesize_audio_for_spec
from pipeline.run_pipeline import render_scene, mux_final_short, extract_frames, CATEGORY_SCENE_MAP

def auto_produce(
    topic: str = None,
    arxiv: str = None,
    category: str = None,
    voice: str = "am_adam",
    speed: float = None,
    quality: str = "-qm",
    skip_script: bool = False,
    template: str = None,
    publish: bool = False,
    privacy: str = "unlisted",
    dry_run_publish: bool = False,
    enable_music: bool = True,
    legacy_engine: bool = False
) -> str:
    print("\n=======================================================")
    print("🚀 THE MODEL VERSE — AUTONOMOUS SHORT VIDEO PRODUCER")
    print("=======================================================\n")

    if speed is None:
        try:
            from pipeline.analytics_feedback import get_recommended_pacing
            speed = get_recommended_pacing().get("tts_speed", 1.12)
            print(f"⚡ Dynamic Audience Retention Pacing Applied: {speed}x speech delivery")
        except Exception:
            speed = 1.10

    templates_dir = PROJECT_ROOT / "pipeline" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    template_path = None
    spec = None

    if template:
        template_path = Path(template).resolve()
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                spec = json.load(f)
            topic = spec.get("title", topic or "Untitled")
            print(f"📄 Loaded specified template: {template_path.name}")
        else:
            raise FileNotFoundError(f"Specified template not found: {template}")

    arxiv_meta = None
    if arxiv and not spec:
        print(f"🔍 Step 1: Ingesting arXiv paper '{arxiv}'...")
        arxiv_meta = fetch_arxiv_paper(arxiv)
        if not arxiv_meta:
            raise RuntimeError(f"Could not retrieve paper metadata for '{arxiv}'")
        if not topic:
            topic = arxiv_meta["title"]
        print(f"📄 Ingested: {arxiv_meta['title']}")

    if not topic and not spec:
        raise ValueError("Either topic, arxiv, or template must be provided.")

    if skip_script and not spec:
        # Search for existing template
        query_words = [w.lower().strip(":-_.,") for w in topic.split() if len(w) >= 4]
        for p in sorted(templates_dir.glob("*.json")):
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
                d_id = d.get("id", "").lower()
                p_name = p.stem.lower()
                topic_lower = topic.lower()
                if (topic_lower in d_id or d_id in topic_lower or 
                    topic_lower in p_name or p_name in topic_lower or
                    any(w in d_id or w in p_name for w in query_words)):
                    spec = d
                    template_path = p
                    print(f"📄 Loaded existing template: {p.name}")
                    break
        if not spec:
            print("⚠️ Existing template not found. Generating fresh script...")

    if not spec:
        print(f"🧠 Step 2: Generating script with Gemini 2.5 Flash for '{topic}'...")
        spec = generate_script(
            topic=topic,
            category=category,
            arxiv_meta=arxiv_meta
        )
        template_path = templates_dir / f"{spec['category']}_{spec['id']}.json"

    # Step 2.5: Script Pedagogy & Comprehensibility Audit
    print(f"\n🎙️ Step 2.5: Running Script Pedagogy & Comprehensibility Audit...")
    from pipeline.script_critic import ScriptCritic
    script_critic = ScriptCritic()
    script_report = script_critic.evaluate_script(spec, use_llm=False)
    print(f"   📊 Pedagogical Score: {script_report.overall_score}/10 | Audience Level: Grade {script_report.grade_level} | Reading Ease: {script_report.reading_ease}/100")
    print(f"   💡 Everyday Analogies Found: {script_report.total_analogies} | Heavy Academic Jargon: {script_report.total_critical_jargon}")
    if not script_report.passed:
        print(f"   ⚠️ Script Warning: {script_report.summary_verdict}")
    else:
        print(f"   ✅ Script Quality Gate Passed: Conversational, accessible, and grounded in everyday examples.")

    # Step 2.8: Script-Driven Visual Storyboard Synthesis
    print(f"\n🎨 Step 2.8: Designing bespoke script-driven visual storyboard...")
    try:
        from pipeline.visual_director import VisualDirector
        visual_director = VisualDirector()
        spec = visual_director.prepare_storyboard_for_spec(spec)
        with open(template_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2)
    except Exception as e:
        print(f"⚠️ Visual Director bypassed: {e}")

    resolved_category = spec.get("category", category or "mechanism_deepdive")
    if resolved_category not in CATEGORY_SCENE_MAP:
        resolved_category = "mechanism_deepdive"

    if not legacy_engine:
        scene_file = "manim_engine/scenes/script_driven_scene.py"
        scene_class = "ScriptDrivenScene"
        engine_label = "Visual Engine 3.0 Script-Driven Compiler"
    else:
        scene_info = CATEGORY_SCENE_MAP[resolved_category]
        scene_file = scene_info["file"]
        scene_class = scene_info["class"]
        engine_label = f"Legacy Template ({scene_class})"

    print(f"\n🎯 Title: {spec['title']}")
    print(f"📂 Category: {resolved_category.upper()}")
    print(f"🧩 Engine: {engine_label}")
    print(f"🎙️ Narration: Kokoro ({voice}) at {speed}x speed")

    # Step 3: Synthesize Audio & Procedural SFX
    print("\n🎙️ Step 3: Synthesizing neural audio narration, procedural SFX, and ambient soundtrack...")
    audio_results = synthesize_audio_for_spec(spec, voice=voice, speed=speed, enable_music=enable_music)
    master_audio = audio_results["master_audio"]
    audio_duration = audio_results.get("total_duration", 40.0)
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

    # Step 4: Render 3Blue1Brown Blackboard Manim Scene
    print(f"\n🎬 Step 4: Rendering 3b1b Manim blackboard scene ({quality}) via {engine_label}...")
    raw_video = render_scene(
        scene_file=scene_file,
        scene_class=scene_class,
        quality=quality,
        spec_path=str(template_path)
    )

    # Step 5: Mux Final Broadcast Short
    print("\n🚀 Step 5: Muxing broadcast MP4 with synchronized kinetic captions...")
    final_output = str(PROJECT_ROOT / f"final_{spec['id']}_{resolved_category}.mp4")
    mux_final_short(raw_video, master_audio, final_output)

    # Step 6: Extract Inspection Keyframes & Generate High-CTR Poster
    print("\n📸 Step 6: Extracting inspection keyframes and generating high-CTR poster...")
    frames_dir = str(PROJECT_ROOT / f"frames_{spec['id']}")
    extract_frames(final_output, frames_dir, category=resolved_category, spec=spec)

    from pipeline.thumbnail_generator import thumbnail_generator
    from scripts.generate_thumbnail import find_best_keyframe
    best_kf = find_best_keyframe(spec['id'])
    poster_path = thumbnail_generator.generate(spec=spec, base_keyframe_path=best_kf)
    print(f"🖼️ High-CTR YouTube Shorts Poster: {poster_path}")

    # Step 6.5: Closed-Loop VLM Critic Quality Audit & Self-Healing Loop (Phase 6)
    print("\n🧐 Step 6.5: Auditing visual quality & 3b1b compliance via Gemini Vision VLM Critic...")
    try:
        from pipeline.vlm_critic import vlm_critic
        from pipeline.fast_beat_renderer import render_beat_keyframe, DRAFT_CACHE_DIR
        import shutil

        audit_report = vlm_critic.audit_batch_keyframes(frames_dir, spec)
        avg_score = audit_report.get('average_score', 0.0)
        print(f"   📊 Initial VLM Quality Score: {avg_score:.2f}/10.0")

        # Self-Healing Loop if score < 8.5
        needs_repair = not audit_report.get("passed_quality_gate", True)
        repair_iteration = 0
        max_repair_iterations = 2
        patches_applied = False

        while needs_repair and repair_iteration < max_repair_iterations:
            repair_iteration += 1
            print(f"\n🔧 [Phase 6 Auto-Repair] Entering Self-Healing Loop (Iteration {repair_iteration}/{max_repair_iterations})...")

            # Clear draft video cache so new patches are rendered fresh
            if DRAFT_CACHE_DIR.exists():
                for stale in DRAFT_CACHE_DIR.glob("draft_*.mp4"):
                    try:
                        stale.unlink()
                    except Exception:
                        pass

            beat_evals = audit_report.get("beat_evaluations", [])
            iteration_patched = False

            for b_eval in beat_evals:
                b_id = b_eval.get("beat_id", 1)
                b_score = b_eval.get("overall_score", 0.0)
                suggested_patches = b_eval.get("suggested_patches", [])

                # Skip beats that already pass the threshold
                if b_score >= 8.5:
                    continue

                if not suggested_patches:
                    continue

                print(f"   🎯 Auto-repairing Beat {b_id} (Score: {b_score:.1f}/10, Patches: {len(suggested_patches)})...")
                if "layout_overrides" not in spec:
                    spec["layout_overrides"] = {}
                if str(b_id) not in spec["layout_overrides"]:
                    spec["layout_overrides"][str(b_id)] = {}

                # Save checkpoint for rollback
                prev_overrides = json.loads(json.dumps(spec["layout_overrides"][str(b_id)]))

                # Apply proposed patches — merge by entity_id (accumulate dx/dy additively)
                for patch in suggested_patches:
                    ent_id = patch.get("entity_id", "hero_visual")
                    dx = float(patch.get("dx", 0.0))
                    dy = float(patch.get("dy", 0.0))
                    scale_m = float(patch.get("scale_multiplier", 1.0))
                    existing = spec["layout_overrides"][str(b_id)].get(ent_id, {"dx": 0.0, "dy": 0.0, "scale_multiplier": 1.0})
                    spec["layout_overrides"][str(b_id)][ent_id] = {
                        "dx": round(existing.get("dx", 0.0) + dx, 3),
                        "dy": round(existing.get("dy", 0.0) + dy, 3),
                        "scale_multiplier": round(existing.get("scale_multiplier", 1.0) * scale_m, 3)
                    }
                    print(f"      Applied patch to '{ent_id}': dx={dx:+.2f}, dy={dy:+.2f}, scale={scale_m:.2f}")

                # Re-render keyframe for this beat with patched layout
                target_png = Path(frames_dir) / f"{b_id:02d}_beat_{b_id}_repaired.png"
                rendered_kf = render_beat_keyframe(
                    spec=spec,
                    beat_id=b_id,
                    output_png_path=str(target_png),
                    layout_patches=spec["layout_overrides"].get(str(b_id), {})
                )

                if rendered_kf and Path(rendered_kf).exists():
                    re_eval = vlm_critic.audit_keyframe(rendered_kf, spec, beat_id=b_id)
                    new_score = re_eval.get("overall_score", 0.0)
                    print(f"      Re-audit score: {new_score:.1f}/10 (Previous: {b_score:.1f}/10)")

                    # Monotonic acceptance: accept only if score improves or holds
                    if new_score >= b_score:
                        print(f"      ✅ Patch accepted (+{new_score - b_score:.1f} score gain)!")
                        iteration_patched = True
                        patches_applied = True
                        try:
                            canonical_frame = Path(frames_dir) / f"beat_{b_id:02d}.png"
                            shutil.copy2(str(target_png), str(canonical_frame))
                        except Exception:
                            pass
                    else:
                        print(f"      ↩️ Score regressed ({new_score:.1f} < {b_score:.1f}). Rolling back Beat {b_id}.")
                        spec["layout_overrides"][str(b_id)] = prev_overrides
                else:
                    print(f"      ⚠️ Keyframe render failed for Beat {b_id}. Rolling back.")
                    spec["layout_overrides"][str(b_id)] = prev_overrides

            if iteration_patched:
                # Persist spec with accepted patches
                with open(template_path, "w", encoding="utf-8") as f:
                    json.dump(spec, f, indent=2)
                # Re-audit against the freshly-patched keyframes in frames_dir
                audit_report = vlm_critic.audit_batch_keyframes(frames_dir, spec)
                needs_repair = not audit_report.get("passed_quality_gate", True)
                avg_after = audit_report.get('average_score', 0.0)
                print(f"   📊 Post-Repair VLM Quality Score: {avg_after:.2f}/10.0")
            else:
                print("   ℹ️ No patches accepted this iteration — stopping repair loop.")
                break

        if patches_applied:
            print("\n🔄 Re-rendering final master scene with accepted layout patches...")
            raw_video = render_scene(
                scene_file=scene_file,
                scene_class=scene_class,
                quality=quality,
                spec_path=str(template_path)
            )
            mux_final_short(raw_video, master_audio, final_output)
            extract_frames(final_output, frames_dir, category=resolved_category, spec=spec)
            print("   ✅ Master render and keyframes updated with patched layout.")

        if audit_report.get("passed_quality_gate"):
            print("   ✅ VLM Critic Quality Gate: PASSED (Broadcast Quality)")
        else:
            print("   ℹ️ VLM Critic Quality Gate: Best-effort self-healing completed.")
    except Exception as e:
        import traceback
        print(f"   ⚠️ VLM Critic Audit bypassed: {e}")
        traceback.print_exc()


    # Step 7: Automated YouTube Shorts Distribution
    if publish or dry_run_publish:
        from pipeline.publisher import generate_shorts_metadata, upload_short
        print("\n🚀 Step 7: YouTube Shorts automated distribution...")
        metadata = generate_shorts_metadata(spec, final_output)
        if dry_run_publish:
            print("\n=======================================================")
            print("🔍 YOUTUBE SHORTS METADATA PREVIEW (DRY-RUN)")
            print("=======================================================\n")
            print(f"🎯 TITLE: {metadata['title']}")
            print(f"📝 DESCRIPTION:\n{metadata['description']}\n")
            print(f"🏷️ TAGS: {', '.join(metadata['tags'])}")
            print(f"💬 PINNED COMMENT: {metadata['pinned_comment']}")
            print(f"🔒 PRIVACY STATUS: {privacy.upper()}")
            print("=======================================================\n")
        else:
            upload_short(final_output, metadata, privacy_status=privacy)

    print("\n=======================================================")
    print("🎉 AUTONOMOUS VIDEO PRODUCTION COMPLETE!")
    print(f"🎥 Video: {final_output}")
    print(f"🖼️ Frames: {frames_dir}/")
    print("=======================================================\n")
    return final_output

def main():
    # Preprocess sys.argv so --quality -qm becomes --quality=-qm
    new_argv = []
    i = 0
    while i < len(sys.argv):
        if sys.argv[i] == "--quality" and i + 1 < len(sys.argv) and sys.argv[i+1].startswith("-"):
            new_argv.append(f"--quality={sys.argv[i+1]}")
            i += 2
        else:
            new_argv.append(sys.argv[i])
            i += 1
    sys.argv = new_argv

    parser = argparse.ArgumentParser(description="The Model Verse — Autonomous Short Video Producer")
    parser.add_argument("--topic", help="Topic name or prompt (e.g. 'FlashAttention-3', 'DeepSeek-R1')")
    parser.add_argument("--arxiv", help="arXiv paper ID or URL (e.g. '2407.08608')")
    parser.add_argument("--template", help="Path to existing spec JSON template")
    parser.add_argument("--category", choices=list(CATEGORY_SCENE_MAP.keys()), help="Optional category override")
    parser.add_argument("--voice", default="am_adam", help="Kokoro voice (default: am_adam)")
    parser.add_argument("--speed", type=float, default=1.10, help="Speech speed (default: 1.10)")
    parser.add_argument("--quality", default="-qh", help="Manim render quality (-ql, -qm, -qh)")
    parser.add_argument("--skip-script", action="store_true", help="Skip script generation if template exists")
    parser.add_argument("--publish", action="store_true", help="Upload produced video to YouTube Shorts")
    parser.add_argument("--privacy", choices=["unlisted", "public", "private"], default="unlisted", help="Upload privacy status (default: unlisted)")
    parser.add_argument("--dry-run-publish", action="store_true", help="Preview YouTube title, tags, description without uploading")
    parser.add_argument("--no-music", action="store_true", help="Disable procedural lo-fi ambient background music")
    args = parser.parse_args()

    if not args.topic and not args.arxiv and not args.template:
        parser.error("Either --topic, --arxiv, or --template must be specified.")

    qual = args.quality
    if qual:
        q_low = qual.lower().strip()
        if q_low in ["ql", "low"]: qual = "-ql"
        elif q_low in ["qm", "medium", "med"]: qual = "-qm"
        elif q_low in ["qh", "high"]: qual = "-qh"
        elif not qual.startswith("-"): qual = f"-{qual}"
    else:
        qual = "-qh"

    auto_produce(
        topic=args.topic,
        arxiv=args.arxiv,
        template=args.template,
        category=args.category,
        voice=args.voice,
        speed=args.speed,
        quality=qual,
        skip_script=args.skip_script,
        publish=args.publish,
        privacy=args.privacy,
        dry_run_publish=args.dry_run_publish,
        enable_music=not args.no_music
    )

if __name__ == "__main__":
    main()
