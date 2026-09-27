"""
The Model Verse — Mechanism Deep Dive Scene (e.g. KV Cache, Attention O(N²))
Parametric Manim scene explaining core AI engineering primitives with
intuitive visual memory models and throughput metrics.
"""

import os
import json
from manim import *
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from manim_engine.base_scene import BaseShortScene
from manim_engine.primitives.tech_card import create_tech_card, create_badge
from manim_engine.primitives.outro_card import create_chalkboard_brand_outro
from manim_engine.primitives.chalkboard_captions import ChalkboardCaptions
from pipeline.config import FONT_HELVETICA, COLOR_MINT, COLOR_DANGER, COLOR_GOLD, COLOR_SLATE

class MechanismDeepDiveScene(BaseShortScene):
    def construct(self):
        self.setup_canvas("MECHANISM DEEP DIVE")
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

        # -----------------------------------------------------------------
        # BEAT 1: (Hook: The Performance Bottleneck Mystery)
        # -----------------------------------------------------------------
        b1_parts, b1_hl = get_beat_parts(
            1, 2,
            ["Why does generating long text", "slow LLMs down to a crawl?"],
            {"long text": COLOR_GOLD, "slow LLMs": COLOR_DANGER}
        )

        b1_dur = get_beat_duration(1, 4.45)
        t1 = scale_times(b1_dur, [0.8, 1.2, 1.3, 0.7, 0.45])

        tag_txt = spec.get("hook_tag", "AI INFERENCE BOTTLENECK")
        title_txt = spec.get("title", "Why Are LLMs Slow?")

        import textwrap
        if len(title_txt) > 28:
            wrapped_title = textwrap.fill(title_txt, width=22)
            font_sz = 34 if len(title_txt) > 42 else 40
            hook_title = Text(wrapped_title, font=FONT_HELVETICA, font_size=font_sz, color=WHITE, weight=HEAVY).shift(UP * 4.3)
        else:
            hook_title = Text(title_txt, font=FONT_HELVETICA, font_size=52, color=WHITE, weight=HEAVY).shift(UP * 4.6)
        if hook_title.width > 7.4:
            hook_title.scale_to_fit_width(7.4)

        tag = Text(tag_txt, font=FONT_HELVETICA, font_size=18, color=COLOR_SLATE, weight=BOLD).shift(UP * 5.6)

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

        b1_brace_label = meta.get("bottleneck_label") or meta.get("scale_label") or ("Tensor Core Underutilization" if "flashattention" in spec.get("id", "").lower() else "Quadratic Attention Trap")
        hook_sub_str = meta.get("hook_sub") or (b1_parts[1] if len(b1_parts) > 1 else "Every new token recalculates all history")

        on2_glyph = SVGMobject("public/math_svgs/on2_glyph.svg").scale_to_fit_width(3.2).shift(UP * 2.1)
        b1_brace = Brace(on2_glyph, DOWN, buff=0.22, color="#64748B")
        b1_brace_txt = Text(b1_brace_label, font=FONT_HELVETICA, font_size=19, color="#FECDD3", weight=BOLD).next_to(b1_brace, DOWN, buff=0.15)
        if b1_brace_txt.width > 7.2:
            b1_brace_txt.scale_to_fit_width(7.2)

        attn_formula = get_math_svg(0, "attention_formula.svg", width=6.8).shift(DOWN * 0.4)
        qkt_dim = get_math_svg(1, "qkt_dim.svg", width=6.2).shift(DOWN * 1.8)
        hook_sub = Text(hook_sub_str, font=FONT_HELVETICA, font_size=18, color="#94A3B8", weight=MEDIUM).shift(DOWN * 2.8)
        if hook_sub.width > 7.4:
            hook_sub.scale_to_fit_width(7.4)

        b1_all = VGroup(tag, hook_title, on2_glyph, b1_brace, b1_brace_txt, attn_formula, qkt_dim, hook_sub)

        self.play(
            FadeIn(tag, shift=DOWN * 0.3),
            FadeIn(hook_title, shift=DOWN * 0.3),
            captions.show(b1_parts[0], b1_hl),
            run_time=t1[0]
        )
        self.play(
            DrawBorderThenFill(on2_glyph),
            FadeIn(b1_brace),
            FadeIn(b1_brace_txt),
            run_time=t1[1]
        )
        self.play(
            FadeIn(attn_formula, shift=UP * 0.2),
            FadeIn(qkt_dim, shift=UP * 0.2),
            Circumscribe(on2_glyph, color=COLOR_DANGER, stroke_width=3.5),
            captions.morph_to(b1_parts[1], b1_hl),
            self.camera.frame.animate.scale(0.96),
            run_time=t1[2]
        )
        self.play(
            Flash(on2_glyph, color=COLOR_DANGER, line_length=0.35, num_lines=8),
            FadeIn(hook_sub),
            run_time=t1[3]
        )
        self.play(FadeOut(b1_all), captions.hide(), self.camera.frame.animate.scale(1 / 0.96), run_time=t1[4])

        # -----------------------------------------------------------------
        # BEAT 2: (The Memory / Compute Bottleneck)
        # -----------------------------------------------------------------
        b2_parts, b2_hl = get_beat_parts(
            2, 3,
            ["In raw self-attention,", "generating each word recalculates history.", "That's an O(N²) memory explosion."],
            {"raw self-attention": WHITE, "recalculates history": COLOR_DANGER, "O(N²)": COLOR_DANGER, "memory explosion": COLOR_DANGER}
        )

        b2_dur = get_beat_duration(2, 9.50)
        t2 = scale_times(b2_dur, [1.8, 2.2, 2.4, 2.4, 0.7])

        cat_title_txt = meta.get("bottleneck_title", "THE ARCHITECTURAL BOTTLENECK")
        cat_title = Text(cat_title_txt, font=FONT_HELVETICA, font_size=22, color=COLOR_DANGER, weight=BOLD).shift(UP * 5.2)
        if cat_title.width > 7.4:
            cat_title.scale_to_fit_width(7.4)

        b2_math = get_math_svg(1, "qkt_dim.svg", width=6.2).shift(UP * 4.3)
        b2_ann = get_term_annotations_group(1, y_pos=3.7)

        # 6x6 Matrix showing redundant token-to-token quadratic growth
        matrix_cells = []
        for r in range(6):
            for c in range(6):
                x = (c - 2.5) * 0.82
                y = 2.6 - (r * 0.82)
                cell = RoundedRectangle(
                    corner_radius=0.08, width=0.68, height=0.68,
                    color="#334155", fill_color="#1E293B", fill_opacity=0.6, stroke_width=1.0
                ).move_to([x, y, 0])
                matrix_cells.append(cell)
        matrix_grid = VGroup(*matrix_cells)

        recalc_pill = create_tech_card(width=7.4, height=1.1, border_color=COLOR_DANGER, stroke_width=2.0).shift(DOWN * 2.9)
        recalc_str = meta.get("bottleneck_desc") or ("⚠️ MEMORY BANDWIDTH & COMPUTE LIMITS" if "flashattention" in spec.get("id", "").lower() else "⚠️ RECOMPUTING REDUNDANT STATES AT SCALE")
        recalc_txt = Text(recalc_str, font=FONT_HELVETICA, font_size=17, color=COLOR_DANGER, weight=HEAVY).move_to(recalc_pill)
        if recalc_txt.width > 7.0:
            recalc_txt.scale_to_fit_width(7.0)
        recalc_grp = VGroup(recalc_pill, recalc_txt)

        b2_all = VGroup(cat_title, b2_math, b2_ann, matrix_grid, recalc_grp)

        self.play(
            FadeIn(cat_title, shift=DOWN * 0.3),
            FadeIn(b2_math, shift=DOWN * 0.2),
            FadeIn(b2_ann, shift=DOWN * 0.2),
            Create(matrix_grid, lag_ratio=0.015),
            captions.show(b2_parts[0], b2_hl),
            run_time=t2[0]
        )
        self.play(
            matrix_grid.animate.set_color(COLOR_DANGER).set_fill("#881337", opacity=0.85),
            FadeIn(recalc_grp, shift=UP * 0.3),
            captions.morph_to(b2_parts[1], b2_hl),
            run_time=t2[1]
        )
        self.play(
            Circumscribe(matrix_grid, color=COLOR_DANGER, stroke_width=3.5),
            captions.morph_to(b2_parts[2], b2_hl),
            self.camera.frame.animate.scale(0.95),
            run_time=t2[2]
        )
        self.play(
            Flash(recalc_pill, color=COLOR_DANGER, line_length=0.3, num_lines=8),
            run_time=t2[3]
        )
        self.play(FadeOut(b2_all), captions.hide(), self.camera.frame.animate.scale(1 / 0.95), run_time=t2[4])

        # -----------------------------------------------------------------
        # BEAT 3: (The Architecture Solution)
        # -----------------------------------------------------------------
        b3_parts, b3_hl = get_beat_parts(
            3, 2,
            ["Enter the Key-Value Cache.", "Storing past keys & values in GPU VRAM."],
            {"Key-Value Cache": COLOR_MINT, "GPU VRAM": COLOR_MINT, "keys & values": COLOR_GOLD}
        )

        b3_dur = get_beat_duration(3, 7.60)
        t3 = scale_times(b3_dur, [1.6, 2.4, 2.0, 1.6])

        b3_title_str = meta.get("solution_title") or ("THE SOLUTION: ASYNC HOPPER TMA" if "flashattention" in spec.get("id", "").lower() else "THE SOLUTION: HIGH-SPEED CACHING")
        solution_title = Text(b3_title_str, font=FONT_HELVETICA, font_size=22, color=COLOR_MINT, weight=BOLD).shift(UP * 5.2)
        if solution_title.width > 7.4:
            solution_title.scale_to_fit_width(7.4)

        b3_math = get_math_svg(2, "block_query.svg", width=6.4).shift(UP * 4.3)
        b3_ann = get_term_annotations_group(2, y_pos=3.7)

        vram_box = RoundedRectangle(
            corner_radius=0.18, width=7.4, height=4.2,
            color=COLOR_MINT, fill_color="#064E3B", fill_opacity=0.25, stroke_width=2.2
        ).shift(UP * 1.3)
        vram_label_str = meta.get("solution_components") or ("⚡ ASYNC TENSOR CORES & HOPPER TMA" if "flashattention" in spec.get("id", "").lower() else "⚡ HIGH-SPEED MEMORY PRIMITIVE")
        vram_label = Text(vram_label_str, font=FONT_HELVETICA, font_size=18, color="#A7F3D0", weight=HEAVY).shift(UP * 3.0)
        if vram_label.width > 7.0:
            vram_label.scale_to_fit_width(7.0)

        slots = []
        for i in range(5):
            slot_box = RoundedRectangle(corner_radius=0.1, width=1.2, height=1.6, color="#10B981", fill_color="#0F172A", fill_opacity=0.9, stroke_width=1.5).shift(LEFT * 2.6 + RIGHT * (i * 1.3) + UP * 1.2)
            k_txt = Text(f"K{i+1}", font=FONT_HELVETICA, font_size=18, color="#38BDF8", weight=BOLD).next_to(slot_box.get_top(), DOWN, buff=0.2)
            v_txt = Text(f"V{i+1}", font=FONT_HELVETICA, font_size=18, color=COLOR_GOLD, weight=BOLD).next_to(k_txt, DOWN, buff=0.2)
            slots.append(VGroup(slot_box, k_txt, v_txt))
        slots_grp = VGroup(*slots)

        b3_all = VGroup(solution_title, b3_math, b3_ann, vram_box, vram_label, slots_grp)

        self.play(
            FadeIn(solution_title),
            FadeIn(b3_math, shift=DOWN * 0.2),
            FadeIn(b3_ann, shift=DOWN * 0.2),
            DrawBorderThenFill(vram_box),
            FadeIn(vram_label),
            captions.show(b3_parts[0], b3_hl),
            run_time=t3[0]
        )
        self.play(
            LaggedStart(*[FadeIn(s, shift=DOWN * 0.3) for s in slots], lag_ratio=0.15),
            captions.morph_to(b3_parts[1], b3_hl),
            run_time=t3[1]
        )
        self.play(
            Circumscribe(vram_box, color=COLOR_MINT, stroke_width=3.5),
            self.camera.frame.animate.scale(0.96),
            run_time=t3[2]
        )
        self.play(Flash(vram_box, color=COLOR_MINT, line_length=0.25, num_lines=8), run_time=t3[3])

        # -----------------------------------------------------------------
        # BEAT 4: (Step-by-Step Execution Pipeline)
        # -----------------------------------------------------------------
        b4_parts, b4_hl = get_beat_parts(
            4, 2,
            ["New token projects a single Query vector,", "fetching prior context in O(1) time."],
            {"Query vector": "#00F0FF", "O(1) time": COLOR_MINT}
        )

        b4_dur = get_beat_duration(4, 7.70)
        t4 = scale_times(b4_dur, [1.2, 2.2, 2.2, 1.6, 0.5])

        b4_math = get_math_svg(3, "online_softmax_running_max.svg", width=6.4).shift(UP * 4.3)
        b4_ann = get_term_annotations_group(3, y_pos=3.7)

        q_capsule = RoundedRectangle(
            corner_radius=0.14, width=4.4, height=0.75,
            color="#00F0FF", fill_color="#0284C7", fill_opacity=0.4, stroke_width=2.2
        ).shift(DOWN * 2.0)
        q_label_str = meta.get("mechanism_step") or ("Warp Specialization: TMA Load" if "flashattention" in spec.get("id", "").lower() else "New Token: Query Projection")
        q_label = Text(q_label_str, font=FONT_HELVETICA, font_size=17, color=WHITE, weight=BOLD).move_to(q_capsule)
        if q_label.width > 4.2:
            q_label.scale_to_fit_width(4.2)
        q_grp = VGroup(q_capsule, q_label)

        fetch_lasers = [
            CurvedArrow(q_capsule.get_top(), s.get_bottom(), angle=0.12 if i > 2 else -0.12, color="#00F0FF", stroke_width=2.2, tip_length=0.16)
            for i, s in enumerate(slots)
        ]

        o1_pill = create_tech_card(width=7.4, height=0.9, border_color=COLOR_MINT, stroke_width=2.0).shift(DOWN * 3.1)
        o1_label_str = meta.get("efficiency_badge") or ("⚡ ASYNCHRONOUS OVERLAPPING PIPELINE" if "flashattention" in spec.get("id", "").lower() else "⚡ O(1) CONSTANT TIME EXECUTION")
        o1_txt = Text(o1_label_str, font=FONT_HELVETICA, font_size=17, color="#FDE047", weight=HEAVY).move_to(o1_pill)
        if o1_txt.width > 7.0:
            o1_txt.scale_to_fit_width(7.0)
        o1_grp = VGroup(o1_pill, o1_txt)

        self.play(
            FadeIn(b4_math, shift=DOWN * 0.2),
            FadeIn(b4_ann, shift=DOWN * 0.2),
            FadeIn(q_grp, shift=UP * 0.3),
            captions.show(b4_parts[0], b4_hl),
            run_time=t4[0]
        )
        self.play(LaggedStart(*[Create(l) for l in fetch_lasers], lag_ratio=0.1), run_time=t4[1])
        self.play(
            FadeIn(o1_grp, shift=UP * 0.3),
            Circumscribe(q_capsule, color="#00F0FF", stroke_width=3.0),
            captions.morph_to(b4_parts[1], b4_hl),
            run_time=t4[2]
        )
        self.play(Flash(o1_pill, color="#FDE047", line_length=0.25, num_lines=8), run_time=t4[3])
        self.play(FadeOut(VGroup(b3_all, b4_math, b4_ann, q_grp, *fetch_lasers, o1_grp)), captions.hide(), self.camera.frame.animate.scale(1 / 0.96), run_time=t4[4])

        # -----------------------------------------------------------------
        # BEAT 5: (The Payoff: Throughput & Hardware Efficiency)
        # -----------------------------------------------------------------
        b5_parts, b5_hl = get_beat_parts(
            5, 2,
            ["Instant inference speed & 10x throughput boost,", "with massive VRAM efficiency on long prompts."],
            {"10x throughput": COLOR_MINT, "massive VRAM efficiency": COLOR_MINT}
        )

        b5_dur = get_beat_duration(5, 7.20)
        t5 = scale_times(b5_dur, [1.3, 1.3, 1.5, 1.4, 1.2, 0.5])

        b5_math = get_math_svg(4, "efficiency_math.svg", width=6.6).shift(UP * 4.3)
        b5_ann = get_term_annotations_group(4, y_pos=3.7)

        stat_val = meta.get("payoff_stat") or meta.get("key_stat", "10x")
        display_num = str(stat_val)[:6]
        lbl_text = meta.get("payoff_label", "THROUGHPUT MULTIPLIER")

        payoff_num = Text(display_num, font=FONT_HELVETICA, font_size=108, color=COLOR_MINT, weight=HEAVY).shift(UP * 1.5)
        if payoff_num.width > 7.0:
            payoff_num.scale_to_fit_width(7.0)
        payoff_lbl = Text(lbl_text, font=FONT_HELVETICA, font_size=20, color=WHITE, weight=HEAVY).next_to(payoff_num, DOWN, buff=0.25)
        if payoff_lbl.width > 7.2:
            payoff_lbl.scale_to_fit_width(7.2)
        payoff_grp = VGroup(payoff_num, payoff_lbl)

        metric_card = create_tech_card(width=7.6, height=1.1, border_color=COLOR_MINT, stroke_width=2.0).shift(DOWN * 0.8)
        metric_str = meta.get("payoff_sub") or ("⚡ 75% FP16 UTILIZATION • 1.2 PFLOPS FP8" if "flashattention" in spec.get("id", "").lower() else "⚡ CONSTANT STEP LATENCY ACROSS 128K CONTEXT")
        metric_txt = Text(metric_str, font=FONT_HELVETICA, font_size=17, color="#A7F3D0", weight=HEAVY).move_to(metric_card)
        if metric_txt.width > 7.2:
            metric_txt.scale_to_fit_width(7.2)
        metric_grp = VGroup(metric_card, metric_txt)

        proof_str = meta.get("proof_tag") or ("✓ BENCHMARKED ON NVIDIA H100 HOPPER ARCHITECTURE" if "flashattention" in spec.get("id", "").lower() else "✓ STANDARD IN ALL SOTA SERVING ENGINES (vLLM / TGI)")
        proof_tag = Text(proof_str, font=FONT_HELVETICA, font_size=16, color=COLOR_SLATE, weight=BOLD).next_to(metric_grp, DOWN, buff=0.3)
        if proof_tag.width > 7.4:
            proof_tag.scale_to_fit_width(7.4)

        b5_all = VGroup(b5_math, b5_ann, payoff_grp, metric_grp, proof_tag)

        self.play(
            FadeIn(payoff_grp, shift=UP * 0.3),
            Flash(payoff_num, color=COLOR_MINT, line_length=0.35, num_lines=10),
            captions.show(b5_parts[0], b5_hl),
            run_time=t5[0]
        )
        self.play(Circumscribe(payoff_num, color=COLOR_MINT, stroke_width=3.5), run_time=t5[1])
        self.play(
            FadeIn(metric_grp, shift=UP * 0.3),
            FadeIn(proof_tag, shift=UP * 0.3),
            captions.morph_to(b5_parts[1], b5_hl),
            run_time=t5[2]
        )
        self.play(Flash(metric_card, color="#FDE047", line_length=0.25, num_lines=8), run_time=t5[3])
        self.play(self.camera.frame.animate.scale(0.96), run_time=t5[4])
        self.play(FadeOut(b5_all), captions.hide(), self.camera.frame.animate.scale(1 / 0.96), run_time=t5[5])

        # -----------------------------------------------------------------
        # BEAT 6: (Chalkboard Brand Outro)
        # -----------------------------------------------------------------
        b6_parts, b6_hl = get_beat_parts(
            6, 2,
            ["Follow The Model Verse", "for modern AI architecture deep dives."],
            {"The Model Verse": COLOR_MINT, "deep dives": WHITE}
        )

        b6_dur = get_beat_duration(6, 4.80)
        t6 = scale_times(b6_dur, [1.3, 2.2, 1.3])

        logo_icon, brand_text, outro_sub = create_chalkboard_brand_outro(
            logo_title="THE MODEL VERSE",
            tagline="Engineering Behind Modern AI Architectures",
            url="themodelverse.in",
            y_center=0.4
        )

        self.play(
            Create(logo_icon, lag_ratio=0.08),
            FadeIn(brand_text, shift=DOWN * 0.3),
            FadeIn(outro_sub, shift=UP * 0.2),
            captions.show(b6_parts[0], b6_hl),
            run_time=t6[0]
        )
        self.play(
            logo_icon.animate.rotate(TAU / 6),
            Circumscribe(brand_text[1], color=COLOR_MINT, stroke_width=2.2, time_width=0.6),
            captions.morph_to(b6_parts[1], b6_hl),
            self.camera.frame.animate.scale(0.97),
            run_time=t6[1]
        )
        self.play(
            FadeOut(VGroup(logo_icon, brand_text, outro_sub)),
            captions.hide(),
            run_time=t6[2]
        )
