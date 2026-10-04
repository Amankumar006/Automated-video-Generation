"""
The Model Verse — Multi-Category Audio Synthesizer, SFX Mixer & Lo-Fi Ducking Engine
Synthesizes Kokoro-82M neural speech (am_adam), procedural SFX, and mixes
procedural Lo-Fi ambient synthpad soundtracks with dynamic sidechain ducking.
"""

import os
import json
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Optional
from kokoro_onnx import Kokoro
from pipeline.config import (
    KOKORO_MODEL_PATH, KOKORO_VOICES_PATH, SAMPLE_RATE,
    DEFAULT_VOICE, DEFAULT_SPEED, PUBLIC_DIR,
    ENABLE_BG_MUSIC, DEFAULT_DUCK_GAIN, DEFAULT_NORMAL_GAIN, CUSTOM_BG_MUSIC_PATH
)
from scripts.sfx_generator import (
    load_sfx, generate_all_sfx,
    create_whoosh, create_click, create_pop, create_glass_ping,
    create_laser_dispatch, create_sub_impact, create_brand_chime
)
from scripts.synth_music_generator import (
    generate_lofi_ambient_soundtrack, mix_master_audio
)
from pipeline.aligner import AcousticForcedAligner, generate_kinetic_sfx_cues

def ensure_kokoro_models():
    """Ensures Kokoro ONNX model and voices are downloaded."""
    os.makedirs(os.path.dirname(KOKORO_MODEL_PATH), exist_ok=True)
    import urllib.request
    
    if not os.path.exists(KOKORO_MODEL_PATH):
        print(f"📥 Downloading kokoro-v1.0.onnx from official release...")
        url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
        urllib.request.urlretrieve(url, KOKORO_MODEL_PATH)
        print("✅ kokoro-v1.0.onnx downloaded successfully.")

    if not os.path.exists(KOKORO_VOICES_PATH):
        print(f"📥 Downloading voices-v1.0.bin from official release...")
        url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
        urllib.request.urlretrieve(url, KOKORO_VOICES_PATH)
        print("✅ voices-v1.0.bin downloaded successfully.")


