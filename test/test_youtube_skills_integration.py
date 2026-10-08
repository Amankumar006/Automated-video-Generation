"""
Test Suite: YouTube Skills Core Pipeline Integration
Verifies:
1. Hook Scoring Gating (skills/yt-script/hookscore.py into pipeline/script_generator.py & pipeline/hook_optimizer.py)
2. Dead-Air Audio Compression (skills/yt-edit/deadair.py into pipeline/audio_generator.py & pipeline/audio_synthesizer.py)
3. Mobile Title Linting (skills/yt-package/title.py into pipeline/youtube_publisher.py & pipeline/publisher.py)
"""

import io
import os
import sys
import copy
import pytest
import numpy as np
import soundfile as sf
from pathlib import Path
from pydub import AudioSegment

def make_tone_segment(duration_ms: int, freq: float = 440.0, sr: int = 24000) -> AudioSegment:
    t = np.linspace(0, duration_ms / 1000.0, int(sr * duration_ms / 1000.0), endpoint=False)
    samples = (0.5 * np.sin(2 * np.pi * freq * t) * 32767).astype(np.int16)
    buf = io.BytesIO()
    sf.write(buf, samples, sr, format="WAV", subtype="PCM_16")
    buf.seek(0)
    return AudioSegment.from_file(buf, format="wav")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.hook_optimizer import (
    score_hook,
    generate_hook_candidates,
    gate_and_select_best_hook,
    optimize_script_hook
)
from pipeline.audio_generator import (
    detect_dead_air_gaps,
    adjust_cue_timestamps,
    compress_dead_air,
    DEFAULT_DEAD_AIR_FLOOR_MS,
    DEFAULT_TARGET_GAP_MS
)
from pipeline.youtube_publisher import (
    lint_title,
    optimize_title_for_mobile,
    generate_shorts_metadata,
    MOBILE_SHORTS_MAX_CHARS,
    MOBILE_SHORTS_OPTIMAL_CHARS
)


# ==============================================================================
# 1. Hook Scoring Gating Tests
# ==============================================================================

def test_hookscore_properties_and_weakest_link_weighting():
    """Verify hookscore evaluates the 5 properties and applies 60% mean + 40% weakest link."""
    # Balanced strong hook
    strong_text = "Why do 90% of your GPU cycles waste time waiting on memory before FlashAttention fixes it?"
    res_strong = score_hook(strong_text)

    props = res_strong["properties"]
    assert "SPECIFICITY" in props
    assert "ADDRESS" in props
    assert "STAKES" in props
    assert "CURIOSITY" in props
    assert "BREVITY" in props

    vals = list(props.values())
    expected_verdict = round(0.6 * (sum(vals) / len(vals)) + 0.4 * min(vals))
    assert res_strong["verdict"] == expected_verdict
    assert res_strong["band"] in ("STRONG", "WORKABLE", "WEAK")
    assert res_strong["verdict"] >= 50

    # Imbalanced hook with weak brevity (way too short, 2 words)
    short_text = "Watch this."
    res_short = score_hook(short_text)
    # The weakest property should severely drag down the verdict
    assert min(res_short["properties"].values()) <= 35
    assert res_short["verdict"] < 50
    assert res_short["band"] == "WEAK"


def test_hook_candidate_generation_archetypes():
    """Verify candidate generation creates archetypes inspired by hooks.json."""
    topic = "FlashAttention-3"
    meta = {"payoff_stat": "1.2 PFLOPS", "scale_metric": "94%"}
    candidates = generate_hook_candidates(topic=topic, metadata=meta)

    assert len(candidates) >= 5
    cand_str = " ".join(candidates)

    # Check for archetype patterns from hooks.json:
    # 1. The Statistic (% or metric)
    assert any("%" in c or "PFLOPS" in c for c in candidates)
    # 2. Address / Mistake ("you")
    assert any("you" in c.lower() for c in candidates)
    # 3. Contrarian / Warning ("everyone" or "do not" or "stop")
    assert any("everyone" in c.lower() or "do not" in c.lower() or "stop" in c.lower() for c in candidates)
    # 4. Question ("why")
    assert any("why" in c.lower() for c in candidates)


