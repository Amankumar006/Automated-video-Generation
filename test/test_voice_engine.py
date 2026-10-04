"""
Unit and Integration Tests for The Model Verse Unified Voice Engine:
- Disk audio caching (zero-credit deduplication)
- Text normalization & phonetic rules
- ElevenLabs provider & voice resolution
- Sarvam AI provider & Hindi decoding
- Seamless fallback to Kokoro on quota exhaustion or error
"""

import io
import os
import sys
import json
import base64
from pathlib import Path
import pytest
import numpy as np
import soundfile as sf
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.text_normalizer import (
    normalize_narration_text,
    normalize_currency,
    normalize_numbers_and_multipliers
)
from pipeline.voice_engine import (
    DiskAudioCache,
    ElevenLabsVoiceProvider,
    SarvamVoiceProvider,
    KokoroVoiceProvider,
    UnifiedVoiceRouter,
    VoiceQuotaExceededError,
    VoiceAuthError,
    resample_audio
)
from pipeline.config import SAMPLE_RATE


# ==============================================================================
# 1. Text Normalizer Tests
# ==============================================================================

def test_normalize_currency():
    assert "42 dollars and 50 cents" in normalize_currency("The price is $42.50 today.")
    assert "10 million dollars" in normalize_currency("They raised $10M in Series A.")
    assert "1 billion dollars" in normalize_currency("Market cap reached $1B.")
    assert "100 dollars" in normalize_currency("Costs $100 per hour.")


def test_normalize_numbers_and_multipliers():
    assert "70 percent" in normalize_numbers_and_multipliers("Bottleneck at 70% compute.")
    assert "3.5 times" in normalize_numbers_and_multipliers("Delivers 3.5x speedup.")
    assert "2 to 4 times" in normalize_numbers_and_multipliers("Ranges between 2x-4x faster.")


def test_normalize_narration_text_tech_acronyms():
    text = "GPU memory is 24GB on H100 with LLMs running KV cache and AST matching."
    norm = normalize_narration_text(text, model_id="eleven_multilingual_v2")
    assert "G P U" in norm
    assert "24 gigabytes" in norm
    assert "L L M's" in norm
    assert "K V cache" in norm
    assert "A S T" in norm


def test_normalize_narration_text_math():
    text = "Attention complexity drops from $O(N^2)$ to $O(N)$ asymptotically."
    norm = normalize_narration_text(text)
    assert "O of N squared" in norm
    assert "O of N" in norm
    assert "$" not in norm


def test_normalize_audio_tags_model_dependent():
    text = "Wait [whispers] listen closely to this breakthrough."
    # eleven_v4 preserves audio tags
    v4_norm = normalize_narration_text(text, model_id="eleven_v4")
    assert "[whispers]" in v4_norm

    # older models strip them so they aren't spoken
    v2_norm = normalize_narration_text(text, model_id="eleven_multilingual_v2")
    assert "[whispers]" not in v2_norm
    assert "listen closely" in v2_norm


def test_normalize_hindi_text():
    text = "यह मॉडल 4x तेज है और 50% मेमोरी बचाता है।"
    norm = normalize_narration_text(text, language="hi")
    assert "4 गुना" in norm
    assert "50 प्रतिशत" in norm


# ==============================================================================
# 2. Disk Audio Cache Tests
# ==============================================================================

def test_disk_audio_cache_put_get(tmp_path):
    cache = DiskAudioCache(cache_dir=str(tmp_path))
    key = cache.compute_key("elevenlabs", "v2", "eric", 1.0, 24000, "Hello world")

    assert cache.get(key) is None
    assert cache.stats["misses"] == 1

    dummy_audio = np.random.randn(24000).astype(np.float32)
    meta = {"char_count": 11, "model": "v2"}
    cache.put(key, dummy_audio, 24000, meta)

    cached = cache.get(key)
    assert cached is not None
    audio, sr, cached_meta = cached
    assert sr == 24000
    assert len(audio) == 24000
    assert cached_meta["char_count"] == 11
    assert cache.stats["hits"] == 1
    assert cache.stats["characters_saved"] == 11


# ==============================================================================
# 3. Audio Resampling Tests
# ==============================================================================

def test_resample_audio_44k_to_24k():
    sr_in = 44100
    sr_out = 24000
    audio_44k = np.random.randn(sr_in).astype(np.float32)
    audio_24k = resample_audio(audio_44k, sr_in, sr_out)
    assert audio_24k.dtype == np.float32
    assert abs(len(audio_24k) - sr_out) <= 2


# ==============================================================================
# 4. ElevenLabs Provider Tests
# ==============================================================================

