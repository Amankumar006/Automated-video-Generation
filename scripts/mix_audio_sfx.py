import soundfile as sf
import numpy as np
import os
from sfx_generator import (
    create_whoosh,
    create_click,
    create_laser_dispatch,
    create_sub_impact,
    create_chime,
    SAMPLE_RATE
)

def generate_master_audio(narration_path="public/deepseek_v3_clean_adam.wav", output_path="public/deepseek_v3_master_audio.wav"):
    narration, sr = sf.read(narration_path)
    total_len = len(narration)
    total_duration = total_len / sr
    print(f"🎙️ Narration duration: {total_duration:.2f}s, SR: {sr}")

    # SFX events: (timestamp_seconds, sfx_sound, volume)
    sfx_events = [
        (0.8, create_sub_impact(), 0.45),      # Beat 1: 671B impact
        (5.9, create_whoosh(), 0.35),          # Transition to Beat 2
        (7.5, create_sub_impact(), 0.40),      # Dense overload pulse
        (14.8, create_whoosh(), 0.35),         # Transition to Beat 3
        (15.5, create_click(), 0.30),          # 256 constellation grid
        (22.5, create_chime(), 0.35),          # Beat 4: Shared Expert activation
        (27.8, create_whoosh(), 0.35),         # Transition to Beat 5 router
        (28.8, create_click(), 0.35),          # Token enters
        (29.8, create_laser_dispatch(), 0.45), # Laser routing to top-8
        (33.8, create_sub_impact(), 0.50),     # Beat 6: 37B punchline
        (42.8, create_whoosh(), 0.35),         # Transition to Beat 7 Outro
        (43.6, create_click(), 0.40),          # Follow CTA click
        (44.3, create_chime(), 0.40),          # themodelverse.in chime
    ]

    sfx_track = np.zeros(total_len, dtype=np.float32)
    for ts, sfx_data, vol in sfx_events:
        start_idx = int(ts * sr)
        end_idx = min(start_idx + len(sfx_data), total_len)
        available = end_idx - start_idx
        if available > 0:
            sfx_track[start_idx:end_idx] += sfx_data[:available] * vol

    # Mix voice (1.0) + SFX (0.8)
    master = narration * 0.95 + sfx_track * 0.75
    # Normalize to prevent any clipping
    peak = np.max(np.abs(master))
    if peak > 0.96:
        master = master * (0.96 / peak)

    sf.write(output_path, master.astype(np.float32), sr)
    print(f"✅ Master audio mixed successfully to: {output_path}")
    return output_path

if __name__ == "__main__":
    generate_master_audio()
