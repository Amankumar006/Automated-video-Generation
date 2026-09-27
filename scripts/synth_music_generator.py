"""
The Model Verse — Procedural Lo-Fi Ambient Synth Generator & Dynamic Ducking Engine
Generates copyright-free mathematical synthwave pad progressions (3Blue1Brown aesthetic)
and applies sample-accurate sidechain ducking under Kokoro neural narration.
"""

import os
import numpy as np
import soundfile as sf
from typing import Optional

SAMPLE_RATE = 24000

# Frequencies for D Minor / Cybernetic Chalkboard Pad Progression
# Chords: Dm9 -> Bbmaj9 -> Gm9 -> Asus4/A7
CHORD_PROGRESSION = [
    # Dm9: D2 (root), D3, F3, A3, C4, E4
    {"root": 73.42, "notes": [146.83, 174.61, 220.00, 261.63, 329.63]},
    # Bbmaj9: Bb1 (root), Bb2, D3, F3, A3, C4
    {"root": 58.27, "notes": [116.54, 146.83, 174.61, 220.00, 261.63]},
    # Gm9: G1 (root), G2, Bb2, D3, F3, A3
    {"root": 49.00, "notes": [98.00, 116.54, 146.83, 174.61, 220.00]},
    # Asus4 / A7: A1 (root), A2, D3, E3, G3, C#4
    {"root": 55.00, "notes": [110.00, 146.83, 164.81, 196.00, 277.18]}
]

