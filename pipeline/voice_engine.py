"""
The Model Verse — Unified Neural Voice Engine & Multi-Provider Router
Coordinates high-fidelity speech synthesis across:
1. ElevenLabs Neural TTS (English) — following official best practices:
   - Models: eleven_multilingual_v2, eleven_v4, eleven_flash_v2
   - Default voice: 'eric' (cjVigY5qzO86Huf0OWal - Smooth, Trustworthy)
   - Dynamic text normalization (currencies, percentages, hardware acronyms, math)
   - Pause & phonetic control
2. Gemini Native TTS (English) — Gemini 3.8 Flash TTS:
   - Default voice: Charon (informative, clear technical delivery)
   - Style-controlled exact transcript generation via the Interactions API
   - Base64 WAV decoding & 24kHz resampling
3. Sarvam AI Neural TTS (Hindi) — bulbul:v3 / bulbul:v1:
   - Target language: hi-IN
   - Default speaker: 'shubh' / 'aditya'
   - Base64 WAV decoding & 24kHz resampling
4. Phonon 31M (Production Local English):
   - Zero-cost local CPU neural speech synthesis
   - Official ptts runtime with 24kHz output and no PyTorch dependency
5. Pocket TTS (Legacy Local Provider):
   - Retained only for explicit backwards-compatible local runs

Features:
- Persistent SHA-256 disk audio caching (public/audio_cache/) for 100% zero-credit re-runs
- Dynamic credit protection and graceful degradation
- Millisecond-exact 24kHz audio normalization
"""

import os
import io
import re
import json
import base64
import hashlib
import logging
import shutil
import subprocess
import tempfile
import threading
import time
import sys
from typing import Tuple, Dict, Any, Optional
import numpy as np
import soundfile as sf
import scipy.signal
import requests

from pipeline.config import (
    SAMPLE_RATE, PUBLIC_DIR, TTS_CACHE_DIR, DEFAULT_SPEED,
    DEFAULT_VOICE,
    ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL_ID, ELEVENLABS_VOICES,
    SARVAM_API_KEY, SARVAM_SPEAKER, SARVAM_MODEL, SARVAM_SPEAKERS,
    GEMINI_API_KEY, GEMINI_TTS_MODEL, GEMINI_TTS_VOICE, GEMINI_TTS_STYLE,
    GEMINI_TTS_TIMEOUT_SECONDS, GEMINI_TTS_MIN_INTERVAL_SECONDS,
    PHONON_TTS_MODEL, PHONON_TTS_VOICE, PHONON_TTS_LANGUAGE, PHONON_TTS_QUANT,
    PHONON_TTS_BIN, PHONON_TTS_TIMEOUT_SECONDS, PHONON_TTS_THREADS,
    FAIL_ON_TTS_PROVIDER_FALLBACK,
    DEFAULT_TTS_PROVIDER
)
from pipeline.text_normalizer import normalize_narration_text
from pipeline.quota_tracker import quota_tracker, is_quota_error

logger = logging.getLogger("voice_engine")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [VoiceEngine] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def sanitize_audio_samples(audio: np.ndarray, target_sr: int = SAMPLE_RATE) -> np.ndarray:
    """Guarantees full 24kHz float32 mono audio with zero NaNs, Infs, or clipping distortions."""
    if not isinstance(audio, np.ndarray):
        audio = np.array(audio, dtype=np.float32)
    if audio.size == 0:
        return np.zeros(int(target_sr * 0.5), dtype=np.float32)
    if audio.ndim > 1:
        if audio.shape[0] <= 2 and audio.shape[0] < audio.shape[1]:
            audio = np.mean(audio, axis=0)
        else:
            audio = np.mean(audio, axis=-1)
    clean = np.nan_to_num(audio, nan=0.0, posinf=0.99, neginf=-0.99).astype(np.float32)
    np.clip(clean, -1.0, 1.0, out=clean)
    return clean.flatten()


class VoiceEngineError(Exception):
    """Base exception for voice engine errors."""
    pass


class VoiceQuotaExceededError(VoiceEngineError):
    """Raised when an external API quota or credit limit is exhausted."""
    pass


class VoiceAuthError(VoiceEngineError):
    """Raised when API credentials are missing or invalid."""
    pass


