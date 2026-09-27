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
    ScriptWaveInterference,
    ScriptRadioTunerDial,
    ScriptSubspacePacking,
    ScriptPrismDisentangler,
    ScriptBranchingOutputs
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
            svg_filename = matching_formula.get("svg_filename", "")
            svg_path = PROJECT_ROOT / "public" / "math_svgs" / svg_filename if svg_filename else None

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
            text_lower = (b_text + " " + v_focus).lower()

            # Skip outro beat, handled separately
            if beat_id >= 6 or "Follow The Model Verse" in b_text or beat_id == total_beats:
                continue

            duration = self.get_beat_duration(beat_id, 6.5)
            print(f"🎬 [ScriptDrivenScene] Choreographing Beat {beat_id} (Allotted: {duration:.2f}s)...")

            # 1. Update lower math/concept tray
            self.display_math_formula(beat_id, run_time=0.4)

            # 2. Select Motifs or Custom SVG based on Beat Content
            active_mobj = None

            if "wave" in text_lower and ("merg" in text_lower or "two distinct" in text_lower or "collision" in text_lower or beat_id == 1):
                # Beat 1 Motif: Wave collision and interference
                motif = ScriptWaveInterference().move_to([0, 0.4, 0])
                enter_time = min(1.2, duration * 0.25)
                self.play(FadeIn(motif, scale=0.95), run_time=enter_time)
                action_time = min(1.6, duration * 0.3)
                self.play(motif.wave_c.animate.set_color("#FF2A55"), run_time=action_time * 0.5)
                self.play(motif.wave_c.animate.set_color("#EF4444"), run_time=action_time * 0.5)
                active_mobj = motif

            elif "radio" in text_lower or "dial" in text_lower or "tuner" in text_lower or "station" in text_lower:
                # Beat 2 Motif: Analog Radio Tuner with Sweeping Needle
                motif = ScriptRadioTunerDial().move_to([0, 0.4, 0])
                enter_time = min(1.2, duration * 0.25)
                self.play(FadeIn(motif, scale=0.95), run_time=enter_time)
                # Sweep needle to show channel conflict
                action_time = min(1.8, duration * 0.35)
                self.play(motif.needle.animate.shift(LEFT * 0.9), run_time=action_time * 0.4, rate_func=there_and_back)
                self.play(motif.needle.animate.shift(RIGHT * 0.9), run_time=action_time * 0.4, rate_func=there_and_back)
                active_mobj = motif

            elif "space" in text_lower or "bookshelf" in text_lower or "save room" in text_lower or "feature" in text_lower or beat_id == 3:
                # Beat 3 Motif: 2D Subspace Packing & Almost Orthogonal Vectors
                motif = ScriptSubspacePacking().move_to([0, 0.4, 0])
                enter_time = min(1.2, duration * 0.25)
                self.play(FadeIn(motif, scale=0.95), run_time=enter_time)
                action_time = min(1.5, duration * 0.3)
                self.play(motif.angle_arc.animate.set_color("#34D399"), motif.badge_box.animate.scale(1.04), rate_func=there_and_back, run_time=action_time)
                active_mobj = motif

            elif "prism" in text_lower or "peel" in text_lower or "light beam" in text_lower or "disentangl" in text_lower:
                # Beat 4 Motif: Optical Prism Beam Disentangler
                motif = ScriptPrismDisentangler().move_to([0, 0.4, 0])
                enter_time = min(1.2, duration * 0.25)
                self.play(FadeIn(motif, scale=0.95), run_time=enter_time)
                action_time = min(1.5, duration * 0.3)
                self.play(motif.out_beam1.animate.set_stroke(width=8.0), motif.out_beam2.animate.set_stroke(width=8.0), rate_func=there_and_back, run_time=action_time)
                active_mobj = motif

            elif "branch" in text_lower or "two clear answers" in text_lower or "forward pass" in text_lower or beat_id == 5:
                # Beat 5 Motif: Dual Branching Answers
                motif = ScriptBranchingOutputs().move_to([0, 0.4, 0])
                enter_time = min(1.2, duration * 0.25)
                self.play(FadeIn(motif, scale=0.95), run_time=enter_time)
                action_time = min(1.5, duration * 0.3)
                self.play(motif.card1.animate.scale(1.05), motif.card2.animate.scale(1.05), rate_func=there_and_back, run_time=action_time)
                active_mobj = motif

            else:
                # General Custom SVG with Auto-Scaling and Manim Typography
                clean_id = self.spec.get("id", "short_topic")
                default_svg = PROJECT_ROOT / "public" / "visual_assets" / f"{clean_id}_beat_{beat_id}.svg"
                svg_rel_path = b.get("bespoke_svg_path")

                active_svg_path = None
                if svg_rel_path and (PROJECT_ROOT / svg_rel_path).exists():
                    active_svg_path = PROJECT_ROOT / svg_rel_path
                elif default_svg.exists():
                    active_svg_path = default_svg

                if active_svg_path and active_svg_path.exists():
                    try:
                        svg_mobj = SVGMobject(str(active_svg_path))
                        # Scale to fill 60-70% of vertical viewport
                        if svg_mobj.width > 6.4:
                            svg_mobj.scale_to_fit_width(6.4)
                        if svg_mobj.height > 6.0:
                            svg_mobj.scale_to_fit_height(6.0)
                        svg_mobj.move_to([0, 0.4, 0])

                        # Add clear descriptive title banner
                        title_text = v_focus.upper() if len(v_focus) < 40 else (v_focus[:37] + "...").upper()
                        callout = Text(title_text, font=FONT_HELVETICA, font_size=14, color="#38BDF8", weight=HEAVY).move_to([0, 3.8, 0])

                        active_mobj = VGroup(svg_mobj, callout)
                        enter_time = min(1.8, duration * 0.35)
                        self.play(Create(svg_mobj), FadeIn(callout, shift=DOWN * 0.2), run_time=enter_time)
                        action_time = min(1.2, duration * 0.25)
                        self.play(svg_mobj.animate.scale(1.03), rate_func=there_and_back, run_time=action_time)

                    except Exception as e:
                        print(f"⚠️ Error rendering bespoke SVG: {e}")

            # 3. Handle Timing and Transition
            if active_mobj:
                used_time = enter_time + action_time
                remaining = duration - used_time - 0.4
                if remaining > 0.1:
                    self.wait(remaining)
                self.play(FadeOut(active_mobj, shift=DOWN * 0.2), run_time=0.4)
            else:
                self.wait(duration)

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
