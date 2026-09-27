"""
The Model Verse — Architecture Breakdown Scene (Pure 3Blue1Brown Mathematical Blackboard Edition)
Broadcast-grade vertical mathematical animation explaining DeepSeek-V3 Sparse Mixture of Experts.

Key 3b1b Principles:
1. Living chalkboard canvas (#0A0D14) with mathematical coordinate dot matrix.
2. Authentic LaTeX Computer Modern mathematical formulas (SVGMobject) in free space.
3. Concrete geometric representations: bipartite synaptic networks, 256-node constellation, routing vectors.
4. Continuous motivated mathematical motion — zero static frames, zero graphic collisions.
5. Pure minimalist chalkboard branding — zero SaaS cards, zero fake buttons.
"""

import os
import json
from manim import *
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from manim_engine.base_scene import BaseShortScene
from manim_engine.primitives.outro_card import create_chalkboard_brand_outro
from manim_engine.primitives.chalkboard_captions import ChalkboardCaptions
from manim_engine.primitives.leaderboard import create_dual_accuracy_bar_chart
from pipeline.config import (
    FONT_HELVETICA, COLOR_MINT, COLOR_DANGER, COLOR_GOLD, COLOR_SLATE,
    FRAME_WIDTH, FRAME_HEIGHT
)