def test_hook_gating_selects_highest_score():
    """Verify gate_and_select_best_hook evaluates all candidates and picks highest verdict."""
    candidates = [
        "Welcome guys, today we are going to explore a new AI paper about attention.", # Vague, filler, weak
        "FlashAttention is cool.", # Low curiosity, short
        "Over 60% of your GPU cycles waste time waiting on memory before FlashAttention-3 fixes it." # Specific, stakes, address
    ]

    winner, win_eval, all_evals = gate_and_select_best_hook(candidates)
    assert winner == candidates[2]
    assert win_eval["verdict"] > all_evals[-1]["verdict"]
    assert len(all_evals) == 3
    # Sorted descending by score
    assert all_evals[0]["verdict"] >= all_evals[1]["verdict"] >= all_evals[2]["verdict"]


def test_script_generator_spec_hook_integration():
    """Verify optimize_script_hook updates Beat 1 and stores hook_gating audit."""
    spec = {
        "id": "flashattention_3",
        "title": "FlashAttention-3: Fast GPU Kernels",
        "beats": [
            {
                "beat_id": 1,
                "text": "Today we look at standard attention kernels in deep learning.",
                "visual_focus": "Hardware matrix"
            },
            {
                "beat_id": 2,
                "text": "The memory bus is completely choked by redundant reads.",
                "visual_focus": "Memory bus"
            }
        ]
    }

    optimized = optimize_script_hook(spec)
    assert "hook_gating" in optimized
    audit = optimized["hook_gating"]
    assert "selected_hook" in audit
    assert "verdict" in audit
    assert "band" in audit
    assert audit["candidates_evaluated"] >= 5

    # Beat 1 text replaced by winning hook
    assert optimized["beats"][0]["text"] == audit["selected_hook"]
    assert "hook_score" in optimized["beats"][0]
    assert optimized["beats"][0]["hook_score"] == audit["verdict"]


def test_hook_gating_empty_candidates_error():
    """Verify ValueError is raised if candidate list is empty."""
    with pytest.raises(ValueError):
        gate_and_select_best_hook([])


# ==============================================================================
# 2. Dead-Air Audio Compression Tests
# ==============================================================================

def test_detect_dead_air_gaps_threshold():
    """Verify dead-air detection flags gaps > 250ms and ignores gaps <= 250ms."""
    cues = [
        {"start": 0.0, "end": 1.0, "text": "Sentence one."},
        {"start": 1.15, "end": 2.0, "text": "Sentence two."},   # Gap = 150ms (<= 250ms, keep)
        {"start": 2.60, "end": 3.5, "text": "Sentence three."},  # Gap = 600ms (> 250ms, dead air)
        {"start": 3.70, "end": 4.5, "text": "Sentence four."},   # Gap = 200ms (<= 250ms, keep)
        {"start": 4.90, "end": 5.5, "text": "Sentence five."}    # Gap = 400ms (> 250ms, dead air)
    ]

    cuts = detect_dead_air_gaps(cues, floor_ms=250.0, target_gap_ms=150.0)
    assert len(cuts) == 2

    # First cut is between cue 1 and 2
    assert cuts[0]["cue_index"] == 2
    assert cuts[0]["gap_duration_ms"] == pytest.approx(600.0)
    assert cuts[0]["excess_ms"] == pytest.approx(450.0)

    # Second cut is between cue 3 and 4
    assert cuts[1]["cue_index"] == 4
    assert cuts[1]["gap_duration_ms"] == pytest.approx(400.0)
    assert cuts[1]["excess_ms"] == pytest.approx(250.0)