def test_elevenlabs_resolve_voice_id():
    provider = ElevenLabsVoiceProvider(api_key="fake_key")
    # Friendly alias
    assert provider.resolve_voice_id("eric") == "cjVigY5qzO86Huf0OWal"
    assert provider.resolve_voice_id("adam") == "pNInz6obpgDQGcFmaJgB"
    # Kokoro voice name stripped
    assert provider.resolve_voice_id("am_eric") == "cjVigY5qzO86Huf0OWal"
    # Direct ID pass-through
    assert provider.resolve_voice_id("custom123456789012") == "custom123456789012"
    # None defaults to Eric
    assert provider.resolve_voice_id(None) == "cjVigY5qzO86Huf0OWal"


def test_elevenlabs_auth_error_when_missing_key():
    provider = ElevenLabsVoiceProvider(api_key="")
    with pytest.raises(VoiceAuthError):
        provider.synthesize("Test narration without key")


@patch("requests.post")
def test_elevenlabs_synthesize_mock_success(mock_post):
    # Prepare dummy WAV bytes in memory
    buf = io.BytesIO()
    dummy_audio = np.random.randn(44100).astype(np.float32)
    sf.write(buf, dummy_audio, 44100, format="WAV")
    wav_bytes = buf.getvalue()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = wav_bytes
    mock_resp.headers = {"character-cost": "25", "history-item-id": "hist_123"}
    mock_post.return_value = mock_resp

    provider = ElevenLabsVoiceProvider(api_key="test_api_key")
    audio, sr, meta = provider.synthesize("Transformers scale efficiently.", voice="eric", speed=1.05)

    assert sr == 24000
    assert meta["provider"] == "elevenlabs"
    assert meta["character_cost"] == 25
    assert meta["history_id"] == "hist_123"


@patch("requests.post")
def test_elevenlabs_quota_exceeded(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 402
    mock_resp.text = "Quota exceeded. Upgrade your subscription."
    mock_post.return_value = mock_resp

    provider = ElevenLabsVoiceProvider(api_key="test_api_key")
    with pytest.raises(VoiceQuotaExceededError):
        provider.synthesize("Test out of credits")


# ==============================================================================
# 5. Sarvam AI Provider Tests
# ==============================================================================

def test_sarvam_resolve_speaker():
    provider = SarvamVoiceProvider(api_key="fake_key")
    assert provider.resolve_speaker("shubh") == "shubh"
    assert provider.resolve_speaker("meera") == "meera"
    assert provider.resolve_speaker(None) == "shubh"


def test_sarvam_auth_error_when_missing_key():
    provider = SarvamVoiceProvider(api_key="")
    with pytest.raises(VoiceAuthError):
        provider.synthesize("नमस्ते बिना चाबी के")


@patch("requests.post")
def test_sarvam_synthesize_mock_success(mock_post):
    # Prepare dummy WAV bytes
    buf = io.BytesIO()
    dummy_audio = np.random.randn(24000).astype(np.float32)
    sf.write(buf, dummy_audio, 24000, format="WAV")
    wav_bytes = buf.getvalue()
    b64_str = base64.b64encode(wav_bytes).decode("utf-8")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"audios": [b64_str]}
    mock_post.return_value = mock_resp

    provider = SarvamVoiceProvider(api_key="test_sarvam_key")
    audio, sr, meta = provider.synthesize("नमस्ते दोस्तों।", voice="shubh", speed=1.0)

    assert sr == 24000
    assert meta["provider"] == "sarvam"
    assert meta["speaker"] == "shubh"


# ==============================================================================
# 6. Unified Voice Router & Automatic Kokoro Fallback Tests
# ==============================================================================

def test_unified_voice_router_cache_hit_avoids_api(tmp_path):
    router = UnifiedVoiceRouter(cache_dir=str(tmp_path))

    # Pre-populate cache
    key = router.cache.compute_key(
        provider="elevenlabs",
        model=router.elevenlabs.model_id,
        voice="cjVigY5qzO86Huf0OWal",
        speed=1.05,
        target_sr=24000,
        text="Cached sentence"
    )
    dummy_audio = np.random.randn(24000).astype(np.float32)
    router.cache.put(key, dummy_audio, 24000, {"provider": "elevenlabs", "char_count": 15})

    with patch.object(router.elevenlabs, "synthesize") as mock_synth:
        audio, sr, meta = router.synthesize_beat(
            text="Cached sentence",
            voice="eric",
            speed=1.05,
            language="en",
            provider="elevenlabs"
        )
        # Should NOT call API
        mock_synth.assert_not_called()
        assert sr == 24000
        assert router.cache.stats["hits"] == 1