class DiskAudioCache:
    """
    Persistent SHA-256 disk cache for synthesized audio segments.
    Prevents repeated API calls and saves user credits.
    """

    def __init__(self, cache_dir: str = TTS_CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self._stats = {"hits": 0, "misses": 0, "characters_saved": 0}

    @staticmethod
    def compute_key(
        provider: str,
        model: str,
        voice: str,
        speed: float,
        target_sr: int,
        text: str
    ) -> str:
        payload = f"{provider.lower()}|{model.lower()}|{voice.lower()}|{speed:.2f}|{target_sr}|{text.strip()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Tuple[np.ndarray, int, Dict[str, Any]]]:
        wav_path = os.path.join(self.cache_dir, f"{key}.wav")
        meta_path = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(wav_path) and os.path.exists(meta_path):
            try:
                audio, sr = sf.read(wav_path, dtype="float32")
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                self._stats["hits"] += 1
                self._stats["characters_saved"] += meta.get("char_count", 0)
                return audio, sr, meta
            except Exception as e:
                logger.warning(f"Error reading cache entry {key}: {e}")
                return None
        self._stats["misses"] += 1
        return None

    def put(
        self,
        key: str,
        audio: np.ndarray,
        sample_rate: int,
        meta: Optional[Dict[str, Any]] = None
    ) -> str:
        wav_path = os.path.join(self.cache_dir, f"{key}.wav")
        meta_path = os.path.join(self.cache_dir, f"{key}.json")
        try:
            sf.write(wav_path, audio, sample_rate)
            meta_record = meta or {}
            meta_record["sample_rate"] = sample_rate
            meta_record["samples"] = len(audio)
            meta_record["duration"] = round(len(audio) / sample_rate, 3)
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta_record, f, indent=2)
            return wav_path
        except Exception as e:
            logger.warning(f"Failed to write audio cache {key}: {e}")
            return ""

    @property
    def stats(self) -> Dict[str, Any]:
        return dict(self._stats)


def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int = SAMPLE_RATE) -> np.ndarray:
    """Resamples 1D float32 audio cleanly to target_sr using polyphase filtering."""
    if orig_sr == target_sr or len(audio) == 0:
        return audio.astype(np.float32)

    import math
    gcd = math.gcd(orig_sr, target_sr)
    up = target_sr // gcd
    down = orig_sr // gcd
    if up <= 1000 and down <= 1000:
        resampled = scipy.signal.resample_poly(audio, up, down)
    else:
        new_len = int(round(len(audio) * target_sr / orig_sr))
        resampled = scipy.signal.resample(audio, new_len)

    return resampled.astype(np.float32)


def apply_audio_speed(audio: np.ndarray, sample_rate: int, speed: float) -> np.ndarray:
    """Adjust narration pace with ffmpeg's pitch-preserving atempo filter."""
    if abs(speed - 1.0) < 0.01 or len(audio) == 0:
        return audio.astype(np.float32)
    ffmpeg = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg")
    if not ffmpeg:
        return resample_audio(audio, sample_rate, int(sample_rate * speed))
    with tempfile.TemporaryDirectory(prefix="tts_speed_") as tmp:
        source = os.path.join(tmp, "source.wav")
        target = os.path.join(tmp, "target.wav")
        sf.write(source, audio, sample_rate)
        result = subprocess.run(
            [ffmpeg, "-y", "-loglevel", "error", "-i", source,
             "-filter:a", f"atempo={max(0.5, min(2.0, speed))}",
             "-ar", str(sample_rate), "-ac", "1", target],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and os.path.exists(target):
            adjusted, adjusted_sr = sf.read(target, dtype="float32")
            return resample_audio(adjusted, adjusted_sr, sample_rate)
    return audio.astype(np.float32)


class BaseVoiceProvider:
    """Abstract interface for all speech synthesis providers."""

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        language: str = "en"
    ) -> Tuple[np.ndarray, int, Dict[str, Any]]:
        raise NotImplementedError


