"""
The Model Verse — Unified Neural Voice Engine & Multi-Provider Router
Coordinates high-fidelity speech synthesis across:
1. ElevenLabs Neural TTS (English) — following official best practices:
   - Models: eleven_multilingual_v2, eleven_v4, eleven_flash_v2
   - Default voice: 'eric' (cjVigY5qzO86Huf0OWal - Smooth, Trustworthy)
   - Dynamic text normalization (currencies, percentages, hardware acronyms, math)
   - Pause & phonetic control
2. Sarvam AI Neural TTS (Hindi) — bulbul:v3 / bulbul:v1:
   - Target language: hi-IN
   - Default speaker: 'shubh' / 'aditya'
   - Base64 WAV decoding & 24kHz resampling
3. Kokoro-82M ONNX (Offline Fallback):
   - Zero-cost offline neural speech synthesis
   - Seamless fallback when API quota is exhausted or offline

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
from typing import Tuple, Dict, Any, Optional
import numpy as np
import soundfile as sf
import scipy.signal
import requests

from pipeline.config import (
    SAMPLE_RATE, PUBLIC_DIR, TTS_CACHE_DIR, DEFAULT_SPEED,
    KOKORO_MODEL_PATH, KOKORO_VOICES_PATH, DEFAULT_VOICE,
    ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL_ID, ELEVENLABS_VOICES,
    SARVAM_API_KEY, SARVAM_SPEAKER, SARVAM_MODEL, SARVAM_SPEAKERS,
    DEFAULT_TTS_PROVIDER
)
from pipeline.text_normalizer import normalize_narration_text

logger = logging.getLogger("voice_engine")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [VoiceEngine] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


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
            raise VoiceEngineError(f"ElevenLabs network request failed: {e}")

        if resp.status_code == 401:
            raise VoiceAuthError(f"ElevenLabs authorization failed (401): {resp.text}")
        elif resp.status_code == 402:
            raise VoiceQuotaExceededError(f"ElevenLabs credit limit exceeded (402): {resp.text}")
        elif resp.status_code == 429:
            raise VoiceQuotaExceededError(f"ElevenLabs rate limit exceeded (429): {resp.text}")
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
                raise VoiceEngineError(f"Sarvam AI retry failed: {e}")

        if resp.status_code == 401:
            raise VoiceAuthError(f"Sarvam AI authorization failed (401): {resp.text}")
        elif resp.status_code in (402, 429):
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


class KokoroVoiceProvider(BaseVoiceProvider):
    """
    Kokoro-82M ONNX Voice Provider.
    Completely offline, zero API credits, high-speed execution.
    Acts as a resilient fallback when online services are unavailable.
    """

    def __init__(self):
        self._kokoro = None

    def _ensure_model(self):
        if self._kokoro is None:
            from kokoro_onnx import Kokoro
            from pipeline.audio_synthesizer import ensure_kokoro_models
            ensure_kokoro_models()
            self._kokoro = Kokoro(KOKORO_MODEL_PATH, KOKORO_VOICES_PATH)
        return self._kokoro

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        language: str = "en"
    ) -> Tuple[np.ndarray, int, Dict[str, Any]]:
        kokoro = self._ensure_model()
        v = voice or DEFAULT_VOICE
        s = float(speed) if speed is not None else DEFAULT_SPEED
        lang = "en-us" if language.lower().startswith("en") else "hi"

        samples, _ = kokoro.create(text, voice=v, speed=s, lang=lang)
        meta = {
            "provider": "kokoro",
            "model": "kokoro-v1.0.onnx",
            "voice": v,
            "speed": s,
            "char_count": len(text)
        }
        return samples, SAMPLE_RATE, meta


class UnifiedVoiceRouter:
    """
    Intelligent router selecting the optimal speech synthesis engine
    with automatic persistent caching and transparent Kokoro fallback.
    """

    def __init__(self, cache_dir: str = TTS_CACHE_DIR):
        self.cache = DiskAudioCache(cache_dir=cache_dir)
        self.elevenlabs = ElevenLabsVoiceProvider()
        self.sarvam = SarvamVoiceProvider()
        self.kokoro = KokoroVoiceProvider()

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
        2. Routes to appropriate provider (ElevenLabs for EN, Sarvam for HI).
        3. If primary provider fails or has no quota, falls back seamlessly to Kokoro.
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
        else:
            target_provider = "kokoro"
            resolved_model = "kokoro-v1.0"
            resolved_voice = voice or DEFAULT_VOICE
            active_speed = float(speed) if speed is not None else DEFAULT_SPEED

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

        # 2. Synthesize via primary provider with automatic fallback
        try:
            if target_provider == "elevenlabs":
                logger.info(f"🎙️ [ElevenLabs] Synthesizing beat with voice '{resolved_voice}', speed {active_speed:.2f}x...")
                audio, sr, meta = self.elevenlabs.synthesize(
                    text=clean_text,
                    voice=resolved_voice,
                    speed=active_speed,
                    language=lang_norm
                )
            elif target_provider == "sarvam":
                logger.info(f"🎙️ [Sarvam AI] Synthesizing Hindi beat with speaker '{resolved_voice}', pace {active_speed:.2f}x...")
                audio, sr, meta = self.sarvam.synthesize(
                    text=clean_text,
                    voice=resolved_voice,
                    speed=active_speed,
                    language=lang_norm
                )
            else:
                logger.info(f"🎙️ [Kokoro ONNX] Synthesizing offline beat with voice '{resolved_voice}'...")
                audio, sr, meta = self.kokoro.synthesize(
                    text=clean_text,
                    voice=resolved_voice,
                    speed=active_speed,
                    language=lang_norm
                )
        except (VoiceQuotaExceededError, VoiceAuthError, VoiceEngineError, Exception) as exc:
            logger.warning(
                f"⚠️ [Voice Router] Provider '{target_provider}' encountered error: {exc}. "
                f"Falling back transparently to Kokoro ONNX offline speech synthesis!"
            )
            # Seamless fallback to Kokoro
            fallback_voice = DEFAULT_VOICE
            audio, sr, meta = self.kokoro.synthesize(
                text=clean_text,
                voice=fallback_voice,
                speed=active_speed,
                language="en-us"
            )
            meta["fallback_from"] = target_provider
            meta["fallback_reason"] = str(exc)

        # 3. Cache the newly synthesized audio
        self.cache.put(cache_key, audio, sr, meta)

        return audio, sr, meta
