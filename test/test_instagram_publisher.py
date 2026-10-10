"""
The Model Verse — Comprehensive Unit & Integration Tests for Instagram Publisher
Tests caption generation, prompt formatting, markdown stripping, Meta Graph API v21.0
container management, resumable Reels video uploads, status polling, and error handling.
"""

import os
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.instagram_caption_generator import (
    strip_markdown_bold,
    extract_template_variables_from_spec,
    generate_fallback_caption,
    generate_instagram_post,
    format_full_caption_with_hashtags
)
from pipeline.instagram_publisher import InstagramPublisher


class TestInstagramCaptionGenerator(unittest.TestCase):
    """Tests for Instagram caption generation and prompt engineering rules."""

    def setUp(self):
        self.sample_spec = {
            "title": "STEPQuant: Mastering Recurrent State Quantization",
            "category": "mechanism_deepdive",
            "metadata": {
                "model_name": "STEPQuant",
                "provider": "Open-Source AI Lab",
                "top_benchmarks": [
                    {"name": "Serving Memory", "score_a": "68.7% less"},
                    {"name": "Accuracy", "score_a": "FP32 Matched"}
                ],
                "pricing": "68.7% GPU Memory Saved",
                "key_highlights": "Dynamic bit-depth allocation across recurrent state matrices"
            },
            "beats": [
                {"beat_id": 1, "text": "Linear attention models choke server memory."},
                {"beat_id": 5, "text": "Results show 68.7% memory cut with zero accuracy drop."}
            ]
        }

    def test_strip_markdown_bold(self):
        """Verifies markdown asterisks (**) are completely removed from caption text."""
        raw = "Here is **bold header** and another **bold metric: 70.3%**."
        cleaned = strip_markdown_bold(raw)
        self.assertNotIn("**", cleaned)
        self.assertEqual(cleaned, "Here is bold header and another bold metric: 70.3%.")

    def test_extract_template_variables(self):
        """Verifies extraction and formatting of template variables from spec dictionary."""
        vars_dict = extract_template_variables_from_spec(self.sample_spec)
        self.assertEqual(vars_dict["model_name"], "STEPQuant")
        self.assertEqual(vars_dict["provider"], "Open-Source AI Lab")
        self.assertIn("Serving Memory: 68.7% less", vars_dict["top_benchmarks"])
        self.assertIn("Accuracy: FP32 Matched", vars_dict["top_benchmarks"])
        self.assertIn("themodelverse.in", vars_dict["model_url"])

    def test_generate_fallback_caption(self):
        """Verifies deterministic fallback adheres to all 6 Instagram Posting Rules."""
        vars_dict = extract_template_variables_from_spec(self.sample_spec)
        post = generate_fallback_caption(vars_dict)

        # Check required schema keys
        self.assertIn("hook", post)
        self.assertIn("caption", post)
        self.assertIn("hashtags", post)
        self.assertIn("first_comment", post)
        self.assertIn("alt_text", post)

        # Check rules compliance
        self.assertNotIn("**", post["caption"])
        self.assertNotIn("**", post["first_comment"])
        self.assertIn("THE TAKEAWAY", post["caption"])
        self.assertIn("link in bio", post["caption"].lower())

        # Check hashtags
        hashtags = post["hashtags"].split()
        self.assertGreaterEqual(len(hashtags), 12)
        self.assertTrue(all(h.startswith("#") for h in hashtags))

    @patch("pipeline.instagram_caption_generator.llm_router.generate_text_with_cascade")
    def test_generate_instagram_post_with_mock_llm(self, mock_cascade):
        """Verifies LLM cascade response parsing and post sanitization."""
        mock_response = json.dumps({
            "hook": "Anthropic dropped Claude 3.7 Sonnet.",
            "caption": "Anthropic introduced **Claude 3.7 Sonnet** with **SWE-bench: 70.3%**.",
            "hashtags": "#TheModelverse #AI #LLM #MachineLearning #TechNews",
            "first_comment": "Check **themodelverse.in** for details!",
            "alt_text": "Claude 3.7 Sonnet model card."
        })
        mock_cascade.return_value = mock_response

        post = generate_instagram_post(self.sample_spec)
        self.assertEqual(post["hook"], "Anthropic dropped Claude 3.7 Sonnet.")
        # Bold asterisks must be stripped
        self.assertNotIn("**", post["caption"])
        self.assertNotIn("**", post["first_comment"])
        self.assertEqual(post["caption"], "Anthropic introduced Claude 3.7 Sonnet with SWE-bench: 70.3%.")

    def test_format_full_caption_with_hashtags(self):
        """Verifies caption payload formatting with spacing dots and hashtags."""
        post = {
            "caption": "Main caption text here.",
            "hashtags": "#Tag1 #Tag2 #Tag3"
        }
        full = format_full_caption_with_hashtags(post)
        self.assertIn("Main caption text here.", full)
        self.assertIn(".\n.\n.", full)
        self.assertIn("#Tag1 #Tag2 #Tag3", full)


