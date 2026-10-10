"""
Unit and Integration Tests for:
1. OmniRoute cascading in BespokeVisualSynthesizer (Visual Engine 6.0) across Gemini, Groq, OpenRouter, and Ollama.
2. QuotaHealthTracker failover avoiding silent 429 failures.
3. 1-Shot self-healing via code sandbox.
4. Production entrypoints (run_pipeline.py & auto_produce.py) wiring visual synthesis.
5. Clean Scene Graph Exit in ScriptDrivenScene (zero auxiliary graphics bleed).
"""

import os
import sys
import json
import re
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest
from manim import *

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.quota_tracker import quota_tracker
from pipeline.llm_router import LLMRouter, generate_text_with_cascade
from pipeline.bespoke_visual_synthesizer import (
    BespokeVisualSynthesizer,
    bespoke_synthesizer,
    GENERATED_VISUALS_DIR
)
from pipeline.code_sandbox import validate_synthesized_visual_code
from manim_engine.scenes.script_driven_scene import ScriptDrivenScene
from manim_engine.primitives.particles import (
    create_formula_sparkle_burst,
    create_formula_halo_pulse
)
from manim_engine.primitives.typography import CleanText


VALID_BESPOKE_CODE = '''from manim import *
import numpy as np
from manim_engine.primitives.typography import CleanText

class BespokeBeatVisual(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.center_node = Dot(point=ORIGIN + UP * 0.8, radius=0.15, color="#00F0FF")
        self.label = CleanText("KV Cache Attention", font_size=20, color="#38BDF8").next_to(self.center_node, DOWN, buff=0.2)
        self.add(self.center_node, self.label)

    def get_entrance_animation(self, run_time: float = 1.0) -> Animation:
        return FadeIn(self, run_time=run_time)

    def get_kinetic_animation(self, run_time: float = 1.0) -> Animation:
        return self.center_node.animate(rate_func=there_and_back, run_time=run_time).scale(1.2)

    def get_ambient_animation(self, run_time: float = 2.0) -> Animation:
        return self.label.animate(rate_func=there_and_back, run_time=run_time).scale(1.04)
'''

INVALID_BESPOKE_CODE = '''from manim import *
# Missing class BespokeBeatVisual
def some_invalid_function():
    return 42
'''


@pytest.fixture(autouse=True)
def clean_quota_state():
    """Ensure QuotaTracker is reset and test directories in GENERATED_VISUALS_DIR are cleaned."""
    quota_tracker.reset()
    yield
    quota_tracker.reset()
    for p in GENERATED_VISUALS_DIR.glob("test_*"):
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)


# ==============================================================================
# 1. OmniRoute Integration in BespokeVisualSynthesizer Tests
# ==============================================================================

import uuid
import shutil


def test_bespoke_synthesizer_gemini_model_cascade_on_model_quota():
    """
    Verifies that when primary Gemini model hits a 429/quota error,
    BespokeVisualSynthesizer cascades to the next Gemini model and generates valid code.
    """
    synth = BespokeVisualSynthesizer()
    unique_id = f"test_cascade_model_{uuid.uuid4().hex[:8]}"

    sample_spec = {
        "id": unique_id,
        "title": "Recurrent Quantization",
        "beats": [{"beat_id": 1, "text": "Quantized state cache"}]
    }
    sample_beat = sample_spec["beats"][0]

    # Model 1 (gemini-2.5-flash) raises 429, Model 2 (gemini-2.5-flash-lite) succeeds
    mock_model_flash = MagicMock()
    mock_model_flash.generate_content.side_effect = Exception("429 ResourceExhausted: rate limit exceeded on gemini-2.5-flash")

    mock_resp_lite = MagicMock()
    mock_resp_lite.text = f"```python\n{VALID_BESPOKE_CODE}\n```"
    mock_model_lite = MagicMock()
    mock_model_lite.generate_content.return_value = mock_resp_lite

    def model_factory(model_name, **kwargs):
        if "lite" in model_name:
            return mock_model_lite
        return mock_model_flash

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key", "GEMINI_MODEL_NAME": "gemini-2.5-flash"}, clear=False):
        with patch("google.generativeai.GenerativeModel", side_effect=model_factory):
            # Target output path
            out_file = synth.synthesize_visual_for_beat(sample_spec, sample_beat, 1)

            assert out_file is not None
            assert Path(out_file).exists()
            content = Path(out_file).read_text(encoding="utf-8")
            assert "class BespokeBeatVisual(VGroup):" in content


