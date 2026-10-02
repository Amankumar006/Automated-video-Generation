"""
The Model Verse — Script-Driven Dynamic Scene (Visual Engine 3.0)
Choreographs bespoke, script-generated vector illustrations and procedural kinetic motion.
Each beat visually explains the narrative and physical analogy directly, eliminating repetitive
monolithic templates and circular score gauges.
"""

import os
import sys
import json
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


class ScriptDrivenScene(Scene):
    """
    Intelligent Script-Driven Visual Engine.
    Directly binds bespoke vector designs and procedural geometric motifs to voiceover beats,
    ensuring every second of video provides clear, intuitive visual intuition.
    """

    def construct(self):
        # 1. Load active specification
        self.spec = self.load_spec()
        self.scheduler = KineticScheduler(self.spec)

        # 2. Setup 3b1b Chalkboard Canvas (#0A0D14 + dot matrix lattice)
        self.setup_chalkboard()

        # 3. Setup Persistent Brand Header & Formula Tray
        self.current_formula_mobj = None
        self.setup_header()

        # 4. Choreograph Each Beat with Script-Driven Visuals
        self.play_script_driven_choreography()

        # 5. Outro Brand Signature
        self.play_brand_outro()

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
        """Constructs the signature 3Blue1Brown carbon chalkboard with dot matrix lattice."""
        self.camera.background_color = "#0A0D14"
        dots = VGroup()
        for x in np.arange(-3.6, 3.7, 0.9):
            for y in np.arange(-6.0, 6.1, 0.9):
                dots.add(Dot(point=[x, y, 0], radius=0.016, color="#2D3748", fill_opacity=0.35))
        self.add(dots)

    def setup_header(self):
        """Places subtle brand watermark in the topmost safe zone."""
        hook_tag = self.spec.get("hook_tag", "AI BREAKTHROUGH").upper()
        watermark = VGroup(
            Text("THE MODEL VERSE", font_size=11, font=FONT_HELVETICA, color="#10B981", weight=BOLD),
            Text(" // ", font_size=11, font=FONT_HELVETICA, color="#475569"),
            Text(hook_tag, font_size=10, font=FONT_HELVETICA, color="#94A3B8", weight=MEDIUM)
        ).arrange(RIGHT, buff=0.1).move_to([0, 7.1, 0])
        self.header_group = watermark
        self.add(self.header_group)

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

    def display_math_formula(self, beat_id: int, run_time: float = 0.5):
        """Displays synchronized mathematical formula or key principle badge in the lower tray."""
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

        tray_group.move_to([0, -4.5, 0])

        if self.current_formula_mobj:
            self.play(ReplacementTransform(self.current_formula_mobj, tray_group), run_time=run_time)
        else:
            self.play(FadeIn(tray_group, shift=UP * 0.2), run_time=run_time)
        self.current_formula_mobj = tray_group

    def play_script_driven_choreography(self):
        """
        Executes sequential beat-by-beat visual storytelling using tailored procedural motifs
        and custom vector artwork that directly explains the narration.
        """
        beats = self.spec.get("beats", [])
        total_beats = len(beats)

        for i, b in enumerate(beats):
            beat_id = b.get("beat_id", i + 1)
            b_text = b.get("text", "")
            v_focus = b.get("visual_focus", "")

            # Skip outro beat, handled separately in play_brand_outro
            if beat_id >= 6 or "Follow The Model Verse" in b_text or beat_id == total_beats:
                continue

            duration = self.get_beat_duration(beat_id, 6.5)
            motif_type = b.get("motif_type")
            motif_params = b.get("motif_params", {})
            kinetic_action = b.get("kinetic_action", "pulse")

            # Fallback if motif_type was not assigned in spec
            if not motif_type or motif_type not in MOTIF_REGISTRY:
                text_lower = (b_text + " " + v_focus).lower()
                if any(k in text_lower for k in ["wave", "signal", "interference", "sound"]):
                    motif_type = "wave_collision"
                elif any(k in text_lower for k in ["radio", "dial", "tuner", "station", "static"]):
                    motif_type = "radio_tuner"
                elif any(k in text_lower for k in ["space", "vector", "dimension", "orthogonal"]):
                    motif_type = "subspace_vectors"
                elif any(k in text_lower for k in ["prism", "peel", "disentangl", "decoder"]):
                    motif_type = "prism_disentangler"
                elif any(k in text_lower for k in ["branch", "two clear answers", "simultaneous", "forward pass"]):
                    motif_type = "branching_outputs"
                elif any(k in text_lower for k in ["tree", "search", "mcts", "reason", "logic", "prun"]):
                    motif_type = "tree_search"
                elif any(k in text_lower for k in ["diffus", "noise", "denois", "image", "latent"]):
                    motif_type = "diffusion_denoise"
                elif any(k in text_lower for k in ["attention", "head", "expert", "moe", "rout"]):
                    motif_type = "attention_routing"
                elif any(k in text_lower for k in ["cache", "kv", "memory", "buffer", "context"]):
                    motif_type = "memory_buffer"
                elif beat_id == 5 or any(k in text_lower for k in ["benchmark", "accuracy", "speedup", "faster"]):
                    motif_type = "comparative_bars"
                else:
                    motif_type = "custom_flow"

            print(f"🎬 [ScriptDrivenScene] Choreographing Beat {beat_id} -> Motif: '{motif_type}' (Allotted: {duration:.2f}s)...")

            # 1. Update lower math/concept tray
            self.display_math_formula(beat_id, run_time=0.4)

            # Resolve paper figure SVG if paper_figure motif requested
            if motif_type == "paper_figure":
                if not motif_params.get("svg_path"):
                    if b.get("paper_figure_path") and os.path.exists(b.get("paper_figure_path")):
                        motif_params["svg_path"] = b.get("paper_figure_path")
                    elif self.spec.get("paper_figures"):
                        motif_params["svg_path"] = self.spec["paper_figures"][0].get("svg_path")
                    elif self.spec.get("arxiv_id"):
                        try:
                            from pipeline.arxiv_vector_extractor import get_paper_vector_figure
                            fig_path = get_paper_vector_figure(self.spec.get("arxiv_id"))
                            if fig_path:
                                motif_params["svg_path"] = fig_path
                        except Exception:
                            pass

            # 2. Instantiate Parameterized Script Motif
            motif = create_script_motif(motif_type, motif_params).move_to([0, 0.4, 0])

            # 3. Entrance: Whole Diagram visible within 1.0s
            enter_time = min(1.1, duration * 0.25)
            self.play(FadeIn(motif, scale=0.96), run_time=enter_time)

            # 4. Focal Kinetic Action (Sweeping, Pulsing, Transforming)
            action_time = min(1.8, duration * 0.35)
            try:
                if motif_type == "paper_figure" and hasattr(motif, "frame"):
                    self.play(motif.frame.animate.set_stroke(color="#38BDF8", width=3.0), motif.badge.animate.scale(1.05), rate_func=there_and_back, run_time=action_time)
                elif motif_type == "radio_tuner" and hasattr(motif, "needle"):
                    self.play(motif.needle.animate.shift(LEFT * 0.9), run_time=action_time * 0.5, rate_func=there_and_back)
                    self.play(motif.needle.animate.shift(RIGHT * 0.9), run_time=action_time * 0.5, rate_func=there_and_back)
                elif motif_type == "wave_collision" and hasattr(motif, "wave_c"):
                    self.play(motif.wave_c.animate.set_color("#FF2A55"), run_time=action_time * 0.5)
                    self.play(motif.wave_c.animate.set_color("#EF4444"), run_time=action_time * 0.5)
                elif motif_type == "subspace_vectors" and hasattr(motif, "angle_arc"):
                    self.play(motif.angle_arc.animate.set_color("#34D399"), motif.badge_box.animate.scale(1.04), rate_func=there_and_back, run_time=action_time)
                elif motif_type == "prism_disentangler" and hasattr(motif, "out_beam1"):
                    self.play(motif.out_beam1.animate.set_stroke(width=8.0), motif.out_beam2.animate.set_stroke(width=8.0), rate_func=there_and_back, run_time=action_time)
                elif motif_type == "branching_outputs" and hasattr(motif, "card1"):
                    self.play(motif.card1.animate.scale(1.05), motif.card2.animate.scale(1.05), rate_func=there_and_back, run_time=action_time)
                elif motif_type == "tree_search" and hasattr(motif, "c1"):
                    self.play(motif.c1.animate.scale(1.06), motif.c2.animate.set_stroke(color="#991B1B"), rate_func=there_and_back, run_time=action_time)
                elif motif_type == "diffusion_denoise" and hasattr(motif, "dots1"):
                    self.play(motif.dots1.animate.set_opacity(0.3), motif.shape3.animate.scale(1.15), rate_func=there_and_back, run_time=action_time)
                elif motif_type == "attention_routing" and hasattr(motif, "lasers"):
                    self.play(motif.lasers.animate.set_stroke(width=6.0, color="#34D399"), rate_func=there_and_back, run_time=action_time)
                elif motif_type == "memory_buffer" and hasattr(motif, "slots"):
                    self.play(motif.slots.animate.set_stroke(color="#34D399"), rate_func=there_and_back, run_time=action_time)
                elif motif_type == "comparative_bars" and hasattr(motif, "fill_bar_a"):
                    self.play(motif.fill_bar_a.animate.scale(1.03), motif.badge.animate.scale(1.04), rate_func=there_and_back, run_time=action_time)
                elif hasattr(motif, "box2"):
                    self.play(motif.box2.animate.scale(1.04), rate_func=there_and_back, run_time=action_time)
                else:
                    self.play(motif.animate.scale(1.02), rate_func=there_and_back, run_time=action_time)
            except Exception as e:
                print(f"⚠️ Kinetic action warning for {motif_type}: {e}")
                self.wait(action_time)

            # 5. Hold and Clean Exit
            used_time = enter_time + action_time
            remaining = duration - used_time - 0.4
            if remaining > 0.1:
                self.wait(remaining)
            self.play(FadeOut(motif, shift=DOWN * 0.15), run_time=0.4)

    def play_brand_outro(self):
        """Standard high-conversion 3Blue1Brown chalkboard outro."""
        duration = self.get_beat_duration(6, 4.5)
        if self.current_formula_mobj:
            self.play(FadeOut(self.current_formula_mobj), run_time=0.3)
            self.current_formula_mobj = None

        logo_icon, brand_text, sub = create_chalkboard_brand_outro(
            logo_title="THE MODEL VERSE",
            tagline="Follow for Daily AI Breakthroughs",
            url="themodelverse.in",
            y_center=0.0
        )
        outro_group = VGroup(logo_icon, brand_text, sub)

        self.play(Create(logo_icon), FadeIn(brand_text, shift=UP * 0.2), run_time=1.0)
        self.play(FadeIn(sub, shift=UP * 0.1), run_time=0.6)
        self.wait(max(0.5, duration - 2.0))
        self.play(FadeOut(outro_group), run_time=0.4)
