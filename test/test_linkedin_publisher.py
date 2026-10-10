"""
Unit & Integration Tests for LinkedIn Publisher and Copy Generator
Verifies:
  1. Algorithm optimization: zero outbound URLs in post commentary, external links in first comment
  2. Dwell-time hook generation and technical breakdown bullets
  3. OAuth 2.0 authorization URL and token exchange
  4. Member profile verification via /v2/userinfo and author URN resolution
  5. Multi-step video upload protocol (/rest/videos initialize -> PUT binary -> finalize -> poll status)
  6. Document carousel upload protocol (/rest/documents initialize -> PUT binary)
  7. Post creation and first comment injection via /rest/socialActions/...
  8. End-to-end publish workflows for videos and document carousels
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.linkedin_copy_generator import (
    build_fallback_linkedin_post,
    generate_linkedin_post,
    LINKEDIN_SYSTEM_PROMPT
)
from pipeline.linkedin_publisher import LinkedInPublisher


# =========================================================================
# FIXTURES
# =========================================================================

@pytest.fixture
def sample_spec():
    return {
        "id": "stepquant_recurrent_quantization",
        "title": "STEPQuant: Mastering Recurrent State Quantization",
        "category": "mechanism_deepdive",
        "arxiv_id": "2609.38169",
        "beats": [
            {
                "beat_id": 1,
                "text": "Linear attention models promise infinite context, but recurrent states become a memory bottleneck."
            },
            {
                "beat_id": 2,
                "text": "Uniform quantization treats all states equally, causing catastrophic accuracy degradation."
            },
            {
                "beat_id": 3,
                "text": "STEPQuant introduces sensitivity profiling across Delta-rule state updates over time."
            },
            {
                "beat_id": 4,
                "text": "By dynamically computing row-level scale factors, critical state updates stay bounded."
            },
            {
                "beat_id": 5,
                "text": "Achieves 4x VRAM compression while retaining full FP16 perplexity on long-context benchmarks."
            },
            {
                "beat_id": 6,
                "text": "Selective precision allocation is essential for sub-quadratic state spaces."
            }
        ]
    }


# =========================================================================
# 1. COPY GENERATOR & ALGORITHM OPTIMIZATION TESTS
# =========================================================================

def test_build_fallback_linkedin_post_zero_links_in_commentary(sample_spec):
    post = build_fallback_linkedin_post(sample_spec)

    assert "hook" in post
    assert "commentary" in post
    assert "first_comment" in post
    assert "hashtags" in post

    # Algorithm Rule: NO external URLs in post commentary (penalizes reach by 50-70%)
    commentary = post["commentary"]
    assert "http://" not in commentary
    assert "https://" not in commentary

    # Commentary must direct readers to comment section
    assert "comments below" in commentary.lower()

    # External links must live safely in first_comment
    first_comment = post["first_comment"]
    assert "https://arxiv.org/abs/2609.38169" in first_comment
    assert "https://themodelverse.in/models/stepquant_recurrent_quantization" in first_comment
    assert "?" in first_comment  # Socratic engagement question


def test_generate_linkedin_post_strips_urls_from_llm_response(sample_spec):
    mock_llm_json = json.dumps({
        "hook": "Why uniform quantization fails for recurrent states.",
        "commentary": "Here is the breakdown: Check out https://arxiv.org/abs/2609.38169 and read more.",
        "first_comment": "Read the paper at https://arxiv.org/abs/2609.38169. What are your thoughts?",
        "hashtags": ["#ML", "#LLMs"]
    })

    with patch("pipeline.llm_router.llm_router.generate_text_with_cascade", return_value=mock_llm_json):
        post = generate_linkedin_post(sample_spec, use_llm=True)

        assert "http://" not in post["commentary"]
        assert "https://" not in post["commentary"]
        assert "comments below" in post["commentary"].lower()
        assert "https://arxiv.org/abs/2609.38169" in post["first_comment"]


def test_generate_linkedin_post_llm_fallback(sample_spec):
    with patch("pipeline.llm_router.llm_router.generate_text_with_cascade", side_effect=Exception("Rate limit")):
        post = generate_linkedin_post(sample_spec, use_llm=True)

        assert post is not None
        assert "hook" in post
        assert "commentary" in post
        assert "first_comment" in post
        assert "http" not in post["commentary"]


# =========================================================================
# 2. OAUTH & MEMBER IDENTITY TESTS
# =========================================================================

def test_get_authorization_url():
    pub = LinkedInPublisher(
        client_id="test_client_id_123",
        client_secret="test_client_secret_456",
        redirect_uri="http://localhost:8080/callback"
    )

    url = pub.get_authorization_url()
    assert "https://www.linkedin.com/oauth/v2/authorization" in url
    assert "client_id=test_client_id_123" in url
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A8080%2Fcallback" in url
    assert "w_member_social" in url


def test_get_authorization_url_missing_client_id():
    pub = LinkedInPublisher(client_id="", client_secret="")
    with pytest.raises(ValueError, match="LINKEDIN_CLIENT_ID is required"):
        pub.get_authorization_url()


def test_exchange_code_for_token():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        temp_token_path = tf.name

    try:
        pub = LinkedInPublisher(
            client_id="test_cid",
            client_secret="test_sec",
            redirect_uri="http://localhost:8080/callback",
            token_path=temp_token_path
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "AQX_mock_access_token_abc123",
            "expires_in": 5184000
        }

        with patch("requests.post", return_value=mock_resp):
            token = pub.exchange_code_for_token("auth_code_xyz")
            assert token == "AQX_mock_access_token_abc123"
            assert pub.access_token == "AQX_mock_access_token_abc123"

        # Check saved token file
        with open(temp_token_path, "r", encoding="utf-8") as f:
            saved = json.load(f)
            assert saved.get("access_token") == "AQX_mock_access_token_abc123"
    finally:
        if os.path.exists(temp_token_path):
            os.remove(temp_token_path)


def test_check_token_validity_and_author_urn():
    pub = LinkedInPublisher(access_token="mock_valid_token")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "sub": "abc123xyz789",
        "name": "The Model Verse Lead",
        "email": "lead@themodelverse.in"
    }

    with patch("requests.get", return_value=mock_resp):
        valid, info = pub.check_token_validity()
        assert valid is True
        assert info["sub"] == "abc123xyz789"
        assert pub.get_author_urn() == "urn:li:person:abc123xyz789"


def test_check_token_validity_unauthorized():
    pub = LinkedInPublisher(access_token="mock_expired_token")

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = '{"message": "Expired access token"}'

    with patch("requests.get", return_value=mock_resp):
        valid, info = pub.check_token_validity()
        assert valid is False
        assert info["status_code"] == 401

        with pytest.raises(RuntimeError, match="Token invalid or expired"):
            pub.get_author_urn()


# =========================================================================
# 3. VIDEO & DOCUMENT UPLOAD PROTOCOL TESTS
# =========================================================================

def test_upload_video_protocol():
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf:
        tf.write(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 1024)
        video_path = tf.name

    try:
        pub = LinkedInPublisher(access_token="mock_valid_token")

        init_resp = MagicMock()
        init_resp.status_code = 200
        init_resp.json.return_value = {
            "value": {
                "uploadUrl": "https://media.licdn.com/upload/video/abc",
                "video": "urn:li:video:123456789"
            }
        }

        put_resp = MagicMock()
        put_resp.status_code = 200

        finalize_resp = MagicMock()
        finalize_resp.status_code = 200

        status_resp = MagicMock()
        status_resp.status_code = 200
        status_resp.json.return_value = {
            "status": "AVAILABLE"
        }

        with patch("requests.post", side_effect=[init_resp, finalize_resp]), \
             patch("requests.put", return_value=put_resp), \
             patch("requests.get", return_value=status_resp), \
             patch("time.sleep", return_value=None):

            video_urn = pub.upload_video(video_path, author_urn="urn:li:person:author_123")
            assert video_urn == "urn:li:video:123456789"
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)


def test_upload_document_protocol():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        tf.write(b"%PDF-1.4\n" + b"\x00" * 512)
        doc_path = tf.name

    try:
        pub = LinkedInPublisher(access_token="mock_valid_token")

        init_resp = MagicMock()
        init_resp.status_code = 200
        init_resp.json.return_value = {
            "value": {
                "uploadUrl": "https://media.licdn.com/upload/document/doc123",
                "document": "urn:li:document:987654321"
            }
        }

        put_resp = MagicMock()
        put_resp.status_code = 200

        with patch("requests.post", return_value=init_resp), \
             patch("requests.put", return_value=put_resp):

            doc_urn = pub.upload_document(doc_path, author_urn="urn:li:person:author_123")
            assert doc_urn == "urn:li:document:987654321"
    finally:
        if os.path.exists(doc_path):
            os.remove(doc_path)


# =========================================================================
# 4. POST CREATION & COMMENT TESTS
# =========================================================================

def test_create_post():
    pub = LinkedInPublisher(access_token="mock_valid_token")

    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.headers = {"x-restli-id": "urn:li:share:1122334455"}

    with patch("requests.post", return_value=mock_resp) as mock_post:
        res = pub.create_post(
            commentary="Clean commentary without links",
            media_urn="urn:li:video:123456789",
            media_title="STEPQuant Video",
            author_urn="urn:li:person:author_123"
        )
        assert res["id"] == "urn:li:share:1122334455"
        assert res["status"] == "success"

        # Verify payload sent to /rest/posts
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["author"] == "urn:li:person:author_123"
        assert payload["commentary"] == "Clean commentary without links"
        assert payload["visibility"] == "PUBLIC"
        assert payload["content"]["media"]["id"] == "urn:li:video:123456789"


def test_create_comment():
    pub = LinkedInPublisher(access_token="mock_valid_token")

    mock_resp = MagicMock()
    mock_resp.status_code = 201

    with patch("requests.post", return_value=mock_resp) as mock_post:
        success = pub.create_comment(
            post_urn="urn:li:share:1122334455",
            comment_text="Paper link: https://arxiv.org/abs/2609.38169",
            author_urn="urn:li:person:author_123"
        )
        assert success is True

        call_args = mock_post.call_args
        url = call_args[0][0]
        assert "socialActions" in url
        # URN must be percent-encoded
        assert "urn%3Ali%3Ashare%3A1122334455" in url


# =========================================================================
# 5. END-TO-END PUBLISH WORKFLOW TESTS
# =========================================================================

def test_publish_video_e2e(sample_spec):
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf:
        tf.write(b"mp4dummy")
        video_path = tf.name

    try:
        pub = LinkedInPublisher(access_token="mock_valid_token")

        with patch.object(pub, "get_author_urn", return_value="urn:li:person:user_1"), \
             patch.object(pub, "upload_video", return_value="urn:li:video:video_99"), \
             patch.object(pub, "create_post", return_value={"id": "urn:li:share:post_88"}), \
             patch.object(pub, "create_comment", return_value=True) as mock_comment:

            result = pub.publish_video(video_path, sample_spec, use_llm=False)
            assert result["post_id"] == "urn:li:share:post_88"
            assert result["video_urn"] == "urn:li:video:video_99"
            mock_comment.assert_called_once()
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)


def test_publish_document_e2e(sample_spec):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        tf.write(b"pdfdummy")
        doc_path = tf.name

    try:
        pub = LinkedInPublisher(access_token="mock_valid_token")

        with patch.object(pub, "get_author_urn", return_value="urn:li:person:user_1"), \
             patch.object(pub, "upload_document", return_value="urn:li:document:doc_77"), \
             patch.object(pub, "create_post", return_value={"id": "urn:li:share:post_66"}), \
             patch.object(pub, "create_comment", return_value=True) as mock_comment:

            result = pub.publish_document(doc_path, sample_spec, use_llm=False)
            assert result["post_id"] == "urn:li:share:post_66"
            assert result["document_urn"] == "urn:li:document:doc_77"
            mock_comment.assert_called_once()
    finally:
        if os.path.exists(doc_path):
            os.remove(doc_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