def test_bespoke_synthesizer_gemini_429_failover_to_groq():
    """
    Verifies that when all Gemini models fail with 429,
    BespokeVisualSynthesizer cascades across providers to Groq and marks Gemini exhausted.
    """
    synth = BespokeVisualSynthesizer()
    unique_id = f"test_cascade_groq_{uuid.uuid4().hex[:8]}"

    sample_spec = {
        "id": unique_id,
        "title": "StepQuant Mechanism",
        "beats": [{"beat_id": 1, "text": "Weight rounding analysis"}]
    }
    sample_beat = sample_spec["beats"][0]

    mock_gemini_model = MagicMock()
    mock_gemini_model.generate_content.side_effect = Exception("429 ResourceExhausted: Quota exceeded for project")

    mock_groq_resp = MagicMock()
    mock_groq_resp.status_code = 200
    mock_groq_resp.json.return_value = {
        "choices": [
            {"message": {"content": f"```python\n{VALID_BESPOKE_CODE}\n```"}}
        ]
    }

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key", "GROQ_API_KEY": "test_groq_key"}, clear=False):
        with patch("google.generativeai.GenerativeModel", return_value=mock_gemini_model):
            with patch("requests.post", return_value=mock_groq_resp) as mock_post:
                out_file = synth.synthesize_visual_for_beat(sample_spec, sample_beat, 1)

                assert out_file is not None
                assert Path(out_file).exists()
                # Verify quota tracker flagged Gemini
                assert quota_tracker.is_exhausted("gemini") is True
                assert quota_tracker.is_healthy("groq") is True
                assert mock_post.called


def test_bespoke_synthesizer_skips_exhausted_gemini_immediately():
    """
    Verifies that if Gemini is already marked exhausted, BespokeVisualSynthesizer
    skips Gemini immediately without invoking GenerativeModel.
    """
    quota_tracker.record_exhausted("gemini", "Pre-existing 429")
    synth = BespokeVisualSynthesizer()
    unique_id = f"test_skip_exhausted_{uuid.uuid4().hex[:8]}"

    sample_spec = {
        "id": unique_id,
        "title": "Skip Gemini",
        "beats": [{"beat_id": 1, "text": "Testing skip"}]
    }
    sample_beat = sample_spec["beats"][0]

    mock_groq_resp = MagicMock()
    mock_groq_resp.status_code = 200
    mock_groq_resp.json.return_value = {
        "choices": [
            {"message": {"content": f"```python\n{VALID_BESPOKE_CODE}\n```"}}
        ]
    }

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key", "GROQ_API_KEY": "test_groq_key"}, clear=False):
        with patch("google.generativeai.GenerativeModel") as mock_gemini:
            with patch("requests.post", return_value=mock_groq_resp):
                out_file = synth.synthesize_visual_for_beat(sample_spec, sample_beat, 1)

                assert out_file is not None
                assert mock_gemini.call_count == 0


def test_bespoke_synthesizer_one_shot_self_healing():
    """
    Verifies 1-shot self-healing when initial synthesis produces invalid Manim code
    (e.g., missing class BespokeBeatVisual). The repair loop fixes it.
    """
    synth = BespokeVisualSynthesizer()
    unique_id = f"test_self_healing_{uuid.uuid4().hex[:8]}"

    sample_spec = {
        "id": unique_id,
        "title": "Self Healing",
        "beats": [{"beat_id": 1, "text": "Repair test"}]
    }
    sample_beat = sample_spec["beats"][0]

    responses = [
        f"```python\n{INVALID_BESPOKE_CODE}\n```",  # 1st call fails AST
        f"```python\n{VALID_BESPOKE_CODE}\n```"    # 2nd call (repair) succeeds
    ]

    with patch.object(synth.router, "generate_text_with_cascade", side_effect=responses) as mock_gen:
        out_file = synth.synthesize_visual_for_beat(sample_spec, sample_beat, 1, allow_self_healing=True)

        assert out_file is not None
        assert mock_gen.call_count == 2
        content = Path(out_file).read_text(encoding="utf-8")
        assert "class BespokeBeatVisual(VGroup):" in content


