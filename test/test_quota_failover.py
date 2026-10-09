"""
Unit and Integration Tests for Autonomous API Quota Failover Engine:
- QuotaHealthTracker in-memory state tracking and error detection
- Resilient Cascading LLM Script Failover (Gemini -> Groq -> OpenRouter -> Ollama Cloud -> Fallback)
- Self-Healing Voice Failover (ElevenLabs / Sarvam -> Kokoro ONNX offline synthesis)
- Self-Healing Vision Failover (Gemini Vision -> Ollama Cloud Vision -> Deterministic Layout Solver)
- End-to-end pipeline dry-run verification
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pytest
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.quota_tracker import quota_tracker, is_quota_error, QuotaHealthTracker
from pipeline.llm_router import (
    LLMRouter,
    strip_thinking_tags,
    sanitize_markdown_json,
    enforce_script_schema,
    generate_deterministic_fallback_script
)
from pipeline.voice_engine import (
    UnifiedVoiceRouter,
    ElevenLabsVoiceProvider,
    SarvamVoiceProvider,
    VoiceQuotaExceededError,
    VoiceAuthError,
    SAMPLE_RATE
)
from pipeline.vlm_critic import VLMCritic
from pipeline.script_generator import generate_script


@pytest.fixture(autouse=True)
def reset_quota_tracker():
    """Ensure QuotaHealthTracker state is pristine for each test."""
    quota_tracker.reset()
    yield
    quota_tracker.reset()


# ==============================================================================
# 1. Quota Health Tracker Tests (Requirement R3)
# ==============================================================================

def test_quota_tracker_initial_health():
    """Verify newly queried providers are healthy by default."""
    assert quota_tracker.is_healthy("gemini") is True
    assert quota_tracker.is_healthy("elevenlabs") is True
    assert quota_tracker.is_healthy("sarvam") is True
    assert quota_tracker.is_healthy("ollama") is True
    assert quota_tracker.is_exhausted("gemini") is False


def test_quota_tracker_record_exhausted_and_skip():
    """Verify recording quota exhaustion immediately flips health state."""
    quota_tracker.record_exhausted("elevenlabs", "429 Too Many Requests")
    assert quota_tracker.is_healthy("elevenlabs") is False
    assert quota_tracker.is_exhausted("elevenlabs") is True

    status = quota_tracker.get_status("elevenlabs")
    assert status["exhausted"] is True
    assert "429" in status["reason"]
    assert status["failure_count"] == 1


def test_quota_tracker_record_success_resets():
    """Verify successful invocation resets exhaustion."""
    quota_tracker.record_exhausted("gemini", "ResourceExhausted")
    assert quota_tracker.is_healthy("gemini") is False

    quota_tracker.record_success("gemini")
    assert quota_tracker.is_healthy("gemini") is True
    assert quota_tracker.is_exhausted("gemini") is False


def test_is_quota_error_detection():
    """Verify robust recognition of quota exhaustion across varied HTTP codes and error strings."""
    assert is_quota_error(429) is True
    assert is_quota_error(402) is True
    assert is_quota_error(401) is True
    assert is_quota_error(500) is False

    assert is_quota_error("ResourceExhausted: 429 Resource has been exhausted") is True
    assert is_quota_error("Resource has been exhausted") is True
    assert is_quota_error("Resource exhausted") is True
    assert is_quota_error('{"status": "quota_exceeded", "detail": "Out of credits"}') is True
    assert is_quota_error("RateLimitError: rate limit reached for default tier") is True
    assert is_quota_error("429 Too Many Requests") is True
    assert is_quota_error("exceeded quota") is True
    assert is_quota_error("insufficient_quota") is True
    assert is_quota_error("billing_not_active") is True
    assert is_quota_error("Standard syntax error") is False

    # Exception class names
    class ResourceExhausted(Exception):
        pass

    class RateLimitError(Exception):
        pass

    assert is_quota_error(ResourceExhausted("Custom message without 429")) is True
    assert is_quota_error(RateLimitError("Too fast")) is True


# ==============================================================================
# 2. Resilient Cascading LLM Script Failover (Requirement R1)
# ==============================================================================

def test_script_generation_gemini_429_failover():
    """Verify simulated 429 / ResourceExhausted on Gemini immediately routes to secondary fallback."""
    router = LLMRouter()

    # Simulate Gemini failing with ResourceExhausted / 429
    with patch("google.generativeai.GenerativeModel") as mock_model_cls:
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = Exception("429 ResourceExhausted: Quota exceeded for project")
        mock_model_cls.return_value = mock_instance

        # Call script generation
        spec, provider = router.route_script_generation(
            prompt="Generate a 6-beat script on FlashAttention-3",
            topic="FlashAttention-3"
        )

        assert provider in ("groq", "openrouter", "ollama", "deterministic_fallback")
        assert quota_tracker.is_exhausted("gemini") is True

        # Verify Gemini is skipped on subsequent calls without making generate_content calls
        mock_instance.generate_content.reset_mock()
        spec2, provider2 = router.route_script_generation(
            prompt="Generate a 6-beat script on DeepSeek-R1",
            topic="DeepSeek-R1"
        )
        assert mock_instance.generate_content.call_count == 0
        assert provider2 in ("groq", "openrouter", "ollama", "deterministic_fallback")


def test_script_generation_absent_api_key_produces_valid_6beat_schema():
    """Verify script generation produces a valid 6-beat JSON schema when Gemini API key is absent."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}, clear=False):
        spec = generate_script(topic="Speculative Decoding")

        assert isinstance(spec, dict)
        assert spec.get("id") is not None
        assert spec.get("title") is not None
        assert spec.get("category") in [
            "architecture_breakdown", "model_showdown", "mechanism_deepdive", "benchmark_news"
        ]
        assert len(spec.get("beats", [])) == 6

        # Enforce all 6 beats have valid required fields
        for idx, beat in enumerate(spec["beats"], start=1):
            assert beat["beat_id"] == idx
            assert isinstance(beat.get("text"), str) and len(beat["text"]) > 0
            assert isinstance(beat.get("visual_focus"), str)
            assert isinstance(beat.get("highlight_words"), dict)
            assert isinstance(beat.get("svo_action"), dict)
            assert "subject" in beat["svo_action"]
            assert "action_verb" in beat["svo_action"]
            assert "anchor_word" in beat["svo_action"]
            assert isinstance(beat.get("visual_blueprint"), dict)
            assert "layout" in beat["visual_blueprint"]

        # Enforce exactly 5 math formulas (Beats 1 to 5)
        formulas = spec.get("math_formulas", [])
        assert len(formulas) == 5
        for f_idx, formula in enumerate(formulas, start=1):
            assert formula["beat_id"] == f_idx
            assert "latex" in formula and len(formula["latex"]) > 0
            assert "filename" in formula


