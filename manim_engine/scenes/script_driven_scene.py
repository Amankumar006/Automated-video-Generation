"""
The Model Verse — Script-Driven Dynamic Scene (Visual Engine 3.0)
Choreographs bespoke, script-generated vector illustrations and procedural kinetic motion.
Each beat visually explains the narrative and physical analogy directly, eliminating repetitive
monolithic templates and circular score gauges.
"""

import os
import sys
import json
import re
import importlib.util
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from manim import *

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT, BG_CARBON,
    FONT_HELVETICA
)
from manim_engine.primitives.typography import CleanText

# Alias Text -> CleanText so HUD headers and brand watermarks render with flawless subpixel typography
Text = CleanText

# 9:16 vertical video dimensions
config.pixel_width = VIDEO_WIDTH
config.pixel_height = VIDEO_HEIGHT
config.frame_width = FRAME_WIDTH
config.frame_height = FRAME_HEIGHT
config.background_color = BG_CARBON

from manim_engine.scheduler import KineticScheduler
from manim_engine.primitives.outro_card import create_chalkboard_brand_outro
from manim_engine.primitives.script_motifs import (
    MOTIF_REGISTRY,
    create_script_motif
)
from manim_engine.controllers import SpotlightStagingController, KineticCameraController
from manim_engine.primitives.particles import create_formula_sparkle_burst, create_formula_halo_pulse


