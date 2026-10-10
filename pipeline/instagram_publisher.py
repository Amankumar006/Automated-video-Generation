"""
The Model Verse — Instagram Reels & Feed Publisher CLI
Publishes rendered vertical videos (Reels) and model card posters to Instagram via Meta Graph API v21.0.

Features:
  1. Meta Graph API v21.0 container initialization & status polling
  2. Resumable video upload protocol (direct binary upload of local MP4 files without external hosting)
  3. Public video_url and image_url container support
  4. Automatic caption formatting with dynamic hashtags and first comment auto-reply
  5. Token validation and clear expiration diagnostics
"""

import os
import sys
import time
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.config import (
    INSTAGRAM_ACCOUNT_ID,
    INSTAGRAM_ACCESS_TOKEN,
    INSTAGRAM_API_VERSION,
    INSTAGRAM_GRAPH_URL,
    INSTAGRAM_RUPLOAD_URL
)
from pipeline.instagram_caption_generator import (
    generate_instagram_post,
    format_full_caption_with_hashtags
)


class InstagramPublisher:
    """Manages publishing of Reels and feed images to Instagram via Meta Graph API."""

    def __init__(
        self,
        account_id: Optional[str] = None,
        access_token: Optional[str] = None,
        api_version: str = INSTAGRAM_API_VERSION
    ):
        self.account_id = account_id or INSTAGRAM_ACCOUNT_ID
        self.access_token = access_token or INSTAGRAM_ACCESS_TOKEN
        self.api_version = api_version
        self.graph_url = f"https://graph.facebook.com/{self.api_version}"
        self.rupload_url = f"https://rupload.facebook.com/ig-video-upload/{self.api_version}"

    def check_token_validity(self) -> Tuple[bool, Dict[str, Any]]:
        """Verifies that the Instagram access token is active and valid."""
        if not self.access_token:
            return False, {"error": "INSTAGRAM_ACCESS_TOKEN is not configured in environment or .env."}

        url = f"{self.graph_url}/{self.account_id}?fields=id,username,name&access_token={self.access_token}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                return True, data
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            try:
                err_json = json.loads(err_body)
                return False, err_json.get("error", {"message": err_body})
            except Exception:
                return False, {"message": err_body, "code": e.code}
        except Exception as e:
            return False, {"message": str(e)}

    def create_image_container(self, image_url: str, caption: str) -> str:
        """Step A for Images: Creates an Instagram image media container."""
        url = f"{self.graph_url}/{self.account_id}/media"
        payload = json.dumps({
            "image_url": image_url,
            "caption": caption,
            "access_token": self.access_token
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data["id"]

    def create_video_url_container(self, video_url: str, caption: str, cover_url: Optional[str] = None) -> str:
        """Creates an Instagram Reels container using a public video URL."""
        url = f"{self.graph_url}/{self.account_id}/media"
        body: Dict[str, Any] = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": self.access_token
        }
        if cover_url:
            body["cover_url"] = cover_url

        payload = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data["id"]

    def create_resumable_reels_container(self, video_path: str, caption: str) -> Tuple[str, str]:
        """
        Step 1 of Resumable Upload:
        Initializes an Instagram Reels container for direct binary upload.
        Returns: (container_id, upload_uri)
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at: {video_path}")

        file_size = os.path.getsize(video_path)
        url = f"{self.graph_url}/{self.account_id}/media"
        
        # Format payload for resumable upload protocol
        params = {
            "media_type": "REELS",
            "upload_type": "resumable",
            "caption": caption,
            "access_token": self.access_token
        }
        data = urllib.parse.urlencode(params).encode("utf-8")

        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=30) as resp:
            res = json.loads(resp.read().decode())
            container_id = res["id"]
            upload_uri = res.get("uri") or f"{self.rupload_url}/{container_id}"
            return container_id, upload_uri

    def upload_binary_video_stream(self, upload_uri: str, video_path: str) -> None:
        """
        Step 2 of Resumable Upload:
        Streams the local MP4 video file binary data directly to Meta's rupload endpoint.
        """
        file_size = os.path.getsize(video_path)
        with open(video_path, "rb") as f:
            video_bytes = f.read()

        headers = {
            "Authorization": f"OAuth {self.access_token}",
            "offset": "0",
            "file_size": str(file_size),
            "Content-Type": "application/octet-stream"
        }

        print(f"📤 Uploading binary video stream ({file_size / (1024*1024):.2f} MB) to Instagram...")
        req = urllib.request.Request(upload_uri, data=video_bytes, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=120) as resp:
            res = json.loads(resp.read().decode())
            if not res.get("success", False):
                print(f"⚠️ Rupload response: {res}")

    def wait_for_container_ready(self, container_id: str, max_wait_sec: int = 180, poll_interval: int = 5) -> bool:
        """
        Step 3: Polls container status until Meta has finished encoding and processing the video.
        """
        url = f"{self.graph_url}/{container_id}?fields=status_code,status&access_token={self.access_token}"
        elapsed = 0
        print(f"⏳ Waiting for Meta video processing (Container ID: {container_id})...")

        while elapsed < max_wait_sec:
            req = urllib.request.Request(url)
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode())
                    status_code = data.get("status_code")
                    if status_code == "FINISHED":
                        print("✅ Instagram video encoding completed and ready for publishing.")
                        return True
                    elif status_code == "ERROR":
                        err_msg = data.get("status", "Unknown processing error")
                        raise RuntimeError(f"Instagram media processing failed: {err_msg}")
                    elif status_code in ("IN_PROGRESS", "EXPIRED"):
                        print(f"   ... processing status: {status_code} ({elapsed}s elapsed)")
            except urllib.error.HTTPError as e:
                print(f"   ⚠️ Polling HTTP error: {e.code}")

            time.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"Instagram container did not reach FINISHED status within {max_wait_sec} seconds.")

    def publish_container(self, container_id: str) -> str:
        """
        Step 4: Publishes the verified container to live Instagram feed/Reels.
        Returns: published media ID
        """
        url = f"{self.graph_url}/{self.account_id}/media_publish"
        payload = json.dumps({
            "creation_id": container_id,
            "access_token": self.access_token
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data["id"]

    def post_first_comment(self, media_id: str, comment_text: str) -> Optional[str]:
        """Step 5: Posts an engagement follow-up first comment to the live post."""
        if not comment_text:
            return None

        url = f"{self.graph_url}/{media_id}/comments"
        data = urllib.parse.urlencode({
            "message": comment_text,
            "access_token": self.access_token
        }).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode())
                print("💬 First comment posted successfully on Instagram.")
                return data.get("id")
        except Exception as e:
            print(f"⚠️ Could not post first comment on Instagram: {e}")
            return None

    def publish_reel(
        self,
        video_path: str,
        post_data: Dict[str, str],
        video_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Full end-to-end publishing pipeline for Instagram Reels.
        Uses resumable binary upload if video_path is local, or video_url if provided.
        """
        caption = format_full_caption_with_hashtags(post_data)

        print("\n=======================================================")
        print("📸 THE MODEL VERSE — INSTAGRAM REELS PUBLISHER")
        print("=======================================================\n")
        print(f"🎬 Video: {video_path}")
        print(f"🪝 Hook: {post_data.get('hook', '')}")
        print(f"📝 Caption length: {len(caption)} characters")

        if video_url:
            print(f"🌐 Creating Reels container via public URL: {video_url}...")
            container_id = self.create_video_url_container(video_url, caption)
        else:
            print(f"📁 Initiating direct binary Resumable Upload for local file: {video_path}...")
            container_id, upload_uri = self.create_resumable_reels_container(video_path, caption)
            self.upload_binary_video_stream(upload_uri, video_path)

        # Poll container readiness
        self.wait_for_container_ready(container_id)

        # Publish container
        print(f"🚀 Publishing container {container_id} to Instagram...")
        media_id = self.publish_container(container_id)
        permalink = f"https://www.instagram.com/p/{media_id}/"

        print("\n=======================================================")
        print("🎉 INSTAGRAM REEL PUBLISHED SUCCESSFULLY!")
        print(f"🆔 Media ID: {media_id}")
        print(f"🔗 Instagram Link: {permalink}")
        print("=======================================================\n")

        # Post first engagement comment
        if post_data.get("first_comment"):
            self.post_first_comment(media_id, post_data["first_comment"])

        return {
            "media_id": media_id,
            "permalink": permalink,
            "container_id": container_id,
            "hook": post_data.get("hook"),
            "caption": caption
        }


# Global singleton
instagram_publisher = InstagramPublisher()


def main():
    parser = argparse.ArgumentParser(description="The Model Verse — Instagram Reels Publisher CLI")
    parser.add_argument("--video", help="Path to rendered MP4 video")
    parser.add_argument("--spec", help="Path to spec JSON template")
    parser.add_argument("--video-url", help="Optional publicly hosted video URL")
    parser.add_argument("--image-url", help="Optional public image URL for feed post")
    parser.add_argument("--check-token", action="store_true", help="Verify Instagram access token and account status")
    parser.add_argument("--dry-run", action="store_true", help="Generate caption, hashtags, and preview payload without publishing")
    args = parser.parse_args()

    pub = InstagramPublisher()

    if args.check_token:
        is_valid, info = pub.check_token_validity()
        if is_valid:
            print(f"✅ Instagram token is VALID for account @{info.get('username', info.get('name'))} (ID: {info.get('id')})")
        else:
            print(f"❌ Instagram token is INVALID or EXPIRED:\n{json.dumps(info, indent=2)}")
        return

    # Load or infer spec
    spec: Dict[str, Any] = {}
    if args.spec and os.path.exists(args.spec):
        with open(args.spec, "r", encoding="utf-8") as f:
            spec = json.load(f)
    elif args.video:
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
            "title": "Frontier AI Architecture Deep Dive",
            "category": "mechanism_deepdive",
            "metadata": {"model_name": "STEPQuant"}
        }

    post_data = generate_instagram_post(spec)

    if args.dry_run or not args.video:
        print("\n=======================================================")
        print("🔍 INSTAGRAM POST METADATA PREVIEW (DRY-RUN)")
        print("=======================================================\n")
        print(f"🪝 HOOK:\n{post_data['hook']}\n")
        print(f"📝 CAPTION ({len(post_data['caption'])} chars):\n{post_data['caption']}\n")
        print(f"🏷️ HASHTAGS:\n{post_data['hashtags']}\n")
        print(f"💬 FIRST COMMENT:\n{post_data['first_comment']}\n")
        print(f"♿ ALT TEXT:\n{post_data['alt_text']}\n")
        full_caption = format_full_caption_with_hashtags(post_data)
        print(f"📦 FULL CAPTION PAYLOAD ({len(full_caption)} chars):\n{full_caption}")
        print("=======================================================\n")
        if not args.video:
            print("💡 Tip: Provide --video <path.mp4> to execute live publish.")
        return

    # Check token before publishing
    is_valid, info = pub.check_token_validity()
    if not is_valid:
        print(f"❌ Cannot publish to Instagram: Access token is invalid or expired:\n{info.get('message', info)}")
        print("\nPlease update INSTAGRAM_ACCESS_TOKEN in your environment or .env file.")
        sys.exit(1)

    pub.publish_reel(args.video, post_data, video_url=args.video_url)


if __name__ == "__main__":
    main()