def test_script_generation_strips_thinking_tags_and_markdown():
    """Verify thinking tags and markdown code blocks are thoroughly sanitized."""
    raw_llm_output = """<think>
    I should carefully structure this 6 beat short video on Mamba SSM.
    Let's make sure the hook is strong and the math is accurate.
    </think>
    ```json
    {
      "id": "mamba_ssm",
      "title": "Mamba State Space Models",
      "category": "mechanism_deepdive",
      "domain_taxonomy": "hardware_efficiency",
      "hook_tag": "MECHANISM DEEPDIVE",
      "beats": [
        {"beat_id": 1, "text": "Mamba breaks the quadratic context barrier.", "visual_focus": "Selective state space line"}
      ]
    }
    ```"""

    cleaned_json_str = sanitize_markdown_json(raw_llm_output)
    assert "<think>" not in cleaned_json_str
    assert "```json" not in cleaned_json_str

    parsed = json.loads(cleaned_json_str)
    enforced = enforce_script_schema(parsed, topic="Mamba SSM")

    assert len(enforced["beats"]) == 6
    assert "<think>" not in enforced["beats"][0]["text"]


# ==============================================================================
# 3. Self-Healing Voice Failovers (Requirement R2)
# ==============================================================================

def test_voice_engine_elevenlabs_quota_exceeded_failover_to_kokoro(tmp_path):
    """Verify voice engine produces full 24kHz audio via Kokoro fallback when ElevenLabs returns quota_exceeded."""
    router = UnifiedVoiceRouter(cache_dir=str(tmp_path))

    # Simulate ElevenLabs returning HTTP 401 with quota_exceeded body
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = json.dumps({
        "detail": {
            "type": "invalid_request",
            "code": "quota_exceeded",
            "message": "This request exceeds your quota of 10000. You have 0 credits remaining."
        }
    })

    with patch("requests.post", return_value=mock_resp):
        audio, sr, meta = router.synthesize_beat(
            text="FlashAttention-3 delivers a massive two point six times throughput leap.",
            voice="eric",
            provider="elevenlabs"
        )

        # Verification: Kokoro fallback was used
        assert sr == SAMPLE_RATE  # Must be 24000 Hz
        assert isinstance(audio, np.ndarray)
        assert len(audio) > 0
        assert np.isfinite(audio).all()
        assert audio.dtype == np.float32

        # Verification: Meta recorded fallback and ElevenLabs marked exhausted
        assert meta.get("fallback_from") == "elevenlabs"
        assert quota_tracker.is_exhausted("elevenlabs") is True


