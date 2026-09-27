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
    create_whoosh, create_click, create_laser_dispatch,
    create_sub_impact, create_chime
)
from scripts.synth_music_generator import (
    generate_lofi_ambient_soundtrack, mix_master_audio
)
from pipeline.aligner import AcousticForcedAligner, generate_kinetic_sfx_cues

def synthesize_audio_for_spec(
    spec_data: dict,
    voice: str = DEFAULT_VOICE,
    speed: float = DEFAULT_SPEED,
    enable_music: bool = ENABLE_BG_MUSIC,
    duck_gain: float = DEFAULT_DUCK_GAIN,
    normal_gain: float = DEFAULT_NORMAL_GAIN,
    custom_music_path: Optional[str] = None
) -> dict:
    """
    Synthesizes speech, procedural SFX, and mixes an ambient synth soundtrack with dynamic ducking.
    Returns: {"master_audio": str, "narration_audio": str, "soundtrack_audio": str, "timing_data": list, "total_duration": float}
    """
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    spec_id = spec_data.get("id", "short")
    narration_out = os.path.join(PUBLIC_DIR, f"{spec_id}_narration.wav")
    soundtrack_out = os.path.join(PUBLIC_DIR, f"{spec_id}_soundtrack.wav")
    master_out = os.path.join(PUBLIC_DIR, f"{spec_id}_master_audio.wav")

    print(f"🎙️ Synthesizing narration for '{spec_data.get('title', spec_id)}' (Voice: {voice}, Speed: {speed})...")
    kokoro = Kokoro(KOKORO_MODEL_PATH, KOKORO_VOICES_PATH)
    aligner = AcousticForcedAligner(tokenizer=kokoro.tokenizer)
    sr = SAMPLE_RATE
    all_audio = []
    current_time = 0.0
    timing_data = []

    beats = spec_data.get("beats", [])
    for beat in beats:
        text = beat["text"]
        samples, _ = kokoro.create(text, voice=voice, speed=speed, lang="en-us")
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
            "word_timings": word_timings
        })
        print(f"   Beat {beat['beat_id']} [{start:.2f}s -> {end:.2f}s | Slot: {dur + pause_dur:.2f}s | Words: {len(word_timings)}]: \"{text[:45]}...\"")
        all_audio.append(samples)
        # Breath pause between beats
        pause = np.zeros(int(pause_dur * sr), dtype=np.float32)
        all_audio.append(pause)
        current_time = end + pause_dur

    narration_audio = np.concatenate(all_audio)
    total_len = len(narration_audio)
    total_duration = total_len / sr
    sf.write(narration_out, narration_audio, sr)
    print(f"   Total speech duration: {total_duration:.2f}s")

    # SFX Synthesizer
    sfx_builders = {
        "whoosh": create_whoosh,
        "click": create_click,
        "laser": create_laser_dispatch,
        "sub_impact": create_sub_impact,
        "chime": create_chime
    }

    sfx_track = np.zeros(total_len, dtype=np.float32)
    
    # Procedurally align SFX cues to exact acoustic word boundaries
    domain = spec_data.get("domain_taxonomy", "robotics_tamp")
    sfx_cues = generate_kinetic_sfx_cues(timing_data, domain_taxonomy=domain)
    for cue in sfx_cues:
        ts = cue["timestamp"]
        sound_type = cue["sound_type"]
        vol = cue.get("volume", 0.4)
        if sound_type in sfx_builders and ts < total_duration:
            sfx_data = sfx_builders[sound_type]()
            start_idx = int(ts * sr)
            end_idx = min(start_idx + len(sfx_data), total_len)
            avail = end_idx - start_idx
            if avail > 0:
                sfx_track[start_idx:end_idx] += sfx_data[:avail] * vol

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
        "timing_data": timing_data,
        "total_duration": total_duration
    }