class TestInstagramPublisher(unittest.TestCase):
    """Tests for Meta Graph API v21.0 container management and Reels uploading."""

    def setUp(self):
        self.publisher = InstagramPublisher(
            account_id="17841425926885618",
            access_token="test_mock_access_token_12345"
        )
        self.test_video_path = Path(__file__).resolve().parent / "test_scratch_video.mp4"
        with open(self.test_video_path, "wb") as f:
            f.write(b"\x00" * 1024)  # 1KB dummy mp4

    def tearDown(self):
        if self.test_video_path.exists():
            self.test_video_path.unlink()

    @patch("urllib.request.urlopen")
    def test_check_token_validity_success(self, mock_urlopen):
        """Verifies token verification returns True on successful API call."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "id": "17841425926885618",
            "username": "themodelverse",
            "name": "The Model Verse"
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        is_valid, info = self.publisher.check_token_validity()
        self.assertTrue(is_valid)
        self.assertEqual(info["username"], "themodelverse")

    @patch("urllib.request.urlopen")
    def test_create_image_container(self, mock_urlopen):
        """Verifies image container creation returns container creation ID."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"id": "17928374620194821"}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        cid = self.publisher.create_image_container(
            image_url="https://themodelverse.in/image.png",
            caption="Test Caption"
        )
        self.assertEqual(cid, "17928374620194821")

    @patch("urllib.request.urlopen")
    def test_create_resumable_reels_container(self, mock_urlopen):
        """Verifies resumable Reels container initialization returns ID and upload URI."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "id": "17928374620194821",
            "uri": "https://rupload.facebook.com/ig-video-upload/v21.0/17928374620194821"
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        cid, uri = self.publisher.create_resumable_reels_container(
            video_path=str(self.test_video_path),
            caption="Test Reels Caption"
        )
        self.assertEqual(cid, "17928374620194821")
        self.assertIn("rupload.facebook.com", uri)

    @patch("urllib.request.urlopen")
    def test_upload_binary_video_stream(self, mock_urlopen):
        """Verifies streaming local file bytes to rupload endpoint."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"success": True}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        self.publisher.upload_binary_video_stream(
            upload_uri="https://rupload.facebook.com/ig-video-upload/v21.0/123",
            video_path=str(self.test_video_path)
        )
        self.assertTrue(mock_urlopen.called)

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_wait_for_container_ready(self, mock_urlopen, mock_sleep):
        """Verifies status polling loop succeeds when status_code reaches FINISHED."""
        mock_resp1 = MagicMock()
        mock_resp1.read.return_value = json.dumps({"status_code": "IN_PROGRESS"}).encode("utf-8")
        mock_resp2 = MagicMock()
        mock_resp2.read.return_value = json.dumps({"status_code": "FINISHED"}).encode("utf-8")

        mock_urlopen.return_value.__enter__.side_effect = [mock_resp1, mock_resp2]

        ready = self.publisher.wait_for_container_ready(container_id="17928374620194821", poll_interval=1)
        self.assertTrue(ready)

    @patch("urllib.request.urlopen")
    def test_publish_container(self, mock_urlopen):
        """Verifies media container publishing returns published media ID."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"id": "17928374620194899"}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        mid = self.publisher.publish_container(container_id="17928374620194821")
        self.assertEqual(mid, "17928374620194899")

    @patch("urllib.request.urlopen")
    def test_post_first_comment(self, mock_urlopen):
        """Verifies first comment posting to published post."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"id": "17928374620199999"}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        cid = self.publisher.post_first_comment(
            media_id="17928374620194899",
            comment_text="First engagement comment!"
        )
        self.assertEqual(cid, "17928374620199999")

    @patch.object(InstagramPublisher, "create_resumable_reels_container")
    @patch.object(InstagramPublisher, "upload_binary_video_stream")
    @patch.object(InstagramPublisher, "wait_for_container_ready")
    @patch.object(InstagramPublisher, "publish_container")
    @patch.object(InstagramPublisher, "post_first_comment")
    def test_full_publish_reel(
        self,
        mock_comment,
        mock_publish,
        mock_wait,
        mock_upload,
        mock_create
    ):
        """Verifies end-to-end execution of publish_reel method."""
        mock_create.return_value = ("cid_123", "https://rupload.facebook.com/uri")
        mock_wait.return_value = True
        mock_publish.return_value = "mid_456"
        mock_comment.return_value = "comm_789"

        post_data = {
            "hook": "Test hook",
            "caption": "Test caption",
            "hashtags": "#test",
            "first_comment": "Test comment"
        }

        res = self.publisher.publish_reel(str(self.test_video_path), post_data)
        self.assertEqual(res["media_id"], "mid_456")
        self.assertEqual(res["permalink"], "https://www.instagram.com/p/mid_456/")
        self.assertTrue(mock_create.called)
        self.assertTrue(mock_upload.called)
        self.assertTrue(mock_wait.called)
        self.assertTrue(mock_publish.called)
        self.assertTrue(mock_comment.called)


if __name__ == "__main__":
    unittest.main()
