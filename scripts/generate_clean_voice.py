from kokoro_onnx import Kokoro
import soundfile as sf
import numpy as np

sentences = [
    "DeepSeek-V3 has 671 billion parameters. But running it costs almost nothing. How?",
    "In a standard dense model, every single word forces all 671 billion weights to calculate at once. A massive brute-force bottleneck.",
    "DeepSeek flips this with Sparse Mixture of Experts, dividing the entire model into 256 specialized sub-networks.",
    "Plus one permanently active shared expert that never sleeps, capturing universal knowledge.",
    "When a token enters, a high-speed router scores affinity, dispatching to only the top 8 experts.",
    "The result? 671 billion parameters of intelligence, but only 37 billion active per token. 94 percent of compute, saved.",
    "Follow The Model Verse for more deep architecture breakdowns like this."
]

kokoro = Kokoro("kokoro_models/kokoro-v1.0.onnx", "kokoro_models/voices-v1.0.bin")
sr = 24000
all_audio = []
current_time = 0.0
timing_data = []

for i, sent in enumerate(sentences):
    samples, _ = kokoro.create(sent, voice="am_adam", speed=1.12, lang="en-us")
    dur = len(samples) / sr
    start = current_time
    end = start + dur
    timing_data.append({
        "beat": i + 1,
        "text": sent,
        "start": round(start, 2),
        "end": round(end, 2),
        "duration": round(dur, 2)
    })
    all_audio.append(samples)
    pause = np.zeros(int(0.28 * sr), dtype=np.float32)
    all_audio.append(pause)
    current_time = end + 0.28

final_audio = np.concatenate(all_audio)
sf.write("public/deepseek_v3_clean_adam.wav", final_audio, sr)
print(f"Total audio duration: {current_time:.2f}s")
for b in timing_data:
    b_num = b['beat']
    b_st = b['start']
    b_en = b['end']
    b_dur = b['duration']
    b_txt = b['text'][:45]
    print(f"Beat {b_num}: [{b_st}s -> {b_en}s] ({b_dur}s) \"{b_txt}...\"")