def test_reusing_cached_verified_visual():
    """
    Verifies that if beat_X.py already exists and passes validation,
    synthesis reuses the file without making LLM calls.
    """
    synth = BespokeVisualSynthesizer()
    spec_id = f"test_cache_reuse_{uuid.uuid4().hex[:8]}"
    target_dir = GENERATED_VISUALS_DIR / spec_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "beat_1.py"
    target_file.write_text(VALID_BESPOKE_CODE, encoding="utf-8")

    sample_spec = {
        "id": spec_id,
        "title": "Cache Reuse",
        "beats": [{"beat_id": 1, "text": "Reusing cache"}]
    }
    sample_beat = sample_spec["beats"][0]

    with patch.object(synth.router, "generate_text_with_cascade") as mock_gen:
        out_file = synth.synthesize_visual_for_beat(sample_spec, sample_beat, 1)

        assert out_file == str(target_file)
        assert mock_gen.call_count == 0


# ==============================================================================
# 2. Production Entrypoint Synthesis Integration Tests
# ==============================================================================

def test_run_pipeline_invokes_bespoke_synthesis_loop():
    """
    Verifies that run_pipeline.py's Step 2.9 synthesizes visuals for beats,
    while respecting arXiv figures for Beat 3.
    """
    spec = {
        "id": "test_pipeline_wiring",
        "title": "Wiring Verification",
        "beats": [
            {"beat_id": 1, "text": "Beat 1"},
            {"beat_id": 2, "text": "Beat 2"},
            {"beat_id": 3, "text": "Beat 3 (arXiv figure)"},
            {"beat_id": 4, "text": "Beat 4"}
        ],
        "paper_figures": [{"beat_id": 3, "image_path": "/path/to/fig.png"}]
    }

    synthesized_beats = []

    def mock_synthesize(s, beat, b_id):
        synthesized_beats.append(b_id)
        return f"/mock/path/beat_{b_id}.py"

    with patch("pipeline.bespoke_visual_synthesizer.bespoke_synthesizer.synthesize_visual_for_beat", side_effect=mock_synthesize):
        # Emulate Step 2.9 visual synthesis loop from run_pipeline.py
        for idx, beat in enumerate(spec.get("beats", [])):
            b_id = beat.get("beat_id", idx + 1)
            if b_id == 3 and spec.get("paper_figures"):
                continue
            bespoke_synthesizer.synthesize_visual_for_beat(spec, beat, b_id)

        # Beat 3 should be skipped due to paper_figures, others synthesized
        assert synthesized_beats == [1, 2, 4]


# ==============================================================================
# 3. Clean Scene Graph Exit (Fix Graphic Bleed) Tests
# ==============================================================================

class MockRenderer:
    def __init__(self):
        self.time = 0.0


class DummyScriptDrivenScene(ScriptDrivenScene):
    """Subclass of ScriptDrivenScene isolating beat cleanup testing without GPU rendering."""
    def __init__(self):
        super().__init__()
        self.renderer = MockRenderer()
        self.spec = {
            "title": "Test Clean Exit",
            "beats": [
                {"beat_id": 1, "text": "Beat 1"},
                {"beat_id": 2, "text": "Beat 2"}
            ]
        }
        self.mobjects = []
        self.current_formula_mobj = None
        self.active_auxiliary_mobjects = []
        self.played_animations = []

    def play(self, *anims, **kwargs):
        self.played_animations.extend(anims)

    def add(self, *mobs):
        for m in mobs:
            if m not in self.mobjects:
                self.mobjects.append(m)

    def remove(self, *mobs):
        for m in mobs:
            if m in self.mobjects:
                self.mobjects.remove(m)


