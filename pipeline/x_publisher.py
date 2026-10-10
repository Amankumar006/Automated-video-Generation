"""
The Model Verse — Autonomous X (Twitter) Video Thread Publisher CLI
Publishes rendered vertical video shorts with automated 4-tweet technical threads
to X (Twitter) using OAuth 1.0a User Context and X API v2.

Features:
  1. OAuth 1.0a User Context authentication & token validation
  2. Resumable chunked video upload (INIT -> APPEND -> FINALIZE -> STATUS polling)
  3. Sequential thread publishing with automatic in_reply_to chaining
  4. Algorithm-optimized formatting (Video lead in Tweet 1, zero links in Tweet 1,
     mechanisms in Tweet 2, benchmarks in Tweet 3, and sources in Tweet 4)
  5. Dry-run preview and diagnostic token checking
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests
from requests_oauthlib import OAuth1

from pipeline.config import (
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET,
    TWITTER_API_BASE_URL,
    TWITTER_UPLOAD_BASE_URL
)
from pipeline.x_thread_generator import generate_x_thread, calculate_tweet_length

CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB chunk size for media upload


class XPublisher:
    """Manages publishing of video shorts and technical threads to X (Twitter)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
        api_base_url: str = TWITTER_API_BASE_URL,
        upload_base_url: str = TWITTER_UPLOAD_BASE_URL
    ):
        self.api_key = api_key if api_key is not None else TWITTER_API_KEY
        self.api_secret = api_secret if api_secret is not None else TWITTER_API_SECRET
        self.access_token = access_token if access_token is not None else TWITTER_ACCESS_TOKEN
        self.access_token_secret = access_token_secret if access_token_secret is not None else TWITTER_ACCESS_TOKEN_SECRET
        self.api_base_url = api_base_url.rstrip("/")
        self.upload_base_url = upload_base_url


        self._auth: Optional[OAuth1] = None
        if self.is_configured:
            self._auth = OAuth1(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret
            )

    @property
    def is_configured(self) -> bool:
        """Returns True if all 4 required OAuth 1.0a keys are provided."""
        return bool(
            self.api_key and
            self.api_secret and
            self.access_token and
            self.access_token_secret
        )

    def check_token_validity(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifies that Twitter credentials are valid and returns user profile data.
        Calls GET https://api.twitter.com/2/users/me
        """
        if not self.is_configured:
            return False, {
                "error": "Twitter credentials missing. Ensure TWITTER_API_KEY, TWITTER_API_SECRET, "
                         "TWITTER_ACCESS_TOKEN, and TWITTER_ACCESS_TOKEN_SECRET are set in .env."
            }

        url = f"{self.api_base_url}/2/users/me"
        try:
            resp = requests.get(url, auth=self._auth, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                return True, data.get("data", {})
            else:
                return False, {
                    "status_code": resp.status_code,
                    "response": resp.text
                }
        except Exception as e:
            return False, {"error": str(e)}

    def upload_video(self, video_path: str) -> str:
        """
        Uploads a video to Twitter using the v1.1 Chunked Media Upload protocol:
          1. INIT: Declare file size and media_type (video/mp4)
          2. APPEND: Upload video chunks (4MB segments)
          3. FINALIZE: Finalize upload and initiate async server-side processing
          4. STATUS: Poll processing state until 'succeeded'

        Returns:
            media_id_string (str) to attach to a tweet.
        """
        path = Path(video_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Video file not found at: {path}")

        total_bytes = path.stat().st_size
        print(f"📦 Step 1/4 (INIT): Registering video upload ({total_bytes / (1024 * 1024):.2f} MB)...")

        # 1. INIT
        init_data = {
            "command": "INIT",
            "total_bytes": str(total_bytes),
            "media_type": "video/mp4",
            "media_category": "tweet_video"
        }
        init_resp = requests.post(
            self.upload_base_url,
            data=init_data,
            auth=self._auth,
            timeout=30
        )
        if init_resp.status_code not in (200, 201, 202):
            raise RuntimeError(
                f"Failed to initialize video upload (HTTP {init_resp.status_code}): {init_resp.text}"
            )

        media_id = init_resp.json().get("media_id_string")
        if not media_id:
            raise RuntimeError(f"No media_id_string returned from INIT: {init_resp.text}")

        # 2. APPEND (Chunked upload)
        print(f"📤 Step 2/4 (APPEND): Uploading video chunks for media_id {media_id}...")
        segment_index = 0
        bytes_sent = 0

        with open(path, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break

                append_data = {
                    "command": "APPEND",
                    "media_id": media_id,
                    "segment_index": str(segment_index)
                }
                append_files = {
                    "media": chunk
                }

                append_resp = requests.post(
                    self.upload_base_url,
                    data=append_data,
                    files=append_files,
                    auth=self._auth,
                    timeout=60
                )
                if append_resp.status_code not in (200, 204):
                    raise RuntimeError(
                        f"Failed to upload segment {segment_index} (HTTP {append_resp.status_code}): {append_resp.text}"
                    )

                bytes_sent += len(chunk)
                progress_pct = (bytes_sent / total_bytes) * 100
                print(f"   Transferred segment {segment_index} ({progress_pct:.1f}% complete)")
                segment_index += 1

        # 3. FINALIZE
        print("⚙️ Step 3/4 (FINALIZE): Finalizing media upload...")
        finalize_data = {
            "command": "FINALIZE",
            "media_id": media_id
        }
        finalize_resp = requests.post(
            self.upload_base_url,
            data=finalize_data,
            auth=self._auth,
            timeout=30
        )
        if finalize_resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Failed to finalize video upload (HTTP {finalize_resp.status_code}): {finalize_resp.text}"
            )

        finalize_json = finalize_resp.json()
        processing_info = finalize_json.get("processing_info")

        # 4. STATUS Polling (if processing is async)
        if processing_info:
            print("⏳ Step 4/4 (STATUS): Awaiting video encoding and processing on X servers...")
            state = processing_info.get("state")
            while state in ("pending", "in_progress"):
                check_after = processing_info.get("check_after_secs", 5)
                print(f"   Encoding in progress ({state}). Checking in {check_after}s...")
                time.sleep(check_after)

                status_resp = requests.get(
                    self.upload_base_url,
                    params={"command": "STATUS", "media_id": media_id},
                    auth=self._auth,
                    timeout=30
                )
                if status_resp.status_code != 200:
                    raise RuntimeError(
                        f"Failed to query media processing status (HTTP {status_resp.status_code}): {status_resp.text}"
                    )

                status_json = status_resp.json()
                processing_info = status_json.get("processing_info", {})
                state = processing_info.get("state")

                if state == "failed":
                    err_msg = processing_info.get("error", {}).get("message", "Unknown video encoding error")
                    raise RuntimeError(f"X video processing failed: {err_msg}")

        print(f"✅ Video processing complete! Media ID ready: {media_id}")
        return media_id

    def post_tweet(
        self,
        text: str,
        media_id: Optional[str] = None,
        in_reply_to_tweet_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a single tweet or reply via X API v2 (POST /2/tweets).
        """
        url = f"{self.api_base_url}/2/tweets"
        payload: Dict[str, Any] = {"text": text}

        if media_id:
            payload["media"] = {"media_ids": [media_id]}

        if in_reply_to_tweet_id:
            payload["reply"] = {"in_reply_to_tweet_id": in_reply_to_tweet_id}

        headers = {"Content-Type": "application/json"}
        resp = requests.post(
            url,
            json=payload,
            headers=headers,
            auth=self._auth,
            timeout=30
        )

        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Failed to post tweet (HTTP {resp.status_code}): {resp.text}")

        return resp.json().get("data", {})

    def post_thread(
        self,
        tweets: List[str],
        media_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Publishes an ordered list of tweets as a connected thread.
        Attaches media_id to the first tweet.
        Chains subsequent tweets using in_reply_to_tweet_id.

        Returns:
            List of tweet response objects with IDs.
        """
        if not tweets:
            raise ValueError("Cannot post an empty tweet list.")

        published_tweets: List[Dict[str, Any]] = []
        previous_tweet_id: Optional[str] = None

        for idx, tweet_text in enumerate(tweets):
            tweet_num = idx + 1
            print(f"🚀 Publishing Tweet {tweet_num}/{len(tweets)} ({calculate_tweet_length(tweet_text)}/280 chars)...")

            # Attach media to Tweet 1 only
            current_media_id = media_id if idx == 0 else None

            result = self.post_tweet(
                text=tweet_text,
                media_id=current_media_id,
                in_reply_to_tweet_id=previous_tweet_id
            )

            tweet_id = result.get("id")
            if not tweet_id:
                raise RuntimeError(f"Missing tweet ID in response: {result}")

            published_tweets.append(result)
            previous_tweet_id = tweet_id
            print(f"   ✅ Tweet {tweet_num} live: https://x.com/themodelverrse/status/{tweet_id}")

            # Brief pause between sequential replies to maintain chronological order
            if idx < len(tweets) - 1:
                time.sleep(2)

        return published_tweets

    def publish_video_thread(
        self,
        video_path: str,
        spec: Dict[str, Any],
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        End-to-end publishing pipeline:
          1. Generates 4-tweet thread from spec
          2. Uploads and encodes video via chunked upload
          3. Posts connected thread with video attached to Tweet 1
        """
        print("\n🧵 Generating 4-tweet technical thread for X...")
        tweets = generate_x_thread(spec, use_llm=use_llm)

        print("\n🎬 Uploading video asset to X media service...")
        media_id = self.upload_video(video_path)

        print("\n🚀 Broadcasting thread to X...")
        published_thread = self.post_thread(tweets, media_id=media_id)

        first_tweet_id = published_thread[0]["id"]
        thread_url = f"https://x.com/themodelverrse/status/{first_tweet_id}"

        print("\n=======================================================")
        print("🎉 X (TWITTER) BROADCAST COMPLETE!")
        print(f"🔗 Thread URL: {thread_url}")
        print(f"🧵 Total Tweets: {len(published_thread)}")
        print("=======================================================\n")

        return {
            "thread_url": thread_url,
            "root_tweet_id": first_tweet_id,
            "media_id": media_id,
            "tweets": published_thread
        }


# Singleton instance
x_publisher = XPublisher()


def main():
    parser = argparse.ArgumentParser(description="The Model Verse — Autonomous X (Twitter) Publisher")
    parser.add_argument("--video", help="Path to vertical MP4 video file to upload")
    parser.add_argument("--spec", help="Path to JSON specification file")
    parser.add_argument("--check-token", action="store_true", help="Verify credentials and account status")
    parser.add_argument("--dry-run", action="store_true", help="Generate thread and display preview without publishing")
    parser.add_argument("--no-llm", action="store_true", help="Bypass LLM and use deterministic thread heuristics")
    args = parser.parse_args()

    publisher = XPublisher()

    if args.check_token:
        print("🔍 Verifying Twitter / X credentials...")
        valid, info = publisher.check_token_validity()
        if valid:
            print("✅ Twitter / X credentials are VALID!")
            print(f"   User ID: {info.get('id')}")
            print(f"   Name: {info.get('name')}")
            print(f"   Username: @{info.get('username')}")
        else:
            print(f"❌ Token validation failed: {info}")
            sys.exit(1)
        return

    # Load specification
    spec: Dict[str, Any] = {}
    if args.spec and os.path.exists(args.spec):
        with open(args.spec, "r", encoding="utf-8") as f:
            spec = json.load(f)
    elif args.video:
        # Attempt to infer template from video filename
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
            "id": Path(args.video).stem if args.video else "ai_breakthrough",
            "beats": []
        }

    tweets = generate_x_thread(spec, use_llm=not args.no_llm)

    if args.dry_run or not args.video:
        print("\n=======================================================")
        print("🔍 X (TWITTER) THREAD PREVIEW (DRY-RUN)")
        print("=======================================================")
        for i, tweet_text in enumerate(tweets, 1):
            eff_len = calculate_tweet_length(tweet_text)
            media_indicator = " [📹 Attached Video]" if i == 1 and args.video else ""
            print(f"\n--- TWEET {i}/4 ({eff_len}/280 chars){media_indicator} ---")
            print(tweet_text)
        print("\n=======================================================\n")
        if not args.video:
            print("💡 Tip: Provide --video <path.mp4> to execute live publishing to X.")
        return

    # Live Publish
    publisher.publish_video_thread(
        video_path=args.video,
        spec=spec,
        use_llm=not args.no_llm
    )


if __name__ == "__main__":
    main()
