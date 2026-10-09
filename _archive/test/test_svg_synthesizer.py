import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.svg_synthesizer import SVGSynthesizer
from manim_engine.primitives.script_motifs import ScriptDynamicBespokeSVG, MOTIF_REGISTRY

def test_svg_synthesizer_procedural():
    synth = SVGSynthesizer()
    beat = {
        "beat_id": 2,
        "text": "Imagine blending fruit into a smoothie",
        "visual_focus": "Fruit being blended into a uniform smoothie vs individual whole fruits.",
        "everyday_analogy": "Smoothie blender vs distinct strawberries",
        "svo_action": {"subject": "Fruit", "action_verb": "blends", "direct_object": "Smoothie"}
    }
    svg_path = synth.synthesize_beat_svg(beat, "TestPaper", "test_paper_slug", 2)
    assert svg_path.exists()
    assert svg_path.stat().st_size > 100
    content = svg_path.read_text(encoding="utf-8")
    assert "<svg" in content
    assert "</svg>" in content

def test_script_dynamic_bespoke_svg_instantiation(tmp_path):
    svg_file = tmp_path / "sample.svg"
    svg_file.write_text(
        '<svg viewBox="0 0 600 400" xmlns="http://www.w3.org/2000/svg">'
        '<rect x="10" y="10" width="580" height="380" fill="#1E293B" stroke="#38BDF8" stroke-width="4"/>'
        '<circle cx="300" cy="200" r="50" fill="#EF4444"/>'
        '</svg>',
        encoding="utf-8"
    )
    
    motif = ScriptDynamicBespokeSVG(
        svg_path=str(svg_file),
        title="TEST BESPOKE DIAGRAM",
        sub="Testing vector parsing in Manim",
        badge_text="VALIDATED BEAT"
    )
    assert motif.fig_mobj is not None
    assert "bespoke_svg" in MOTIF_REGISTRY
    assert MOTIF_REGISTRY["bespoke_svg"] is ScriptDynamicBespokeSVG