def test_voice_engine_skips_exhausted_elevenlabs_without_network_call(tmp_path):
    """Verify subsequent voice synthesis in same run immediately uses Kokoro without calling ElevenLabs."""
    router = UnifiedVoiceRouter(cache_dir=str(tmp_path))

    # Mark elevenlabs exhausted in QuotaTracker
    quota_tracker.record_exhausted("elevenlabs", "simulated 429")

    with patch("requests.post") as mock_post:
        audio, sr, meta = router.synthesize_beat(
            text="Second beat narration skipping exhausted provider immediately.",
            voice="eric",
            provider="elevenlabs"
        )

        # Requests should never have been made
        assert mock_post.call_count == 0
        assert sr == 24000
        assert meta["fallback_from"] == "elevenlabs"
        assert len(audio) > 0


def test_voice_engine_sarvam_quota_exceeded_failover(tmp_path):
    """Verify Sarvam AI Hindi synthesis cascades cleanly to Kokoro on 429."""
    router = UnifiedVoiceRouter(cache_dir=str(tmp_path))

    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.text = "429 Rate limit exceeded for Sarvam AI"

    with patch("requests.post", return_value=mock_resp):
        audio, sr, meta = router.synthesize_beat(
            text="यह मॉडल अत्यधिक कुशल है।",
            voice="shubh",
            language="hi",
            provider="sarvam"
        )

        assert sr == SAMPLE_RATE
        assert len(audio) > 0
        assert quota_tracker.is_exhausted("sarvam") is True
        assert meta["fallback_from"] == "sarvam"


# ==============================================================================
# 4. Self-Healing Vision Failovers (Requirement R2)
# ==============================================================================

def test_vlm_critic_gemini_vision_429_failover_produces_patches():
    """Verify VLM Critic detects quota exhaustion and produces valid evaluation report and layout patch proposals."""
    critic = VLMCritic()

    test_image = PROJECT_ROOT / "public" / "test_frame.png"
    if not test_image.exists():
        from PIL import Image
        img = Image.new("RGB", (1080, 1920), color=(10, 13, 20))
        img.save(test_image)

    dummy_spec = {
        "title": "Robotics Kinematics",
        "domain_taxonomy": "robotics_tamp",
        "beats": [
            {
                "beat_id": 1,
                "text": "Humanoid robots freeze when planning collision-free manifolds.",
                "visual_focus": "Kinematic arm colliding with table safe zone."
            }
        ],
        "math_formulas": [
            {"beat_id": 1, "latex": r"$\mathcal{C}_{\mathrm{free}} = \mathcal{C} \setminus \mathcal{C}_{\mathrm{obs}}$"}
        ]
    }

    # Simulate Gemini Vision raising 429
    with patch("google.generativeai.GenerativeModel") as mock_genai_model:
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = Exception("429 ResourceExhausted: Quota exceeded")
        mock_genai_model.return_value = mock_instance

        report = critic.audit_keyframe(
            image_path=str(test_image),
            spec=dummy_spec,
            beat_id=1
        )

        # Acceptance Criteria:
        # 1. Valid evaluation report
        assert isinstance(report, dict)
        assert "overall_score" in report
        assert "passed" in report
        assert "semantic_alignment_score" in report
        assert "chalkboard_compliance_score" in report
        assert "safe_zone_score" in report
        assert "pedagogical_clarity_score" in report
        assert "primary_observation" in report

        # 2. Valid layout patch proposals produced
        assert "suggested_patches" in report
        assert len(report["suggested_patches"]) > 0
        first_patch = report["suggested_patches"][0]
        assert "entity_id" in first_patch
        assert "action" in first_patch
        assert "dx" in first_patch
        assert "dy" in first_patch
        assert "scale_multiplier" in first_patch

        # 3. Quota tracker state
        assert quota_tracker.is_exhausted("gemini_vision") is True


def test_vlm_critic_immediate_skip_when_vision_exhausted():
    """Verify subsequent keyframe audits immediately skip Gemini vision without timeouts."""
    critic = VLMCritic()
    quota_tracker.record_exhausted("gemini_vision", "pre-existing 429")

    test_image = PROJECT_ROOT / "public" / "test_frame.png"
    if not test_image.exists():
        from PIL import Image
        img = Image.new("RGB", (1080, 1920), color=(10, 13, 20))
        img.save(test_image)

    dummy_spec = {
        "title": "FlashAttention-3",
        "domain_taxonomy": "hardware_efficiency",
        "beats": [{"beat_id": 1, "text": "Hardware attention", "visual_focus": "KV Cache"}],
        "math_formulas": []
    }

    with patch("google.generativeai.GenerativeModel") as mock_model:
        report = critic.audit_keyframe(str(test_image), dummy_spec, beat_id=1)
        # Should not have called GenerativeModel
        assert mock_model.call_count == 0
        assert report["overall_score"] > 0
        assert len(report["suggested_patches"]) > 0


