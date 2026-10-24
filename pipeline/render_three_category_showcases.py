"""
The Model Verse — Three Category Full Audio & Video Showcase Renderer
Renders full broadcast-grade audio + video results across all 3 tracks:
  1. Track 1: Academic Architecture Deep Dive (DeepSeek-V3 MoE)
  2. Track 2: Official Tech News & Drops (OpenAI o3-mini Reasoning Release)
  3. Track 3: Developer Perks & Startup Credits (Anthropic Claude $31K Stack)

Each category executes:
  - Neural TTS synthesis with Kokoro ONNX offline voice + Lo-Fi ambient soundtrack + SFX ducking
  - Millisecond acoustic forced alignment for kinetic subtitles
  - Synchronized VSG-IR declarative AST assembly
  - Remotion broadcast rendering (1080x1920 @ 60fps)
  - Master FFmpeg muxing into high-bitrate MP4 with synchronized AAC audio
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.audio_synthesizer import synthesize_audio_for_spec
from pipeline.adapters.remotion_adapter import RemotionBroadcastAdapter

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
logger = logging.getLogger("ThreeCategoryShowcases")


CATEGORY_SPECS = [
    {
        "id": "category_1_architecture",
        "title": "DeepSeek-V3 MoE Architecture Breakdown",
        "domain_taxonomy": "FRONTIER_AI_ARCHITECTURES",
        "theme_id": "cyber_cyan",
        "beats_script": [
            {
                "beat_id": 1,
                "text": "DeepSeek V3 routes eight routed experts dynamically per token.",
                "intent": "Introduce sparse mixture-of-experts routing",
                "visual_node": {
                    "id": "moe_matrix_node",
                    "node_type": "MoERouterMatrix",
                    "props": {
                        "tokenText": "deepseek_r1",
                        "totalExperts": 256,
                        "activeRouted": 8,
                        "sharedExperts": 1
                    },
                    "bounds": {"x_min_px": 140, "y_min_px": 500, "width_px": 760, "height_px": 650}
                }
            },
            {
                "beat_id": 2,
                "text": "Multi-Head Attention compresses query key states without memory overhead.",
                "intent": "Explain multi-head latent attention mechanism",
                "visual_node": {
                    "id": "attn_map_node",
                    "node_type": "AttentionHeatmap",
                    "props": {
                        "matrixDim": 5,
                        "highlightHead": 1,
                        "activeLatentDim": 512
                    },
                    "bounds": {"x_min_px": 140, "y_min_px": 500, "width_px": 760, "height_px": 580}
                }
            },
            {
                "beat_id": 3,
                "text": "DeepSeek matches frontier models on benchmarks at a fraction of the compute cost.",
                "intent": "Empirical benchmark showdown payoff",
                "visual_node": {
                    "id": "race_bars_node",
                    "node_type": "HorizontalRaceBars",
                    "props": {
                        "title": "MMLU-Pro Accuracy Showdown",
                        "contestants": [
                            {"name": "DeepSeek-V3", "score": 88.5, "color": "#38BDF8", "isHero": True, "tag": "SOTA"},
                            {"name": "Claude 3.5 Sonnet", "score": 85.1, "color": "#64748B", "isHero": False},
                            {"name": "GPT-4o (0513)", "score": 84.8, "color": "#475569", "isHero": False}
                        ],
                        "maxScore": 100.0
                    },
                    "bounds": {"x_min_px": 140, "y_min_px": 500, "width_px": 760, "height_px": 540}
                }
            }
        ]
    },
    {
        "id": "category_2_news",
        "title": "OpenAI Releases o3-mini Globally",
        "domain_taxonomy": "OFFICIAL_TECH_NEWS",
        "theme_id": "cyber_cyan",
        "beats_script": [
            {
                "beat_id": 1,
                "text": "OpenAI just dropped o3-mini globally with high reasoning effort.",
                "intent": "Official lab drop breaking news",
                "visual_node": {
                    "id": "news_banner_node",
                    "node_type": "NewsAnnouncementBanner",
                    "props": {
                        "title": "o3-mini Released Globally with High Reasoning Effort",
                        "labName": "OpenAI Newsroom",
                        "badgeText": "03-MINI",
                        "metric1Label": "Math & Code",
                        "metric1Val": "88.2%",
                        "metric1Delta": "+7.4% vs o1-mini",
                        "metric2Label": "Token Pricing",
                        "metric2Val": "$1.10",
                        "metric2Delta": "-63% Cost Cut",
                        "metric3Label": "Inference Latency",
                        "metric3Val": "3.2s",
                        "metric3Delta": "2.8x Faster",
                        "metric4Label": "Context Window",
                        "metric4Val": "200K",
                        "metric4Delta": "Full Multimodal",
                        "sourceUrl": "openai.com/index/openai-o3-mini"
                    },
                    "bounds": {"x_min_px": 140, "y_min_px": 500, "width_px": 760, "height_px": 480}
                }
            },
            {
                "beat_id": 2,
                "text": "It crushes competitive coding and math benchmarks with eighty-eight percent accuracy.",
                "intent": "Competitive benchmark showdown",
                "visual_node": {
                    "id": "race_bars_news_node",
                    "node_type": "HorizontalRaceBars",
                    "props": {
                        "title": "STEM & Coding Reasoning Benchmark",
                        "contestants": [
                            {"name": "o3-mini (High)", "score": 88.2, "color": "#10B981", "isHero": True, "tag": "SOTA"},
                            {"name": "o1-mini", "score": 80.8, "color": "#64748B", "isHero": False},
                            {"name": "Claude 3.5 Sonnet", "score": 78.4, "color": "#475569", "isHero": False}
                        ],
                        "maxScore": 100.0
                    },
                    "bounds": {"x_min_px": 140, "y_min_px": 500, "width_px": 760, "height_px": 540}
                }
            },
            {
                "beat_id": 3,
                "text": "And token pricing drops sixty-three percent, cutting inference costs for production AI.",
                "intent": "Inference pricing disruption analysis",
                "visual_node": {
                    "id": "pricing_delta_node",
                    "node_type": "PricingDeltaComparison",
                    "props": {
                        "title": "API Inference Cost Disruption",
                        "subtitle": "OpenAI Reasoning Models Economics",
                        "oldTierName": "Legacy o1-mini",
                        "oldPrice": "$3.00 / 1M",
                        "oldLatency": "7.8s Latency",
                        "newTierName": "o3-mini (Standard)",
                        "newPrice": "$1.10 / 1M",
                        "newLatency": "3.2s Latency",
                        "savingsPercentage": "63.3% CHEAPER",
                        "efficiencyMultiplier": "2.4x FASTER"
                    },
                    "bounds": {"x_min_px": 140, "y_min_px": 500, "width_px": 760, "height_px": 440}
                }
            }
        ]
    },
    {
        "id": "category_3_perks",
        "title": "Claim $31,000 in Free AI Credits",
        "domain_taxonomy": "STARTUP_PERKS_AND_GRANTS",
        "theme_id": "cyber_cyan",
        "beats_script": [
            {
                "beat_id": 1,
                "text": "Anthropic is giving one thousand dollars in free API credits to early stage startups.",
                "intent": "Actionable startup credits walkthrough",
                "visual_node": {
                    "id": "perk_portal_node",
                    "node_type": "PerkPortalWindow",
                    "props": {
                        "urlPath": "anthropic.com/startups",
                        "partnerName": "Claude Startups Accelerator",
                        "benefitAmount": "$1,000 FREE CREDITS",
                        "eligibilitySteps": [
                            "Raised under $5M in funding",
                            "Valid company domain & work email",
                            "Building production AI application"
                        ],
                        "ctaLabel": "CLAIM CREDITS NOW →"
                    },
                    "bounds": {"x_min_px": 140, "y_min_px": 500, "width_px": 760, "height_px": 520}
                }
            },
            {
                "beat_id": 2,
                "text": "You can stack this with twenty-five thousand from AWS Activate and GitHub Copilot.",
                "intent": "Ecosystem grant stack matrix",
                "visual_node": {
                    "id": "partner_app_grid_node",
                    "node_type": "PartnerAppGrid",
                    "props": {
                        "title": "Active Founder Grant Matrix",
                        "subtitle": "Stackable founder tiers verified today",
                        "partners": [
                            {"name": "Anthropic Claude", "perk": "$1,000", "type": "API Credits", "status": "APPROVED", "color": "#38BDF8"},
                            {"name": "AWS Activate", "perk": "$25,000", "type": "Compute Tier", "status": "APPROVED", "color": "#F59E0B"},
                            {"name": "Stripe Atlas", "perk": "$5,000", "type": "Waived Fees", "status": "APPROVED", "color": "#A855F7"},
                            {"name": "GitHub Copilot", "perk": "1-Yr Free", "type": "Developer Seats", "status": "APPROVED", "color": "#10B981"}
                        ],
                        "totalValue": "$31,000+ Available Value"
                    },
                    "bounds": {"x_min_px": 140, "y_min_px": 500, "width_px": 760, "height_px": 460}
                }
            },
            {
                "beat_id": 3,
                "text": "Apply with your company domain to claim over thirty-one thousand dollars today.",
                "intent": "Bootstrap vs subsidized cost delta",
                "visual_node": {
                    "id": "perks_pricing_delta_node",
                    "node_type": "PricingDeltaComparison",
                    "props": {
                        "title": "Startup Runway Capital Leverage",
                        "subtitle": "Bootstrapped out-of-pocket vs grant acceleration",
                        "oldTierName": "Out-of-Pocket Compute",
                        "oldPrice": "$31,000 Cash",
                        "oldLatency": "Zero Subsidy",
                        "newTierName": "Accelerated Stack",
                        "newPrice": "$0 Subsidized",
                        "newLatency": "100% Covered",
                        "savingsPercentage": "100% SUBSIDIZED",
                        "efficiencyMultiplier": "$31K VALUE"
                    },
                    "bounds": {"x_min_px": 140, "y_min_px": 500, "width_px": 760, "height_px": 440}
                }
            }
        ]
    }
]


def render_category(category_config: dict) -> Path:
    cat_id = category_config["id"]
    logger.info(f"\n=======================================================")
    logger.info(f"🚀 PRODUCING CATEGORY: {category_config['title']} ({cat_id})")
    logger.info(f"=======================================================")

    # 1. Synthesize audio
    spec_input = {
        "spec_id": cat_id,
        "beats": [
            {"beat_id": b["beat_id"], "text": b["text"]}
            for b in category_config["beats_script"]
        ]
    }
    audio_res = synthesize_audio_for_spec(
        spec_input,
        voice="am_adam",
        speed=1.05,
        enable_music=True
    )
    master_audio_path = audio_res["master_audio"]
    total_duration = audio_res["total_duration"]
    timing_data = audio_res["timing_data"]
    logger.info(f"✅ Audio generated: {master_audio_path} ({total_duration:.2f}s)")

    # 2. Assemble VSG-IR Manifest matching exact audio timestamps
    fps = 60
    total_frames = int(round(total_duration * fps))

    vsg_beats = []
    for beat_cfg, time_info in zip(category_config["beats_script"], timing_data):
        b_id = beat_cfg["beat_id"]
        start_sec = time_info["start"]
        end_sec = time_info["end"]
        start_frame = int(round(start_sec * fps))
        end_frame = int(round((start_sec + time_info["slot_duration"]) * fps))
        if b_id == len(timing_data):
            end_frame = max(end_frame, total_frames)

        # Convert acoustic word timings to kinetic subtitle anchors
        acoustic_anchors = []
        for wt in time_info.get("word_timings", []):
            clean_word = wt.get("clean_word") or wt.get("word", "")
            word_str = clean_word.upper().strip(".,!?:;")
            if not word_str:
                continue
            w_start = wt.get("start", start_sec)
            acoustic_anchors.append({
                "word": word_str,
                "timestamp_sec": round(w_start, 3),
                "frame_trigger": int(round(w_start * fps))
            })

        v_node = beat_cfg["visual_node"]
        v_node_copy = json.loads(json.dumps(v_node))
        v_node_copy["motion_track"] = {
            "enter": {
                "type": "SPRING_DAMPED",
                "start_frame": start_frame,
                "duration_frames": 24
            }
        }

        vsg_beats.append({
            "beat_id": b_id,
            "time_range": {
                "start_sec": round(start_sec, 3),
                "end_sec": round(end_sec, 3),
                "start_frame": start_frame,
                "end_frame": end_frame
            },
            "narrative": {
                "spoken_text": beat_cfg["text"],
                "intent": beat_cfg["intent"],
                "visual_metaphor": v_node["node_type"],
                "primary_focus_node_id": v_node["id"]
            },
            "acoustic_anchors": acoustic_anchors,
            "layout_containers": [
                {
                    "container_id": f"stage_b{b_id}",
                    "band": "BAND_3_STAGE",
                    "bounds": v_node["bounds"],
                    "nodes": [v_node_copy]
                }
            ]
        })

    vsg_manifest = {
        "version": "1.0.0",
        "metadata": {
            "project_id": cat_id,
            "title": category_config["title"],
            "domain_taxonomy": category_config["domain_taxonomy"],
            "aspect_ratio": "9:16",
            "canvas": {
                "width_px": 1080,
                "height_px": 1920,
                "fps": fps,
                "duration_seconds": round(total_duration, 2),
                "total_frames": total_frames
            },
            "audio": {
                "master_voiceover_path": str(master_audio_path),
                "sample_rate_hz": 24000,
                "music_ducking_db": -18.0
            }
        },
        "theme": {
            "theme_id": "cyber_cyan",
            "colors": {
                "canvas_void": "#06080F",
                "surface_recessed": "#0B101D",
                "surface_primary": "rgba(15, 23, 42, 0.85)",
                "surface_elevated": "rgba(30, 41, 59, 0.95)",
                "surface_border": "rgba(255, 255, 255, 0.15)",
                "text_primary": "#F8FAFC",
                "text_secondary": "#94A3B8",
                "text_tertiary": "#64748B",
                "hero_accent": "#38BDF8",
                "secondary_accent": "#10B981",
                "status_gain": "#10B981",
                "status_loss": "#EF4444",
                "status_warning": "#F59E0B"
            },
            "materials": {
                "card_blur_px": 24.0,
                "border_radius_px": 20.0,
                "border_width_px": 1.5,
                "shadow_elevation": "0 24px 48px -12px rgba(0, 0, 0, 0.65)",
                "vignette_intensity": 0.4
            },
            "typography": {
                "font_family_display": "Inter Display",
                "font_family_code": "JetBrains Mono",
                "font_family_math": "KaTeX Main",
                "open_type_features": "cv05=1, cv08=1, zero=1, tnum=1"
            }
        },
        "beats": vsg_beats
    }

    # Save VSG manifest
    vsg_path = PROJECT_ROOT / "data" / f"{cat_id}.vsg.json"
    with open(vsg_path, "w", encoding="utf-8") as f:
        json.dump(vsg_manifest, f, indent=2)
    logger.info(f"✅ Saved VSG-IR manifest: {vsg_path}")

    # 3. Render video track with Remotion
    out_dir = PROJECT_ROOT / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_video_path = out_dir / f"{cat_id}_video_only.mp4"
    final_output_path = out_dir / f"{cat_id}_broadcast.mp4"

    logger.info(f"🎬 Rendering {total_frames} video frames via Remotion...")
    remotion_cmd = [
        "npx", "remotion", "render",
        "BroadcastComposition",
        str(raw_video_path),
        f"--props={str(vsg_path)}",
        f"--frames=0-{total_frames - 1}",
        "--overwrite"
    ]
    render_proc = subprocess.run(remotion_cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    if render_proc.returncode != 0:
        logger.error(f"❌ Remotion render failed:\n{render_proc.stderr}\n{render_proc.stdout}")
        raise RuntimeError(f"Remotion render failed for {cat_id}")
    logger.info(f"✅ Video rendered: {raw_video_path}")

    # 4. Mux master audio and video with FFmpeg
    logger.info(f"🎛️ Muxing master audio and video via FFmpeg...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_video_path),
        "-i", str(master_audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(final_output_path)
    ]
    mux_proc = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if mux_proc.returncode != 0:
        logger.error(f"❌ FFmpeg muxing failed:\n{mux_proc.stderr}")
        raise RuntimeError(f"FFmpeg muxing failed for {cat_id}")

    logger.info(f"🎉 BROADCAST READY: {final_output_path} ({os.path.getsize(final_output_path) / (1024*1024):.2f} MB)")
    return final_output_path


def main():
    logger.info("==================================================================")
    logger.info("THE MODEL VERSE — PRODUCING 3-CATEGORY BROADCAST AUDIO & VIDEO")
    logger.info("==================================================================")
    
    results = {}
    for spec in CATEGORY_SPECS:
        final_mp4 = render_category(spec)
        results[spec["id"]] = str(final_mp4)

    logger.info("\n==================================================================")
    logger.info("ALL 3 CATEGORIES SUCCESSFULLY GENERATED:")
    for cat_id, p in results.items():
        logger.info(f"  • {cat_id}: {p}")
    logger.info("==================================================================")


if __name__ == "__main__":
    main()
