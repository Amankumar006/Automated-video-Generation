"""
Unit & Integration Tests for X (Twitter) Publisher and Thread Automation
Verifies:
  1. Effective character counting (23 chars per URL) and safe tweet truncation
  2. 4-tweet thread generation, formatting, and algorithm optimization (no links in Tweet 1)
  3. OAuth 1.0a configuration and user validation
  4. Resumable chunked video upload (INIT -> APPEND -> FINALIZE -> STATUS loop)
  5. Sequential thread posting with in_reply_to chaining
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.x_thread_generator import (
    calculate_tweet_length,
    truncate_to_tweet_limit,
    build_fallback_thread,
    generate_x_thread,
    TWITTER_MAX_CHARS,
    TWITTER_URL_LENGTH
)
from pipeline.x_publisher import XPublisher


# =========================================================================
# 1. CHARACTER COUNTING & TRUNCATION TESTS
# =========================================================================

def test_calculate_tweet_length_plain_text():
    text = "Hello world! This is a simple test tweet."
    assert calculate_tweet_length(text) == len(text)


def test_calculate_tweet_length_with_urls():
    # In Twitter, any URL counts as exactly 23 characters
    url_short = "https://t.co/xyz"
    url_long = "https://arxiv.org/abs/2609.38169?ref=themodelverse&source=social_feed_automation"

    text = f"Read the paper: {url_long}"
    # "Read the paper: " is 16 chars + 23 = 39 chars
    assert calculate_tweet_length(text) == 16 + TWITTER_URL_LENGTH

    text_two_urls = f"Link 1: {url_short} and Link 2: {url_long}"
    # "Link 1: " (8) + 23 + " and Link 2: " (13) + 23 = 67 chars
    assert calculate_tweet_length(text_two_urls) == 8 + 23 + 13 + 23


def test_truncate_to_tweet_limit_short_text():
    short = "This is well under the limit."
    assert truncate_to_tweet_limit(short, max_chars=280) == short


def test_truncate_to_tweet_limit_long_text():
    long_text = "Word " * 70  # ~350 chars
    truncated = truncate_to_tweet_limit(long_text, max_chars=280)
    assert calculate_tweet_length(truncated) <= 280
    assert truncated.endswith("...")


def test_truncate_to_tweet_limit_with_urls():
    long_text = ("Detail about model " * 15) + " https://arxiv.org/abs/2609.38169"
    truncated = truncate_to_tweet_limit(long_text, max_chars=280)
    assert calculate_tweet_length(truncated) <= 280


# =========================================================================
# 2. THREAD GENERATOR TESTS
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
                "text": "Linear attention models promise infinite context, but their recurrent states become a massive memory graveyard."
            },
            {
                "beat_id": 2,
                "text": "The villain is uniform quantization. It treats every state bit as equally vital, causing catastrophic accuracy drift."
            },
            {
                "beat_id": 3,
                "text": "STEPQuant pivots to sensitivity analysis, measuring how specific Delta-rule state rows impact final output error across time."
            },
            {
                "beat_id": 4,
                "text": "We assign high precision to long-lived rows, while jointly fitting key-row and value-column scales to minimize propagation error."
            },
            {
                "beat_id": 5,
                "text": "The result? 68.7% less memory usage, matching FP32 accuracy at 6 bits. It is pure, high-stakes efficiency."
            },
            {
                "beat_id": 6,
                "text": "Follow The Model Verse for daily deep-dives into how modern AI actually works under the hood."
            }
        ]
    }


def test_build_fallback_thread(sample_spec):
    tweets = build_fallback_thread(sample_spec)
    assert len(tweets) == 4

    # Tweet 1: Hook & Video Lead (Must NOT contain external URLs to protect reach)
    assert "https://" not in tweets[0]
    assert "http://" not in tweets[0]
    assert "🧵👇" in tweets[0]
    assert calculate_tweet_length(tweets[0]) <= 280

    # Tweet 2: Mechanism breakdown
    assert calculate_tweet_length(tweets[1]) <= 280

    # Tweet 3: Benchmarks & Impact
    assert calculate_tweet_length(tweets[2]) <= 280

    # Tweet 4: Sources & CTA
    assert "arxiv.org" in tweets[3]
    assert "@themodelverrse" in tweets[3]
    assert calculate_tweet_length(tweets[3]) <= 280


def test_generate_x_thread_with_llm_fallback(sample_spec):
    # Test when LLM returns None, fallback thread is cleanly returned
    with patch("pipeline.x_thread_generator.llm_router.generate_text_with_cascade", return_value=None):
        tweets = generate_x_thread(sample_spec, use_llm=True)
        assert len(tweets) == 4
        for tw in tweets:
            assert calculate_tweet_length(tw) <= 280


def test_generate_x_thread_with_valid_llm_json(sample_spec):
    fake_json = (
        '{"tweets": ['
        '"Linear attention is broken at scale. Memory fills up instantly. Watch below 🧵👇",'
        '"STEPQuant replaces uniform quant with sensitivity profiling across state rows.",'
        '"68.7% VRAM reduction with zero perplexity loss at 6-bit precision.",'
        '"Paper: https://arxiv.org/abs/2609.38169 Follow @themodelverrse for more."'
        ']}'
    )
    with patch("pipeline.x_thread_generator.llm_router.generate_text_with_cascade", return_value=fake_json):
        tweets = generate_x_thread(sample_spec, use_llm=True)
        assert len(tweets) == 4
        assert "Linear attention is broken" in tweets[0]
        assert "🧵👇" in tweets[0]
        assert "68.7% VRAM" in tweets[2]
        for tw in tweets:
            assert calculate_tweet_length(tw) <= 280


# =========================================================================
# 3. X PUBLISHER CLIENT & TOKEN VERIFICATION TESTS
# =========================================================================

def test_x_publisher_configuration():
    pub = XPublisher(
        api_key="test_key",
        api_secret="test_secret",
        access_token="test_token",
        access_token_secret="test_token_secret"
    )
    assert pub.is_configured is True

    pub_empty = XPublisher(api_key="", api_secret="", access_token="", access_token_secret="")
    assert pub_empty.is_configured is False


def test_x_publisher_check_token_validity_success():
    pub = XPublisher(
        api_key="test_key",
        api_secret="test_secret",
        access_token="test_token",
        access_token_secret="test_token_secret"
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": {
            "id": "123456789",
            "name": "Themodelverse",
            "username": "themodelverrse"
        }
    }

    with patch("requests.get", return_value=mock_resp):
        valid, info = pub.check_token_validity()
        assert valid is True
        assert info["username"] == "themodelverrse"
        assert info["id"] == "123456789"


def test_x_publisher_check_token_validity_unauthorized():
    pub = XPublisher(
        api_key="test_key",
        api_secret="test_secret",
        access_token="test_token",
        access_token_secret="test_token_secret"
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = "Unauthorized"

    with patch("requests.get", return_value=mock_resp):
        valid, info = pub.check_token_validity()
        assert valid is False
        assert info["status_code"] == 401


# =========================================================================
# 4. CHUNKED VIDEO UPLOAD TESTS
# =========================================================================

def test_x_publisher_upload_video():
    pub = XPublisher(
        api_key="test_key",
        api_secret="test_secret",
        access_token="test_token",
        access_token_secret="test_token_secret"
    )

    # Create temporary video file (100 KB)
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
        tmp_file.write(b"\x00" * 102400)
        tmp_path = tmp_file.name

    try:
        # Mock INIT response
        init_mock = MagicMock()
        init_mock.status_code = 202
        init_mock.json.return_value = {"media_id_string": "media_987654321"}

        # Mock APPEND response
        append_mock = MagicMock()
        append_mock.status_code = 204

        # Mock FINALIZE response with async processing
        finalize_mock = MagicMock()
        finalize_mock.status_code = 201
        finalize_mock.json.return_value = {
            "media_id_string": "media_987654321",
            "processing_info": {
                "state": "pending",
                "check_after_secs": 1
            }
        }

        # Mock STATUS response (succeeded)
        status_mock = MagicMock()
        status_mock.status_code = 200
        status_mock.json.return_value = {
            "processing_info": {
                "state": "succeeded"
            }
        }

        with patch("requests.post", side_effect=[init_mock, append_mock, finalize_mock]) as mock_post, \
             patch("requests.get", return_value=status_mock) as mock_get, \
             patch("time.sleep", return_value=None):

            media_id = pub.upload_video(tmp_path)
            assert media_id == "media_987654321"
            assert mock_post.call_count == 3
            assert mock_get.call_count == 1

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# =========================================================================
# 5. THREAD POSTING & REPLY CHAINING TESTS
# =========================================================================

def test_x_publisher_post_thread():
    pub = XPublisher(
        api_key="test_key",
        api_secret="test_secret",
        access_token="test_token",
        access_token_secret="test_token_secret"
    )

    tweets = [
        "Tweet 1: High curiosity hook 🧵👇",
        "Tweet 2: Architecture breakdown",
        "Tweet 3: Benchmarks and speedups",
        "Tweet 4: Paper links and follow CTA"
    ]

    # Track posted payloads
    posted_payloads = []

    def mock_post_impl(url, json=None, headers=None, auth=None, timeout=None):
        resp = MagicMock()
        resp.status_code = 201
        posted_payloads.append(json)
        tweet_id = f"tweet_id_{len(posted_payloads)}"
        resp.json.return_value = {"data": {"id": tweet_id, "text": json.get("text")}}
        return resp

    with patch("requests.post", side_effect=mock_post_impl), \
         patch("time.sleep", return_value=None):

        published = pub.post_thread(tweets, media_id="media_12345")

        assert len(published) == 4
        assert len(posted_payloads) == 4

        # Tweet 1 has media attached and no in_reply_to
        assert posted_payloads[0]["text"] == tweets[0]
        assert posted_payloads[0]["media"]["media_ids"] == ["media_12345"]
        assert "reply" not in posted_payloads[0]

        # Tweet 2 replies to Tweet 1
        assert posted_payloads[1]["text"] == tweets[1]
        assert posted_payloads[1]["reply"]["in_reply_to_tweet_id"] == "tweet_id_1"
        assert "media" not in posted_payloads[1]

        # Tweet 3 replies to Tweet 2
        assert posted_payloads[2]["reply"]["in_reply_to_tweet_id"] == "tweet_id_2"

        # Tweet 4 replies to Tweet 3
        assert posted_payloads[3]["reply"]["in_reply_to_tweet_id"] == "tweet_id_3"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