# ==============================================================================
# 5. End-to-End Pipeline Dry-Run Verification (Acceptance Criteria)
# ==============================================================================

def test_pipeline_dry_run_command_completes_with_zero_errors():
    """Verifies that `python3 -m pipeline.run_pipeline --dry-run` completes with return code 0 and 0 errors."""
    cmd = [sys.executable, "-m", "pipeline.run_pipeline", "--dry-run"]
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=120
    )

    assert result.returncode == 0, f"Dry-run failed with stderr:\n{result.stderr}\nstdout:\n{result.stdout}"
    assert "End-to-end dry-run test completed successfully with 0 errors" in result.stdout


# ==============================================================================
# 6. Adversarial Multi-Provider Cascade & Edge Case Verification
# ==============================================================================

def test_script_generation_skips_mocked_gemini_on_subsequent_call():
    """Verify that even when genai is mocked with a MagicMock on script_generator,
    subsequent calls skip Gemini immediately without calling the mock when marked exhausted."""
    router = LLMRouter()
    import pipeline.script_generator as sg

    mock_genai = MagicMock()
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = Exception("429 Resource has been exhausted")
    mock_genai.GenerativeModel.return_value = mock_model

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=False), \
         patch.object(sg, "genai", mock_genai):

        # Call 1: fails and marks exhausted
        spec1, provider1 = router.route_script_generation(
            prompt="Prompt 1",
            topic="Test Topic 1"
        )
        assert quota_tracker.is_exhausted("gemini") is True
        assert mock_model.generate_content.call_count == 1

        # Call 2: MUST skip Gemini immediately and NOT call mock_model.generate_content
        spec2, provider2 = router.route_script_generation(
            prompt="Prompt 2",
            topic="Test Topic 2"
        )
        assert mock_model.generate_content.call_count == 1  # Not incremented!
        assert provider2 in ("groq", "openrouter", "ollama", "deterministic_fallback")


def test_script_generation_full_cascade_to_deterministic():
    """Verify complete failure cascade across Gemini -> Groq -> OpenRouter -> Ollama -> Deterministic Fallback."""
    router = LLMRouter()

    # Pre-exhaust Gemini
    quota_tracker.record_exhausted("gemini", "429 Quota Exceeded")

    # Set fake API keys for Groq and OpenRouter
    env_patch = {
        "GROQ_API_KEY": "fake_groq_key",
        "OPENROUTER_API_KEY": "fake_or_key"
    }

    mock_429_resp = MagicMock()
    mock_429_resp.status_code = 429
    mock_429_resp.text = '{"error": {"message": "Rate limit exceeded"}}'

    with patch.dict(os.environ, env_patch, clear=False), \
         patch("requests.post", return_value=mock_429_resp), \
         patch("pipeline.ollama_client.OllamaClient.generate_completion", side_effect=Exception("429 Too Many Requests")):

        spec, provider = router.route_script_generation(
            prompt="Generate fallback spec",
            topic="Cascading Transformers"
        )

        assert provider == "deterministic_fallback"
        assert quota_tracker.is_exhausted("gemini") is True
        assert quota_tracker.is_exhausted("groq") is True
        assert quota_tracker.is_exhausted("openrouter") is True
        assert quota_tracker.is_exhausted("ollama") is True

        assert len(spec["beats"]) == 6
        assert len(spec["math_formulas"]) == 5
        assert spec["category"] == "mechanism_deepdive"


def test_voice_engine_sarvam_hindi_fallback_preserves_language(tmp_path):
    """Verify Sarvam AI Hindi synthesis falls back to Kokoro with language='hi' passed through."""
    router = UnifiedVoiceRouter(cache_dir=str(tmp_path))

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = "quota_exceeded: Sarvam credits finished"

    with patch("requests.post", return_value=mock_resp), \
         patch.object(router.kokoro, "synthesize", wraps=router.kokoro.synthesize) as mock_synth:

        audio, sr, meta = router.synthesize_beat(
            text="यह एक परीक्षण वाक्य है।",
            voice="shubh",
            language="hi",
            provider="sarvam"
        )

        assert sr == SAMPLE_RATE
        assert meta["fallback_from"] == "sarvam"
        assert quota_tracker.is_exhausted("sarvam") is True

        # Kokoro synthesize must have received language="hi" (not hardcoded en-us)
        mock_synth.assert_called_once()
        _, kwargs = mock_synth.call_args
        assert kwargs.get("language") == "hi"


