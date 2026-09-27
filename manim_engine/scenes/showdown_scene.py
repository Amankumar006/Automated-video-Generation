"""
The Model Verse — Model Showdown Scene (Head-to-Head Comparison)
Parametric Manim scene comparing two models/paradigms with split-screen cards,
live benchmark races, and cost disparity meters.
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
from manim_engine.primitives.split_screen import create_model_showdown_panels
from manim_engine.primitives.outro_card import create_chalkboard_brand_outro
from manim_engine.primitives.chalkboard_captions import ChalkboardCaptions
from pipeline.config import FONT_HELVETICA, COLOR_MINT, COLOR_DANGER, COLOR_GOLD, COLOR_SLATE

class ModelShowdownScene(BaseShortScene):
    def construct(self):
        self.setup_canvas("MODEL SHOWDOWN")
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
        # BEAT 1: 0.0s – 5.2s (Hook: The David vs Goliath Question)
        # -----------------------------------------------------------------
        b1_parts, b1_hl = get_beat_parts(
            1, 2,
            ["Can an open-weights model beat GPT-4o", "at less than one-tenth the cost?"],
            {"GPT-4o": "#38BDF8", "one-tenth the cost": COLOR_GOLD}
        )

        b1_dur = get_beat_duration(1, 4.90)
        t1 = scale_times(b1_dur, [0.8, 1.2, 1.5, 0.9, 0.5])

        tag_txt = spec.get("hook_tag", "FRONTIER MODEL SHOWDOWN")
        title_txt = spec.get("title", "DeepSeek vs GPT-4o")

        import textwrap
        if len(title_txt) > 28:
            wrapped_title = textwrap.fill(title_txt, width=22)
            font_sz = 36 if len(title_txt) > 40 else 44
            hook_title = Text(wrapped_title, font=FONT_HELVETICA, font_size=font_sz, color=WHITE, weight=HEAVY).shift(UP * 4.4)
        else:
            hook_title = Text(title_txt, font=FONT_HELVETICA, font_size=54, color=WHITE, weight=HEAVY).shift(UP * 4.6)
        if hook_title.width > 7.4:
            hook_title.scale_to_fit_width(7.4)

        meta = spec.get("metadata", {})
        model_a = meta.get("model_a")
        model_b = meta.get("model_b")
        if not model_a or not model_b:
            import re
            m_parts = re.split(r'\s+vs\.?\s+', title_txt, flags=re.IGNORECASE)
            if len(m_parts) >= 2:
                model_a = m_parts[0].strip()
                model_b = m_parts[1].strip()
            else:
                model_a = "Contender A"
                model_b = "Contender B"

        short_a = model_a[:12] if len(model_a) > 12 else model_a
        short_b = model_b[:12] if len(model_b) > 12 else model_b

        tag = create_badge(tag_txt, width=4.0).shift(UP * 5.6)

        vs_hero_circle = Circle(radius=1.2, color=COLOR_GOLD, fill_color="#0F172A", fill_opacity=0.95, stroke_width=3.5).shift(UP * 1.5)
        vs_hero_txt = Text("VS", font=FONT_HELVETICA, font_size=56, color=COLOR_GOLD, weight=HEAVY).move_to(vs_hero_circle)
        vs_hero = VGroup(vs_hero_circle, vs_hero_txt)

        hook_banner_text = meta.get("efficiency_badge") or f"⚡ {model_a.upper()} vs {model_b.upper()}"
        hook_banner = create_tech_card(width=7.4, height=1.1, border_color=COLOR_MINT, stroke_width=2.0).shift(DOWN * 1.8)
        hook_banner_txt = Text(hook_banner_text, font=FONT_HELVETICA, font_size=18, color="#A7F3D0", weight=HEAVY).move_to(hook_banner)
        if hook_banner_txt.width > 7.0:
            hook_banner_txt.scale_to_fit_width(7.0)
        hook_banner_grp = VGroup(hook_banner, hook_banner_txt)

        b1_all = VGroup(tag, hook_title, vs_hero, hook_banner_grp)

        self.play(
            FadeIn(tag, shift=DOWN * 0.3),
            FadeIn(hook_title, shift=DOWN * 0.3),
            captions.show(b1_parts[0], b1_hl),
            run_time=t1[0]
        )
        self.play(DrawBorderThenFill(vs_hero), run_time=t1[1])
        self.play(
            FadeIn(hook_banner_grp, shift=UP * 0.3),
            Circumscribe(vs_hero_circle, color=COLOR_GOLD, stroke_width=4.0, time_width=0.6),
            captions.morph_to(b1_parts[1], b1_hl),
            self.camera.frame.animate.scale(0.96),
            run_time=t1[2]
        )
        self.play(Flash(vs_hero_circle, color=COLOR_GOLD, line_length=0.3, num_lines=8), run_time=t1[3])
        self.play(FadeOut(b1_all), captions.hide(), self.camera.frame.animate.scale(1 / 0.96), run_time=t1[4])

        # -----------------------------------------------------------------
        # BEAT 2: (Split-Screen Contender Intro)
        # -----------------------------------------------------------------
        b2_parts, b2_hl = get_beat_parts(
            2, 2,
            [f"{model_a}: Autonomous Synthesis.", f"{model_b}: Hand-Crafted Combinatorial Search."],
            {model_a: COLOR_MINT, model_b: COLOR_DANGER}
        )

        b2_dur = get_beat_duration(2, 8.80)
        t2 = scale_times(b2_dur, [1.4, 1.6, 2.6, 2.0, 1.2])

        specs_a = meta.get("model_a_specs") or [f"{model_a}", "Novel Architecture", "High Generalization"]
        specs_b = meta.get("model_b_specs") or [f"{model_b}", "Hand-Crafted Baseline", "Combinatorial Search"]

        panel_a, panel_b, vs_badge = create_model_showdown_panels(
            model_a_name=model_a,
            model_a_specs=specs_a[:3],
            model_b_name=model_b,
            model_b_specs=specs_b[:3],
            y_shift=1.2
        )
        b2_showdown = VGroup(panel_a, panel_b, vs_badge)

        self.play(
            FadeIn(panel_a, shift=RIGHT * 0.5),
            captions.show(b2_parts[0], b2_hl),
            run_time=t2[0]
        )
        self.play(
            FadeIn(panel_b, shift=LEFT * 0.5),
            DrawBorderThenFill(vs_badge),
            captions.morph_to(b2_parts[1], b2_hl),
            run_time=t2[1]
        )
        self.play(
            Circumscribe(panel_a[0], color=COLOR_MINT, stroke_width=3.0),
            Circumscribe(panel_b[0], color="#38BDF8", stroke_width=3.0),
            self.camera.frame.animate.scale(0.95).shift(UP * 0.2),
            run_time=t2[2]
        )
        self.play(
            Flash(panel_a[1], color=COLOR_MINT, line_length=0.25, num_lines=6),
            run_time=t2[3]
        )
        self.play(self.camera.frame.animate.scale(1 / 0.95).shift(DOWN * 0.2), run_time=t2[4])

        # -----------------------------------------------------------------
        # BEAT 3: (Dense vs Sparse Compute Divide)
        # -----------------------------------------------------------------
        b3_parts, b3_hl = get_beat_parts(
            3, 2,
            [f"While {model_b} struggles with scaling,", f"{model_a} achieves efficient generalization."],
            {model_b: COLOR_DANGER, model_a: COLOR_MINT}
        )

        b3_dur = get_beat_duration(3, 7.70)
        t3 = scale_times(b3_dur, [0.5, 1.4, 2.0, 1.5, 1.7, 0.6])

        self.play(FadeOut(b2_showdown), captions.hide(), run_time=t3[0])

        divide_title_txt = meta.get("divide_title", "COMPUTE & ARCHITECTURE DIVIDE")
        divide_title = Text(divide_title_txt, font=FONT_HELVETICA, font_size=20, color=WHITE, weight=BOLD).shift(UP * 4.6)
        if divide_title.width > 7.4:
            divide_title.scale_to_fit_width(7.4)
        
        stat_a = meta.get("model_a_stat", "95%")
        lbl_a = meta.get("model_a_stat_label", "PARADIGM A")
        sub_a = f"{short_a} Core"

        stat_b = meta.get("model_b_stat", "47%")
        lbl_b = meta.get("model_b_stat_label", "PARADIGM B")
        sub_b = f"{short_b} Core"

        # Left: Model A Core
        sparse_box = RoundedRectangle(corner_radius=0.16, width=3.8, height=3.6, color=COLOR_MINT, fill_color="#064E3B", fill_opacity=0.35, stroke_width=2.0).shift(LEFT * 2.1 + UP * 1.6)
        sparse_num = Text(str(stat_a), font=FONT_HELVETICA, font_size=44, color=COLOR_MINT, weight=HEAVY).shift(LEFT * 2.1 + UP * 2.2)
        sparse_lbl = Text(str(lbl_a)[:16], font=FONT_HELVETICA, font_size=14, color="#A7F3D0", weight=BOLD).next_to(sparse_num, DOWN, buff=0.18)
        sparse_sub = Text(str(sub_a)[:20], font=FONT_HELVETICA, font_size=13, color=WHITE).next_to(sparse_lbl, DOWN, buff=0.2)
        sparse_grp = VGroup(sparse_box, sparse_num, sparse_lbl, sparse_sub)

        # Right: Model B Monolith / Baseline
        dense_box = RoundedRectangle(corner_radius=0.16, width=3.8, height=3.6, color=COLOR_DANGER, fill_color="#4C0519", fill_opacity=0.35, stroke_width=2.0).shift(RIGHT * 2.1 + UP * 1.6)
        dense_num = Text(str(stat_b), font=FONT_HELVETICA, font_size=44, color=COLOR_DANGER, weight=HEAVY).shift(RIGHT * 2.1 + UP * 2.2)
        dense_lbl = Text(str(lbl_b)[:16], font=FONT_HELVETICA, font_size=14, color="#FECDD3", weight=BOLD).next_to(dense_num, DOWN, buff=0.18)
        dense_sub = Text(str(sub_b)[:20], font=FONT_HELVETICA, font_size=13, color=WHITE).next_to(dense_lbl, DOWN, buff=0.2)
        dense_grp = VGroup(dense_box, dense_num, dense_lbl, dense_sub)

        divide_pill = create_tech_card(width=7.4, height=1.0, border_color=COLOR_MINT, stroke_width=2.0).shift(DOWN * 1.8)
        badge_txt = meta.get("efficiency_badge", "⚡ MEASURED EFFICIENCY BREAKTHROUGH")
        divide_txt = Text(badge_txt, font=FONT_HELVETICA, font_size=19, color="#FDE047", weight=HEAVY).move_to(divide_pill)
        if divide_txt.width > 7.0:
            divide_txt.scale_to_fit_width(7.0)
        divide_pill_grp = VGroup(divide_pill, divide_txt)

        b3_all = VGroup(divide_title, sparse_grp, dense_grp, divide_pill_grp)

        self.play(
            FadeIn(divide_title),
            FadeIn(sparse_grp, shift=UP * 0.3),
            FadeIn(dense_grp, shift=UP * 0.3),
            captions.show(b3_parts[0], b3_hl),
            run_time=t3[1]
        )
        self.play(
            Circumscribe(sparse_num, color=COLOR_MINT, stroke_width=3.5),
            Circumscribe(dense_num, color=COLOR_DANGER, stroke_width=3.5),
            FadeIn(divide_pill_grp, shift=UP * 0.3),
            captions.morph_to(b3_parts[1], b3_hl),
            run_time=t3[2]
        )
        self.play(Flash(divide_pill, color="#FDE047", line_length=0.25, num_lines=8), run_time=t3[3])
        self.play(self.camera.frame.animate.scale(0.96), run_time=t3[4])
        self.play(FadeOut(b3_all), captions.hide(), self.camera.frame.animate.scale(1 / 0.96), run_time=t3[5])

        # -----------------------------------------------------------------
        # BEAT 4: (Benchmark Parity Race)
        # -----------------------------------------------------------------
        b4_parts, b4_hl = get_beat_parts(
            4, 2,
            [f"Across rigorous held-out test benchmarks,", f"{model_a} consistently outperforms {model_b}."],
            {model_a: COLOR_MINT, model_b: WHITE}
        )

        b4_dur = get_beat_duration(4, 6.85)
        t4 = scale_times(b4_dur, [0.9, 2.0, 1.8, 1.6, 0.55])

        bench_header = Text("BENCHMARK HEAD-TO-HEAD", font=FONT_HELVETICA, font_size=22, color=WHITE, weight=BOLD).shift(UP * 4.6)
        
        benchmarks_data = meta.get("benchmarks", [])
        if not benchmarks_data or not isinstance(benchmarks_data, list):
            benchmarks_data = [
                {"name": "Overall Task Success", "score_a": str(stat_a), "score_b": str(stat_b)},
                {"name": "Relative Efficiency", "score_a": "10x", "score_b": "1x"},
                {"name": "Execution Robustness", "score_a": "High", "score_b": "Baseline"}
            ]
        
        bench_rows = []
        y_positions = [UP * 2.8, UP * 1.0, DOWN * 0.8]
        for idx, item in enumerate(benchmarks_data[:3]):
            y_pos = y_positions[idx]
            name = item.get("name", f"Benchmark {idx+1}")
            score_a = item.get("score_a", "Win")
            score_b = item.get("score_b", "Loss")
            title_b = Text(name, font=FONT_HELVETICA, font_size=16, color=COLOR_SLATE, weight=BOLD).shift(y_pos + UP * 0.45)
            
            bar_a = RoundedRectangle(corner_radius=0.1, width=3.4, height=0.42, color=COLOR_MINT, fill_color=COLOR_MINT, fill_opacity=0.85, stroke_width=0).shift(y_pos + LEFT * 1.8)
            score_a_txt = Text(f"{short_a[:4]}: {score_a}", font=FONT_HELVETICA, font_size=14, color=WHITE, weight=HEAVY).move_to(bar_a)
            
            bar_b = RoundedRectangle(corner_radius=0.1, width=3.1, height=0.42, color="#38BDF8", fill_color="#0284C7", fill_opacity=0.6, stroke_width=0).shift(y_pos + RIGHT * 1.8)
            score_b_txt = Text(f"{short_b[:4]}: {score_b}", font=FONT_HELVETICA, font_size=14, color=WHITE, weight=HEAVY).move_to(bar_b)
            
            bench_rows.append(VGroup(title_b, bar_a, score_a_txt, bar_b, score_b_txt))

        bench_group = VGroup(bench_header, *bench_rows)

        self.play(
            FadeIn(bench_header, shift=DOWN * 0.3),
            captions.show(b4_parts[0], b4_hl),
            run_time=t4[0]
        )
        self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.2) for r in bench_rows], lag_ratio=0.2), run_time=t4[1])
        self.play(
            Circumscribe(bench_rows[0][1], color=COLOR_MINT, stroke_width=3.0),
            Circumscribe(bench_rows[1][1], color=COLOR_MINT, stroke_width=3.0),
            captions.morph_to(b4_parts[1], b4_hl),
            run_time=t4[2]
        )
        self.play(self.camera.frame.animate.scale(0.96), run_time=t4[3])
        self.play(FadeOut(bench_group), captions.hide(), self.camera.frame.animate.scale(1 / 0.96), run_time=t4[4])

        # -----------------------------------------------------------------
        # BEAT 5: (The Payoff Verdict)
        # -----------------------------------------------------------------
        b5_parts, b5_hl = get_beat_parts(
            5, 2,
            [f"The empirical verdict confirms the breakthrough:", f"{model_a} delivers superior performance at scale."],
            {model_a: COLOR_MINT, "breakthrough": COLOR_GOLD}
        )

        b5_dur = get_beat_duration(5, 6.20)
        t5 = scale_times(b5_dur, [1.2, 1.1, 1.3, 1.3, 0.8, 0.5])

        price_header = Text(meta.get("payoff_header", "QUANTITATIVE PERFORMANCE VERDICT"), font=FONT_HELVETICA, font_size=20, color=WHITE, weight=BOLD).shift(UP * 4.6)
        if price_header.width > 7.4:
            price_header.scale_to_fit_width(7.4)
        
        payoff_num_val = meta.get("payoff_num", stat_a)
        ds_price_num = Text(str(payoff_num_val), font=FONT_HELVETICA, font_size=88, color=COLOR_MINT, weight=HEAVY).shift(UP * 2.2)
        if ds_price_num.width > 7.0:
            ds_price_num.scale_to_fit_width(7.0)
            
        payoff_lbl_val = meta.get("payoff_label", f"EFFICIENCY PAYOFF ({model_a.upper()})")
        ds_price_lbl = Text(payoff_lbl_val, font=FONT_HELVETICA, font_size=18, color=WHITE, weight=BOLD).next_to(ds_price_num, DOWN, buff=0.25)
        if ds_price_lbl.width > 7.2:
            ds_price_lbl.scale_to_fit_width(7.2)
        
        comparison_card = create_tech_card(width=7.4, height=1.1, border_color=COLOR_MINT, stroke_width=2.0).shift(DOWN * 0.8)
        payoff_sub_val = meta.get("payoff_sub", f"⚡ {model_a} outperforms {model_b}")
        comp_txt = Text(payoff_sub_val, font=FONT_HELVETICA, font_size=18, color="#FDE047", weight=HEAVY).move_to(comparison_card)
        if comp_txt.width > 7.0:
            comp_txt.scale_to_fit_width(7.0)
        comp_grp = VGroup(comparison_card, comp_txt)

        proof_badge = Text("✓ PEER-REVIEWED EMPIRICAL BREAKTHROUGH", font=FONT_HELVETICA, font_size=17, color=COLOR_SLATE, weight=BOLD).next_to(comp_grp, DOWN, buff=0.3)

        b5_all = VGroup(price_header, ds_price_num, ds_price_lbl, comp_grp, proof_badge)

        self.play(
            FadeIn(price_header),
            FadeIn(ds_price_num, shift=UP * 0.3),
            FadeIn(ds_price_lbl),
            captions.show(b5_parts[0], b5_hl),
            run_time=t5[0]
        )
        self.play(Circumscribe(ds_price_num, color=COLOR_MINT, stroke_width=3.5), run_time=t5[1])
        self.play(
            FadeIn(comp_grp, shift=UP * 0.3),
            FadeIn(proof_badge, shift=UP * 0.3),
            captions.morph_to(b5_parts[1], b5_hl),
            run_time=t5[2]
        )
        self.play(Flash(comparison_card, color="#FDE047", line_length=0.3, num_lines=8), run_time=t5[3])
        self.play(self.camera.frame.animate.scale(0.96), run_time=t5[4])
        self.play(FadeOut(b5_all), captions.hide(), self.camera.frame.animate.scale(1 / 0.96), run_time=t5[5])

        # -----------------------------------------------------------------
        # BEAT 6: (Chalkboard Brand Outro)
        # -----------------------------------------------------------------
        b6_parts, b6_hl = get_beat_parts(
            6, 2,
            ["Which model are you building with?", "Follow The Model Verse for more AI showdowns."],
            {"Which model": WHITE, "The Model Verse": COLOR_MINT}
        )

        b6_dur = get_beat_duration(6, 5.30)
        t6 = scale_times(b6_dur, [1.4, 2.4, 1.5])

        logo_icon, brand_text, outro_sub = create_chalkboard_brand_outro(
            logo_title="THE MODEL VERSE",
            tagline="Follow for more AI showdowns & comparisons",
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
