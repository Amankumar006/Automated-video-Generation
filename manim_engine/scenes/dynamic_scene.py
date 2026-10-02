"""
The Model Verse — Dynamic Composite Scene (Visual Engine 2.0)
Replaces rigid monolithic templates with an autonomous, declarative visual compiler.
Directly choreographs modular 3Blue1Brown primitives based on the Declarative Visual Scene Graph (VSG)
and Domain Taxonomy (Robotics/TAMP, Neural SAE, MoE, Attention, Search, Benchmarks).
"""

import os
import sys
import json
from typing import Optional, List, Dict, Any, Tuple
import numpy as np
from pathlib import Path
from manim import *

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT, BG_CARBON
)

# Enforce 9:16 vertical dimensions and 3b1b background
config.pixel_width = VIDEO_WIDTH
config.pixel_height = VIDEO_HEIGHT
config.frame_width = FRAME_WIDTH
config.frame_height = FRAME_HEIGHT
config.background_color = BG_CARBON

from pipeline.vsg_schema import (
    convert_legacy_spec_to_vsg,
    VisualStoryboard,
    DomainTaxonomy,
    VisualPrimitiveType,
    ActionType
)

# Import Modular 3b1b Primitives
from manim_engine.primitives.robotics.coupled_state_space import (
    CoupledCanvas, CoupledNode, ConstraintProjectionSheaf, GeometricRefinementPulse
)
from manim_engine.primitives.robotics.kinematic_arm import ParametricKinematicArm
from manim_engine.primitives.robotics.ast_tree import ASTMorphTree
from manim_engine.primitives.robotics.sandbox_pod import SandboxIsolationPod

from manim_engine.primitives.neural.sae_constellation import SAEConstellation, FeatureProjectionChip
from manim_engine.primitives.neural.moe_lattice import SparseMoELattice, LoadBalancingManometer
from manim_engine.primitives.neural.attention_grid import TransformerAttentionGrid, RoutingRibbon

from manim_engine.primitives.search.search_tree import DynamicSearchTree, MCTSNodeGauge
from manim_engine.primitives.search.branch_bound import BranchAndBoundLaser

from manim_engine.primitives.metrics.dual_metric_gauge import (
    DualMetricGauge, RadialScoreMeter, ComparativeCoordinateManifold
)
from manim_engine.scheduler import KineticScheduler
from pipeline.arxiv_vector_extractor import get_paper_vector_figure