def test_sanitize_audio_samples_stereo_and_artifacts():
    """Verify sanitize_audio_samples converts stereo 2D audio to mono 1D float32
    and strips NaNs, Infs, and clipping distortion."""
    from pipeline.voice_engine import sanitize_audio_samples

    # Stereo array with NaNs, Infs, and out-of-bound values
    raw_stereo = np.array([
        [0.5, np.nan, 2.5, -3.0, 0.1],
        [0.7, np.inf, -np.inf, 0.0, 0.2]
    ], dtype=np.float64)

    clean = sanitize_audio_samples(raw_stereo, target_sr=24000)

    assert clean.ndim == 1
    assert clean.dtype == np.float32
    assert len(clean) == 5
    assert np.isfinite(clean).all()
    assert (clean >= -1.0).all() and (clean <= 1.0).all()


def test_vlm_critic_ollama_vision_attempts_when_text_ollama_exhausted():
    """Verify that exhausting text Ollama does NOT block Ollama Vision from executing."""
    critic = VLMCritic()

    # Pre-exhaust Gemini vision and text Ollama
    quota_tracker.record_exhausted("gemini_vision", "429")
    quota_tracker.record_exhausted("ollama", "Text model exhausted")

    # ollama_vision is healthy
    assert quota_tracker.is_healthy("ollama_vision") is True

    test_image = PROJECT_ROOT / "public" / "test_frame.png"
    if not test_image.exists():
        from PIL import Image
        img = Image.new("RGB", (1080, 1920), color=(10, 13, 20))
        img.save(test_image)

    dummy_spec = {
        "title": "Decoupled Vision",
        "domain_taxonomy": "hardware_efficiency",
        "beats": [{"beat_id": 1, "text": "Testing vision decoupling", "visual_focus": "Screen"}],
        "math_formulas": []
    }

    mock_vision_resp = MagicMock()
    mock_vision_resp.to_dict.return_value = {
        "overall_score": 9.2,
        "passed": True,
        "primary_observation": "Ollama vision successfully validated frame.",
        "detected_entities": [{"entity_id": "hero_visual", "box_2d": [100, 200, 800, 900]}],
        "suggested_patches": []
    }
    mock_vision_resp.model = "gemma4:31b:cloud"

    with patch("pipeline.ollama_client.OllamaClient.generate_vision_completion", return_value=mock_vision_resp) as mock_vis:
        report = critic.audit_keyframe(str(test_image), dummy_spec, beat_id=1)

        # generate_vision_completion MUST have been called despite ollama text model being exhausted
        assert mock_vis.called
        assert report["overall_score"] >= 8.0
        assert report["model_used"] == "gemma4:31b:cloud"
        assert quota_tracker.is_healthy("ollama_vision") is True


def test_is_quota_error_requests_http_error():
    """Verify is_quota_error inspects requests.exceptions.HTTPError response status codes."""
    import requests

    resp_429 = requests.Response()
    resp_429.status_code = 429
    err_429 = requests.exceptions.HTTPError("Client error occurred", response=resp_429)
    assert is_quota_error(err_429) is True

    resp_401 = requests.Response()
    resp_401.status_code = 401
    err_401 = requests.exceptions.HTTPError("Client error occurred", response=resp_401)
    assert is_quota_error(err_401) is True

    resp_500 = requests.Response()
    resp_500.status_code = 500
    err_500 = requests.exceptions.HTTPError("Server error occurred", response=resp_500)
    assert is_quota_error(err_500) is False


def test_voice_engine_elevenlabs_natural_quota_phrasing(tmp_path):
    """Verify ElevenLabs 401 with natural quota phrasing raises VoiceQuotaExceededError and cascades to Kokoro."""
    router = UnifiedVoiceRouter(cache_dir=str(tmp_path))

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = json.dumps({"detail": {"message": "You have exceeded your monthly quota"}})

    with patch("requests.post", return_value=mock_resp):
        audio, sr, meta = router.synthesize_beat(
            text="Natural phrasing quota failover test.",
            voice="eric",
            provider="elevenlabs"
        )
        assert sr == SAMPLE_RATE
        assert len(audio) > 0
        assert meta["fallback_from"] == "elevenlabs"
        assert quota_tracker.is_exhausted("elevenlabs") is True