def test_adjust_cue_timestamps():
    """Verify cue timestamps are shifted backwards by the exact excess dead-air duration."""
    cues = [
        {
            "start": 0.0,
            "end": 1.0,
            "text": "Hello world",
            "word_timings": [{"word": "Hello", "start": 0.0, "end": 0.4}, {"word": "world", "start": 0.5, "end": 1.0}]
        },
        {
            "start": 1.6,
            "end": 2.5,
            "text": "Second phrase",
            "word_timings": [{"word": "Second", "start": 1.6, "end": 2.0}, {"word": "phrase", "start": 2.1, "end": 2.5}]
        }
    ]

    # Gap = 600ms, target = 150ms -> excess = 450ms (0.45s)
    cuts = detect_dead_air_gaps(cues, floor_ms=250.0, target_gap_ms=150.0)
    adjusted = adjust_cue_timestamps(cues, cuts)

    # First cue unchanged
    assert adjusted[0]["start"] == 0.0
    assert adjusted[0]["end"] == 1.0
    assert adjusted[0]["word_timings"][0]["start"] == 0.0

    # Second cue shifted backwards by 0.45s: 1.6 -> 1.15, 2.5 -> 2.05
    assert adjusted[1]["start"] == pytest.approx(1.15, abs=0.01)
    assert adjusted[1]["end"] == pytest.approx(2.05, abs=0.01)
    assert adjusted[1]["word_timings"][0]["start"] == pytest.approx(1.15, abs=0.01)

    # The resulting gap between cue 0 end and cue 1 start is exactly 150ms
    new_gap_ms = (adjusted[1]["start"] - adjusted[0]["end"]) * 1000.0
    assert new_gap_ms == pytest.approx(150.0, abs=5.0)


def test_compress_dead_air_audio_segment():
    """Verify AudioSegment dead-air compression removes silence and maintains target gap."""
    # Create audio: 1000ms tone, 600ms silence, 1000ms tone
    tone1 = make_tone_segment(duration_ms=1000)
    silence = AudioSegment.silent(duration=600)
    tone2 = make_tone_segment(duration_ms=1000)
    combined = tone1 + silence + tone2

    cues = [
        {"start": 0.0, "end": 1.0, "text": "Tone 1"},
        {"start": 1.6, "end": 2.6, "text": "Tone 2"}
    ]

    res = compress_dead_air(combined, cues=cues, floor_ms=250.0, target_gap_ms=150.0)
    assert res["cuts_count"] == 1
    # Original: 2.6s. Cut removed 450ms. Compressed: ~2.15s
    assert res["original_duration_s"] == pytest.approx(2.6, abs=0.05)
    assert res["compressed_duration_s"] == pytest.approx(2.15, abs=0.05)
    assert res["time_saved_s"] == pytest.approx(0.45, abs=0.05)


def test_compress_dead_air_numpy_waveform():
    """Verify numpy audio array dead-air compression operates correctly."""
    sr = 24000
    # 2.8s total: 1s speech, 600ms silence, 1.2s speech
    audio = np.zeros(int(2.8 * sr), dtype=np.float32)
    audio[0:int(1.0 * sr)] = 0.4
    audio[int(1.6 * sr):int(2.8 * sr)] = 0.4

    cues = [
        {"start": 0.0, "end": 1.0, "text": "Speech 1"},
        {"start": 1.6, "end": 2.8, "text": "Speech 2"}
    ]

    res = compress_dead_air(audio, cues=cues, floor_ms=250.0, target_gap_ms=150.0, sample_rate=sr)
    assert res["cuts_count"] == 1
    assert res["time_saved_s"] > 0.40
    assert len(res["adjusted_cues"]) == 2


def test_compress_dead_air_no_cuts_when_pacing_tight():
    """Verify audio with gaps <= 250ms is untouched."""
    tone1 = make_tone_segment(duration_ms=1000)
    silence = AudioSegment.silent(duration=180) # 180ms gap
    tone2 = make_tone_segment(duration_ms=1000)
    combined = tone1 + silence + tone2

    cues = [
        {"start": 0.0, "end": 1.0, "text": "Tone 1"},
        {"start": 1.18, "end": 2.18, "text": "Tone 2"}
    ]

    res = compress_dead_air(combined, cues=cues, floor_ms=250.0, target_gap_ms=150.0)
    assert res["cuts_count"] == 0
    assert res["time_saved_s"] == 0.0
    assert res["compressed_duration_s"] == res["original_duration_s"]


# ==============================================================================
# 3. Mobile Title Linting Tests
# ==============================================================================

