# Changelog: Project Aether

All notable changes to Project Aether will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0-repair] - 2026-10-05
### Added
- Implemented **Phase 6: Surgical Repair Engine (WBS 1.7)** under `aether/repair/`:
  - `schemas.py`: Pydantic V2 models for `RepairActionType` (including alias support for regional temporal inpainting), `RepairBoundaryMask`, `ProtectedRegion`, `ProtectedRegionType`, `ComputeTier`, `SurgicalRepairTask`, `RepairPlan`, and `RepairExecutionResult`.
  - `masking.py`: `TemporalMaskEngine` implementing spatio-temporal inpainting masks, continuous distance-based spatial feathering (Gaussian, cosine, linear falloffs), temporal ramp-in/ramp-out frame padding weights (eliminating boundary strobing), actor face/background protection shielding, and quantitative boundary seam metrics addressing RSK-004.
  - `planner.py`: `RepairPlanner` implementing the Minimum Necessary Intervention policy:
    - Dialogue desync / clipping -> `AUDIO_REMASTER_VOICE` without touching video pixels.
    - Foley audio mismatch -> `AUDIO_REMASTER_FOLEY`.
    - Localized hand deformation at $t=5.8-6.4\text{s}$ in 8s shot -> `REGIONAL_TEMPORAL_INPAINTING` targeting sub-region without re-rendering entire shot.
    - Physical trajectory failure -> `SPATIAL_PREVIS_REBLOCK` targeting UE5 motion guides.
    - Defect escalation to `FULL_SHOT_REGENERATION` when > 3 severe non-localized defects exist or multiple hard gates fail across > 70% of frames.
    - Clean pass / `NO_OP` handling for accepted shots.
    - Deduplication and spatial/temporal merging of overlapping defect masks.
  - `executor.py`: `SurgicalRepairExecutor` dispatching repair plans:
    - ComfyUI inpaint node payload synthesis with flow-guided blending flags.
    - FFmpeg audio remux and latency shift payload synthesis with video preservation.
    - UE5 motion guide re-blocking payload synthesis.
    - Foundation video model full shot regeneration synthesis.
    - Seam continuity metric validation and council approval flagging.
    - High-seam fallback escalation execution.
  - `test/test_aether_repair.py`: 34 unit, regression, and edge-case tests with 100% pass rate. Total repository Aether test suite expanded to 249 passing tests.

## [0.7.0-council] - 2026-10-05
### Added
- Implemented **Phase 4: Critic Council & Quality Gatekeeping** under `aether/council/`:
  - `schemas.py`: Pydantic V2 models for `CriticType`, `DefectSeverity`, `HardGateType`, `RepairRecommendation`, `CriticFailureObject`, `CriticAuditResult`, and `CouncilEvaluationReport`.
  - `cv_analyzer.py`: `CVTemporalAnalyzer` implementing deterministic computer vision analysis (NumPy/OpenCV Farneback optical flow motion vector jitter, SSIM-like frame variance, 4x4 spatial subgrid localized micro-flicker detection, and multi-frame morphing bounding box extraction).
  - `critics.py`: Specialized evaluation agents:
    - `VisualCritic`: Audits anatomical integrity (extra limbs, deformed hands, face geometry) and surface artifacts.
    - `TemporalCritic`: Hybrid CV analyzer + temporal flow checks.
    - `ContinuityCritic`: Cross-references candidate detections against `AetherWorldModel` / `SceneState` (wardrobe damage persistence, held prop continuity, injuries, and reciprocal eyeline gaze).
    - `PerformanceCritic`: Lip-sync offset (ms), phonetic mouth movement, and vocal performance.
    - `PhysicsCritic`: Gravity violations, trajectory accelerations, and solid-body intersections.
    - `AudioCritic`: Acoustic clipping, noise floor, and sound artifact auditing.
  - `council.py`: `CriticCouncil` master evaluation coordinator enforcing binary Hard Gates (`ANATOMICAL_INTEGRITY`, `CHARACTER_IDENTITY`, `PROP_CONTINUITY`, `LIP_SYNC_ALIGNMENT`, `PHYSICAL_TRAJECTORY`), zeroing aesthetic scores on failure, and assembling prioritized repair directives.
  - `test/test_aether_council.py`: 52 unit and regression tests with 100% pass rate. Total repository Aether test suite expanded to 215 passing tests.

## [0.5.0-compiler] - 2026-10-05
### Added
- Implemented **Phase 3: Complexity Planner & Shot Compiler** under `aether/compiler/`:
  - `schemas.py`: Pydantic V2 models for `ComplexityLevel` (0 to 5), `ShotRequirement`, `SpatialRepresentationPackage`, `CompiledModelPayload`, and compute tiers.
  - `complexity.py`: `ComplexityPlanner` rules engine evaluating scene complexity based on actor count, camera velocity, physical challenges (grapples, fluids, stunts), and continuity sensitivity.
  - `compiler.py`: `ShotCompiler` translating abstract `SceneState` snapshots and `StateDelta` trajectories into model-specific API payloads:
    - Google Veo 3.1: first/last frame pairs, reference assets, cinematic lighting/weather prompt, native audio flags.
    - Kling 3.0: first frame, dynamic motion brush / element tracking masks, lip-sync audio, duration limits.
    - Runway Gen-4.5: Director Mode camera choreography syntax parsing (pan, tilt, zoom, dolly, truck, pedestal, roll), image-to-video conditioning.
    - ComfyUI (CogVideoX & HunyuanVideo): full node workflow graph generation with Video ControlNet (Canny, OpenPose), character LoRA injection, and latent dimension calculation.
    - Auto-compiler with complexity-driven model routing.
  - `test/test_aether_compiler.py`: 52 unit and regression tests with 100% pass rate. Total repository Aether test suite expanded to 163 passing tests.

