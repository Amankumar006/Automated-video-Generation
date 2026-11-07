"""
Unit tests for Audience-First Curiosity Scripting & 10-Second Plain-English Identity Rules.
Verifies that:
1. The Intellectual Thriller Engine requires plain-English identity and human stakes in Beat 1 or 2.
2. The Feynman Dialogue Engine (Alex) rejects scripts that dive into compiler/tensor internals without explaining what the subject is.
3. The Script Critic enforces the 10-second rule.
4. Deterministic fallbacks produce curiosity-driven hooks with plain-English identity.
"""

import pytest
from pipeline.intellectual_thriller_engine import IntellectualThrillerEngine
from pipeline.feynman_dialogue_engine import CuriousNoviceListenerAgent, TechScriptwriterAgent
from pipeline.script_critic import ScriptCritic


def test_intellectual_thriller_audit_detects_missing_identity():
    engine = IntellectualThrillerEngine()
    # Script that dives straight into low-level compiler jargon without introducing what it is
    jargon_script = {
        "title": "Low-Level Kernel Optimization",
        "beats": [
            {"beat_id": 1, "text": "Why are GPUs wasting up to 60% of their compute time?"},
            {"beat_id": 2, "text": "SRAM kernel launch overhead stalls the asynchronous execution pipeline."},
            {"beat_id": 3, "text": "Normally, memory transfers choke the processor before computation finishes."},
            {"beat_id": 4, "text": "Under the hood, it fuses operations into a single GPU pass."},
            {"beat_id": 5, "text": "The result is a 3x faster speedup on benchmark runs."},
            {"beat_id": 6, "text": "Follow The Model Verse for daily deep-dives under the hood."}
        ]
    }
    audit = engine.audit_thriller_compliance(jargon_script)
    assert audit["has_plain_english_identity"] is False
    assert audit["passed"] is False


def test_intellectual_thriller_audit_passes_curiosity_bridge():
    engine = IntellectualThrillerEngine()
    # Script that follows the Curiosity Bridge: Universal Hook -> Plain-English Identity & Stakes
    curiosity_script = {
        "title": "Unsloth Local Training",
        "beats": [
            {"beat_id": 1, "text": "What if you could run a private ChatGPT on your laptop without paying cloud fees?"},
            {"beat_id": 2, "text": "Meet Unsloth: a free open-source engine that rewrites AI training code so it runs on normal consumer PCs."},
            {"beat_id": 3, "text": "Normally, training crashes home computers with Out of Memory errors because standard software wastes 80% of its time."},
            {"beat_id": 4, "text": "Instead of slow memory chips, it fuses five math operations into a single pass directly on the GPU."},
            {"beat_id": 5, "text": "The payoff? Training runs 5 times faster with 70% less memory, saving thousands in cloud bills."},
            {"beat_id": 6, "text": "You do not need a million dollar cluster anymore. Follow The Model Verse for daily deep-dives."}
        ]
    }
    audit = engine.audit_thriller_compliance(curiosity_script)
    assert audit["has_plain_english_identity"] is True
    assert audit["has_human_stakes"] is True
    assert audit["hook_passed"] is True
    assert audit["score"] >= 8.0
    assert audit["passed"] is True


