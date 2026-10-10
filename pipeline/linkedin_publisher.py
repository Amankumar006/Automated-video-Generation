"""
The Model Verse — Autonomous LinkedIn Video & Carousel Publisher CLI
Publishes rendered vertical video shorts and PDF document carousels to LinkedIn
using OAuth 2.0 and the LinkedIn REST Posts API (/rest/posts, /rest/videos, /rest/documents).

Features:
  1. OAuth 2.0 3-legged authentication with automated local callback server
  2. Member profile verification via /v2/userinfo
  3. Native video upload protocol (/rest/videos initialize -> PUT binary -> finalize -> poll status)
  4. Native PDF document carousel upload protocol (/rest/documents initialize -> PUT binary)
  5. Post creation with dwell-time optimized hook and auto-posted first comment for links
  6. Dry-run preview and diagnostic token verification
"""

import os
import sys
import time
import json
import urllib.parse
import argparse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests

from pipeline.config import (
    LINKEDIN_CLIENT_ID,
    LINKEDIN_CLIENT_SECRET,
    LINKEDIN_ACCESS_TOKEN,
    LINKEDIN_REDIRECT_URI,
    LINKEDIN_TOKEN_PATH,
    LINKEDIN_API_VERSION,
    LINKEDIN_API_BASE_URL
)
from pipeline.linkedin_copy_generator import generate_linkedin_post