def test_voice_engine_sarvam_natural_credits_phrasing(tmp_path):
    """Verify Sarvam 401 with 'credits exhausted' raises VoiceQuotaExceededError and cascades to Kokoro."""
    router = UnifiedVoiceRouter(cache_dir=str(tmp_path))

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = json.dumps({"detail": "User credits exhausted for this account"})

    with patch("requests.post", return_value=mock_resp):
        audio, sr, meta = router.synthesize_beat(
            text="नमस्ते यह क्रेडिट समाप्त परीक्षण है।",
            voice="shubh",
            language="hi",
            provider="sarvam"
        )
        assert sr == SAMPLE_RATE
        assert len(audio) > 0
        assert meta["fallback_from"] == "sarvam"
        assert quota_tracker.is_exhausted("sarvam") is True


def test_voice_engine_kokoro_direct_failure_does_not_mark_quota_exhausted(tmp_path):
    """Verify that a direct Kokoro synthesis failure does not mark Kokoro as quota exhausted and re-raises."""
    router = UnifiedVoiceRouter(cache_dir=str(tmp_path))

    with patch.object(router.kokoro, "synthesize", side_effect=RuntimeError("ONNX engine corrupted")):
        with pytest.raises(RuntimeError, match="ONNX engine corrupted"):
            router.synthesize_beat(
                text="Offline Kokoro direct failure test.",
                provider="kokoro"
            )

    # Kokoro must NOT be marked exhausted (it is an offline engine with no quota)
    assert quota_tracker.is_healthy("kokoro") is True


def test_script_generation_gemini_exhaustion_syncs_gemini_vision():
    """Verify that Gemini text 429 exhaustion also marks gemini_vision as exhausted in QuotaHealthTracker."""
    router = LLMRouter()
    import pipeline.script_generator as sg

    mock_genai = MagicMock()
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = Exception("429 ResourceExhausted: Project quota exceeded")
    mock_genai.GenerativeModel.return_value = mock_model

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=False), \
         patch.object(sg, "genai", mock_genai):

        spec, provider = router.route_script_generation(
            prompt="Prompt syncing vision",
            topic="Attention Mechanisms"
        )

        assert quota_tracker.is_exhausted("gemini") is True
        assert quota_tracker.is_exhausted("gemini_vision") is True


def test_groq_empty_choices_or_malformed_json_cascades_safely():
    """Verify Groq returning HTTP 200 with empty choices or invalid JSON body cleanly cascades to next provider without crashing."""
    router = LLMRouter()
    quota_tracker.record_exhausted("gemini", "Gemini pre-exhausted")

    # Mock Groq returning HTTP 200 with empty choices
    mock_empty_resp = MagicMock()
    mock_empty_resp.status_code = 200
    mock_empty_resp.json.return_value = {"choices": []}

    with patch.dict(os.environ, {"GROQ_API_KEY": "test_groq_key"}, clear=False), \
         patch("requests.post", return_value=mock_empty_resp):

        spec, provider = router.route_script_generation(
            prompt="Prompt test",
            topic="Sparse Attention"
        )

        # Must have cascaded past Groq to OpenRouter/Ollama/deterministic
        assert provider in ("openrouter", "ollama", "deterministic_fallback")
        assert len(spec["beats"]) == 6


def test_quota_tracker_thread_safety_concurrency():
    """Verify thread-safety and lack of race conditions in QuotaHealthTracker under concurrent access."""
    import concurrent.futures

    def worker(idx: int):
        prov = f"provider_{idx % 5}"
        if idx % 2 == 0:
            quota_tracker.record_exhausted(prov, f"Thread {idx} exhausted")
        else:
            quota_tracker.record_success(prov)
        return quota_tracker.is_healthy(prov)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(100)]
        results = [f.result() for f in futures]

    assert len(results) == 100
    statuses = quota_tracker.get_all_statuses()
    assert len(statuses) <= 5


def test_provider_pref_groq_and_openrouter_routing():
    """Verify that setting LLM_PROVIDER=groq or openrouter prioritizes that provider."""
    router = LLMRouter()

    mock_groq_spec = {
        "id": "groq_test",
        "title": "Groq Script",
        "category": "mechanism_deepdive",
        "beats": [{"beat_id": i, "text": f"Beat {i}"} for i in range(1, 7)]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": json.dumps(mock_groq_spec)}}]
    }

    with patch.dict(os.environ, {"LLM_PROVIDER": "groq", "GROQ_API_KEY": "test_key"}, clear=False), \
         patch("requests.post", return_value=mock_resp), \
         patch.object(router, "call_gemini") as mock_gemini:

        spec, provider = router.route_script_generation("Prompt", topic="Groq Priority")
        assert provider == "groq"
        assert mock_gemini.call_count == 0