def synthesize_pad_chord(notes: list, root_freq: float, duration: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Synthesizes a lush, analog detuned pad chord with sub-bass foundation and subtle tape drift."""
    n_samples = int(duration * sr)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    
    # 1. Analog tape wow & flutter LFO (0.28 Hz subtle pitch drift)
    tape_lfo = np.sin(2 * np.pi * 0.28 * t) * 0.0025
    
    chord_wave = np.zeros(n_samples, dtype=np.float32)
    
    # Detuned unison oscillators for each note in the chord
    for f in notes:
        # Voice 1: Center
        v1 = np.sin(2 * np.pi * f * (t + tape_lfo))
        # Voice 2: Sharp detune (+0.18%)
        v2 = np.sin(2 * np.pi * (f * 1.0018) * (t - tape_lfo))
        # Voice 3: Flat detune (-0.18%)
        v3 = np.sin(2 * np.pi * (f * 0.9982) * t)
        # Soft triangle harmonic overtone
        v4 = (2.0 / np.pi) * np.arcsin(np.sin(2 * np.pi * (f * 2.0) * t)) * 0.25
        chord_wave += (v1 + v2 + v3 + v4) * 0.06

    # 2. Sub-bass foundation drone (root frequency + sub octave)
    sub1 = np.sin(2 * np.pi * root_freq * t) * 0.28
    sub2 = np.sin(2 * np.pi * (root_freq * 0.5) * t) * 0.16
    
    # 3. Soft harmonic high bell/chime arpeggio notes
    bell_wave = np.zeros(n_samples, dtype=np.float32)
    arp_rate = 0.50  # note every 0.5 seconds
    n_arps = int(duration / arp_rate)
    for i in range(n_arps):
        arp_time = i * arp_rate
        arp_idx = int(arp_time * sr)
        note_f = notes[(i * 2 + 1) % len(notes)] * 2.0  # octave up
        decay_dur = min(1.2, duration - arp_time)
        if decay_dur > 0.05:
            decay_len = int(decay_dur * sr)
            t_decay = np.linspace(0, decay_dur, decay_len, endpoint=False)
            bell_env = np.exp(-t_decay * 4.5)
            bell_tone = np.sin(2 * np.pi * note_f * t_decay) * bell_env * 0.05
            end_idx = min(arp_idx + decay_len, n_samples)
            avail = end_idx - arp_idx
            bell_wave[arp_idx:end_idx] += bell_tone[:avail]

    # Combine layers
    raw_audio = chord_wave + sub1 + sub2 + bell_wave

    # 4. Soft ADSR Envelope (Gentle swell in and fade out)
    attack_time = min(0.8, duration * 0.25)
    release_time = min(0.8, duration * 0.25)
    env = np.ones(n_samples, dtype=np.float32)
    
    att_samples = int(attack_time * sr)
    rel_samples = int(release_time * sr)
    if att_samples > 0:
        env[:att_samples] = 0.5 * (1 - np.cos(np.linspace(0, np.pi, att_samples)))
    if rel_samples > 0:
        env[-rel_samples:] = 0.5 * (1 + np.cos(np.linspace(0, np.pi, rel_samples)))

    audio = raw_audio * env

    # 5. Warm analog tape saturation (tanh soft limiting)
    audio = np.tanh(audio * 1.35) * 0.75
    return audio.astype(np.float32)

def generate_lofi_ambient_soundtrack(total_duration: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Generates a full continuous ambient synthwave soundtrack for the exact duration of the short.
    Uses overlapping cross-fading chord cycles for seamless, endless harmonic progression.
    """
    chord_dur = 4.2  # seconds per chord
    overlap = 0.8    # crossfade overlap in seconds
    step = chord_dur - overlap

    n_samples = int(total_duration * sr)
    soundtrack = np.zeros(n_samples + int(chord_dur * sr), dtype=np.float32)

    current_time = 0.0
    chord_idx = 0

    while current_time < total_duration:
        chord_info = CHORD_PROGRESSION[chord_idx % len(CHORD_PROGRESSION)]
        chord_audio = synthesize_pad_chord(
            notes=chord_info["notes"],
            root_freq=chord_info["root"],
            duration=chord_dur,
            sr=sr
        )
        start_idx = int(current_time * sr)
        end_idx = start_idx + len(chord_audio)
        soundtrack[start_idx:end_idx] += chord_audio
        current_time += step
        chord_idx += 1

    # Crop to exact duration
    final_track = soundtrack[:n_samples]

    # Global fade in (first 1.5s) and fade out (last 2.0s)
    fade_in_len = int(1.5 * sr)
    fade_out_len = int(2.0 * sr)
    if fade_in_len < n_samples:
        final_track[:fade_in_len] *= 0.5 * (1 - np.cos(np.linspace(0, np.pi, fade_in_len)))
    if fade_out_len < n_samples:
        final_track[-fade_out_len:] *= 0.5 * (1 + np.cos(np.linspace(0, np.pi, fade_out_len)))

    # Gentle low-pass smoothing (removes high harshness)
    filter_kernel_size = 7
    kernel = np.ones(filter_kernel_size, dtype=np.float32) / filter_kernel_size
    final_track = np.convolve(final_track, kernel, mode="same")

    return final_track.astype(np.float32)

def compute_dynamic_ducking_envelope(
    narration: np.ndarray,
    sr: int = SAMPLE_RATE,
    duck_gain: float = 0.10,    # -20 dB during voiceover
    normal_gain: float = 0.32,  # -10 dB during breath pauses & outro
    threshold: float = 0.018,
    attack_ms: float = 80.0,
    release_ms: float = 350.0
) -> np.ndarray:
    """
    Computes sample-accurate sidechain ducking envelope from narration signal.
    Ducks background music smoothly when speech is present, and swells up during pauses.
    """
    n_samples = len(narration)
    
    # 1. Compute instant power / rectified amplitude
    rectified = np.abs(narration)
    
    # Block-level RMS energy window (20ms frames)
    frame_len = int(0.020 * sr)
    if frame_len > 0:
        kernel = np.ones(frame_len, dtype=np.float32) / frame_len
        smoothed_power = np.sqrt(np.convolve(rectified ** 2, kernel, mode="same") + 1e-9)
    else:
        smoothed_power = rectified

    # 2. Target gain vector based on voice activity
    is_speaking = smoothed_power > threshold
    target_gain = np.where(is_speaking, duck_gain, normal_gain).astype(np.float32)

    # 3. Dynamic Attack & Release Filter
    # Fast attack: drops quickly to keep speech intelligible
    # Smooth release: swells naturally without pumping or flutter
    alpha_attack = 1.0 - np.exp(-1.0 / (sr * (attack_ms / 1000.0)))
    alpha_release = 1.0 - np.exp(-1.0 / (sr * (release_ms / 1000.0)))

    envelope = np.zeros(n_samples, dtype=np.float32)
    current_gain = normal_gain

    # Run vectorized downsampled filter for blazing speed, then interpolate
    step = 40  # filter every 40 samples (~1.6ms resolution)
    down_targets = target_gain[::step]
    down_env = np.zeros(len(down_targets), dtype=np.float32)
    
    for i in range(len(down_targets)):
        target = down_targets[i]
        if target < current_gain:
            current_gain += alpha_attack * step * (target - current_gain)
        else:
            current_gain += alpha_release * step * (target - current_gain)
        down_env[i] = current_gain

    # Interpolate back to full sample rate
    xp = np.arange(len(down_env)) * step
    x_full = np.arange(n_samples)
    envelope = np.interp(x_full, xp, down_env).astype(np.float32)
    return envelope

def mix_master_audio(
    narration: np.ndarray,
    soundtrack: np.ndarray,
    sfx: Optional[np.ndarray] = None,
    sr: int = SAMPLE_RATE,
    duck_gain: float = 0.10,
    normal_gain: float = 0.32
) -> np.ndarray:
    """
    Produces final master audio by sidechain ducking the soundtrack under narration,
    overlaying procedural SFX, and applying soft master limiting.
    """
    total_len = len(narration)
    
    # Ensure soundtrack matches total length
    if len(soundtrack) < total_len:
        pad = np.zeros(total_len - len(soundtrack), dtype=np.float32)
        soundtrack = np.concatenate([soundtrack, pad])
    else:
        soundtrack = soundtrack[:total_len]

    # Compute and apply dynamic ducking envelope
    duck_env = compute_dynamic_ducking_envelope(
        narration=narration,
        sr=sr,
        duck_gain=duck_gain,
        normal_gain=normal_gain
    )
    ducked_music = soundtrack * duck_env

    # Base mix
    master = narration * 0.95 + ducked_music

    # Overlay SFX if present
    if sfx is not None:
        sfx_matched = sfx[:total_len] if len(sfx) >= total_len else np.pad(sfx, (0, total_len - len(sfx)))
        master += sfx_matched * 0.70

    # Broadcast Ceiling Limiter (prevents clipping, targets -0.5 dB peak = 0.94)
    peak = np.max(np.abs(master))
    if peak > 0.94:
        master = master * (0.94 / peak)

    return master.astype(np.float32)

if __name__ == "__main__":
    test_dur = 15.0
    print(f"🎵 Generating test Lo-Fi ambient synth track ({test_dur}s)...")
    music = generate_lofi_ambient_soundtrack(test_dur)
    os.makedirs("public/audio", exist_ok=True)
    sf.write("public/audio/test_ambient_synth.wav", music, SAMPLE_RATE)
    print("✅ Test soundtrack saved to public/audio/test_ambient_synth.wav")