class ArchitectureBreakdownScene(BaseShortScene):
    def construct(self):
        self.setup_canvas("ARCHITECTURE LAB")
        captions = ChalkboardCaptions(self, y_pos=-4.8)

        spec = {}
        spec_path = os.environ.get("ACTIVE_SPEC_PATH")
        if spec_path and os.path.exists(spec_path):
            try:
                with open(spec_path, "r", encoding="utf-8") as f:
                    spec = json.load(f)
            except Exception:
                pass

        def get_beat_parts(beat_id: int, count: int, defaults: list, def_hl: dict):
            for b in spec.get("beats", []):
                if b.get("beat_id") == beat_id:
                    full_text = b.get("text", "")
                    hl = b.get("highlight_words", def_hl)
                    import re
                    sentences = [s.strip() for s in re.split(r'(?<=[.?!])\s+', full_text) if s.strip()]
                    if len(sentences) >= count:
                        return sentences[:count], hl
                    words = full_text.split()
                    if len(words) >= count * 2:
                        chunk_sz = len(words) // count
                        parts = []
                        for i in range(count):
                            if i == count - 1:
                                parts.append(" ".join(words[i * chunk_sz:]))
                            else:
                                parts.append(" ".join(words[i * chunk_sz:(i + 1) * chunk_sz]))
                        return parts, hl
                    res = list(sentences) if sentences else [full_text]
                    while len(res) < count:
                        res.append(res[-1])
                    return res[:count], hl
            return defaults, def_hl

        def get_beat_duration(beat_id: int, default_dur: float) -> float:
            for b in spec.get("beats", []):
                if b.get("beat_id") == beat_id:
                    if "slot_duration" in b:
                        return float(b["slot_duration"])
                    if "audio_duration" in b:
                        return float(b["audio_duration"]) + 0.30
                    if "duration" in b:
                        return float(b["duration"])
            return default_dur

        def scale_times(target_dur: float, default_times: list) -> list:
            total_def = sum(default_times)
            if total_def <= 0:
                return default_times
            scale = target_dur / total_def
            return [max(0.15, round(t * scale, 3)) for t in default_times]

        meta = spec.get("metadata", {})

        def get_math_svg(index: int, default_svg: str, width: float = 6.4) -> Mobject:
            formulas = spec.get("math_formulas", [])
            if index < len(formulas):
                cand_name = formulas[index].get("filename", "")
                cand_path = PROJECT_ROOT / "public" / "math_svgs" / cand_name
                if cand_path.exists():
                    try:
                        return SVGMobject(str(cand_path)).scale_to_fit_width(width)
                    except Exception:
                        pass
            def_path = PROJECT_ROOT / "public" / "math_svgs" / default_svg
            if def_path.exists():
                try:
                    return SVGMobject(str(def_path)).scale_to_fit_width(width)
                except Exception:
                    pass
            fallback_text = formulas[index].get("latex", "") if index < len(formulas) else ""
            t = Text(fallback_text[:30], font=FONT_HELVETICA, font_size=20, color=WHITE)
            if t.width > width:
                t.scale_to_fit_width(width)
            return t

        def get_term_annotations_group(index: int, y_pos: float = 3.9) -> VGroup:
            formulas = spec.get("math_formulas", [])
            chips = []
            if index < len(formulas):
                ann_list = formulas[index].get("term_annotations", [])
                for item in ann_list[:2]:
                    term_str = item.get("term", "")
                    lbl_str = item.get("label", "")
                    if term_str and lbl_str:
                        # Clean LaTeX syntax for human-readable chip typography
                        term_clean = term_str.replace("{", "").replace("}", "").replace("\\tau", "τ").replace("\\theta", "θ").replace("\\lambda", "λ").replace("\\alpha", "α").replace("\\mu", "μ").replace("\\sigma", "σ")
                        lbl_clean = lbl_str.replace("{", "").replace("}", "")
                        chip_bg = RoundedRectangle(
                            width=3.4, height=0.46, corner_radius=0.1,
                            color="#334155", fill_color="#0A0D14", fill_opacity=0.88, stroke_width=1.0
                        )
                        chip_txt = Text(f"{term_clean}: {lbl_clean}", font=FONT_HELVETICA, font_size=13, color="#94A3B8")
                        if chip_txt.width > 3.2:
                            chip_txt.scale_to_fit_width(3.2)
                        chip_txt.move_to(chip_bg)
                        chips.append(VGroup(chip_bg, chip_txt))
            if not chips:
                return VGroup()
            if len(chips) == 1:
                chips[0].move_to([0.0, y_pos, 0.0])
                return VGroup(chips[0])
            chips[0].move_to([-1.9, y_pos, 0.0])
            chips[1].move_to([1.9, y_pos, 0.0])
            return VGroup(*chips)

        total_beats = len(spec.get("beats", []))
        is_latent_cluster = (
            meta.get("visual_metaphor") == "latent_clusters"
            or any(w in (spec.get("title", "") + " " + spec.get("id", "") + " " + spec.get("hook_tag", "")).lower()
                   for w in ["sae", "latent", "cluster", "interpret", "pos", "speech", "semantic", "embedding", "polysemantic", "morpho", "dictionary"])
        )

        # =====================================================================
        # BEAT 1: (The Hard Scale Mystery)
        # =====================================================================
        b1_parts, b1_hl = get_beat_parts(
            1, 3,
            ["Frontier AI models scale to massive complexity.", "Yet executing inference can be remarkably efficient.", "How?"],
            {"massive complexity": COLOR_MINT, "inference": "#38BDF8", "How?": COLOR_MINT}
        )

        b1_dur = get_beat_duration(1, 6.42)
        t1 = scale_times(b1_dur, [0.7, 1.8, 1.1, 1.2, 1.1, 0.52])

        tag_txt = spec.get("hook_tag", "FRONTIER AI ARCHITECTURE")
        title_txt = spec.get("title", "AI Architecture Breakdown")

        b1_tag = Text(tag_txt, font=FONT_HELVETICA, font_size=20, color=COLOR_SLATE, weight=BOLD).shift(UP * 5.6)
        
        import textwrap
        if len(title_txt) > 28:
            wrapped_title = textwrap.fill(title_txt, width=22)
            font_sz = 36 if len(title_txt) > 40 else 46
            b1_title = Text(wrapped_title, font=FONT_HELVETICA, font_size=font_sz, color=WHITE, weight=HEAVY).shift(UP * 4.4)
        else:
            b1_title = Text(title_txt, font=FONT_HELVETICA, font_size=56, color=WHITE, weight=HEAVY).shift(UP * 4.6)
        if b1_title.width > 7.4:
            b1_title.scale_to_fit_width(7.4)

        total_params_str = meta.get("scale_metric") or meta.get("total_parameters")
        if not total_params_str:
            import re
            m = re.search(r'\b(\d+[BKMkmb]?%?)\b', title_txt + " " + b1_parts[0])
            total_params_str = m.group(1) if m else "100%"

        import re
        match = re.search(r'\d+', total_params_str)
        target_num = int(match.group()) if match else 100
        unit = total_params_str.replace(str(target_num), "") if total_params_str else ""
        if not unit and "%" in total_params_str:
            unit = "%"

        counter_val = ValueTracker(0)
        counter_num = always_redraw(
            lambda: Text(
                f"{int(counter_val.get_value())}{unit}",
                font=FONT_HELVETICA,
                font_size=108,
                color=COLOR_MINT,
                weight=HEAVY
            ).shift(UP * 2.2)
        )
        
        counter_static_anchor = Text(f"{target_num}{unit}", font=FONT_HELVETICA, font_size=108, weight=HEAVY).shift(UP * 2.2)
        b1_brace = Brace(counter_static_anchor, DOWN, buff=0.25, color="#64748B")
        scale_label_txt = meta.get("scale_label", "Total Neural Complexity")
        b1_brace_txt = Text(scale_label_txt, font=FONT_HELVETICA, font_size=20, color="#E2E8F0", weight=MEDIUM).next_to(b1_brace, DOWN, buff=0.18)
        if b1_brace_txt.width > 7.2:
            b1_brace_txt.scale_to_fit_width(7.2)

        param_svg = get_math_svg(0, "sae_scale_dim.svg" if is_latent_cluster else "param_scale.svg", width=6.2).shift(DOWN * 0.4)
        b1_ann = get_term_annotations_group(0, y_pos=-1.2)
        hook_sub_txt = meta.get("hook_sub", b1_parts[1] if len(b1_parts) > 1 else "How does it scale?")
        hook_sub = Text(hook_sub_txt, font=FONT_HELVETICA, font_size=20, color="#FDE047", weight=BOLD).shift(DOWN * 2.2)
        if hook_sub.width > 7.4:
            hook_sub.scale_to_fit_width(7.4)

        self.play(
            FadeIn(b1_tag, shift=DOWN * 0.2),
            FadeIn(b1_title, shift=DOWN * 0.2),
            captions.show(b1_parts[0], b1_hl),
            run_time=t1[0]
        )
        self.add(counter_num)
        self.play(
            counter_val.animate.set_value(target_num),
            run_time=t1[1]
        )
        self.play(
            GrowFromCenter(b1_brace),
            FadeIn(b1_brace_txt, shift=UP * 0.2),
            FadeIn(param_svg, shift=UP * 0.3),
            FadeIn(b1_ann, shift=UP * 0.2),
            run_time=t1[2]
        )
        self.play(
            FadeIn(hook_sub, shift=UP * 0.3),
            captions.morph_to(b1_parts[1], b1_hl),
            self.camera.frame.animate.scale(0.96).shift(UP * 0.1),
            run_time=t1[3]
        )
        self.play(
            Circumscribe(param_svg, color="#FBBF24", stroke_width=2.5, time_width=0.6),
            Flash(counter_num, color=COLOR_MINT, line_length=0.3, num_lines=8),
            captions.morph_to(b1_parts[2], b1_hl),
            run_time=t1[4]
        )
        self.play(
            FadeOut(VGroup(b1_tag, b1_title, b1_brace, b1_brace_txt, param_svg, b1_ann, hook_sub)),
            FadeOut(counter_num),
            captions.hide(),
            self.camera.frame.animate.move_to(ORIGIN).set(width=FRAME_WIDTH, height=FRAME_HEIGHT),
            run_time=t1[5]
        )

        # =====================================================================
        # BEAT 2: (Dense Monolithic Bottleneck)
        # =====================================================================
        b2_parts, b2_hl = get_beat_parts(
            2, 4,
            ["In standard architectures,", "every token forces all representations", "to compute simultaneously.", "A massive computational bottleneck."],
            {"standard architectures": "#F87171", "computational bottleneck": COLOR_DANGER}
        )

        b2_dur = get_beat_duration(2, 9.28)
        t2 = scale_times(b2_dur, [0.8, 1.6, 0.7, 0.9, 1.8, 1.4, 1.58, 0.50])

        b2_title_txt = meta.get("bottleneck_title", "BASELINE ARCHITECTURAL BOTTLENECK")
        b2_title = Text(b2_title_txt, font=FONT_HELVETICA, font_size=24, color="#F87171", weight=HEAVY).shift(UP * 5.6)
        if b2_title.width > 7.4:
            b2_title.scale_to_fit_width(7.4)

        dense_math = get_math_svg(1, "sae_superposition.svg" if is_latent_cluster else "dense_matmul.svg", width=6.4).shift(UP * 4.6)
        b2_ann = get_term_annotations_group(1, y_pos=3.9)

        if is_latent_cluster:
            # Polysemantic Superposition & Vector Entanglement
            origin_pt = np.array([0.0, 0.4, 0.0])
            coord_plane = NumberPlane(
                x_range=[-3, 3, 1],
                y_range=[-3, 3, 1],
                x_length=5.6,
                y_length=5.2,
                background_line_style={"stroke_color": "#1E293B", "stroke_width": 1.0, "stroke_opacity": 0.6},
                axis_config={"color": "#334155", "stroke_width": 1.2}
            ).move_to(origin_pt)

            v_words_data = meta.get("visual_entities", {}).get("bottleneck_tokens")
            if v_words_data and isinstance(v_words_data, list):
                v_words = []
                for idx, item in enumerate(v_words_data[:4]):
                    raw_str = item.get("word") or item.get("name") or f"Feature {idx+1}"
                    clean_str = raw_str.replace("Token '", "").replace("'", "").replace('"', '').strip()
                    t_target = np.array(item.get("target", [2.0 if idx % 2 == 0 else -1.9, 1.4 if idx < 2 else -1.2, 0.0]))
                    t_col = item.get("color", "#EF4444")
                    v_words.append((f"Feature: {clean_str}", t_target, t_col))
            else:
                v_words = [
                    ("Feature: bank", np.array([2.0, 1.3, 0.0]), "#EF4444"),
                    ("Feature: run", np.array([-1.9, 1.3, 0.0]), "#F59E0B"),
                    ("Feature: model", np.array([1.8, -1.1, 0.0]), "#A855F7"),
                    ("Feature: train", np.array([-1.8, -1.1, 0.0]), "#38BDF8")
                ]
            arrows = []
            word_labels = []
            for w_text, target, col in v_words:
                arr = Arrow(start=origin_pt, end=target, color=col, stroke_width=2.5, buff=0.08)
                lbl = Text(w_text, font=FONT_HELVETICA, font_size=14, color=col)
                diff = target - origin_pt
                direction = diff / np.linalg.norm(diff)
                lbl.next_to(target, direction, buff=0.12)
                arrows.append(arr)
                word_labels.append(lbl)

            superpos_rings = VGroup(
                Circle(radius=0.9, color="#EF4444", stroke_width=1.5, stroke_opacity=0.6).move_to(origin_pt),
                Circle(radius=1.6, color="#EF4444", stroke_width=1.5, stroke_opacity=0.4).move_to(origin_pt),
                Circle(radius=2.3, color="#EF4444", stroke_width=1.5, stroke_opacity=0.25).move_to(origin_pt)
            )

            b2_brace = Brace(coord_plane, DOWN, buff=0.20, color="#64748B")
            b2_brace_label = meta.get("bottleneck_desc", "Failure of 1-to-1 Morpho-Syntactic Latent Mapping")
            b2_brace_txt = Text(b2_brace_label, font=FONT_HELVETICA, font_size=18, color=COLOR_DANGER, weight=HEAVY).next_to(b2_brace, DOWN, buff=0.12)
            if b2_brace_txt.width > 7.4:
                b2_brace_txt.scale_to_fit_width(7.4)

            self.play(FadeIn(b2_title, shift=DOWN * 0.2), FadeIn(dense_math, shift=DOWN * 0.2), FadeIn(b2_ann, shift=DOWN * 0.2), captions.show(b2_parts[0], b2_hl), run_time=t2[0])
            self.play(Create(coord_plane), FadeIn(superpos_rings), run_time=t2[1])
            self.play(
                LaggedStart(*[Create(a) for a in arrows], lag_ratio=0.1),
                LaggedStart(*[FadeIn(l) for l in word_labels], lag_ratio=0.1),
                captions.morph_to(b2_parts[1], b2_hl),
                run_time=t2[2] + t2[3]
            )
            self.play(
                superpos_rings.animate.scale(1.15).set_color("#DC2626"),
                GrowFromCenter(b2_brace),
                FadeIn(b2_brace_txt, shift=UP * 0.2),
                captions.morph_to(b2_parts[2], b2_hl),
                run_time=t2[4]
            )
            self.play(
                Circumscribe(superpos_rings, color=COLOR_DANGER, stroke_width=2.5, time_width=0.7),
                captions.morph_to(b2_parts[3], b2_hl),
                self.camera.frame.animate.scale(0.96).shift(DOWN * 0.1),
                run_time=t2[5]
            )
            self.play(Flash(b2_brace_txt, color=COLOR_DANGER, line_length=0.3, num_lines=8), run_time=t2[6])
            self.play(
                FadeOut(VGroup(b2_title, dense_math, b2_ann, coord_plane, superpos_rings, *arrows, *word_labels, b2_brace, b2_brace_txt)),
                captions.hide(),
                self.camera.frame.animate.move_to(ORIGIN).set(width=FRAME_WIDTH, height=FRAME_HEIGHT),
                run_time=t2[7]
            )
        else:
            # Bipartite Synaptic Neural Network (6 input nodes, 6 output nodes, 36 lines)
            in_nodes = []
            out_nodes = []
            synapses = []
            y_coords = [1.8, 1.1, 0.4, -0.3, -1.0, -1.7]

            for y in y_coords:
                in_dot = Dot(point=[-2.2, y, 0], radius=0.10, color="#38BDF8")
                out_dot = Dot(point=[2.2, y, 0], radius=0.10, color="#38BDF8")
                in_nodes.append(in_dot)
                out_nodes.append(out_dot)

            for idot in in_nodes:
                for odot in out_nodes:
                    line = Line(idot.get_center(), odot.get_center(), stroke_width=1.0, color="#334155")
                    synapses.append(line)

            synapse_net = VGroup(*synapses)
            network_group = VGroup(synapse_net, *in_nodes, *out_nodes)

            x_vec_label = Text("Input x", font=FONT_HELVETICA, font_size=18, color="#38BDF8", weight=BOLD).next_to(in_nodes[0], UP, buff=0.2)
            y_vec_label = Text("Output y", font=FONT_HELVETICA, font_size=18, color="#38BDF8", weight=BOLD).next_to(out_nodes[0], UP, buff=0.2)

            token_packet = Dot(point=[-3.8, 0.0, 0], radius=0.18, color="#00F0FF")
            token_label = Text('"token"', font=FONT_HELVETICA, font_size=16, color=WHITE, weight=BOLD).next_to(token_packet, LEFT, buff=0.12)
            token_group = VGroup(token_packet, token_label)

            b2_brace = Brace(network_group, DOWN, buff=0.25, color="#64748B")
            b2_brace_label = meta.get("bottleneck_desc", "Brute-Force Computational Bottleneck")
            b2_brace_txt = Text(b2_brace_label, font=FONT_HELVETICA, font_size=20, color=COLOR_DANGER, weight=HEAVY).next_to(b2_brace, DOWN, buff=0.15)
            if b2_brace_txt.width > 7.2:
                b2_brace_txt.scale_to_fit_width(7.2)
            
            dense_compute_svg = get_math_svg(2, "dense_compute.svg", width=5.8).next_to(b2_brace_txt, DOWN, buff=0.25)
            b2_bottleneck_txt = Text(b2_parts[1] if len(b2_parts) > 1 else "Quadratic Scaling Barrier", font=FONT_HELVETICA, font_size=17, color="#CBD5E1").next_to(dense_compute_svg, DOWN, buff=0.20)
            if b2_bottleneck_txt.width > 7.2:
                b2_bottleneck_txt.scale_to_fit_width(7.2)

            self.play(
                FadeIn(b2_title, shift=DOWN * 0.2),
                FadeIn(dense_math, shift=DOWN * 0.2),
                captions.show(b2_parts[0], b2_hl),
                run_time=t2[0]
            )
            self.play(Create(network_group, lag_ratio=0.01), FadeIn(x_vec_label), FadeIn(y_vec_label), run_time=t2[1])
            
            self.play(
                FadeIn(token_group, shift=RIGHT * 0.5),
                captions.morph_to(b2_parts[1], b2_hl),
                run_time=t2[2]
            )
            self.play(token_group.animate.shift(RIGHT * 1.6), run_time=t2[3])

            self.play(
                synapse_net.animate.set_color(COLOR_DANGER).set_stroke(width=2.2),
                *[d.animate.set_color("#EF4444") for d in in_nodes + out_nodes],
                GrowFromCenter(b2_brace),
                FadeIn(b2_brace_txt, shift=UP * 0.2),
                FadeIn(dense_compute_svg, shift=UP * 0.2),
                captions.morph_to(b2_parts[2], b2_hl),
                run_time=t2[4]
            )
            self.play(
                Circumscribe(network_group, color=COLOR_DANGER, stroke_width=2.5, time_width=0.7),
                captions.morph_to(b2_parts[3], b2_hl),
                self.camera.frame.animate.scale(0.96).shift(DOWN * 0.1),
                run_time=t2[5]
            )
            self.play(
                Flash(b2_brace_txt, color=COLOR_DANGER, line_length=0.3, num_lines=8),
                run_time=t2[6]
            )
            self.play(
                FadeOut(VGroup(
                    b2_title, dense_math, network_group, x_vec_label, y_vec_label,
                    token_group, b2_brace, b2_brace_txt, dense_compute_svg, b2_bottleneck_txt
                )),
                captions.hide(),
                self.camera.frame.animate.move_to(ORIGIN).set(width=FRAME_WIDTH, height=FRAME_HEIGHT),
                run_time=t2[7]
            )

        # =====================================================================
        # BEAT 3: (Modular Architecture Partition / Latent Constellation)
        # =====================================================================
        b3_parts, b3_hl = get_beat_parts(
            3, 2,
            ["The breakthrough decomposes this monolithic space,", "dividing into specialized sparse sub-networks."],
            {"breakthrough": COLOR_MINT, "specialized sparse": COLOR_MINT}
        )

        b3_dur = get_beat_duration(3, 7.80)
        t3 = scale_times(b3_dur, [0.8, 2.0, 1.2, 2.0, 1.30, 0.50])

        b3_title_txt = meta.get("solution_title", "MODULAR DECOMPOSED ARCHITECTURE")
        b3_title = Text(b3_title_txt, font=FONT_HELVETICA, font_size=24, color=COLOR_MINT, weight=HEAVY).shift(UP * 5.6)
        if b3_title.width > 7.4:
            b3_title.scale_to_fit_width(7.4)

        moe_partition_svg = get_math_svg(2, "sae_encoder_32k.svg" if is_latent_cluster else "moe_partition.svg", width=6.8).shift(UP * 4.6)
        b3_ann = get_term_annotations_group(2, y_pos=3.9)

        if is_latent_cluster:
            # Overcomplete Dictionary & Latent Feature Axes
            c_center = np.array([0.0, 0.5, 0.0])
            axis_x = Arrow(start=c_center + LEFT * 2.6, end=c_center + RIGHT * 2.6, color="#64748B", stroke_width=1.8, buff=0)
            axis_y = Arrow(start=c_center + DOWN * 1.8, end=c_center + UP * 2.0, color="#64748B", stroke_width=1.8, buff=0)
            axis_z = Arrow(start=c_center + [-1.6, -1.1, 0], end=c_center + [1.6, 1.3, 0], color="#38BDF8", stroke_width=2.2, buff=0)

            lbl_x = Text("Latent Axis D_1", font=FONT_HELVETICA, font_size=13, color="#94A3B8").next_to(axis_x.get_end(), RIGHT, buff=0.12)
            lbl_y = Text("Latent Axis D_2", font=FONT_HELVETICA, font_size=13, color="#94A3B8").next_to(axis_y.get_end(), UP, buff=0.12)
            lbl_z = Text("Overcomplete Basis D_k (k=32k)", font=FONT_HELVETICA, font_size=13, color="#38BDF8", weight=BOLD).next_to(axis_z.get_end(), UP * 0.6 + RIGHT * 0.1, buff=0.15)

            feature_pts = []
            feature_a = [c_center + [0.8 * i, 0.15 * (i % 2), 0] for i in range(-3, 4)]
            feature_b = [c_center + [0, 0.6 * i, 0] for i in range(-3, 4)]
            feature_c = [c_center + [0.5 * i, 0.42 * i, 0] for i in range(-3, 4)]
            all_pts = feature_a + feature_b + feature_c
            for pt in all_pts:
                dot = Dot(point=pt, radius=0.07, color="#334155")
                feature_pts.append(dot)
            feature_pts_group = VGroup(*feature_pts)

            b3_brace = Brace(VGroup(axis_x, axis_y, axis_z), DOWN, buff=0.25, color="#64748B")
            b3_components_label = meta.get("solution_components", "Distributed Geometric Feature Ensembles")
            b3_brace_txt = Text(b3_components_label, font=FONT_HELVETICA, font_size=18, color=COLOR_MINT, weight=BOLD).next_to(b3_brace, DOWN, buff=0.14)
            if b3_brace_txt.width > 7.4:
                b3_brace_txt.scale_to_fit_width(7.4)

            self.play(FadeIn(b3_title, shift=DOWN * 0.2), FadeIn(moe_partition_svg, shift=DOWN * 0.2), FadeIn(b3_ann, shift=DOWN * 0.2), captions.show(b3_parts[0], b3_hl), run_time=t3[0])
            self.play(Create(VGroup(axis_x, axis_y, axis_z)), FadeIn(VGroup(lbl_x, lbl_y, lbl_z)), run_time=t3[1])
            self.play(Create(feature_pts_group, lag_ratio=0.02), GrowFromCenter(b3_brace), FadeIn(b3_brace_txt, shift=UP * 0.2), captions.morph_to(b3_parts[1], b3_hl), run_time=t3[2])
            self.play(
                LaggedStart(*[d.animate.set_color(COLOR_MINT).scale(1.3) for d in feature_pts[::3]], lag_ratio=0.04),
                self.camera.frame.animate.scale(0.96).shift(UP * 0.1),
                run_time=t3[3]
            )
            self.play(
                self.camera.frame.animate.move_to(ORIGIN).set(width=FRAME_WIDTH, height=FRAME_HEIGHT),
                run_time=t3[4]
            )
            self.play(
                FadeOut(VGroup(b3_title, moe_partition_svg, b3_ann, axis_x, axis_y, axis_z, lbl_x, lbl_y, lbl_z, feature_pts_group, b3_brace, b3_brace_txt)),
                captions.hide(),
                run_time=t3[5]
            )
        else:
            # 256 Expert / Latent Constellation (16x16 micro-grid)
            expert_dots = []
            for i in range(256):
                r = i // 16
                c = i % 16
                x = (c - 7.5) * 0.36
                y = 2.2 - (r * 0.25)
                d = Dot(point=[x, y, 0], radius=0.065, color="#334155", fill_opacity=0.85)
                expert_dots.append(d)
            
            experts_constellation = VGroup(*expert_dots)

            b3_brace = Brace(experts_constellation, DOWN, buff=0.25, color="#64748B")
            b3_components_label = meta.get("solution_components", "High-Dimensional Latent Dictionary")
            b3_brace_txt = Text(b3_components_label, font=FONT_HELVETICA, font_size=21, color=COLOR_MINT, weight=BOLD).next_to(b3_brace, DOWN, buff=0.16)
            if b3_brace_txt.width > 7.2:
                b3_brace_txt.scale_to_fit_width(7.2)
            b3_sub_txt = b3_parts[1] if len(b3_parts) > 1 else "Sparse sub-networks decompose specialized representations"
            b3_sub = Text(b3_sub_txt, font=FONT_HELVETICA, font_size=17, color="#94A3B8").next_to(b3_brace_txt, DOWN, buff=0.18)
            if b3_sub.width > 7.4:
                b3_sub.scale_to_fit_width(7.4)

            self.play(
                FadeIn(b3_title, shift=DOWN * 0.2),
                FadeIn(moe_partition_svg, shift=DOWN * 0.2),
                FadeIn(b3_ann, shift=DOWN * 0.2),
                captions.show(b3_parts[0], b3_hl),
                run_time=t3[0]
            )
            self.play(Create(experts_constellation, lag_ratio=0.003), run_time=t3[1])
            self.play(
                GrowFromCenter(b3_brace),
                FadeIn(b3_brace_txt, shift=UP * 0.2),
                FadeIn(b3_sub, shift=UP * 0.2),
                captions.morph_to(b3_parts[1], b3_hl),
                run_time=t3[2]
            )
            self.play(
                self.camera.frame.animate.scale(0.95).shift(UP * 0.1),
                LaggedStart(
                    *[expert_dots[i].animate.set_color("#34D399").set_opacity(0.95) for i in range(0, 256, 8)],
                    lag_ratio=0.03
                ),
                run_time=t3[3]
            )
            self.play(
                *[expert_dots[i].animate.set_color("#334155").set_opacity(0.85) for i in range(0, 256, 8)],
                self.camera.frame.animate.move_to(ORIGIN).set(width=FRAME_WIDTH, height=FRAME_HEIGHT),
                run_time=t3[4]
            )
            self.play(
                FadeOut(VGroup(b3_title, moe_partition_svg, b3_ann, b3_brace, b3_brace_txt, b3_sub)),
                captions.hide(),
                run_time=t3[5]
            )

        if total_beats >= 7:
            # -------------------------------------------------------------
            # 7-BEAT LEGACY SPEC PATH
            # -------------------------------------------------------------
            b4_parts, b4_hl = get_beat_parts(
                4, 2,
                ["Plus one permanently active shared expert", "capturing universal knowledge."],
                {"shared expert": COLOR_GOLD, "universal knowledge": "#FDE68A"}
            )
            b4_dur = get_beat_duration(4, 5.44)
            t4 = scale_times(b4_dur, [0.6, 1.2, 2.0, 1.14, 0.50])

            b4_title = Text(meta.get("core_module_title", "SHARED FOUNDATION EXPERT"), font=FONT_HELVETICA, font_size=24, color=COLOR_GOLD, weight=HEAVY).shift(UP * 5.6)
            shared_math = get_math_svg(min(3, len(spec.get("math_formulas", []))-1), "shared_expert.svg", width=6.4).shift(UP * 4.6)
            
            shared_dot = Dot(point=[0, 3.1, 0], radius=0.28, color=COLOR_GOLD)
            shared_glyph = SVGMobject("public/math_svgs/es_glyph.svg").set_color("#0A0D14").scale_to_fit_height(0.28).move_to(shared_dot)
            shared_node = VGroup(shared_dot, shared_glyph)
            shared_auras = Circle(radius=0.45, color=COLOR_GOLD, stroke_width=1.8, stroke_opacity=0.85).move_to(shared_dot)
            shared_group = VGroup(shared_node, shared_auras)

            shared_desc = Text(b4_parts[0], font=FONT_HELVETICA, font_size=19, color="#FDE68A", weight=BOLD).shift(DOWN * 2.5)
            if shared_desc.width > 7.4:
                shared_desc.scale_to_fit_width(7.4)

            self.play(FadeIn(b4_title, shift=DOWN * 0.2), FadeIn(shared_math, shift=DOWN * 0.2), captions.show(b4_parts[0], b4_hl), run_time=t4[0])
            self.play(FadeIn(shared_group, shift=DOWN * 0.3), FadeIn(shared_desc, shift=UP * 0.2), captions.morph_to(b4_parts[1], b4_hl), run_time=t4[1])
            self.play(Indicate(shared_dot, color="#FDE047", scale_factor=1.12), run_time=t4[2])
            self.play(Flash(shared_dot, color=COLOR_GOLD, line_length=0.3, num_lines=8), run_time=t4[3])
            self.play(FadeOut(VGroup(b4_title, shared_math, shared_desc, shared_auras)), captions.hide(), shared_node.animate.move_to([1.5, 3.2, 0]), run_time=t4[4])

            # Beat 5: Routing & Top-8 Lasers
            b5_parts, b5_hl = get_beat_parts(
                5, 2,
                ["When a token enters, a router scores affinity,", "dispatching to only the top 8 experts."],
                {"token": "#00F0FF", "router": COLOR_MINT, "top 8 experts": COLOR_MINT}
            )
            b5_dur = get_beat_duration(5, 6.08)
            t5 = scale_times(b5_dur, [0.7, 0.7, 1.8, 1.88, 1.0])

            b5_title = Text(meta.get("mechanism_title", "DYNAMIC TOKEN ROUTING"), font=FONT_HELVETICA, font_size=24, color=COLOR_MINT, weight=HEAVY).shift(UP * 5.7)
            gating_math = get_math_svg(min(3, len(spec.get("math_formulas", []))-1), "gating_formula.svg", width=6.6).shift(UP * 4.8)

            token_node = Dot(point=[0, 3.95, 0], radius=0.15, color="#00F0FF")
            token_txt = Text('Token x', font=FONT_HELVETICA, font_size=17, color="#00F0FF", weight=BOLD).next_to(token_node, UP, buff=0.12)
            token_entry = VGroup(token_node, token_txt)

            router_center = Dot(point=[-1.5, 3.2, 0], radius=0.15, color=COLOR_MINT)
            router_tag = Text("Router", font=FONT_HELVETICA, font_size=15, color=COLOR_MINT, weight=BOLD).next_to(router_center, LEFT, buff=0.14)
            router_beam = Arrow(start=[0, 3.85, 0], end=[-1.35, 3.25, 0], buff=0.08, color="#38BDF8", stroke_width=2.2)
            router_group = VGroup(router_beam, router_center, router_tag)

            shared_tag = Text("Shared Expert", font=FONT_HELVETICA, font_size=15, color=COLOR_GOLD, weight=BOLD).next_to(shared_node, RIGHT, buff=0.14)
            shared_beam = Arrow(start=[0, 3.85, 0], end=[1.35, 3.25, 0], buff=0.08, color=COLOR_GOLD, stroke_width=2.2)

            top8_indices = [23, 55, 88, 116, 143, 180, 216, 249]
            lasers = []
            active_expert_dots = []
            for idx in top8_indices:
                target_pt = expert_dots[idx].get_center()
                active_dot = Dot(point=target_pt, radius=0.13, color=COLOR_MINT)
                active_expert_dots.append(active_dot)
                beam = Line(start=router_center.get_center(), end=target_pt, stroke_width=2.2, color=COLOR_MINT)
                lasers.append(beam)

            b5_label = Text(meta.get("payoff_badge", "Top 8 Experts Activated  •  248 Remain Dark"), font=FONT_HELVETICA, font_size=20, color="#38BDF8", weight=BOLD).shift(DOWN * 2.5)

            self.play(FadeIn(b5_title, shift=DOWN * 0.2), FadeIn(gating_math, shift=DOWN * 0.2), captions.show(b5_parts[0], b5_hl), run_time=t5[0])
            self.play(FadeIn(token_entry, shift=DOWN * 0.2), Create(router_group), Create(shared_beam), FadeIn(shared_tag, shift=LEFT * 0.1), run_time=t5[1])
            self.play(LaggedStart(*[Create(b) for b in lasers], lag_ratio=0.04), captions.morph_to(b5_parts[1], b5_hl), *[Transform(expert_dots[idx], active_expert_dots[i]) for i, idx in enumerate(top8_indices)], run_time=t5[2])
            unselected_dots = [expert_dots[i] for i in range(256) if i not in top8_indices]
            self.play(FadeIn(b5_label, shift=UP * 0.2), *[d.animate.set_color("#1E293B").set_opacity(0.30) for d in unselected_dots], Circumscribe(gating_math, color=COLOR_MINT, stroke_width=2.2), run_time=t5[3])
            self.play(Flash(router_center, color="#00F0FF", line_length=0.25, num_lines=8), run_time=t5[4])

            # Beat 6: Synthesis
            b6_parts, b6_hl = get_beat_parts(
                6, 3,
                ["The result? Full intelligence capacity,", "with only a sparse fraction active per token.", "Massive compute saved."],
                {"intelligence capacity": WHITE, "sparse fraction": COLOR_MINT, "compute saved": COLOR_MINT}
            )
            b6_dur = get_beat_duration(6, 9.37)
            t6 = scale_times(b6_dur, [0.60, 0.8, 1.2, 1.3, 1.8, 1.8, 1.37, 0.50])

            self.play(FadeOut(VGroup(b5_title, gating_math, token_entry, router_group, shared_node, shared_beam, shared_tag, b5_label, experts_constellation, *lasers, *active_expert_dots)), captions.hide(), self.camera.frame.animate.move_to(ORIGIN).set(width=FRAME_WIDTH, height=FRAME_HEIGHT), run_time=t6[0])

            b6_title = Text(meta.get("payoff_header", "MATHEMATICAL SYNTHESIS"), font=FONT_HELVETICA, font_size=24, color=COLOR_MINT, weight=HEAVY).shift(UP * 5.6)
            moe_output_svg = get_math_svg(min(3, len(spec.get("math_formulas", []))-1), "moe_output.svg", width=6.6).shift(UP * 4.6)
            active_params_str = meta.get("payoff_stat", meta.get("active_parameters", "37B"))
            hero_val = Text(active_params_str, font=FONT_HELVETICA, font_size=115, color=COLOR_MINT, weight=HEAVY).shift(UP * 2.2)
            b6_brace = Brace(hero_val, DOWN, buff=0.22, color="#64748B")
            b6_brace_txt = Text(meta.get("payoff_label", "Active Parameters Per Token"), font=FONT_HELVETICA, font_size=22, color=WHITE, weight=HEAVY).next_to(b6_brace, DOWN, buff=0.16)
            efficiency_svg = get_math_svg(min(4, len(spec.get("math_formulas", []))-1), "efficiency_math.svg", width=6.8).shift(DOWN * 0.4)
            flop_svg = get_math_svg(min(5, len(spec.get("math_formulas", []))-1), "flop_reduction.svg", width=6.2).shift(DOWN * 1.8)
            proof_sub = Text(meta.get("payoff_sub", "✓ Full Reasoning Capacity Intact"), font=FONT_HELVETICA, font_size=18, color="#94A3B8", weight=MEDIUM).shift(DOWN * 2.9)

            self.play(FadeIn(b6_title, shift=DOWN * 0.2), FadeIn(moe_output_svg, shift=DOWN * 0.2), captions.show(b6_parts[0], b6_hl), run_time=t6[1])
            self.play(FadeIn(hero_val, shift=UP * 0.3), Flash(hero_val, color=COLOR_MINT, line_length=0.4, num_lines=10), captions.morph_to(b6_parts[1], b6_hl), run_time=t6[2])
            self.play(GrowFromCenter(b6_brace), FadeIn(b6_brace_txt, shift=UP * 0.2), FadeIn(efficiency_svg, shift=UP * 0.2), run_time=t6[3])
            self.play(Circumscribe(efficiency_svg, color="#FDE047", stroke_width=2.5, time_width=0.6), FadeIn(flop_svg, shift=UP * 0.2), FadeIn(proof_sub, shift=UP * 0.2), captions.morph_to(b6_parts[2], b6_hl), run_time=t6[4])
            self.play(self.camera.frame.animate.scale(0.95).shift(DOWN * 0.2), Flash(efficiency_svg, color="#FDE047", line_length=0.3, num_lines=8), run_time=t6[5])
            self.play(Circumscribe(hero_val, color=COLOR_MINT, stroke_width=2.5), run_time=t6[6])
            self.play(FadeOut(VGroup(b6_title, moe_output_svg, hero_val, b6_brace, b6_brace_txt, efficiency_svg, flop_svg, proof_sub)), captions.hide(), self.camera.frame.animate.move_to(ORIGIN).set(width=FRAME_WIDTH, height=FRAME_HEIGHT), run_time=t6[7])

            # Beat 7: Outro
            b7_parts, b7_hl = get_beat_parts(
                7, 2,
                ["Follow The Model Verse", "for more deep architecture breakdowns."],
                {"The Model Verse": COLOR_MINT, "architecture breakdowns": WHITE}
            )
            b7_dur = get_beat_duration(7, 3.86)
            t7 = scale_times(b7_dur, [1.4, 1.7, 0.76])

            logo_icon, brand_text, outro_sub = create_chalkboard_brand_outro(
                logo_title="THE MODEL VERSE",
                tagline="Follow for more deep architecture breakdowns",
                url="themodelverse.in",
                y_center=0.4
            )
            self.play(Create(logo_icon, lag_ratio=0.08), FadeIn(brand_text, shift=DOWN * 0.3), FadeIn(outro_sub, shift=UP * 0.2), captions.show(b7_parts[0], b7_hl), run_time=t7[0])
            self.play(logo_icon.animate.rotate(TAU / 6), Circumscribe(brand_text[1], color=COLOR_MINT, stroke_width=2.2, time_width=0.6), captions.morph_to(b7_parts[1], b7_hl), self.camera.frame.animate.scale(0.97), run_time=t7[1])
            self.play(FadeOut(VGroup(logo_icon, brand_text, outro_sub)), captions.hide(), run_time=t7[2])

        else:
            # -------------------------------------------------------------
            # STANDARD 6-BEAT SPEC PATH
            # -------------------------------------------------------------
            # Beat 4: Dynamic Routing & Structured Latent Dispatch
            if is_latent_cluster:
                # Emergent Morpho-Syntactic Category Clusters (NOUNS, VERBS, CLOSED CLASS)
                b4_parts, b4_hl = get_beat_parts(
                    4, 2,
                    ["Dynamic sparse projection exposes compact latent clusters,", "cleanly partitioning open and closed word classes."],
                    {"sparse projection": COLOR_MINT, "compact latent clusters": "#38BDF8", "open and closed": COLOR_GOLD}
                )
                b4_dur = get_beat_duration(4, 7.0)
                t4 = scale_times(b4_dur, [0.8, 1.0, 1.8, 1.8, 1.1, 0.5])

                b4_title = Text(meta.get("mechanism_title", "OVERCOMPLETE SPARSE PROJECTION"), font=FONT_HELVETICA, font_size=23, color=COLOR_MINT, weight=HEAVY).shift(UP * 5.6)
                if b4_title.width > 7.4:
                    b4_title.scale_to_fit_width(7.4)

                gating_math = get_math_svg(3, "sae_pos_partition.svg" if is_latent_cluster else "gating_formula.svg", width=6.6).shift(UP * 4.6)
                b4_ann = get_term_annotations_group(3, y_pos=3.9)

                # Dynamic Category Cluster Envelopes
                clusters_meta = meta.get("visual_entities", {}).get("clusters")
                if clusters_meta and len(clusters_meta) >= 3:
                    c1_meta, c2_meta, c3_meta = clusters_meta[0], clusters_meta[1], clusters_meta[2]
                else:
                    c1_meta = {"name": "[NOUNS]", "color": "#38BDF8", "items": ["theory", "vector", "matrix"]}
                    c2_meta = {"name": "[VERBS]", "color": "#10B981", "items": ["scales", "learns", "encodes"]}
                    c3_meta = {"name": "[FUNCTION WORDS / CLOSED]", "color": "#F59E0B", "items": ["the", "in", "and"]}

                # Cluster 1 (Left, Cyan/Custom)
                c1_pos = np.array([-1.9, 1.2, 0.0])
                c1_col = c1_meta.get("color", "#38BDF8")
                c1_boundary = RoundedRectangle(width=2.8, height=2.4, corner_radius=0.4, color=c1_col, stroke_width=2.0).set_stroke(opacity=0.7).set_fill("#0E2A38", opacity=0.40).move_to(c1_pos)
                c1_tag = Text(c1_meta.get("name", "[NOUNS]"), font=FONT_HELVETICA, font_size=15, color=c1_col, weight=HEAVY).shift(c1_pos + UP * 0.9)
                if c1_tag.width > 2.6:
                    c1_tag.scale_to_fit_width(2.6)
                c1_items = c1_meta.get("items", ["theory", "vector", "matrix"])[:3]
                c1_offsets = [[-0.5, 0.3, 0], [0.5, 0.1, 0], [-0.2, -0.5, 0]]
                c1_words = [Text(str(w), font=FONT_HELVETICA, font_size=14, color=WHITE).shift(c1_pos + c1_offsets[i]) for i, w in enumerate(c1_items)]
                c1_dots = [Dot(w.get_left() + LEFT * 0.12, radius=0.06, color=c1_col) for w in c1_words]
                cluster_nouns = VGroup(c1_boundary, c1_tag, *c1_words, *c1_dots)

                # Cluster 2 (Right, Mint/Custom)
                c2_pos = np.array([1.9, 1.2, 0.0])
                c2_col = c2_meta.get("color", "#10B981")
                c2_boundary = RoundedRectangle(width=2.8, height=2.4, corner_radius=0.4, color=c2_col, stroke_width=2.0).set_stroke(opacity=0.7).set_fill("#06281E", opacity=0.40).move_to(c2_pos)
                c2_tag = Text(c2_meta.get("name", "[VERBS]"), font=FONT_HELVETICA, font_size=15, color=c2_col, weight=HEAVY).shift(c2_pos + UP * 0.9)
                if c2_tag.width > 2.6:
                    c2_tag.scale_to_fit_width(2.6)
                c2_items = c2_meta.get("items", ["scales", "learns", "encodes"])[:3]
                c2_offsets = [[-0.5, 0.3, 0], [0.5, 0.1, 0], [-0.2, -0.5, 0]]
                c2_words = [Text(str(w), font=FONT_HELVETICA, font_size=14, color=WHITE).shift(c2_pos + c2_offsets[i]) for i, w in enumerate(c2_items)]
                c2_dots = [Dot(w.get_left() + LEFT * 0.12, radius=0.06, color=c2_col) for w in c2_words]
                cluster_verbs = VGroup(c2_boundary, c2_tag, *c2_words, *c2_dots)

                # Cluster 3 (Bottom, Gold/Custom)
                c3_pos = np.array([0.0, -1.1, 0.0])
                c3_col = c3_meta.get("color", "#F59E0B")
                c3_boundary = RoundedRectangle(width=3.6, height=1.7, corner_radius=0.4, color=c3_col, stroke_width=2.0).set_stroke(opacity=0.7).set_fill("#2B1C05", opacity=0.40).move_to(c3_pos)
                c3_tag = Text(c3_meta.get("name", "[FUNCTION WORDS / CLOSED]"), font=FONT_HELVETICA, font_size=14, color=c3_col, weight=HEAVY).shift(c3_pos + UP * 0.55)
                if c3_tag.width > 3.4:
                    c3_tag.scale_to_fit_width(3.4)
                c3_items = c3_meta.get("items", ["the", "in", "and"])[:3]
                c3_offsets = [[-1.0, -0.15, 0], [0.0, -0.15, 0], [1.0, -0.15, 0]]
                c3_words = [Text(str(w), font=FONT_HELVETICA, font_size=14, color=WHITE).shift(c3_pos + c3_offsets[i]) for i, w in enumerate(c3_items)]
                c3_dots = [Dot(w.get_left() + LEFT * 0.12, radius=0.06, color=c3_col) for w in c3_words]
                cluster_closed = VGroup(c3_boundary, c3_tag, *c3_words, *c3_dots)

                clusters_group = VGroup(cluster_nouns, cluster_verbs, cluster_closed)

                # Incoming Unseen Token
                in_token_meta = meta.get("visual_entities", {}).get("incoming_token") or {}
                raw_label = in_token_meta.get("label", 'Token: "converges"')
                clean_label = raw_label.replace('"', '').replace("'", "")
                token_val_str = in_token_meta.get("token", 'converges').replace('"', '').replace("'", "")

                token_pill = RoundedRectangle(width=2.8, height=0.55, corner_radius=0.14, color="#34D399", fill_color="#06281E", fill_opacity=0.92, stroke_width=1.8).move_to([0.0, 3.2, 0.0])
                token_txt = Text(clean_label, font=FONT_HELVETICA, font_size=14, color=WHITE).move_to(token_pill)
                if token_txt.width > 2.6:
                    token_txt.scale_to_fit_width(2.6)
                token_entry = VGroup(token_pill, token_txt)

                # Dynamic projection arrow: from token pill straight into the [VERBS] cluster centroid
                proj_arrow = Arrow(start=[0.6, 2.9, 0], end=[1.4, 1.7, 0], buff=0.10, color="#34D399", stroke_width=2.5)

                new_verb_dot = Dot(point=[1.9, 0.45, 0], radius=0.08, color="#34D399")
                new_verb_txt = Text(token_val_str, font=FONT_HELVETICA, font_size=14, color="#34D399", weight=BOLD).next_to(new_verb_dot, RIGHT, buff=0.10)
                new_verb_item = VGroup(new_verb_dot, new_verb_txt)

                b4_label_txt = meta.get("payoff_badge", "✓ Emergent Morpho-Syntactic Categorization")
                b4_label = Text(b4_label_txt, font=FONT_HELVETICA, font_size=17, color="#38BDF8", weight=BOLD).shift(DOWN * 2.6)
                if b4_label.width > 7.4:
                    b4_label.scale_to_fit_width(7.4)

                self.play(FadeIn(b4_title, shift=DOWN * 0.2), FadeIn(gating_math, shift=DOWN * 0.2), FadeIn(b4_ann, shift=DOWN * 0.2), captions.show(b4_parts[0], b4_hl), run_time=t4[0])
                self.play(FadeIn(clusters_group, lag_ratio=0.15), run_time=t4[1])
                self.play(FadeIn(token_entry, shift=DOWN * 0.2), run_time=t4[2])
                self.play(
                    Create(proj_arrow),
                    token_entry.animate.move_to([1.9, 1.7, 0]).scale(0.80),
                    c2_boundary.animate.set_stroke(color="#34D399", width=3.5).set_fill("#06281E", opacity=0.7),
                    FadeIn(new_verb_item, shift=UP * 0.2),
                    captions.morph_to(b4_parts[1], b4_hl),
                    run_time=t4[3]
                )
                self.play(
                    Flash(new_verb_dot, color="#34D399", line_length=0.25, num_lines=8),
                    FadeIn(b4_label, shift=UP * 0.2),
                    Circumscribe(cluster_verbs, color=COLOR_MINT, stroke_width=2.2),
                    run_time=t4[4]
                )
                self.play(
                    FadeOut(VGroup(b4_title, gating_math, b4_ann, clusters_group, token_entry, proj_arrow, new_verb_item, b4_label)),
                    captions.hide(),
                    run_time=t4[5]
                )
            else:
                # (Standard MoE Router with Anti-Collision Guard)
                b4_parts, b4_hl = get_beat_parts(
                    4, 2,
                    ["Dynamic projection scores input tokens,", "dispatching representations to specialized active groups."],
                    {"Dynamic projection": COLOR_MINT, "specialized active groups": COLOR_MINT}
                )
                b4_dur = get_beat_duration(4, 7.0)
                t4 = scale_times(b4_dur, [0.8, 1.0, 2.0, 2.0, 0.7, 0.5])

                b4_title = Text(meta.get("mechanism_title", "DYNAMIC ROUTING & DISPATCH"), font=FONT_HELVETICA, font_size=24, color=COLOR_MINT, weight=HEAVY).shift(UP * 5.7)
                if b4_title.width > 7.4:
                    b4_title.scale_to_fit_width(7.4)

                gating_math = get_math_svg(3, "gating_formula.svg", width=6.6).shift(UP * 4.8)
                b4_ann = get_term_annotations_group(3, y_pos=4.1)

                token_node = Dot(point=[-1.4, 3.8, 0], radius=0.15, color="#00F0FF")
                token_txt = Text('Input x', font=FONT_HELVETICA, font_size=15, color="#00F0FF", weight=BOLD).next_to(token_node, LEFT, buff=0.15)
                token_entry = VGroup(token_node, token_txt)

                router_center = Dot(point=[-1.4, 3.1, 0], radius=0.16, color=COLOR_MINT)
                router_tag_bg = RoundedRectangle(width=1.8, height=0.5, corner_radius=0.1, color="#1E293B", fill_color="#0A0D14", fill_opacity=0.9, stroke_width=1.0).next_to(router_center, LEFT, buff=0.15)
                router_tag = Text("Router", font=FONT_HELVETICA, font_size=15, color=COLOR_MINT, weight=BOLD).move_to(router_tag_bg)
                router_beam = Arrow(start=[-1.4, 3.7, 0], end=[-1.4, 3.25, 0], buff=0.08, color="#38BDF8", stroke_width=2.2)
                router_group = VGroup(router_beam, router_center, router_tag_bg, router_tag)

                active_indices = [23, 55, 88, 116, 143, 180, 216, 249]
                lasers = []
                active_expert_dots = []
                for idx in active_indices:
                    target_pt = expert_dots[idx].get_center()
                    active_dot = Dot(point=target_pt, radius=0.13, color=COLOR_MINT)
                    active_expert_dots.append(active_dot)
                    beam = Line(start=router_center.get_center(), end=target_pt, stroke_width=2.2, color=COLOR_MINT)
                    lasers.append(beam)

                b4_label_txt = meta.get("payoff_badge", "Sparse Structured Features Activated")
                b4_label = Text(b4_label_txt, font=FONT_HELVETICA, font_size=20, color="#38BDF8", weight=BOLD).shift(DOWN * 2.5)
                if b4_label.width > 7.4:
                    b4_label.scale_to_fit_width(7.4)

                self.play(FadeIn(b4_title, shift=DOWN * 0.2), FadeIn(gating_math, shift=DOWN * 0.2), FadeIn(b4_ann, shift=DOWN * 0.2), captions.show(b4_parts[0], b4_hl), run_time=t4[0])
                self.play(FadeIn(token_entry, shift=DOWN * 0.2), Create(router_group), run_time=t4[1])
                self.play(LaggedStart(*[Create(b) for b in lasers], lag_ratio=0.04), captions.morph_to(b4_parts[1], b4_hl), *[Transform(expert_dots[idx], active_expert_dots[i]) for i, idx in enumerate(active_indices)], run_time=t4[2])
                unselected_dots = [expert_dots[i] for i in range(256) if i not in active_indices]
                self.play(FadeIn(b4_label, shift=UP * 0.2), *[d.animate.set_color("#1E293B").set_opacity(0.30) for d in unselected_dots], Circumscribe(gating_math, color=COLOR_MINT, stroke_width=2.2), run_time=t4[3])
                self.play(Flash(router_center, color="#00F0FF", line_length=0.25, num_lines=8), run_time=t4[4])
                self.play(FadeOut(VGroup(b4_title, gating_math, b4_ann, token_entry, router_group, b4_label, experts_constellation, *lasers, *active_expert_dots)), captions.hide(), run_time=t4[5])

            # Beat 5: Output Synthesis & Payoff
            b5_parts, b5_hl = get_beat_parts(
                5, 2,
                ["The empirical outcome delivers massive gains:", "High interpretability and extreme compute efficiency."],
                {"massive gains": COLOR_MINT, "compute efficiency": COLOR_GOLD}
            )
            b5_dur = get_beat_duration(5, 8.5)
            t5 = scale_times(b5_dur, [0.8, 1.2, 1.8, 2.2, 1.5, 0.50])

            b5_title = Text(meta.get("payoff_header", "MATHEMATICAL SYNTHESIS"), font=FONT_HELVETICA, font_size=24, color=COLOR_MINT, weight=HEAVY).shift(UP * 5.6)
            if b5_title.width > 7.4:
                b5_title.scale_to_fit_width(7.4)

            moe_output_svg = get_math_svg(4, "sae_recovery_metric.svg" if is_latent_cluster else "moe_output.svg", width=6.6).shift(UP * 4.6)
            b5_ann = get_term_annotations_group(4, y_pos=3.9)

            if is_latent_cluster:
                # Dynamic Dual Accuracy Bar Chart comparing SAE Latents vs Dense Baseline
                chart = create_dual_accuracy_bar_chart(
                    hero_label="Sparse SAE Latents",
                    hero_val=98.2,
                    base_label="Dense Baseline",
                    base_val=41.5,
                    unit="%",
                    delta_label="⚡ +56.7% SYNTACTIC RECOVERY GAIN",
                    chart_width=6.6,
                    max_height=2.0,
                    y_base=0.4
                )
                efficiency_svg = get_math_svg(5, "sae_loss.svg", width=6.6).shift(DOWN * 1.5)
                proof_sub_txt = meta.get("payoff_sub", "✓ Generalization Confirmed Across 10,000+ Held-Out Tokens")
                proof_sub = Text(proof_sub_txt, font=FONT_HELVETICA, font_size=15, color="#94A3B8").shift(DOWN * 2.8)
                if proof_sub.width > 7.4:
                    proof_sub.scale_to_fit_width(7.4)

                self.play(FadeIn(b5_title, shift=DOWN * 0.2), FadeIn(moe_output_svg, shift=DOWN * 0.2), FadeIn(b5_ann, shift=DOWN * 0.2), captions.show(b5_parts[0], b5_hl), run_time=t5[0])
                self.play(
                    Create(chart["axis"]),
                    FadeIn(chart["base_sub"]),
                    FadeIn(chart["hero_sub"]),
                    GrowFromEdge(chart["base_bar"], DOWN),
                    FadeIn(chart["base_val"], shift=UP * 0.1),
                    GrowFromEdge(chart["hero_bar"], DOWN),
                    FadeIn(chart["hero_val"], shift=UP * 0.1),
                    FadeIn(chart["delta"], shift=DOWN * 0.2),
                    FadeIn(efficiency_svg, shift=UP * 0.2),
                    FadeIn(proof_sub, shift=UP * 0.2),
                    captions.morph_to(b5_parts[1], b5_hl),
                    run_time=t5[1] + t5[2]
                )
                self.play(
                    Circumscribe(chart["hero_bar"], color="#34D399", stroke_width=2.5, time_width=0.6),
                    Flash(chart["hero_val"], color="#34D399", line_length=0.3, num_lines=8),
                    run_time=t5[3]
                )
                self.play(
                    self.camera.frame.animate.scale(0.96).shift(DOWN * 0.1),
                    Circumscribe(efficiency_svg, color="#FDE047", stroke_width=2.0, time_width=0.6),
                    run_time=t5[4]
                )
                self.play(
                    FadeOut(VGroup(b5_title, moe_output_svg, b5_ann, chart["full_group"], efficiency_svg, proof_sub)),
                    captions.hide(),
                    self.camera.frame.animate.move_to(ORIGIN).set(width=FRAME_WIDTH, height=FRAME_HEIGHT),
                    run_time=t5[5]
                )
            else:
                payoff_stat_str = meta.get("payoff_stat", meta.get("active_parameters", "95%"))
                hero_val = Text(payoff_stat_str, font=FONT_HELVETICA, font_size=108, color=COLOR_MINT, weight=HEAVY).shift(UP * 2.2)
                if hero_val.width > 7.0:
                    hero_val.scale_to_fit_width(7.0)

                b5_brace = Brace(hero_val, DOWN, buff=0.22, color="#64748B")
                b5_brace_label = meta.get("payoff_label", "Measured Empirical Gain")
                b5_brace_txt = Text(b5_brace_label, font=FONT_HELVETICA, font_size=22, color=WHITE, weight=HEAVY).next_to(b5_brace, DOWN, buff=0.16)
                if b5_brace_txt.width > 7.2:
                    b5_brace_txt.scale_to_fit_width(7.2)

                efficiency_svg = get_math_svg(5, "efficiency_math.svg", width=6.8).shift(DOWN * 0.4)
                proof_sub_txt = meta.get("payoff_sub", "✓ Rigorous Empirical Grounding Intact")
                proof_sub = Text(proof_sub_txt, font=FONT_HELVETICA, font_size=18, color="#94A3B8", weight=MEDIUM).shift(DOWN * 2.5)
                if proof_sub.width > 7.4:
                    proof_sub.scale_to_fit_width(7.4)

                self.play(FadeIn(b5_title, shift=DOWN * 0.2), FadeIn(moe_output_svg, shift=DOWN * 0.2), FadeIn(b5_ann, shift=DOWN * 0.2), captions.show(b5_parts[0], b5_hl), run_time=t5[0])
                self.play(FadeIn(hero_val, shift=UP * 0.3), Flash(hero_val, color=COLOR_MINT, line_length=0.4, num_lines=10), captions.morph_to(b5_parts[1], b5_hl), run_time=t5[1])
                self.play(GrowFromCenter(b5_brace), FadeIn(b5_brace_txt, shift=UP * 0.2), FadeIn(efficiency_svg, shift=UP * 0.2), run_time=t5[2])
                self.play(Circumscribe(efficiency_svg, color="#FDE047", stroke_width=2.5, time_width=0.6), FadeIn(proof_sub, shift=UP * 0.2), run_time=t5[3])
                self.play(self.camera.frame.animate.scale(0.95).shift(DOWN * 0.1), Flash(efficiency_svg, color="#FDE047", line_length=0.3, num_lines=8), run_time=t5[4])
                self.play(FadeOut(VGroup(b5_title, moe_output_svg, b5_ann, hero_val, b5_brace, b5_brace_txt, efficiency_svg, proof_sub)), captions.hide(), self.camera.frame.animate.move_to(ORIGIN).set(width=FRAME_WIDTH, height=FRAME_HEIGHT), run_time=t5[5])

            # Beat 6: Chalkboard Brand Outro
            b6_parts, b6_hl = get_beat_parts(
                6, 2,
                ["Follow The Model Verse", "for the engineering behind modern AI architectures."],
                {"The Model Verse": COLOR_MINT, "modern AI architectures": WHITE}
            )
            b6_dur = get_beat_duration(6, 4.2)
            t6 = scale_times(b6_dur, [1.4, 2.0, 0.8])

            logo_icon, brand_text, outro_sub = create_chalkboard_brand_outro(
                logo_title="THE MODEL VERSE",
                tagline="Follow for more deep architecture breakdowns",
                url="themodelverse.in",
                y_center=0.4
            )
            self.play(Create(logo_icon, lag_ratio=0.08), FadeIn(brand_text, shift=DOWN * 0.3), FadeIn(outro_sub, shift=UP * 0.2), captions.show(b6_parts[0], b6_hl), run_time=t6[0])
            self.play(logo_icon.animate.rotate(TAU / 6), Circumscribe(brand_text[1], color=COLOR_MINT, stroke_width=2.2, time_width=0.6), captions.morph_to(b6_parts[1], b6_hl), self.camera.frame.animate.scale(0.97), run_time=t6[1])
            self.play(FadeOut(VGroup(logo_icon, brand_text, outro_sub)), captions.hide(), run_time=t6[2])