def test_is_quota_error_extended_patterns():
    """Verify newly added natural quota error phrases and exception classes are detected."""
    phrases = [
        "Quota limit reached",
        "User is over quota",
        "insufficient credits for this operation",
        "daily limit reached",
        "usage limit exceeded",
        "out of quota",
        "Tokens per minute limit exceeded",
        "Capacity exceeded on current tier",
        "503 The model is overloaded. Please try again later.",
        "Account has insufficient funds",
    ]
    for phrase in phrases:
        assert is_quota_error(phrase) is True, f"Failed to detect: {phrase}"

    # Custom exception classes
    class TooManyRequests(Exception): pass
    class OverQuotaError(Exception): pass
    class InsufficientQuotaError(Exception): pass
    class QuotaError(Exception): pass
    class PaymentRequired(Exception): pass
    class BudgetExceededError(Exception): pass

    for exc_cls in [TooManyRequests, OverQuotaError, InsufficientQuotaError, QuotaError, PaymentRequired, BudgetExceededError]:
        assert is_quota_error(exc_cls("Custom error message")) is True, f"Failed on class {exc_cls.__name__}"


def test_voice_engine_http_503_cascades_to_kokoro_and_records_exhausted(tmp_path):
    """Verify ElevenLabs returning HTTP 503 cascades to Kokoro and marks ElevenLabs exhausted."""
    router = UnifiedVoiceRouter(cache_dir=str(tmp_path))

    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.text = "Service Unavailable: ElevenLabs cluster overloaded"

    with patch("requests.post", return_value=mock_resp):
        audio, sr, meta = router.synthesize_beat(
            text="Service 503 outage failover test.",
            voice="eric",
            provider="elevenlabs"
        )
        assert sr == SAMPLE_RATE
        assert len(audio) > 0
        assert meta["fallback_from"] == "elevenlabs"
        assert quota_tracker.is_exhausted("elevenlabs") is True

    # Subsequent beat immediately skips ElevenLabs without making network requests
    with patch("requests.post") as mock_post:
        audio2, sr2, meta2 = router.synthesize_beat(
            text="Next beat skipping unavailable provider.",
            voice="eric",
            provider="elevenlabs"
        )
        assert mock_post.call_count == 0
        assert sr2 == SAMPLE_RATE
        assert meta2["fallback_from"] == "elevenlabs"


def test_voice_engine_connection_error_cascades_to_kokoro_and_records_exhausted(tmp_path):
    """Verify network connection drop on ElevenLabs cascades to Kokoro and records exhaustion."""
    import requests
    router = UnifiedVoiceRouter(cache_dir=str(tmp_path))

    with patch("requests.post", side_effect=requests.exceptions.ConnectionError("Connection refused by peer")):
        audio, sr, meta = router.synthesize_beat(
            text="Connection drop failover test.",
            voice="eric",
            provider="elevenlabs"
        )
        assert sr == SAMPLE_RATE
        assert len(audio) > 0
        assert meta["fallback_from"] == "elevenlabs"
        assert quota_tracker.is_exhausted("elevenlabs") is True

    # Subsequent beat immediately skips ElevenLabs without making network requests
    with patch("requests.post") as mock_post:
        audio2, sr2, meta2 = router.synthesize_beat(
            text="Next beat skipping after connection drop.",
            voice="eric",
            provider="elevenlabs"
        )
        assert mock_post.call_count == 0
        assert sr2 == SAMPLE_RATE


def test_vlm_critic_all_gemini_models_failing_syncs_quota_tracker():
    """Verify that when all Gemini Vision models fail, gemini_vision is marked exhausted and subsequent audits skip."""
    critic = VLMCritic()

    test_image = PROJECT_ROOT / "public" / "test_frame.png"
    if not test_image.exists():
        from PIL import Image
        img = Image.new("RGB", (1080, 1920), color=(10, 13, 20))
        img.save(test_image)

    dummy_spec = {
        "title": "Hardware Bandwidth Ceiling",
        "domain_taxonomy": "hardware_efficiency",
        "beats": [{"beat_id": 1, "text": "HBM bandwidth limits", "visual_focus": "Bus diagram"}],
        "math_formulas": []
    }

    # Simulate all Gemini Vision models failing with 503
    with patch("google.generativeai.GenerativeModel") as mock_model_cls:
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = Exception("503 The model is overloaded. Please try again later.")
        mock_model_cls.return_value = mock_instance

        report = critic.audit_keyframe(str(test_image), dummy_spec, beat_id=1)
        assert report["overall_score"] > 0
        assert quota_tracker.is_exhausted("gemini_vision") is True
        assert quota_tracker.is_exhausted("gemini") is True

    # Call 2: Must skip Gemini Vision immediately without calling GenerativeModel
    with patch("google.generativeai.GenerativeModel") as mock_model_cls2:
        report2 = critic.audit_keyframe(str(test_image), dummy_spec, beat_id=1)
        assert mock_model_cls2.call_count == 0
        assert report2["overall_score"] > 0


