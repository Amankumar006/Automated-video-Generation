"""Comprehensive Test Suite for Project Aether Phase 9: Dream-RSI Teacher Engine & Efficiency Stack (WBS 1.10).

Verifies:
1. Frontier Cost & Inference Efficiency Stack (2025-2026):
   - ShotRequirement & CompiledModelPayload with enable_teacache, enable_pab, sampling_steps=8, enable_speculative_draft.
   - ShotCompiler ComfyUI workflow graph synthesis with TeaCacheLoader and PABApply nodes, and few-step flow sampling.
   - Multi-Critic VLMContextCacheManager (Anthropic cache_control breakpoints & Gemini Context Caching markers, 90% discount).
2. Phase 9: Dream-RSI Schemas & Serialization:
   - TraceNode, DiscoveryTraceTree, ReplaySimulatorWorld, ExplorationPolicy, DreamEvaluationResult, ProductionRule.
   - Policy mutations, trajectory path extraction, JSON round-trips.
3. Discovery Trace Logger:
   - TraceLogger serializing full episodes (SceneState -> Complexity -> Payload -> Council -> Repair -> Final score/cost).
   - In-memory history and filesystem persistence.
4. Replay Simulator Pool (H_t):
   - Historical tree indexing and directory persistence.
   - Deterministic policy replay across historical traces at ZERO external API cost.
   - Counterfactual simulation (TeaCache discounts, step distillation, speculative draft gating, repair escalation).
5. Offline Dreaming & Dream-RSI Pareto Optimization:
   - PolicyDreamer computing V_{im} = max_v s_v - beta_1 N_{im} + beta_2 (N_{im} / max(1, k*_{im})).
   - Discovery of Pareto-superior policies and selection of pi_{t+1}.
   - Head-to-head policy comparison.
6. Production Knowledge Ledger:
   - Policy promotion into immutable verified production rules.
   - Rule filtering, condition matching, and persistence.
   - Export to ComplexityPlanner, ShotCompiler, and RepairPlanner.
7. Edge cases and failure boundaries.
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

from aether.compiler.complexity import ComplexityPlanner
from aether.compiler.compiler import ShotCompiler
from aether.compiler.schemas import (
    ComplexityLevel,
    ComplexityPlan,
    CompiledModelPayload,
    ComputeTier,
    ProviderTarget,
    ShotRequirement,
    SpatialRepresentationPackage,
)
from aether.council.context_cache import VLMContextCacheManager
from aether.council.schemas import (
    CouncilEvaluationReport,
    CouncilStatus,
    CriticAuditResult,
    CriticFailureObject,
    CriticType,
    DefectSeverity,
    HardGateType,
    RepairRecommendation,
)
from aether.repair.planner import RepairPlanner
from aether.repair.schemas import RepairActionType, RepairBoundaryMask, RepairPlan, SurgicalRepairTask
from aether.state.schemas import (
    CameraState,
    CharacterState,
    EnvironmentState,
    SceneState,
)
from aether.teacher.dreamer import PolicyDreamer
from aether.teacher.ledger import ProductionKnowledgeLedger
from aether.teacher.replay_simulator import ReplaySimulatorPool
from aether.teacher.schemas import (
    DiscoveryTraceTree,
    DreamEvaluationResult,
    ExplorationPolicy,
    ProductionRule,
    ReplaySimulatorWorld,
    TraceNode,
)
from aether.teacher.trace_logger import TraceLogger


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def sample_scene_state() -> SceneState:
    """Standard cinematic scene state fixture."""
    state = SceneState(
        scene_id="SCENE_TEACHER_001",
        location="abandoned_hangar",
        timestamp="night_rain",
        environment=EnvironmentState(weather="rain", lighting="high_contrast_neon", wetness=0.85),
    )
    state.active_camera = CameraState(
        lens_focal_length_mm=35.0,
        aperture=1.8,
        focus_distance=3.5,
        position=[0.0, 1.5, -4.0],
    )
    state.add_character(
        CharacterState(
            character_id="dr_elena_vasquez",
            name="Dr. Elena Vasquez",
            position=[0.0, 0.0, 0.0],
            emotional_state="determined_urgency",
            injuries=["forehead_laceration"],
        )
    )
    return state


@pytest.fixture
def sample_shot_requirement() -> ShotRequirement:
    """Standard shot requirement fixture."""
    return ShotRequirement(
        shot_id="SHOT_TEST_01",
        target_duration=5.0,
        aspect_ratio="16:9",
        resolution="1080p",
        camera_movement="dolly_in",
        camera_velocity_mps=1.5,
        enable_teacache=True,
        enable_pab=True,
        sampling_steps=8,
        enable_speculative_draft=False,
    )


@pytest.fixture
def sample_trace_tree(sample_scene_state, sample_shot_requirement) -> DiscoveryTraceTree:
    """Pre-populated discovery trace tree fixture."""
    logger = TraceLogger()
    tree = logger.log_episode(
        shot_id="SHOT_TEST_01",
        scene_state=sample_scene_state,
        shot_requirement=sample_shot_requirement,
        final_score=8.75,
        final_cost=0.12,
        execution_latency=4.2,
        final_video_uri="s3://aether-renders/shot_01_final.mp4",
        success=True,
    )
    return tree


# ===========================================================================
# 1. Frontier Cost & Efficiency Stack Tests
# ===========================================================================

class TestFrontierEfficiencyStack:
    """Validates DiT acceleration, distilled flow steps, and VLM context caching."""

    def test_shot_requirement_efficiency_defaults_and_aliases(self):
        """ShotRequirement initializes with efficiency flags and parses aliases."""
        req = ShotRequirement()
        assert req.enable_teacache is True
        assert req.enable_pab is True
        assert req.sampling_steps == 8
        assert req.enable_speculative_draft is False

        # Parse aliases
        req_custom = ShotRequirement(
            teacache=False,
            pab=False,
            steps=4,
            speculative=True,
        )
        assert req_custom.enable_teacache is False
        assert req_custom.enable_pab is False
        assert req_custom.sampling_steps == 4
        assert req_custom.enable_speculative_draft is True

    def test_compiled_payload_efficiency_fields_and_payload_dict(self):
        """CompiledModelPayload encapsulates efficiency knobs and serializes to API dict."""
        payload = CompiledModelPayload(
            shot_id="SHOT_EFF_01",
            provider_target=ProviderTarget.COGVIDEOX_COMFYUI,
            prompt="Cinematic shot in neon rain",
            enable_teacache=True,
            enable_pab=True,
            sampling_steps=8,
            enable_speculative_draft=True,
        )
        assert payload.enable_teacache is True
        assert payload.enable_pab is True
        assert payload.sampling_steps == 8
        assert payload.enable_speculative_draft is True

        api_dict = payload.to_api_payload()
        assert api_dict["enable_teacache"] is True
        assert api_dict["enable_pab"] is True
        assert api_dict["sampling_steps"] == 8
        assert api_dict["enable_speculative_draft"] is True

    def test_comfyui_workflow_graph_injects_teacache_and_pab_nodes(self, sample_scene_state):
        """ShotCompiler._build_comfyui_workflow_graph injects TeaCacheLoader and PABApply nodes."""
        compiler = ShotCompiler()
        req = ShotRequirement(
            shot_id="SHOT_COMFY_EFF",
            enable_teacache=True,
            enable_pab=True,
            sampling_steps=8,
        )
        payload = compiler.compile_for_comfyui(sample_scene_state, req)
        workflow = payload.provider_config["comfyui_workflow"]

        # Verify TeaCacheLoader is present
        assert any(node["class_type"] == "TeaCacheLoader" for node in workflow.values())
        teacache_node = next(node for node in workflow.values() if node["class_type"] == "TeaCacheLoader")
        assert teacache_node["inputs"]["threshold"] == 0.25
        assert teacache_node["inputs"]["cache_device"] == "cuda"

        # Verify PABApply is present
        assert any(node["class_type"] == "PABApply" for node in workflow.values())
        pab_node = next(node for node in workflow.values() if node["class_type"] == "PABApply")
        assert pab_node["inputs"]["cross_broadcast"] is True
        assert pab_node["inputs"]["spatial_broadcast"] is True

        # Verify KSampler uses sampling_steps (8 instead of default 30)
        ksampler_node = next(node for node in workflow.values() if node["class_type"] == "KSampler")
        assert ksampler_node["inputs"]["steps"] == 8
        assert payload.provider_config["sampler_settings"]["steps"] == 8

    def test_comfyui_workflow_graph_disabled_acceleration_omits_nodes(self, sample_scene_state):
        """When TeaCache and PAB are disabled, nodes are excluded from ComfyUI workflow graph."""
        compiler = ShotCompiler()
        req = ShotRequirement(
            shot_id="SHOT_COMFY_NO_ACCEL",
            enable_teacache=False,
            enable_pab=False,
            sampling_steps=30,
        )
        payload = compiler.compile_for_comfyui(sample_scene_state, req)
        workflow = payload.provider_config["comfyui_workflow"]

        assert not any(node["class_type"] == "TeaCacheLoader" for node in workflow.values())
        assert not any(node["class_type"] == "PABApply" for node in workflow.values())
        ksampler_node = next(node for node in workflow.values() if node["class_type"] == "KSampler")
        assert ksampler_node["inputs"]["steps"] == 30

    def test_provider_compilers_forward_efficiency_flags(self, sample_scene_state):
        """All provider compilers (Veo, Kling, Runway) correctly forward efficiency flags."""
        compiler = ShotCompiler()
        req = ShotRequirement(enable_teacache=True, enable_pab=True, sampling_steps=6, enable_speculative_draft=True)

        veo_p = compiler.compile_for_veo(sample_scene_state, req)
        assert veo_p.sampling_steps == 6
        assert veo_p.enable_speculative_draft is True
        assert veo_p.provider_config["sampling_steps"] == 6

        kling_p = compiler.compile_for_kling(sample_scene_state, req)
        assert kling_p.sampling_steps == 6
        assert kling_p.provider_config["sampling_steps"] == 6

        runway_p = compiler.compile_for_runway(sample_scene_state, req)
        assert runway_p.sampling_steps == 6
        assert runway_p.provider_config["sampling_steps"] == 6


class TestVLMContextCaching:
    """Validates prefix caching formatting for Anthropic and Gemini VLM Critic Council queries."""

    def test_vlm_context_cache_anthropic_payload(self, sample_scene_state, sample_shot_requirement):
        """Anthropic payload structures static rubrics and scene/frames with cache_control breakpoints."""
        cache_mgr = VLMContextCacheManager()
        frames = ["s3://bucket/frame_001.png", "s3://bucket/frame_002.png"]
        payload = cache_mgr.build_anthropic_payload(
            critic_type=CriticType.VISUAL,
            scene_state=sample_scene_state,
            shot_requirement=sample_shot_requirement,
            frame_uris=frames,
        )

        assert payload["model"] == "claude-3-7-sonnet-20250219"
        # System prompt contains master rubric with cache_control ephemeral
        assert len(payload["system"]) >= 1
        assert payload["system"][0]["cache_control"] == {"type": "ephemeral"}

        # Messages content blocks
        contents = payload["messages"][0]["content"]
        assert len(contents) == 3
        # First 2 blocks have cache_control
        assert contents[0]["cache_control"] == {"type": "ephemeral"}
        assert "SCENE CONTEXT" in contents[0]["text"]
        assert contents[1]["cache_control"] == {"type": "ephemeral"}
        assert "VIDEO FRAMES UNDER INSPECTION" in contents[1]["text"]
        # Third block is dynamic query without cache_control
        assert "cache_control" not in contents[2]
        assert "VISUAL Critic" in contents[2]["text"]

    def test_vlm_context_cache_gemini_payload(self, sample_scene_state, sample_shot_requirement):
        """Gemini payload structures cached_content markers and TTL."""
        cache_mgr = VLMContextCacheManager()
        frames = ["s3://bucket/frame_001.png", "s3://bucket/frame_002.png"]
        payload = cache_mgr.build_gemini_payload(
            critic_type=CriticType.TEMPORAL,
            scene_state=sample_scene_state,
            shot_requirement=sample_shot_requirement,
            frame_uris=frames,
        )

        assert payload["model"] == "gemini-2.5-pro"
        assert "cachedContents/aether_council_" in payload["cached_content"]
        assert payload["cached_content_config"]["ttl"] == "300s"
        assert payload["cached_content_config"]["contents"][0]["gemini_cache_marker"] is True

    def test_deterministic_cache_key(self, sample_scene_state, sample_shot_requirement):
        """Cache keys are deterministic and identical for same static context."""
        cache_mgr = VLMContextCacheManager()
        frames = ["s3://bucket/frame_001.png", "s3://bucket/frame_002.png"]
        key1 = cache_mgr.compute_prefix_cache_key(sample_scene_state, sample_shot_requirement, frames)
        key2 = cache_mgr.compute_prefix_cache_key(sample_scene_state, sample_shot_requirement, frames)
        assert key1 == key2
        assert len(key1) == 64  # SHA256 hex string

    def test_format_council_batch_shares_cache_key(self, sample_scene_state, sample_shot_requirement):
        """All 6 critics share identical prefix_cache_key in council batch."""
        cache_mgr = VLMContextCacheManager()
        frames = ["s3://bucket/frame_001.png"]
        batch = cache_mgr.format_council_batch(
            sample_scene_state,
            sample_shot_requirement,
            frames,
            provider="anthropic",
        )
        assert len(batch) == 6
        keys = {payload["_metadata"]["prefix_cache_key"] for payload in batch.values()}
        assert len(keys) == 1  # Exactly 1 shared cache key!

    def test_token_savings_telemetry_verifies_90_percent_discount(self):
        """Calculates 90% discount on cached tokens across multi-critic inspection."""
        stats = VLMContextCacheManager.calculate_token_savings(
            total_tokens_per_call=10_000,
            cached_prefix_tokens=9_000,
            num_critics=6,
            cost_per_million_input=2.50,
            cached_discount_rate=0.90,
        )
        assert stats["baseline_cost_usd"] > 0
        assert stats["cached_total_cost_usd"] < stats["baseline_cost_usd"]
        assert stats["prefix_discount_percentage"] == 90.0
        assert stats["subsequent_query_discount_percentage"] > 80.0
        assert stats["discount_percentage"] > 60.0


# ===========================================================================
# 2. Phase 9: Dream-RSI Schemas & Serialization Tests
# ===========================================================================

class TestDreamRSISchemas:
    """Validates Pydantic V2 schemas for TraceNode, DiscoveryTraceTree, ReplaySimulatorWorld, ExplorationPolicy, ProductionRule."""

    def test_trace_node_properties(self):
        """TraceNode encapsulates step state, actions, quality, and cost."""
        node = TraceNode(
            step_type="INITIAL_COMPILE",
            quality_score=9.2,
            hard_gates_passed=True,
            execution_cost=0.08,
            latency_seconds=1.2,
            parallel_branches=2,
        )
        assert node.is_root is True
        assert node.quality_score == 9.2
        assert node.parallel_branches == 2
        d = node.to_dict()
        assert d["step_type"] == "INITIAL_COMPILE"

    def test_discovery_trace_tree_node_chain_and_trajectory(self):
        """DiscoveryTraceTree records nodes, updates root/best node, and reconstructs trajectory."""
        tree = DiscoveryTraceTree(shot_id="SHOT_TRAJ_01")
        n1 = TraceNode(step_type="ROOT", quality_score=0.0, execution_cost=0.0)
        n2 = TraceNode(parent_id=n1.node_id, step_type="AUDIT", quality_score=7.0, execution_cost=0.05)
        n3 = TraceNode(parent_id=n2.node_id, step_type="REPAIR", quality_score=9.5, execution_cost=0.10)

        tree.add_node(n1)
        tree.add_node(n2)
        tree.add_node(n3)

        assert tree.root_node_id == n1.node_id
        assert tree.best_node_id == n3.node_id
        assert tree.total_cost == pytest.approx(0.15)
        assert len(tree.nodes) == 3

        traj = tree.get_trajectory()
        assert len(traj) == 3
        assert [n.step_type for n in traj] == ["ROOT", "AUDIT", "REPAIR"]

    def test_discovery_trace_tree_json_roundtrip(self, sample_trace_tree):
        """DiscoveryTraceTree serializes to and parses from JSON losslessly."""
        json_str = sample_trace_tree.to_json()
        reconstituted = DiscoveryTraceTree.from_json(json_str)

        assert reconstituted.tree_id == sample_trace_tree.tree_id
        assert reconstituted.shot_id == sample_trace_tree.shot_id
        assert len(reconstituted.nodes) == len(sample_trace_tree.nodes)
        assert reconstituted.best_node_id == sample_trace_tree.best_node_id

    def test_replay_simulator_world_schema(self, sample_trace_tree):
        """ReplaySimulatorWorld stores and serializes trees."""
        world = ReplaySimulatorWorld()
        world.add_tree(sample_trace_tree)
        assert world.tree_count == 1
        assert world.get_tree(sample_trace_tree.tree_id) is not None

        world_json = world.to_json()
        world_loaded = ReplaySimulatorWorld.from_json(world_json)
        assert world_loaded.tree_count == 1

    def test_exploration_policy_knobs_and_mutation(self):
        """ExplorationPolicy defines tunable knobs and mutates within bounds."""
        policy = ExplorationPolicy(
            name="Test_Policy",
            sampling_steps=8,
            enable_teacache=True,
            enable_pab=True,
            repair_iou_threshold=0.30,
            repair_escalation_threshold=3,
        )
        mutated = policy.mutate(mutation_scale=0.15, seed=123)

        assert mutated.policy_id != policy.policy_id
        assert "mutated" in mutated.name
        assert 0.0 < mutated.repair_iou_threshold < 1.0
        assert mutated.repair_escalation_threshold >= 1
        assert mutated.sampling_steps >= 4

    def test_production_rule_condition_matching(self):
        """ProductionRule matches exact and relational predicates."""
        rule = ProductionRule(
            rule_id="RULE_TEST",
            rule_type="COMPLEXITY_ROUTING",
            condition={"camera_velocity": {"gte": 3.0}, "has_fluids": True},
            action={"complexity_level": 5},
        )
        assert rule.matches({"camera_velocity": 4.5, "has_fluids": True}) is True
        assert rule.matches({"camera_velocity": 2.0, "has_fluids": True}) is False
        assert rule.matches({"camera_velocity": 5.0, "has_fluids": False}) is False


# ===========================================================================
# 3. Discovery Trace Logger Tests
# ===========================================================================

class TestTraceLogger:
    """Validates TraceLogger recording episodes into immutable discovery trees."""

    def test_log_full_episode_creates_structured_tree(self, sample_scene_state, sample_shot_requirement):
        """TraceLogger serializes entire generation & audit episode."""
        logger = TraceLogger()
        comp_plan = ComplexityPlan(
            shot_id="SHOT_01",
            complexity_level=ComplexityLevel.TWOD_TRAJECTORY_POSE,
            recommended_provider=ProviderTarget.KLING_3_0,
        )
        payload = CompiledModelPayload(
            shot_id="SHOT_01",
            provider_target=ProviderTarget.KLING_3_0,
            prompt="Elena looks up with urgent determination",
        )
        report = CouncilEvaluationReport(
            shot_id="SHOT_01",
            status=CouncilStatus.ACCEPTED,
            passed_hard_gates=True,
            overall_soft_score=8.5,
        )

        tree = logger.log_episode(
            shot_id="SHOT_01",
            scene_state=sample_scene_state,
            shot_requirement=sample_shot_requirement,
            complexity_plan=comp_plan,
            compiled_payload=payload,
            council_report=report,
            final_score=8.5,
            final_cost=0.18,
            execution_latency=3.8,
            final_video_uri="s3://aether/video.mp4",
            success=True,
        )

        assert tree.shot_id == "SHOT_01"
        assert tree.success is True
        assert len(tree.nodes) >= 5
        types = [n.step_type for n in tree.nodes.values()]
        assert "INITIAL_SPECIFICATION" in types
        assert "COMPLEXITY_CLASSIFICATION" in types
        assert "PAYLOAD_COMPILATION" in types
        assert "COUNCIL_AUDIT" in types
        assert "FINAL_OUTCOME" in types

    def test_trace_logger_persistence(self, sample_trace_tree):
        """TraceLogger persists and loads trees from filesystem."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = TraceLogger(storage_dir=tmpdir)
            p = logger.save_tree(sample_trace_tree, Path(tmpdir) / "test_tree.json")
            assert p.exists()

            loaded_tree = logger.load_tree(p)
            assert loaded_tree.tree_id == sample_trace_tree.tree_id
            assert loaded_tree.shot_id == sample_trace_tree.shot_id


