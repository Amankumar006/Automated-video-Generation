"""Comprehensive Test Suite for Phase 0: AetherBench.

Verifies Pydantic scenario schemas, scenario registry, benchmark suite generation,
semantic scenario validation, multi-gate evaluation, defect auditing, repair
recommendations, and batch benchmark runner harness.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import threading
import pytest
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from aether.bench.schemas import (
    AetherScenario,
    CameraMovementType,
    CameraParameters,
    CandidateEvaluationInput,
    CharacterDescriptor,
    ComplexityLevel,
    DefectAnnotation,
    EnvironmentLighting,
    GateStatus,
    HardGateConstraints,
    HardGateType,
    PhysicsChallengeType,
    PhysicsDifficulty,
    PhysicsProfile,
    RepairStrategy,
    SceneVariables,
    SoftScoringSpec,
    StressTestCategory,
    SurfaceProperties,
    TemporalContinuityConstraints,
    WardrobeGarment,
)
from aether.bench.registry import (
    ScenarioRegistry,
    get_default_registry,
    register_scenario,
)
from aether.bench.scenarios import (
    generate_benchmark_suite,
    get_gold_standard_scenarios,
    populate_registry_with_benchmarks,
)
from aether.bench.runner import (
    BenchmarkEvaluator,
    BenchmarkRunner,
    BenchmarkSuiteReport,
    MockModelProvider,
    ScenarioValidator,
)
from aether.bench.defects import (
    DefectCategory,
    DefectSeverity,
    GroundTruthDefect,
    SyntheticDefectDataset,
    generate_ground_truth_defect_dataset,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def sample_scenario() -> AetherScenario:
    """Provide a minimal valid AetherScenario for testing."""
    return AetherScenario(
        id="BENCH-TEST-001",
        title="Test Shot Alpha",
        description="A diagnostic test scenario with a single focal character.",
        category=StressTestCategory.MULTI_CHARACTER_INTERACTION,
        complexity_level=ComplexityLevel.LEVEL_3_2D_TRAJECTORY,
        duration_seconds=5.0,
        target_fps=24,
        resolution=(1920, 1080),
        scene_variables=SceneVariables(
            location="lab_interior",
            time_of_day="12:00",
            environment=EnvironmentLighting(
                ambient_description="diffuse_white",
                color_temperature_k=5500,
                strobe_frequency_hz=0.0,
                key_light_direction=[0.0, -1.0, 0.0],
                contrast_ratio=2.0,
            ),
            surface=SurfaceProperties(wetness=0.1, reflections=False),
        ),
        characters=[
            CharacterDescriptor(
                id="char_alpha",
                name="Character Alpha",
                position=[0.0, 0.0, 1.5],
                facing_angle=0.0,
                eyeline_vector=[0.0, 0.0, 1.0],
                wardrobe={"main": WardrobeGarment(id="w1", type="coat", state="pristine")},
                props={"right_hand": "data_pad"},
            )
        ],
        camera=CameraParameters(
            lens_mm=50.0,
            movement_type=CameraMovementType.DOLLY_IN,
            start_position=[0.0, 1.4, -1.0],
            end_position=[0.0, 1.4, 0.2],
            velocity_mps=0.24,
            focus_distance_m=1.8,
        ),
        physics_profile=PhysicsProfile(
            difficulty=PhysicsDifficulty.LOW,
            challenges=[PhysicsChallengeType.SPECULAR_REFLECTION],
        ),
        hard_gate_constraints=HardGateConstraints(
            anatomical_integrity=True,
            character_identity_preservation=True,
            prop_continuity=False,
            lip_sync_alignment=False,
        ),
        temporal_constraints=TemporalContinuityConstraints(
            max_optical_flow_jitter=0.10,
            min_ssim_frame_to_frame=0.85,
            max_flicker_ratio=0.05,
        ),
        soft_scoring_spec=SoftScoringSpec(
            min_cinematography=8.0,
            min_visual_aesthetic=8.0,
            min_narrative_pacing=8.0,
            min_aggregate_score=8.0,
        ),
        tags=["test", "diagnostic"],
    )


# -----------------------------------------------------------------------------
# 1. Schema Validation Tests
# -----------------------------------------------------------------------------


def test_valid_scenario_creation(sample_scenario: AetherScenario):
    """Scenario should instantiate correctly with all fields populated."""
    assert sample_scenario.id == "BENCH-TEST-001"
    assert sample_scenario.duration_seconds == 5.0
    assert len(sample_scenario.characters) == 1
    assert sample_scenario.complexity_level == ComplexityLevel.LEVEL_3_2D_TRAJECTORY


def test_scenario_serialization_roundtrip(sample_scenario: AetherScenario):
    """Scenario should serialize to JSON and deserialize back with identical fields."""
    raw_json = sample_scenario.model_dump_json()
    reconstructed = AetherScenario.model_validate_json(raw_json)
    assert reconstructed.id == sample_scenario.id
    assert reconstructed.category == sample_scenario.category
    assert reconstructed.camera.lens_mm == sample_scenario.camera.lens_mm
    assert reconstructed.characters[0].position == sample_scenario.characters[0].position


def test_invalid_scenario_id():
    """Empty or whitespace-only scenario IDs must raise ValidationError."""
    with pytest.raises(ValidationError):
        AetherScenario.model_validate({
            "id": "   ",
            "title": "Bad",
            "description": "Bad",
            "category": "TEMPORAL_CONTINUITY",
            "complexity_level": 1,
            "duration_seconds": 3.0,
            "scene_variables": {
                "location": "nowhere",
                "time_of_day": "now",
                "environment": {"ambient_description": "none"},
            },
            "camera": {
                "lens_mm": 50.0,
                "movement_type": "STATIC",
                "start_position": [0, 0, 0],
                "end_position": [0, 0, 0],
            },
            "physics_profile": {
                "difficulty": "LOW",
                "challenges": ["SPECULAR_REFLECTION"],
            },
        })


def test_invalid_camera_parameters(sample_scenario: AetherScenario):
    """Negative lens mm or invalid rack focus must raise ValidationError."""
    data = json.loads(sample_scenario.model_dump_json())
    data["camera"]["lens_mm"] = -10.0
    with pytest.raises(ValidationError):
        AetherScenario.model_validate(data)

    data["camera"]["lens_mm"] = 35.0
    data["camera"]["rack_focus"] = True
    data["camera"]["rack_focus_target_m"] = None
    with pytest.raises(ValidationError):
        AetherScenario.model_validate(data)


def test_invalid_coordinate_dimensions(sample_scenario: AetherScenario):
    """Positions must be 3-element lists [x, y, z]."""
    data = json.loads(sample_scenario.model_dump_json())
    data["characters"][0]["position"] = [0.0, 1.0]  # Only 2 elements
    with pytest.raises(ValidationError):
        AetherScenario.model_validate(data)


def test_duplicate_characters_rejected(sample_scenario: AetherScenario):
    """Scenarios with duplicate character IDs must raise ValidationError."""
    data = json.loads(sample_scenario.model_dump_json())
    char_copy = dict(data["characters"][0])
    data["characters"].append(char_copy)
    with pytest.raises(ValidationError, match="Characters in scenario must possess unique IDs"):
        AetherScenario.model_validate(data)


def test_handoff_validation(sample_scenario: AetherScenario):
    """Handoff characters must exist, and handoff window must be physically valid."""
    data = json.loads(sample_scenario.model_dump_json())
    data["hard_gate_constraints"]["handoff_prop_id"] = "data_pad"
    data["hard_gate_constraints"]["handoff_source_character"] = "non_existent_char"
    with pytest.raises(ValidationError, match="handoff_source_character 'non_existent_char' not found"):
        AetherScenario.model_validate(data)

    # Window end before start
    data["hard_gate_constraints"]["handoff_source_character"] = "char_alpha"
    data["hard_gate_constraints"]["handoff_window_start_sec"] = 4.0
    data["hard_gate_constraints"]["handoff_window_end_sec"] = 2.0
    with pytest.raises(ValidationError, match="handoff_window_start_sec must be strictly less than handoff_window_end_sec"):
        AetherScenario.model_validate(data)

    # Window end exceeds scenario duration
    data["hard_gate_constraints"]["handoff_window_start_sec"] = 2.0
    data["hard_gate_constraints"]["handoff_window_end_sec"] = 10.0  # Duration is 5.0s
    with pytest.raises(ValidationError, match="exceeds scenario duration"):
        AetherScenario.model_validate(data)


def test_soft_scoring_weight_validation(sample_scenario: AetherScenario):
    """Weights must sum to 1.0."""
    data = json.loads(sample_scenario.model_dump_json())
    data["soft_scoring_spec"]["cinematography_weight"] = 0.8
    data["soft_scoring_spec"]["aesthetic_weight"] = 0.8
    data["soft_scoring_spec"]["pacing_weight"] = 0.8
    with pytest.raises(ValidationError, match="must sum to 1.0"):
        AetherScenario.model_validate(data)


def test_defect_bounding_box_validation():
    """Bounding box coordinates must be normalized 0 <= x1 <= x2 <= 1."""
    # Valid
    d_valid = DefectAnnotation(
        defect_id="D1",
        gate=HardGateType.ANATOMICAL_INTEGRITY,
        description="Valid",
        bounding_box=(0.1, 0.2, 0.4, 0.5),
    )
    assert d_valid.bounding_box == (0.1, 0.2, 0.4, 0.5)

    # Invalid: x1 > x2
    with pytest.raises(ValidationError):
        DefectAnnotation(
            defect_id="D2",
            gate=HardGateType.ANATOMICAL_INTEGRITY,
            description="Bad",
            bounding_box=(0.8, 0.2, 0.4, 0.5),
        )

    # Invalid: out of bounds
    with pytest.raises(ValidationError):
        DefectAnnotation(
            defect_id="D3",
            gate=HardGateType.ANATOMICAL_INTEGRITY,
            description="Bad",
            bounding_box=(-0.1, 0.2, 0.4, 1.5),
        )


# -----------------------------------------------------------------------------
# 2. Scenario Registry Tests
# -----------------------------------------------------------------------------


def test_registry_registration_and_lookup(sample_scenario: AetherScenario):
    """Registry should store, retrieve, count, and delete scenarios."""
    reg = ScenarioRegistry()
    assert reg.count() == 0

    reg.register(sample_scenario)
    assert reg.count() == 1
    assert reg.get("BENCH-TEST-001") == sample_scenario
    assert reg.get_or_raise("BENCH-TEST-001") == sample_scenario

    # Duplicate without allow_overwrite should fail
    with pytest.raises(ValueError, match="already registered"):
        reg.register(sample_scenario, allow_overwrite=False)

    # With allow_overwrite should succeed
    reg.register(sample_scenario, allow_overwrite=True)
    assert reg.count() == 1

    # Unregister
    assert reg.unregister("BENCH-TEST-001") is True
    assert reg.get("BENCH-TEST-001") is None
    assert reg.unregister("BENCH-TEST-001") is False

    with pytest.raises(KeyError):
        reg.get_or_raise("BENCH-TEST-001")


def test_registry_filtering():
    """Registry filter method should correctly isolate subsets by criteria."""
    reg = ScenarioRegistry()
    gold_scenarios = get_gold_standard_scenarios()
    reg.register_many(gold_scenarios)
    assert reg.count() == 8

    # Filter by category
    mc_shots = reg.filter(category=StressTestCategory.MULTI_CHARACTER_INTERACTION)
    assert len(mc_shots) == 1
    assert mc_shots[0].id == "BENCH-MC-001"

    # Filter by complexity level
    level_5_shots = reg.filter(complexity_level=ComplexityLevel.LEVEL_5_DETERMINISTIC_SIM)
    assert len(level_5_shots) >= 3  # GR-001, FP-001, AN-001

    # Filter by physics difficulty
    extreme_physics = reg.filter(physics_difficulty=PhysicsDifficulty.EXTREME)
    assert len(extreme_physics) >= 3

    # Filter by character count
    two_character_shots = reg.filter(min_characters=2, max_characters=2)
    assert len(two_character_shots) >= 2  # MC-001, HO-001, AN-001

    # Filter by tags
    neon_shots = reg.filter(tags=["neon"])
    assert len(neon_shots) == 1
    assert neon_shots[0].id == "BENCH-GR-001"


def test_registry_summary():
    """Summary should report correct aggregate totals."""
    reg = ScenarioRegistry()
    reg.register_many(get_gold_standard_scenarios())
    summary = reg.summary()

    assert summary["total_scenarios"] == 8
    assert len(summary["categories"]) == 8
    assert summary["average_duration_seconds"] > 0.0
    assert summary["total_characters"] > 0


def test_registry_json_export_and_import(tmp_path: Path):
    """Registry should export to a JSON file and import back without data loss."""
    reg = ScenarioRegistry()
    reg.register_many(get_gold_standard_scenarios())

    export_file = tmp_path / "scenarios.json"
    exported_count = reg.export_to_json(export_file)
    assert exported_count == 8
    assert export_file.exists()

    new_reg = ScenarioRegistry()
    imported_count = new_reg.import_from_json(export_file)
    assert imported_count == 8
    assert new_reg.count() == 8
    assert new_reg.get("BENCH-MC-001") is not None


def test_registry_directory_export_and_import(tmp_path: Path):
    """Registry should export individual scenario JSON files to a directory."""
    reg = ScenarioRegistry()
    reg.register_many(get_gold_standard_scenarios())

    export_dir = tmp_path / "scenarios_dir"
    count = reg.export_to_dir(export_dir)
    assert count == 8
    assert len(list(export_dir.glob("*.json"))) == 8

    new_reg = ScenarioRegistry()
    new_count = new_reg.import_from_dir(export_dir)
    assert new_count == 8
    assert new_reg.count() == 8


def test_default_registry_helpers():
    """Default registry helpers should register and fetch consistently."""
    def_reg = get_default_registry()
    scenarios = get_gold_standard_scenarios()
    register_scenario(scenarios[0], allow_overwrite=True)
    assert def_reg.get(scenarios[0].id) is not None


# -----------------------------------------------------------------------------
# 3. Gold-Standard Scenarios & Suite Generator Tests
# -----------------------------------------------------------------------------


def test_gold_standard_scenarios_completeness():
    """Gold standard suite must contain all 8 foundational scenarios covering each category."""
    scenarios = get_gold_standard_scenarios()
    assert len(scenarios) == 8

    categories_present = {s.category for s in scenarios}
    assert len(categories_present) == len(StressTestCategory)

    expected_ids = {
        "BENCH-MC-001",
        "BENCH-HO-001",
        "BENCH-RC-001",
        "BENCH-GR-001",
        "BENCH-TC-001",
        "BENCH-FP-001",
        "BENCH-LT-001",
        "BENCH-AN-001",
    }
    actual_ids = {s.id for s in scenarios}
    assert actual_ids == expected_ids


def test_gold_standard_scenarios_pass_semantic_validation():
    """All 8 gold-standard scenarios must be semantically valid with zero errors."""
    scenarios = get_gold_standard_scenarios()
    for s in scenarios:
        res = ScenarioValidator.validate(s)
        assert res.is_valid, f"Scenario {s.id} failed validation with errors: {res.errors}"
        assert len(res.errors) == 0


def test_generate_benchmark_suite_250():
    """Generator must produce exactly 250 validated, unique scenarios."""
    suite = generate_benchmark_suite(target_count=250, seed=100)
    assert len(suite) == 250

    ids = [s.id for s in suite]
    assert len(ids) == len(set(ids)), "Generated scenario IDs must be strictly unique"

    # Verify coverage across all 8 categories
    cat_counts = {}
    for s in suite:
        cat_counts[s.category] = cat_counts.get(s.category, 0) + 1

    assert len(cat_counts) == len(StressTestCategory)
    for cat, cnt in cat_counts.items():
        assert cnt >= 25, f"Category {cat} should have substantial scenario representation (got {cnt})"


def test_generate_benchmark_suite_deterministic():
    """Generator must produce identical outputs when seeded identically."""
    suite_1 = generate_benchmark_suite(target_count=50, seed=42)
    suite_2 = generate_benchmark_suite(target_count=50, seed=42)
    assert [s.id for s in suite_1] == [s.id for s in suite_2]
    assert [s.title for s in suite_1] == [s.title for s in suite_2]


def test_populate_registry_with_benchmarks():
    """populate_registry_with_benchmarks helper should populate registry."""
    reg = ScenarioRegistry()
    count = populate_registry_with_benchmarks(registry=reg, include_generated_250=False)
    assert count == 8
    assert reg.count() == 8

    count_250 = populate_registry_with_benchmarks(registry=reg, include_generated_250=True, allow_overwrite=True)
    assert count_250 == 250
    assert reg.count() == 250


# -----------------------------------------------------------------------------
# 4. Semantic Scenario Validator Tests
# -----------------------------------------------------------------------------


def test_validator_character_collision_detection(sample_scenario: AetherScenario):
    """Validator should flag overlapping character coordinates in non-grapple scenarios."""
    data = json.loads(sample_scenario.model_dump_json())
    char1 = data["characters"][0]
    char2 = dict(char1)
    char2["id"] = "char_beta"
    char2["position"] = list(char1["position"])  # Exact same position
    data["characters"].append(char2)

    scenario = AetherScenario.model_validate(data)
    val_res = ScenarioValidator.validate(scenario)
    assert not val_res.is_valid
    assert any("overlapping coordinates" in err for err in val_res.errors)


def test_validator_handoff_prop_missing_warning(sample_scenario: AetherScenario):
    """Validator should warn if handoff source character lacks the designated prop."""
    data = json.loads(sample_scenario.model_dump_json())
    char2 = dict(data["characters"][0])
    char2["id"] = "char_target"
    char2["position"] = [1.0, 0.0, 1.5]
    char2["props"] = {}
    data["characters"].append(char2)

    data["hard_gate_constraints"]["handoff_prop_id"] = "non_existent_prop"
    data["hard_gate_constraints"]["handoff_source_character"] = "char_alpha"
    data["hard_gate_constraints"]["handoff_target_character"] = "char_target"
    data["hard_gate_constraints"]["handoff_window_start_sec"] = 1.0
    data["hard_gate_constraints"]["handoff_window_end_sec"] = 3.0

    scenario = AetherScenario.model_validate(data)
    val_res = ScenarioValidator.validate(scenario)
    assert any("does not have prop 'non_existent_prop'" in w for w in val_res.warnings)


# -----------------------------------------------------------------------------
# 5. Benchmark Evaluator & Multi-Gate Auditing Tests
# -----------------------------------------------------------------------------


def test_evaluator_all_pass(sample_scenario: AetherScenario):
    """High-performing candidate should pass all hard gates, temporal checks, and soft scores."""
    candidate = CandidateEvaluationInput(
        scenario_id=sample_scenario.id,
        model_id="google_veo_3.1",
        candidate_id="cand_001",
        anatomical_score=0.99,
        face_similarity_cosine=0.95,
        prop_handoff_success=True,
        lip_sync_offset_ms=5.0,
        optical_flow_jitter=0.03,
        min_observed_ssim=0.92,
        observed_flicker_ratio=0.01,
        line_of_action_preserved=True,
        soft_cinematography=8.8,
        soft_aesthetic=8.7,
        soft_pacing=8.5,
    )

    report = BenchmarkEvaluator.evaluate(sample_scenario, candidate)
    assert report.passed is True
    assert report.hard_gates_passed is True
    assert report.temporal_passed is True
    assert len(report.defects) == 0
    assert "PASS" in report.summary


def test_evaluator_anatomical_integrity_failure(sample_scenario: AetherScenario):
    """Deformed limbs must trigger ANATOMICAL_INTEGRITY failure and suggest repair."""
    candidate = CandidateEvaluationInput(
        scenario_id=sample_scenario.id,
        model_id="google_veo_3.1",
        candidate_id="cand_bad_anatomy",
        anatomical_score=0.70,  # Below tolerance (0.95)
        face_similarity_cosine=0.95,
        soft_cinematography=8.5,
        soft_aesthetic=8.5,
        soft_pacing=8.5,
    )

    report = BenchmarkEvaluator.evaluate(sample_scenario, candidate)
    assert report.passed is False
    assert report.hard_gates_passed is False
    assert report.gate_results[HardGateType.ANATOMICAL_INTEGRITY.value].status == GateStatus.FAIL
    assert RepairStrategy.SPATIAL_PREVIS_FALLBACK in report.recommended_repairs


def test_evaluator_identity_drift_failure(sample_scenario: AetherScenario):
    """Face embedding drift below threshold triggers CHARACTER_IDENTITY failure."""
    candidate = CandidateEvaluationInput(
        scenario_id=sample_scenario.id,
        model_id="kling_3.0",
        candidate_id="cand_face_drift",
        anatomical_score=0.98,
        face_similarity_cosine=0.72,  # Below threshold (0.85)
        soft_cinematography=8.5,
        soft_aesthetic=8.5,
        soft_pacing=8.5,
    )

    report = BenchmarkEvaluator.evaluate(sample_scenario, candidate)
    assert report.passed is False
    assert report.hard_gates_passed is False
    assert report.gate_results[HardGateType.CHARACTER_IDENTITY.value].status == GateStatus.FAIL
    assert RepairStrategy.TEMPORAL_INPAINTING in report.recommended_repairs


def test_evaluator_lip_sync_failure(sample_scenario: AetherScenario):
    """Phoneme offset exceeding threshold triggers LIP_SYNC_ALIGNMENT failure."""
    # Enable lip sync on scenario
    data = json.loads(sample_scenario.model_dump_json())
    data["hard_gate_constraints"]["lip_sync_alignment"] = True
    data["hard_gate_constraints"]["max_phoneme_offset_ms"] = 30.0
    scenario = AetherScenario.model_validate(data)

    candidate = CandidateEvaluationInput(
        scenario_id=scenario.id,
        model_id="runway_gen4.5",
        candidate_id="cand_sync_lag",
        anatomical_score=0.98,
        face_similarity_cosine=0.92,
        lip_sync_offset_ms=75.0,  # Exceeds 30.0ms threshold
        soft_cinematography=8.5,
        soft_aesthetic=8.5,
        soft_pacing=8.5,
    )

    report = BenchmarkEvaluator.evaluate(scenario, candidate)
    assert report.passed is False
    assert report.hard_gates_passed is False
    assert report.gate_results[HardGateType.LIP_SYNC_ALIGNMENT.value].status == GateStatus.FAIL
    assert RepairStrategy.AUDIO_ONLY_REMASTER in report.recommended_repairs


def test_evaluator_soft_score_failure(sample_scenario: AetherScenario):
    """Candidate with passing hard gates but sub-8.0 soft scores fails overall."""
    candidate = CandidateEvaluationInput(
        scenario_id=sample_scenario.id,
        model_id="open_cogvideox",
        candidate_id="cand_poor_aesthetic",
        anatomical_score=0.98,
        face_similarity_cosine=0.92,
        soft_cinematography=6.5,
        soft_aesthetic=6.0,
        soft_pacing=6.5,
    )

    report = BenchmarkEvaluator.evaluate(sample_scenario, candidate)
    assert report.passed is False
    assert report.hard_gates_passed is True
    assert report.aggregate_soft_score < 8.0
    assert "FAIL Soft" in report.summary


# -----------------------------------------------------------------------------
# 6. Mock Model Provider & Benchmark Runner Suite Tests
# -----------------------------------------------------------------------------


def test_mock_model_provider_generation(sample_scenario: AetherScenario):
    """MockModelProvider should generate realistic candidate metrics."""
    provider = MockModelProvider(model_id="google_veo_3.1")
    cand = provider.generate_candidate_input(sample_scenario)
    assert cand.model_id == "google_veo_3.1"
    assert cand.generation_latency_sec > 0.0
    assert cand.estimated_cost_usd > 0.0

    report = BenchmarkEvaluator.evaluate(sample_scenario, cand)
    assert report.passed is True


def test_mock_model_provider_defect_injection(sample_scenario: AetherScenario):
    """Injected defects in mock provider must be detected by the evaluator."""
    provider = MockModelProvider(
        model_id="test_model",
        default_fail_gates=[HardGateType.ANATOMICAL_INTEGRITY],
    )
    cand = provider.generate_candidate_input(sample_scenario)
    assert len(cand.synthetic_defects) > 0

    report = BenchmarkEvaluator.evaluate(sample_scenario, cand)
    assert report.passed is False
    assert report.gate_results[HardGateType.ANATOMICAL_INTEGRITY.value].status == GateStatus.FAIL
    assert len(report.defects) > 0


def test_benchmark_runner_single_scenario(sample_scenario: AetherScenario):
    """BenchmarkRunner should execute a single scenario with provider."""
    runner = BenchmarkRunner()
    provider = MockModelProvider()
    report = runner.run_scenario_with_provider(sample_scenario, provider)
    assert report.scenario_id == sample_scenario.id
    assert report.passed is True


def test_benchmark_runner_suite_execution(tmp_path: Path):
    """BenchmarkRunner should execute across a list of scenarios and aggregate metrics."""
    runner = BenchmarkRunner()
    scenarios = get_gold_standard_scenarios()
    provider = MockModelProvider(model_id="google_veo_3.1")

    suite_report = runner.run_suite(scenarios, provider)
    assert isinstance(suite_report, BenchmarkSuiteReport)
    assert suite_report.total_scenarios == 8
    assert suite_report.passed_count == 8
    assert suite_report.pass_rate == 1.0
    assert suite_report.average_aggregate_soft_score >= 8.0
    assert suite_report.total_estimated_cost_usd > 0.0
    assert len(suite_report.category_metrics) == 8

    # Test JSON export
    report_file = tmp_path / "benchmark_run.json"
    suite_report.export_json(report_file)
    assert report_file.exists()

    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_scenarios"] == 8
    assert data["pass_rate"] == 1.0


# -----------------------------------------------------------------------------
# 7. Edge Cases & Boundary Value Tests
# -----------------------------------------------------------------------------


def test_complexity_level_enum_properties():
    """Complexity levels must cover levels 0 through 5 with exact integer mappings."""
    levels = list(ComplexityLevel)
    assert len(levels) == 6
    for i in range(6):
        assert ComplexityLevel(i) == levels[i]
        assert int(levels[i]) == i


def test_invalid_physics_refraction_index(sample_scenario: AetherScenario):
    """Refraction index < 1.0 is physically impossible and must raise ValidationError."""
    data = json.loads(sample_scenario.model_dump_json())
    data["physics_profile"]["optical_refraction_index"] = 0.5
    with pytest.raises(ValidationError):
        AetherScenario.model_validate(data)


def test_zero_vector_key_light_direction_rejected(sample_scenario: AetherScenario):
    """Zero vector for key light direction must raise ValidationError."""
    data = json.loads(sample_scenario.model_dump_json())
    data["scene_variables"]["environment"]["key_light_direction"] = [0.0, 0.0, 0.0]
    with pytest.raises(ValidationError, match="cannot be a zero vector"):
        AetherScenario.model_validate(data)


def test_zero_vector_eyeline_rejected(sample_scenario: AetherScenario):
    """Zero vector for character eyeline must raise ValidationError."""
    data = json.loads(sample_scenario.model_dump_json())
    data["characters"][0]["eyeline_vector"] = [0.0, 0.0, 0.0]
    with pytest.raises(ValidationError, match="cannot be zero vector"):
        AetherScenario.model_validate(data)


def test_registry_corrupt_json_handling(tmp_path: Path):
    """Non-list JSON or missing dir must raise appropriate errors."""
    reg = ScenarioRegistry()
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text('{"not": "a list"}')
    with pytest.raises(ValueError, match="Expected a JSON list"):
        reg.import_from_json(corrupt_file)

    non_existent_dir = tmp_path / "does_not_exist"
    with pytest.raises(NotADirectoryError):
        reg.import_from_dir(non_existent_dir)


def test_registry_clear_and_empty_operations():
    """Empty operations on registry should behave cleanly."""
    reg = ScenarioRegistry()
    assert reg.register_many([]) == 0
    assert reg.filter(category=StressTestCategory.MULTI_CHARACTER_INTERACTION) == []
    assert reg.summary()["total_scenarios"] == 0
    assert reg.summary()["average_duration_seconds"] == 0.0

    reg.register_many(get_gold_standard_scenarios())
    assert reg.count() == 8
    reg.clear()
    assert reg.count() == 0


def test_evaluator_multiple_simultaneous_hard_gate_failures(sample_scenario: AetherScenario):
    """When multiple hard gates fail, all failures must be reported with deduplicated repairs."""
    data = json.loads(sample_scenario.model_dump_json())
    data["hard_gate_constraints"]["lip_sync_alignment"] = True
    scenario = AetherScenario.model_validate(data)

    candidate = CandidateEvaluationInput(
        scenario_id=scenario.id,
        model_id="multi_fail_model",
        candidate_id="cand_fail_all",
        anatomical_score=0.60,       # Anatomy FAIL
        face_similarity_cosine=0.50, # Identity FAIL
        lip_sync_offset_ms=120.0,    # Lip sync FAIL
        soft_cinematography=8.5,
        soft_aesthetic=8.5,
        soft_pacing=8.5,
    )

    report = BenchmarkEvaluator.evaluate(scenario, candidate)
    assert report.passed is False
    assert report.hard_gates_passed is False
    assert report.gate_results[HardGateType.ANATOMICAL_INTEGRITY.value].status == GateStatus.FAIL
    assert report.gate_results[HardGateType.CHARACTER_IDENTITY.value].status == GateStatus.FAIL
    assert report.gate_results[HardGateType.LIP_SYNC_ALIGNMENT.value].status == GateStatus.FAIL

    # Repairs should contain multiple strategies without duplicate entries
    assert len(report.recommended_repairs) == len(set(report.recommended_repairs))
    assert RepairStrategy.AUDIO_ONLY_REMASTER in report.recommended_repairs
    assert RepairStrategy.TEMPORAL_INPAINTING in report.recommended_repairs


def test_benchmark_runner_category_fail_injections():
    """Runner should correctly simulate per-category failure injections."""
    runner = BenchmarkRunner()
    scenarios = get_gold_standard_scenarios()
    provider = MockModelProvider(model_id="test_provider")

    # Specifically inject anatomical failure only into HAND_OBJECT_HANDOFF category
    category_injections = {
        StressTestCategory.HAND_OBJECT_HANDOFF: [HardGateType.ANATOMICAL_INTEGRITY]
    }

    suite_report = runner.run_suite(scenarios, provider, category_fail_injections=category_injections)
    assert suite_report.total_scenarios == 8
    assert suite_report.passed_count == 7
    assert suite_report.failed_count == 1
    assert suite_report.category_metrics["HAND_OBJECT_HANDOFF"]["pass_rate"] == 0.0
    assert suite_report.category_metrics["MULTI_CHARACTER_INTERACTION"]["pass_rate"] == 1.0


def test_validator_camera_motion_warnings(sample_scenario: AetherScenario):
    """Validator should emit warnings for mismatched camera velocities."""
    data = json.loads(sample_scenario.model_dump_json())
    # Camera velocity > 0 but stationary positions
    data["camera"]["velocity_mps"] = 5.0
    data["camera"]["start_position"] = [0.0, 1.0, 0.0]
    data["camera"]["end_position"] = [0.0, 1.0, 0.0]
    scenario = AetherScenario.model_validate(data)
    val = ScenarioValidator.validate(scenario)
    assert any("nearly identical" in w for w in val.warnings)

    # Stationary velocity 0 but moving distance
    data["camera"]["velocity_mps"] = 0.0
    data["camera"]["start_position"] = [0.0, 1.0, 0.0]
    data["camera"]["end_position"] = [5.0, 1.0, 0.0]
    scenario = AetherScenario.model_validate(data)
    val = ScenarioValidator.validate(scenario)
    assert any("velocity_mps is 0.0" in w for w in val.warnings)


def test_validator_complexity_level_warnings(sample_scenario: AetherScenario):
    """Validator should warn when complexity level is too low for physical scene."""
    data = json.loads(sample_scenario.model_dump_json())
    data["category"] = StressTestCategory.FLUID_COLLISION_PHYSICS
    data["complexity_level"] = ComplexityLevel.LEVEL_1_REF_CONDITIONED
    data["physics_profile"]["challenges"] = [PhysicsChallengeType.FLUID_DYNAMICS]
    scenario = AetherScenario.model_validate(data)
    val = ScenarioValidator.validate(scenario)
    assert any("Fluid collision physics typically requires complexity Level 4 or 5" in w for w in val.warnings)


def test_prop_continuity_failure_without_handoff_prop(sample_scenario: AetherScenario):
    """Prop continuity gate must fail when prop defect occurs even without a handoff."""
    data = json.loads(sample_scenario.model_dump_json())
    data["hard_gate_constraints"]["prop_continuity"] = True
    data["hard_gate_constraints"]["handoff_prop_id"] = None
    scenario = AetherScenario.model_validate(data)

    candidate = CandidateEvaluationInput(
        scenario_id=scenario.id,
        model_id="test_model",
        candidate_id="cand_prop_glitch",
        prop_handoff_success=False,
        synthetic_defects=[
            DefectAnnotation(
                defect_id="DEF-PROP-GLITCH",
                gate=HardGateType.PROP_CONTINUITY,
                description="Held item vanished during camera orbit",
                severity="FATAL",
            )
        ],
    )

    report = BenchmarkEvaluator.evaluate(scenario, candidate)
    assert report.passed is False
    assert report.hard_gates_passed is False
    assert HardGateType.PROP_CONTINUITY.value in report.gate_results
    assert report.gate_results[HardGateType.PROP_CONTINUITY.value].status == GateStatus.FAIL
    assert report.gate_results[HardGateType.PROP_CONTINUITY.value].defect_count == 1
    assert "FAIL Hard Gates: PROP_CONTINUITY" in report.summary


def test_mock_model_provider_lip_sync_defect_injection(sample_scenario: AetherScenario):
    """MockModelProvider must generate DefectAnnotation when LIP_SYNC_ALIGNMENT fails."""
    data = json.loads(sample_scenario.model_dump_json())
    data["hard_gate_constraints"]["lip_sync_alignment"] = True
    scenario = AetherScenario.model_validate(data)

    provider = MockModelProvider(
        model_id="lip_fail_provider",
        default_fail_gates=[HardGateType.LIP_SYNC_ALIGNMENT],
    )
    cand = provider.generate_candidate_input(scenario)
    assert any(d.gate == HardGateType.LIP_SYNC_ALIGNMENT for d in cand.synthetic_defects)

    report = BenchmarkEvaluator.evaluate(scenario, cand)
    assert report.gate_results[HardGateType.LIP_SYNC_ALIGNMENT.value].status == GateStatus.FAIL
    assert report.gate_results[HardGateType.LIP_SYNC_ALIGNMENT.value].defect_count >= 1


def test_generate_benchmark_suite_zero_warnings():
    """All 250 benchmark scenarios must validate with zero errors and zero warnings."""
    scenarios = generate_benchmark_suite(250)
    assert len(scenarios) == 250

    for s in scenarios:
        res = ScenarioValidator.validate(s)
        assert res.is_valid is True, f"Scenario {s.id} invalid: {res.errors}"
        assert len(res.warnings) == 0, f"Scenario {s.id} generated warnings: {res.warnings}"


def test_invalid_resolution_rejected(sample_scenario: AetherScenario):
    """Negative and zero resolutions must raise ValidationError."""
    data = json.loads(sample_scenario.model_dump_json())
    data["resolution"] = (-1920, 1080)
    with pytest.raises(ValidationError, match="strictly positive"):
        AetherScenario.model_validate(data)

    data["resolution"] = (1920, 0)
    with pytest.raises(ValidationError, match="strictly positive"):
        AetherScenario.model_validate(data)


def test_camera_eyeline_vector_validation(sample_scenario: AetherScenario):
    """CameraParameters must validate eyeline_vector dimensions and non-zero magnitude."""
    data = json.loads(sample_scenario.model_dump_json())
    data["camera"]["eyeline_vector"] = [1.0]  # Invalid dimension
    with pytest.raises(ValidationError, match="3-element"):
        AetherScenario.model_validate(data)

    data["camera"]["eyeline_vector"] = [0.0, 0.0, 0.0]  # Zero vector
    with pytest.raises(ValidationError, match="cannot be a zero vector"):
        AetherScenario.model_validate(data)


def test_defect_inverted_frame_range_rejected():
    """DefectAnnotation must reject start_frame > end_frame."""
    with pytest.raises(ValidationError, match="cannot be greater than end_frame"):
        DefectAnnotation(
            defect_id="DEF-INV",
            gate=HardGateType.ANATOMICAL_INTEGRITY,
            description="Inverted frame bounds",
            start_frame=60,
            end_frame=30,
        )


def test_validator_handoff_missing_required_fields(sample_scenario: AetherScenario):
    """Validator must reject HAND_OBJECT_HANDOFF scenarios without required handoff params."""
    data = json.loads(sample_scenario.model_dump_json())
    data["category"] = StressTestCategory.HAND_OBJECT_HANDOFF
    data["hard_gate_constraints"]["handoff_prop_id"] = None
    data["hard_gate_constraints"]["handoff_source_character"] = None
    scenario = AetherScenario.model_validate(data)

    val = ScenarioValidator.validate(scenario)
    assert val.is_valid is False
    assert any("must specify handoff_prop_id" in e for e in val.errors)
    assert any("must specify handoff_source_character" in e for e in val.errors)


def test_validator_multi_character_single_character_rejected(sample_scenario: AetherScenario):
    """Validator must reject MULTI_CHARACTER_INTERACTION when fewer than 2 characters are present."""
    data = json.loads(sample_scenario.model_dump_json())
    data["category"] = StressTestCategory.MULTI_CHARACTER_INTERACTION
    # sample_scenario has only 1 character
    scenario = AetherScenario.model_validate(data)
    val = ScenarioValidator.validate(scenario)
    assert val.is_valid is False
    assert any("requires at least 2 characters" in e for e in val.errors)


def test_candidate_finite_number_validation(sample_scenario: AetherScenario):
    """CandidateEvaluationInput must reject NaN and infinite metrics."""
    with pytest.raises(ValidationError):
        CandidateEvaluationInput(
            scenario_id=sample_scenario.id,
            model_id="test",
            candidate_id="cand_nan",
            lip_sync_offset_ms=float("nan"),
        )

    with pytest.raises(ValidationError, match="finite number"):
        CandidateEvaluationInput(
            scenario_id=sample_scenario.id,
            model_id="test",
            candidate_id="cand_inf",
            optical_flow_jitter=float("inf"),
        )


def test_synthetic_defect_ground_truth_dataset():
    """WBS 1.1.3: Verify synthetic defect dataset generation, queries, and summary."""
    dataset = generate_ground_truth_defect_dataset()
    assert dataset.count() >= 14
    summary = dataset.summary()
    assert summary["total_defects"] >= 14
    assert summary["target_scenarios_count"] >= 5
    assert "ANATOMICAL_INTEGRITY" in summary["categories"]
    assert "CHARACTER_IDENTITY" in summary["categories"]
    assert "PROP_CONTINUITY" in summary["categories"]
    assert "LIP_SYNC_ALIGNMENT" in summary["categories"]

    # Filter tests
    anat_defects = dataset.filter_by_category(DefectCategory.ANATOMICAL_INTEGRITY)
    assert len(anat_defects) >= 3

    fatal_defects = dataset.filter_by_severity(DefectSeverity.FATAL)
    assert len(fatal_defects) >= 8

    mc_defects = dataset.filter_by_scenario("BENCH-MC-001")
    assert len(mc_defects) >= 3

    # Lookup test
    d = dataset.get_by_id("GT-DEF-ANAT-001")
    assert d is not None
    assert d.defect_class == "fused_digits"
    assert d.start_frame < d.end_frame
    assert d.expected_repair_strategy == RepairStrategy.TEMPORAL_INPAINTING


def test_synthetic_defect_dataset_serialization_roundtrip(tmp_path: Path):
    """WBS 1.1.3: Verify JSON export and import for ground truth defect dataset."""
    dataset = generate_ground_truth_defect_dataset()
    target_file = tmp_path / "defects_gt.json"
    exported_count = dataset.export_to_json(target_file)
    assert exported_count == dataset.count()
    assert target_file.exists()

    loaded = SyntheticDefectDataset.import_from_json(target_file)
    assert loaded.count() == dataset.count()
    assert loaded.dataset_id == dataset.dataset_id
    assert loaded.defects[0].defect_id == dataset.defects[0].defect_id


def test_ground_truth_defect_conversion_to_annotation(sample_scenario: AetherScenario):
    """WBS 1.1.3: Ground-truth defect must convert cleanly to DefectAnnotation for evaluator."""
    dataset = generate_ground_truth_defect_dataset()
    gt = dataset.get_by_id("GT-DEF-ANAT-001")
    assert gt is not None

    annotation = gt.to_defect_annotation()
    assert isinstance(annotation, DefectAnnotation)
    assert annotation.defect_id == "GT-DEF-ANAT-001"
    assert annotation.gate == HardGateType.ANATOMICAL_INTEGRITY

    cand = CandidateEvaluationInput(
        scenario_id=sample_scenario.id,
        model_id="test_model",
        candidate_id="cand_gt_eval",
        synthetic_defects=[annotation],
    )
    report = BenchmarkEvaluator.evaluate(sample_scenario, cand)
    assert report.passed is False
    assert report.gate_results[HardGateType.ANATOMICAL_INTEGRITY.value].status == GateStatus.FAIL


def test_temporal_continuity_detailed_metrics_and_summary(sample_scenario: AetherScenario):
    """Evaluator must populate structured temporal_metrics and clear diagnostic summaries."""
    cand = CandidateEvaluationInput(
        scenario_id=sample_scenario.id,
        model_id="test",
        candidate_id="cand_temp_fail",
        optical_flow_jitter=0.25,  # Exceeds 0.10
        min_observed_ssim=0.65,    # Below 0.85
        observed_flicker_ratio=0.12, # Exceeds 0.05
    )

    report = BenchmarkEvaluator.evaluate(sample_scenario, cand)
    assert report.temporal_passed is False
    assert report.temporal_metrics["optical_flow_jitter"]["passed"] is False
    assert report.temporal_metrics["min_ssim"]["passed"] is False
    assert report.temporal_metrics["flicker_ratio"]["passed"] is False
    assert "FAIL Temporal Continuity: optical_flow" in report.summary
    assert "ssim" in report.summary
    assert "flicker" in report.summary


def test_registry_thread_safety():
    """ScenarioRegistry must support concurrent operations across threads without corruption."""
    reg = ScenarioRegistry()
    scenarios = get_gold_standard_scenarios()
    errors: list[Exception] = []

    def writer_thread(idx: int):
        try:
            for s in scenarios:
                clone_data = json.loads(s.model_dump_json())
                clone_data["id"] = f"{s.id}-T{idx}"
                reg.register(AetherScenario.model_validate(clone_data), allow_overwrite=True)
        except Exception as e:
            errors.append(e)

    def reader_thread():
        try:
            for _ in range(20):
                reg.list_all()
                reg.summary()
                reg.filter(complexity_level=ComplexityLevel.LEVEL_4_3D_BLOCKING)
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=writer_thread, args=(i,)) for i in range(4)
    ] + [
        threading.Thread(target=reader_thread) for _ in range(4)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Thread concurrency errors: {errors}"
    assert reg.count() == 8 * 4


def test_registry_directory_export_path_traversal_protection(tmp_path: Path):
    """ScenarioRegistry must reject attempts to write outside the export directory."""
    reg = ScenarioRegistry()
    sc = get_gold_standard_scenarios()[0]
    data = json.loads(sc.model_dump_json())
    # Attempt directory traversal in scenario id
    data["id"] = "../illegal_scenario"
    scenario = AetherScenario.model_validate(data)
    reg.register(scenario)

    export_dir = tmp_path / "scenarios_export"
    # Should safely sanitize to "illegal_scenario.json" inside export_dir
    reg.export_to_dir(export_dir)
    assert (export_dir / "illegal_scenario.json").exists()
    assert not (tmp_path / "illegal_scenario.json").exists()


if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))