class ElevenLabsVoiceProvider(BaseVoiceProvider):
    """
    ElevenLabs Text-to-Speech Provider.
    Adheres strictly to official best practices:
    - Pre-normalizes text (currencies, numbers, tech acronyms, math)
    - Employs eleven_multilingual_v2 / eleven_v4 models
    - Maps friendly voice names ('eric', 'adam', 'alice') to verified IDs
    - Decodes MP3 and resamples to target 24kHz
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None,
        default_voice_id: Optional[str] = None
    ):
        self.api_key = api_key if api_key is not None else ELEVENLABS_API_KEY
        self.model_id = model_id or ELEVENLABS_MODEL_ID
        self.default_voice_id = default_voice_id or ELEVENLABS_VOICE_ID

    def resolve_voice_id(self, voice_name_or_id: Optional[str]) -> str:
        if not voice_name_or_id:
            return self.default_voice_id
        # Check alias dictionary
        clean = voice_name_or_id.lower().replace("am_", "").replace("af_", "")
        if clean in ELEVENLABS_VOICES:
            return ELEVENLABS_VOICES[clean]
        # Or return as-is if already an alphanumeric ID
        if len(voice_name_or_id) >= 15 and re.match(r"^[A-Za-z0-9]+$", voice_name_or_id):
            return voice_name_or_id
        return self.default_voice_id

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        language: str = "en"
    ) -> Tuple[np.ndarray, int, Dict[str, Any]]:
        if not self.api_key:
            raise VoiceAuthError("ELEVENLABS_API_KEY is not configured in environment or .env")

        voice_id = self.resolve_voice_id(voice)
        norm_text = normalize_narration_text(text, model_id=self.model_id, language=language)
        
        # ElevenLabs speed setting ranges from 0.7 to 1.2 (default 1.0)
        target_speed = float(speed) if speed is not None else 1.05
        target_speed = max(0.70, min(1.20, target_speed))

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": norm_text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.50,
                "similarity_boost": 0.75,
                "speed": round(target_speed, 2)
            }
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20.0)
        except Exception as e:
            if is_quota_error(e):
                raise VoiceQuotaExceededError(f"ElevenLabs rate/quota limit reached: {e}")
            raise VoiceEngineError(f"ElevenLabs network request failed: {e}")

        resp_text_lower = resp.text.lower()
        if (
            resp.status_code in (401, 402, 429)
            or is_quota_error(resp.text)
            or is_quota_error(resp.status_code)
        ):
            if resp.status_code == 401 and not is_quota_error(resp.text):
                raise VoiceAuthError(f"ElevenLabs authorization failed (401): {resp.text}")
            raise VoiceQuotaExceededError(f"ElevenLabs quota/credit limit exceeded ({resp.status_code}): {resp.text}")
        elif resp.status_code != 200:
            raise VoiceEngineError(f"ElevenLabs API error (status {resp.status_code}): {resp.text[:200]}")

        char_cost = int(resp.headers.get("character-cost", len(norm_text)))
        history_id = resp.headers.get("history-item-id", "")

        # Decode MP3 bytes
        try:
            audio_data, source_sr = sf.read(io.BytesIO(resp.content), dtype="float32")
        except Exception as e:
            raise VoiceEngineError(f"Failed to decode ElevenLabs MP3 stream: {e}")

        # Resample to 24000 Hz if needed
        audio_24k = resample_audio(audio_data, source_sr, SAMPLE_RATE)

        meta = {
            "provider": "elevenlabs",
            "model": self.model_id,
            "voice_id": voice_id,
            "speed": target_speed,
            "char_count": len(norm_text),
            "character_cost": char_cost,
            "history_id": history_id,
            "normalized_text": norm_text
        }

        return audio_24k, SAMPLE_RATE, meta


class SarvamVoiceProvider(BaseVoiceProvider):
    """
    Sarvam AI Text-to-Speech Provider (Hindi).
    Uses the state-of-the-art bulbul:v3 neural model.
    Decodes base64 WAV payload and resamples to 24kHz.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        default_speaker: Optional[str] = None
    ):
        self.api_key = api_key if api_key is not None else SARVAM_API_KEY
        self.model = model or SARVAM_MODEL
        self.default_speaker = default_speaker or SARVAM_SPEAKER

    def resolve_speaker(self, speaker_name: Optional[str]) -> str:
        if not speaker_name:
            return self.default_speaker
        clean = speaker_name.lower().strip()
        if clean in SARVAM_SPEAKERS:
            return clean
        return self.default_speaker

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        language: str = "hi"
    ) -> Tuple[np.ndarray, int, Dict[str, Any]]:
        if not self.api_key:
            raise VoiceAuthError("SARVAM_API_KEY is not configured in environment or .env")

        speaker = self.resolve_speaker(voice)
        norm_text = normalize_narration_text(text, model_id=self.model, language="hi")
        
        # Pace control in Sarvam ranges from 0.5 to 2.0 (default 1.0)
        target_pace = float(speed) if speed is not None else 1.05
        target_pace = max(0.50, min(2.00, target_pace))

        url = "https://api.sarvam.ai/text-to-speech"
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Try modern bulbul:v3 payload schema
        payload = {
            "text": norm_text,
            "speaker": speaker,
            "model": self.model,
            "language_code": "hi-IN",
            "pace": round(target_pace, 2)
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20.0)
        except Exception as e:
            if is_quota_error(e):
                raise VoiceQuotaExceededError(f"Sarvam AI rate/quota limit reached: {e}")
            raise VoiceEngineError(f"Sarvam AI network request failed: {e}")

        # Fallback to bulbul:v1 schema if 400 bad request
        if resp.status_code == 400:
            logger.info("Retrying Sarvam AI with inputs array schema...")
            alt_payload = {
                "inputs": [norm_text],
                "target_language_code": "hi-IN",
                "speaker": speaker,
                "pitch": 0,
                "pace": round(target_pace, 2),
                "loudness": 1.5,
                "speech_sample_rate": 24000,
                "enable_preprocessing": True,
                "model": "bulbul:v1"
            }
            try:
                resp = requests.post(url, headers=headers, json=alt_payload, timeout=20.0)
            except Exception as e:
                if is_quota_error(e):
                    raise VoiceQuotaExceededError(f"Sarvam AI rate/quota limit reached: {e}")
                raise VoiceEngineError(f"Sarvam AI retry failed: {e}")

        resp_text_lower = resp.text.lower()
        if (
            resp.status_code in (401, 402, 429)
            or is_quota_error(resp.text)
            or is_quota_error(resp.status_code)
        ):
            if resp.status_code == 401 and not is_quota_error(resp.text):
                raise VoiceAuthError(f"Sarvam AI authorization failed (401): {resp.text}")
            raise VoiceQuotaExceededError(f"Sarvam AI credit or rate limit exceeded ({resp.status_code}): {resp.text}")
        elif resp.status_code != 200:
            raise VoiceEngineError(f"Sarvam AI API error (status {resp.status_code}): {resp.text[:200]}")

        data = resp.json()
        audios = data.get("audios", [])
        if not audios or not audios[0]:
            raise VoiceEngineError(f"Sarvam AI returned empty audio data: {data}")

        b64_audio = audios[0]
        raw_bytes = base64.b64decode(b64_audio)

        try:
            audio_data, source_sr = sf.read(io.BytesIO(raw_bytes), dtype="float32")
        except Exception as e:
            raise VoiceEngineError(f"Failed to decode Sarvam WAV stream: {e}")

        audio_24k = resample_audio(audio_data, source_sr, SAMPLE_RATE)

        meta = {
            "provider": "sarvam",
            "model": self.model,
            "speaker": speaker,
            "pace": target_pace,
            "char_count": len(norm_text),
            "normalized_text": norm_text
        }

        return audio_24k, SAMPLE_RATE, meta


