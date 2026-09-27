"""
The Model Verse — Procedural SFX Audio Generator
Synthesizes broadcast-grade UI sound effects (whooshes, laser pulses, sub-bass impacts, digital clicks)
using pure NumPy and SoundFile.
"""

import numpy as np
import soundfile as sf
import os

SAMPLE_RATE = 24000

def create_whoosh(duration=0.35, sr=SAMPLE_RATE):
    """Smooth filtered noise whoosh for camera transitions."""
    t = np.linspace(0, duration, int(sr * duration))
    # Gaussian envelope
    env = np.exp(-((t - duration * 0.5) ** 2) / (2 * (duration * 0.18) ** 2))
    noise = np.random.uniform(-1, 1, len(t))
    # Simple lowpass moving average
    window_size = 40
    filtered = np.convolve(noise, np.ones(window_size)/window_size, mode='same')
    # Add subtle pitch swoop
    freq = np.linspace(200, 600, len(t))
    tone = np.sin(2 * np.pi * freq * t) * 0.2
    audio = (filtered * 0.8 + tone) * env * 0.35
    return audio.astype(np.float32)

def create_click(duration=0.06, sr=SAMPLE_RATE):
    """Crisp high-frequency UI pop / click."""
    t = np.linspace(0, duration, int(sr * duration))
    env = np.exp(-t * 80)
    freq = np.linspace(1800, 600, len(t))
    audio = np.sin(2 * np.pi * freq * t) * env * 0.4
    return audio.astype(np.float32)

def create_laser_dispatch(duration=0.22, sr=SAMPLE_RATE):
    """Cyber laser beam chirp for token routing."""
    t = np.linspace(0, duration, int(sr * duration))
    env = np.exp(-t * 22)
    freq = np.linspace(2200, 320, len(t))
    audio = np.sin(2 * np.pi * freq * t) * env * 0.3
    return audio.astype(np.float32)

def create_sub_impact(duration=0.45, sr=SAMPLE_RATE):
    """Deep sub-bass impact for big number / punchline reveals."""
    t = np.linspace(0, duration, int(sr * duration))
    env = np.exp(-t * 9)
    freq = np.linspace(110, 42, len(t))
    audio = np.sin(2 * np.pi * freq * t) * env * 0.5
    return audio.astype(np.float32)

def create_chime(duration=0.6, sr=SAMPLE_RATE):
    """Elegant harmonic chime for success / follow CTA."""
    t = np.linspace(0, duration, int(sr * duration))
    env = np.exp(-t * 5)
    f1 = np.sin(2 * np.pi * 587.33 * t) # D5
    f2 = np.sin(2 * np.pi * 880.00 * t) * 0.5 # A5
    f3 = np.sin(2 * np.pi * 1174.66 * t) * 0.25 # D6
    audio = (f1 + f2 + f3) * env * 0.3
    return audio.astype(np.float32)

def build_sfx_track(total_duration, sfx_events, sr=SAMPLE_RATE, output_file="public/sfx_track.wav"):
    """
    Assembles a timeline of SFX events into a single audio track.
    sfx_events is a list of tuples: (timestamp_sec, sfx_array)
    """
    total_samples = int(total_duration * sr)
    track = np.zeros(total_samples, dtype=np.float32)

    for timestamp, audio in sfx_events:
        start_idx = int(timestamp * sr)
        end_idx = min(start_idx + len(audio), total_samples)
        available = end_idx - start_idx
        if available > 0:
            track[start_idx:end_idx] += audio[:available]

    # Normalize to avoid clipping
    peak = np.max(np.abs(track))
    if peak > 0.95:
        track = track * (0.95 / peak)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    sf.write(output_file, track, sr)
    print(f"🎵 Generated SFX track: {output_file} ({total_duration:.2f}s, {len(sfx_events)} cues)")
    return output_file

if __name__ == "__main__":
    os.makedirs("public/sfx", exist_ok=True)
    sf.write("public/sfx/whoosh.wav", create_whoosh(), SAMPLE_RATE)
    sf.write("public/sfx/click.wav", create_click(), SAMPLE_RATE)
    sf.write("public/sfx/laser.wav", create_laser_dispatch(), SAMPLE_RATE)
    sf.write("public/sfx/sub_impact.wav", create_sub_impact(), SAMPLE_RATE)
    sf.write("public/sfx/chime.wav", create_chime(), SAMPLE_RATE)
    print("✅ All procedural SFX generated successfully in public/sfx/")
