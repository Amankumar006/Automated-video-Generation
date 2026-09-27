#!/usr/bin/env python3
"""
The Model Verse — Broadcast-Grade Automated Short Video Generator
Style: Minimalist Clean Tech (Fireship / Dieter Rams Aesthetic)
Integrates:
  - High-Retention Technical Scripting
  - Kokoro-82M Neural Speech (am_adam)
  - Procedural SFX Audio Engine (Sub-bass pulses, whooshes, clicks, laser routing)
  - 1080x1920 Manim Vector Animation with MovingCameraScene
  - Frame extraction & verification
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

FFMPEG_BIN = "/Users/amankumar/bin/ffmpeg"
KOKORO_MODEL = "kokoro_models/kokoro-v1.0.onnx"
KOKORO_VOICES = "kokoro_models/voices-v1.0.bin"

# Architectural Specs & Structured Scripts
MODEL_SPECS = {
    "deepseek-v3": {
        "title": "DeepSeek-V3",
        "scene_file": "scripts/render_deepseek_clean_tech.py",
        "scene_class": "DeepSeekV3CleanTech",
        "video_raw": "media/videos/render_deepseek_clean_tech/1920p30/DeepSeekV3CleanTech.mp4",
        "sentences": [
            "DeepSeek-V3 has 671 billion parameters. But running it costs almost nothing. How?",
            "In a standard dense model, every single word forces all 671 billion weights to calculate at once. A massive brute-force bottleneck.",
            "DeepSeek flips this with Sparse Mixture of Experts, dividing the entire model into 256 specialized sub-networks.",
            "Plus one permanently active shared expert that never sleeps, capturing universal knowledge.",
            "When a token enters, a high-speed router scores affinity, dispatching to only the top 8 experts.",
            "The result? 671 billion parameters of intelligence, but only 37 billion active per token. 94 percent of compute, saved.",
            "Follow The Model Verse for more deep architecture breakdowns like this."
        ],
        "sfx_cues": [
            (0.8, "sub_impact", 0.45),
            (5.9, "whoosh", 0.35),
            (7.5, "sub_impact", 0.40),
            (14.8, "whoosh", 0.35),
            (15.5, "click", 0.30),
            (22.5, "chime", 0.35),
            (27.8, "whoosh", 0.35),
            (28.8, "click", 0.35),
            (29.8, "laser_dispatch", 0.45),
            (33.8, "sub_impact", 0.50),
            (42.8, "whoosh", 0.35),
            (43.6, "click", 0.40),
            (44.3, "chime", 0.40),
        ]
    }
}

def generate_voice_and_sfx(spec, voice="am_adam", speed=1.12):
    """Synthesizes speech via Kokoro and mixes procedural SFX cues."""
    from kokoro_onnx import Kokoro
    import soundfile as sf
    import numpy as np
    from scripts.sfx_generator import (
        create_whoosh, create_click, create_laser_dispatch,
        create_sub_impact, create_chime, SAMPLE_RATE
    )

    os.makedirs("public", exist_ok=True)
    narration_out = f"public/{spec['title'].lower()}_narration.wav"
    master_out = f"public/{spec['title'].lower()}_master_audio.wav"

    print(f"🎙️ Generating neural narration with Kokoro (Voice: {voice}, Speed: {speed})...")
    kokoro = Kokoro(KOKORO_MODEL, KOKORO_VOICES)
    sr = SAMPLE_RATE
    all_audio = []
    current_time = 0.0

    for i, sent in enumerate(spec["sentences"]):
        samples, _ = kokoro.create(sent, voice=voice, speed=speed, lang="en-us")
        dur = len(samples) / sr
        print(f"   Beat {i+1} [{current_time:.2f}s -> {current_time+dur:.2f}s]: \"{sent[:42]}...\"")
        all_audio.append(samples)
        pause = np.zeros(int(0.28 * sr), dtype=np.float32)
        all_audio.append(pause)
        current_time += dur + 0.28

    narration_audio = np.concatenate(all_audio)
    total_len = len(narration_audio)
    print(f"   Total narration duration: {total_len / sr:.2f}s")

    # Procedural SFX Mapping
    sfx_builders = {
        "whoosh": create_whoosh,
        "click": create_click,
        "laser_dispatch": create_laser_dispatch,
        "sub_impact": create_sub_impact,
        "chime": create_chime
    }

    sfx_track = np.zeros(total_len, dtype=np.float32)
    for ts, sfx_name, vol in spec["sfx_cues"]:
        if sfx_name in sfx_builders:
            sfx_data = sfx_builders[sfx_name]()
            start_idx = int(ts * sr)
            end_idx = min(start_idx + len(sfx_data), total_len)
            available = end_idx - start_idx
            if available > 0:
                sfx_track[start_idx:end_idx] += sfx_data[:available] * vol

    # Master mix: 95% narration + 75% SFX track
    master = narration_audio * 0.95 + sfx_track * 0.75
    peak = np.max(np.abs(master))
    if peak > 0.96:
        master = master * (0.96 / peak)

    sf.write(master_out, master.astype(np.float32), sr)
    print(f"✅ Master audio with integrated SFX saved to: {master_out}")
    return master_out

def render_manim(scene_file, scene_class):
    """Renders the scene with Manim Community."""
    env = os.environ.copy()
    env["PATH"] = f"/Users/amankumar/bin:{env.get('PATH', '')}"
    cmd = [
        sys.executable, "-m", "manim",
        "-qm",
        scene_file,
        scene_class
    ]
    print(f"🎬 Rendering Manim scene {scene_class} from {scene_file}...")
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if res.returncode != 0:
        print("Manim Error:\n", res.stderr)
        raise RuntimeError("Manim render failed.")
    print("✅ Manim scene rendered successfully.")

def mux_final_video(video_path, audio_path, output_path):
    """Muxes visual video and master audio with FFmpeg."""
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
    print(f"🚀 Muxing final vertical short into: {output_path}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg Error:\n", res.stderr)
        raise RuntimeError("FFmpeg muxing failed.")
    print(f"🎉 Final broadcast short ready at: {output_path}")

def extract_preview_frames(video_path, output_dir="frames_cleantech"):
    """Extracts key inspection frames across the timeline."""
    os.makedirs(output_dir, exist_ok=True)
    timestamps = [
        ("00:00:03.000", "01_hook_671b.png"),
        ("00:00:10.000", "02_dense_overload.png"),
        ("00:00:18.000", "03_moe_256_constellation.png"),
        ("00:00:25.000", "04_shared_expert.png"),
        ("00:00:31.000", "05_router_laser_dispatch.png"),
        ("00:00:38.000", "06_active_37b_payoff.png"),
        ("00:00:44.500", "07_clean_outro_cta.png"),
    ]
    for ts, fname in timestamps:
        out_f = os.path.join(output_dir, fname)
        subprocess.run([
            FFMPEG_BIN, "-y", "-ss", ts, "-i", video_path,
            "-vframes", "1", "-q:v", "2", out_f
        ], capture_output=True)
    print(f"📸 Extracted {len(timestamps)} inspection frames to {output_dir}/")

def main():
    parser = argparse.ArgumentParser(description="The Model Verse Shorts Engine")
    parser.add_argument("--model", choices=list(MODEL_SPECS.keys()), default="deepseek-v3")
    parser.add_argument("--voice", default="am_adam")
    parser.add_argument("--output", default="final_deepseek_v3_cleantech_short.mp4")
    parser.add_argument("--skip-render", action="store_true", help="Skip Manim render if already rendered")
    args = parser.parse_args()

    spec = MODEL_SPECS[args.model]
    print(f"\n=======================================================")
    print(f"⚡ THE MODEL VERSE — CLEAN TECH SHORTS ENGINE")
    print(f"🎯 Target Architecture: {spec['title']}")
    print(f"🎨 Aesthetic: Minimalist Clean Tech (Fireship Style)")
    print(f"🎙️ Voice: Kokoro-82M ({args.voice}) + Procedural SFX")
    print(f"=======================================================\n")

    # Step 1: Voice & SFX
    master_audio = generate_voice_and_sfx(spec, voice=args.voice)

    # Step 2: Manim Render
    if not args.skip_render:
        render_manim(spec["scene_file"], spec["scene_class"])

    # Step 3: Mux
    mux_final_video(spec["video_raw"], master_audio, args.output)

    # Step 4: Extract Frames
    extract_preview_frames(args.output)

if __name__ == "__main__":
    main()