class DynamicCompositeScene(Scene):
    """
    Unified 3b1b Pedagogical Scene Compiler.
    Ingests any valid VSG specification or legacy JSON spec and choreographs
    living geometric manifolds without static text cards.
    """

    def construct(self):
        # 1. Load active specification & storyboard
        self.storyboard, self.raw_spec = self.load_active_storyboard()
        self.domain = self.storyboard.domain_taxonomy
        self.scheduler = KineticScheduler(self.raw_spec)
        
        # 2. Setup 3b1b Chalkboard Canvas (#0A0D14 + subtle dot matrix)
        self.setup_chalkboard()
        
        # 3. Setup Persistent Brand Header & Formula Tray
        self.current_formula_mobj = None
        self.setup_header()
        
        # 4. Dispatch Domain-Specific Semantic Choreography
        print(f"🎬 Executing Visual Engine 2.0 Choreography for Domain: '{self.domain.value}'...")
        spec_id = str(self.raw_spec.get("id", "")).lower()
        if "one_second" in spec_id or "thinks" in spec_id:
            self.play_ai_thinking_in_one_second_choreography()
        elif "diffusion" in spec_id or "static" in spec_id or "creates_images" in spec_id:
            self.play_diffusion_static_choreography()
        elif self.domain == DomainTaxonomy.ROBOTICS_TAMP:
            self.play_robotics_tamp_choreography()
        elif self.domain == DomainTaxonomy.NEURAL_SAE:
            self.play_neural_sae_choreography()
        elif self.domain == DomainTaxonomy.NEURAL_MOE:
            self.play_neural_moe_choreography()
        elif self.domain == DomainTaxonomy.NEURAL_ATTENTION:
            self.play_neural_attention_choreography()
        elif self.domain == DomainTaxonomy.ALGORITHMIC_SEARCH:
            self.play_algorithmic_search_choreography()
        else:
            self.play_quantitative_benchmark_choreography()
            
        # 5. Outro Brand Signature
        self.play_brand_outro()

    # =========================================================================
    # SPECIFICATION LOADING & SETUP
    # =========================================================================

    def load_active_storyboard(self) -> tuple[VisualStoryboard, dict]:
        """Loads specification from ACTIVE_SPEC_PATH or default template."""
        spec_path = os.environ.get("ACTIVE_SPEC_PATH")
        spec_data = {}
        if spec_path and os.path.exists(spec_path):
            try:
                with open(spec_path, "r", encoding="utf-8") as f:
                    spec_data = json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading ACTIVE_SPEC_PATH '{spec_path}': {e}")
        
        if not spec_data:
            # Fallback to any available template in pipeline/templates
            templates = list((PROJECT_ROOT / "pipeline" / "templates").glob("*.json"))
            if templates:
                with open(templates[0], "r", encoding="utf-8") as f:
                    spec_data = json.load(f)
            else:
                spec_data = {
                    "id": "sample_dynamic_spec",
                    "title": "Autonomous TAMP Agentic Synthesis",
                    "category": "mechanism_deepdive",
                    "hook_tag": "TAMP REVOLUTION",
                    "beats": [{"beat_id": i, "text": f"Beat {i} spoken audio"} for i in range(1, 7)]
                }
                
        storyboard = convert_legacy_spec_to_vsg(spec_data)
        return storyboard, spec_data

    def setup_chalkboard(self):
        """Constructs the signature 3Blue1Brown carbon chalkboard with dot lattice."""
        self.camera.background_color = "#0A0D14"
        
        # Subtle dot lattice grid
        dots = VGroup()
        for x in np.arange(-3.6, 3.7, 0.9):
            for y in np.arange(-6.0, 6.1, 0.9):
                dots.add(Dot(point=[x, y, 0], radius=0.016, color="#2D3748", fill_opacity=0.35))
        self.add(dots)

    def setup_header(self):
        """Places subtle brand watermark in the topmost safe zone, preserving pure canvas space."""
        hook_text = self.storyboard.hook_tag.upper()
        watermark = VGroup(
            Text("THE MODEL VERSE", font_size=11, font="Helvetica", color="#10B981", weight=BOLD),
            Text(" // ", font_size=11, font="Helvetica", color="#475569"),
            Text(hook_text, font_size=10, font="Helvetica", color="#94A3B8", weight=MEDIUM)
        ).arrange(RIGHT, buff=0.1).move_to([0, 7.1, 0])
        self.header_group = watermark
        self.add(self.header_group)

    def display_math_formula(self, beat_id: int, run_time: float = 0.6):
        """
        Renders and morphs the active beat's mathematical LaTeX formula in the chalk tray.
        Uses rendered SVG from public/math_svgs if available, or clean MathTex fallback.
        """
        matching_formula = None
        for mf in self.storyboard.math_formulas:
            if mf.beat_id == beat_id:
                matching_formula = mf
                break
                
        if not matching_formula and beat_id <= len(self.storyboard.math_formulas):
            matching_formula = self.storyboard.math_formulas[beat_id - 1]
            
        new_mobj = None
        if matching_formula:
            cand_path = PROJECT_ROOT / "public" / "math_svgs" / matching_formula.filename
            if cand_path.exists():
                try:
                    new_mobj = SVGMobject(str(cand_path))
                    new_mobj.set_color(matching_formula.color or "#38BDF8")
                except Exception:
                    pass
            if new_mobj is None and matching_formula.latex:
                clean_latex = matching_formula.latex.strip("$").replace("\\mathrm", "\\text")
                try:
                    new_mobj = MathTex(clean_latex, font_size=22, color=matching_formula.color or "#38BDF8")
                except Exception:
                    new_mobj = Text(clean_latex, font_size=16, color="#38BDF8")
                    
        if new_mobj:
            if new_mobj.width > 5.8:
                new_mobj.scale_to_fit_width(5.8)
            if new_mobj.height > 1.15:
                new_mobj.scale_to_fit_height(1.15)
            new_mobj.move_to([0, -4.5, 0])
            
            # Subtitle / term annotation badge
            ann_group = VGroup()
            if matching_formula.term_annotations:
                for ann in matching_formula.term_annotations[:2]:
                    term = ann.get("term", "")
                    lbl = ann.get("label", "")
                    chip = Text(f"{term} : {lbl}", font_size=12, font="Helvetica", color="#94A3B8")
                    ann_group.add(chip)
                ann_group.arrange(RIGHT, buff=0.4).next_to(new_mobj, DOWN, buff=0.12)
                if ann_group.width > 6.0:
                    ann_group.scale_to_fit_width(6.0)
                    
            full_formula_group = VGroup(new_mobj, ann_group)
            full_formula_group = self.apply_layout_patch(full_formula_group, "math_formula", beat_id)
            
            if self.current_formula_mobj:
                self.play(ReplacementTransform(self.current_formula_mobj, full_formula_group), run_time=run_time)
            else:
                self.play(FadeIn(full_formula_group, shift=UP * 0.2), run_time=run_time)
            self.current_formula_mobj = full_formula_group

    def apply_layout_patch(self, mobj: Mobject, entity_id: str, beat_id: int) -> Mobject:
        """Applies hot-patched layout overrides (offsets and scales) to a mobject."""
        overrides = self.raw_spec.get("layout_overrides", {})
        beat_overrides = overrides.get(str(beat_id), overrides.get(beat_id, {}))
        ent_override = beat_overrides.get(entity_id, overrides.get(entity_id, {}))
        
        if ent_override:
            scale_factor = ent_override.get("scale", ent_override.get("scale_multiplier", 1.0))
            if scale_factor != 1.0:
                mobj.scale(scale_factor)
            dx = ent_override.get("dx", 0.0)
            dy = ent_override.get("dy", 0.0)
            if dx != 0.0 or dy != 0.0:
                mobj.shift(RIGHT * dx + UP * dy)
        return mobj


    def get_beat_duration(self, beat_id: int, default_dur: float = 6.0) -> float:
        """Calculates duration allotted to the specific beat."""
        for b in self.raw_spec.get("beats", []):
            if b.get("beat_id") == beat_id:
                if "slot_duration" in b:
                    return float(b["slot_duration"])
                if "audio_duration" in b:
                    return float(b["audio_duration"]) + 0.35
                if "duration" in b:
                    return float(b["duration"])
        return default_dur

    def kinetic_pacing(
        self,
        beat_id: int,
        anchor_word: Optional[str] = None,
        desired_action_dur: float = 1.5
    ) -> tuple[float, float, float]:
        """
        Calculates (pre_wait, action_run_time, post_wait) from acoustic word timings
        ensuring animations trigger synchronously with spoken narration.
        """
        budget = self.scheduler.compute_kinetic_budget(
            beat_id=beat_id,
            anchor_word=anchor_word,
            desired_action_duration=desired_action_dur
        )
        return budget["pre_wait"], budget["action_run_time"], budget["post_wait"]

    def get_arxiv_vector_figure(self, index: int = 0) -> Optional[SVGMobject]:
        """Loads and prepares native chalkboard-recolored arXiv vector figure if available."""
        arxiv_id = self.raw_spec.get("arxiv_id") or self.storyboard.metadata.get("arxiv_id")
        if not arxiv_id:
            return None
        svg_path = get_paper_vector_figure(arxiv_id, index=index)
        if not svg_path or not os.path.exists(svg_path):
            return None
        try:
            mobj = SVGMobject(svg_path)
            if mobj.width > 5.8:
                mobj.scale_to_fit_width(5.8)
            if mobj.height > 4.5:
                mobj.scale_to_fit_height(4.5)
            return mobj
        except Exception as e:
            print(f"⚠️ Could not load vector figure SVGMobject: {e}")
            return None

    # =========================================================================
    # DOMAIN 1: ROBOTICS & TASK/MOTION PLANNING (TAMP) CHOREOGRAPHY
    # =========================================================================

    def play_robotics_tamp_choreography(self):
        """
        Coupled dual-manifold choreography:
        Discrete Task Plan (top) coupled with Continuous C-space Trajectories (bottom).
        """
        # BEAT 1: Foundational Split Manifold (Coupled Discrete-Continuous Space)
        b1_dur = self.get_beat_duration(1, 8.5)
        canvas = CoupledCanvas(title="Coupled Task & Motion Planning")
        arm = ParametricKinematicArm(
            base_point=[-1.2, -3.2, 0], link_lengths=[1.5, 1.2],
            joint_angles=[0.4, 0.8], color="#38BDF8"
        )
        tp_text = Text("TASK: ∃ q ∈ C_free . Reach(q, Goal)", font="Courier", font_size=10, color="#94A3B8")
        tp_bg = RoundedRectangle(
            corner_radius=0.08,
            width=tp_text.width + 0.36,
            height=0.36,
            color="#334155",
            fill_color="#0A0D14",
            fill_opacity=0.92,
            stroke_width=1.0
        )
        tp_text.move_to(tp_bg)
        task_predicate = VGroup(tp_bg, tp_text).move_to([0, 3.2, 0])
        node_init = CoupledNode(title="Action a_0", symbol="a_0", status="active").move_to([0, 2.0, 0])
        sheaf_init = ConstraintProjectionSheaf(
            coupled_node=node_init,
            continuous_target=arm.ee_frame,
            color="#38BDF8"
        )
        self.display_math_formula(1, run_time=0.5)
        self.play(Create(canvas), run_time=1.2)
        self.play(Create(arm), FadeIn(task_predicate), FadeIn(node_init), run_time=1.2)
        self.play(sheaf_init.pulse_beam(run_time=1.4))
        self.wait(max(0.1, b1_dur - 4.3))
        
        # BEAT 2: The Bottleneck (Exponential Search Complexity & Infeasibility)
        b2_dur = self.get_beat_duration(2, 10.5)
        self.display_math_formula(2, run_time=0.5)
        self.play(FadeOut(node_init), FadeOut(sheaf_init), FadeOut(task_predicate), run_time=0.4)
        
        # Add obstacle and target goal in C-space
        obstacle = Circle(radius=0.45, color="#EF4444", fill_opacity=0.35, stroke_width=2).move_to([0.2, -2.0, 0])
        obs_lbl = Text("OBSTACLE", font_size=11, font="Helvetica", color="#EF4444", weight=BOLD).move_to(obstacle.get_center())
        obs_group = VGroup(obstacle, obs_lbl)
        
        target_goal = Dot(point=[1.5, -1.8, 0], radius=0.12, color="#34D399")
        target_ring = Circle(radius=0.28, color="#34D399", stroke_width=1.5).move_to(target_goal.get_center())
        goal_group = VGroup(target_goal, target_ring)
        
        # Search tree branching choking on continuous collision
        search_tree = DynamicSearchTree(root_pos=np.array([0.0, 3.2, 0.0]), h_spacing=1.4, v_spacing=0.75)
        node_cand = CoupledNode(title="Pick(Can_1)", symbol="a_1", status="failed").move_to([-1.5, 2.2, 0])
        node_cand = self.apply_layout_patch(node_cand, "node_cand", 2)
        sheaf_fail = ConstraintProjectionSheaf(
            coupled_node=node_cand,
            continuous_target=obstacle,
            color="#EF4444"
        )
        self.play(Create(obs_group), Create(goal_group), run_time=0.8)
        self.play(FadeIn(search_tree), run_time=1.0)
        search_tree.animate_mcts_cycle(self, selected_path=["s0", "s2_fail", "s21_coll"], reward_color="#EF4444", duration=1.2)
        self.play(FadeIn(node_cand), FadeIn(sheaf_fail), run_time=0.6)
        
        # Collision shockwave: GeometricRefinementPulse
        witness, cross = GeometricRefinementPulse.trigger_failure(
            self,
            coupled_node=node_cand,
            sheaf=sheaf_fail,
            collision_point=np.array([0.2, -2.0, 0]),
            duration=min(2.0, b2_dur * 0.3)
        )
        self.wait(max(0.1, b2_dur - 6.0))
        
        # BEAT 3: Core Innovation (Code AST Synthesis & Amortized Policy)
        b3_dur = self.get_beat_duration(3, 10.5)
        self.display_math_formula(3, run_time=0.5)
        self.play(
            FadeOut(search_tree), FadeOut(node_cand), FadeOut(sheaf_fail),
            FadeOut(witness), FadeOut(cross),
            run_time=0.5
        )
        
        ast_tree = ASTMorphTree(scale=0.75).move_to([0.0, 2.35, 0])
        tl_text = Text("SYNTHESIZED CODE AST POLICY", font_size=10, font="Helvetica", color="#38BDF8", weight=BOLD)
        tl_bg = RoundedRectangle(
            corner_radius=0.08,
            width=tl_text.width + 0.36,
            height=0.34,
            color="#0284C7",
            fill_color="#0A0D14",
            fill_opacity=0.95,
            stroke_width=1.2
        )
        tl_text.move_to(tl_bg)
        tree_label = VGroup(tl_bg, tl_text).next_to(ast_tree, UP, buff=0.15)
        main_fig_mobj = VGroup(ast_tree, tree_label)
        main_fig_mobj = self.apply_layout_patch(main_fig_mobj, "ast_tree", 3)
        
        sheaf = ConstraintProjectionSheaf(
            coupled_node=ast_tree.nodes,
            continuous_target=target_goal,
            color="#34D399"
        )
        self.play(FadeIn(main_fig_mobj, shift=DOWN * 0.2), run_time=1.2)
        self.play(sheaf.pulse_beam(run_time=1.4))
        self.wait(max(0.1, b3_dur - 3.6))
        
        # BEAT 4: Mathematical Mechanism (Synthesis Execution in Clean Sandbox)
        b4_dur = self.get_beat_duration(4, 11.0)
        self.display_math_formula(4, run_time=0.5)
        self.play(FadeOut(main_fig_mobj), FadeOut(sheaf), run_time=0.5)
        
        pod = SandboxIsolationPod(title="KINEMATIC SANDBOX [SIMULATION]", scale=0.75).move_to([0.0, 2.3, 0])
        pod = self.apply_layout_patch(pod, "sandbox_pod", 4)
        self.play(FadeIn(pod, scale=0.9), run_time=0.8)
        self.play(pod.run_assertions(run_time=1.8))
        
        # Valid path avoids obstacle smoothly, reaching the target goal
        self.play(arm.animate_to_angles([0.8, -0.6], run_time=1.5))
        goal_pulse = Circle(radius=0.45, color="#34D399", stroke_width=2.5).move_to(target_goal.get_center())
        self.play(Create(goal_pulse), goal_pulse.animate.scale(1.4).set_opacity(0), run_time=0.8)
        self.wait(max(0.1, b4_dur - 5.4))
        
        # BEAT 5: Quantitative Proof (Comparative Coordinate Manifold)
        b5_dur = self.get_beat_duration(5, 11.5)
        self.display_math_formula(5, run_time=0.5)
        
        # Clean transition of canvas to payoff meter
        self.play(
            FadeOut(canvas), FadeOut(arm), FadeOut(obs_group),
            FadeOut(goal_group), FadeOut(pod),
            run_time=0.8
        )
        
        meta = self.storyboard.metadata
        manifold = ComparativeCoordinateManifold(
            model_a_name=meta.get("challenger", meta.get("model_a", "Coding Policy")),
            model_a_score=meta.get("model_a_stat", "95%"),
            val_a=0.95,
            model_b_name=meta.get("incumbent", meta.get("model_b", "Classical TAMP")),
            model_b_score=meta.get("model_b_stat", "47%"),
            val_b=0.47,
            delta_label=meta.get("payoff_delta_badge", "⚡ +48% GENERALIZATION GAIN")
        ).move_to([0, 0.15, 0])
        manifold = self.apply_layout_patch(manifold, "comparative_manifold", 5)

        
        self.play(manifold.animate_draw(run_time=min(2.5, b5_dur * 0.4)))
        self.wait(max(0.1, b5_dur - 3.8))
        
        # Clean up before outro
        self.play(FadeOut(manifold), run_time=0.6)

    # =========================================================================
    # DOMAIN 2: SPARSE AUTOENCODERS & MECHANISTIC INTERPRETABILITY
    # =========================================================================

    def play_neural_sae_choreography(self):
        """
        SAE Geometry choreography:
        Entangled Superposition -> Overcomplete Starburst Dictionary -> Monosemantic Sieve.
        """
        # BEAT 1: Coordinate Space & Entangled Vector
        b1_dur = self.get_beat_duration(1, 6.0)
        sae = SAEConstellation().move_to([0, 0.2, 0])
        sae = self.apply_layout_patch(sae, "sae_constellation", 1)
        self.display_math_formula(1, run_time=0.5)
        self.play(
            Create(sae.plane),
            GrowArrow(sae.entangled_vector),
            FadeIn(sae.vector_label),
            run_time=min(2.2, b1_dur * 0.45)
        )
        self.wait(max(0.1, b1_dur - 2.7))
        
        # BEAT 2: Polysemantic Bottleneck
        b2_dur = self.get_beat_duration(2, 7.5)
        self.display_math_formula(2, run_time=0.5)
        self.play(
            Wiggle(sae.entangled_vector),
            Circumscribe(sae.entangled_vector, color="#EF4444"),
            run_time=min(2.5, b2_dur * 0.45)
        )
        self.wait(max(0.1, b2_dur - 3.0))
        
        # BEAT 3: Starburst Overcomplete Dictionary Expansion
        b3_dur = self.get_beat_duration(3, 7.5)
        self.display_math_formula(3, run_time=0.5)
        self.play(
            LaggedStart(*[GrowArrow(a) for a in sae.dict_arrows], lag_ratio=0.08),
            FadeIn(sae.label_group),
            run_time=min(2.5, b3_dur * 0.45)
        )
        self.wait(max(0.1, b3_dur - 3.0))
        
        # BEAT 4: Sparsity Sieve & Feature Chips
        b4_dur = self.get_beat_duration(4, 7.5)
        self.display_math_formula(4, run_time=0.5)
        sae.trigger_sparsity_sieve(self, duration=min(2.5, b4_dur * 0.45))
        
        chip1 = FeatureProjectionChip(feature_id=1042, label="Syntax Latent", intensity=0.94, color="#34D399").move_to([-1.5, -2.4, 0])
        chip2 = FeatureProjectionChip(feature_id=8819, label="Code Latent", intensity=0.88, color="#38BDF8").move_to([1.5, -2.4, 0])
        chips = VGroup(chip1, chip2)
        chips = self.apply_layout_patch(chips, "feature_chips", 4)
        self.play(FadeIn(chips, shift=UP * 0.3), run_time=1.0)
        self.wait(max(0.1, b4_dur - 4.0))
        
        # BEAT 5: Payoff Metrics
        b5_dur = self.get_beat_duration(5, 7.5)
        self.display_math_formula(5, run_time=0.5)
        self.play(FadeOut(sae), FadeOut(chips), run_time=0.8)
        
        meta = self.storyboard.metadata
        dual_gauge = DualMetricGauge(
            model_a_name=meta.get("model_a", "Sparse SAE Latents"),
            model_a_score=meta.get("model_a_stat", "98.2%"),
            model_b_name=meta.get("model_b", "Dense Residual Baseline"),
            model_b_score=meta.get("model_b_stat", "41.5%"),
            delta_label=meta.get("payoff_delta_badge", "⚡ +56.7% SYNTACTIC RECOVERY")
        ).move_to([0, 0.4, 0])
        dual_gauge = self.apply_layout_patch(dual_gauge, "dual_metric_gauge", 5)

        
        self.play(FadeIn(dual_gauge, scale=0.9), run_time=1.0)
        self.play(dual_gauge.animate_count_up(run_time=min(2.5, b5_dur * 0.4)))
        self.wait(max(0.1, b5_dur - 4.3))
        self.play(FadeOut(dual_gauge), run_time=0.6)

    # =========================================================================
    # DOMAIN 3: MIXTURE OF EXPERTS (MoE) CHOREOGRAPHY
    # =========================================================================

    def play_neural_moe_choreography(self):
        """
        Sparse MoE routing choreography:
        Router Softmax Gating -> Top-k Laser Dispatch -> Load Balancing Manometers.
        """
        # BEAT 1: Constellation
        b1_dur = self.get_beat_duration(1, 6.0)
        moe = SparseMoELattice(num_experts=8).move_to([0, 0.4, 0])
        moe = self.apply_layout_patch(moe, "moe_lattice", 1)
        self.display_math_formula(1, run_time=0.5)
        self.play(
            Create(moe.expert_group),
            FadeIn(moe.router_group),
            FadeIn(moe.shared_group),
            run_time=min(2.0, b1_dur * 0.4)
        )
        self.wait(max(0.1, b1_dur - 2.5))
        
        # BEAT 2: Load Imbalance Crisis
        b2_dur = self.get_beat_duration(2, 7.5)
        self.display_math_formula(2, run_time=0.5)
        manometer = LoadBalancingManometer(num_experts=8).move_to([0, -2.6, 0])
        manometer = self.apply_layout_patch(manometer, "load_manometer", 2)
        self.play(FadeIn(manometer, shift=UP * 0.3), run_time=1.0)
        self.play(Indicate(manometer.bars, color="#EF4444"), run_time=1.5)
        self.wait(max(0.1, b2_dur - 3.0))
        
        # BEAT 3: Router Softmax Scan & Shared Core
        b3_dur = self.get_beat_duration(3, 7.5)
        self.display_math_formula(3, run_time=0.5)
        self.play(
            Indicate(moe.router_core, color="#00F0FF"),
            Circumscribe(moe.shared_core, color=COLOR_GOLD),
            run_time=min(2.5, b3_dur * 0.45)
        )
        self.wait(max(0.1, b3_dur - 3.0))
        
        # BEAT 4: Top-k Laser Dispatch & Packet Flow
        b4_dur = self.get_beat_duration(4, 7.5)
        self.display_math_formula(4, run_time=0.5)
        moe.dispatch_top_k(self, top_indices=[2, 5], duration=min(2.5, b4_dur * 0.45))
        self.wait(max(0.1, b4_dur - 3.0))
        
        # BEAT 5: Payoff Metrics
        b5_dur = self.get_beat_duration(5, 7.5)
        self.display_math_formula(5, run_time=0.5)
        self.play(FadeOut(moe), FadeOut(manometer), run_time=0.8)
        
        meta = self.storyboard.metadata
        dual_gauge = DualMetricGauge(
            model_a_name=meta.get("model_a", "Sparse MoE (DeepSeek)"),
            model_a_score=meta.get("model_a_stat", "10x"),
            model_b_name=meta.get("model_b", "Dense Transformer"),
            model_b_score=meta.get("model_b_stat", "1x"),
            delta_label=meta.get("efficiency_badge", "⚡ 94.5% COMPUTE REDUCTION")
        ).move_to([0, 0.4, 0])
        dual_gauge = self.apply_layout_patch(dual_gauge, "dual_metric_gauge", 5)
        self.play(FadeIn(dual_gauge, scale=0.9), run_time=1.0)
        self.play(dual_gauge.animate_count_up(run_time=min(2.5, b5_dur * 0.4)))
        self.wait(max(0.1, b5_dur - 4.3))
        self.play(FadeOut(dual_gauge), run_time=0.6)

    # =========================================================================
    # DOMAIN 4: TRANSFORMER ATTENTION & HARDWARE ACCELERATION
    # =========================================================================

    def play_neural_attention_choreography(self):
        """
        Attention mechanism choreography:
        Attention Heatmap Matrix -> Quadratic Bottleneck -> Orthogonal Ribbons.
        """
        b1_dur = self.get_beat_duration(1, 6.0)
        grid = TransformerAttentionGrid(grid_size=3.8).move_to([0, 0.4, 0])
        grid = self.apply_layout_patch(grid, "attention_grid", 1)
        self.display_math_formula(1, run_time=0.5)
        self.play(Create(grid), run_time=min(2.0, b1_dur * 0.4))
        self.wait(max(0.1, b1_dur - 2.5))
        
        b2_dur = self.get_beat_duration(2, 7.5)
        self.display_math_formula(2, run_time=0.5)
        self.play(grid.highlight_attention_cell(1, 2, color="#EF4444"), run_time=min(2.5, b2_dur * 0.45))
        self.wait(max(0.1, b2_dur - 3.0))
        
        b3_dur = self.get_beat_duration(3, 7.5)
        self.display_math_formula(3, run_time=0.5)
        self.play(
            *[grid.highlight_attention_cell(i, i, color="#00F0FF") for i in range(len(grid.tokens))],
            run_time=min(2.5, b3_dur * 0.45)
        )
        self.wait(max(0.1, b3_dur - 3.0))
        
        b4_dur = self.get_beat_duration(4, 7.5)
        self.display_math_formula(4, run_time=0.5)
        ribbon = RoutingRibbon(start_point=grid.cells[0][1].get_center(), end_point=grid.cells[2][3].get_center())
        ribbon = self.apply_layout_patch(ribbon, "routing_ribbon", 4)
        self.play(Create(ribbon), run_time=1.0)
        ribbon.animate_payload_transmission(self, duration=1.2)
        self.wait(max(0.1, b4_dur - 3.0))
        
        b5_dur = self.get_beat_duration(5, 7.5)
        self.display_math_formula(5, run_time=0.5)
        self.play(FadeOut(grid), FadeOut(ribbon), run_time=0.8)
        
        meta = self.storyboard.metadata
        dual_gauge = DualMetricGauge(
            model_a_name=meta.get("model_a", "FlashAttention-3"),
            model_a_score=meta.get("model_a_stat", "840 TFLOPs"),
            model_b_name=meta.get("model_b", "Standard PyTorch"),
            model_b_score=meta.get("model_b_stat", "310 TFLOPs"),
            delta_label=meta.get("payoff_delta_badge", "⚡ 2.7x HARDWARE EFFICIENCY")
        ).move_to([0, 0.4, 0])
        dual_gauge = self.apply_layout_patch(dual_gauge, "dual_metric_gauge", 5)
        self.play(FadeIn(dual_gauge, scale=0.9), run_time=1.0)
        self.play(dual_gauge.animate_count_up(run_time=min(2.5, b5_dur * 0.4)))
        self.wait(max(0.1, b5_dur - 4.3))
        self.play(FadeOut(dual_gauge), run_time=0.6)

    # =========================================================================
    # SPECIALIZED PEDAGOGICAL DEEP DIVE: HOW AN AI THINKS IN ONE SECOND
    # =========================================================================

    def play_ai_thinking_in_one_second_choreography(self):
        """
        Deep pedagogical 3Blue1Brown animation of how a transformer generates a token in 1000ms:
        Beat 1: Input Words Disintegrate into High-Dimensional Vector Space (R^d)
        Beat 2: Attention Mechanism Query-Key Dot Product & Quadratic Matrix Explosion
        Beat 3: FlashAttention SRAM Memory Tiling vs HBM Choke
        Beat 4: 80 Transformer Layers & SwiGLU Gating Activation
        Beat 5: Logit Probability Distribution & Discrete Token Sampling
        """
        # ---------------------------------------------------------------------
        # BEAT 1: WORDS DISINTEGRATE INTO VECTOR SPACE (t = 0 - 10ms)
        # ---------------------------------------------------------------------
        b1_dur = self.get_beat_duration(1, 8.56)
        self.display_math_formula(1, run_time=0.5)

        # 1. Floating Raw Text Prompt (Chalkboard style - NO rounded rectangle cards!)
        raw_words = ["Why", "is", "the", "sky", "blue", "?"]
        prompt_mobjects = VGroup()
        for w in raw_words:
            t = Text(w, font="Helvetica", font_size=24, color=WHITE, weight=BOLD)
            prompt_mobjects.add(t)
        prompt_mobjects.arrange(RIGHT, buff=0.18).move_to([0, 3.8, 0])

        # Token ID labels appearing below words
        token_ids = ["15234", "374", "279", "13180", "6437", "30"]
        id_labels = VGroup()
        for w_obj, tid in zip(prompt_mobjects, token_ids):
            lbl = Text(f"[{tid}]", font="Courier", font_size=10, color="#94A3B8").next_to(w_obj, DOWN, buff=0.1)
            id_labels.add(lbl)

        # 2. Embedding Space Manifold Axes R^12288
        axes = Axes(
            x_range=[-2.4, 2.4, 1], y_range=[-2.2, 2.2, 1],
            x_length=4.8, y_length=4.4,
            axis_config={"color": "#334155", "stroke_width": 1.2, "include_ticks": False}
        ).move_to([0, 0.1, 0])
        axes_label = Text("EMBEDDING MANIFOLD: ℝ¹²²⁸⁸", font="Courier", font_size=11, color="#64748B", weight=BOLD).next_to(axes, UP, buff=0.12)

        # 3. High-Dimensional Vector Projections
        origin = axes.c2p(0, 0)
        v_sky = Arrow(origin, axes.c2p(1.7, 1.3), color="#38BDF8", buff=0, stroke_width=3.5, max_tip_length_to_length_ratio=0.15)
        lbl_sky = Text("v_sky", font="Courier", font_size=12, color="#38BDF8", weight=BOLD).next_to(v_sky.get_end(), UR, buff=0.08)

        v_blue = Arrow(origin, axes.c2p(1.8, -1.0), color="#60A5FA", buff=0, stroke_width=3.5, max_tip_length_to_length_ratio=0.15)
        lbl_blue = Text("v_blue", font="Courier", font_size=12, color="#60A5FA", weight=BOLD).next_to(v_blue.get_end(), DR, buff=0.08)

        v_why = Arrow(origin, axes.c2p(-1.6, 1.2), color="#F59E0B", buff=0, stroke_width=3.5, max_tip_length_to_length_ratio=0.15)
        lbl_why = Text("v_why", font="Courier", font_size=12, color="#F59E0B", weight=BOLD).next_to(v_why.get_end(), UL, buff=0.08)

        # Numerical coordinate vector bracket annotation
        coord_preview = Text("v_sky = [+0.42, -0.81, +0.19, ..., +0.07] ∈ ℝ¹²²⁸⁸", font="Courier", font_size=10, color="#94A3B8").next_to(axes, DOWN, buff=0.15)

        vector_group = VGroup(axes, axes_label, v_sky, lbl_sky, v_blue, lbl_blue, v_why, lbl_why, coord_preview)
        vector_group = self.apply_layout_patch(vector_group, "vector_group", 1)

        self.play(FadeIn(prompt_mobjects, shift=DOWN * 0.2), run_time=0.8)
        self.play(FadeIn(id_labels, shift=UP * 0.1), run_time=0.6)
        self.play(
            prompt_mobjects.animate.scale(0.75).move_to([0, 4.4, 0]),
            id_labels.animate.scale(0.75).move_to([0, 4.05, 0]),
            Create(axes), FadeIn(axes_label),
            GrowArrow(v_sky), FadeIn(lbl_sky),
            GrowArrow(v_blue), FadeIn(lbl_blue),
            GrowArrow(v_why), FadeIn(lbl_why),
            FadeIn(coord_preview),
            run_time=2.0
        )
        self.wait(max(0.1, b1_dur - 3.9))

        # ---------------------------------------------------------------------
        # BEAT 2: ATTENTION DOT PRODUCT & QUADRATIC EXPLOSION (t = 50ms)
        # ---------------------------------------------------------------------
        b2_dur = self.get_beat_duration(2, 10.0)
        self.display_math_formula(2, run_time=0.5)

        self.play(
            FadeOut(prompt_mobjects), FadeOut(id_labels), FadeOut(vector_group),
            run_time=0.4
        )

        # 1. Query-Key Vector Dot Product Angle Geometry (Upper Half: Y = 2.0)
        center_pt = np.array([0, 2.0, 0])
        q_vec = Arrow(center_pt, center_pt + np.array([2.0, 1.1, 0]), color="#38BDF8", buff=0, stroke_width=3.8)
        q_lbl = Text("Query: q_sky", font="Helvetica", font_size=12, color="#38BDF8", weight=BOLD).next_to(q_vec.get_end(), UR, buff=0.08)

        k_vec = Arrow(center_pt, center_pt + np.array([2.3, -0.2, 0]), color="#F59E0B", buff=0, stroke_width=3.8)
        k_lbl = Text("Key: k_blue", font="Helvetica", font_size=12, color="#F59E0B", weight=BOLD).next_to(k_vec.get_end(), DR, buff=0.08)

        angle_arc = Arc(
            radius=0.70, start_angle=k_vec.get_angle(), angle=q_vec.get_angle() - k_vec.get_angle(),
            arc_center=center_pt, color="#34D399", stroke_width=2.4
        )
        theta_lbl = Text("θ", font="Helvetica", font_size=11, color="#34D399").next_to(angle_arc, RIGHT, buff=0.08)

        proj_pt = center_pt + np.array([1.6, -0.14, 0])
        proj_line = DashedLine(q_vec.get_end(), proj_pt, color="#94A3B8", stroke_width=1.5)

        dot_formula = Text("q · k = |q||k| cos(θ) = 0.89  [STRONG AFFINITY]", font="Courier", font_size=11, color="#34D399", weight=BOLD).move_to([0, 0.7, 0])

        # 2. Pairwise Quadratic Dot Product Matrix O(N^2) (Lower Half: Y = -1.7)
        grid_title = Text("ALL-TO-ALL ATTENTION GRAPH: O(N²)", font="Helvetica", font_size=11, color="#EF4444", weight=BOLD).move_to([0, 0.1, 0])
        
        # 5 token nodes in a pentagonal constellation centered at Y = -1.7
        token_names = ["Why", "is", "the", "sky", "blue"]
        node_radius = 1.15
        node_group = VGroup()
        node_centers = []
        for i, name in enumerate(token_names):
            ang = PI / 2 + i * (2 * PI / 5)
            pos = np.array([node_radius * np.cos(ang), -1.7 + node_radius * np.sin(ang), 0])
            node_centers.append(pos)
            dot = Dot(point=pos, radius=0.08, color="#38BDF8")
            lbl = Text(name, font="Helvetica", font_size=9, color=WHITE).next_to(dot, UP if np.sin(ang) >= 0 else DOWN, buff=0.06)
            node_group.add(VGroup(dot, lbl))

        # Fully connected O(N^2) directed laser lines
        laser_lines = VGroup()
        for i in range(len(node_centers)):
            for j in range(len(node_centers)):
                if i != j:
                    line = Line(
                        node_centers[i], node_centers[j],
                        stroke_width=1.0, color="#EF4444", stroke_opacity=0.35
                    )
                    laser_lines.add(line)

        matrix_group = VGroup(grid_title, laser_lines, node_group)
        attn_group = VGroup(q_vec, q_lbl, k_vec, k_lbl, angle_arc, theta_lbl, proj_line, dot_formula, matrix_group)
        attn_group = self.apply_layout_patch(attn_group, "attention_group", 2)

        self.play(
            GrowArrow(q_vec), FadeIn(q_lbl),
            GrowArrow(k_vec), FadeIn(k_lbl),
            Create(angle_arc), FadeIn(theta_lbl),
            run_time=1.4
        )
        self.play(Create(proj_line), FadeIn(dot_formula), run_time=0.8)
        self.play(FadeIn(grid_title), Create(node_group), Create(laser_lines), run_time=1.2)
        self.wait(max(0.1, b2_dur - 4.3))

        # ---------------------------------------------------------------------
        # BEAT 3: FLASHATTENTION SRAM HARDWARE TILING (t = 200ms)
        # ---------------------------------------------------------------------
        b3_dur = self.get_beat_duration(3, 10.41)
        self.display_math_formula(3, run_time=0.5)

        self.play(FadeOut(attn_group), run_time=0.4)

        # GPU Memory Hierarchy Chalkboard Schematic (No cards!)
        # 1. On-Chip Fast SRAM Cache (Top: Y = 2.4)
        sram_line = Line([-3.4, 2.4, 0], [3.4, 2.4, 0], color="#38BDF8", stroke_width=2.0)
        sram_title = Text("ON-CHIP SRAM CACHE (19.2 TB/s BANDWIDTH)", font="Helvetica", font_size=11, color="#38BDF8", weight=BOLD).next_to(sram_line, UP, buff=0.10)
        
        # Fast SRAM register blocks
        sram_registers = VGroup()
        for idx in range(3):
            reg = Rectangle(width=1.5, height=0.55, stroke_color="#34D399", stroke_width=1.5, fill_color="#064E3B", fill_opacity=0.6)
            reg_lbl = Text(f"Tile {idx+1}: Q_i · K_jᵀ", font="Courier", font_size=9, color="#34D399", weight=BOLD).move_to(reg)
            sram_registers.add(VGroup(reg, reg_lbl))
        sram_registers.arrange(RIGHT, buff=0.25).move_to([0, 1.7, 0])
        sram_group = VGroup(sram_line, sram_title, sram_registers)

        # 2. Central FlashAttention Status Label (Y = 0.0)
        flash_badge = Text("FLASHATTENTION: Fused Tiling Prevents HBM Round-Trips", font="Courier", font_size=10, color="#34D399", weight=BOLD).move_to([0, 0.0, 0])

        # 3. Off-Chip Slow HBM Memory (Bottom: Y = -1.7)
        hbm_line = Line([-3.4, -1.7, 0], [3.4, -1.7, 0], color="#64748B", stroke_width=1.5)
        hbm_title = Text("OFF-CHIP HBM3 MEMORY (3.35 TB/s - MEMORY BOTTLENECK)", font="Helvetica", font_size=10, color="#94A3B8", weight=BOLD).next_to(hbm_line, DOWN, buff=0.08)

        # KV-cache tape blocks in HBM
        kv_tape = VGroup()
        for idx in range(5):
            cell = Rectangle(width=1.0, height=0.50, stroke_color="#475569", stroke_width=1.0, fill_color="#1E293B", fill_opacity=0.7)
            cell_lbl = Text(f"KV_{idx}", font="Courier", font_size=9, color="#94A3B8").move_to(cell)
            kv_tape.add(VGroup(cell, cell_lbl))
        kv_tape.arrange(RIGHT, buff=0.12).move_to([0, -2.6, 0])
        hbm_group = VGroup(hbm_line, hbm_title, kv_tape)

        # 4. Flanking Non-Colliding Curved Dataflow Streaming Arrows
        flow_arrow_left = CurvedArrow(kv_tape[0].get_top(), sram_registers[0].get_bottom(), angle=TAU/8, color="#34D399", stroke_width=2.5)
        flow_arrow_right = CurvedArrow(kv_tape[4].get_top(), sram_registers[2].get_bottom(), angle=-TAU/8, color="#34D399", stroke_width=2.5)

        flash_group = VGroup(sram_group, hbm_group, flow_arrow_left, flow_arrow_right, flash_badge)
        flash_group = self.apply_layout_patch(flash_group, "flash_group", 3)

        self.play(FadeIn(sram_group), FadeIn(hbm_group), run_time=1.2)
        self.play(
            Create(flow_arrow_left), Create(flow_arrow_right),
            FadeIn(flash_badge),
            Indicate(sram_registers, color="#34D399"),
            run_time=1.5
        )
        self.wait(max(0.1, b3_dur - 3.6))

        # ---------------------------------------------------------------------
        # BEAT 4: 80 TRANSFORMER LAYERS & SwiGLU GATING (t = 500ms)
        # ---------------------------------------------------------------------
        b4_dur = self.get_beat_duration(4, 10.48)
        self.display_math_formula(4, run_time=0.5)

        self.play(FadeOut(flash_group), run_time=0.4)

        # 1. Residual Stream Highway (Left Column: X = -2.4)
        residual_line = Line([-2.4, -3.2, 0], [-2.4, 3.2, 0], color="#38BDF8", stroke_width=3.5)
        res_label = Text("RESIDUAL STREAM", font="Courier", font_size=9, color="#38BDF8", weight=BOLD).next_to(residual_line, UP, buff=0.1)
        
        layer_ticks = VGroup()
        for ly_name, y_coord in [("Layer 1", -2.4), ("Layer 2", -1.5), ("Layer ...", -0.6), ("Layer 40", 0.3), ("Layer ...", 1.2), ("Layer 80", 2.1)]:
            dot = Dot(point=[-2.4, y_coord, 0], radius=0.08, color="#38BDF8")
            lbl = Text(ly_name, font="Courier", font_size=9, color="#94A3B8").next_to(dot, LEFT, buff=0.1)
            layer_ticks.add(VGroup(dot, lbl))

        # 2. Geometric SwiGLU Gating Bifurcation (Right Side: X = 0.5)
        swiglu_header = Text("SwiGLU GATING UNIT", font="Helvetica", font_size=12, color="#F59E0B", weight=BOLD).move_to([0.8, 2.5, 0])
        
        # Branch bifurcation curves from x input
        input_pt = np.array([-1.2, 0.0, 0])
        input_dot = Dot(point=input_pt, radius=0.09, color=WHITE)
        input_lbl = Text("x", font="Helvetica", font_size=13, color=WHITE, weight=BOLD).next_to(input_dot, LEFT, buff=0.08)

        # Left branch: Linear projection W_up
        linear_curve = CubicBezier(
            input_pt, input_pt + np.array([0.5, 0.9, 0]),
            np.array([1.0, 0.9, 0]), np.array([1.5, 0.3, 0]),
            color="#38BDF8", stroke_width=2.5
        )
        linear_lbl = Text("W_up · x", font="Courier", font_size=10, color="#38BDF8").move_to([0.6, 1.25, 0])

        # Right branch: Swish activation Gate σ(W_gate)
        gate_curve = CubicBezier(
            input_pt, input_pt + np.array([0.5, -0.9, 0]),
            np.array([1.0, -0.9, 0]), np.array([1.5, -0.3, 0]),
            color="#34D399", stroke_width=2.5
        )
        gate_lbl = Text("σ(W_gate · x)", font="Courier", font_size=10, color="#34D399").move_to([0.6, -1.25, 0])

        # Elementwise multiplication symbol ⊗ positioned safely at X = 1.5
        mult_circle = Circle(radius=0.32, color="#F59E0B", stroke_width=2.0).move_to([1.5, 0.0, 0])
        mult_symbol = Text("⊗", font="Helvetica", font_size=18, color="#F59E0B", weight=BOLD).move_to(mult_circle)
        mult_lbl = Text("W_down · (Linear ⊗ Gate)", font="Courier", font_size=9, color="#F59E0B", weight=BOLD).next_to(mult_circle, UP, buff=0.18)

        # Re-injection arrow back into residual highway
        return_arrow = CurvedArrow(mult_circle.get_left() + LEFT * 0.1, np.array([-2.3, 1.2, 0]), angle=-TAU/5, color="#F59E0B", stroke_width=2.2)

        # Energy pulse travelling up residual line
        pulse = Dot(point=[-2.4, -3.2, 0], radius=0.16, color="#00F0FF")

        layers_group = VGroup(
            residual_line, res_label, layer_ticks, swiglu_header,
            input_dot, input_lbl, linear_curve, linear_lbl, gate_curve, gate_lbl,
            mult_circle, mult_symbol, mult_lbl, return_arrow, pulse
        )
        layers_group = self.apply_layout_patch(layers_group, "layers_group", 4)

        self.play(
            Create(residual_line), FadeIn(res_label), FadeIn(layer_ticks),
            FadeIn(swiglu_header), FadeIn(input_dot), FadeIn(input_lbl),
            Create(linear_curve), FadeIn(linear_lbl),
            Create(gate_curve), FadeIn(gate_lbl),
            Create(mult_circle), FadeIn(mult_symbol), FadeIn(mult_lbl),
            Create(return_arrow),
            run_time=1.6
        )
        self.play(pulse.animate.move_to([-2.4, 0.0, 0]), run_time=0.8)
        self.play(Indicate(mult_circle, color="#F59E0B"), run_time=0.8)
        self.play(pulse.animate.move_to([-2.4, 3.2, 0]), run_time=0.8)
        self.wait(max(0.1, b4_dur - 4.9))

        # ---------------------------------------------------------------------
        # BEAT 5: VOCABULARY LOGIT COLLAPSE & TOKEN SAMPLING (t = 900 - 1000ms)
        # ---------------------------------------------------------------------
        b5_dur = self.get_beat_duration(5, 9.58)
        self.display_math_formula(5, run_time=0.5)

        self.play(FadeOut(layers_group), run_time=0.4)

        # 1. 3Blue1Brown Softmax Probability Distribution & Sampling
        prob_title = Text("VOCABULARY LOGIT DISTRIBUTION: P(w | x)", font="Helvetica", font_size=11, color="#38BDF8", weight=BOLD).move_to([0, 2.5, 0])

        candidates = [
            ("Rayleigh", 0.68, "#34D399", True),
            ("scattering", 0.18, "#60A5FA", False),
            ("particles", 0.08, "#64748B", False),
            ("wavelength", 0.04, "#475569", False),
            ("other (128k)", 0.02, "#334155", False)
        ]

        bars = VGroup()
        for idx, (word, prob, bar_color, is_winner) in enumerate(candidates):
            y_pos = 1.4 - idx * 0.65
            w_label = Text(f'"{word}"', font="Helvetica", font_size=12, color=WHITE if is_winner else "#94A3B8", weight=BOLD if is_winner else NORMAL).move_to([-1.8, y_pos, 0])
            bar_width = prob * 3.8
            bar = Rectangle(
                width=max(0.08, bar_width), height=0.32, stroke_width=1.0,
                stroke_color=bar_color, fill_color=bar_color, fill_opacity=0.9 if is_winner else 0.5
            )
            bar.next_to(w_label, RIGHT, buff=0.22)
            prob_lbl = Text(f"{int(prob*100)}%", font="Courier", font_size=11, color=bar_color, weight=BOLD).next_to(bar, RIGHT, buff=0.14)
            bars.add(VGroup(w_label, bar, prob_lbl))

        # Dynamic sampling laser cursor pointing down to Rayleigh bar
        cursor_arrow = Arrow([0.8, 2.1, 0], [0.8, 1.58, 0], color="#F59E0B", stroke_width=3.0, buff=0, max_tip_length_to_length_ratio=0.25)
        cursor_tag = Text("ARGMAX SAMPLING (T = 0.7)", font="Courier", font_size=9, color="#F59E0B", weight=BOLD).next_to(cursor_arrow, UP, buff=0.08)
        cursor_group = VGroup(cursor_arrow, cursor_tag)

        # Sampled Token Result Floating Prominently
        token_emitted = Text('"Rayleigh"', font="Helvetica", font_size=28, color="#34D399", weight=BOLD).move_to([0, -2.1, 0])
        token_time = Text("[t = 980ms // NEXT TOKEN GENERATED]", font="Courier", font_size=11, color="#F59E0B", weight=BOLD).next_to(token_emitted, DOWN, buff=0.15)
        token_result = VGroup(token_emitted, token_time)

        sampling_group = VGroup(prob_title, bars, cursor_group, token_result)
        sampling_group = self.apply_layout_patch(sampling_group, "sampling_group", 5)

        self.play(FadeIn(prob_title), FadeIn(bars), run_time=1.2)
        self.play(GrowArrow(cursor_arrow), FadeIn(cursor_tag), run_time=0.8)
        self.play(
            Indicate(bars[0], color="#34D399", scale_factor=1.06),
            FadeIn(token_emitted, scale=1.2),
            FadeIn(token_time, shift=UP * 0.1),
            run_time=1.2
        )
        self.wait(max(0.1, b5_dur - 4.6))
        self.play(FadeOut(sampling_group), run_time=0.5)

    # =========================================================================
    # DOMAIN: DIFFUSION & GENERATIVE NOISE REMOVAL CHOREOGRAPHY
    # =========================================================================

    def play_diffusion_static_choreography(self):
        """
        Pure 3Blue1Brown educational chalkboard choreography for Diffusion models:
        Beat 1: The TV Static Canvas (Pure 100% Noise Cloud)
        Beat 2: Seeing Shapes in Clouds (Pareidolia: Faint Golden Constellation)
        Beat 3: The Foggy Mirror Training (3-Stage Forward Process t=0 -> 1000)
        Beat 4: The Sculptor's Chisel (Sweeping Laser Subtracting Red Noise Dust)
        Beat 5: Art Out of Chaos (Progress Meter + Glowing Multi-Color Masterpiece)
        """
        rng = np.random.RandomState(42)

        # ---------------------------------------------------------------------
        # BEAT 1: The TV Static Canvas (Pure Random Chaos)
        # ---------------------------------------------------------------------
        b1_dur = self.get_beat_duration(1, 7.6)
        self.display_math_formula(1, run_time=0.5)

        # Main Canvas Frame
        canvas_frame = RoundedRectangle(
            width=5.8, height=5.4, corner_radius=0.18,
            color="#38BDF8", stroke_width=1.8, stroke_opacity=0.85
        ).move_to([0, 0.7, 0])

        b1_title = Text("STEP 0: THE STATIC CANVAS", font_size=13, font="Helvetica", color="#38BDF8", weight=BOLD).move_to([0, 3.1, 0])
        b1_sub = Text("[100% MAXIMUM GAUSSIAN NOISE]", font_size=10, font="Courier", color="#94A3B8").next_to(b1_title, DOWN, buff=0.12)

        # Crossout badge showing "No Database / No Copy-Paste"
        no_lib_box = RoundedRectangle(width=3.6, height=0.55, corner_radius=0.1, color="#EF4444", stroke_width=1.4).move_to([0, -1.5, 0])
        no_lib_txt = Text("NOT A DATABASE SEARCH", font_size=10, font="Courier", color="#EF4444", weight=BOLD).move_to(no_lib_box.get_center())
        no_lib_group = VGroup(no_lib_box, no_lib_txt)

        # Generate 100 random noise dots inside canvas frame
        noise_dots = VGroup()
        dot_colors = ["#475569", "#64748B", "#94A3B8", "#38BDF8", "#E2E8F0"]
        for _ in range(110):
            rx = rng.uniform(-2.5, 2.5)
            ry = rng.uniform(-1.8, 2.4)
            c = rng.choice(dot_colors)
            noise_dots.add(Dot(point=[rx, ry, 0], radius=rng.uniform(0.03, 0.06), color=c, fill_opacity=rng.uniform(0.5, 0.95)))

        self.play(Create(canvas_frame), FadeIn(b1_title), FadeIn(b1_sub), run_time=0.9)
        self.play(FadeIn(noise_dots, lag_ratio=0.01), FadeIn(no_lib_group, shift=UP * 0.1), run_time=1.3)
        # Jitter the static slightly to convey TV snow
        jittered_dots = noise_dots.copy()
        for d in jittered_dots:
            d.shift([rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06), 0])
        self.play(Transform(noise_dots, jittered_dots), run_time=1.0)

        # Wait remaining beat budget
        anim_time = 0.9 + 1.3 + 1.0  # 3.2s
        self.wait(max(0.1, b1_dur - anim_time))
        self.play(FadeOut(no_lib_group), run_time=0.3)

        # ---------------------------------------------------------------------
        # BEAT 2: Seeing Shapes in Clouds (Pareidolia)
        # ---------------------------------------------------------------------
        b2_dur = self.get_beat_duration(2, 7.55)
        self.display_math_formula(2, run_time=0.5)

        b2_title = Text("PAREIDOLIA: SHAPES IN THE NOISE", font_size=13, font="Helvetica", color="#F59E0B", weight=BOLD).move_to([0, 3.1, 0])
        b2_sub = Text("[DETECTING FAINT LATENT CONTOURS]", font_size=10, font="Courier", color="#F59E0B").next_to(b2_title, DOWN, buff=0.12)

        # Geometric origami cat/rabbit silhouette in gold dashed lines
        pts = [
            [-0.7, -0.7, 0], [0.7, -0.7, 0], [1.1, 0.3, 0], [0.65, 1.7, 0],
            [0.2, 0.7, 0], [-0.2, 0.7, 0], [-0.65, 1.7, 0], [-1.1, 0.3, 0]
        ]
        constellation_lines = VGroup()
        for i in range(len(pts)):
            p_start = np.array(pts[i]) + np.array([0, 0.2, 0])
            p_end = np.array(pts[(i + 1) % len(pts)]) + np.array([0, 0.2, 0])
            constellation_lines.add(DashedLine(p_start, p_end, color="#F59E0B", stroke_width=2.4, dash_length=0.12))

        cross1 = DashedLine(pts[0] + np.array([0, 0.2, 0]), pts[4] + np.array([0, 0.2, 0]), color="#F59E0B", stroke_width=1.5, stroke_opacity=0.6)
        cross2 = DashedLine(pts[1] + np.array([0, 0.2, 0]), pts[5] + np.array([0, 0.2, 0]), color="#F59E0B", stroke_width=1.5, stroke_opacity=0.6)
        constellation_group = VGroup(constellation_lines, cross1, cross2)

        # Radar scanner pulse
        radar = Circle(radius=0.25, color="#F59E0B", stroke_width=1.8).move_to([0, 0.6, 0])

        self.play(
            Transform(b1_title, b2_title),
            Transform(b1_sub, b2_sub),
            canvas_frame.animate.set_color("#F59E0B"),
            run_time=0.6
        )
        self.play(Create(constellation_group), run_time=1.5)
        self.play(radar.animate.scale(5.5).set_opacity(0), run_time=1.4)

        anim_time = 0.6 + 1.5 + 1.4  # 3.5s
        self.wait(max(0.1, b2_dur - anim_time))

        # ---------------------------------------------------------------------
        # BEAT 3: The Foggy Mirror Training (Forward Process)
        # ---------------------------------------------------------------------
        b3_dur = self.get_beat_duration(3, 7.6)
        self.display_math_formula(3, run_time=0.5)

        # Clear canvas to show 3-stage mirror fogging progression
        self.play(
            FadeOut(noise_dots), FadeOut(constellation_group),
            FadeOut(canvas_frame), FadeOut(b1_title), FadeOut(b1_sub),
            run_time=0.5
        )

        b3_title = Text("THE FOGGY MIRROR (FORWARD DIFFUSION)", font_size=12, font="Helvetica", color="#38BDF8", weight=BOLD).move_to([0, 3.8, 0])
        b3_sub = Text("Adding noise step-by-step until reflection vanishes", font_size=10, font="Courier", color="#94A3B8").next_to(b3_title, DOWN, buff=0.10)

        # 3 stage boxes: Left (Clean), Center (Foggy), Right (100% Noise)
        stages = VGroup()
        centers = [-2.1, 0.0, 2.1]
        titles = ["STAGE 1\nCLEAR ART", "STAGE 2\nSTEAM FOG", "STAGE 3\nPURE NOISE"]
        colors = ["#10B981", "#F59E0B", "#64748B"]

        for cx, stitle, scolor in zip(centers, titles, colors):
            box = RoundedRectangle(width=1.75, height=3.0, corner_radius=0.12, color=scolor, stroke_width=1.6).move_to([cx, 0.8, 0])
            lbl = Text(stitle, font_size=9, font="Helvetica", color=scolor, weight=BOLD, line_spacing=0.9).move_to([cx, 2.0, 0])
            stages.add(VGroup(box, lbl))

        # Stage 1: clean diamond contour
        c_shape = Polygon([-2.1, 0.3, 0], [-1.6, 0.8, 0], [-2.1, 1.3, 0], [-2.6, 0.8, 0], color="#10B981", stroke_width=2.5, fill_opacity=0.25)
        
        # Stage 2: half-corrupted shape + 25 dots
        foggy_dots = VGroup()
        for _ in range(25):
            foggy_dots.add(Dot(point=[rng.uniform(-0.6, 0.6), rng.uniform(0.2, 1.4), 0], radius=0.035, color="#F59E0B", fill_opacity=0.7))
        foggy_shape = DashedVMobject(Polygon([0.0, 0.3, 0], [0.5, 0.8, 0], [0.0, 1.3, 0], [-0.5, 0.8, 0], color="#F59E0B", stroke_width=2.0), num_dashes=12)

        # Stage 3: pure 45 noise dots
        noise_stage_dots = VGroup()
        for _ in range(45):
            noise_stage_dots.add(Dot(point=[rng.uniform(1.4, 2.8), rng.uniform(0.2, 1.4), 0], radius=0.04, color="#64748B", fill_opacity=0.85))

        # Connecting curved conduits (Use Create for CurvedArrow)
        arr1 = CurvedArrow(np.array([-1.2, 0.8, 0]), np.array([-0.9, 0.8, 0]), angle=-PI / 4, color="#38BDF8", stroke_width=1.8)
        arr2 = CurvedArrow(np.array([0.9, 0.8, 0]), np.array([1.2, 0.8, 0]), angle=-PI / 4, color="#38BDF8", stroke_width=1.8)
        fog_lbl = Text("+ STEAM NOISE (t = 0 -> 1000)", font_size=9, font="Courier", color="#38BDF8").move_to([0, -1.0, 0])

        self.play(FadeIn(b3_title), FadeIn(b3_sub), Create(stages), run_time=1.0)
        self.play(
            Create(c_shape),
            Create(foggy_shape), FadeIn(foggy_dots),
            FadeIn(noise_stage_dots),
            Create(arr1), Create(arr2), FadeIn(fog_lbl),
            run_time=1.6
        )

        anim_time = 0.5 + 1.0 + 1.6  # 3.1s
        self.wait(max(0.1, b3_dur - anim_time))

        # ---------------------------------------------------------------------
        # BEAT 4: The Sculptor's Chisel (Subtracting Noise Dust)
        # ---------------------------------------------------------------------
        b4_dur = self.get_beat_duration(4, 7.15)
        self.display_math_formula(4, run_time=0.5)

        # Clear stage boxes
        self.play(
            FadeOut(stages), FadeOut(c_shape), FadeOut(foggy_shape),
            FadeOut(foggy_dots), FadeOut(noise_stage_dots),
            FadeOut(arr1), FadeOut(arr2), FadeOut(fog_lbl),
            FadeOut(b3_title), FadeOut(b3_sub),
            run_time=0.5
        )

        # Back to hero canvas
        chisel_frame = RoundedRectangle(
            width=5.8, height=5.4, corner_radius=0.18,
            color="#34D399", stroke_width=1.8
        ).move_to([0, 0.7, 0])

        b4_title = Text("THE SCULPTOR'S CHISEL: DENOISING", font_size=13, font="Helvetica", color="#34D399", weight=BOLD).move_to([0, 3.1, 0])
        b4_sub = Text("[PREDICTING & CHIPPING NOISE DUST]", font_size=10, font="Courier", color="#34D399").next_to(b4_title, DOWN, buff=0.12)

        # 60 red noise dust particles to subtract
        noise_dust = VGroup()
        for _ in range(60):
            noise_dust.add(Dot(
                point=[rng.uniform(-2.3, 2.3), rng.uniform(-1.5, 2.2), 0],
                radius=rng.uniform(0.04, 0.07), color="#EF4444", fill_opacity=0.85
            ))

        # The crisp underlying contour to reveal
        chiseled_contour = VGroup()
        for i in range(len(pts)):
            p_start = np.array(pts[i]) + np.array([0, 0.2, 0])
            p_end = np.array(pts[(i + 1) % len(pts)]) + np.array([0, 0.2, 0])
            chiseled_contour.add(Line(p_start, p_end, color="#34D399", stroke_width=3.2))

        # Cyan sweeping chisel laser
        wiper_bar = Line(np.array([-2.6, 2.3, 0]), np.array([2.6, 2.3, 0]), color="#00F0FF", stroke_width=3.5)
        wiper_lbl = Text("SWEEPING DENOISER (-eps_theta)", font_size=9, font="Courier", color="#00F0FF", weight=BOLD).next_to(wiper_bar, UP, buff=0.08)
        wiper_group = VGroup(wiper_bar, wiper_lbl)

        self.play(Create(chisel_frame), FadeIn(b4_title), FadeIn(b4_sub), FadeIn(noise_dust), run_time=0.9)
        self.play(FadeIn(wiper_group), run_time=0.4)

        # Laser sweeps down, dust vanishes, clean emerald lines appear!
        self.play(
            wiper_group.animate.shift(DOWN * 3.8),
            FadeOut(noise_dust, lag_ratio=0.02),
            Create(chiseled_contour),
            run_time=2.0
        )
        self.play(FadeOut(wiper_group), run_time=0.3)

        anim_time = 0.5 + 0.9 + 0.4 + 2.0 + 0.3  # 4.1s
        self.wait(max(0.1, b4_dur - anim_time))

        # ---------------------------------------------------------------------
        # BEAT 5: Art Out of Chaos (50 Steps Complete)
        # ---------------------------------------------------------------------
        b5_dur = self.get_beat_duration(5, 7.55)
        self.display_math_formula(5, run_time=0.5)

        b5_title = Text("ART CARVED OUT OF CHAOS", font_size=13, font="Helvetica", color="#34D399", weight=BOLD).move_to([0, 3.1, 0])
        b5_sub = Text("[50 REVERSE STEPS COMPLETED IN 2.0s]", font_size=10, font="Courier", color="#F59E0B").next_to(b5_title, DOWN, buff=0.12)

        # Denoising Progress Slider
        slider_bg = RoundedRectangle(width=4.6, height=0.22, corner_radius=0.08, color="#334155", stroke_width=1.0, fill_color="#1E293B", fill_opacity=0.8).move_to([0, -1.5, 0])
        slider_fill = RoundedRectangle(width=4.6, height=0.22, corner_radius=0.08, color="#34D399", fill_color="#34D399", fill_opacity=1.0).move_to([0, -1.5, 0])
        slider_txt = Text("DENOISING: 100% -> 0% NOISE [100% ARTWORK]", font_size=9, font="Courier", color="#34D399", weight=BOLD).next_to(slider_bg, DOWN, buff=0.12)

        # Halo around finished masterpiece
        halo = Circle(radius=1.85, color="#34D399", stroke_width=1.8, stroke_opacity=0.8, fill_opacity=0.06).move_to([0, 0.6, 0])
        sparkles = VGroup()
        for angle in [0.2, 0.7, 1.2, 1.7, 2.3, 2.8, 3.5, 4.2, 5.0, 5.8]:
            sp_pos = halo.point_at_angle(angle)
            sparkles.add(Dot(point=sp_pos, radius=0.05, color="#F59E0B"))

        self.play(
            Transform(b4_title, b5_title),
            Transform(b4_sub, b5_sub),
            FadeIn(slider_bg),
            Create(slider_fill),
            FadeIn(slider_txt),
            run_time=0.8
        )
        self.play(
            Indicate(chiseled_contour, color="#F59E0B", scale_factor=1.08),
            Create(halo),
            FadeIn(sparkles, lag_ratio=0.05),
            run_time=1.6
        )

        anim_time = 0.8 + 1.6  # 2.4s
        self.wait(max(0.1, b5_dur - anim_time))

        # Fade out before Beat 6 brand outro
        self.play(
            FadeOut(chisel_frame), FadeOut(b4_title), FadeOut(b4_sub),
            FadeOut(slider_bg), FadeOut(slider_fill), FadeOut(slider_txt),
            FadeOut(chiseled_contour), FadeOut(halo), FadeOut(sparkles),
            run_time=0.5
        )

    # =========================================================================
    # DOMAIN 5: ALGORITHMIC SEARCH & GRAPH TREES
    # =========================================================================

    def play_algorithmic_search_choreography(self):
        """
        Search tree choreography:
        MCTS Frontier Expansion -> Combinatorial Explosion -> Branch-and-Bound Laser Slice.
        """
        b1_dur = self.get_beat_duration(1, 6.0)
        tree = DynamicSearchTree().move_to([0, 1.2, 0])
        self.display_math_formula(1, run_time=0.5)
        self.play(Create(tree.edges), Create(tree.node_group), run_time=1.5)
        self.wait(max(0.1, b1_dur - 2.0))
        
        b2_dur = self.get_beat_duration(2, 7.5)
        self.display_math_formula(2, run_time=0.5)
        self.play(Wiggle(tree.node_group), run_time=min(2.5, b2_dur * 0.45))
        self.wait(max(0.1, b2_dur - 3.0))
        
        b3_dur = self.get_beat_duration(3, 7.5)
        self.display_math_formula(3, run_time=0.5)
        tree.animate_mcts_cycle(self, selected_path=("s0", "s1_win", "s11"), duration=min(2.8, b3_dur * 0.5))
        self.wait(max(0.1, b3_dur - 3.3))
        
        b4_dur = self.get_beat_duration(4, 7.5)
        self.display_math_formula(4, run_time=0.5)
        laser = BranchAndBoundLaser(incumbent_value=4.2).move_to([0, -0.8, 0])
        self.play(FadeIn(laser), run_time=0.8)
        self.wait(max(0.1, b4_dur - 2.0))
        
        b5_dur = self.get_beat_duration(5, 7.5)
        self.display_math_formula(5, run_time=0.5)
        self.play(FadeOut(tree), FadeOut(laser), run_time=0.8)
        
        dual_gauge = DualMetricGauge(
            model_a_name="Pruned MCTS Search",
            model_a_score="99.4%",
            model_b_name="Brute Force A*",
            model_b_score="34.1%",
            delta_label="⚡ 100x SEARCH PRUNING SPEED"
        ).move_to([0, 0.4, 0])
        self.play(FadeIn(dual_gauge, scale=0.9), run_time=1.0)
        self.play(dual_gauge.animate_count_up(run_time=min(2.5, b5_dur * 0.4)))
        self.wait(max(0.1, b5_dur - 4.3))
        self.play(FadeOut(dual_gauge), run_time=0.6)

    # =========================================================================
    # DOMAIN 6: QUANTITATIVE BENCHMARK / DEFAULT SHOWDOWN
    # =========================================================================

    def play_quantitative_benchmark_choreography(self):
        """Dynamic comparative metric breakdown for benchmarks & showdowns."""
        meta = self.storyboard.metadata
        m_a = meta.get("model_a", "Challenger Model")
        m_a_name = m_a.get("name", "Challenger") if isinstance(m_a, dict) else str(m_a)
        m_a_score = meta.get("model_a_stat", m_a.get("coding_score", "96.5%")) if isinstance(m_a, dict) else meta.get("model_a_stat", "96.5%")
        
        m_b = meta.get("model_b", "Incumbent Baseline")
        m_b_name = m_b.get("name", "Incumbent") if isinstance(m_b, dict) else str(m_b)
        m_b_score = meta.get("model_b_stat", m_b.get("coding_score", "52.3%")) if isinstance(m_b, dict) else meta.get("model_b_stat", "52.3%")

        b1_dur = self.get_beat_duration(1, 6.0)
        self.display_math_formula(1, run_time=0.5)
        
        gauge = DualMetricGauge(
            model_a_name=m_a_name,
            model_a_score=str(m_a_score),
            model_b_name=m_b_name,
            model_b_score=str(m_b_score),
            delta_label=meta.get("efficiency_badge", "⚡ 1.8x PERFORMANCE ADVANTAGE")
        ).move_to([0, 0.4, 0])
        
        self.play(FadeIn(gauge, scale=0.9), run_time=1.2)
        self.wait(max(0.1, b1_dur - 1.7))
        
        b2_dur = self.get_beat_duration(2, 7.5)
        self.display_math_formula(2, run_time=0.5)
        self.play(gauge.highlight_bottleneck(run_time=1.5))
        self.wait(max(0.1, b2_dur - 2.0))
        
        b3_dur = self.get_beat_duration(3, 7.5)
        self.display_math_formula(3, run_time=0.5)
        self.play(gauge.activate_contender_a(run_time=1.5))
        self.wait(max(0.1, b3_dur - 2.0))
        
        b4_dur = self.get_beat_duration(4, 7.5)
        self.display_math_formula(4, run_time=0.5)
        self.play(gauge.animate_count_up(run_time=2.2))
        self.wait(max(0.1, b4_dur - 2.7))
        
        b5_dur = self.get_beat_duration(5, 7.5)
        self.display_math_formula(5, run_time=0.5)
        self.play(gauge.flash_victory_state(run_time=2.0))
        self.wait(max(0.1, b5_dur - 2.5))
        
        self.play(FadeOut(gauge), run_time=0.6)

    # =========================================================================
    # BEAT 6: MINIMALIST BRAND OUTRO
    # =========================================================================

    def play_brand_outro(self):
        """Minimalist 3b1b brand signature for The Model Verse."""
        b6_dur = self.get_beat_duration(6, 4.5)
        if self.current_formula_mobj:
            self.play(FadeOut(self.current_formula_mobj), FadeOut(self.header_group), run_time=0.4)
            
        # Central Logo Accent Rings (Upper Emblem)
        logo_ring = Circle(radius=0.75, color="#38BDF8", stroke_width=2.2).move_to([0, 0.95, 0])
        logo_ring_inner = Circle(radius=0.58, color="#34D399", stroke_width=1.5).move_to([0, 0.95, 0])
        logo_dot = Dot(point=[0, 0.95, 0], radius=0.10, color=WHITE)
        
        channel_title = Text("THE MODEL VERSE", font_size=26, font="Helvetica", color=WHITE, weight=BOLD).move_to([0, -0.15, 0])
        tagline = Text("themodelverse.in", font_size=15, font="Helvetica", color="#94A3B8").next_to(channel_title, DOWN, buff=0.20)
        cta = Text("SUBSCRIBE FOR ARCHITECTURE DEEP DIVES", font_size=12, font="Helvetica", color="#38BDF8", weight=BOLD).next_to(tagline, DOWN, buff=0.45)
        
        brand_card = VGroup(logo_ring, logo_ring_inner, logo_dot, channel_title, tagline, cta)
        
        self.play(
            FadeIn(channel_title, scale=0.9),
            Create(logo_ring),
            Create(logo_ring_inner),
            FadeIn(logo_dot),
            FadeIn(tagline, shift=UP * 0.15),
            FadeIn(cta, shift=UP * 0.15),
            run_time=1.2
        )
        self.play(
            Rotate(logo_ring, angle=PI / 2, run_time=max(0.5, b6_dur - 2.0), rate_func=linear),
            Rotate(logo_ring_inner, angle=-PI / 2, run_time=max(0.5, b6_dur - 2.0), rate_func=linear)
        )
        self.play(FadeOut(brand_card), run_time=0.6)
