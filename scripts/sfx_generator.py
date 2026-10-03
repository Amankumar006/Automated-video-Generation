"""
The Model Verse — Studio-Grade Tactile Foley SFX Engine
Synthesizes broadcast-grade physical UI and motion sound effects (aerodynamic whooshes,
resonant wood/bubble pops, crisp mechanical clicks, crystal formula pings, 808 sub-bass impacts,
cyber laser sweeps, and sparkling brand chimes) using acoustic DSP modeling with NumPy and SciPy.
"""

import os
from pathlib import Path
from typing import Dict, Optional
import numpy as np
import scipy.signal
import soundfile as sf

SAMPLE_RATE = 24000
SFX_DIR = Path(__file__).resolve().parent.parent / "public" / "sfx"


def create_whoosh(duration: float = 0.32, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Aerodynamic filtered air whoosh for camera transitions and motif entrances.
    Uses pink noise with a time-varying resonant bandpass filter and Gaussian bell envelope.
    """
    n_samples = int(sr * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    # Generate pink noise via filtered white noise
    white = np.random.normal(0, 1, n_samples)
    b, a = scipy.signal.butter(1, 0.05, btype="low")
    pink = scipy.signal.lfilter(b, a, white)

    # Smooth Gaussian amplitude envelope
    env = np.exp(-((t - duration * 0.45) ** 2) / (2 * (duration * 0.16) ** 2))

    # Time-varying sweeping resonance tone (air displacement whistle)
    center_freq = 250 + 600 * env
    phase = 2 * np.pi * np.cumsum(center_freq) / sr
    air_tone = np.sin(phase) * 0.25

    audio = (pink * 0.75 + air_tone) * env
    # Anti-click micro-fades
    fade_len = int(sr * 0.015)
    audio[:fade_len] *= np.linspace(0, 1, fade_len)
    audio[-fade_len:] *= np.linspace(1, 0, fade_len)

    peak = np.max(np.abs(audio))
    return (audio / (peak + 1e-8) * 0.75).astype(np.float32)


def create_pop(duration: float = 0.08, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Resonant organic interface / bubble pop for spawning nodes, graphs, and badges.
    Fast pitch drop (850Hz -> 180Hz) with rapid exponential mechanical damping.
    """
    n_samples = int(sr * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    pitch = 850 * np.exp(-t * 45) + 180
    phase = 2 * np.pi * np.cumsum(pitch) / sr
    body = np.sin(phase) * np.exp(-t * 55)
    transient = np.sin(2 * np.pi * 2200 * t) * np.exp(-t * 220) * 0.35
    audio = body + transient

    fade_len = int(sr * 0.002)
    audio[:fade_len] *= np.linspace(0, 1, fade_len)
    peak = np.max(np.abs(audio))
    return (audio / (peak + 1e-8) * 0.80).astype(np.float32)


def create_click(duration: float = 0.045, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Crisp tactile mechanical micro-snap for metric updates, checkboxes, and counters.
    Dual transient impact (contact + latch release) with high-pass 3.4kHz response.
    """
    n_samples = int(sr * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    t1 = t
    t2 = np.maximum(0, t - 0.012)
    click1 = np.sin(2 * np.pi * 3400 * t1) * np.exp(-t1 * 260)
    click2 = np.sin(2 * np.pi * 2600 * t2) * np.exp(-t2 * 220) * 0.60
    audio = click1 + click2

    fade_len = int(sr * 0.001)
    audio[:fade_len] *= np.linspace(0, 1, fade_len)
    peak = np.max(np.abs(audio))
    return (audio / (peak + 1e-8) * 0.70).astype(np.float32)


def create_glass_ping(duration: float = 0.45, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Pure crystalline glass ping / formula chime for LaTeX formula appearance in lower tray.
    Models physical inharmonic modes (f0=1760Hz, f1=4850Hz, f2=9500Hz) with high Q decay.
    """
    n_samples = int(sr * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    f0 = 1760.0
    f1 = f0 * 2.76
    f2 = f0 * 5.40
    m0 = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 8.5)
    m1 = np.sin(2 * np.pi * f1 * t) * np.exp(-t * 18.0) * 0.35
    m2 = np.sin(2 * np.pi * f2 * t) * np.exp(-t * 35.0) * 0.15
    audio = m0 + m1 + m2

    fade_len = int(sr * 0.002)
    audio[:fade_len] *= np.linspace(0, 1, fade_len)
    peak = np.max(np.abs(audio))
    return (audio / (peak + 1e-8) * 0.70).astype(np.float32)


def create_sub_impact(duration: float = 0.42, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Cinematic 808 sub-bass impact for hook punchlines and bottleneck reveals.
    Exponential sweep (110Hz -> 38Hz) with soft tanh saturation and punch transient.
    """
    n_samples = int(sr * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    pitch = 110 * np.exp(-t * 12) + 38
    phase = 2 * np.pi * np.cumsum(pitch) / sr
    env = np.exp(-t * 8.0)
    sine = np.sin(phase) * env
    sat = np.tanh(sine * 2.2) * 0.8
    punch = np.sin(2 * np.pi * 320 * t) * np.exp(-t * 60) * 0.25
    audio = sat + punch

    fade_len = int(sr * 0.003)
    audio[:fade_len] *= np.linspace(0, 1, fade_len)
    peak = np.max(np.abs(audio))
    return (audio / (peak + 1e-8) * 0.85).astype(np.float32)


def create_laser_dispatch(duration: float = 0.20, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Cyber frequency-modulated laser sweep for routing tokens, rays, and data streams.
    Chirped FM sweep (2400Hz -> 300Hz) with sharp decay.
    """
    n_samples = int(sr * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    freq = 2400 * np.exp(-t * 22) + 300
    phase = 2 * np.pi * np.cumsum(freq) / sr
    env = np.exp(-t * 18)
    audio = np.sin(phase) * env

    fade_len = int(sr * 0.002)
    audio[:fade_len] *= np.linspace(0, 1, fade_len)
    peak = np.max(np.abs(audio))
    return (audio / (peak + 1e-8) * 0.70).astype(np.float32)


def create_brand_chime(duration: float = 0.85, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Shimmering D-major pentatonic crystal chime for The Model Verse signature outro.
    Harmonic stack (D5, A5, D6, F#6) with gentle chorus detuning and crystalline decay.
    """
    n_samples = int(sr * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    notes = [
        (587.33, 1.0, 4.0),
        (880.00, 0.70, 5.0),
        (1174.66, 0.45, 6.5),
        (1479.98, 0.30, 8.0)
    ]
    audio = np.zeros(n_samples)
    for freq, amp, decay in notes:
        audio += np.sin(2 * np.pi * freq * t) * np.exp(-t * decay) * amp
        # Chorus detune
        audio += np.sin(2 * np.pi * (freq * 1.004) * t) * np.exp(-t * decay) * (amp * 0.30)

    fade_len = int(sr * 0.003)
    audio[:fade_len] *= np.linspace(0, 1, fade_len)
    peak = np.max(np.abs(audio))
    return (audio / (peak + 1e-8) * 0.75).astype(np.float32)


# Aliases
def create_chime(duration: float = 0.45, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Alias for glass ping / formula chime."""
    return create_glass_ping(duration=duration, sr=sr)


SFX_BUILDERS = {
    "whoosh": create_whoosh,
    "pop": create_pop,
    "click": create_click,
    "glass_ping": create_glass_ping,
    "chime": create_glass_ping,
    "sub_impact": create_sub_impact,
    "laser": create_laser_dispatch,
    "laser_dispatch": create_laser_dispatch,
    "brand_chime": create_brand_chime,
}


def generate_all_sfx(output_dir: Optional[str] = None, sr: int = SAMPLE_RATE) -> Dict[str, str]:
    """Generates and saves the full curated suite of zero-license WAV files to disk."""
    target_dir = Path(output_dir) if output_dir else SFX_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    saved_files = {}

    catalog = {
        "whoosh.wav": create_whoosh(sr=sr),
        "pop.wav": create_pop(sr=sr),
        "click.wav": create_click(sr=sr),
        "glass_ping.wav": create_glass_ping(sr=sr),
        "chime.wav": create_glass_ping(sr=sr),
        "sub_impact.wav": create_sub_impact(sr=sr),
        "laser.wav": create_laser_dispatch(sr=sr),
        "brand_chime.wav": create_brand_chime(sr=sr),
    }

    for fname, data in catalog.items():
        out_path = target_dir / fname
        sf.write(str(out_path), data, sr)
        saved_files[fname] = str(out_path)

    print(f"✅ Generated {len(saved_files)} studio-grade tactile Foley WAV assets in {target_dir}")
    return saved_files


def load_sfx(sound_type: str, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Loads SFX audio buffer from public/sfx/ disk cache, or synthesizes on-the-fly.
    Guarantees zero crashes and instant fallback.
    """
    normalized_type = sound_type.lower().strip()
    # Map common aliases
    alias_map = {
        "swish": "whoosh",
        "formula_ping": "glass_ping",
        "ping": "glass_ping",
        "chime": "glass_ping",
        "bubble": "pop",
        "snap": "click",
        "laser_dispatch": "laser",
        "outro_chime": "brand_chime",
        "sparkle": "brand_chime"
    }
    key = alias_map.get(normalized_type, normalized_type)

    wav_file = SFX_DIR / f"{key}.wav"
    if wav_file.exists():
        try:
            data, file_sr = sf.read(str(wav_file))
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
            if file_sr != sr:
                orig_t = np.linspace(0, len(data) / file_sr, len(data))
                new_t = np.linspace(0, len(data) / file_sr, int(len(data) * sr / file_sr))
                data = np.interp(new_t, orig_t, data)
            return data.astype(np.float32)
        except Exception as e:
            print(f"⚠️ Notice reading {wav_file}: {e}. Falling back to synthesis.")

    if key in SFX_BUILDERS:
        return SFX_BUILDERS[key](sr=sr)

    # Safe fallback: soft click
    return create_click(sr=sr)


if __name__ == "__main__":
    generate_all_sfx()