def test_unified_voice_router_seamless_kokoro_fallback_on_quota(tmp_path):
    router = UnifiedVoiceRouter(cache_dir=str(tmp_path))

    # Mock ElevenLabs raising QuotaExceededError
    with patch.object(
        router.elevenlabs,
        "synthesize",
        side_effect=VoiceQuotaExceededError("Credit exhausted")
    ):
        with patch.object(
            router.kokoro,
            "synthesize",
            return_value=(np.zeros(24000, dtype=np.float32), 24000, {"provider": "kokoro"})
        ) as mock_kokoro:
            audio, sr, meta = router.synthesize_beat(
                text="Fall back to offline Kokoro",
                voice="eric",
                language="en",
                provider="elevenlabs"
            )
            mock_kokoro.assert_called_once()
            assert meta["fallback_from"] == "elevenlabs"
            assert "Credit exhausted" in meta["fallback_reason"]


def test_synthesize_audio_for_spec_integration(tmp_path):
    from pipeline.audio_synthesizer import synthesize_audio_for_spec

    spec = {
        "id": "test_voice_short",
        "title": "Voice Engine Test",
        "beats": [
            {
                "beat_id": 1,
                "text": "First beat testing neural synthesis.",
                "visual_focus": "Intro"
            },
            {
                "beat_id": 2,
                "text": "Second beat verifying acoustic alignment.",
                "visual_focus": "Details"
            }
        ]
    }

    dummy_sample = np.zeros(24000, dtype=np.float32)
    with patch("pipeline.voice_engine.UnifiedVoiceRouter.synthesize_beat") as mock_beat:
        mock_beat.return_value = (dummy_sample, 24000, {"provider": "elevenlabs", "voice_id": "eric"})
        result = synthesize_audio_for_spec(spec, provider="elevenlabs", enable_music=False)

        assert "master_audio" in result
        assert "timing_data" in result
        assert len(result["timing_data"]) == 2
        assert result["timing_data"][0]["provider"] == "elevenlabs"
        assert os.path.exists(result["master_audio"])


def test_default_tts_provider_is_elevenlabs():
    from pipeline.config import DEFAULT_TTS_PROVIDER, DEFAULT_VOICE
    assert DEFAULT_TTS_PROVIDER in ("elevenlabs", "auto")
    assert DEFAULT_VOICE in ("eric", "am_eric")

    router = UnifiedVoiceRouter()
    with patch.object(router.elevenlabs, "synthesize", return_value=(np.zeros(24000, dtype=np.float32), 24000, {"provider": "elevenlabs", "voice_id": "eric"})):
        audio, sr, meta = router.synthesize_beat(
            text="Testing default ElevenLabs routing",
            language="en"
        )
        assert meta["provider"] == "elevenlabs"
        assert meta["voice_id"] == "eric"


def test_kinetic_sfx_cues_synchronized_transitions():
    from pipeline.aligner import generate_kinetic_sfx_cues

    timing_data = [
        {
            "beat_id": 1,
            "start": 0.0,
            "duration": 5.0,
            "text": "Hook beat text",
            "word_timings": [{"clean_word": "paradox", "frame_ahead_trigger": 1.25}]
        },
        {
            "beat_id": 2,
            "start": 5.0,
            "duration": 6.0,
            "text": "Mechanism breakdown text",
            "word_timings": [{"clean_word": "bottleneck", "frame_ahead_trigger": 6.40}]
        },
        {
            "beat_id": 3,
            "start": 11.0,
            "duration": 7.0,
            "text": "Geometric mechanism text",
            "word_timings": []
        },
        {
            "beat_id": 4,
            "start": 18.0,
            "duration": 5.0,
            "text": "Outro: Follow The Model Verse",
            "word_timings": []
        }
    ]

    cues = generate_kinetic_sfx_cues(timing_data)
    # Beat 1 transition entrance cue must be at 0.05s (synchronized with visual entrance)
    beat_1_cues = [c for c in cues if "beat_1" in c["reason"]]
    assert any(c["sound_type"] == "whoosh" and c["timestamp"] == 0.05 for c in beat_1_cues)
    # There should NOT be any premature glass_ping or delayed 0.35s whoosh
    assert not any(c["sound_type"] == "glass_ping" for c in beat_1_cues)
    assert not any(c["sound_type"] == "whoosh" and c["timestamp"] == 0.35 for c in beat_1_cues)

    # Beat 2 transition entrance cue must be at 5.05s (exactly matching Beat 2 scene start)
    beat_2_cues = [c for c in cues if "beat_2" in c["reason"]]
    assert any(c["sound_type"] == "whoosh" and c["timestamp"] == 5.05 for c in beat_2_cues)

