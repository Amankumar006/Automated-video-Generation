"""Comprehensive Test Suite for Project Aether Phase 10: Autonomous Director Integration (WBS 1.11).

Verifies:
1. Pydantic V2 Schemas:
   - DirectorProductionBrief, FilmScene, DirectorProductionStatus, ShotTimelineRecord, MasteredFilm.
   - Data normalization, string parsing (durations, aspect ratios), and JSON round-trips.
2. Master Virtual Studio Orchestrator (AetherDirector):
   - Full end-to-end autonomous prompt-to-mastered-film execution.
   - World state setup with persistent characters, wardrobe damage, and held props.
   - Complexity classification and multi-model compilation (Veo, Kling, Runway, ComfyUI).
   - Speculative 480p draft gating (rapid pre-audit before 1080p latent upscale).
   - Critic Council binary hard quality gate enforcement (Anatomy, Identity, Props, Lip-sync).
   - Surgical Repair Engine recovery (regional inpainting and audio remastering).
   - Multi-shot continuity auditing and timeline assembly.
   - Dream-RSI trace logging integration into ReplaySimulatorPool.
   - Budget limit enforcement and failure handling.
3. Master CLI & Daemon Entrypoint:
   - Argument parsing and dry-run simulation mode.
   - Module execution compatibility (python3 -m aether.director).
4. Backwards-Compatible Pipeline Wrapper:
   - pipeline/aether_director.py pipeline hooks and convenience functions.
5. Robustness & Edge Cases:
   - Single shot, custom scenes, zero repairs allowed, callback hooks.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from aether.compiler.schemas import (
    AudioRequirement,
    ComplexityLevel,
    ProviderTarget,
    ShotRequirement,
)
from aether.council.schemas import (
    CouncilStatus,
    DefectSeverity,
    HardGateType,
)
from aether.director import (
    AetherDirector,
    DirectorProductionBrief,
    DirectorProductionStatus,
    FilmScene,
    MasteredFilm,
    ProductionState,
    ShotTimelineRecord,
    build_arg_parser,
    main as cli_main,
)
from pipeline.aether_director import (
    AetherDirectorPipeline,
    produce_aether_film,
    run_director_pipeline,
)
from aether.state.schemas import CharacterState, PropState, WardrobeItemState


# ===========================================================================
# 1. Schemas & Data Normalization Tests
# ===========================================================================

class TestDirectorSchemas:
    """Tests Pydantic V2 schemas for production briefs, scenes, and status."""

    def test_brief_defaults_and_normalization(self) -> None:
        brief = DirectorProductionBrief(title="Cyberpunk Heist")
        assert brief.title == "Cyberpunk Heist"
        assert brief.target_duration == 30.0
        assert brief.aspect_ratio == "9:16"
        assert brief.budget_limit == 100.0
        assert brief.speculative_draft is True
        assert brief.max_repair_attempts == 2

    def test_brief_string_duration_and_aspect_ratio_parsing(self) -> None:
        brief_data = {
            "title": "Neon Echoes",
            "target_duration": "45s",
            "aspect_ratio": "landscape",
            "budget": "50.5",
            "speculative": False,
        }
        brief = DirectorProductionBrief.model_validate(brief_data)
        assert brief.target_duration == 45.0
        assert brief.aspect_ratio == "16:9"
        assert brief.budget_limit == 50.5
        assert brief.speculative_draft is False

    def test_brief_target_models_normalization(self) -> None:
        brief = DirectorProductionBrief(
            title="Model Test",
            target_models=[ProviderTarget.VEO_3_1, "kling_3_0"],
        )
        assert brief.target_models == ["veo_3_1", "kling_3_0"]

    def test_film_scene_normalization(self) -> None:
        scene_data = {
            "id": "SC_100",
            "beat": "Infiltration begins",
            "location": "rooftop_helipad",
            "environment": {"lighting": "neon_blue", "weather": "rain"},
            "characters": ["maya", {"character_id": "kai", "name": "Kai"}],
            "props": ["scanner_01"],
            "shots": [
                {
                    "shot_id": "SHOT_101",
                    "target_duration": 4.0,
                    "aspect_ratio": "9:16",
                }
            ],
        }
        scene = FilmScene.model_validate(scene_data)
        assert scene.scene_id == "SC_100"
        assert scene.narrative_beat == "Infiltration begins"
        assert scene.location == "rooftop_helipad"
        assert scene.environment_parameters["lighting"] == "neon_blue"
        assert len(scene.characters) == 2
        assert scene.characters[0]["character_id"] == "maya"
        assert scene.characters[1]["name"] == "Kai"
        assert len(scene.props) == 1
        assert len(scene.shot_list_requirements) == 1
        assert scene.shot_list_requirements[0].shot_id == "SHOT_101"

    def test_production_status_transitions(self) -> None:
        status = DirectorProductionStatus(total_shots=5)
        assert status.state == ProductionState.INITIALIZING
        assert status.total_shots == 5
        assert status.current_shot_index == 0

        status.transition_to(ProductionState.WORLD_SETUP, "Setting up scene state")
        assert status.state == ProductionState.WORLD_SETUP
        assert status.message == "Setting up scene state"

    def test_mastered_film_summary_and_serialization(self) -> None:
        film = MasteredFilm(
            film_id="FILM_TEST_01",
            title="Midnight Protocol",
            scenes_count=2,
            total_shots_count=4,
            duration_seconds=20.0,
            master_video_artifact_uri="asset://master.mp4",
            master_audio_artifact_uri="asset://master.wav",
            total_production_cost=0.45,
            dream_rsi_trace_episode_id="tree_001",
            trace_episode_ids=["tree_001", "tree_002"],
        )
        summary = film.summary()
        assert "Midnight Protocol" in summary
        assert "FILM_TEST_01" in summary
        assert "20.0s" in summary
        assert "tree_001" in summary

        # JSON Roundtrip
        json_data = film.model_dump(mode="json")
        loaded = MasteredFilm.model_validate(json_data)
        assert loaded.film_id == film.film_id
        assert loaded.duration_seconds == film.duration_seconds


# ===========================================================================
# 2. Master Director Orchestrator End-to-End Tests
# ===========================================================================

class TestAetherDirectorOrchestrator:
    """Verifies end-to-end autonomous execution across all 6 pillars."""

    @pytest.fixture
    def temp_director(self) -> AetherDirector:
        with tempfile.TemporaryDirectory() as tmpdir:
            director = AetherDirector(output_dir=Path(tmpdir))
            yield director

    def test_produce_from_concept_string_prompt(self, temp_director: AetherDirector) -> None:
        """Verifies full execution when provided just a raw string prompt."""
        concept = "Cyberpunk detective discovering breach in neon research lab"
        film = temp_director.produce(concept, dry_run=False)

        assert film.status == "COMPLETED"
        assert film.scenes_count >= 1
        assert film.total_shots_count >= 2
        assert film.duration_seconds >= 20.0
        assert film.total_production_cost > 0.0
        assert film.master_video_artifact_uri.endswith(".mp4")
        assert film.master_audio_artifact_uri.endswith(".wav")
        assert len(film.production_timeline_ledger) == film.total_shots_count
        assert len(film.trace_episode_ids) == film.total_shots_count

        # Check world model state
        assert len(temp_director.world_model.character_roster) >= 1
        assert "maya" in temp_director.world_model.character_roster
        assert len(temp_director.world_model.prop_roster) >= 1

        # Check replay simulator pool indexed traces
        assert temp_director.replay_pool.size == film.total_shots_count

    def test_produce_with_explicit_production_brief(self, temp_director: AetherDirector) -> None:
        """Verifies full execution with a fully specified DirectorProductionBrief."""
        brief = DirectorProductionBrief(
            title="The Quantum Heist",
            logline="Maya bypasses security mainframe",
            target_duration=15.0,
            aspect_ratio="16:9",
            visual_style="hyperrealistic anamorphic 35mm",
            budget_limit=50.0,
            speculative_draft=True,
            max_repair_attempts=2,
        )
        film = temp_director.produce(brief, dry_run=False)

        assert film.title == "The Quantum Heist"
        assert film.duration_seconds == pytest.approx(15.0, abs=1.0)
        assert film.metadata["aspect_ratio"] == "16:9"
        assert temp_director.status.state == ProductionState.COMPLETED
        assert temp_director.status.shots_passed_count == film.total_shots_count

    def test_status_callback_receives_lifecycle_updates(self, temp_director: AetherDirector) -> None:
        """Verifies that status_callback is invoked across all production steps."""
        states_recorded: List[ProductionState] = []

        def on_status(st: DirectorProductionStatus) -> None:
            states_recorded.append(st.state)

        temp_director.status_callback = on_status
        temp_director.produce("Brief test", dry_run=True)

        assert ProductionState.WORLD_SETUP in states_recorded
        assert ProductionState.COMPILING_SHOTS in states_recorded
        assert ProductionState.RENDERING_AND_CRITIQUING in states_recorded
        assert ProductionState.MASTERING in states_recorded
        assert ProductionState.COMPLETED in states_recorded


# ===========================================================================
# 3. Speculative Draft Gating & Surgical Repair Recovery Tests
# ===========================================================================

class TestSpeculativeGatingAndRepair:
    """Verifies 480p speculative gating and surgical defect repair recovery."""

    @pytest.fixture
    def temp_director(self) -> AetherDirector:
        with tempfile.TemporaryDirectory() as tmpdir:
            director = AetherDirector(output_dir=Path(tmpdir))
            yield director

    def test_speculative_draft_recovers_from_injected_defect(
        self,
        temp_director: AetherDirector,
    ) -> None:
        """Verifies that an injected anatomical defect in draft triggers surgical repair and passes."""
        shot1 = ShotRequirement(
            shot_id="SHOT_REPAIR_01",
            target_duration=5.0,
            aspect_ratio="9:16",
            character_ids_involved=["maya"],
            enable_speculative_draft=True,
            metadata={
                "injected_draft_defect": {
                    "defect_class": "fused_fingers",
                    "severity": "FATAL",
                    "start_frame": 0,
                    "end_frame": 24,
                    "bbox": [0.4, 0.4, 0.6, 0.6],
                    "character_id": "maya",
                }
            },
        )
        scene = FilmScene(
            scene_id="SC_REPAIR",
            narrative_beat="Tense confrontation",
            location="cleanroom",
            shot_list_requirements=[shot1],
            characters=[{"character_id": "maya", "name": "Maya Lin"}],
            props=[],
        )
        brief = DirectorProductionBrief(
            title="Repair Test Film",
            target_duration=5.0,
            scenes=[scene],
            max_repair_attempts=2,
            speculative_draft=True,
        )

        film = temp_director.produce(brief, dry_run=False)

        assert film.status == "COMPLETED"
        assert film.total_shots_count == 1
        # Repairs were performed
        assert temp_director.status.repairs_performed_count >= 1
        ledger_entry = film.production_timeline_ledger[0]
        assert ledger_entry["repairs_count"] >= 1
        assert ledger_entry["passed_hard_gates"] is True

    def test_full_candidate_lip_sync_defect_audio_remaster(
        self,
        temp_director: AetherDirector,
    ) -> None:
        """Verifies that dialogue audio desync triggers audio remaster repair."""
        shot1 = ShotRequirement(
            shot_id="SHOT_LIPSYNC_01",
            target_duration=4.0,
            aspect_ratio="9:16",
            audio=AudioRequirement(dialogue=True, dialogue_text="System rebooted."),
            enable_speculative_draft=False,
            metadata={"lip_sync_offset_ms": 80.0},  # Desync trips Hard Gate
        )
        scene = FilmScene(
            scene_id="SC_AUDIO",
            narrative_beat="Dialogue line",
            location="server_room",
            shot_list_requirements=[shot1],
            characters=[{"character_id": "maya"}],
            props=[],
        )
        brief = DirectorProductionBrief(
            title="Lip Sync Test Film",
            target_duration=4.0,
            scenes=[scene],
            max_repair_attempts=2,
            speculative_draft=False,
        )

        film = temp_director.produce(brief, dry_run=False)

        assert film.status == "COMPLETED"
        assert temp_director.status.repairs_performed_count >= 1
        ledger_entry = film.production_timeline_ledger[0]
        assert ledger_entry["passed_hard_gates"] is True


# ===========================================================================
# 4. Multi-Shot Continuity Auditing & Assembly Tests
# ===========================================================================

class TestContinuityAndTimelineAssembly:
    """Verifies multi-shot cinematic continuity auditing across cuts."""

    @pytest.fixture
    def temp_director(self) -> AetherDirector:
        with tempfile.TemporaryDirectory() as tmpdir:
            director = AetherDirector(output_dir=Path(tmpdir))
            yield director

    def test_multi_shot_continuity_audited(self, temp_director: AetherDirector) -> None:
        """Verifies multi-shot transition audits are captured in MasteredFilm."""
        shot1 = ShotRequirement(shot_id="SHOT_C_01", target_duration=4.0)
        shot2 = ShotRequirement(shot_id="SHOT_C_02", target_duration=4.0)
        shot3 = ShotRequirement(shot_id="SHOT_C_03", target_duration=4.0)

        scene = FilmScene(
            scene_id="SC_CONT",
            location="cleanroom",
            shot_list_requirements=[shot1, shot2, shot3],
            characters=[
                {
                    "character_id": "maya",
                    "position": [0.0, 0.0, 1.0],
                    "wardrobe": {"jacket": {"id": "leather_001", "state": "torn"}},
                    "held_props": {"right": "keycard"},
                }
            ],
            props=[{"prop_id": "keycard", "name": "Keycard", "owner_id": "maya"}],
        )
        brief = DirectorProductionBrief(
            title="Continuity Film",
            target_duration=12.0,
            scenes=[scene],
        )

        film = temp_director.produce(brief, dry_run=False)

        assert film.total_shots_count == 3
        assert film.continuity_report is not None
        assert film.continuity_report["total_transitions_checked"] == 2
        assert film.continuity_report["all_transitions_valid"] is True


# ===========================================================================
# 5. Dream-RSI Trace Logging Integration Tests
# ===========================================================================

class TestDreamRSITraceIntegration:
    """Verifies that all render episodes are serialized into the ReplaySimulatorPool."""

    @pytest.fixture
    def temp_director(self) -> AetherDirector:
        with tempfile.TemporaryDirectory() as tmpdir:
            director = AetherDirector(output_dir=Path(tmpdir))
            yield director

    def test_traces_indexed_in_replay_pool(self, temp_director: AetherDirector) -> None:
        brief = DirectorProductionBrief(title="Dream-RSI Film", target_duration=10.0)
        film = temp_director.produce(brief, dry_run=False)

        assert len(film.trace_episode_ids) == film.total_shots_count
        assert temp_director.replay_pool.size == film.total_shots_count

        # Retrieve each tree and verify contents
        for tree_id in film.trace_episode_ids:
            tree = temp_director.replay_pool.get_tree(tree_id)
            assert tree is not None
            assert tree.tree_id == tree_id
            assert len(tree.nodes) >= 3
            assert tree.total_cost > 0.0

        # Primary episode ID matches first tree
        assert film.dream_rsi_trace_episode_id == film.trace_episode_ids[0]


# ===========================================================================
# 6. Budget Limits & Failure Boundaries
# ===========================================================================

class TestBudgetLimitsAndBoundaries:
    """Verifies budget limits and error handling."""

    @pytest.fixture
    def temp_director(self) -> AetherDirector:
        with tempfile.TemporaryDirectory() as tmpdir:
            director = AetherDirector(output_dir=Path(tmpdir))
            yield director

    def test_budget_limit_exceeded_raises_error(self, temp_director: AetherDirector) -> None:
        """Verifies that a tiny budget limit stops execution with RuntimeError."""
        brief = DirectorProductionBrief(
            title="Over Budget Film",
            target_duration=30.0,
            budget_limit=0.01,  # Tiny budget
        )
        with pytest.raises(RuntimeError, match="budget limit"):
            temp_director.produce(brief, dry_run=False)

        assert temp_director.status.state == ProductionState.FAILED


# ===========================================================================
# 7. CLI & Argument Parsing Tests
# ===========================================================================

class TestDirectorCLI:
    """Verifies CLI argument parsing and execution modes."""

    def test_cli_argument_parser(self) -> None:
        parser = build_arg_parser()
        args = parser.parse_args([
            "--brief", "Noir sci-fi thriller",
            "--duration", "45",
            "--aspect-ratio", "16:9",
            "--budget-limit", "75.0",
            "--no-speculative",
            "--max-repairs", "3",
            "--dry-run",
        ])
        assert args.brief == "Noir sci-fi thriller"
        assert args.duration == 45.0
        assert args.aspect_ratio == "16:9"
        assert args.budget_limit == 75.0
        assert args.speculative is False
        assert args.max_repairs == 3
        assert args.dry_run is True

    def test_cli_main_dry_run_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = cli_main([
                "--brief", "Quick Dry Run",
                "--duration", "10",
                "--output", tmpdir,
                "--dry-run",
            ])
            assert exit_code == 0

            # Verify manifest was generated
            manifests = list(Path(tmpdir).glob("*_manifest.json"))
            assert len(manifests) == 1


# ===========================================================================
# 8. Pipeline Backwards-Compatible Wrapper Tests
# ===========================================================================

class TestPipelineWrapper:
    """Verifies pipeline/aether_director.py helper functions."""

    def test_aether_director_pipeline_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = AetherDirectorPipeline(output_dir=tmpdir)
            film = pipeline.run("Pipeline prompt", duration=10.0, dry_run=True)
            assert isinstance(film, MasteredFilm)
            assert film.status == "COMPLETED"

    def test_produce_aether_film_convenience(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            film = produce_aether_film(
                brief="Convenience function test",
                duration=10.0,
                output_dir=tmpdir,
                dry_run=True,
            )
            assert isinstance(film, MasteredFilm)
            assert film.status == "COMPLETED"

    def test_run_director_pipeline_serializable_dict(self) -> None:
        result = run_director_pipeline("JSON pipeline test", duration=10.0, dry_run=True)
        assert isinstance(result, dict)
        assert result["status"] == "COMPLETED"
        assert "master_video_artifact_uri" in result
        assert "dream_rsi_trace_episode_id" in result



# ===========================================================================
# 9. Hardened Edge Cases & Architectural Gating Tests
# ===========================================================================

class TestHardenedDirectorEdgeCases:
    """Verifies architectural invariants: dynamic routing, draft gating aborts, and budget limits."""

    @pytest.fixture
    def temp_director(self) -> AetherDirector:
        with tempfile.TemporaryDirectory() as tmpdir:
            director = AetherDirector(output_dir=Path(tmpdir))
            yield director

    def test_dynamic_complexity_provider_routing(self, temp_director: AetherDirector) -> None:
        """Verifies that dialogue/movement shots dynamically route to Kling vs Veo based on Complexity."""
        film = temp_director.produce("Dynamic routing concept test", dry_run=True)
        # Shot 1 has dialogue (Complexity Level 3) -> should route to kling_3_0
        shot_providers = {s["shot_id"]: (s["provider"], s["complexity_level"]) for s in film.production_timeline_ledger}
        assert "SHOT_001" in shot_providers
        assert "SHOT_002" in shot_providers
        # SHOT_002 is talking head dialogue
        assert shot_providers["SHOT_002"][0] == "kling_3_0"
        assert shot_providers["SHOT_002"][1] == 3
        # SHOT_001 is camera movement
        assert shot_providers["SHOT_001"][0] == "veo_3_1"

    def test_failed_shot_sets_film_status_to_failed(self, temp_director: AetherDirector) -> None:
        """Verifies that unrepairable defects result in FAILED status for both director and MasteredFilm."""
        shot = ShotRequirement(
            shot_id="SHOT_FATAL_01",
            target_duration=5.0,
            metadata={
                "injected_defect": {
                    "defect_class": "fused_fingers",
                    "severity": "FATAL",
                    "start_frame": 0,
                    "end_frame": 24,
                    "character_id": "maya",
                }
            },
        )
        scene = FilmScene(scene_id="SC_FATAL", shot_list_requirements=[shot])
        brief = DirectorProductionBrief(title="Fatal Defect Film", max_repair_attempts=0, scenes=[scene])

        film = temp_director.produce(brief, dry_run=False)
        assert film.status == "FAILED"
        assert temp_director.status.state == ProductionState.FAILED
        assert temp_director.status.shots_passed_count == 0

    def test_speculative_draft_failure_aborts_1080p_upscale(self, temp_director: AetherDirector) -> None:
        """Verifies speculative 480p draft gating aborts before expensive 1080p generation, saving compute."""
        shot = ShotRequirement(
            shot_id="SHOT_DRAFT_REJECT",
            target_duration=5.0,
            enable_speculative_draft=True,
            metadata={
                "injected_draft_defect": {
                    "defect_class": "fused_fingers",
                    "severity": "FATAL",
                    "start_frame": 0,
                    "end_frame": 24,
                    "character_id": "maya",
                }
            },
        )
        scene = FilmScene(scene_id="SC_DRAFT_FAIL", shot_list_requirements=[shot])
        brief = DirectorProductionBrief(
            title="Draft Gating Abort Test",
            max_repair_attempts=0,
            speculative_draft=True,
            scenes=[scene],
        )

        film = temp_director.produce(brief, dry_run=False)
        assert film.status == "FAILED"
        assert film.production_timeline_ledger[0]["speculative_draft_passed"] is False
        # Cost should only reflect 480p draft generation ($0.02) + VLM token audit ($0.015) = $0.035
        # NOT the full $0.13 that includes 1080p upscale!
        assert film.total_production_cost == pytest.approx(0.035, abs=0.001)

    def test_single_shot_budget_limit_enforced(self, temp_director: AetherDirector) -> None:
        """Verifies that budget limit is strictly enforced on single-shot productions."""
        shot = ShotRequirement(shot_id="SHOT_BUDGET_01", target_duration=5.0)
        scene = FilmScene(scene_id="SC_BUDGET", shot_list_requirements=[shot])
        brief = DirectorProductionBrief(title="Strict Budget Film", budget_limit=0.05, scenes=[scene])

        with pytest.raises(RuntimeError, match="budget limit"):
            temp_director.produce(brief, dry_run=False)

        assert temp_director.status.state == ProductionState.FAILED

    def test_repair_failure_retains_defect(self) -> None:
        """Verifies that if repair execution returns success_status=False, defects are not falsely cleared."""
        from aether.repair.executor import SurgicalRepairExecutor
        from aether.repair.schemas import RepairExecutionResult

        class FailingRepairExecutor(SurgicalRepairExecutor):
            def execute_plan(self, plan, base_asset_uri=None, auto_execute_fallback=False):
                return [
                    RepairExecutionResult(
                        task_id=task.task_id,
                        success_status=False,
                        error_message="Simulated executor failure",
                    )
                    for task in plan.ordered_tasks_list
                ]

        with tempfile.TemporaryDirectory() as tmpdir:
            director = AetherDirector(
                output_dir=Path(tmpdir),
                repair_executor=FailingRepairExecutor(),
            )
            shot = ShotRequirement(
                shot_id="SHOT_REPAIR_FAIL_01",
                target_duration=5.0,
                character_ids_involved=["maya"],
                enable_speculative_draft=False,
                metadata={
                    "injected_defect": {
                        "defect_class": "fused_fingers",
                        "severity": "FATAL",
                        "start_frame": 0,
                        "end_frame": 24,
                        "character_id": "maya",
                    }
                },
            )
            scene = FilmScene(scene_id="SC_01", shot_list_requirements=[shot], characters=[{"character_id": "maya"}])
            brief = DirectorProductionBrief(title="Repair Failure Film", max_repair_attempts=1, speculative_draft=False, scenes=[scene])

            film = director.produce(brief, dry_run=False)
            assert film.status == "FAILED"
            assert director.status.shots_passed_count == 0

    def test_multi_scene_location_and_character_tracking(self, temp_director: AetherDirector) -> None:
        """Verifies multi-scene briefs update scene_id, location, and character rosters across cuts."""
        scene1 = FilmScene(
            scene_id="SC_01",
            location="cleanroom",
            characters=[{"character_id": "maya", "name": "Maya"}],
            shot_list_requirements=[ShotRequirement(shot_id="SHOT_S1_01", target_duration=4.0)],
        )
        scene2 = FilmScene(
            scene_id="SC_02",
            location="rooftop",
            characters=[{"character_id": "kai", "name": "Kai"}],
            shot_list_requirements=[ShotRequirement(shot_id="SHOT_S2_01", target_duration=4.0)],
        )
        brief = DirectorProductionBrief(title="Multi Scene Film", scenes=[scene1, scene2])

        film = temp_director.produce(brief, dry_run=True)
        assert film.status == "COMPLETED"
        assert film.scenes_count == 2
        assert temp_director.world_model.active_state.scene_id == "SC_02"
        assert temp_director.world_model.active_state.location == "rooftop"
        assert "maya" in temp_director.world_model.active_state.character_roster
        assert "kai" in temp_director.world_model.active_state.character_roster

    def test_run_now_false_staged_execution(self, temp_director: AetherDirector) -> None:
        """Verifies run_now=False stages the production plan without running rendering."""
        brief = DirectorProductionBrief(title="Staged Run Test", target_duration=10.0)
        film = temp_director.produce(brief, run_now=False)

        assert film.status == "STAGED"
        assert temp_director.status.state == ProductionState.COMPILING_SHOTS
        assert film.total_production_cost == 0.0
        assert film.total_shots_count == 2
        assert film.production_timeline_ledger[0]["video_uri"].startswith("asset://staged/")

    def test_cli_no_run_now_flag(self) -> None:
        """Verifies CLI argument parsing for --no-run-now."""
        parser = build_arg_parser()
        args = parser.parse_args(["--no-run-now"])
        assert args.run_now is False

    def test_custom_world_model_preservation(self) -> None:
        """Verifies pre-configured world models are preserved in AetherDirector."""
        from aether.state.graph import AetherWorldModel
        from aether.state.schemas import SceneState, CharacterState

        custom_wm = AetherWorldModel()
        custom_state = SceneState(
            scene_id="SC_CUSTOM",
            location="orbital_station",
            character_roster={"astro": CharacterState(character_id="astro", name="Astro")},
        )
        custom_wm.set_active_state(custom_state)

        with tempfile.TemporaryDirectory() as tmpdir:
            director = AetherDirector(output_dir=Path(tmpdir), world_model=custom_wm)
            film = director.produce("Preserve test", dry_run=True)
            assert director.world_model is custom_wm
            assert "astro" in director.world_model.active_state.character_roster


if __name__ == "__main__":
    pytest.main(["-v", __file__])