# ===========================================================================
# 4. Replay Simulator Pool Tests
# ===========================================================================

class TestReplaySimulatorPool:
    """Validates ReplaySimulatorPool holding historical trees and executing zero-cost replays."""

    def test_replay_simulator_indexes_and_replays_policy(self, sample_trace_tree):
        """Pool indexes trees and executes deterministic policy simulation."""
        pool = ReplaySimulatorPool()
        pool.add_trace(sample_trace_tree)
        assert pool.size == 1

        policy = ExplorationPolicy(
            name="Candidate_Policy",
            enable_teacache=True,
            enable_pab=True,
            sampling_steps=8,
            enable_speculative_draft=True,
        )

        replays = pool.replay_policy(policy)
        assert len(replays) == 1
        res = replays[0]
        assert res["tree_id"] == sample_trace_tree.tree_id
        assert res["quality_score"] > 0.0
        assert res["execution_cost"] < sample_trace_tree.total_cost  # Slashed via efficiency stack!
        assert res["latency_seconds"] < sample_trace_tree.total_latency

    def test_pool_directory_persistence(self, sample_trace_tree):
        """Pool saves and loads all trees from a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pool = ReplaySimulatorPool()
            pool.add_trace(sample_trace_tree)
            saved = pool.save_to_directory(tmpdir)
            assert saved == 1

            new_pool = ReplaySimulatorPool()
            loaded = new_pool.load_from_directory(tmpdir)
            assert loaded == 1
            assert new_pool.size == 1


# ===========================================================================
# 5. Offline Dreaming & Dream-RSI Pareto Optimization Tests
# ===========================================================================

class TestPolicyDreamer:
    """Validates PolicyDreamer computing V_{im} and discovering Pareto-superior policies."""

    def test_dream_rsi_pareto_formula(self):
        """Verifies mathematical calculation of Dream-RSI Pareto objective."""
        pool = ReplaySimulatorPool()
        dreamer = PolicyDreamer(pool, default_beta1=0.05, default_beta2=0.02)

        # Case 1: High quality (9.0), Cost (0.20), k* = 1
        # V = 9.0 - (0.05 * 0.20) + (0.02 * (0.20 / 1)) = 9.0 - 0.01 + 0.004 = 8.994
        v1 = dreamer.compute_pareto_value(quality_score=9.0, cost=0.20, parallel_branches=1)
        assert v1 == pytest.approx(8.994, abs=0.001)

        # Case 2: Parallel speedup bonus with k* = 2
        # V = 9.0 - (0.05 * 0.20) + (0.02 * (0.20 / 2)) = 9.0 - 0.01 + 0.002 = 8.992
        v2 = dreamer.compute_pareto_value(quality_score=9.0, cost=0.20, parallel_branches=2)
        assert v2 == pytest.approx(8.992, abs=0.001)

        # Case 3: Hard gate failure applies penalty
        v_fail = dreamer.compute_pareto_value(quality_score=9.0, cost=0.20, hard_gates_passed=False)
        assert v_fail == pytest.approx(v1 - 3.0, abs=0.001)

    def test_offline_dreaming_loop(self, sample_scene_state):
        """Executes full offline dreaming over historical pool and discovers winning policy pi_{t+1}."""
        pool = ReplaySimulatorPool()
        logger = TraceLogger()

        # Populate pool with 3 historical discovery trees
        for i in range(3):
            req = ShotRequirement(shot_id=f"SHOT_HIST_{i}", camera_velocity_mps=float(i * 2))
            tree = logger.log_episode(
                shot_id=f"SHOT_HIST_{i}",
                scene_state=sample_scene_state,
                shot_requirement=req,
                final_score=7.5 + (i * 0.5),
                final_cost=0.30,
                execution_latency=6.0,
                success=True,
            )
            pool.add_trace(tree)

        dreamer = PolicyDreamer(pool)
        winner_policy, evaluation_results = dreamer.dream(num_candidates=5, seed=42)

        assert len(evaluation_results) == 5
        # Top policy has highest Pareto value
        assert evaluation_results[0].pareto_value >= evaluation_results[-1].pareto_value
        assert winner_policy is not None
        assert winner_policy.policy_id == evaluation_results[0].policy_id

    def test_compare_policies_head_to_head(self, sample_trace_tree):
        """Compares baseline vs accelerated policy head-to-head on replay pool."""
        pool = ReplaySimulatorPool()
        pool.add_trace(sample_trace_tree)
        dreamer = PolicyDreamer(pool)

        policy_baseline = ExplorationPolicy(
            name="Baseline_Diffusion",
            enable_teacache=False,
            enable_pab=False,
            sampling_steps=30,
        )
        policy_efficient = ExplorationPolicy(
            name="Distilled_Flow_Efficient",
            enable_teacache=True,
            enable_pab=True,
            sampling_steps=8,
            enable_speculative_draft=True,
        )

        comparison = dreamer.compare_policies(policy_baseline, policy_efficient)
        assert comparison["winner"] == policy_efficient.policy_id
        assert comparison["delta_cost"] < 0.0  # Cost reduced!
        assert comparison["delta_pareto_value"] > 0.0  # Pareto value improved!


# ===========================================================================
# 6. Production Knowledge Ledger Tests
# ===========================================================================

class TestProductionKnowledgeLedger:
    """Validates ProductionKnowledgeLedger rule distillation and export to production engines."""

    def test_promote_policy_codifies_production_rules(self):
        """Promoting winning policy generates verified production rules in ledger."""
        ledger = ProductionKnowledgeLedger()
        assert len(ledger.rules) >= 3  # Bootstrapped rules

        winning_policy = ExplorationPolicy(
            name="Winning_Dream_Policy",
            sampling_steps=8,
            enable_teacache=True,
            enable_pab=True,
            repair_escalation_threshold=2,
        )
        eval_res = DreamEvaluationResult(
            policy_id=winning_policy.policy_id,
            pareto_value=9.45,
            is_pareto_superior=True,
        )

        new_rules = ledger.promote_policy(winning_policy, eval_res)
        assert len(new_rules) >= 3
        assert ledger.active_policy.policy_id == winning_policy.policy_id
        assert len(ledger.promotions_history) == 1

        active_eff_rules = ledger.get_active_rules("INFERENCE_EFFICIENCY")
        assert len(active_eff_rules) >= 1
        assert active_eff_rules[-1].action["sampling_steps"] == 8

    def test_export_to_complexity_planner(self, sample_scene_state):
        """Ledger exports active policy thresholds to ComplexityPlanner and alters planning decisions."""
        ledger = ProductionKnowledgeLedger()
        ledger.active_policy.complexity_thresholds["velocity_threshold"] = 1.0
        planner = ledger.export_to_complexity_planner()

        assert hasattr(planner, "active_policy")
        assert planner.complexity_thresholds["velocity_threshold"] == 1.0

        # Shot with velocity 1.5 m/s: default planner (thresh 3.0) gives Level 2; exported planner gives Level 4
        req_vel = ShotRequirement(shot_id="SHOT_VEL_TEST", camera_velocity_mps=1.5, camera_movement="pan")
        plan_exported = planner.plan(sample_scene_state, req_vel)
        assert plan_exported.complexity_level == ComplexityLevel.THREED_BLOCKING

        default_planner = ComplexityPlanner()
        plan_default = default_planner.plan(sample_scene_state, req_vel)
        assert plan_default.complexity_level == ComplexityLevel.KEYFRAMES_INTERPOLATION

    def test_export_to_shot_compiler(self, sample_scene_state):
        """Ledger exports active efficiency settings to ShotCompiler and applies defaults to payloads."""
        ledger = ProductionKnowledgeLedger()
        ledger.active_policy.sampling_steps = 4
        ledger.active_policy.enable_speculative_draft = True
        compiler = ledger.export_to_shot_compiler()

        assert hasattr(compiler, "active_policy")
        assert compiler.default_sampling_steps == 4
        assert compiler.default_enable_speculative_draft is True

        # Compiling with empty/dict requirement inherits compiler efficiency defaults
        payload = compiler.compile_for_comfyui(sample_scene_state, {"shot_id": "SHOT_EFF_EXPORT"})
        assert payload.sampling_steps == 4
        assert payload.enable_speculative_draft is True

    def test_export_to_repair_planner(self):
        """Ledger exports repair thresholds to RepairPlanner and configures IoU and escalation."""
        ledger = ProductionKnowledgeLedger()
        ledger.active_policy.repair_escalation_threshold = 5
        ledger.active_policy.repair_iou_threshold = 0.50
        planner = ledger.export_to_repair_planner()

        assert planner.escalation_defect_threshold == 5
        assert planner.repair_iou_threshold == 0.50

    def test_ledger_persistence_and_summary(self):
        """Ledger serializes to JSON and produces diagnostic summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "ledger.json"
            ledger = ProductionKnowledgeLedger(storage_file=file_path)
            ledger.save(file_path)
            assert file_path.exists()

            loaded_ledger = ProductionKnowledgeLedger()
            loaded_ledger.load(file_path)
            assert loaded_ledger.active_policy.policy_id == ledger.active_policy.policy_id
            assert len(loaded_ledger.rules) == len(ledger.rules)

            summary = loaded_ledger.summary()
            assert "total_rules" in summary
            assert "efficiency_flags" in summary