## [0.4.0-state] - 2026-10-05
### Added
- Implemented **Phase 2: Aether World Model (Scene State Graph)** under `aether/state/`:
  - `schemas.py`: Pydantic V2 models for persistent cinematic reality (`SceneState`, `CharacterState`, `PropState`, `CameraState`, `EnvironmentLighting`, `WardrobeItem`, `MicroExpression`, `SceneAction`, `StateDelta`).
  - `graph.py`: `AetherWorldModel` engine managing active scene states, sequential action application, frozen immutable shot slices, granular state delta computations, and multi-timeline branching/rollback.
  - `continuity.py`: `ContinuityAuditor` multi-shot verification engine enforcing physical velocity thresholds, recipient/hand-aware prop conservation, slot-specific wardrobe damage regressions, medical injury tracking, and reciprocal eyeline gaze detection.
  - `store.py`: `WorldStateStore` supporting JSON roundtrip serialization, file-based persistence, historical query filters (props, movement paths, wardrobe changes), and state ledger export.
  - `test/test_aether_state.py`: 55 unit and integration tests with 100% pass rate. Total Aether test suite expanded to 111 passing tests.

## [0.3.0-bench] - 2026-10-05
### Added
- Implemented **Phase 0: AetherBench** under `aether/bench/`:
  - `schemas.py`: Pydantic V2 schemas for cinematic test scenarios, camera trajectories, physics profiles, lighting, hard gate constraints, defect annotations, and evaluation telemetry.
  - `scenarios.py`: 8 handcrafted gold-standard cinematic scenarios and algorithmic generator for the complete 250-scenario benchmark suite.
  - `registry.py`: Thread-safe scenario registry with category/difficulty indexing, search, JSON serialization, and sanitised directory export.
  - `runner.py`: Semantic scenario validator and multi-gate evaluator enforcing binary hard gates (`ANATOMICAL_INTEGRITY`, `CHARACTER_IDENTITY`, `PROP_CONTINUITY`, `LIP_SYNC_ALIGNMENT`) and soft aesthetic scoring.
  - `defects.py`: Synthetic Defect Ground-Truth Dataset generator (WBS 1.1.3) for calibrating the Phase 4 Critic Council.
  - `pytest.ini`: Project-wide test runner configuration with `pythonpath = .`.
  - `test/test_aether_bench.py`: 56 unit and integration tests with 100% pass rate.

### Added
- Created dedicated branch `feature/project-aether` to isolate development from legacy Manim pipeline.
- Established comprehensive documentation suite in `project-aether-docs/`:
  - `Idea.md`: Core IP definition, philosophical foundation, and paradigm shift from slot-machine generation to autonomous virtual studio.
  - `architecture.md`: Full technical specification of the 6-Pillar Virtual Studio (Creative Brain, State Graph, Complexity Planner, Shot Compiler, Critic Council, Repair Planner, Teacher Agent).
  - `SOW.md`: Detailed Statement of Work covering Phases 0-10, key deliverables, and acceptance criteria.
  - `PMP.md`: Project Management Plan detailing governance, roles, quality gating, and tooling management.
  - `WBS.md`: Hierarchical Work Breakdown Structure with work packages from 1.1 to 1.11.
  - `Project_Schedule.md`: Project timeline, Gantt chart, milestone dates, and critical path analysis.
  - `Risk_Register.md`: Formal risk matrix covering API limitations, VLM temporal blindspots, cost controls, and compute overheads.
  - `Issue_Risk_Log.md`: Active issue and risk tracking log with current technical focus areas.
- Updated root `AGENTS.md` with official instructions directing all AI agents to reference `project-aether-docs/` and adhere to Aether v2 specifications.
- Added agent skills integration policy for leveraging procedural knowledge from the open agent ecosystem (e.g., `skills.sh`).

## [0.2.0-spec] - 2026-10-04
### Changed
- Pivoted from Manim-based 2D programmatic pipeline to Project Aether autonomous cinematic engine.
- Upgraded Aether v1 to Aether v2 based on architectural critique:
  - Added Pillar 2: Persistent Aether World Model (Scene State Graph).
  - Replaced hard-coded model routing with Complexity Planner (Levels 0-5) and Model Tournament.
  - Replaced single VLM critic with specialized Critic Council and binary Hard Gates.
  - Upgraded Teacher from prompt re-roller to surgical Repair Planner and long-term production knowledge learner.

## [0.1.0-alpha] - 2026-10-03
### Added
- ElevenLabs neural voice synthesis integration with disk caching.
- YouTube Shorts publishing daemon with OAuth2 token persistence.
- Audio-video synchronization fixes and spotlight staging in legacy pipeline.
