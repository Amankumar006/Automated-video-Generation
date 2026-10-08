"""AetherBench: Empirical Evaluation Framework for Project Aether v2.

Exports scenario schemas, registry, benchmark suites, and runner harness.
"""

from aether.bench.schemas import (
    AetherScenario,
    CameraMovementType,
    CameraParameters,
    CandidateEvaluationInput,
    CharacterDescriptor,
    ComplexityLevel,
    DefectAnnotation,
    EnvironmentLighting,
    GateEvaluationResult,
    GateStatus,
    HardGateConstraints,
    HardGateType,
    PhysicsChallengeType,
    PhysicsDifficulty,
    PhysicsProfile,
    RepairStrategy,
    ScenarioEvaluationReport,
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
    ValidationResult,
)
from aether.bench.defects import (
    DefectCategory,
    DefectSeverity,
    GroundTruthDefect,
    SyntheticDefectDataset,
    generate_ground_truth_defect_dataset,
)

__all__ = [
    # Schemas
    "AetherScenario",
    "CameraMovementType",
    "CameraParameters",
    "CandidateEvaluationInput",
    "CharacterDescriptor",
    "ComplexityLevel",
    "DefectAnnotation",
    "EnvironmentLighting",
    "GateEvaluationResult",
    "GateStatus",
    "HardGateConstraints",
    "HardGateType",
    "PhysicsChallengeType",
    "PhysicsDifficulty",
    "PhysicsProfile",
    "RepairStrategy",
    "ScenarioEvaluationReport",
    "SceneVariables",
    "SoftScoringSpec",
    "StressTestCategory",
    "SurfaceProperties",
    "TemporalContinuityConstraints",
    "WardrobeGarment",
    # Registry
    "ScenarioRegistry",
    "get_default_registry",
    "register_scenario",
    # Scenarios
    "generate_benchmark_suite",
    "get_gold_standard_scenarios",
    "populate_registry_with_benchmarks",
    # Runner & Validator
    "BenchmarkEvaluator",
    "BenchmarkRunner",
    "BenchmarkSuiteReport",
    "MockModelProvider",
    "ScenarioValidator",
    "ValidationResult",
    # Defects (WBS 1.1.3)
    "DefectCategory",
    "DefectSeverity",
    "GroundTruthDefect",
    "SyntheticDefectDataset",
    "generate_ground_truth_defect_dataset",
]
