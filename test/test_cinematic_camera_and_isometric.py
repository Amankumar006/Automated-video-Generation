"""
Test Suite for Engine 8.0: 2.5D Isometric Engine, Cinematic Camera Controller,
and HUD Parallax Anchoring.
"""

import sys
from pathlib import Path
import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from manim import Square, VGroup, ORIGIN, RIGHT, UP, MovingCameraScene
from manim_engine.primitives.isometric import (
    get_isometric_matrix,
    apply_isometric_tilt,
    create_isometric_slab,
    create_isometric_layer_stack,
)
from manim_engine.controllers.kinetic_camera_controller import (
    KineticCameraController,
    kinetic_camera_controller,
)
from manim_engine.primitives.visual_compositions import (
    BlueprintPipelineStages,
    BlueprintGridMemory,
    BlueprintLayerStack,
)


def test_isometric_matrix_properties():
    mat = get_isometric_matrix(shear=0.38, tilt=0.62)
    assert mat.shape == (3, 3)
    # Check that z-axis is identity
    assert mat[2, 2] == 1.0
    assert mat[2, 0] == 0.0
    assert mat[2, 1] == 0.0


def test_apply_isometric_tilt():
    sq = Square(side_length=2.0)
    original_center = sq.get_center().copy()
    tilted = apply_isometric_tilt(sq, shear=0.4, tilt=0.6, in_place=True)
    np.testing.assert_allclose(tilted.get_center(), original_center, atol=1e-5)


def test_create_isometric_slab():
    slab = create_isometric_slab(
        width=4.0,
        height=2.0,
        thickness=0.3,
        face_color="#0F172A",
        rim_color="#1E293B",
        stroke_color="#38BDF8"
    )
    assert isinstance(slab, VGroup)
    # Contains side_rim, front_rim, top_face
    assert len(slab) == 3


def test_create_isometric_layer_stack():
    layers_data = [
        ("INPUT LAYER", "#94A3B8", -0.2),
        ("ATTENTION MANIFOLD", "#38BDF8", 0.0),
        ("OUTPUT PREDICTION", "#34D399", 0.2),
    ]
    stack_grp, proj_rays = create_isometric_layer_stack(layers_data)
    assert len(stack_grp) == 3
    assert len(proj_rays) > 0


def test_kinetic_camera_controller_lateral_tracking():
    ctrl = KineticCameraController()
    scene = MovingCameraScene()
    scene.setup()
    
    anim = ctrl.get_lateral_tracking_animation(
        camera_frame=scene.camera.frame,
        start_x=-1.5,
        end_x=1.5,
        y=0.0,
        run_time=1.5
    )
    assert anim is not None
    # Start anchor verified
    np.testing.assert_allclose(scene.camera.frame.get_center()[:2], [-1.5, 0.0], atol=1e-5)


def test_kinetic_camera_controller_selective_punch_in():
    ctrl = KineticCameraController()
    scene = MovingCameraScene()
    scene.setup()
    
    anim = ctrl.get_selective_punch_in(
        camera_frame=scene.camera.frame,
        target_point=np.array([0.0, 1.0, 0.0]),
        zoom_factor=0.76,
        run_time=0.4
    )
    assert anim is not None


def test_visual_compositions_custom_kinetics():
    # Verify BlueprintPipelineStages has custom conduit kinetics
    pipe = BlueprintPipelineStages(
        stage_1_label="INPUT",
        stage_2_label="ENCODER",
        stage_3_label="OUTPUT"
    )
    pipe_anim = pipe.get_kinetic_animation(run_time=1.0)
    assert pipe_anim is not None

    # Verify BlueprintGridMemory has matrix laser kinetics
    grid = BlueprintGridMemory()
    grid_anim = grid.get_kinetic_animation(run_time=1.0)
    assert grid_anim is not None

    # Verify BlueprintLayerStack uses 2.5D isometric stack
    stack = BlueprintLayerStack()
    assert hasattr(stack, "stack_group")
    assert hasattr(stack, "proj_rays")
    stack_anim = stack.get_kinetic_animation(run_time=1.0)
    assert stack_anim is not None


def test_script_dynamic_bespoke_svg_instantiation(tmp_path):
    from manim_engine.primitives.script_motifs import ScriptDynamicBespokeSVG, MOTIF_REGISTRY
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

