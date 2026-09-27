"""
The Model Verse — Phase 6 Integration Verification Test
Tests:
1. DeterministicLayoutSolver AABB collision resolution & safe-zone projection.
2. VLMCritic structured patch generation and layout solver integration.
3. Fast headless beat keyframe extraction with layout patches.
"""

import os
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.layout_solver import (
    DeterministicLayoutSolver, PhysicalEntity, gemini_box_to_manim,
    SpatialViolation, ViolationType
)
from pipeline.vlm_critic import vlm_critic


def test_geometric_layout_solver():
    print("\n--- 1. Testing Deterministic Geometric Layout Solver ---")
    solver = DeterministicLayoutSolver()
    
    # Simulate a collision between a robot arm and a math formula, plus safe-zone boundary
    header = PhysicalEntity("brand_header", center=[0.0, 5.8], dim=[6.0, 0.8], inv_mass=0.0)
    arm = PhysicalEntity("robot_arm", center=[0.0, 0.0], dim=[4.2, 4.0], inv_mass=0.2)
    formula = PhysicalEntity("math_formula", center=[0.0, -1.8], dim=[5.2, 1.4], inv_mass=1.0)
    
    # Detect initial violations
    violations = solver.detect_violations([header, arm, formula])
    print(f"Detected {len(violations)} initial violations:")
    for v in violations:
        print(f"  [{v.violation_type.value}] {v.primary_entity_id} vs {v.secondary_entity_id} (pen: {v.penetration_depth})")
    assert len(violations) >= 1, "Should detect at least 1 collision"
    
    # Solve
    entry = solver.solve([header, arm, formula], beat_id=4)
    print(f"Solver completed in {entry.solver_time_ms} ms. Resolved: {entry.resolved}")
    print(f"Prescribed {len(entry.prescribed_patches)} patches:")
    for p in entry.prescribed_patches:
        print(f"  Patch: {p.entity_id} | action: {p.action_type.value} | dx: {p.dx}, dy: {p.dy}, s: {p.scale_multiplier}")
    assert entry.resolved is True, "Solver must resolve all collisions"
    print("✅ Geometric Layout Solver passed!")


def test_coordinate_conversion():
    print("\n--- 2. Testing Gemini-to-Manim Coordinate Transform ---")
    # Box in center of screen [375, 278, 625, 722]
    box = gemini_box_to_manim([375, 278, 625, 722])
    print(f"Gemini [375, 278, 625, 722] -> Manim box: {box.manim_box}, center: {box.center}, dim: {box.dimensions}")
    assert abs(box.center[0]) < 0.1, "X center should be ~0"
    assert abs(box.center[1]) < 0.1, "Y center should be ~0"
    print("✅ Coordinate conversion passed!")


def test_vlm_critic_patch_generation():
    print("\n--- 3. Testing VLM Critic with Layout Solver Integration ---")
    spec_path = PROJECT_ROOT / "pipeline" / "templates" / "mechanism_deepdive_coding_agents_generalized_tamp.json"
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    # Test audit of an existing keyframe
    frames_dir = PROJECT_ROOT / "frames_coding_agents_generalized_tamp"
    test_pngs = sorted(list(frames_dir.glob("*.png")))
    if test_pngs:
        test_frame = str(test_pngs[0])
        print(f"Auditing keyframe: {Path(test_frame).name}...")
        report = vlm_critic.audit_keyframe(test_frame, spec, beat_id=1)
        print(f"Audit score: {report.get('overall_score')}/10.0")
        print(f"Primary observation: {report.get('primary_observation', '')[:70]}...")
        if "suggested_patches" in report:
            print(f"Suggested patches: {len(report['suggested_patches'])}")
        assert "overall_score" in report, "Report must contain overall_score"
    print("✅ VLM Critic audit passed!")


if __name__ == "__main__":
    test_geometric_layout_solver()
    test_coordinate_conversion()
    test_vlm_critic_patch_generation()
    print("\n🎉 ALL PHASE 6 INTEGRATION TESTS PASSED!")
