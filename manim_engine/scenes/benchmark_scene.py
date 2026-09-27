"""
The Model Verse — Benchmark News Scene (Category 4)
Parametric 3Blue1Brown chalkboard scene for SOTA milestones, leaderboard shakeups,
and open-weights performance breakthroughs.
"""

import os
import json
import textwrap
import re
from manim import *
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from manim_engine.base_scene import BaseShortScene
from manim_engine.primitives.tech_card import create_tech_card, create_badge
from manim_engine.primitives.leaderboard import (
    create_leaderboard_row, create_cost_disruption_meter
)
from manim_engine.primitives.outro_card import create_chalkboard_brand_outro
from manim_engine.primitives.chalkboard_captions import ChalkboardCaptions
from pipeline.config import FONT_HELVETICA, COLOR_MINT, COLOR_DANGER, COLOR_GOLD, COLOR_SLATE

class BenchmarkNewsScene(BaseShortScene):
    def construct(self):
        self.setup_canvas("BENCHMARK DISPATCH")
        captions = ChalkboardCaptions(self, y_pos=-4.8)

        # Ingest active spec
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
            return [max(0.10, round(t * scale, 3)) for t in default_times]

        meta = spec.get("metadata", {})
        challenger_name = meta.get("challenger", meta.get("model_a", "DeepSeek-R1"))
        incumbent_name = meta.get("incumbent", meta.get("model_b", "OpenAI o1"))

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

        # -----------------------------------------------------------------
        # BEAT 1: (Hook: The Leaderboard Upset)
        # -----------------------------------------------------------------
        b1_parts, b1_hl = get_beat_parts(
            1, 2,
            ["The AI leaderboard just had its biggest upset.", f"An open-weights model matched {incumbent_name} at a fraction of the cost."],
            {"biggest upset": COLOR_GOLD, "open-weights": COLOR_MINT, incumbent_name: "#38BDF8"}
        )
        b1_dur = get_beat_duration(1, 7.25)
        t1 = scale_times(b1_dur, [0.8, 1.3, 1.8, 2.5, 0.4])

        tag_txt = spec.get("hook_tag", "LEADERBOARD UPSET // NEW SOTA")
        title_txt = spec.get("title", f"{challenger_name} Shocks Frontier AI")

        if len(title_txt) > 28:
            wrapped_title = textwrap.fill(title_txt, width=22)
            font_sz = 34 if len(title_txt) > 42 else 40
            hook_title = Text(wrapped_title, font=FONT_HELVETICA, font_size=font_sz, color=WHITE, weight=HEAVY).shift(UP * 4.3)
        else:
            hook_title = Text(title_txt, font=FONT_HELVETICA, font_size=50, color=WHITE, weight=HEAVY).shift(UP * 4.5)
        if hook_title.width > 7.4:
            hook_title.scale_to_fit_width(7.4)

        tag = create_badge(tag_txt, width=4.6, border_color=COLOR_GOLD, fill_color="#78350F", text_color="#FDE68A").shift(UP * 5.6)

        # Hero benchmark stamp
        sota_box = create_tech_card(width=7.2, height=2.4, border_color=COLOR_MINT, stroke_width=2.2).shift(UP * 1.5)
        sota_header = Text(meta.get("milestone_metric", "HISTORIC BENCHMARK MILESTONE"), font=FONT_HELVETICA, font_size=18, color=COLOR_GOLD, weight=HEAVY).align_to(sota_box, UP).shift(DOWN * 0.3)
        if sota_header.width > 7.0:
            sota_header.scale_to_fit_width(7.0)
        
        aime_svg = get_math_svg(0, "aime_benchmark.svg", width=6.2).move_to(sota_box).shift(DOWN * 0.1)
        sota_sub_txt = meta.get("milestone_sub", "American Invitational Math Exam • Pass@1")
        sota_sub = Text(sota_sub_txt, font=FONT_HELVETICA, font_size=16, color="#94A3B8", weight=MEDIUM).align_to(sota_box, DOWN).shift(UP * 0.25)
        if sota_sub.width > 7.0:
            sota_sub.scale_to_fit_width(7.0)
        sota_grp = VGroup(sota_box, sota_header, aime_svg, sota_sub)

        banner_sub = create_tech_card(width=7.2, height=0.9, border_color="#334155", stroke_width=1.5).shift(DOWN * 1.5)
        banner_sub_txt = Text(meta.get("efficiency_badge", "⚡ MEASURED SOTA PARITY AT A FRACTION OF COST"), font=FONT_HELVETICA, font_size=18, color="#A7F3D0", weight=HEAVY).move_to(banner_sub)
        if banner_sub_txt.width > 7.0:
            banner_sub_txt.scale_to_fit_width(7.0)
        banner_grp = VGroup(banner_sub, banner_sub_txt)

        b1_all = VGroup(tag, hook_title, sota_grp, banner_grp)

        self.play(
            FadeIn(tag, shift=DOWN * 0.3),
            FadeIn(hook_title, shift=DOWN * 0.3),
            captions.show(b1_parts[0], b1_hl),
            run_time=t1[0]
        )
        self.play(
            FadeIn(sota_grp, shift=UP * 0.2),
            run_time=t1[1]
        )
        self.play(
            FadeIn(banner_grp, shift=UP * 0.2),
            Circumscribe(sota_box, color=COLOR_MINT, stroke_width=3.5),
            captions.morph_to(b1_parts[1], b1_hl),
            run_time=t1[2]
        )
        self.wait(t1[3])
        self.play(FadeOut(b1_all), captions.hide(), run_time=t1[4])

        # -----------------------------------------------------------------
        # BEAT 2: (The Incumbent Monopoly Baseline)
        # -----------------------------------------------------------------
        b2_parts, b2_hl = get_beat_parts(
            2, 2,
            ["Proprietary reasoning models held the monopoly.", "Frontier math capabilities were locked behind expensive enterprise APIs."],
            {"Proprietary": COLOR_DANGER, "monopoly": COLOR_DANGER, "expensive": COLOR_GOLD}
        )
        b2_dur = get_beat_duration(2, 7.36)
        t2 = scale_times(b2_dur, [0.8, 1.4, 1.8, 2.5, 0.4])

        b2_title = Text("THE PROPRIETARY BASELINE", font=FONT_HELVETICA, font_size=28, color=COLOR_SLATE, weight=BOLD).shift(UP * 4.6)
        
        # Static baseline rows showing previous hierarchy
        row_o1 = create_leaderboard_row(1, incumbent_name, "79.2%", 79.2, is_hero=False, width=7.4).shift(UP * 2.6)
        row_claude = create_leaderboard_row(2, "Claude 3.5 Sonnet", "65.4%", 65.4, is_hero=False, width=7.4).shift(UP * 1.3)
        row_gpt4 = create_leaderboard_row(3, "GPT-4o", "41.7%", 41.7, is_hero=False, width=7.4).shift(ORIGIN)

        # Monopolistic enterprise cost badge
        cost_wall = create_tech_card(width=7.4, height=1.6, border_color=COLOR_DANGER, stroke_width=2.0).shift(DOWN * 1.8)
        cost_wall_title = Text("PROPRIETARY API WALL", font=FONT_HELVETICA, font_size=18, color=COLOR_DANGER, weight=HEAVY).align_to(cost_wall, UP).shift(DOWN * 0.25)
        cost_wall_val = Text("$15.00 to $60.00 / Million Tokens", font=FONT_HELVETICA, font_size=22, color=WHITE, weight=BOLD).move_to(cost_wall).shift(DOWN * 0.1)
        cost_wall_grp = VGroup(cost_wall, cost_wall_title, cost_wall_val)

        b2_all = VGroup(b2_title, row_o1, row_claude, row_gpt4, cost_wall_grp)

        self.play(
            FadeIn(b2_title, shift=DOWN * 0.2),
            captions.show(b2_parts[0], b2_hl),
            run_time=t2[0]
        )
        self.play(
            FadeIn(row_o1, shift=LEFT * 0.4),
            FadeIn(row_claude, shift=LEFT * 0.4),
            FadeIn(row_gpt4, shift=LEFT * 0.4),
            run_time=t2[1]
        )
        self.play(
            FadeIn(cost_wall_grp, shift=UP * 0.3),
            Indicate(cost_wall, color=COLOR_DANGER),
            captions.morph_to(b2_parts[1], b2_hl),
            run_time=t2[2]
        )
        self.wait(t2[3])
        self.play(FadeOut(b2_all), captions.hide(), run_time=t2[4])

        # -----------------------------------------------------------------
        # BEAT 3: (The Technical Breakthrough: Pure RL Reasoning Tree)
        # -----------------------------------------------------------------
        b3_parts, b3_hl = get_beat_parts(
            3, 2,
            [f"Enter {challenger_name}: trained without human supervision.", "Developing chain-of-thought reasoning purely through reinforcement learning."],
            {challenger_name: COLOR_MINT, "without human supervision": COLOR_GOLD, "reinforcement learning": COLOR_MINT}
        )
        b3_dur = get_beat_duration(3, 7.45)
        t3 = scale_times(b3_dur, [0.7, 1.4, 1.8, 2.6, 0.4])

        b3_title = Text("PURE REINFORCEMENT LEARNING", font=FONT_HELVETICA, font_size=28, color=COLOR_MINT, weight=HEAVY).shift(UP * 4.6)

        # Reasoning Tree Visual (Chalkboard Branching)
        root_node = Dot(point=[0, 3.2, 0], radius=0.18, color=COLOR_MINT)
        root_txt = Text(r"Prompt", font=FONT_HELVETICA, font_size=17, color=WHITE, weight=BOLD).next_to(root_node, UP, buff=0.15)
        
        # Step 1 layer
        s1_nodes = [Dot(point=[x, 2.0, 0], radius=0.12, color="#38BDF8") for x in [-2.4, 0.0, 2.4]]
        s1_lines = [Line(root_node.get_center(), n.get_center(), stroke_width=2.0, color="#475569") for n in s1_nodes]

        # Step 2 layer (Reasoning search paths)
        s2_nodes = [
            Dot(point=[-2.8, 0.8, 0], radius=0.10, color=COLOR_DANGER),
            Dot(point=[-1.8, 0.8, 0], radius=0.10, color=COLOR_DANGER),
            Dot(point=[-0.6, 0.8, 0], radius=0.12, color=COLOR_MINT),  # Winning branch
            Dot(point=[0.6, 0.8, 0], radius=0.10, color=COLOR_DANGER),
            Dot(point=[2.0, 0.8, 0], radius=0.10, color=COLOR_DANGER),
            Dot(point=[2.8, 0.8, 0], radius=0.10, color=COLOR_DANGER),
        ]
        s2_lines = [
            Line(s1_nodes[0].get_center(), s2_nodes[0].get_center(), stroke_width=1.5, color="#334155"),
            Line(s1_nodes[0].get_center(), s2_nodes[1].get_center(), stroke_width=1.5, color="#334155"),
            Line(s1_nodes[1].get_center(), s2_nodes[2].get_center(), stroke_width=2.5, color=COLOR_MINT),
            Line(s1_nodes[1].get_center(), s2_nodes[3].get_center(), stroke_width=1.5, color="#334155"),
            Line(s1_nodes[2].get_center(), s2_nodes[4].get_center(), stroke_width=1.5, color="#334155"),
            Line(s1_nodes[2].get_center(), s2_nodes[5].get_center(), stroke_width=1.5, color="#334155"),
        ]

        # Verified solution terminal
        sol_node = Dot(point=[-0.6, -0.2, 0], radius=0.20, color=COLOR_GOLD)
        sol_line = Line(s2_nodes[2].get_center(), sol_node.get_center(), stroke_width=3.0, color=COLOR_GOLD)
        sol_txt = Text("Self-Reflected Proof", font=FONT_HELVETICA, font_size=17, color=COLOR_GOLD, weight=BOLD).next_to(sol_node, DOWN, buff=0.15)

        tree_grp = VGroup(
            root_node, root_txt,
            *s1_lines, *s1_nodes,
            *s2_lines, *s2_nodes,
            sol_line, sol_node, sol_txt
        )

        grpo_svg = SVGMobject("public/math_svgs/grpo_formula.svg").scale_to_fit_width(7.2).shift(DOWN * 1.8)
        grpo_label = Text("Group Relative Policy Optimization (GRPO)", font=FONT_HELVETICA, font_size=16, color="#94A3B8", weight=MEDIUM).next_to(grpo_svg, DOWN, buff=0.15)
        grpo_grp = VGroup(grpo_svg, grpo_label)

        b3_all = VGroup(b3_title, tree_grp, grpo_grp)

        self.play(
            FadeIn(b3_title, shift=DOWN * 0.2),
            captions.show(b3_parts[0], b3_hl),
            run_time=t3[0]
        )
        self.play(
            FadeIn(root_node), FadeIn(root_txt),
            *[Create(l) for l in s1_lines],
            *[FadeIn(n) for n in s1_nodes],
            run_time=t3[1]
        )
        self.play(
            *[Create(l) for l in s2_lines],
            *[FadeIn(n) for n in s2_nodes],
            Create(sol_line), FadeIn(sol_node), FadeIn(sol_txt),
            FadeIn(grpo_grp, shift=UP * 0.2),
            captions.morph_to(b3_parts[1], b3_hl),
            run_time=t3[2]
        )
        self.wait(t3[3])
        self.play(FadeOut(b3_all), captions.hide(), run_time=t3[4])

        # -----------------------------------------------------------------
        # BEAT 4: (The Leaderboard Race: Challenger Takes #1!)
        # -----------------------------------------------------------------
        b4_parts, b4_hl = get_beat_parts(
            4, 2,
            ["On the grueling AIME exam, it scored 79.8 percent.", "Overtaking o1 and matching the 96th percentile on Codeforces."],
            {"79.8 percent": COLOR_GOLD, "Overtaking o1": COLOR_MINT, "Codeforces": "#38BDF8"}
        )
        b4_dur = get_beat_duration(4, 8.02)
        t4 = scale_times(b4_dur, [0.6, 1.0, 1.4, 3.8, 0.4])

        b4_title = Text("GLOBAL LEADERBOARD RACE", font=FONT_HELVETICA, font_size=28, color=COLOR_GOLD, weight=HEAVY).shift(UP * 4.6)

        # Leaderboard with Challenger crowned at #1!
        rank1 = create_leaderboard_row(1, challenger_name, "79.8%", 79.8, is_hero=True, hero_color=COLOR_MINT, width=7.4).shift(UP * 2.8)
        rank2 = create_leaderboard_row(2, incumbent_name, "79.2%", 79.2, is_hero=False, width=7.4).shift(UP * 1.5)
        rank3 = create_leaderboard_row(3, "Claude 3.5 Sonnet", "65.4%", 65.4, is_hero=False, width=7.4).shift(UP * 0.2)
        rank4 = create_leaderboard_row(4, "GPT-4o", "41.7%", 41.7, is_hero=False, width=7.4).shift(DOWN * 1.1)

        # Delta callout
        delta_card = create_tech_card(width=7.4, height=1.3, border_color="#38BDF8", stroke_width=1.8).shift(DOWN * 2.6)
        delta_svg = SVGMobject("public/math_svgs/accuracy_delta.svg").scale_to_fit_width(6.8).move_to(delta_card)
        delta_grp = VGroup(delta_card, delta_svg)

        b4_all = VGroup(b4_title, rank1, rank2, rank3, rank4, delta_grp)

        self.play(
            FadeIn(b4_title, shift=DOWN * 0.2),
            captions.show(b4_parts[0], b4_hl),
            run_time=t4[0]
        )
        # Baselines appear first
        self.play(
            FadeIn(rank2, shift=DOWN * 0.2),
            FadeIn(rank3, shift=DOWN * 0.2),
            FadeIn(rank4, shift=DOWN * 0.2),
            run_time=t4[1]
        )
        # Dramatic surge: Challenger crashes into #1 with golden glow
        self.play(
            FadeIn(rank1, shift=UP * 0.4),
            Flash(rank1[0].get_center(), color=COLOR_GOLD, line_length=0.4, num_lines=12),
            Circumscribe(rank1[0], color=COLOR_GOLD, stroke_width=3.5),
            FadeIn(delta_grp, shift=UP * 0.2),
            captions.morph_to(b4_parts[1], b4_hl),
            run_time=t4[2]
        )
        self.wait(t4[3])
        self.play(FadeOut(b4_all), captions.hide(), run_time=t4[4])

        # -----------------------------------------------------------------
        # BEAT 5: (The Economic Disruption: 27x Cheaper & 100% Open Weights)
        # -----------------------------------------------------------------
        b5_parts, b5_hl = get_beat_parts(
            5, 2,
            ["Best of all: it is fully open source under MIT license.", "Running at 27 times lower API cost than proprietary alternatives."],
            {"open source": COLOR_MINT, "MIT license": COLOR_GOLD, "27 times lower": COLOR_MINT}
        )
        b5_dur = get_beat_duration(5, 8.41)
        t5 = scale_times(b5_dur, [0.6, 1.2, 1.4, 4.0, 0.4])

        b5_title = Text("THE ECONOMIC SHOCKWAVE", font=FONT_HELVETICA, font_size=28, color=COLOR_MINT, weight=HEAVY).shift(UP * 4.6)

        cost_meter = create_cost_disruption_meter(
            incumbent_name=incumbent_name,
            incumbent_price=meta.get("incumbent_price", "$15.00 / 1M"),
            challenger_name=challenger_name,
            challenger_price=meta.get("challenger_price", "$0.55 / 1M"),
            multiplier_str=meta.get("payoff_stat", "27x CHEAPER"),
            width=7.4
        ).shift(UP * 2.0)

        cost_formula_svg = get_math_svg(min(3, len(spec.get("math_formulas", []))-1), "cost_disparity_r1.svg", width=7.2).shift(DOWN * 0.3)

        open_badge_str = meta.get("proof_tag", "🔓 100% OPEN WEIGHTS // MIT PERMISSIVE LICENSE")
        open_badge = create_badge(open_badge_str, width=7.2, height=0.7, border_color=COLOR_MINT, fill_color="#064E3B", text_color="#A7F3D0").shift(DOWN * 1.6)

        b5_all = VGroup(b5_title, cost_meter, cost_formula_svg, open_badge)

        self.play(
            FadeIn(b5_title, shift=DOWN * 0.2),
            captions.show(b5_parts[0], b5_hl),
            run_time=t5[0]
        )
        self.play(
            FadeIn(cost_meter, shift=UP * 0.3),
            run_time=t5[1]
        )
        self.play(
            FadeIn(cost_formula_svg, shift=UP * 0.2),
            FadeIn(open_badge, shift=UP * 0.2),
            Indicate(cost_meter[5], color=COLOR_GOLD),
            captions.morph_to(b5_parts[1], b5_hl),
            run_time=t5[2]
        )
        self.wait(t5[3])
        self.play(FadeOut(b5_all), captions.hide(), run_time=t5[4])

        # -----------------------------------------------------------------
        # BEAT 6: (Brand Signature Outro)
        # -----------------------------------------------------------------
        b6_parts, b6_hl = get_beat_parts(
            6, 2,
            ["Follow The Model Verse", "for the engineering behind frontier AI."],
            {"The Model Verse": COLOR_MINT, "frontier AI": WHITE}
        )
        b6_dur = get_beat_duration(6, 3.98)
        t6 = scale_times(b6_dur, [1.0, 1.8, 0.8])

        logo_icon, brand_text, outro_sub = create_chalkboard_brand_outro(
            logo_title="THE MODEL VERSE",
            tagline="Engineering Behind Frontier AI Architectures",
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
            captions.morph_to(b6_parts[1], b6_hl) if len(b6_parts) > 1 else Wait(0.1),
            self.camera.frame.animate.scale(0.97),
            run_time=t6[1]
        )
        self.play(
            FadeOut(VGroup(logo_icon, brand_text, outro_sub)),
            captions.hide(),
            run_time=t6[2]
        )