class GeminiTTSVoiceProvider(BaseVoiceProvider):
    """Google Gemini native TTS provider using the Interactions REST API."""

    _rate_limit_lock = threading.Lock()
    _last_request_at = 0.0

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        default_voice: Optional[str] = None,
        style: Optional[str] = None,
        timeout: Optional[float] = None,
        min_interval: Optional[float] = None,
    ):
        self.api_key = api_key if api_key is not None else GEMINI_API_KEY
        self.model = model or GEMINI_TTS_MODEL
        self.default_voice = default_voice or GEMINI_TTS_VOICE
        self.style = style if style is not None else GEMINI_TTS_STYLE
        self.timeout = float(timeout if timeout is not None else GEMINI_TTS_TIMEOUT_SECONDS)
        self.min_interval = float(
            min_interval if min_interval is not None else GEMINI_TTS_MIN_INTERVAL_SECONDS
        )

    def resolve_voice(self, voice_name: Optional[str]) -> str:
        return (voice_name or self.default_voice).strip()

    @staticmethod
    def _extract_audio_b64(data: Dict[str, Any]) -> Optional[str]:
        output_audio = data.get("output_audio")
        if isinstance(output_audio, dict) and output_audio.get("data"):
            return output_audio["data"]
        for step in data.get("steps", []):
            if not isinstance(step, dict):
                continue
            for item in step.get("content", []):
                if isinstance(item, dict) and item.get("type") == "audio" and item.get("data"):
                    return item["data"]
        return None

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        language: str = "en",
    ) -> Tuple[np.ndarray, int, Dict[str, Any]]:
        if not self.api_key:
            raise VoiceAuthError("GEMINI_API_KEY is not configured in environment or .env")
        if not language.lower().startswith("en"):
            raise VoiceEngineError("Gemini TTS English production voice is configured for English narration.")

        resolved_voice = self.resolve_voice(voice)
        norm_text = normalize_narration_text(text, model_id=self.model, language=language)
        style = self.style
        if speed is not None:
            style = f"{style}; target delivery speed {float(speed):.2f}x"

        payload = {
            "model": self.model,
            "input": [{
                "type": "user_input",
                "content": [{
                    "type": "text",
                    "text": norm_text,
                    "annotations": [{"type": "speech_metadata", "style": style}],
                }],
            }],
            "response_format": {"type": "audio"},
            "generation_config": {"speech_config": [{"voice": resolved_voice}]},
        }

        # Gemini's free tier is limited to roughly three TTS requests per
        # minute. Keep every beat on the selected voice instead of silently
        # falling back halfway through a short when the limit is reached.
        with self._rate_limit_lock:
            elapsed = time.monotonic() - self._last_request_at
            wait_seconds = max(0.0, self.min_interval - elapsed)
            if wait_seconds:
                logger.info(
                    f"⏳ [Gemini TTS] Rate-limit pacing: waiting {wait_seconds:.1f}s before the next beat"
                )
                time.sleep(wait_seconds)
            self.__class__._last_request_at = time.monotonic()

        try:
            resp = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/interactions",
                headers={"x-goog-api-key": self.api_key, "Content-Type": "application/json"},
                json=payload,
                timeout=self.timeout,
            )
        except Exception as exc:
            if is_quota_error(exc):
                raise VoiceQuotaExceededError(f"Gemini TTS quota/rate limit reached: {exc}") from exc
            raise VoiceEngineError(f"Gemini TTS network request failed: {exc}") from exc

        if resp.status_code in (401, 403):
            raise VoiceAuthError(f"Gemini TTS authorization failed ({resp.status_code}): {resp.text[:300]}")
        if resp.status_code in (402, 429) or is_quota_error(resp.text):
            raise VoiceQuotaExceededError(f"Gemini TTS quota/rate limit exceeded ({resp.status_code}): {resp.text[:300]}")
        if resp.status_code != 200:
            raise VoiceEngineError(f"Gemini TTS API error (status {resp.status_code}): {resp.text[:300]}")

        try:
            audio_b64 = self._extract_audio_b64(resp.json())
            if not audio_b64:
                raise ValueError("response contained no audio block")
            raw_audio = base64.b64decode(audio_b64)
            audio_data, source_sr = sf.read(io.BytesIO(raw_audio), dtype="float32")
        except Exception as exc:
            raise VoiceEngineError(f"Failed to decode Gemini TTS audio: {exc}") from exc

        audio_24k = resample_audio(sanitize_audio_samples(audio_data, source_sr), source_sr, SAMPLE_RATE)
        return audio_24k, SAMPLE_RATE, {
            "provider": "gemini",
            "model": self.model,
            "voice": resolved_voice,
            "speed": speed,
            "style": style,
            "char_count": len(norm_text),
            "normalized_text": norm_text,
        }