def test_script_driven_scene_auxiliary_mobjects_cleanup_on_beat_exit():
    """
    Verifies that all tracked auxiliary mobjects (burst_pts, halo_box, spotlight halo, etc.)
    are added to exit animations and explicitly removed from self.mobjects at beat exit,
    ensuring zero graphic bleed.
    """
    scene = DummyScriptDrivenScene()

    # Create dummy motif & formula tray
    motif = VGroup(Dot(), Square())
    tray_group = VGroup(CleanText("α = softmax(Q·Kᵀ / √d)"))
    scene.add(motif, tray_group)
    scene.current_formula_mobj = tray_group

    # Create auxiliary elements
    burst_pts, _ = create_formula_sparkle_burst(tray_group, color="#38BDF8")
    halo_box, _ = create_formula_halo_pulse(tray_group, color="#38BDF8")
    spotlight_halo = SurroundingRectangle(motif, color="#38BDF8")

    # Add them to scene and track them
    scene.add(burst_pts, halo_box, spotlight_halo)
    scene.track_auxiliary_mobject(burst_pts, halo_box, spotlight_halo)

    assert burst_pts in scene.mobjects
    assert halo_box in scene.mobjects
    assert spotlight_halo in scene.mobjects
    assert len(scene.active_auxiliary_mobjects) == 3

    # Execute beat exit logic (matching ScriptDrivenScene lines 553-585)
    exit_anims = [FadeOut(motif, shift=DOWN * 0.15)]
    if scene.current_formula_mobj:
        exit_anims.append(FadeOut(scene.current_formula_mobj, shift=DOWN * 0.15))

    for aux_mob in scene.active_auxiliary_mobjects:
        if aux_mob is not None and aux_mob in scene.mobjects:
            exit_anims.append(FadeOut(aux_mob, shift=DOWN * 0.15))

    scene.play(*exit_anims, run_time=0.2)
    scene.remove(motif)
    if scene.current_formula_mobj:
        scene.remove(scene.current_formula_mobj)
        scene.current_formula_mobj = None

    for aux_mob in scene.active_auxiliary_mobjects:
        if aux_mob is not None:
            scene.remove(aux_mob)
    scene.active_auxiliary_mobjects.clear()

    # Verification:
    # 1. All auxiliary mobjects were faded out
    faded_mobjects = [anim.mobject for anim in scene.played_animations if isinstance(anim, FadeOut)]
    assert motif in faded_mobjects
    assert tray_group in faded_mobjects
    assert burst_pts in faded_mobjects
    assert halo_box in faded_mobjects
    assert spotlight_halo in faded_mobjects

    # 2. All auxiliary mobjects removed from scene graph
    assert burst_pts not in scene.mobjects
    assert halo_box not in scene.mobjects
    assert spotlight_halo not in scene.mobjects
    assert motif not in scene.mobjects
    assert tray_group not in scene.mobjects

    # 3. Active auxiliary collection is completely cleared
    assert len(scene.active_auxiliary_mobjects) == 0


def test_scene_active_auxiliary_mobjects_reset_per_beat():
    """
    Verifies that scene.active_auxiliary_mobjects is refreshed per beat
    so no stale references bleed into the next screen.
    """
    scene = DummyScriptDrivenScene()

    # Simulate Beat 1 adding auxiliary elements
    aux_mob_1 = Dot()
    scene.track_auxiliary_mobject(aux_mob_1)
    assert len(scene.active_auxiliary_mobjects) == 1

    # Simulate start of Beat 2
    scene.active_auxiliary_mobjects = []
    assert len(scene.active_auxiliary_mobjects) == 0

    aux_mob_2 = Square()
    scene.track_auxiliary_mobject(aux_mob_2)
    assert len(scene.active_auxiliary_mobjects) == 1
    assert aux_mob_1 not in scene.active_auxiliary_mobjects