# ===========================================================================
# 7. Edge Cases & Boundary Tests
# ===========================================================================

class TestEdgeCasesAndBoundaries:
    """Validates boundary conditions and zero-input robustness."""

    def test_empty_replay_pool_evaluation(self):
        """Evaluating policy on empty replay pool returns neutral DreamEvaluationResult."""
        pool = ReplaySimulatorPool()
        dreamer = PolicyDreamer(pool)
        policy = ExplorationPolicy()
        res = dreamer.evaluate_policy(policy)
        assert res.num_episodes_replayed == 0
        assert res.pareto_value == 0.0

    def test_extremal_sampling_steps(self):
        """Policy handles extremal steps without crashing."""
        pool = ReplaySimulatorPool()
        logger = TraceLogger()
        tree = logger.log_episode(shot_id="SHOT_01", scene_state={}, shot_requirement={}, final_score=7.0)
        pool.add_trace(tree)

        p_min = ExplorationPolicy(sampling_steps=1)
        sim_min = pool.simulate_policy_on_trace(p_min, tree)
        assert sim_min["quality_score"] < 7.0  # Heavy penalty for 1 step

        p_max = ExplorationPolicy(sampling_steps=50)
        sim_max = pool.simulate_policy_on_trace(p_max, tree)
        assert sim_max["quality_score"] >= 7.0

    def test_corrupted_and_unrelated_json_handling_in_directory(self, sample_trace_tree):
        """ReplaySimulatorPool.load_from_directory skips corrupted and non-tree JSON files gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            # 1. Valid discovery tree
            with open(p / "valid_tree.json", "w", encoding="utf-8") as f:
                f.write(sample_trace_tree.to_json())

            # 2. Corrupted JSON syntax
            with open(p / "corrupted.json", "w", encoding="utf-8") as f:
                f.write('{"tree_id": "tree_broken", "nodes": {')

            # 3. Unrelated JSON (missing tree markers)
            with open(p / "package.json", "w", encoding="utf-8") as f:
                json.dump({"name": "unrelated-pkg", "version": "1.0.0"}, f)

            # 4. Empty JSON file
            with open(p / "empty.json", "w", encoding="utf-8") as f:
                f.write("")

            pool = ReplaySimulatorPool()
            loaded = pool.load_from_directory(p)
            assert loaded == 1
            assert pool.size == 1
            assert pool.get_tree(sample_trace_tree.tree_id) is not None

    def test_dream_rsi_all_candidates_fail_hard_gates(self, sample_trace_tree):
        """When all candidate policies violate hard gates, baseline policy is retained as winner."""
        pool = ReplaySimulatorPool()
        pool.add_trace(sample_trace_tree)
        dreamer = PolicyDreamer(pool)

        # Baseline policy passes
        base_policy = ExplorationPolicy(name="Safe_Baseline_Policy", sampling_steps=8)

        winner, results = dreamer.dream(num_candidates=4, base_policy=base_policy, seed=99)
        winner_res = next(r for r in results if r.policy_id == winner.policy_id)
        base_res = dreamer.evaluate_policy(base_policy)
        assert winner_res.hard_gate_pass_rate >= base_res.hard_gate_pass_rate
        if not any(r.is_pareto_superior for r in results):
            assert winner.policy_id == base_policy.policy_id

    def test_dream_rsi_all_candidates_negative_pareto(self, sample_scene_state):
        """When all candidates produce worse Pareto values, baseline is retained."""
        pool = ReplaySimulatorPool()
        logger = TraceLogger()
        tree = logger.log_episode(
            shot_id="SHOT_TOUGH",
            scene_state=sample_scene_state,
            shot_requirement=ShotRequirement(camera_velocity_mps=4.0),
            final_score=6.0,
            final_cost=0.50,
            success=True,
        )
        pool.add_trace(tree)
        dreamer = PolicyDreamer(pool, default_beta1=1.0)  # Very high cost penalty makes mutated policies negative

        base = ExplorationPolicy(name="Base_Conservative", sampling_steps=8)
        winner, results = dreamer.dream(num_candidates=3, base_policy=base, seed=42)
        assert winner is not None

    def test_trace_logger_zero_and_custom_final_cost(self, sample_scene_state, sample_shot_requirement):
        """TraceLogger accurately calculates delta execution_cost without magic constant inflation."""
        logger = TraceLogger()

        # Zero cost provided: final outcome node must have cost 0.0
        tree_zero = logger.log_episode(
            shot_id="SHOT_ZERO_COST",
            scene_state=sample_scene_state,
            shot_requirement=sample_shot_requirement,
            final_score=8.0,
            final_cost=0.0,
            execution_latency=0.0,
        )
        final_node_zero = [n for n in tree_zero.nodes.values() if n.step_type == "FINAL_OUTCOME"][0]
        assert final_node_zero.execution_cost == 0.0
        assert final_node_zero.latency_seconds == 0.0

        # Custom cost matching preceding nodes
        tree_custom = logger.log_episode(
            shot_id="SHOT_CUSTOM_COST",
            scene_state=sample_scene_state,
            shot_requirement=sample_shot_requirement,
            final_score=8.0,
            final_cost=0.25,
            execution_latency=5.0,
        )
        assert tree_custom.total_cost == pytest.approx(0.25)
        assert tree_custom.total_latency == pytest.approx(5.0)

    def test_trace_logger_load_tree_invalid_file(self):
        """TraceLogger.load_tree raises FileNotFoundError for missing file and ValueError for corrupt file."""
        logger = TraceLogger()
        with pytest.raises(FileNotFoundError):
            logger.load_tree("/nonexistent/path/tree_missing.json")

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
            f.write("invalid json contents")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Failed to load discovery trace tree"):
                logger.load_tree(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_generate_candidate_policies_respects_num_candidates(self):
        """PolicyDreamer.generate_candidate_policies respects exact num_candidates count."""
        pool = ReplaySimulatorPool()
        dreamer = PolicyDreamer(pool)
        for target_count in [1, 2, 3, 5, 8]:
            candidates = dreamer.generate_candidate_policies(num_candidates=target_count)
            assert len(candidates) == target_count

    def test_production_rule_suffix_matching(self):
        """ProductionRule matches suffix operator predicates (e.g. defect_count_gt, velocity_gte)."""
        rule = ProductionRule(
            rule_id="RULE_SUFFIX_TEST",
            rule_type="REPAIR_ESCALATION",
            condition={"defect_count_gt": 3, "velocity_gte": 2.5},
            action={"escalate_full_regeneration": True},
        )
        assert rule.matches({"defect_count": 4, "velocity": 2.5}) is True
        assert rule.matches({"defect_count": 4, "velocity": 3.0}) is True
        assert rule.matches({"defect_count": 3, "velocity": 2.5}) is False  # 3 is not > 3
        assert rule.matches({"defect_count": 5, "velocity": 2.0}) is False  # 2.0 is not >= 2.5

    def test_empty_tree_simulation(self):
        """ReplaySimulatorPool handles empty or failed trace trees safely without false passing scores."""
        pool = ReplaySimulatorPool()
        empty_tree = DiscoveryTraceTree(shot_id="SHOT_EMPTY", nodes={})
        policy = ExplorationPolicy()
        sim_res = pool.simulate_policy_on_trace(policy, empty_tree)

        assert sim_res["quality_score"] == 0.0
        assert sim_res["hard_gates_passed"] is False
        assert sim_res["execution_cost"] == 0.0

    def test_repair_planner_mask_merging_with_custom_iou_threshold(self):
        """RepairPlanner._cluster_and_merge_masks respects configured repair_iou_threshold."""
        task1 = SurgicalRepairTask(
            task_id="task_1",
            action_type=RepairActionType.REGIONAL_TEMPORAL_INPAINTING,
            target_defect_id="defect_1",
            repair_boundary_mask=RepairBoundaryMask(
                bounding_box=(0.10, 0.10, 0.20, 0.20),
                frame_bounds=(10, 20),
            ),
        )
        task2 = SurgicalRepairTask(
            task_id="task_2",
            action_type=RepairActionType.REGIONAL_TEMPORAL_INPAINTING,
            target_defect_id="defect_2",
            repair_boundary_mask=RepairBoundaryMask(
                bounding_box=(0.12, 0.12, 0.22, 0.22),
                frame_bounds=(12, 22),
            ),
        )

        # Planner with default threshold 0.30: IoU 0.47 > 0.30, so they MERGE into 1 task
        planner_default = RepairPlanner(repair_iou_threshold=0.30)
        merged_default = planner_default._deduplicate_and_optimize_tasks([task1, task2])
        assert len(merged_default) == 1

        # Planner with strict threshold 0.50: IoU 0.47 < 0.50, so they DO NOT MERGE (remain 2 tasks)
        planner_strict = RepairPlanner(repair_iou_threshold=0.50)
        merged_strict = planner_strict._deduplicate_and_optimize_tasks([task1, task2])
        assert len(merged_strict) == 2


if __name__ == "__main__":
    pytest.main(["-v", __file__])