class ScriptDrivenScene(MovingCameraScene):
    """
    Intelligent Script-Driven Visual Engine (Visual Engine 7.0).
    Directly binds bespoke vector designs and procedural geometric motifs to voiceover beats,
    with cognitive spotlight staging (100% focal illumination / 20% background dimming)
    and continuous kinetic camera breathing with punch-in zooms to eliminate static screens.
    """

    def construct(self):
        # 1. Load active specification & controllers
        self.spec = self.load_spec()
        self.scheduler = KineticScheduler(self.spec)
        self.spotlight_controller = SpotlightStagingController()
        self.kinetic_camera = KineticCameraController()

        # 2. Setup 3b1b Chalkboard Canvas (#0A0D14 + dot matrix lattice)
        self.setup_chalkboard()

        # 3. Setup Persistent Brand Header & Formula Tray
        self.current_formula_mobj = None
        self.active_auxiliary_mobjects = []
        self.setup_header()

        # 3.5 Setup Synchronized Kinetic Subtitle Pill
        self.setup_kinetic_captions()

        # 4. Choreograph Each Beat with Script-Driven Visuals
        self.play_script_driven_choreography()

        # 5. Outro Brand Signature
        self.play_brand_outro()

    def track_auxiliary_mobject(self, *mobjects: Mobject):
        """Registers transient/auxiliary mobjects (particles, halos, overlays) to be cleaned up at beat exit."""
        for m in mobjects:
            if m is not None and m not in self.active_auxiliary_mobjects:
                self.active_auxiliary_mobjects.append(m)

    def load_spec(self) -> Dict[str, Any]:
        """Loads active spec from ACTIVE_SPEC_PATH or latest generated template."""
        spec_path = os.environ.get("ACTIVE_SPEC_PATH")
        spec_data = {}
        if spec_path and os.path.exists(spec_path):
            try:
                with open(spec_path, "r", encoding="utf-8") as f:
                    spec_data = json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading ACTIVE_SPEC_PATH '{spec_path}': {e}")

        if not spec_data:
            templates = list((PROJECT_ROOT / "pipeline" / "templates").glob("*.json"))
            if templates:
                with open(templates[0], "r", encoding="utf-8") as f:
                    spec_data = json.load(f)

        return spec_data

    def setup_chalkboard(self):
        """Constructs the signature 3Blue1Brown carbon chalkboard with dot matrix lattice (Depth Layer 1)."""
        self.camera.background_color = "#0A0D14"
        dots = VGroup()
        for x in np.arange(-3.6, 3.7, 0.9):
            for y in np.arange(-6.0, 6.1, 0.9):
                dots.add(Dot(point=[x, y, 0], radius=0.016, color="#2D3748", fill_opacity=0.35))
        dots.set_z_index(-10)
        self.dots = dots
        self.add(self.dots)

    def setup_header(self):
        """Places subtle brand watermark in the topmost safe zone (Depth Layer 3)."""
        hook_tag = self.spec.get("hook_tag", "AI BREAKTHROUGH").upper()
        watermark = VGroup(
            Text("THE MODEL VERSE", font_size=11, font=FONT_HELVETICA, color="#10B981", weight=BOLD),
            Text(" // ", font_size=11, font=FONT_HELVETICA, color="#475569"),
            Text(hook_tag, font_size=10, font=FONT_HELVETICA, color="#94A3B8", weight=MEDIUM)
        ).arrange(RIGHT, buff=0.1).move_to([0, 7.1, 0])
        self.header_group = watermark
        self.header_group.set_z_index(50)
        def update_header(mob, dt):
            cam_center = self.camera.frame.get_center()
            mob.move_to([cam_center[0], cam_center[1] + 7.1, 0])
        self.header_group.add_updater(update_header)
        self.add(self.header_group)

    def setup_kinetic_captions(self):
        """Constructs dynamically updating kinetic subtitle pill positioned at y = -3.45 (Depth Layer 3)."""
        try:
            from pipeline.subtitle_generator import generate_phrase_chunks
            self.caption_chunks = generate_phrase_chunks(self.spec.get("beats", []))
        except Exception as e:
            print(f"⚠️ Kinetic subtitle setup notice: {e}")
            self.caption_chunks = []

        self.caption_container = VGroup().move_to([0, -3.45, 0])
        self.caption_container.set_z_index(60)
        self.add(self.caption_container)

        if not self.caption_chunks:
            return

        self.current_caption_idx = -1

        def update_caption(mob, dt):
            t = self.renderer.time
            matched = False
            for i, c in enumerate(self.caption_chunks):
                if c["start"] <= t < c["end"]:
                    matched = True
                    if self.current_caption_idx != i:
                        self.current_caption_idx = i
                        raw_text = c["text"]
                        highlight = c.get("highlight_word", "")
                        h_color = c.get("highlight_color", "#FDE047")
                        t2c = {highlight: h_color} if highlight and highlight in raw_text else {}

                        txt = Text(
                            raw_text,
                            font=FONT_HELVETICA,
                            font_size=19,
                            weight=BOLD,
                            color=WHITE,
                            t2c=t2c
                        )
                        if txt.width > 6.0:
                            txt.scale_to_fit_width(6.0)
                        pill_w = min(6.5, txt.width + 0.65)
                        pill_h = 0.72
                        bg = RoundedRectangle(
                            corner_radius=0.18,
                            width=pill_w,
                            height=pill_h,
                            fill_color="#080C14",
                            fill_opacity=0.92,
                            stroke_color="#334155",
                            stroke_width=1.4
                        )
                        cam_center = self.camera.frame.get_center()
                        mob.become(VGroup(bg, txt).move_to([cam_center[0], cam_center[1] - 3.45, 0]))
                    break

            if not matched and self.current_caption_idx != -1:
                self.current_caption_idx = -1
                mob.become(VGroup())

        self.caption_container.add_updater(update_caption)

    def get_beat_duration(self, beat_id: int, default_dur: float = 6.0) -> float:
        """Calculates duration allotted to the specific beat."""
        for b in self.spec.get("beats", []):
            if b.get("beat_id") == beat_id:
                if "slot_duration" in b:
                    return float(b["slot_duration"])
                if "audio_duration" in b:
                    return float(b["audio_duration"]) + 0.35
                if "duration" in b:
                    return float(b["duration"])
        return default_dur

    def _build_formula_tray_mobject(self, beat_id: int) -> VGroup:
        """Constructs the math formula or key concept badge for the given beat."""
        formulas = self.spec.get("math_formulas", [])
        matching_formula = None
        for f in formulas:
            if f.get("beat_id") == beat_id:
                matching_formula = f
                break

        if not matching_formula and beat_id <= len(formulas):
            matching_formula = formulas[beat_id - 1]

        tray_group = VGroup()
        if matching_formula:
            # Check for pre-rendered SVG math
            svg_filename = matching_formula.get("svg_filename") or matching_formula.get("filename") or ""
            svg_path = PROJECT_ROOT / "public" / "math_svgs" / svg_filename if svg_filename else None

            # Render on-the-fly via matplotlib mathtext if file is missing from disk
            if svg_filename and (not svg_path or not svg_path.exists()):
                latex_code = matching_formula.get("latex", "")
                if latex_code:
                    try:
                        from scripts.generate_math_svgs import render_math_to_svg
                        render_math_to_svg(latex_code, svg_filename, fontsize=matching_formula.get("fontsize", 24))
                    except Exception as e:
                        print(f"⚠️ On-the-fly math SVG generation failed: {e}")

            if svg_path and svg_path.exists():
                try:
                    math_mobj = SVGMobject(str(svg_path))
                    math_mobj.set_color_by_gradient("#38BDF8", "#34D399")
                    if math_mobj.width > 5.5:
                        math_mobj.scale_to_fit_width(5.5)
                    if math_mobj.height > 0.9:
                        math_mobj.scale_to_fit_height(0.9)
                    tray_group.add(math_mobj)
                except Exception:
                    pass

            if len(tray_group) == 0:
                latex_code = matching_formula.get("latex", "")
                if latex_code:
                    try:
                        clean_tex = latex_code.replace(r"\implies", r"\to").replace(r"\iff", r"\leftrightarrow")
                        math_mobj = MathTex(clean_tex, font_size=24, color="#38BDF8")
                        if math_mobj.width > 5.5:
                            math_mobj.scale_to_fit_width(5.5)
                        tray_group.add(math_mobj)
                    except Exception:
                        pass

        # If no formula, add key insight chip
        if len(tray_group) == 0:
            for b in self.spec.get("beats", []):
                if b.get("beat_id") == beat_id:
                    v_focus = b.get("visual_focus", "")
                    short_label = v_focus[:45] + "..." if len(v_focus) > 45 else v_focus
                    chip = Text(short_label.upper(), font_size=11, font=FONT_HELVETICA, color="#64748B", weight=BOLD)
                    tray_group.add(chip)
                    break

        tray_group.set_z_index(70)
        tray_group.move_to([0, -4.5, 0])
        return tray_group

    def display_math_formula(self, beat_id: int, run_time: float = 0.35):
        """Displays synchronized mathematical formula or key principle badge in the lower tray."""
        tray_group = self._build_formula_tray_mobject(beat_id)
        if self.current_formula_mobj:
            self.play(ReplacementTransform(self.current_formula_mobj, tray_group), run_time=run_time)
        else:
            self.play(FadeIn(tray_group, shift=UP * 0.2), run_time=run_time)
        self.current_formula_mobj = tray_group

    def play_script_driven_choreography(self):
        """
        Executes sequential beat-by-beat visual storytelling using tailored procedural motifs
        and custom vector artwork that directly explains the narration, locked to millisecond audio timestamps.
        """
        beats = self.spec.get("beats", [])
        total_beats = len(beats)

        for i, b in enumerate(beats):
            beat_id = b.get("beat_id", i + 1)
            b_text = b.get("text", "")
            v_focus = b.get("visual_focus", "")

            # Reset active auxiliary mobjects tracking collection for the beat
            self.active_auxiliary_mobjects = []

            # Skip final outro beat, handled separately in play_brand_outro
            if beat_id == total_beats:
                continue

            duration = self.get_beat_duration(beat_id, 6.5)
            motif_type = b.get("motif_type")
            motif_params = dict(b.get("motif_params", {}))
            kinetic_action = b.get("kinetic_action", "pulse")

            from manim_engine.primitives.visual_compositions import BLUEPRINT_COMPOSITION_REGISTRY

            # Visual Engine 4.0: Unpack visual_blueprint as the primary driver for bespoke composition
            visual_blueprint = b.get("visual_blueprint")
            if visual_blueprint and isinstance(visual_blueprint, dict):
                bp_layout = visual_blueprint.get("layout")
                motif_type = "visual_composition"
                motif_params["layout"] = bp_layout
                if visual_blueprint.get("title"):
                    motif_params["title"] = visual_blueprint["title"]
                if visual_blueprint.get("sub"):
                    motif_params["sub"] = visual_blueprint["sub"]
                if visual_blueprint.get("accent_color"):
                    motif_params["accent_color"] = visual_blueprint["accent_color"]
                if "params" in visual_blueprint and isinstance(visual_blueprint["params"], dict):
                    motif_params.update(visual_blueprint["params"])

            # Auto-enrich benchmark layouts with paper's empirical ground truth
            bm = self.spec.get("benchmark_comparison", {})
            curr_layout = motif_params.get("layout")
            if curr_layout in ["horizontal_race_bars", "benchmark_race", "race_bars", "comparative_bars"]:
                motif_params["layout"] = "horizontal_race_bars"
                if not motif_params.get("contestants") and bm.get("contestants"):
                    motif_params["contestants"] = bm["contestants"]
                if not motif_params.get("metric_name") and bm.get("metric_name"):
                    motif_params["metric_name"] = bm["metric_name"]
                if not motif_params.get("unit") and bm.get("unit"):
                    motif_params["unit"] = bm["unit"]
                if not motif_params.get("delta_badge") and bm.get("delta_badge"):
                    motif_params["delta_badge"] = bm["delta_badge"]
                if not motif_params.get("title") and bm.get("title"):
                    motif_params["title"] = bm["title"]

            # Force Upgrade: Never render legacy repetitive canned motifs or generic placeholder cards!
            canned_legacy = [
                "prism_disentangler", "attention_routing", "tree_search",
                "memory_buffer", "custom_flow", "branching_outputs",
                "wave_collision", "radio_tuner", "subspace_vectors", "diffusion_denoise"
            ]

            # Visual Engine 4.0: Composable Visual Blueprint (First-class citizen)
            if beat_id == 5:
                # Beat 5 is the empirical victory / payoff beat.
                # Always elevate generic placeholders or comparison cards to authentic benchmark race bars!
                if not visual_blueprint or curr_layout in ["comparative_bars", "benchmark_bars", "comparison_side_by_side", None] or not motif_params.get("contestants"):
                    from pipeline.benchmark_extractor import BenchmarkExtractor
                    b_comp = BenchmarkExtractor().extract_or_fallback(self.spec)
                    motif_type = "visual_composition"
                    motif_params["layout"] = "horizontal_race_bars"
                    motif_params["contestants"] = [
                        {
                            "name": c.name,
                            "value": c.value,
                            "display_val": c.raw_str,
                            "is_hero": c.is_hero,
                            "color": c.color
                        }
                        for c in b_comp.contestants
                    ]
                    motif_params["metric_name"] = b_comp.metric_name
                    motif_params["unit"] = b_comp.unit
                    motif_params["delta_badge"] = b_comp.delta_badge
                    if not motif_params.get("title") or motif_params.get("title") in ["THE PERFORMANCE GAP", "ARCHITECTURAL OVERVIEW"]:
                        motif_params["title"] = b_comp.title
                    if not motif_params.get("sub"):
                        motif_params["sub"] = "Quantitative empirical evaluation against frontier baselines"
                else:
                    motif_type = "visual_composition"
            elif motif_type == "visual_composition" or motif_type in BLUEPRINT_COMPOSITION_REGISTRY:
                pass
            elif motif_type in canned_legacy or not motif_type or motif_type not in MOTIF_REGISTRY:
                if beat_id == 3 and self.spec.get("paper_figures"):
                    motif_type = "paper_figure"
                else:
                    motif_type = "visual_composition"

            # Strict audio-synchronous timing anchors
            expected_start = float(b.get("start", self.renderer.time))
            expected_end = expected_start + duration
            if self.renderer.time < expected_start:
                self.wait(expected_start - self.renderer.time)

            print(f"🎬 [ScriptDrivenScene] Choreographing Beat {beat_id} -> Motif: '{motif_type}' [Target: {expected_start:.2f}s -> {expected_end:.2f}s | Dur: {duration:.2f}s]...")

            # Resolve SVG / Image asset for paper_figure or bespoke_svg
            if motif_type in ["paper_figure", "bespoke_svg", "dynamic_svg"]:
                current_svg = motif_params.get("svg_path") or b.get("svg_path") or b.get("paper_figure_path")
                current_img = motif_params.get("image_path") or b.get("image_path")
                if motif_type == "paper_figure" and self.spec.get("paper_figures"):
                    first_fig = self.spec["paper_figures"][0]
                    if not current_svg and first_fig.get("svg_path"):
                        current_svg = first_fig.get("svg_path")
                    if not current_img and first_fig.get("image_path"):
                        current_img = first_fig.get("image_path")

                if current_svg and os.path.exists(current_svg):
                    motif_params["svg_path"] = current_svg
                if current_img and os.path.exists(current_img):
                    motif_params["image_path"] = current_img

                if not motif_params.get("title"):
                    motif_params["title"] = f"{self.spec.get('title', 'AI')[:22].upper()}: BEAT {beat_id}"
                if not motif_params.get("sub"):
                    motif_params["sub"] = v_focus[:55] or "Official architectural diagram tailored to narrative beat"
                if not motif_params.get("arxiv_id") and self.spec.get("arxiv_id"):
                    motif_params["arxiv_id"] = self.spec.get("arxiv_id")

            from manim_engine.primitives.visual_compositions import BaseBlueprintComposition

            # Instantiate Visual: Check for Bespoke Synthesized Module (Visual Engine 6.0)
            spec_clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", self.spec.get("id", "short")).lower()
            bespoke_module_path = PROJECT_ROOT / "manim_engine" / "generated" / spec_clean_id / f"beat_{beat_id}.py"
            motif = None

            if bespoke_module_path.exists():
                try:
                    mod_name = f"bespoke_{spec_clean_id}_beat_{beat_id}"
                    spec_import = importlib.util.spec_from_file_location(mod_name, str(bespoke_module_path))
                    mod = importlib.util.module_from_spec(spec_import)
                    spec_import.loader.exec_module(mod)
                    if hasattr(mod, "BespokeBeatVisual"):
                        motif = mod.BespokeBeatVisual()
                        print(f"   ✨ [Visual Engine 6.0] Successfully loaded bespoke visual from {bespoke_module_path.name}")
                except Exception as e:
                    print(f"⚠️ Error loading bespoke visual for Beat {beat_id}: {e}. Falling back to motif registry.")

            if motif is None:
                motif = create_script_motif(motif_type, motif_params)

            if not isinstance(motif, BaseBlueprintComposition):
                motif.move_to([0, 0.65, 0])
            motif.set_z_index(10)

            # 1 & 2. Construct Tray & Prepare Synchronous Entrance
            tray_group = self._build_formula_tray_mobject(beat_id)
            if self.current_formula_mobj:
                formula_anim = ReplacementTransform(self.current_formula_mobj, tray_group)
            else:
                formula_anim = FadeIn(tray_group, shift=UP * 0.2)
            self.current_formula_mobj = tray_group

            enter_time = min(0.85, duration * 0.20)
            if hasattr(motif, "get_entrance_animation"):
                motif_enter = motif.get_entrance_animation(run_time=enter_time)
            else:
                motif_enter = FadeIn(motif, scale=0.96, run_time=enter_time)

            # Cognitive Spotlight Staging (Visual Engine 7.0)
            # Prepared concurrently with entrance so it never adds dead pauses!
            spotlight_anims = []
            try:
                spotlight_anims = self.spotlight_controller.apply_spotlight(
                    scene=self,
                    motif=motif,
                    svo_action=b.get("svo_action"),
                    highlight_words=b.get("highlight_words"),
                    run_time=enter_time,
                    dim_opacity=0.55,
                    play_now=False
                )
                if getattr(self.spotlight_controller, "active_halo", None) is not None:
                    self.track_auxiliary_mobject(self.spotlight_controller.active_halo)
            except Exception as e:
                print(f"⚠️ Spotlight staging notice: {e}")

            # Formula Luminous Sparkle Burst & Neon Halo (Visual Engine 7.5)
            particle_anims = []
            try:
                if len(tray_group) > 0 and beat_id in [3, 4, 5]:
                    burst_pts, burst_anim = create_formula_sparkle_burst(tray_group, color="#38BDF8", run_time=enter_time)
                    halo_box, halo_anim = create_formula_halo_pulse(tray_group, color="#38BDF8", run_time=enter_time)
                    self.add(burst_pts, halo_box)
                    self.track_auxiliary_mobject(burst_pts, halo_box)
                    particle_anims = [burst_anim, halo_anim]
            except Exception as e_p:
                print(f"⚠️ Particle entrance notice: {e_p}")

            entrance_group = [motif_enter, formula_anim]
            if spotlight_anims:
                entrance_group.extend(spotlight_anims)
            if particle_anims:
                entrance_group.extend(particle_anims)
            self.play(*entrance_group, run_time=enter_time)

            # 3. Focal Kinetic Action & Cinematic Camera Staging (Cinematic Engine 8.0)
            action_time = min(1.3, duration * 0.26)
            camera_action_anim = None

            if beat_id == 5:
                # Climax Peak: High-energy snap zoom framing the empirical victory / SOTA delta badge
                try:
                    camera_action_anim = self.kinetic_camera.get_hero_metric_snap_animation(
                        camera_frame=self.camera.frame,
                        target_point=motif.get_center(),
                        zoom_factor=0.76,
                        run_time=action_time
                    )
                except Exception as e:
                    print(f"⚠️ Hero metric snap notice: {e}")
            elif beat_id == 3 and motif_type in ["pipeline_stages", "split_flow", "branching_outputs"]:
                # Lateral Tracking Dolly: Smooth camera tracking pan across pipeline stages (Left to Right)
                try:
                    camera_action_anim = self.kinetic_camera.get_lateral_tracking_animation(
                        camera_frame=self.camera.frame,
                        start_x=-0.8,
                        end_x=0.8,
                        y=0.0,
                        run_time=action_time
                    )
                except Exception as e:
                    print(f"⚠️ Lateral tracking dolly notice: {e}")
            else:
                # Beats 1, 2, 4 maintain visual stability without repetitive zoom pulsing
                camera_action_anim = None

            try:
                if hasattr(motif, "get_kinetic_animation"):
                    kinetic_anim = motif.get_kinetic_animation(run_time=action_time)
                elif motif_type in ["paper_figure", "bespoke_svg", "dynamic_svg"] and hasattr(motif, "fig_mobj") and motif.fig_mobj:
                    kinetic_anim = motif.fig_mobj.animate(rate_func=there_and_back, run_time=action_time).scale(1.03)
                elif motif_type == "radio_tuner" and hasattr(motif, "needle"):
                    kinetic_anim = motif.needle.animate(rate_func=there_and_back, run_time=action_time).shift(RIGHT * 0.5)
                elif motif_type == "wave_collision" and hasattr(motif, "wave_c"):
                    kinetic_anim = motif.wave_c.animate(run_time=action_time).set_color("#FF2A55")
                elif motif_type == "subspace_vectors" and hasattr(motif, "angle_arc"):
                    badge_grp = VGroup(motif.badge_box, motif.badge_txt, motif.badge_sub) if hasattr(motif, "badge_txt") else motif.badge_box
                    kinetic_anim = AnimationGroup(motif.angle_arc.animate(rate_func=there_and_back, run_time=action_time).set_color("#34D399"), badge_grp.animate(rate_func=there_and_back, run_time=action_time).scale(1.04))
                elif motif_type == "prism_disentangler" and hasattr(motif, "out_beam1"):
                    kinetic_anim = AnimationGroup(motif.out_beam1.animate(rate_func=there_and_back, run_time=action_time).set_stroke(width=8.0), motif.out_beam2.animate(rate_func=there_and_back, run_time=action_time).set_stroke(width=8.0))
                elif motif_type == "branching_outputs" and hasattr(motif, "card1"):
                    kinetic_anim = AnimationGroup(motif.card1.animate(rate_func=there_and_back, run_time=action_time).scale(1.05), motif.card2.animate(rate_func=there_and_back, run_time=action_time).scale(1.05))
                elif motif_type == "tree_search" and hasattr(motif, "c1"):
                    kinetic_anim = AnimationGroup(motif.c1.animate(rate_func=there_and_back, run_time=action_time).scale(1.06), motif.c2.animate(rate_func=there_and_back, run_time=action_time).set_stroke(color="#991B1B"))
                elif motif_type == "diffusion_denoise" and hasattr(motif, "dots1"):
                    kinetic_anim = AnimationGroup(motif.dots1.animate(rate_func=there_and_back, run_time=action_time).set_opacity(0.3), motif.shape3.animate(rate_func=there_and_back, run_time=action_time).scale(1.15))
                elif motif_type == "attention_routing" and hasattr(motif, "lasers"):
                    kinetic_anim = motif.lasers.animate(rate_func=there_and_back, run_time=action_time).set_stroke(width=6.0, color="#34D399")
                elif motif_type == "memory_buffer" and hasattr(motif, "slots"):
                    kinetic_anim = motif.slots.animate(rate_func=there_and_back, run_time=action_time).set_stroke(color="#34D399")
                elif motif_type == "comparative_bars" and hasattr(motif, "fill_bar_a"):
                    kinetic_anim = AnimationGroup(motif.fill_bar_a.animate(rate_func=there_and_back, run_time=action_time).scale(1.03), motif.badge.animate(rate_func=there_and_back, run_time=action_time).scale(1.04))
                elif hasattr(motif, "box2"):
                    kinetic_anim = motif.box2.animate(rate_func=there_and_back, run_time=action_time).scale(1.04)
                else:
                    kinetic_anim = motif.animate(rate_func=there_and_back, run_time=action_time).scale(1.02)

                action_anims = [kinetic_anim]
                if camera_action_anim:
                    action_anims.append(camera_action_anim)
                self.play(*action_anims, run_time=action_time)
            except Exception as e:
                print(f"⚠️ Kinetic action warning for {motif_type}: {e}")
                self.wait(action_time)

            # 4. Continuous Ambient Micro-Motion (Strict Clock Alignment)
            exit_time = 0.30
            time_before_exit = expected_end - exit_time
            remaining = max(0.0, time_before_exit - self.renderer.time)
            if remaining > 0.05:
                self.play_ambient_micro_motion(motif, motif_type, remaining)

            # 5. Clean Exit & Framing Reset (Simultaneous, Exact Audio Cut)
            actual_exit = max(0.15, expected_end - self.renderer.time)
            exit_anims = [FadeOut(motif, shift=DOWN * 0.15)]
            if self.current_formula_mobj:
                exit_anims.append(FadeOut(self.current_formula_mobj, shift=DOWN * 0.15))

            # Include all tracked auxiliary mobjects (particles, halos, overlays) in exit animation
            for aux_mob in self.active_auxiliary_mobjects:
                if aux_mob is not None and aux_mob in self.mobjects:
                    exit_anims.append(FadeOut(aux_mob, shift=DOWN * 0.15))
            
            # Only reset camera framing if the camera actually moved or zoomed
            if camera_action_anim is not None or beat_id == 5:
                reset_anim = self.kinetic_camera.get_reset_animation(self.camera.frame, run_time=actual_exit)
                exit_anims.append(reset_anim)

            self.play(*exit_anims, run_time=actual_exit)
            self.remove(motif)
            if self.current_formula_mobj:
                self.remove(self.current_formula_mobj)
                self.current_formula_mobj = None

            # Explicitly purge all tracked auxiliary mobjects from scene graph
            for aux_mob in self.active_auxiliary_mobjects:
                if aux_mob is not None:
                    self.remove(aux_mob)
            self.active_auxiliary_mobjects.clear()
            if hasattr(self.spotlight_controller, "active_halo"):
                self.spotlight_controller.active_halo = None

    def play_ambient_micro_motion(self, motif: Mobject, motif_type: str, remaining_time: float):
        """
        3Blue1Brown-Standard Continuous Ambient Micro-Motion:
        Eliminates 'dead screens' / static wait during remaining voiceover narration.
        Applies a gentle 2.5% slow camera push-in and subtle drift,
        coupled with contextual traveling energy pulses across active motif elements.
        """
        if remaining_time <= 0.05:
            return

        anims = []

        # 1. Continuous Organic Camera Breathing (6% dynamic glide)
        anims.append(
            self.kinetic_camera.get_ambient_drift_animation(
                camera_frame=self.camera.frame,
                duration=remaining_time,
                scale_factor=0.94,
                shift_vector=np.array([0.0, 0.12, 0.0])
            )
        )

        # 2. Contextual Traveling Energy & Shimmer on the Active Motif
        try:
            if hasattr(motif, "get_ambient_animation"):
                anims.append(motif.get_ambient_animation(run_time=remaining_time))
            elif motif_type == "wave_collision" and hasattr(motif, "wave_c"):
                anims.append(motif.wave_c.animate(rate_func=there_and_back, run_time=remaining_time).set_stroke(width=6.2, color="#F43F5E"))
            elif motif_type == "radio_tuner" and hasattr(motif, "needle"):
                anims.append(motif.needle.animate(rate_func=there_and_back, run_time=remaining_time).shift(RIGHT * 0.28))
            elif motif_type == "subspace_vectors" and hasattr(motif, "angle_arc"):
                anims.append(motif.angle_arc.animate(rate_func=there_and_back, run_time=remaining_time).set_stroke(color="#10B981", width=5.5))
            elif motif_type == "prism_disentangler" and hasattr(motif, "out_beam1") and hasattr(motif, "out_beam2"):
                anims.append(motif.out_beam1.animate(rate_func=there_and_back, run_time=remaining_time).set_stroke(width=7.5, color="#67E8F9"))
                anims.append(motif.out_beam2.animate(rate_func=there_and_back, run_time=remaining_time).set_stroke(width=7.5, color="#FBBF24"))
            elif motif_type == "branching_outputs" and hasattr(motif, "card1") and hasattr(motif, "card2"):
                anims.append(motif.card1.animate(rate_func=there_and_back, run_time=remaining_time).scale(1.05))
                anims.append(motif.card2.animate(rate_func=there_and_back, run_time=remaining_time).scale(1.05))
            elif motif_type == "tree_search" and hasattr(motif, "c1"):
                anims.append(motif.c1.animate(rate_func=there_and_back, run_time=remaining_time).set_stroke(color="#FBBF24", width=4.5))
            elif motif_type == "diffusion_denoise" and hasattr(motif, "shape3"):
                anims.append(motif.shape3.animate(rate_func=there_and_back, run_time=remaining_time).scale(1.08))
            elif motif_type == "attention_routing" and hasattr(motif, "lasers"):
                anims.append(motif.lasers.animate(rate_func=there_and_back, run_time=remaining_time).set_stroke(width=7.0, color="#6EE7B7"))
            elif motif_type == "memory_buffer" and hasattr(motif, "slots"):
                anims.append(motif.slots.animate(rate_func=there_and_back, run_time=remaining_time).set_stroke(color="#34D399", width=4.5))
            elif motif_type == "comparative_bars" and hasattr(motif, "fill_bar_a"):
                anims.append(motif.fill_bar_a.animate(rate_func=there_and_back, run_time=remaining_time).scale(1.05))
            elif motif_type in ["paper_figure", "bespoke_svg", "dynamic_svg"] and hasattr(motif, "fig_mobj") and motif.fig_mobj:
                anims.append(motif.fig_mobj.animate(rate_func=there_and_back, run_time=remaining_time).scale(1.04))
            elif hasattr(motif, "badge"):
                anims.append(motif.badge.animate(rate_func=there_and_back, run_time=remaining_time).scale(1.04))
            else:
                anims.append(motif.animate(rate_func=there_and_back, run_time=remaining_time).scale(1.04))
        except Exception as e:
            print(f"⚠️ Ambient micro-motion note for {motif_type}: {e}")

        # 3. Dynamic ambient pulse on lower concept/formula tray
        if self.current_formula_mobj:
            anims.append(
                self.current_formula_mobj.animate(rate_func=there_and_back, run_time=remaining_time).scale(1.035)
            )

        self.play(*anims, run_time=remaining_time)

    def play_brand_outro(self):
        """Standard high-conversion 3Blue1Brown chalkboard outro with continuous subtle drift."""
        total_beats = len(self.spec.get("beats", []))
        duration = self.get_beat_duration(total_beats, 4.5)
        # 1. Cleanly purge ALL lingering vector mobjects from prior beats (except background dots & header)
        persistent = {getattr(self, "dots", None), getattr(self, "header_group", None)}
        lingering = [m for m in list(self.mobjects) if m not in persistent and m is not None]

        if hasattr(self, "caption_container") and self.caption_container:
            try:
                self.caption_container.clear_updaters()
            except Exception:
                pass

        purge_time = 0.25 if lingering else 0.0
        if lingering:
            self.play(*[FadeOut(m) for m in lingering], run_time=purge_time)
            for m in lingering:
                self.remove(m)

        self.current_formula_mobj = None
        self.caption_container = None

        logo_icon, brand_text, sub = create_chalkboard_brand_outro(
            logo_title="THE MODEL VERSE",
            tagline="Follow for Daily AI Breakthroughs",
            url="themodelverse.in",
            y_center=0.0
        )
        outro_group = VGroup(logo_icon, brand_text, sub)

        intro_logo_time = 0.9
        intro_sub_time = 0.5
        exit_time = 0.35
        self.play(Create(logo_icon), FadeIn(brand_text, shift=UP * 0.2), run_time=intro_logo_time)
        self.play(FadeIn(sub, shift=UP * 0.1), run_time=intro_sub_time)

        # Micro-drift during outro narration & music
        used_so_far = purge_time + intro_logo_time + intro_sub_time + exit_time
        outro_hold = max(0.5, duration - used_so_far)
        self.play(
            self.camera.frame.animate(rate_func=linear).scale(0.985).shift(UP * 0.05),
            brand_text.animate(rate_func=there_and_back).set_color("#34D399"),
            logo_icon.animate(rate_func=there_and_back).scale(1.03),
            run_time=outro_hold
        )
        self.play(FadeOut(outro_group), run_time=exit_time)