class PhononTTSVoiceProvider(BaseVoiceProvider):
    """Local Phonon 31M CPU provider using the official ``ptts`` runtime."""

    def __init__(self):
        self.model = os.environ.get("PHONON_TTS_MODEL", PHONON_TTS_MODEL)
        self.default_voice = os.environ.get("PHONON_TTS_VOICE", PHONON_TTS_VOICE)
        self.language = os.environ.get("PHONON_TTS_LANGUAGE", PHONON_TTS_LANGUAGE)
        self.quant = os.environ.get("PHONON_TTS_QUANT", PHONON_TTS_QUANT)
        self.binary_path = os.environ.get("PHONON_TTS_BIN", PHONON_TTS_BIN)
        self.timeout = float(os.environ.get("PHONON_TTS_TIMEOUT_SECONDS", str(PHONON_TTS_TIMEOUT_SECONDS)))
        self.threads = int(os.environ.get("PHONON_TTS_THREADS", str(PHONON_TTS_THREADS)))

    def _resolve_command(self) -> list[str]:
        candidate = self.binary_path or shutil.which("ptts")
        if candidate:
            if not os.path.isfile(candidate) or not os.access(candidate, os.X_OK):
                raise VoiceEngineError(
                    f"Phonon TTS binary is not executable: {candidate}. "
                    "Install ptts==0.4.2 or set PHONON_TTS_BIN to its executable."
                )
            return [candidate]
        # This keeps local virtualenvs and CI environments robust when the
        # console-script directory is not on PATH.
        return [sys.executable, "-m", "ptts"]

    def resolve_voice(self, voice_name: Optional[str]) -> str:
        candidate = (voice_name or self.default_voice or "").strip()
        # Preserve compatibility with the old ElevenLabs default. Phonon
        # should use the checkpoint voice unless a Phonon catalog ID is set.
        if candidate.lower() in {"eric", "am_eric", "default"}:
            return ""
        return candidate

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        language: str = "en"
    ) -> Tuple[np.ndarray, int, Dict[str, Any]]:
        if not language.lower().startswith("en"):
            raise VoiceEngineError("Phonon 31M is configured for English narration in this pipeline.")

        norm_text = normalize_narration_text(text, model_id="phonon-31m-en", language=language)
        target_speed = float(speed) if speed is not None else DEFAULT_SPEED
        resolved_voice = self.resolve_voice(voice)
        with tempfile.TemporaryDirectory(prefix="phonon_tts_") as tmp:
            output_path = os.path.join(tmp, "speech.wav")
            command = self._resolve_command() + [
                "--model", self.model,
                "--lang", self.language,
                "--quant", self.quant,
                "--seed", "0",
                "--output", output_path,
            ]
            if self.threads > 0:
                command.extend(["--threads", str(self.threads)])
            if resolved_voice:
                command.extend(["--voice", resolved_voice])
            command.append(norm_text)
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
            except subprocess.TimeoutExpired as exc:
                raise VoiceEngineError(f"Phonon TTS timed out after {self.timeout:.0f}s") from exc
            if result.returncode != 0 or not os.path.exists(output_path):
                detail = (result.stderr or result.stdout or "unknown Phonon TTS failure").strip()
                raise VoiceEngineError(f"Phonon TTS failed: {detail[:320]}")
            audio, source_sr = sf.read(output_path, dtype="float32")

        audio = sanitize_audio_samples(audio, source_sr)
        audio = apply_audio_speed(audio, source_sr, target_speed)
        return audio, SAMPLE_RATE, {
            "provider": "phonon",
            "model": self.model,
            "voice": resolved_voice or "default",
            "speed": target_speed,
            "char_count": len(norm_text),
            "binary": self._resolve_command()[0],
            "quant": self.quant,
        }


