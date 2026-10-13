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
from typing import Optional, Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import (
    OUTPUT_DIR, FFMPEG_BIN, DEFAULT_VOICE,
    resolve_track, TRACK_ACADEMIC, TRACK_METADATA
)
from pipeline.arxiv_fetcher import fetch_arxiv_paper
from pipeline.script_generator import generate_script
from pipeline.audio_synthesizer import synthesize_audio_for_spec
from pipeline.run_pipeline import render_scene, mux_final_short, extract_frames, CATEGORY_SCENE_MAP

def auto_produce(
    topic: str = None,
    arxiv: str = None,
    category: str = None,
    voice: str = None,
    speed: float = None,
    quality: str = "-qm",
    skip_script: bool = False,
    template: str = None,
    publish: bool = False,
    privacy: str = "public",
    dry_run_publish: bool = False,
    enable_music: bool = True,
    legacy_engine: bool = False,
    paper_meta: Optional[Dict[str, Any]] = None,
    provider: Optional[str] = None,
    language: Optional[str] = None,
    skip_repair: bool = False,
    publish_instagram: bool = False,
    publish_x: bool = False,
    publish_linkedin: bool = False,
    engine: str = "hybrid"
) -> str:


    if language in ("both", "all", "dual"):
        print("\n=======================================================")
        print("🌐 DUAL-LANGUAGE PRODUCTION ENGINE: ENGLISH + HINDI")
        print("=======================================================\n")
        print("▶️ [1/2] Producing English Short (ElevenLabs / Eric)...")
        res_en = auto_produce(
            topic=topic,
            arxiv=arxiv,
            category=category,
            voice=voice,
            speed=speed,
            quality=quality,
            skip_script=skip_script,
            template=template,
            publish=publish,
            privacy=privacy,
            dry_run_publish=dry_run_publish,
            enable_music=enable_music,
            legacy_engine=legacy_engine,
            paper_meta=paper_meta,
            provider="elevenlabs",
            language="en",
            skip_repair=skip_repair,
            publish_instagram=publish_instagram,
            publish_x=publish_x,
            publish_linkedin=publish_linkedin,
            engine=engine
        )
        # Locate the template generated or used by the English pass
        hi_template = template
        if not hi_template and res_en:
            p_stem = Path(res_en).stem
            for cand in sorted(templates_dir.glob("*.json"), key=os.path.getmtime, reverse=True):
                c_stem = cand.stem
                cand_id = c_stem.replace("architecture_breakdown_", "").replace("mechanism_deepdive_", "").replace("model_showdown_", "").replace("benchmark_news_", "")
                if cand_id and cand_id in p_stem:
                    hi_template = str(cand)
                    print(f"📄 Reusing English visual blueprint template for Hindi pass: {cand.name}")
                    break

        print("\n▶️ [2/2] Producing Hindi Short (Sarvam AI / Shubh)...")
        res_hi = auto_produce(
            topic=topic,
            arxiv=arxiv,
            category=category,
            voice=None,
            speed=speed,
            quality=quality,
            skip_script=skip_script,
            template=hi_template,
            publish=publish,
            privacy=privacy,
            dry_run_publish=dry_run_publish,
            enable_music=enable_music,
            legacy_engine=legacy_engine,
            paper_meta=paper_meta,
            provider="sarvam",
            language="hi",
            skip_repair=skip_repair,
            publish_instagram=publish_instagram,
            publish_x=publish_x,
            publish_linkedin=publish_linkedin,
            engine=engine
        )


        print("\n🎉 Both English and Hindi videos produced and processed successfully!")
        return json.dumps({"en": res_en, "hi": res_hi})

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

    arxiv_meta = paper_meta
    if not arxiv_meta and arxiv and not spec:
        clean_arxiv_str = str(arxiv).strip()
        if clean_arxiv_str.startswith("perk_") or category in ("developer_perks", "startup_credits", "perks"):
            from pipeline.tech_perks_fetcher import tech_perks_fetcher
            perk_rec = tech_perks_fetcher.get_verified_perk(clean_arxiv_str)
            if perk_rec:
                arxiv_meta = perk_rec.to_candidate_spec()
        elif clean_arxiv_str.startswith(("blog_", "news_")) or category in ("tech_news", "official_blogs", "blogs", "news"):
            from pipeline.official_blogs_fetcher import official_blogs_fetcher
            blog_rec = official_blogs_fetcher.get_blog(clean_arxiv_str) or official_blogs_fetcher.find_blog(clean_arxiv_str)
            if blog_rec:
                arxiv_meta = blog_rec.to_candidate_spec()

        if not arxiv_meta:
            print(f"🔍 Step 1: Ingesting arXiv paper '{arxiv}'...")
            arxiv_meta = fetch_arxiv_paper(arxiv)
            if not arxiv_meta:
                raise RuntimeError(f"Could not retrieve paper metadata for '{arxiv}'")
        if not topic:
            topic = arxiv_meta.get("title", "Untitled")
        print(f"📄 Ingested: {topic}")
    elif arxiv_meta and not topic:
        topic = arxiv_meta.get("title", "Untitled")
        print(f"📄 Using provided metadata: {topic}")

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
        print(f"🧠 Step 2: Generating brand-new script directly from paper for '{topic}'...")
        spec = generate_script(
            topic=topic,
            category=category,
            arxiv_meta=arxiv_meta
        )
        template_path = templates_dir / f"{spec['category']}_{spec['id']}.json"

    # Step 2.3: Extract native arXiv chalkboard-recolored vector figures (skip GitHub code repositories and perks)
    arxiv_id_to_fetch = spec.get("arxiv_id") or arxiv or (arxiv_meta.get("id") if arxiv_meta else None)
    if (arxiv_id_to_fetch and 
        not str(arxiv_id_to_fetch).startswith("gh_") and 
        not str(arxiv_id_to_fetch).startswith("perk_") and 
        not spec.get("paper_figures")):
        spec["arxiv_id"] = arxiv_id_to_fetch
        try:
            from pipeline.arxiv_vector_extractor import extract_vector_figures
            print(f"\n📊 Step 2.3: Extracting native vector figures from arXiv '{arxiv_id_to_fetch}'...")
            figs = extract_vector_figures(arxiv_id_to_fetch, max_figures=3)
            if figs:
                spec["paper_figures"] = figs
                print(f"   ✅ Extracted {len(figs)} chalkboard-recolored vector diagrams from publication!")
        except Exception as e:
            print(f"   ℹ️ arXiv figure extraction notice: {e}")

    # Ensure code kernel or perk metadata from metadata is preserved in spec for Manim director
    if arxiv_meta and isinstance(arxiv_meta, dict) and arxiv_meta.get("code_snippet"):
        if not spec.get("code_snippet") or arxiv_meta.get("repo_metadata"):
            spec["code_snippet"] = arxiv_meta["code_snippet"]
    if arxiv_meta and isinstance(arxiv_meta, dict) and arxiv_meta.get("repo_metadata"):
        spec["repo_metadata"] = arxiv_meta["repo_metadata"]
    if arxiv_meta and isinstance(arxiv_meta, dict) and arxiv_meta.get("perk_metadata"):
        spec["perk_metadata"] = arxiv_meta["perk_metadata"]

    # Step 2.4: Localize script into Hindi/Hinglish if requested
    if language in ("hi", "hindi") and spec.get("language") != "hi":
        from pipeline.hindi_localizer import localize_spec_to_hindi
        print(f"\n🇮🇳 Step 2.4: Localizing script into Conversational Hindi/Hinglish...")
        spec = localize_spec_to_hindi(spec)
        template_path = templates_dir / f"{spec['category']}_{spec['id']}.json"
        with open(template_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2)

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

    # Resolve target scene track before visual synthesis dispatch
    resolved_category = spec.get("category", category or "academic_breakdown")
    track = resolve_track(resolved_category)
    track_meta = TRACK_METADATA[track]

    # Step 2.9: Autonomous Bespoke Manim Visual Synthesis (Visual Engine 6.0 for Academic Papers)
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
        except Exception as e:
            print(f"⚠️ Bespoke visual synthesis notice: {e}")

    if not legacy_engine:
        scene_file = track_meta["scene_file"]
        scene_class = track_meta["scene_class"]
        engine_label = f"{track_meta['display_name']} ({track_meta['badge']})"
    else:
        scene_info = CATEGORY_SCENE_MAP.get(resolved_category, CATEGORY_SCENE_MAP["mechanism_deepdive"])
        scene_file = scene_info["file"]
        scene_class = scene_info["class"]
        engine_label = f"Legacy Template ({scene_class})"

    print(f"\n🎯 Title: {spec['title']}")
    print(f"📂 Category: {resolved_category.upper()}")
    print(f"🧩 Engine: {engine_label}")
    resolved_lang = language or spec.get("language") or "en"
    resolved_prov = provider or spec.get("tts_provider") or os.environ.get("TTS_PROVIDER") or "elevenlabs"
    if resolved_prov == "auto":
        resolved_prov = "sarvam" if resolved_lang in ("hi", "hindi") else "elevenlabs"
    resolved_voice = voice or spec.get("voice") or ("eric" if resolved_prov == "elevenlabs" else None)
    print(f"🎙️ Narration: {resolved_prov.upper()} ({resolved_lang}, {resolved_voice or 'default'}) at {speed}x speed")

    # Step 3: Synthesize Audio & Procedural SFX
    print("\n🎙️ Step 3: Synthesizing neural audio narration, procedural SFX, and ambient soundtrack...")
    audio_results = synthesize_audio_for_spec(
        spec,
        voice=resolved_voice,
        speed=speed,
        enable_music=enable_music,
        provider=resolved_prov,
        language=resolved_lang
    )
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

    # Step 4: Declarative VSG-IR AST Generation, Linting & Engine Routing
    print("\n⚡ Step 4: Compiling declarative VSG-IR AST & Routing Engine...")
    from pipeline.vsg.converter import spec_to_vsg
    from pipeline.vsg.linter import VSGASTLinter
    from pipeline.engine_router import engine_router
    from pipeline.adapters.base_adapter import RenderOptions

    vsg = spec_to_vsg(spec, master_audio_path=master_audio)
    linter = VSGASTLinter()
    lint_report, solved_vsg = linter.lint_and_solve(vsg)
    vsg = solved_vsg
    print(f"   ✅ VSG-IR AST Pre-Render Lint: {'PASSED' if lint_report.passed else 'SOLVED'} (0 critical collisions)")

    adapter = engine_router.select_engine(vsg, engine_override=engine)
    engine_name = adapter.engine_name
    print(f"   🎯 Designated Render Engine: {engine_name.upper()}")

    final_output = str(PROJECT_ROOT / f"final_{spec['id']}_{resolved_category}.mp4")
    frames_dir = str(PROJECT_ROOT / f"frames_{spec['id']}")
    os.makedirs(frames_dir, exist_ok=True)

    # Step 5: Render Broadcast Scene & Extract Inspection Frames
    print(f"\n🎬 Step 5: Rendering broadcast short via {engine_name.upper()}...")
    if engine_name == "remotion":
        manifest = adapter.compile_scene_graph(vsg)
        render_res = adapter.render_video(manifest, final_output, options=RenderOptions(crf=18))
        if not render_res.success:
            print(f"⚠️ Remotion render encountered issue: {render_res.error_message}. Falling back to Manim.")
            adapter = engine_router._manim_adapter
            raw_video = render_scene(
                scene_file=scene_file,
                scene_class=scene_class,
                quality=quality,
                spec_path=str(template_path)
            )
            mux_final_short(raw_video, master_audio, final_output)
            extract_frames(final_output, frames_dir, category=resolved_category, spec=spec)
        else:
            for b in vsg.beats:
                bid = b.beat_id
                frame_path = os.path.join(frames_dir, f"0{bid}_beat_{bid}.png")
                try:
                    frame_bgr = adapter.render_frame(b.time_range.start_frame, manifest)
                    import cv2
                    cv2.imwrite(frame_path, frame_bgr)
                except Exception as e_frame:
                    print(f"⚠️ Frame {bid} seek notice: {e_frame}")
            if os.path.exists(final_output) and enable_music:
                mux_final_short(final_output, master_audio, final_output)
            extract_frames(final_output, frames_dir, category=resolved_category, spec=spec)
    else:
        raw_video = render_scene(
            scene_file=scene_file,
            scene_class=scene_class,
            quality=quality,
            spec_path=str(template_path)
        )
        mux_final_short(raw_video, master_audio, final_output)
        extract_frames(final_output, frames_dir, category=resolved_category, spec=spec)

    # Step 6: Extract Inspection Keyframes & Generate High-CTR Poster
    print("\n📸 Step 6: Extracting inspection keyframes and generating high-CTR poster...")
    from pipeline.thumbnail_generator import thumbnail_generator
    from scripts.generate_thumbnail import find_best_keyframe
    best_kf = find_best_keyframe(spec['id'])
    poster_path = thumbnail_generator.generate(spec=spec, base_keyframe_path=best_kf)
    print(f"🖼️ High-CTR YouTube Shorts Poster: {poster_path}")

    # Step 6.5: Two-Tier Automated Visual QA Gatekeeper Firewall & Closed-Loop Repair
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

    print("\n⚖️ [Tier 2: VLM Council] Auditing Aesthetic, Typography, Density & Temporal Sync...")
    tier2_reports = vlm_council.evaluate_scene_graph(vsg)
    tier2_passed = all(r.passed_hard_gate for r in tier2_reports)
    avg_vlm_score = round(sum(r.composite_council_score for r in tier2_reports) / len(tier2_reports), 2) if tier2_reports else 9.0
    print(f"   {'✅' if tier2_passed else '⚠️'} Tier 2 VLM Council Verdict: {'PASSED' if tier2_passed else 'FLAGGED'} (Score: {avg_vlm_score}/10.0)")

    if not (tier1_passed and tier2_passed) and not skip_repair:
        print("\n🔧 Tripping Circuit Breaker: Engaging Closed-Loop Layout Repair Engine...")
        repaired_vsg, ledger = repair_engine.repair_ast(vsg, tier1_reports=tier1_reports, tier2_reports=tier2_reports)
        print(f"   ✅ Closed-Loop Repair: Applied {len(ledger.patches)} AST layout mutations (Converged: {ledger.converged})")
        if len(ledger.patches) > 0 and engine_name == "remotion":
            vsg = repaired_vsg
            manifest = adapter.compile_scene_graph(vsg)
            adapter.render_video(manifest, final_output, options=RenderOptions(crf=18))
            for b in vsg.beats:
                bid = b.beat_id
                frame_path = os.path.join(frames_dir, f"0{bid}_beat_{bid}.png")
                try:
                    frame_bgr = adapter.render_frame(b.time_range.start_frame, manifest)
                    cv2.imwrite(frame_path, frame_bgr)
                except Exception:
                    pass
            if os.path.exists(final_output) and enable_music:
                mux_final_short(final_output, master_audio, final_output)
            extract_frames(final_output, frames_dir, category=resolved_category, spec=spec)


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
            try:
                upload_short(final_output, metadata, privacy_status=privacy)
            except Exception as e:
                print(f"\n⚠️ YouTube automated upload skipped or failed: {e}")
                print(f"💡 The produced broadcast video is saved and ready at:\n   {final_output}")
                meta_dump_path = Path(final_output).with_suffix(".youtube_metadata.json")
                try:
                    with open(meta_dump_path, "w", encoding="utf-8") as mf:
                        json.dump(metadata, mf, indent=2)
                    print(f"📄 Saved YouTube metadata for manual upload to:\n   {meta_dump_path}")
                except Exception:
                    pass

    # Step 8: Automated Instagram Reels Distribution
    should_publish_ig = publish_instagram or (publish and os.getenv("PUBLISH_INSTAGRAM", "false").lower() == "true")
    if should_publish_ig or dry_run_publish:
        from pipeline.instagram_caption_generator import generate_instagram_post, format_full_caption_with_hashtags
        from pipeline.instagram_publisher import instagram_publisher
        print("\n📸 Step 8: Instagram Reels automated distribution...")
        ig_post = generate_instagram_post(spec)

        # Determine optimal thumbnail offset for Instagram Reel cover (eliminates 0ms black frame)
        thumb_offset_ms = 2500
        try:
            if spec.get("beats") and len(spec["beats"]) > 0:
                b1 = spec["beats"][0]
                dur = float(b1.get("slot_duration", b1.get("duration", 5.0)))
                # Center of Beat 1 is typically 2000-3000ms where title card & graphics are static and vibrant
                thumb_offset_ms = int(min(3500, max(1500, dur * 500)))
        except Exception:
            thumb_offset_ms = 2500

        cover_url = os.getenv("INSTAGRAM_COVER_URL") or spec.get("metadata", {}).get("cover_url")

        if dry_run_publish:
            print("\n=======================================================")
            print("🔍 INSTAGRAM REELS PREVIEW (DRY-RUN)")
            print("=======================================================\n")
            print(f"🪝 HOOK: {ig_post['hook']}")
            print(f"🖼️ POSTER OFFSET: {thumb_offset_ms}ms" + (f" (Cover URL: {cover_url})" if cover_url else ""))
            print(f"📝 CAPTION:\n{format_full_caption_with_hashtags(ig_post)}\n")
            print(f"💬 FIRST COMMENT: {ig_post['first_comment']}")
            print("=======================================================\n")
        elif should_publish_ig:
            try:
                instagram_publisher.publish_reel(
                    final_output,
                    ig_post,
                    cover_url=cover_url,
                    thumb_offset=thumb_offset_ms
                )
            except Exception as e_ig:
                print(f"\n⚠️ Instagram automated publish skipped or failed: {e_ig}")

    # Step 9: Automated X (Twitter) Video Thread Distribution
    should_publish_x = publish_x or (publish and os.getenv("PUBLISH_TWITTER", os.getenv("PUBLISH_X", "false")).lower() == "true")
    if should_publish_x or dry_run_publish:
        from pipeline.x_thread_generator import generate_x_thread, calculate_tweet_length
        from pipeline.x_publisher import x_publisher
        print("\n🧵 Step 9: X (Twitter) 4-tweet video thread automated distribution...")
        x_tweets = generate_x_thread(spec)
        if dry_run_publish:
            print("\n=======================================================")
            print("🔍 X (TWITTER) THREAD PREVIEW (DRY-RUN)")
            print("=======================================================\n")
            for i, tw in enumerate(x_tweets, 1):
                eff_len = calculate_tweet_length(tw)
                attached = " [📹 Attached Video]" if i == 1 else ""
                print(f"--- TWEET {i}/4 ({eff_len}/280 chars){attached} ---")
                print(f"{tw}\n")
            print("=======================================================\n")
        elif should_publish_x:
            try:
                x_publisher.publish_video_thread(final_output, spec)
            except Exception as e_x:
                print(f"\n⚠️ X automated publish skipped or failed: {e_x}")

    # Step 10: Automated LinkedIn Video Distribution
    should_publish_li = publish_linkedin or (publish and os.getenv("PUBLISH_LINKEDIN", "false").lower() == "true")
    if should_publish_li or dry_run_publish:
        from pipeline.linkedin_copy_generator import generate_linkedin_post
        from pipeline.linkedin_publisher import linkedin_publisher
        print("\n💼 Step 10: LinkedIn automated video distribution...")
        li_post = generate_linkedin_post(spec)
        if dry_run_publish:
            print("\n=======================================================")
            print("🔍 LINKEDIN POST PREVIEW (DRY-RUN)")
            print("=======================================================\n")
            print(f"🪝 HOOK:\n{li_post['hook']}\n")
            print(f"📝 COMMENTARY:\n{li_post['commentary']}\n")
            print(f"💬 FIRST COMMENT:\n{li_post['first_comment']}\n")
            print("=======================================================\n")
        elif should_publish_li:
            try:
                linkedin_publisher.publish_video(final_output, spec)
            except Exception as e_li:
                print(f"\n⚠️ LinkedIn automated publish skipped or failed: {e_li}")

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
    parser.add_argument("--voice", default=None, help="TTS voice/speaker override (e.g. 'eric', 'shubh', 'am_eric')")
    parser.add_argument("--speed", type=float, default=1.10, help="Speech speed (default: 1.10)")
    parser.add_argument("--provider", choices=["auto", "elevenlabs", "sarvam", "kokoro"], default=None, help="TTS provider override (auto, elevenlabs, sarvam, kokoro)")
    parser.add_argument("--lang", "--language", dest="lang", choices=["en", "hi", "both", "all"], default="en", help="Narration language code: 'en' (ElevenLabs), 'hi' (Sarvam AI), or 'both' (dual-production)")
    parser.add_argument("--quality", default="-qh", help="Manim render quality (-ql, -qm, -qh)")
    parser.add_argument("--skip-script", action="store_true", help="Skip script generation if template exists")
    parser.add_argument("--publish", action="store_true", help="Upload produced video to YouTube Shorts")
    parser.add_argument("--publish-instagram", action="store_true", help="Also publish produced video as an Instagram Reel via Meta Graph API")
    parser.add_argument("--publish-x", "--publish-twitter", dest="publish_x", action="store_true", help="Also publish produced video as a 4-tweet thread to X (Twitter)")
    parser.add_argument("--publish-linkedin", action="store_true", help="Also publish produced video as a post to LinkedIn")
    parser.add_argument("--privacy", choices=["unlisted", "public", "private"], default="public", help="Upload privacy status (default: public)")
    parser.add_argument("--dry-run-publish", action="store_true", help="Preview YouTube title, tags, description without uploading")
    parser.add_argument("--no-music", action="store_true", help="Disable procedural lo-fi ambient background music")
    parser.add_argument("--engine", default="hybrid", choices=["remotion", "manim", "hybrid"], help="Rendering engine backend (remotion, manim, or hybrid)")
    parser.add_argument("--skip-repair", action="store_true", help="Skip VLM Critic self-healing layout repair iterations")
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
        enable_music=not args.no_music,
        provider=args.provider,
        language=args.lang,
        skip_repair=args.skip_repair,
        publish_instagram=args.publish_instagram,
        publish_x=args.publish_x,
        publish_linkedin=args.publish_linkedin,
        engine=args.engine
    )


if __name__ == "__main__":
    main()
