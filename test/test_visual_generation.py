from pathlib import Path

import pipeline.bespoke_visual_synthesizer as synthesizer_module
from pipeline.bespoke_visual_synthesizer import BespokeVisualSynthesizer, _fallback_visual_code
from pipeline.mechanism_visual_library import (
    mechanism_recipe,
    resolve_mechanism_family,
    validate_mechanism_semantics,
)
from pipeline.visual_generation import (
    ensure_visual_generation_key,
    mark_bespoke_visual,
    resolve_visual_mode,
)
from pipeline.code_sandbox import validate_visual_quality_contract


def test_visual_mode_defaults_to_on_demand_policy(monkeypatch):
    monkeypatch.delenv("VISUAL_GENERATION_MODE", raising=False)
    assert resolve_visual_mode() == "on_demand"


def test_on_demand_assigns_distinct_visual_grammars_per_beat():
    from pipeline.visual_generation import assign_visual_grammars

    spec = {"title": "Fresh Topic", "id": "fresh-topic", "beats": [{"beat_id": idx} for idx in range(1, 7)]}
    assign_visual_grammars(spec)

    grammars = [beat["visual_grammar"] for beat in spec["beats"]]
    assert len(grammars) == len(set(grammars))


def test_on_demand_rejects_silent_blueprint_fallback():
    from pipeline.visual_generation import require_on_demand_visuals

    spec = {"beats": [{"beat_id": 1, "bespoke_visual_path": "/tmp/beat_1.py"}, {"beat_id": 2}]}
    try:
        require_on_demand_visuals(spec, "on_demand")
    except RuntimeError as exc:
        assert "beat(s): 2" in str(exc)
    else:
        raise AssertionError("on_demand mode must reject missing bespoke visuals")


def test_on_demand_visuals_get_a_fresh_run_key():
    spec = {"id": "fresh-topic"}
    key = ensure_visual_generation_key(spec, "on_demand")
    assert key
    assert spec["visual_generation_key"] == key
    next_key = ensure_visual_generation_key(spec, "on_demand")
    assert next_key
    assert next_key != key


def test_new_generation_clears_stale_bespoke_path():
    spec = {
        "beats": [{"visual_source": "bespoke", "bespoke_visual_path": "/old/beat.py"}]
    }
    ensure_visual_generation_key(spec, "on_demand")
    assert "visual_source" not in spec["beats"][0]
    assert "bespoke_visual_path" not in spec["beats"][0]


def test_topic_resolver_selects_causal_mechanism_families():
    cases = [
        ("Diffusion flow matching", "particles follow a velocity field", "diffusion_flow"),
        ("KV cache compression", "attention keys become a latent vector", "attention_cache"),
        ("Mixture of Experts", "the router selects top-k experts", "moe_routing"),
        ("Speculative decoding", "a draft model proposes tokens for verification", "speculative_decoding"),
        ("Low rank projection", "compress a high dimensional matrix", "latent_compression"),
    ]
    for title, text, expected in cases:
        spec = {"id": title.lower().replace(" ", "_"), "title": title}
        beat = {"text": text, "visual_focus": text}
        assert resolve_mechanism_family(spec, beat) == expected
        assert mechanism_recipe(spec, beat)["family"] == expected


def test_domain_fallbacks_are_deterministic_and_valid():
    from pipeline.code_sandbox import validate_synthesized_visual_code
    from pipeline.visual_generation import assign_visual_grammars

    topics = [
        ("Diffusion flow matching", "particles follow a velocity field"),
        ("KV cache compression", "attention reads stored key value memory"),
        ("Mixture of Experts", "the router selects experts"),
        ("Speculative decoding", "draft tokens pass through verification"),
        ("Low rank projection", "compress a high dimensional matrix"),
    ]
    for title, text in topics:
        spec = {"id": title.lower().replace(" ", "_"), "title": title, "beats": [{"beat_id": 1, "text": text}]}
        assign_visual_grammars(spec)
        code = _fallback_visual_code(spec, spec["beats"][0], 1)
        valid, error = validate_synthesized_visual_code(code)
        assert valid, error


def test_mechanism_semantic_contract_rejects_cross_topic_attention_map():
    spec = {"id": "flow", "title": "Diffusion Flow Matching"}
    beat = {"text": "particles follow a velocity field", "visual_focus": "flow field"}
    valid, error = validate_mechanism_semantics(
        'CleanText("FIELD / Attention Map"); self.field = VGroup(*[Circle() for _ in range(4)])',
        spec,
        beat,
    )
    assert not valid
    assert "another topic family" in error


def test_visual_quality_contract_rejects_random_coordinates():
    code = """
from manim import *
import numpy as np
class BespokeBeatVisual(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dot = Dot([np.random.random(), 0, 0])
        self.add(self.dot)
    def get_entrance_animation(self, run_time=1.0):
        return FadeIn(self.dot)
    def get_kinetic_animation(self, run_time=1.0):
        return self.dot.animate.shift(RIGHT)
"""
    valid, error = validate_visual_quality_contract(code)
    assert not valid
    assert "deterministic" in error


def test_bespoke_cache_isolated_by_generation_key(tmp_path, monkeypatch):
    monkeypatch.setattr(synthesizer_module, "GENERATED_VISUALS_DIR", tmp_path)
    monkeypatch.setattr(
        synthesizer_module,
        "validate_synthesized_visual_code",
        lambda code: (True, ""),
    )
    synth = BespokeVisualSynthesizer()
    monkeypatch.setattr(synth, "_generate_code", lambda prompt: "class BespokeBeatVisual: pass")
    beat = {"beat_id": 1, "text": "A fresh mechanism graphic"}

    first = synth.synthesize_visual_for_beat(
        {"id": "topic", "title": "Topic", "visual_generation_key": "run_a"}, beat, 1
    )
    second = synth.synthesize_visual_for_beat(
        {"id": "topic", "title": "Topic", "visual_generation_key": "run_b"}, beat, 1
    )

    assert first != second
    assert Path(first).parent.name == "run_a"
    assert Path(second).parent.name == "run_b"


def test_mark_bespoke_visual_preserves_blueprint_fields():
    beat = {"motif_type": "visual_composition", "motif_params": {"layout": "grid_memory"}}
    mark_bespoke_visual(beat, "/tmp/generated/beat_1.py")
    assert beat["visual_source"] == "bespoke"
    assert beat["bespoke_visual_path"] == "/tmp/generated/beat_1.py"
    assert beat["motif_params"]["layout"] == "grid_memory"