class PocketTTSVoiceProvider(BaseVoiceProvider):
    """Optional Kyutai Pocket TTS CLI provider for reliable local CPU speech."""

    def __init__(self):
        self.binary_path = os.environ.get("POCKET_TTS_BIN") or shutil.which("pocket-tts")
        self.language = os.environ.get("POCKET_TTS_LANGUAGE", "english_18m_2026-10")
        self.voice = os.environ.get("POCKET_TTS_VOICE", "")
        self.timeout = float(os.environ.get("POCKET_TTS_TIMEOUT_SECONDS", "90"))

    def _resolve_binary(self) -> str:
        path = self.binary_path or shutil.which("pocket-tts")
        if not path or not os.path.isfile(path) or not os.access(path, os.X_OK):
            raise VoiceEngineError(
                "Pocket TTS binary unavailable. Install the official Kyutai binary and set POCKET_TTS_BIN."
            )
        return path

    def resolve_voice(self, voice_name: Optional[str]) -> str:
        """Pocket's CLI accepts a conditioning-file path; otherwise use alba."""
        candidate = voice_name or self.voice
        return candidate if candidate and os.path.isfile(candidate) else "alba"

    @staticmethod
    def _apply_speed(audio: np.ndarray, sample_rate: int, speed: float) -> np.ndarray:
        """Apply pitch-preserving speed where ffmpeg is available."""
        return apply_audio_speed(audio, sample_rate, speed)

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        language: str = "en"
    ) -> Tuple[np.ndarray, int, Dict[str, Any]]:
        if not language.lower().startswith("en"):
            raise VoiceEngineError("Pocket TTS is configured for English narration in this pipeline.")
        binary = self._resolve_binary()
        norm_text = normalize_narration_text(text, model_id="pocket-tts", language=language)
        target_speed = float(speed) if speed is not None else DEFAULT_SPEED
        with tempfile.TemporaryDirectory(prefix="pocket_tts_") as tmp:
            output_path = os.path.join(tmp, "speech.wav")
            command = [
                binary, "generate", "--language", self.language,
                "--text", norm_text, "--output-path", output_path, "--quiet"
            ]
            # Pocket's built-in voices are selected by omission. A supplied
            # path is supported for future voice cloning without treating
            # Voice values are conditioning-file paths for Pocket TTS.
            voice_path = self.resolve_voice(voice)
            if voice_path and os.path.isfile(voice_path):
                command.extend(["--voice", voice_path])
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
            except subprocess.TimeoutExpired as exc:
                raise VoiceEngineError(f"Pocket TTS timed out after {self.timeout:.0f}s") from exc
            if result.returncode != 0 or not os.path.exists(output_path):
                detail = (result.stderr or result.stdout or "unknown Pocket TTS failure").strip()
                raise VoiceEngineError(f"Pocket TTS failed: {detail[:240]}")
            audio, source_sr = sf.read(output_path, dtype="float32")

        audio = sanitize_audio_samples(audio, source_sr)
        audio = self._apply_speed(audio, source_sr, target_speed)
        return audio, SAMPLE_RATE, {
            "provider": "pocket",
            "model": self.language,
            "voice": voice_path,
            "speed": target_speed,
            "char_count": len(norm_text),
            "binary": binary,
        }


