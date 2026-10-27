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
import re
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import (
    YOUTUBE_CLIENT_SECRETS_PATH,
    YOUTUBE_TOKEN_PATH,
    YOUTUBE_DEFAULT_CATEGORY,
    resolve_track,
    TRACK_METADATA,
    TRACK_ACADEMIC,
    TRACK_TECH_NEWS,
    TRACK_DEVELOPER_PERKS,
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
            # Port 8080 is commonly occupied by local dev servers. Port 0
            # asks the OS for a free callback port and avoids needless auth
            # failures on developer machines.
            oauth_port = int(os.getenv("YOUTUBE_OAUTH_PORT", "0"))
            creds = flow.run_local_server(port=oauth_port, prompt="consent")

            # Persist token for future headless runs
            os.makedirs(os.path.dirname(os.path.abspath(token_file)), exist_ok=True)
            with open(token_file, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
            print(f"✅ Credentials saved to {token_file}")

    return build("youtube", "v3", credentials=creds)


def _first_http_url(*values: Any) -> Optional[str]:
    """Return the first explicit HTTP(S) source URL, never an invented fallback."""
    for value in values:
        if isinstance(value, str):
            candidate = value.strip()
            if candidate.startswith(("https://", "http://")):
                return candidate
    return None


def _explicit_provenance(spec: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, str]:
    """Collect source/provider/model fields only when the spec explicitly supplies them."""
    values = {
        "source_url": _first_http_url(
            spec.get("source_url"),
            spec.get("canonical_url"),
            spec.get("claim_url"),
            spec.get("arxiv_url"),
            meta.get("source_url"),
            meta.get("canonical_url"),
            meta.get("claim_url"),
            meta.get("arxiv_url"),
        ),
        "provider": next(
            (
                str(value).strip()
                for value in (
                    spec.get("source_provider"),
                    spec.get("provider"),
                    meta.get("source_provider"),
                    meta.get("provider"),
                )
                if isinstance(value, str) and value.strip()
            ),
            None,
        ),
        "model": next(
            (
                str(value).strip()
                for value in (
                    spec.get("model_name"),
                    spec.get("model"),
                    meta.get("model_name"),
                    meta.get("model"),
                )
                if isinstance(value, str) and value.strip()
            ),
            None,
        ),
        "tts_provider": next(
            (
                str(value).strip()
                for value in (
                    spec.get("tts_provider"),
                    meta.get("tts_provider"),
                )
                if isinstance(value, str) and value.strip()
            ),
            None,
        ),
    }
    return {key: value for key, value in values.items() if value}


def _topic_tags(spec: Dict[str, Any], title_raw: str, provenance: Dict[str, str]) -> set[str]:
    """Build tags from the current topic and explicit provenance, not historical video claims."""
    blob = " ".join(
        str(value)
        for value in (
            title_raw,
            spec.get("id", ""),
            spec.get("abstract", ""),
            spec.get("topic", ""),
            provenance.get("provider", ""),
            provenance.get("model", ""),
        )
    ).lower()
    tags: set[str] = set()
    keyword_tags = {
        "diffusion": {"DiffusionModels", "GenerativeAI"},
        "robot": {"Robotics", "EmbodiedAI"},
        "humanoid": {"Robotics", "Humanoid"},
        "transformer": {"Transformer", "AttentionMechanism"},
        "attention": {"AttentionMechanism", "GPUOptimization"},
        "flashattention": {"FlashAttention", "GPUOptimization"},
        "mixture of experts": {"MixtureOfExperts", "SparseModels"},
        "moe": {"MixtureOfExperts", "SparseModels"},
        "reasoning": {"ReasoningModels", "Inference"},
        "agent": {"AIAgents", "ToolUse"},
        "inference": {"Inference", "ModelServing"},
        "quant": {"Quantization", "EfficientAI"},
    }
    for keyword, additions in keyword_tags.items():
        if keyword in blob:
            tags.update(additions)

    for name in ("Kimi", "OpenAI", "Anthropic", "DeepSeek", "Google", "Meta", "Mistral", "Qwen"):
        if name.lower() in blob:
            tags.add(name)

    # Preserve recognizable model/provider names as searchable tags when explicit.
    for key in ("provider", "model"):
        value = provenance.get(key)
        if value:
            normalized = re.sub(r"[^A-Za-z0-9]+", "", value)
            if 2 <= len(normalized) <= 40:
                tags.add(normalized)
    return tags


def generate_shorts_metadata(spec: Dict[str, Any], video_path: str) -> Dict[str, Any]:
    """Generates viral, SEO-optimized title, description, tags, and pinned comment from spec."""
    title_raw = str(spec.get("title") or spec.get("topic") or "AI Architecture Deep Dive").strip()
    category = spec.get("category", "mechanism_deepdive")
    meta = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
    provenance = _explicit_provenance(spec, meta)

    clean_t = re.sub(r"\s+", " ", title_raw).strip()
    if len(clean_t) > 42:
        clean_t = clean_t[:39].rsplit(" ", 1)[0] + "..."
    title = f"{clean_t} #Shorts"

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
    beats = spec.get("beats") or []
    b1_text = beats[0].get("text", "") if len(beats) > 0 else ""
    b5_text = beats[-2].get("text", "") if len(beats) >= 2 else ""

    arxiv_url = provenance.get("source_url")
    if not arxiv_url:
        m = re.search(r"(?<!\d)(\d{4}\.\d{4,5})(?!\d)", str(spec.get("arxiv_id") or spec.get("id") or ""))
        if m:
            arxiv_url = f"https://arxiv.org/abs/{m.group(1)}"
            provenance["source_url"] = arxiv_url

    # 4. Canonical track resolution and references block
    track = resolve_track(spec.get("category") or spec.get("metadata", {}).get("category", ""))
    track_meta = TRACK_METADATA.get(track, TRACK_METADATA[TRACK_ACADEMIC])

    if track == TRACK_TECH_NEWS:
        source_url = arxiv_url
        ref_block = f"""📰 OFFICIAL SOURCE & ANNOUNCEMENT:
• Breakthrough: {title_raw}
• Source Link: {source_url or 'Not provided in source record'}
• Track: {track_meta['display_name']} // {track_meta['badge']}
• Visuals: Powered by The Model Verse Engine"""
    elif track == TRACK_DEVELOPER_PERKS:
        perk_url = arxiv_url
        ref_block = f"""🎁 DEVELOPER PERK DETAILS:
• Program: {title_raw}
• Claim Portal: {perk_url or 'Not provided in source record'}
• Track: {track_meta['display_name']} // {track_meta['badge']}
• Verification: Ground-truth audited by The Model Verse"""
    else:
        ref_block = f"""📄 PAPER & REFERENCES:
• Title: {title_raw}
• Paper link: {arxiv_url or 'Not provided in source record'}
• Track: {track_meta['display_name']} // {track_meta['badge']}
• Visuals: Powered by The Model Verse Engine"""

    provenance_lines = []
    if provenance.get("provider"):
        provenance_lines.append(f"• Source provider: {provenance['provider']}")
    if provenance.get("model"):
        provenance_lines.append(f"• Model: {provenance['model']}")
    if provenance.get("tts_provider"):
        provenance_lines.append(f"• Voice provider: {provenance['tts_provider']}")
    if provenance_lines:
        ref_block += "\n" + "\n".join(provenance_lines)

    # 5. Hashtags construction (dynamically category-aware)
    tag_set = set(track_meta.get("default_tags", ["AI", "MachineLearning", "Shorts"]))
    title_lower = title_raw.lower()
    spec_id_lower = str(spec.get("id", "")).lower()
    tag_set.update(_topic_tags(spec, title_raw, provenance))

    hashtags = [f"#{t.replace(' ', '')}" for t in sorted(tag_set)]
    hashtags_str = " ".join(hashtags[:12])

    # 6. Description construction
    description = f"""{title_raw} — {track_meta['description_prefix']}.

{b1_text}

{b5_text}

⏱️ CHAPTERS:
{chapters_block}

{ref_block}

🌐 CONNECT WITH US:
• Website: https://themodelverse.in
• Subscribe for daily engineering deep dives into frontier AI models!

{hashtags_str}
"""

    # 7. Targeted Tags for YouTube Metadata
    base_tags = list(track_meta.get("default_tags", []))
    for t in sorted(tag_set):
        if t not in base_tags:
            base_tags.append(t)

    # 8. Pinned Comment (Drives Algorithm Engagement)
    if any(k in title_lower for k in ["diffusion", "tv static", "creates images"]):
        pinned_comment = "🎨 Question: Does thinking of diffusion as 'a sculptor chipping away noise dust' make generative image models click for you? Drop your thoughts below! 👇"
    elif any(k in title_lower or k in spec_id_lower for k in ["robot", "humanoid", "reflex", "kinematic", "locomotion"]):
        pinned_comment = "🤖 Question: Will reactive visual reflex loops replace traditional trajectory planning for humanoid robots? Drop your take below! 👇"
    elif any(k in title_lower or k in spec_id_lower for k in ["transformer", "one second", "ai thinks"]):
        pinned_comment = "⚡ From token disintegration to 80-layer SwiGLU gating in under 1000ms: What part of the inference pipeline surprised you most? Drop your thoughts below! 👇"
    elif any(k in title_lower or k in spec_id_lower for k in ["r1", "reasoning"]):
        pinned_comment = "🧠 Question: Can pure reinforcement learning without human supervision replace human-annotated fine-tuning entirely? Drop your thoughts below! 👇"
    elif "flashattention" in title_lower:
        pinned_comment = "⚡ Question: Are you bottlenecked more by GPU memory bandwidth (HBM) or compute FLOPS in your inference stack? Drop your hardware setup below! 👇"
    elif "deepseek" in title_lower:
        pinned_comment = "🧠 Question: Would you rather serve an active 37B MoE or a monolithic 70B dense model for your production workflows? Let's discuss! 👇"
    elif any(k in title_lower or k in spec_id_lower for k in ["sae", "latent", "interpret"]):
        pinned_comment = "🧠 Question: Do you think Sparse Autoencoders will completely demystify neural network 'black boxes'? Drop your thoughts below! 👇"
    elif any(k in title_lower or k in spec_id_lower for k in ["tamp", "motion planning"]):
        pinned_comment = "🤖 Question: Will programmatic coding agents replace traditional PDDLStream search algorithms for physical robots? Drop your take below! 👇"
    else:
        pinned_comment = track_meta.get("pinned_comment", "💡 What topic or architectural breakthrough should we break down next? Let us know below! 👇")

    result = {
        "title": title,
        "description": description.strip(),
        "tags": base_tags[:20],
        "category_id": YOUTUBE_DEFAULT_CATEGORY,
        "pinned_comment": pinned_comment,
        "privacy_status": "unlisted",
        "language": spec.get("language", "en"),
        "title_lint": title_lint_report
    }
    result.update(provenance)
    return result


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
    parser.add_argument("--x", "--twitter", dest="publish_x", action="store_true", help="Also publish as 4-tweet video thread to X (Twitter)")
    parser.add_argument("--linkedin", action="store_true", help="Also publish as video post to LinkedIn")
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

        if args.publish_x:
            from pipeline.x_thread_generator import generate_x_thread, calculate_tweet_length
            x_tweets = generate_x_thread(spec)
            print("=======================================================")
            print("🔍 X (TWITTER) THREAD PREVIEW (DRY-RUN)")
            print("=======================================================")
            for i, tw in enumerate(x_tweets, 1):
                eff_len = calculate_tweet_length(tw)
                attached = " [📹 Attached Video]" if i == 1 else ""
                print(f"\n--- TWEET {i}/4 ({eff_len}/280 chars){attached} ---")
                print(tw)
            print("\n=======================================================\n")

        if args.linkedin:
            from pipeline.linkedin_copy_generator import generate_linkedin_post
            li_post = generate_linkedin_post(spec)
            print("=======================================================")
            print("🔍 LINKEDIN POST PREVIEW (DRY-RUN)")
            print("=======================================================")
            print(f"🪝 HOOK:\n{li_post['hook']}\n")
            print(f"📝 COMMENTARY:\n{li_post['commentary']}\n")
            print(f"💬 FIRST COMMENT (WITH EXTERNAL LINKS):\n{li_post['first_comment']}\n")
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

    if args.publish_x:
        from pipeline.x_publisher import x_publisher
        print("\n🧵 Cross-posting to X (Twitter) as a 4-tweet video thread...")
        try:
            x_publisher.publish_video_thread(video_path, spec)
        except Exception as e_x:
            print(f"⚠️ X publication skipped or failed: {e_x}")

    if args.linkedin:
        from pipeline.linkedin_publisher import linkedin_publisher
        print("\n💼 Cross-posting to LinkedIn...")
        try:
            linkedin_publisher.publish_video(video_path, spec)
        except Exception as e_li:
            print(f"⚠️ LinkedIn publication skipped or failed: {e_li}")




if __name__ == "__main__":
    main()
