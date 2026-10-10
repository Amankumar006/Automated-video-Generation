"""
The Model Verse — Autonomous YouTube Shorts Publisher CLI
Uploads rendered chalkboard animations directly to YouTube Shorts via YouTube Data API v3.
Features:
  1. OAuth2 credential management with automatic token refresh
  2. Viral, SEO-optimized title, description, chapter timestamps, and tags
  3. Interactive/dry-run modes and privacy status controls (unlisted, public, private)
  4. Auto-posted pinned engagement comment to drive algorithm retention
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import (
    YOUTUBE_CLIENT_SECRETS_PATH,
    YOUTUBE_TOKEN_PATH,
    YOUTUBE_DEFAULT_CATEGORY,
)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube"
]

def get_authenticated_service(
    client_secrets_file: str = YOUTUBE_CLIENT_SECRETS_PATH,
    token_file: str = YOUTUBE_TOKEN_PATH,
    interactive: bool = True
):
    """Authenticates and returns an authorized YouTube API service object."""
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        except Exception as e:
            print(f"⚠️ Warning: Could not load existing token file ({e}). Re-authenticating...")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("🔄 Refreshing expired YouTube OAuth token...")
                creds.refresh(Request())
                with open(token_file, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
            except Exception as e:
                print(f"⚠️ Token refresh failed: {e}. Starting fresh authentication flow...")
                creds = None

        if not creds:
            if not interactive:
                raise RuntimeError("Non-interactive mode: YouTube credentials not available or expired.")

            # Check if running in a headless or CI environment
            is_headless = (
                os.environ.get("CI") == "true" or
                os.environ.get("GITHUB_ACTIONS") == "true" or
                (not os.environ.get("DISPLAY") and sys.platform.startswith("linux"))
            )
            if is_headless:
                raise RuntimeError(
                    f"❌ YouTube OAuth token expired or missing in headless CI environment.\n"
                    f"Cannot open local browser for interactive login on GitHub Actions.\n"
                    f"Please re-authenticate locally and update the YOUTUBE_TOKEN_JSON_BASE64 repository secret:\n"
                    f"  cat pipeline/youtube_token.json | base64 | pbcopy"
                )

            if not os.path.exists(client_secrets_file):
                raise FileNotFoundError(
                    f"❌ YouTube client secrets file not found at: {client_secrets_file}\n\n"
                    f"To enable YouTube uploads:\n"
                    f"  1. Go to Google Cloud Console (https://console.cloud.google.com)\n"
                    f"  2. Enable the 'YouTube Data API v3'\n"
                    f"  3. Create an OAuth 2.0 Client ID (Application type: 'Desktop app')\n"
                    f"  4. Download the JSON and save it as: {client_secrets_file}\n"
                    f"  (Or test metadata generation with --dry-run)"
                )

            print(f"🔐 Starting OAuth 2.0 browser authorization using {client_secrets_file}...")
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            creds = flow.run_local_server(port=8080, prompt="consent")

            # Persist token for future headless runs
            os.makedirs(os.path.dirname(os.path.abspath(token_file)), exist_ok=True)
            with open(token_file, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
            print(f"✅ Credentials saved to {token_file}")

    return build("youtube", "v3", credentials=creds)


def generate_shorts_metadata(spec: Dict[str, Any], video_path: str) -> Dict[str, Any]:
    """Generates viral, SEO-optimized title, description, tags, and pinned comment from spec."""
    title_raw = spec.get("title", "AI Architecture Deep Dive")
    category = spec.get("category", "mechanism_deepdive")
    meta = spec.get("metadata", {})
    arxiv_id = spec.get("id", "").replace("arxiv_", "")

    if "tv static" in title_raw.lower() or "creates images" in title_raw.lower() or "diffusion" in title_raw.lower():
        title = "How AI Creates Images From TV Static #Shorts"
    elif "one second" in title_raw.lower() or "ai thinks" in title_raw.lower() or "how_ai_thinks" in spec.get("id", "").lower():
        title = "How an AI Thinks in One Second #Shorts"
    elif "flashattention" in title_raw.lower():
        title = "FlashAttention-3: How GPUs Hit 1.2 PFLOPS #Shorts"
    elif "r1" in title_raw.lower() or "r1" in spec.get("id", "").lower():
        title = "DeepSeek-R1: Open Weights Shock OpenAI o1 #Shorts"
    elif "deepseek" in title_raw.lower() and "gpt" in title_raw.lower():
        title = "DeepSeek-V3 vs GPT-4o: 18x Cheaper AI? #Shorts"
    elif "deepseek" in title_raw.lower():
        title = "How DeepSeek-V3 Saved 94% of Compute #Shorts"
    elif "kv" in title_raw.lower() and "cache" in title_raw.lower():
        title = "KV Cache Explained: How LLMs Generate Fast #Shorts"
    elif "sae" in title_raw.lower() or "latent" in title_raw.lower() or "parts-of-speech" in title_raw.lower():
        title = "Do Sparse Autoencoders Learn Grammar? #Shorts"
    elif "tamp" in title_raw.lower() or "motion planning" in title_raw.lower() or "coding agents" in title_raw.lower():
        title = "Coding Agents for Robotic Task & Motion Planning #Shorts"
    else:
        clean_t = title_raw.split(":")[0].strip()
        if len(clean_t) > 42:
            clean_t = clean_t[:39] + "..."
        title = f"{clean_t} Explained #Shorts"

    if spec.get("language") in ("hi", "hindi") and "(Hindi)" not in title:
        title = title.replace(" #Shorts", " (Hindi) #Shorts")

    # Mobile Title Linting & Truncation Guard (skills/yt-package/title.py)
    title_lint_report = None
    try:
        from pipeline.youtube_publisher import lint_title, optimize_title_for_mobile
        if len(title) > 50:
            title = optimize_title_for_mobile(title, max_chars=50)
        title_lint_report = lint_title(title)
        if not title_lint_report["passed"]:
            title = optimize_title_for_mobile(title, max_chars=48)
            title_lint_report = lint_title(title)
        print(f"📱 [Mobile Title Lint] ({title_lint_report['chars']} chars, score {title_lint_report['score']}/100): \"{title}\"")
    except Exception as e_lint:
        if len(title) > 50:
            title = title[:45].rsplit(" ", 1)[0] + " #Shorts"

    # 2. Chapter timestamps from beats
    chapter_lines = []
    for b in spec.get("beats", []):
        start = float(b.get("start", 0.0))
        mins = int(start // 60)
        secs = int(start % 60)
        ts_str = f"{mins}:{secs:02d}"
        if b.get("chapter_title"):
            focus = b["chapter_title"]
        else:
            focus = b.get("visual_focus", b.get("text", "")[:32]).replace("_", " ").title()
        if len(focus) > 35:
            focus = focus[:32] + "..."
        chapter_lines.append(f"{ts_str} - {focus}")

    chapters_block = "\n".join(chapter_lines) if chapter_lines else "0:00 - Introduction\n0:30 - Deep Dive"

    # 3. Core summary paragraph
    b1_text = spec.get("beats", [{}])[0].get("text", "")
    b5_text = spec.get("beats", [{}])[-2].get("text", "") if len(spec.get("beats", [])) >= 2 else ""

    import re
    arxiv_url = spec.get("arxiv_url") or spec.get("metadata", {}).get("arxiv_url")
    if not arxiv_url:
        search_blob = f"{spec.get('id', '')} {spec.get('arxiv_id', '')} {spec.get('title', '')} {video_path}"
        m = re.search(r'\d{4}\.\d{4,5}', search_blob)
        if m:
            arxiv_url = f"https://arxiv.org/abs/{m.group(0)}"
        else:
            arxiv_url = "https://themodelverse.in"

    # 4. Description construction
    description = f"""{title_raw} — Animated in pure 3Blue1Brown chalkboard style.