def test_feynman_novice_listener_enforces_identity_gate():
    listener = CuriousNoviceListenerAgent()
    # Candidate script missing plain-English identity
    jargon_text = (
        "Beat 1: Why are GPUs wasting compute?\n"
        "Beat 2: SRAM bandwidth chokes the tensor cores.\n"
        "Beat 3: Traditional pipelines bottleneck the execution wall.\n"
        "Beat 4: Asynchronous scheduling coordinates task streams.\n"
        "Beat 5: Benchmark gains reach 2x speedup.\n"
        "Beat 6: Follow The Model Verse for daily updates."
    )
    res = listener._heuristic_audit(jargon_text, [])
    assert res["plain_english_identity_present"] is False
    assert res["approved"] is False
    assert "missing_plain_english_identity" in res["confusing_elements"]

    # Candidate script WITH plain-English identity
    good_text = (
        "Beat 1: What if you could eliminate the biggest bottleneck in AI?\n"
        "Beat 2: Meet Unsloth: an open-source engine built to run AI on standard laptop hardware.\n"
        "Beat 3: Normally, home PCs hit an invisible wall because memory transfers choke the processor.\n"
        "Beat 4: Under the hood, it eliminates wasted cycles by keeping active computations in chip cache.\n"
        "Beat 5: The result? 5x faster speedup with zero loss in fidelity.\n"
        "Beat 6: Follow The Model Verse for daily deep-dives under the hood."
    )
    good_res = listener._heuristic_audit(good_text, [])
    assert good_res["plain_english_identity_present"] is True
    assert good_res["has_human_stakes"] is True
    assert good_res["approved"] is True


def test_script_critic_enforces_10_second_rule():
    critic = ScriptCritic()
    # Script without identity definition
    bad_spec = {
        "title": "Compiler Pass Optimization",
        "beats": [
            {"beat_id": 1, "text": "Why do large neural networks waste GPU compute time?"},
            {"beat_id": 2, "text": "Kernel launch delays cause sequential memory contention."},
            {"beat_id": 3, "text": "Normally, traditional systems hit a wall."},
            {"beat_id": 4, "text": "Under the hood, operations coordinate in parallel."},
            {"beat_id": 5, "text": "The result is a 30% speedup on benchmarks."},
            {"beat_id": 6, "text": "Follow The Model Verse for daily deep-dives."}
        ]
    }
    report_bad = critic.evaluate_script(bad_spec, use_llm=False)
    assert report_bad.plain_english_identity_present is False
    assert report_bad.passed is False
    assert "fails 10-second rule" in report_bad.summary_verdict

    # Script WITH plain-English identity in Beat 2
    good_spec = {
        "title": "Unsloth Local Training",
        "beats": [
            {"beat_id": 1, "text": "What if you could run a private ChatGPT on your laptop?"},
            {"beat_id": 2, "text": "Meet Unsloth: an open-source engine built to run AI on consumer PCs."},
            {"beat_id": 3, "text": "Normally, home computers crash with out of memory errors."},
            {"beat_id": 4, "text": "Under the hood, it fuses math operations directly on the chip."},
            {"beat_id": 5, "text": "The result? 5x faster training saving thousands in cloud costs."},
            {"beat_id": 6, "text": "Follow The Model Verse for daily deep-dives into modern AI."}
        ]
    }
    report_good = critic.evaluate_script(good_spec, use_llm=False)
    assert report_good.plain_english_identity_present is True
    assert report_good.has_human_stakes is True
    assert report_good.passed is True


def test_deterministic_fallbacks_produce_plain_identity():
    # Test Intellectual Thriller Engine deterministic fallback
    thriller_engine = IntellectualThrillerEngine()
    spec = {
        "title": "BitNet b1.58",
        "beats": [
            {"beat_id": 1, "text": "Today we explore BitNet."},
            {"beat_id": 2, "text": "It is about matrix multiplication."}
        ]
    }
    rewritten = thriller_engine._apply_deterministic_thriller_rewrite(spec)
    b2 = rewritten["beats"][1]["text"]
    assert "Meet BitNet" in b2 or "engine" in b2 or "open-source" in b2

    # Test Feynman Scriptwriter Agent fallback
    writer = TechScriptwriterAgent()
    context = {
        "title": "vLLM High-Throughput Serving",
        "abstract": "Large language model serving is bottlenecked by KV cache memory fragmentation. We propose PagedAttention.",
        "domain": "hardware_efficiency",
        "category": "mechanism_deepdive"
    }
    script = writer._generate_resilient_fallback(context)
    b2_text = script["beats"][1]["text"]
    assert "Meet vLLM" in b2_text
    assert "open-source" in b2_text