def test_vlm_critic_ollama_vision_connection_error_records_exhausted_and_uses_layout_solver():
    """Verify Ollama Vision connection error records exhaustion and cascades to layout solver heuristics."""
    critic = VLMCritic()
    quota_tracker.record_exhausted("gemini_vision", "Pre-exhausted")

    test_image = PROJECT_ROOT / "public" / "test_frame.png"
    if not test_image.exists():
        from PIL import Image
        img = Image.new("RGB", (1080, 1920), color=(10, 13, 20))
        img.save(test_image)

    dummy_spec = {
        "title": "Layout Solver Verification",
        "domain_taxonomy": "robotics_tamp",
        "beats": [{"beat_id": 1, "text": "Robotics manifold planning", "visual_focus": "Robot arm"}],
        "math_formulas": []
    }

    with patch("pipeline.ollama_client.OllamaClient.generate_vision_completion", side_effect=requests.exceptions.ConnectionError("Ollama daemon down")):
        report = critic.audit_keyframe(str(test_image), dummy_spec, beat_id=1)

        # Must have fallen back to deterministic layout heuristics
        assert report["model_used"] == "deterministic_layout_heuristics"
        assert len(report["suggested_patches"]) > 0
        assert quota_tracker.is_exhausted("ollama_vision") is True


def test_enforce_script_schema_corrupted_svo_and_blueprints():
    """Verify that partial or corrupted svo_action, visual_blueprint, and highlight_words are thoroughly repaired."""
    malformed_spec = {
        "id": "corrupted_spec",
        "title": "Malformed Test",
        "beats": [
            {
                "beat_id": 1,
                "text": "FlashAttention avoids high latency memory stalls.",
                "highlight_words": {},  # Empty dict!
                "svo_action": {"subject": "Kernel"},  # Missing verb, direct_object, anchor_word!
                "visual_blueprint": {"title": "BROKEN BLUEPRINT"}  # Missing layout, sub, params!
            }
        ],
        "math_formulas": [
            {"beat_id": 1}  # Missing latex and filename!
        ]
    }

    repaired = enforce_script_schema(malformed_spec, topic="FlashAttention")

    beat1 = repaired["beats"][0]
    assert len(beat1["highlight_words"]) > 0
    assert "anchor_word" in beat1["svo_action"]
    assert "action_verb" in beat1["svo_action"]
    assert "direct_object" in beat1["svo_action"]
    assert "layout" in beat1["visual_blueprint"]
    assert "params" in beat1["visual_blueprint"]

    formula1 = repaired["math_formulas"][0]
    assert len(formula1["latex"]) > 0
    assert len(formula1["filename"]) > 0
    assert formula1["fontsize"] == 24


def test_groq_http_503_cascades_to_openrouter():
    """Verify Groq returning HTTP 503 cascades cleanly to OpenRouter/Ollama/deterministic."""
    router = LLMRouter()
    quota_tracker.record_exhausted("gemini", "Gemini pre-exhausted")

    mock_503_resp = MagicMock()
    mock_503_resp.status_code = 503
    mock_503_resp.text = "Service Unavailable: Groq node down"

    with patch.dict(os.environ, {"GROQ_API_KEY": "test_groq_key"}, clear=False), \
         patch("requests.post", return_value=mock_503_resp):

        spec, provider = router.route_script_generation(
            prompt="Prompt 503 test",
            topic="Memory Bandwidth"
        )

        assert provider in ("openrouter", "ollama", "deterministic_fallback")
        assert len(spec["beats"]) == 6
        assert quota_tracker.is_exhausted("groq") is True


def test_unicode_and_special_char_topic_sanitization():
    """Verify topics with emojis, brackets, and punctuation generate clean filesystem slugs and valid schemas."""
    crazy_topic = "⚡ Super-Fast Attention (Paper #42) [2026] & Beyond! 🚀"
    fallback = generate_deterministic_fallback_script(topic=crazy_topic)

    assert fallback["id"] is not None
    assert not any(c in fallback["id"] for c in ["⚡", " ", "(", ")", "[", "]", "#", "&", "!", "🚀"])
    assert len(fallback["id"]) > 0
    assert len(fallback["beats"]) == 6
    for f in fallback["math_formulas"]:
        assert not any(c in f["filename"] for c in ["⚡", " ", "(", ")", "[", "]", "#", "&", "!", "🚀"])