{b1_text}

{b5_text}

⏱️ CHAPTERS:
{chapters_block}

📄 PAPER & REFERENCES:
• Title: {title_raw}
• Paper link: {arxiv_url}
• Architecture & Visuals: Powered by The Model Verse engine

🌐 CONNECT WITH US:
• Website: https://themodelverse.in
• Subscribe for daily engineering deep dives into frontier AI models!

#Shorts #AI #MachineLearning #DeepSeek #arXiv #3Blue1Brown #NeuralNetworks #GPU #ComputerScience #LLM #ArtificialIntelligence
"""

    # 5. Targeted Tags
    base_tags = [
        "AI", "Machine Learning", "Artificial Intelligence", "Deep Learning",
        "Neural Networks", "3Blue1Brown", "The Model Verse", "LLM", "Tech Shorts",
        "arXiv", "GPU Acceleration", "Computer Science", "Shorts"
    ]
    if "diffusion" in title_raw.lower() or "tv static" in title_raw.lower() or "creates images" in title_raw.lower():
        base_tags.extend(["Diffusion Models", "Stable Diffusion", "Midjourney", "Denoising", "Reverse Diffusion", "Gaussian Noise", "AI Art", "Generative AI", "Computer Vision"])
    elif "one second" in title_raw.lower() or "ai thinks" in title_raw.lower() or "how_ai_thinks" in spec.get("id", "").lower():
        base_tags.extend(["Transformer", "Attention Mechanism", "GPU Memory", "SRAM", "FlashAttention", "SwiGLU", "Logits", "Softmax", "Inference Speed", "AI Hardware", "LLM Inference"])
    elif "r1" in title_raw.lower() or "r1" in spec.get("id", "").lower():
        base_tags.extend(["DeepSeek-R1", "OpenAI o1", "Reinforcement Learning", "GRPO", "Reasoning Models", "AIME 2024", "Math AI"])
    elif "deepseek" in title_raw.lower():
        base_tags.extend(["DeepSeek", "DeepSeek-V3", "Mixture of Experts", "MoE", "Sparse MoE"])
    if "flashattention" in title_raw.lower():
        base_tags.extend(["FlashAttention", "FlashAttention-3", "NVIDIA H100", "Tensor Cores", "CUDA", "Hopper TMA"])
    if "kv" in title_raw.lower() or "cache" in title_raw.lower():
        base_tags.extend(["KV Cache", "Transformer Attention", "Inference Optimization", "vLLM"])
    if "sae" in title_raw.lower() or "latent" in title_raw.lower() or "interpret" in title_raw.lower():
        base_tags.extend(["Sparse Autoencoders", "Mechanistic Interpretability", "SAE Latents", "Anthropic", "Parts of Speech", "Superposition", "AI Research", "Neural Geometry"])
    if "tamp" in title_raw.lower() or "motion planning" in title_raw.lower() or "robot" in title_raw.lower() or "coding" in title_raw.lower():
        base_tags.extend(["Robotics", "TAMP", "Coding Agents", "Task and Motion Planning", "Program Synthesis", "Kinematics", "Autonomous Agents", "Robot Learning", "3Blue1Brown"])

    # 6. Pinned Comment (Drives Algorithm Engagement)
    if "diffusion" in title_raw.lower() or "tv static" in title_raw.lower() or "creates images" in title_raw.lower():
        pinned_comment = "🎨 Question: Does thinking of diffusion as 'a sculptor chipping away noise dust' make generative image models click for you? Drop your thoughts below! 👇"
    elif "one second" in title_raw.lower() or "ai thinks" in title_raw.lower() or "how_ai_thinks" in spec.get("id", "").lower():
        pinned_comment = "⚡ From token disintegration to 80-layer SwiGLU gating in under 1000ms: What part of the transformer inference pipeline surprised you most? Drop your thoughts below! 👇"
    elif "r1" in title_raw.lower() or "r1" in spec.get("id", "").lower():
        pinned_comment = "🧠 Question: Can pure reinforcement learning without human supervision replace human-annotated fine-tuning entirely? Drop your thoughts below! 👇"
    elif "flashattention" in title_raw.lower():
        pinned_comment = "⚡ Question: Are you bottlenecked more by GPU memory bandwidth (HBM) or compute FLOPS in your inference stack? Drop your hardware setup below! 👇"
    elif "deepseek" in title_raw.lower():
        pinned_comment = "🧠 Question: Would you rather serve an active 37B MoE or a monolithic 70B dense model for your production workflows? Let's discuss! 👇"
    elif "sae" in title_raw.lower() or "latent" in title_raw.lower() or "interpret" in title_raw.lower():
        pinned_comment = "🧠 Question: Do you think Sparse Autoencoders will completely demystify neural network 'black boxes'? Drop your thoughts below! 👇"
    elif "tamp" in title_raw.lower() or "motion planning" in title_raw.lower() or "robot" in title_raw.lower() or "coding" in title_raw.lower():
        pinned_comment = "🤖 Question: Will programmatic coding agents replace traditional PDDLStream search algorithms for physical robots? Drop your take below! 👇"
    else:
        pinned_comment = "💡 What AI paper or architectural breakthrough should we break down on the chalkboard next? Let us know below! 👇"

    return {
        "title": title,
        "description": description.strip(),
        "tags": base_tags[:20],
        "category_id": YOUTUBE_DEFAULT_CATEGORY,
        "pinned_comment": pinned_comment,
        "privacy_status": "unlisted",
        "language": spec.get("language", "en"),
        "title_lint": title_lint_report
    }


def upload_short(
    video_path: str,
    metadata: Dict[str, Any],
    privacy_status: str = "unlisted",
    post_comment: bool = True
) -> Dict[str, Any]:
    """Uploads video to YouTube Shorts using resumable upload and optionally pins a comment."""
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found at: {video_path}")

    print("\n=======================================================")
    print("🚀 THE MODEL VERSE — YOUTUBE SHORTS PUBLISHER")
    print("=======================================================\n")
    print(f"🎬 Video: {video_path}")
    print(f"🎯 Title: {metadata['title']}")
    print(f"🔒 Privacy: {privacy_status.upper()}")
    print(f"🏷️ Tags: {', '.join(metadata['tags'][:6])}...")

    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata["tags"],
            "categoryId": metadata.get("category_id", YOUTUBE_DEFAULT_CATEGORY),
            "defaultLanguage": "hi" if metadata.get("language") in ("hi", "hindi") else "en",
            "defaultAudioLanguage": "hi" if metadata.get("language") in ("hi", "hindi") else "en"
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
            "license": "youtube"
        }
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        chunksize=1024 * 1024 * 2,  # 2MB chunks
        resumable=True
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    print("\n📤 Uploading to YouTube (resumable chunks)...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"   ⏳ Upload Progress: {pct}% complete...")

    video_id = response.get("id")
    shorts_url = f"https://youtube.com/shorts/{video_id}"
    studio_url = f"https://studio.youtube.com/video/{video_id}/edit"

    print("\n=======================================================")
    print("🎉 YOUTUBE SHORTS UPLOAD SUCCESSFUL!")
    print(f"🆔 Video ID: {video_id}")
    print(f"📱 Shorts URL: {shorts_url}")
    print(f"🛠️ Studio URL: {studio_url}")
    print("=======================================================\n")

    # Set Custom High-CTR Thumbnail Poster if available
    try:
        from pipeline.thumbnail_generator import THUMBNAILS_DIR
        stem = Path(video_path).stem.replace('final_', '')
        stem_clean = (
            stem.replace('_architecture_breakdown', '')
            .replace('_mechanism_deepdive', '')
            .replace('_model_showdown', '')
            .replace('_benchmark_news', '')
        )
        poster_cands = [
            THUMBNAILS_DIR / f"{stem_clean}_poster.png",
            THUMBNAILS_DIR / f"{stem_clean}_poster.jpg",
            THUMBNAILS_DIR / f"{stem}_poster.png",
            THUMBNAILS_DIR / f"{stem}_poster.jpg",
        ]
        for p in sorted(THUMBNAILS_DIR.glob("*_poster.png")):
            if any(part in p.name for part in stem_clean.split("_") if len(part) >= 4):
                poster_cands.append(p)
        for p in sorted(THUMBNAILS_DIR.glob("*_poster.jpg")):
            if any(part in p.name for part in stem_clean.split("_") if len(part) >= 4):
                poster_cands.append(p)

        poster_to_upload = next((p for p in poster_cands if p.exists()), None)
        if poster_to_upload:
            print(f"🖼️ Uploading custom high-CTR poster: {poster_to_upload.name}...")
            mime = "image/jpeg" if poster_to_upload.suffix == ".jpg" else "image/png"
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(poster_to_upload), mimetype=mime)
            ).execute()
            print("✅ Custom poster thumbnail set successfully!")
    except Exception as e:
        print(f"⚠️ Could not set custom thumbnail: {e}")

    # Post Pinned Engagement Comment
    if post_comment and metadata.get("pinned_comment"):
        try:
            print("💬 Posting engagement comment...")
            comment_body = {
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": metadata["pinned_comment"]
                        }
                    }
                }
            }
            comment_resp = youtube.commentThreads().insert(
                part="snippet",
                body=comment_body
            ).execute()
            print("✅ Comment posted successfully.")
        except Exception as e:
            print(f"⚠️ Could not post comment automatically: {e}")

    return {
        "video_id": video_id,
        "shorts_url": shorts_url,
        "studio_url": studio_url,
        "title": metadata["title"]
    }


def main():
    parser = argparse.ArgumentParser(description="The Model Verse — Autonomous YouTube Shorts Publisher CLI")
    parser.add_argument("--video", help="Path to rendered MP4 video")
    parser.add_argument("--spec", help="Path to spec JSON template with metadata & chapters")
    parser.add_argument("--title", help="Optional title override")
    parser.add_argument("--privacy", choices=["unlisted", "public", "private"], default="unlisted", help="Upload privacy status (default: unlisted)")
    parser.add_argument("--instagram", action="store_true", help="Also publish as Instagram Reel via Meta Graph API")
    parser.add_argument("--dry-run", action="store_true", help="Print generated metadata, title, description, and tags without uploading")
    parser.add_argument("--auth-only", action="store_true", help="Run interactive OAuth2 flow and exit")
    args = parser.parse_args()

    if args.auth_only:
        print("🔐 Authenticating with YouTube Data API...")
        get_authenticated_service()
        print("✅ OAuth2 authentication verified and saved.")
        return

    spec = {}
    if args.spec and os.path.exists(args.spec):
        with open(args.spec, "r", encoding="utf-8") as f:
            spec = json.load(f)
    elif args.video:
        # Attempt to find matching spec in pipeline/templates/
        v_stem = Path(args.video).stem.replace("final_", "").lower()
        templates_dir = PROJECT_ROOT / "pipeline" / "templates"
        for p in templates_dir.glob("*.json"):
            if p.stem.lower() in v_stem or v_stem in p.stem.lower():
                with open(p, "r", encoding="utf-8") as f:
                    spec = json.load(f)
                    print(f"📄 Inferred spec from template: {p.name}")
                    break

    if not spec:
        spec = {
            "title": args.title or "Frontier AI Architecture Deep Dive",
            "category": "architecture_breakdown",
            "id": Path(args.video).stem if args.video else "ai_short",
            "beats": []
        }

    if args.title:
        spec["title"] = args.title

    video_path = args.video or "final_deepseek-v3_architecture_breakdown.mp4"
    metadata = generate_shorts_metadata(spec, video_path)

    if args.dry_run or not args.video:
        print("\n=======================================================")
        print("🔍 YOUTUBE SHORTS METADATA PREVIEW (DRY-RUN)")
        print("=======================================================")
        print(f"🎯 TITLE ({len(metadata['title'])} chars):\n{metadata['title']}\n")
        print(f"📝 DESCRIPTION:\n{metadata['description']}\n")
        print(f"🏷️ TAGS ({len(metadata['tags'])}):\n{', '.join(metadata['tags'])}\n")
        print(f"💬 PINNED COMMENT:\n{metadata['pinned_comment']}\n")
        print(f"🔒 PRIVACY STATUS: {args.privacy.upper()}")
        print("=======================================================\n")

        if args.instagram:
            from pipeline.instagram_caption_generator import generate_instagram_post, format_full_caption_with_hashtags
            ig_post = generate_instagram_post(spec)
            print("=======================================================")
            print("🔍 INSTAGRAM REELS PREVIEW (DRY-RUN)")
            print("=======================================================")
            print(f"🪝 HOOK:\n{ig_post['hook']}\n")
            print(f"📝 CAPTION:\n{format_full_caption_with_hashtags(ig_post)}\n")
            print(f"💬 FIRST COMMENT:\n{ig_post['first_comment']}\n")
            print("=======================================================\n")

        if not args.video:
            print("💡 Tip: Provide --video <path.mp4> to execute live upload.")
        return

    upload_short(video_path, metadata, privacy_status=args.privacy)

    if args.instagram:
        from pipeline.instagram_caption_generator import generate_instagram_post
        from pipeline.instagram_publisher import instagram_publisher
        print("\n📸 Cross-posting to Instagram Reels...")
        ig_post_data = generate_instagram_post(spec)
        try:
            instagram_publisher.publish_reel(video_path, ig_post_data)
        except Exception as e_ig:
            print(f"⚠️ Instagram publication skipped or failed: {e_ig}")


if __name__ == "__main__":
    main()