class UnifiedVoiceRouter:
    """
    Intelligent router selecting the optimal speech synthesis engine
    with automatic persistent caching and transparent Pocket TTS fallback.
    """

    def __init__(self, cache_dir: str = TTS_CACHE_DIR):
        self.cache = DiskAudioCache(cache_dir=cache_dir)
        self.elevenlabs = ElevenLabsVoiceProvider()
        self.sarvam = SarvamVoiceProvider()
        self.gemini = GeminiTTSVoiceProvider()
        self.phonon = PhononTTSVoiceProvider()
        self.pocket = PocketTTSVoiceProvider()

    def synthesize_beat(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        language: str = "en",
        provider: str = DEFAULT_TTS_PROVIDER
    ) -> Tuple[np.ndarray, int, Dict[str, Any]]:
        """
        Synthesizes a beat of speech.
        1. Checks disk cache first. If hit, returns instantly (0 credits spent).
        2. Routes to appropriate provider (Phonon/ElevenLabs for EN, Sarvam for HI).
        3. If a remote primary provider fails, optionally falls back to Pocket TTS.
        4. Writes result to disk cache.
        """
        clean_text = text.strip()
        lang_norm = language.lower()
        prov_norm = provider.lower()

        # Determine target provider
        if prov_norm == "auto":
            if lang_norm in ("hi", "hindi", "hi-in"):
                target_provider = "sarvam"
            else:
                target_provider = "elevenlabs"
        else:
            target_provider = prov_norm

        # Resolve model and voice identifiers for cache key
        if target_provider == "elevenlabs":
            resolved_model = self.elevenlabs.model_id
            resolved_voice = self.elevenlabs.resolve_voice_id(voice)
            active_speed = float(speed) if speed is not None else 1.05
        elif target_provider == "sarvam":
            resolved_model = self.sarvam.model
            resolved_voice = self.sarvam.resolve_speaker(voice)
            active_speed = float(speed) if speed is not None else 1.05
        elif target_provider == "gemini":
            resolved_model = self.gemini.model
            resolved_voice = self.gemini.resolve_voice(voice)
            active_speed = float(speed) if speed is not None else DEFAULT_SPEED
        elif target_provider == "phonon":
            resolved_model = self.phonon.model
            resolved_voice = self.phonon.resolve_voice(voice)
            active_speed = float(speed) if speed is not None else DEFAULT_SPEED
        elif target_provider == "pocket":
            resolved_model = self.pocket.language
            resolved_voice = self.pocket.resolve_voice(voice)
            active_speed = float(speed) if speed is not None else DEFAULT_SPEED
        else:
            raise VoiceEngineError(
                f"Unsupported TTS provider '{target_provider}'. Choose auto, elevenlabs, gemini, phonon, sarvam, or pocket."
            )

        # 1. Check Disk Cache
        cache_key = self.cache.compute_key(
            provider=target_provider,
            model=resolved_model,
            voice=resolved_voice,
            speed=active_speed,
            target_sr=SAMPLE_RATE,
            text=clean_text
        )

        cached = self.cache.get(cache_key)
        if cached is not None:
            audio, sr, meta = cached
            logger.info(f"💾 [Audio Cache Hit] (0 credits spent) for \"{clean_text[:40]}...\"")
            return audio, sr, meta

        # 2. Check Quota Health Tracker: if primary provider is already exhausted, skip directly to Pocket TTS.
        if target_provider in ("elevenlabs", "sarvam", "gemini") and not quota_tracker.is_healthy(target_provider):
            if FAIL_ON_TTS_PROVIDER_FALLBACK:
                raise VoiceEngineError(
                    f"TTS provider '{target_provider}' is exhausted and fallback is disabled; "
                    "refusing to create mixed-voice narration."
                )
            logger.info(
                f"⏩ [VoiceRouter] Provider '{target_provider}' is marked EXHAUSTED in QuotaTracker. "
                f"Immediately cascading to Pocket TTS offline synthesis."
            )
            fallback_voice = self.pocket.resolve_voice(voice)
            audio, sr, meta = self.pocket.synthesize(
                text=clean_text,
                voice=fallback_voice,
                speed=active_speed,
                language=lang_norm
            )
            audio = sanitize_audio_samples(audio, sr)
            meta["fallback_from"] = target_provider
            meta["fallback_reason"] = f"Provider '{target_provider}' previously marked exhausted"
            self.cache.put(cache_key, audio, sr, meta)
            return audio, sr, meta

        # 3. Synthesize via primary provider with automatic fallback
        try:
            if target_provider == "elevenlabs":
                logger.info(f"🎙️ [ElevenLabs] Synthesizing beat with voice '{resolved_voice}', speed {active_speed:.2f}x...")
                audio, sr, meta = self.elevenlabs.synthesize(
                    text=clean_text,
                    voice=resolved_voice,
                    speed=active_speed,
                    language=lang_norm
                )
                quota_tracker.record_success("elevenlabs")
            elif target_provider == "sarvam":
                logger.info(f"🎙️ [Sarvam AI] Synthesizing Hindi beat with speaker '{resolved_voice}', pace {active_speed:.2f}x...")
                audio, sr, meta = self.sarvam.synthesize(
                    text=clean_text,
                    voice=resolved_voice,
                    speed=active_speed,
                    language=lang_norm
                )
                quota_tracker.record_success("sarvam")
            elif target_provider == "gemini":
                logger.info(f"🎙️ [Gemini TTS] Synthesizing beat with voice '{resolved_voice}', speed {active_speed:.2f}x...")
                audio, sr, meta = self.gemini.synthesize(
                    text=clean_text,
                    voice=resolved_voice,
                    speed=active_speed,
                    language=lang_norm,
                )
                quota_tracker.record_success("gemini")
            elif target_provider == "phonon":
                logger.info(f"🎙️ [Phonon 31M] Synthesizing local CPU beat with voice '{resolved_voice or 'default'}', speed {active_speed:.2f}x...")
                audio, sr, meta = self.phonon.synthesize(
                    text=clean_text,
                    voice=resolved_voice,
                    speed=active_speed,
                    language=lang_norm,
                )
            elif target_provider == "pocket":
                logger.info(f"🎙️ [Pocket TTS] Synthesizing local CPU beat with voice '{resolved_voice}'...")
                audio, sr, meta = self.pocket.synthesize(
                    text=clean_text,
                    voice=resolved_voice,
                    speed=active_speed,
                    language=lang_norm
                )
            audio = sanitize_audio_samples(audio, sr)
        except (VoiceQuotaExceededError, VoiceAuthError, VoiceEngineError, Exception) as exc:
            if target_provider in ("elevenlabs", "sarvam", "gemini"):
                err_msg = str(exc)
                if (
                    is_quota_error(exc)
                    or "quota_exceeded" in err_msg.lower()
                    or "429" in err_msg
                    or "402" in err_msg
                    or "401" in err_msg
                ):
                    quota_tracker.record_exhausted(target_provider, f"TTS quota exhausted: {err_msg}")
                else:
                    quota_tracker.record_exhausted(target_provider, f"TTS provider failure: {err_msg}")

                logger.warning(
                    f"⚠️ [Voice Router] Provider '{target_provider}' encountered error: {exc}. "
                    f"Falling back transparently to Pocket TTS offline speech synthesis!"
                )
                if not lang_norm.startswith("en"):
                    raise VoiceEngineError(
                        "Pocket TTS fallback is English-only; configure Sarvam or another Hindi provider."
                    ) from exc
                if FAIL_ON_TTS_PROVIDER_FALLBACK:
                    raise VoiceEngineError(
                        f"TTS provider '{target_provider}' failed and fallback is disabled; "
                        "refusing to create mixed-voice narration."
                    ) from exc
                fallback_voice = self.pocket.resolve_voice(voice)
                audio, sr, meta = self.pocket.synthesize(
                    text=clean_text,
                    voice=fallback_voice,
                    speed=active_speed,
                    language=lang_norm
                )
                audio = sanitize_audio_samples(audio, sr)
                meta["fallback_from"] = target_provider
                meta["fallback_reason"] = str(exc)
            else:
                # Local providers are the lowest tier; surface their failure
                # instead of hiding it behind a different voice.
                raise exc

        # 4. Cache the newly synthesized audio
        self.cache.put(cache_key, audio, sr, meta)

        return audio, sr, meta