class LinkedInOAuthCallbackHandler(BaseHTTPRequestHandler):
    """Local HTTP callback listener to capture the OAuth authorization code."""

    auth_code: Optional[str] = None
    error: Optional[str] = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            LinkedInOAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <html>
            <body style="font-family: -apple-system, sans-serif; text-align: center; padding: 40px; background: #0A0D14; color: #10B981;">
                <h2>✅ LinkedIn Authorization Successful!</h2>
                <p style="color: #94A3B8;">You can close this tab and return to the terminal.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
        elif "error" in params:
            LinkedInOAuthCallbackHandler.error = params.get("error_description", ["Unknown error"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<h2>❌ Authorization Failed: {LinkedInOAuthCallbackHandler.error}</h2>".encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence local server request logging
        pass


class LinkedInPublisher:
    """Manages publishing of videos, document carousels, and posts to LinkedIn."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        token_path: Optional[str] = None,
        api_version: str = LINKEDIN_API_VERSION,
        api_base_url: str = LINKEDIN_API_BASE_URL
    ):
        self.client_id = client_id if client_id is not None else LINKEDIN_CLIENT_ID
        self.client_secret = client_secret if client_secret is not None else LINKEDIN_CLIENT_SECRET
        self.redirect_uri = redirect_uri if redirect_uri is not None else LINKEDIN_REDIRECT_URI
        self.token_path = token_path if token_path is not None else LINKEDIN_TOKEN_PATH
        self.api_version = api_version
        self.api_base_url = api_base_url.rstrip("/")

        # Load access token: constructor override -> saved token file -> env variable
        self.access_token = access_token or self._load_saved_token() or LINKEDIN_ACCESS_TOKEN

    def _load_saved_token(self) -> Optional[str]:
        """Loads access token from local JSON cache if present."""
        if self.token_path and os.path.exists(self.token_path):
            try:
                with open(self.token_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("access_token")
            except Exception:
                pass
        return None

    def _save_token(self, token_data: Dict[str, Any]):
        """Persists access token data to local JSON cache."""
        if not self.token_path:
            return
        os.makedirs(os.path.dirname(os.path.abspath(self.token_path)), exist_ok=True)
        with open(self.token_path, "w", encoding="utf-8") as f:
            json.dump(token_data, f, indent=2)
        print(f"✅ LinkedIn credentials saved to {self.token_path}")

    @property
    def is_configured(self) -> bool:
        """Returns True if client credentials or access token are configured."""
        return bool(self.access_token or (self.client_id and self.client_secret))

    def get_authorization_url(self) -> str:
        """Constructs the OAuth 2.0 3-legged authorization URL."""
        if not self.client_id:
            raise ValueError("LINKEDIN_CLIENT_ID is required to generate authorization URL.")

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid profile email w_member_social"
        }
        return f"https://www.linkedin.com/oauth/v2/authorization?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> str:
        """Exchanges an authorization code for a long-lived access token."""
        url = "https://www.linkedin.com/oauth/v2/accessToken"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        resp = requests.post(url, data=data, headers=headers, timeout=20)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to exchange code for access token (HTTP {resp.status_code}): {resp.text}")

        token_data = resp.json()
        self.access_token = token_data.get("access_token")
        self._save_token(token_data)
        return self.access_token

    def run_interactive_auth(self, port: int = 8080) -> str:
        """
        Runs local web server on port 8080 to capture the OAuth redirect and automatically save token.
        """
        auth_url = self.get_authorization_url()
        print("\n=======================================================")
        print("🔐 LINKEDIN OAUTH 2.0 AUTHORIZATION FLOW")
        print("=======================================================")
        print(f"Opening browser for authorization:\n{auth_url}\n")

        try:
            webbrowser.open(auth_url)
        except Exception:
            pass

        print(f"Waiting for authorization callback on {self.redirect_uri}...")
        server = HTTPServer(("localhost", port), LinkedInOAuthCallbackHandler)
        LinkedInOAuthCallbackHandler.auth_code = None
        LinkedInOAuthCallbackHandler.error = None

        while not LinkedInOAuthCallbackHandler.auth_code and not LinkedInOAuthCallbackHandler.error:
            server.handle_request()

        if LinkedInOAuthCallbackHandler.error:
            raise RuntimeError(f"LinkedIn authorization denied: {LinkedInOAuthCallbackHandler.error}")

        code = LinkedInOAuthCallbackHandler.auth_code
        print("✅ Authorization code received! Exchanging for access token...")
        token = self.exchange_code_for_token(code)
        print("🎉 Authentication successful!")
        return token

    def check_token_validity(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifies that the access token is valid and returns user profile info from /v2/userinfo.
        """
        if not self.access_token:
            return False, {"error": "LINKEDIN_ACCESS_TOKEN is not configured or authenticated."}

        url = "https://api.linkedin.com/v2/userinfo"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                return True, data
            else:
                return False, {
                    "status_code": resp.status_code,
                    "response": resp.text
                }
        except Exception as e:
            return False, {"error": str(e)}

    def get_author_urn(self) -> str:
        """Returns the member URN in the format urn:li:person:{sub}."""
        valid, info = self.check_token_validity()
        if not valid:
            raise RuntimeError(f"Cannot get author URN: Token invalid or expired ({info})")

        sub = info.get("sub")
        if not sub:
            raise RuntimeError(f"Missing 'sub' field in userinfo response: {info}")

        return f"urn:li:person:{sub}"

    def upload_video(self, video_path: str, author_urn: Optional[str] = None) -> str:
        """
        Uploads a video to LinkedIn via the Videos API:
          1. Initialize upload via /rest/videos?action=initializeUpload
          2. PUT binary data to uploadUrl
          3. Finalize upload via /rest/videos?action=finalizeUpload
          4. Poll status until 'AVAILABLE'
        """
        path = Path(video_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Video file not found at: {path}")

        author = author_urn or self.get_author_urn()
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "LinkedIn-Version": self.api_version,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }

        # 1. Initialize Upload
        print(f"📦 Step 1/4: Initializing LinkedIn video upload ({path.stat().st_size / (1024 * 1024):.2f} MB)...")
        init_url = f"{self.api_base_url}/rest/videos?action=initializeUpload"
        init_body = {
            "initializeUploadRequest": {
                "owner": author
            }
        }
        init_resp = requests.post(init_url, json=init_body, headers=headers, timeout=30)
        if init_resp.status_code not in (200, 201):
            raise RuntimeError(f"Failed to initialize video upload (HTTP {init_resp.status_code}): {init_resp.text}")

        init_data = init_resp.json().get("value", {})
        upload_url = init_data.get("uploadUrl")
        video_urn = init_data.get("video")
        if not upload_url or not video_urn:
            raise RuntimeError(f"Missing uploadUrl or video URN in response: {init_resp.text}")

        # 2. Binary Upload
        print(f"📤 Step 2/4: Streaming video binary to LinkedIn storage...")
        with open(path, "rb") as f:
            video_bytes = f.read()

        upload_resp = requests.put(
            upload_url,
            data=video_bytes,
            headers={"Content-Type": "application/octet-stream"},
            timeout=180
        )
        if upload_resp.status_code not in (200, 201, 204):
            raise RuntimeError(f"Failed to stream video bytes (HTTP {upload_resp.status_code}): {upload_resp.text}")

        # 3. Finalize Upload
        print("⚙️ Step 3/4: Finalizing video upload...")
        finalize_url = f"{self.api_base_url}/rest/videos?action=finalizeUpload"
        finalize_body = {
            "finalizeUploadRequest": {
                "video": video_urn,
                "uploadToken": ""
            }
        }
        finalize_resp = requests.post(finalize_url, json=finalize_body, headers=headers, timeout=30)
        if finalize_resp.status_code not in (200, 201):
            raise RuntimeError(f"Failed to finalize video upload (HTTP {finalize_resp.status_code}): {finalize_resp.text}")

        # 4. Poll Video Status
        print("⏳ Step 4/4: Waiting for LinkedIn server video processing...")
        video_id = video_urn.split(":")[-1]
        status_url = f"{self.api_base_url}/rest/videos/{video_id}"

        for attempt in range(12):
            time.sleep(3)
            status_resp = requests.get(status_url, headers=headers, timeout=15)
            if status_resp.status_code == 200:
                stat_data = status_resp.json()
                status = stat_data.get("status")
                if status == "AVAILABLE":
                    print(f"✅ Video processing complete! Video URN: {video_urn}")
                    return video_urn
                elif status == "PROCESSING_FAILED":
                    raise RuntimeError(f"LinkedIn video processing failed: {stat_data}")
            print(f"   Processing in progress (attempt {attempt+1}/12)...")

        print(f"ℹ️ Status polling reached timeout; proceeding with video URN: {video_urn}")
        return video_urn

    def upload_document(self, document_path: str, author_urn: Optional[str] = None) -> str:
        """
        Uploads a PDF document (carousel) to LinkedIn via the Documents API:
          1. Initialize upload via /rest/documents?action=initializeUpload
          2. PUT binary PDF to uploadUrl
          Returns document URN (e.g. urn:li:document:...)
        """
        path = Path(document_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Document file not found at: {path}")

        author = author_urn or self.get_author_urn()
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "LinkedIn-Version": self.api_version,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }

        # 1. Initialize Document Upload
        print(f"📦 Step 1/2: Initializing LinkedIn document upload ({path.stat().st_size / 1024:.1f} KB)...")
        init_url = f"{self.api_base_url}/rest/documents?action=initializeUpload"
        init_body = {
            "initializeUploadRequest": {
                "owner": author
            }
        }
        init_resp = requests.post(init_url, json=init_body, headers=headers, timeout=30)
        if init_resp.status_code not in (200, 201):
            raise RuntimeError(f"Failed to initialize document upload (HTTP {init_resp.status_code}): {init_resp.text}")

        init_data = init_resp.json().get("value", {})
        upload_url = init_data.get("uploadUrl")
        document_urn = init_data.get("document")
        if not upload_url or not document_urn:
            raise RuntimeError(f"Missing uploadUrl or document URN in response: {init_resp.text}")

        # 2. Upload Binary PDF
        print(f"📤 Step 2/2: Streaming PDF carousel to LinkedIn storage...")
        with open(path, "rb") as f:
            pdf_bytes = f.read()

        upload_resp = requests.put(
            upload_url,
            data=pdf_bytes,
            headers={"Content-Type": "application/pdf"},
            timeout=60
        )
        if upload_resp.status_code not in (200, 201, 204):
            raise RuntimeError(f"Failed to upload document binary (HTTP {upload_resp.status_code}): {upload_resp.text}")

        print(f"✅ Document upload complete! Document URN: {document_urn}")
        return document_urn

    def create_post(
        self,
        commentary: str,
        media_urn: Optional[str] = None,
        media_title: Optional[str] = None,
        author_urn: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a post via the Posts API (/rest/posts).
        """
        author = author_urn or self.get_author_urn()
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "LinkedIn-Version": self.api_version,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }

        payload: Dict[str, Any] = {
            "author": author,
            "commentary": commentary,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "lifecycleState": "PUBLISHED"
        }

        if media_urn:
            media_item: Dict[str, Any] = {"id": media_urn}
            if media_title:
                media_item["title"] = media_title
            payload["content"] = {"media": media_item}

        post_url = f"{self.api_base_url}/rest/posts"
        resp = requests.post(post_url, json=payload, headers=headers, timeout=30)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Failed to create LinkedIn post (HTTP {resp.status_code}): {resp.text}")

        post_id = resp.headers.get("x-restli-id") or resp.headers.get("X-LinkedIn-Id") or "created"
        return {"id": post_id, "status": "success"}

    def create_comment(self, post_urn: str, comment_text: str, author_urn: Optional[str] = None) -> bool:
        """
        Adds a first comment to the post to share external links without suffering post-reach penalty.
        """
        if not comment_text or not post_urn or post_urn == "created":
            return False

        author = author_urn or self.get_author_urn()
        encoded_urn = urllib.parse.quote(post_urn, safe="")
        url = f"{self.api_base_url}/rest/socialActions/{encoded_urn}/comments"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "LinkedIn-Version": self.api_version,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }
        body = {
            "actor": author,
            "message": {
                "text": comment_text
            }
        }
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=15)
            if resp.status_code in (200, 201):
                print("💬 First comment successfully published with paper & platform links!")
                return True
        except Exception as e:
            print(f"ℹ️ Note: Auto-comment skipped ({e}). Links remain accessible in the first comment draft.")
        return False

    def publish_video(
        self,
        video_path: str,
        spec: Dict[str, Any],
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        Publishes a video short with algorithm-optimized post copy and first-comment links.
        """
        print("\n📝 Step 1/3: Crafting LinkedIn post copy & first comment...")
        post_data = generate_linkedin_post(spec, use_llm=use_llm)

        print("\n🎬 Step 2/3: Uploading vertical video to LinkedIn...")
        author_urn = self.get_author_urn()
        video_urn = self.upload_video(video_path, author_urn=author_urn)

        print("\n🚀 Step 3/3: Publishing post to LinkedIn main feed...")
        title = spec.get("title", "AI Architecture Deep Dive")
        post_res = self.create_post(
            commentary=post_data["commentary"],
            media_urn=video_urn,
            media_title=title,
            author_urn=author_urn
        )

        post_id = post_res.get("id")
        if post_id and post_id != "created":
            self.create_comment(post_id, post_data["first_comment"], author_urn=author_urn)

        print("\n=======================================================")
        print("🎉 LINKEDIN VIDEO POST PUBLISHED!")
        print(f"🆔 Post ID: {post_id}")
        print("=======================================================\n")

        return {
            "post_id": post_id,
            "video_urn": video_urn,
            "post_data": post_data
        }

    def publish_document(
        self,
        document_path: str,
        spec: Dict[str, Any],
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        Publishes a PDF document carousel with algorithm-optimized post copy and first-comment links.
        """
        print("\n📝 Step 1/3: Crafting LinkedIn post copy & first comment...")
        post_data = generate_linkedin_post(spec, use_llm=use_llm)

        print("\n📄 Step 2/3: Uploading PDF document carousel to LinkedIn...")
        author_urn = self.get_author_urn()
        doc_urn = self.upload_document(document_path, author_urn=author_urn)

        print("\n🚀 Step 3/3: Publishing document carousel to LinkedIn main feed...")
        title = spec.get("title", "AI Architecture Deep Dive")
        post_res = self.create_post(
            commentary=post_data["commentary"],
            media_urn=doc_urn,
            media_title=title,
            author_urn=author_urn
        )

        post_id = post_res.get("id")
        if post_id and post_id != "created":
            self.create_comment(post_id, post_data["first_comment"], author_urn=author_urn)

        print("\n=======================================================")
        print("🎉 LINKEDIN DOCUMENT CAROUSEL PUBLISHED!")
        print(f"🆔 Post ID: {post_id}")
        print("=======================================================\n")

        return {
            "post_id": post_id,
            "document_urn": doc_urn,
            "post_data": post_data
        }


# Singleton instance
linkedin_publisher = LinkedInPublisher()


def main():
    parser = argparse.ArgumentParser(description="The Model Verse — LinkedIn Publisher CLI")
    parser.add_argument("--auth", action="store_true", help="Run interactive browser OAuth 2.0 flow to obtain access token")
    parser.add_argument("--check-token", action="store_true", help="Verify access token and display member profile")
    parser.add_argument("--video", help="Path to MP4 vertical video to publish")
    parser.add_argument("--document", help="Path to PDF document carousel to publish")
    parser.add_argument("--spec", help="Path to specification JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Preview post commentary and first comment without uploading")
    parser.add_argument("--no-llm", action="store_true", help="Use deterministic copy generation instead of LLM")
    args = parser.parse_args()

    publisher = LinkedInPublisher()

    if args.auth:
        publisher.run_interactive_auth()
        return

    if args.check_token:
        print("🔍 Verifying LinkedIn credentials...")
        valid, info = publisher.check_token_validity()
        if valid:
            print("✅ LinkedIn credentials are VALID!")
            print(f"   Member ID: {info.get('sub')}")
            print(f"   Name: {info.get('name')}")
            print(f"   Email: {info.get('email')}")
            print(f"   Author URN: urn:li:person:{info.get('sub')}")
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

    post_data = generate_linkedin_post(spec, use_llm=not args.no_llm)

    if args.dry_run or (not args.video and not args.document):
        print("\n=======================================================")
        print("🔍 LINKEDIN POST PREVIEW (DRY-RUN)")
        print("=======================================================")
        print(f"🪝 HOOK:\n{post_data['hook']}\n")
        print(f"📝 COMMENTARY:\n{post_data['commentary']}\n")
        print(f"💬 FIRST COMMENT (WITH EXTERNAL LINKS):\n{post_data['first_comment']}\n")
        print("=======================================================\n")
        if not args.video and not args.document:
            print("💡 Tip: Provide --video <path.mp4> or --document <path.pdf> to publish.")
        return

    # Live Publish
    if args.video:
        publisher.publish_video(args.video, spec, use_llm=not args.no_llm)
    elif args.document:
        publisher.publish_document(args.document, spec, use_llm=not args.no_llm)


if __name__ == "__main__":
    main()