def synthesize_audio_for_spec(
    spec_data: dict,
    voice: Optional[str] = None,
    speed: Optional[float] = None,
    enable_music: bool = ENABLE_BG_MUSIC,
    duck_gain: float = DEFAULT_DUCK_GAIN,
    normal_gain: float = DEFAULT_NORMAL_GAIN,
    custom_music_path: Optional[str] = None,
    provider: Optional[str] = None,
    language: Optional[str] = None
) -> dict:
    """
    Synthesizes speech using the unified neural voice router (ElevenLabs, Sarvam AI, Kokoro fallback),
    generates procedural SFX, and mixes an ambient synth soundtrack with dynamic ducking.
    Returns: {"master_audio": str, "narration_audio": str, "soundtrack_audio": str, "timing_data": list, "total_duration": float}
    """
    from pipeline.voice_engine import UnifiedVoiceRouter

    os.makedirs(PUBLIC_DIR, exist_ok=True)
    spec_id = spec_data.get("id", "short")
    narration_out = os.path.join(PUBLIC_DIR, f"{spec_id}_narration.wav")
    soundtrack_out = os.path.join(PUBLIC_DIR, f"{spec_id}_soundtrack.wav")
    master_out = os.path.join(PUBLIC_DIR, f"{spec_id}_master_audio.wav")

    lang = language or spec_data.get("language") or spec_data.get("lang") or "en"
    prov = provider or spec_data.get("tts_provider") or os.environ.get("TTS_PROVIDER", "auto")
    effective_speed = speed if speed is not None else DEFAULT_SPEED
    effective_voice = voice or spec_data.get("voice")

    print(f"🎙️ Synthesizing narration for '{spec_data.get('title', spec_id)}' (Provider: {prov}, Lang: {lang}, Voice: {effective_voice or 'default'}, Speed: {effective_speed}x)...")

    router = UnifiedVoiceRouter()
    
    # Initialize acoustic aligner (using Kokoro tokenizer if available for phonetic precision)
    tokenizer = None
    try:
        if os.path.exists(KOKORO_MODEL_PATH) and os.path.exists(KOKORO_VOICES_PATH):
            kokoro = Kokoro(KOKORO_MODEL_PATH, KOKORO_VOICES_PATH)
            tokenizer = kokoro.tokenizer
    except Exception:
        tokenizer = None
    aligner = AcousticForcedAligner(tokenizer=tokenizer)

    sr = SAMPLE_RATE
    all_audio = []
    current_time = 0.0
    timing_data = []

    beats = spec_data.get("beats", [])
    for beat in beats:
        text = beat["text"]
        samples, sr, meta = router.synthesize_beat(
            text=text,
            voice=effective_voice,
            speed=effective_speed,
            language=lang,
            provider=prov
        )
        dur = len(samples) / sr
        start = current_time
        end = start + dur
        pause_dur = 0.30 if beat != beats[-1] else 0.50

        # Run Acoustic Forced Alignment on this beat
        word_timings = aligner.align_audio_segment(
            audio=samples,
            text=text,
            sample_rate=sr,
            beat_offset=start
        )

        timing_data.append({
            "beat_id": beat["beat_id"],
            "text": text,
            "visual_focus": beat.get("visual_focus", ""),
            "start": round(start, 2),
            "end": round(end, 2),
            "duration": round(dur, 2),
            "slot_duration": round(dur + pause_dur, 2),
            "word_timings": word_timings,
            "provider": meta.get("provider", "tts"),
            "model": meta.get("model", ""),
            "voice": meta.get("voice_id") or meta.get("speaker") or meta.get("voice")
        })
        provider_badge = meta.get("provider", "tts").upper()
        print(f"   Beat {beat['beat_id']} [{start:.2f}s -> {end:.2f}s | {provider_badge} | Words: {len(word_timings)}]: \"{text[:45]}...\"")
        all_audio.append(samples)
        # Breath pause between beats
        pause = np.zeros(int(pause_dur * sr), dtype=np.float32)
        all_audio.append(pause)
        current_time = end + pause_dur

    narration_audio = np.concatenate(all_audio)
    total_len = len(narration_audio)
    total_duration = total_len / sr
    sf.write(narration_out, narration_audio, sr)
    print(f"   Total speech duration: {total_duration:.2f}s (Cache hits: {router.cache.stats['hits']})")

    # Kinetic Subtitles & Phrase Chunks (SRT & ASS Export)
    srt_out = os.path.join(PUBLIC_DIR, f"{spec_id}.srt")
    ass_out = os.path.join(PUBLIC_DIR, f"{spec_id}.ass")
    caption_chunks = []
    try:
        from pipeline.subtitle_generator import generate_phrase_chunks, export_srt, export_ass
        enriched_beats = []
        for b in beats:
            b_copy = dict(b)
            for td in timing_data:
                if td["beat_id"] == b.get("beat_id"):
                    b_copy["word_timings"] = td.get("word_timings", [])
                    b_copy["start"] = td["start"]
                    b_copy["end"] = td["end"]
            enriched_beats.append(b_copy)
        caption_chunks = generate_phrase_chunks(enriched_beats)
        export_srt(caption_chunks, srt_out)
        export_ass(caption_chunks, ass_out, title=spec_data.get("title", spec_id))
    except Exception as e:
        print(f"⚠️ Notice generating subtitles: {e}")

    # Tactile Foley SFX Synthesizer & Spatial Track Mixer
    sfx_out = os.path.join(PUBLIC_DIR, f"{spec_id}_sfx_track.wav")
    sfx_track = np.zeros(total_len, dtype=np.float32)

    # Procedurally align SFX cues to exact acoustic word boundaries & Manim visual moments
    domain = spec_data.get("domain_taxonomy", "robotics_tamp")
    sfx_cues = generate_kinetic_sfx_cues(timing_data, domain_taxonomy=domain, spec=spec_data)
    print(f"🔊 [Tactile SFX Engine] Mixed {len(sfx_cues)} tactile Foley cues across {len(timing_data)} beats...")

    for cue in sfx_cues:
        ts = cue["timestamp"]
        sound_type = cue["sound_type"]
        vol = cue.get("volume", 0.35)
        if ts < total_duration:
            sfx_data = load_sfx(sound_type, sr=sr)
            start_idx = int(ts * sr)
            end_idx = min(start_idx + len(sfx_data), total_len)
            avail = end_idx - start_idx
            if avail > 0:
                sfx_track[start_idx:end_idx] += sfx_data[:avail] * vol

    # Peak normalize sfx_track to prevent harsh transients
    sfx_peak = np.max(np.abs(sfx_track))
    if sfx_peak > 0.85:
        sfx_track = sfx_track * (0.85 / sfx_peak)
    sf.write(sfx_out, sfx_track, sr)

    # Background Soundtrack & Dynamic Ducking
    if enable_music:
        music_file = custom_music_path or CUSTOM_BG_MUSIC_PATH
        if music_file and os.path.exists(music_file):
            print(f"🎵 Loading custom soundtrack: {music_file}")
            soundtrack, music_sr = sf.read(music_file)
            if len(soundtrack.shape) > 1:
                soundtrack = np.mean(soundtrack, axis=1)
            if music_sr != sr:
                orig_t = np.linspace(0, len(soundtrack) / music_sr, len(soundtrack))
                new_t = np.linspace(0, len(soundtrack) / music_sr, int(len(soundtrack) * sr / music_sr))
                soundtrack = np.interp(new_t, orig_t, soundtrack).astype(np.float32)
            if len(soundtrack) < total_len:
                repeats = int(np.ceil(total_len / len(soundtrack)))
                soundtrack = np.tile(soundtrack, repeats)[:total_len]
            else:
                soundtrack = soundtrack[:total_len]
        else:
            print(f"🎹 Synthesizing procedural Lo-Fi ambient synth soundtrack ({total_duration:.2f}s)...")
            soundtrack = generate_lofi_ambient_soundtrack(total_duration, sr=sr)

        sf.write(soundtrack_out, soundtrack, sr)

        print(f"🎚️ Applying dynamic audio ducking (Speech: {duck_gain * 100:.0f}%, Pauses: {normal_gain * 100:.0f}%)...")
        master = mix_master_audio(
            narration=narration_audio,
            soundtrack=soundtrack,
            sfx=sfx_track,
            sr=sr,
            duck_gain=duck_gain,
            normal_gain=normal_gain
        )
    else:
        master = narration_audio * 0.95 + sfx_track * 0.75
        peak = np.max(np.abs(master))
        if peak > 0.95:
            master = master * (0.95 / peak)

    sf.write(master_out, master.astype(np.float32), sr)
    print(f"✅ Master audio mixed with dynamic ducking: {master_out}")

    return {
        "master_audio": master_out,
        "narration_audio": narration_out,
        "soundtrack_audio": soundtrack_out if enable_music else "",
        "sfx_audio": sfx_out,
        "sfx_cues": sfx_cues,
        "srt_file": srt_out,
        "ass_file": ass_out,
        "caption_chunks": caption_chunks,
        "timing_data": timing_data,
        "total_duration": total_duration
    }