def test_mobile_title_length_constraints():
    """Verify titles > 50 characters trigger mobile_truncation while <= 45-50 pass."""
    # Optimal mobile title (<= 45 chars)
    t_optimal = "How AI Thinks in 10ms #Shorts"
    r_optimal = lint_title(t_optimal)
    assert r_optimal["chars"] <= MOBILE_SHORTS_OPTIMAL_CHARS
    assert r_optimal["passed"] is True
    assert not any(i[0] == "mobile_truncation" for i in r_optimal["issues"])

    # Permissible boundary title (46-50 chars)
    t_boundary = "FlashAttention-3: How GPUs Hit 1.2 PFLOPS #Shorts"
    assert len(t_boundary) == 49
    r_boundary = lint_title(t_boundary)
    assert r_boundary["passed"] is True
    assert not any(i[0] == "mobile_truncation" for i in r_boundary["issues"])

    # Over-length title (> 50 chars)
    t_long = "DeepSeek-V3 vs GPT-4o: Why Open Weights Changed Everything in Modern AI #Shorts"
    assert len(t_long) > MOBILE_SHORTS_MAX_CHARS
    r_long = lint_title(t_long)
    assert r_long["passed"] is False
    assert any(i[0] == "mobile_truncation" for i in r_long["issues"])


def test_vague_buzzwords_flagged():
    """Verify vague buzzwords (amazing, insane, revolutionary) are flagged and penalize score."""
    t_vague = "This Insane AI Model Has Revolutionary Power #Shorts"
    res = lint_title(t_vague)
    assert res["passed"] is False
    vague_issues = [i for i in res["issues"] if i[0] == "vague"]
    assert len(vague_issues) > 0
    assert "insane" in vague_issues[0][1].lower() or "revolutionary" in vague_issues[0][1].lower()


def test_front_loaded_curiosity_and_numbers():
    """Verify titles with curiosity triggers and concrete figures receive bonuses."""
    t_good = "Why 94% of AI Memory Is Wasted #Shorts"
    res = lint_title(t_good)
    assert res["score"] >= 85
    good_msgs = " ".join(res["good"])
    assert "figure" in good_msgs.lower()
    assert "curiosity" in good_msgs.lower()

    # Title with filler front-loading
    t_filler = "In this video we test attention #Shorts"
    res_filler = lint_title(t_filler)
    assert any(i[0] == "front_load" for i in res_filler["issues"])


def test_shouting_caps_penalty():
    """Verify titles with > 2 all-caps words trigger shouting issue."""
    t_shouting = "WHY THIS NEW MODEL DESTROYS EVERYTHING #Shorts"
    res = lint_title(t_shouting)
    assert any(i[0] == "shouting" for i in res["issues"])


def test_optimize_title_for_mobile():
    """Verify optimize_title_for_mobile strips buzzwords and trims cleanly under 50 chars."""
    raw_title = "This INSANE and AMAZING Model Breaks the 1.2 PFLOPS Speed Barrier in Deep Learning #Shorts"
    assert len(raw_title) > 50

    optimized = optimize_title_for_mobile(raw_title, max_chars=MOBILE_SHORTS_MAX_CHARS)
    assert len(optimized) <= MOBILE_SHORTS_MAX_CHARS
    assert "#Shorts" in optimized
    # Vague buzzwords stripped
    assert "insane" not in optimized.lower()
    assert "amazing" not in optimized.lower()


def test_youtube_publisher_metadata_integration():
    """Verify generate_shorts_metadata in youtube_publisher executes linting and enforces constraints."""
    spec = {
        "id": "flashattention_3",
        "title": "FlashAttention-3: Ultra Fast GPU Kernels for Modern Transformers",
        "category": "mechanism_deepdive",
        "beats": [
            {"beat_id": 1, "text": "Over 60% of GPU cycles waste memory bandwidth.", "start": 0.0},
            {"beat_id": 5, "text": "Throughput doubled to 1.2 PFLOPS.", "start": 35.0}
        ]
    }

    meta = generate_shorts_metadata(spec, "sample_video.mp4")
    assert "title" in meta
    assert len(meta["title"]) <= MOBILE_SHORTS_MAX_CHARS
    assert "title_lint" in meta
    lint = meta["title_lint"]
    assert "chars" in lint
    assert "score" in lint
    assert lint["chars"] <= MOBILE_SHORTS_MAX_CHARS
