"""
The Model Verse — Official Tech News Scene (Category: tech_news / blogs)
Launch & Benchmark Studio for official AI lab drops (OpenAI, Anthropic, Google DeepMind, HF):
- Official lab vector emblems
- Benchmark comparison bar charts (SWE-bench, AIME, GPQA)
- Pricing tables & latency delta meters
- Hero announcement cards
- Dark tech launchroom backdrop
"""

import os
import json
import re
from manim import *
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from manim_engine.base_scene import BaseShortScene
from manim_engine.primitives.chalkboard_captions import ChalkboardCaptions
from manim_engine.primitives.outro_card import create_chalkboard_brand_outro
from manim_engine.primitives.lab_branding import get_lab_logo, create_lab_hero_badge
from pipeline.config import (
    FONT_HELVETICA, COLOR_MINT, COLOR_DANGER, COLOR_GOLD, COLOR_SLATE
)
from manim_engine.primitives.typography import clean_text

COLOR_DARK_STUDIO = "#080B10"
COLOR_CYAN = "#38BDF8"
COLOR_CARD_BG = "#0D121F"
COLOR_BORDER = "#1E293B"


class TechNewsScene(BaseShortScene):
    """
    Dedicated Launch & Benchmark Studio for official AI lab announcements.
    """

    def construct(self):
        self.setup_canvas("TECH NEWS DISPATCH")
        captions = ChalkboardCaptions(self, y_pos=-5.1, default_font_size=23)

        # 1. Load active specification
        spec = self._load_spec()
        meta = spec.get("metadata", {})
        news_meta = spec.get("tech_news_metadata", {})
        provider = news_meta.get("provider") or meta.get("provider") or self._infer_provider(spec)
        model_name = news_meta.get("model_name") or spec.get("title", "Frontier AI Release").split("—")[0].strip()

        # Helper to get beat text, highlight words, and slot duration
        def get_beat(bid: int, def_text: str, def_dur: float, def_hl: dict = None):
            for b in spec.get("beats", []):
                if b.get("beat_id") == bid:
                    dur = float(b.get("slot_duration", b.get("audio_duration", def_dur)))
                    return b.get("text", def_text), dur, b.get("highlight_words", def_hl or {})
            return def_text, def_dur, def_hl or {}

        # -----------------------------------------------------------------
        # BEAT 1: Hero Announcement Card & Official Lab Emblem (0 - ~8s)
        # -----------------------------------------------------------------
        b1_text, b1_dur, b1_hl = get_beat(
            1,
            f"Before you update your stack, see what just dropped with {model_name}.",
            7.5,
            {model_name: COLOR_CYAN, "dropped": COLOR_GOLD}
        )

        hero_badge = create_lab_hero_badge(
            provider_name=provider,
            status_text="OFFICIAL LAB DROP",
            model_name=model_name,
            width=7.4
        ).shift(UP * 2.8)

        # Hero announcement container card
        hero_card = RoundedRectangle(
            corner_radius=0.18,
            width=7.4,
            height=3.8,
            color=COLOR_CYAN,
            fill_color=COLOR_CARD_BG,
            fill_opacity=0.95,
            stroke_width=2.2
        ).next_to(hero_badge, DOWN, buff=0.35)

        lab_emblem = get_lab_logo(provider, size=1.8).move_to(hero_card).shift(UP * 0.4)
        headline_txt = clean_text(
            spec.get("title", f"Introducing {model_name}"),
            font=FONT_HELVETICA,
            font_size=18,
            color=WHITE,
            weight=BOLD,
            max_width=6.6
        )
        headline_txt.next_to(lab_emblem, DOWN, buff=0.4)

        status_tag = clean_text(
            "⚡ FRONTIER REASONING & ACCELERATION",
            font=FONT_HELVETICA,
            font_size=12,
            color=COLOR_CYAN,
            weight=BOLD,
            max_width=6.6
        ).next_to(headline_txt, DOWN, buff=0.2)

        hero_group = VGroup(hero_badge, hero_card, lab_emblem, headline_txt, status_tag)
        t_in = 0.8
        t_out = 0.35
        t_action = max(0.2, b1_dur - t_in - t_out)
        self.play(
            captions.show(b1_text, highlights=b1_hl, run_time=t_in),
            FadeIn(hero_group, scale=0.94),
            run_time=t_in
        )
        
        # Subtle kinetic breathing while narration plays
        self.play(
            lab_emblem.animate(rate_func=there_and_back, run_time=t_action).scale(1.06),
            hero_card.animate(rate_func=there_and_back, run_time=t_action).set_stroke(color=COLOR_MINT, width=2.8)
        )
        self.clean_transition([hero_group], run_time=t_out)

        # -----------------------------------------------------------------
        # BEAT 2: Predecessor Ceiling & Cost/Latency Pain Point (~8s - ~16s)
        # -----------------------------------------------------------------
        b2_text, b2_dur, b2_hl = get_beat(
            2,
            "Prior reasoning models were powerful but suffered from high latency and steep token prices.",
            7.5,
            {"latency": COLOR_DANGER, "steep token prices": COLOR_GOLD}
        )

        ceiling_card = RoundedRectangle(
            corner_radius=0.18,
            width=7.4,
            height=5.2,
            color=COLOR_DANGER,
            fill_color=COLOR_CARD_BG,
            fill_opacity=0.95,
            stroke_width=2.0
        ).shift(UP * 1.2)

        ceiling_title = clean_text("PREDECESSOR BOTTLENECKS", font=FONT_HELVETICA, font_size=18, color=COLOR_DANGER, weight=HEAVY)
        ceiling_title.align_to(ceiling_card, UP).shift(DOWN * 0.45)

        # 3 Pain Point Rows
        pain_points = [
            ("🐢 HIGH INFERENCE LATENCY", "Slow token output blocks real-time developer workflows"),
            ("💸 EXPENSIVE API BILLS", "Reasoning tokens burn through seed runways ($15-$60/1M)"),
            ("⚠️ RESTRICTED CONCURRENCY", "Strict rate limits and heavy server queueing")
        ]
        row_groups = []
        for title, sub in pain_points:
            box = RoundedRectangle(corner_radius=0.12, width=6.6, height=0.95, color="#334155", fill_color="#080C14", fill_opacity=0.9, stroke_width=1.2)
            t_txt = clean_text(title, font=FONT_HELVETICA, font_size=13, color=WHITE, weight=BOLD, max_width=5.9).align_to(box, LEFT).shift(RIGHT * 0.35 + UP * 0.16)
            s_txt = clean_text(sub, font=FONT_HELVETICA, font_size=10, color="#CBD5E1", weight=MEDIUM, max_width=5.9).align_to(box, LEFT).shift(RIGHT * 0.35 + DOWN * 0.16)
            row_groups.append(VGroup(box, t_txt, s_txt))

        rows_col = VGroup(*row_groups).arrange(DOWN, buff=0.25).next_to(ceiling_title, DOWN, buff=0.35)
        ceiling_group = VGroup(ceiling_card, ceiling_title, rows_col)

        t_in = 0.8
        t_out = 0.35
        t_action = max(0.2, b2_dur - t_in - t_out)
        self.play(
            captions.morph_to(b2_text, highlights=b2_hl, run_time=t_in),
            FadeIn(ceiling_group, shift=UP * 0.2),
            run_time=t_in
        )
        self.play(rows_col[1].animate(rate_func=there_and_back, run_time=t_action).scale(1.03).set_stroke(color=COLOR_DANGER, width=2.0))
        self.clean_transition([ceiling_group], run_time=t_out)

        # -----------------------------------------------------------------
        # BEAT 3: Breakthrough Architecture & Distilled Speedup (~16s - ~24s)
        # -----------------------------------------------------------------
        b3_text, b3_dur, b3_hl = get_beat(
            3,
            f"Enter {model_name}. It uses distilled reasoning tokens to deliver frontier intelligence at speed.",
            8.0,
            {model_name: COLOR_MINT, "distilled": COLOR_CYAN}
        )

        arch_card = RoundedRectangle(
            corner_radius=0.18,
            width=7.4,
            height=5.2,
            color=COLOR_MINT,
            fill_color=COLOR_CARD_BG,
            fill_opacity=0.95,
            stroke_width=2.0
        ).shift(UP * 1.2)

        arch_title = clean_text("DISTILLED REASONING ENGINE", font=FONT_HELVETICA, font_size=18, color=COLOR_MINT, weight=HEAVY)
        arch_title.align_to(arch_card, UP).shift(DOWN * 0.45)

        # Throughput speedup meter
        meter_bg = RoundedRectangle(corner_radius=0.14, width=6.6, height=1.6, color="#334155", fill_color="#080C14", fill_opacity=0.95, stroke_width=1.4)
        meter_val = clean_text("3.2x FASTER", font=FONT_HELVETICA, font_size=32, color=COLOR_MINT, weight=HEAVY).move_to(meter_bg).shift(UP * 0.18)
        meter_sub = clean_text("THROUGHPUT VS PREDECESSOR REASONING MODELS", font=FONT_HELVETICA, font_size=10, color="#CBD5E1", weight=BOLD, max_width=6.2).next_to(meter_val, DOWN, buff=0.15)
        meter_grp = VGroup(meter_bg, meter_val, meter_sub).next_to(arch_title, DOWN, buff=0.35)

        # Features grid
        feat_1 = RoundedRectangle(corner_radius=0.12, width=3.15, height=1.4, color=COLOR_CYAN, fill_color="#080C14", fill_opacity=0.9, stroke_width=1.4)
        feat_1_t = clean_text("DISTILLED KV", font=FONT_HELVETICA, font_size=13, color=COLOR_CYAN, weight=BOLD, max_width=2.8).align_to(feat_1, UP).shift(DOWN * 0.3)
        feat_1_s = clean_text("60% Less RAM", font=FONT_HELVETICA, font_size=12, color=WHITE, weight=SEMIBOLD, max_width=2.8).next_to(feat_1_t, DOWN, buff=0.15)
        feat_1_grp = VGroup(feat_1, feat_1_t, feat_1_s)

        feat_2 = RoundedRectangle(corner_radius=0.12, width=3.15, height=1.4, color=COLOR_GOLD, fill_color="#080C14", fill_opacity=0.9, stroke_width=1.4)
        feat_2_t = clean_text("CODING SOTA", font=FONT_HELVETICA, font_size=13, color=COLOR_GOLD, weight=BOLD, max_width=2.8).align_to(feat_2, UP).shift(DOWN * 0.3)
        feat_2_s = clean_text("SWE-bench Top", font=FONT_HELVETICA, font_size=12, color=WHITE, weight=SEMIBOLD, max_width=2.8).next_to(feat_2_t, DOWN, buff=0.15)
        feat_2_grp = VGroup(feat_2, feat_2_t, feat_2_s)

        feats_row = VGroup(feat_1_grp, feat_2_grp).arrange(RIGHT, buff=0.3).next_to(meter_grp, DOWN, buff=0.25)
        arch_group = VGroup(arch_card, arch_title, meter_grp, feats_row)

        t_in = 0.8
        t_out = 0.35
        t_action = max(0.2, b3_dur - t_in - t_out)
        self.play(
            captions.morph_to(b3_text, highlights=b3_hl, run_time=t_in),
            FadeIn(arch_group, scale=0.96),
            run_time=t_in
        )
        self.play(meter_val.animate(rate_func=there_and_back, run_time=t_action).scale(1.08))
        self.clean_transition([arch_group], run_time=t_out)

        # -----------------------------------------------------------------
        # BEAT 4: Verified Benchmark Comparison Bar Chart (~24s - ~33s)
        # -----------------------------------------------------------------
        b4_text, b4_dur, b4_hl = get_beat(
            4,
            "On SWE-bench Verified, it hits forty-nine percent, dominating competitive math and coding benchmarks.",
            8.0,
            {"forty-nine percent": COLOR_MINT, "SWE-bench": COLOR_CYAN}
        )

        bench_card = RoundedRectangle(
            corner_radius=0.18,
            width=7.4,
            height=5.2,
            color=COLOR_CYAN,
            fill_color=COLOR_CARD_BG,
            fill_opacity=0.95,
            stroke_width=2.0
        ).shift(UP * 1.2)

        bench_title = clean_text("VERIFIED SOTA BENCHMARKS", font=FONT_HELVETICA, font_size=18, color=COLOR_CYAN, weight=HEAVY)
        bench_title.align_to(bench_card, UP).shift(DOWN * 0.45)

        # Benchmark 1: SWE-bench Verified
        b1_container = RoundedRectangle(corner_radius=0.12, width=6.6, height=1.75, color="#334155", fill_color="#080C14", fill_opacity=0.95, stroke_width=1.2)
        b1_lbl = clean_text("SWE-BENCH VERIFIED (CODING)", font=FONT_HELVETICA, font_size=12, color="#CBD5E1", weight=BOLD, max_width=4.0).align_to(b1_container, LEFT).shift(RIGHT * 0.35 + UP * 0.55)
        
        # New model bar
        bar_w_max = 3.6
        bar_new_w = bar_w_max * 0.92
        bar_new = Rectangle(width=bar_new_w, height=0.28, color=COLOR_MINT, fill_color=COLOR_MINT, fill_opacity=1.0, stroke_width=0).align_to(b1_container, LEFT).shift(RIGHT * 0.35 + UP * 0.12)
        val_new = clean_text(f"{model_name}: 49.3%", font=FONT_HELVETICA, font_size=12, color=COLOR_MINT, weight=BOLD, max_width=2.6).next_to(bar_new, RIGHT, buff=0.15)
        
        # Baseline model bar
        bar_old_w = bar_w_max * 0.65
        bar_old = Rectangle(width=bar_old_w, height=0.22, color="#475569", fill_color="#475569", fill_opacity=0.8, stroke_width=0).align_to(b1_container, LEFT).shift(RIGHT * 0.35 + DOWN * 0.28)
        val_old = clean_text("o1-preview: 38.2%", font=FONT_HELVETICA, font_size=11, color="#CBD5E1", weight=MEDIUM, max_width=2.6).next_to(bar_old, RIGHT, buff=0.15)
        
        # SOTA Leap Chip
        chip_bg = RoundedRectangle(corner_radius=0.08, width=1.8, height=0.32, color=COLOR_GOLD, fill_color="#78350F", fill_opacity=0.8, stroke_width=1.0)
        chip_txt = clean_text("+11.1% SOTA", font=FONT_HELVETICA, font_size=10, color=COLOR_GOLD, weight=BOLD, max_width=1.6).move_to(chip_bg)
        sota_chip = VGroup(chip_bg, chip_txt).align_to(b1_container, RIGHT).shift(LEFT * 0.35 + UP * 0.55)

        b1_group = VGroup(b1_container, b1_lbl, bar_new, val_new, bar_old, val_old, sota_chip).next_to(bench_title, DOWN, buff=0.25)

        # Benchmark 2: AIME 2024 (Math)
        b2_container = RoundedRectangle(corner_radius=0.12, width=6.6, height=1.5, color="#334155", fill_color="#080C14", fill_opacity=0.95, stroke_width=1.2)
        b2_lbl = clean_text("AIME 2024 (COMPETITIVE MATH)", font=FONT_HELVETICA, font_size=12, color="#CBD5E1", weight=BOLD, max_width=4.0).align_to(b2_container, LEFT).shift(RIGHT * 0.35 + UP * 0.42)
        
        bar_aime_w = bar_w_max * 0.88
        bar_aime = Rectangle(width=bar_aime_w, height=0.26, color=COLOR_CYAN, fill_color=COLOR_CYAN, fill_opacity=1.0, stroke_width=0).align_to(b2_container, LEFT).shift(RIGHT * 0.35 + DOWN * 0.08)
        val_aime = clean_text(f"{model_name}: 87.3%", font=FONT_HELVETICA, font_size=12, color=COLOR_CYAN, weight=BOLD, max_width=2.6).next_to(bar_aime, RIGHT, buff=0.15)

        b2_group = VGroup(b2_container, b2_lbl, bar_aime, val_aime).next_to(b1_group, DOWN, buff=0.2)
        bench_group = VGroup(bench_card, bench_title, b1_group, b2_group)

        t_in = 0.8
        t_out = 0.35
        t_action = max(0.2, b4_dur - t_in - t_out)
        self.play(
            captions.morph_to(b4_text, highlights=b4_hl, run_time=t_in),
            FadeIn(bench_group, shift=UP * 0.2),
            run_time=t_in
        )
        self.play(sota_chip.animate(rate_func=there_and_back, run_time=t_action).scale(1.15))
        self.clean_transition([bench_group], run_time=t_out)

        # -----------------------------------------------------------------
        # BEAT 5: Pricing Table & Availability Deltas (~33s - ~42s)
        # -----------------------------------------------------------------
        b5_text, b5_dur, b5_hl = get_beat(
            5,
            "The pricing delta is wild: just one dollar and ten cents per million tokens, available now.",
            8.0,
            {"one dollar and ten cents": COLOR_MINT, "available now": COLOR_CYAN}
        )

        price_card = RoundedRectangle(
            corner_radius=0.18,
            width=7.4,
            height=5.2,
            color=COLOR_GOLD,
            fill_color=COLOR_CARD_BG,
            fill_opacity=0.95,
            stroke_width=2.0
        ).shift(UP * 1.2)

        price_title = clean_text("TOKEN PRICING & AVAILABILITY", font=FONT_HELVETICA, font_size=18, color=COLOR_GOLD, weight=HEAVY)
        price_title.align_to(price_card, UP).shift(DOWN * 0.45)

        # Price comparison grid
        p1_box = RoundedRectangle(corner_radius=0.12, width=6.6, height=1.35, color="#334155", fill_color="#080C14", fill_opacity=0.95, stroke_width=1.2)
        p1_lbl = clean_text("INPUT TOKENS", font=FONT_HELVETICA, font_size=12, color="#CBD5E1", weight=BOLD, max_width=3.0).align_to(p1_box, LEFT).shift(RIGHT * 0.35 + UP * 0.32)
        p1_val = clean_text("$1.10 / 1M", font=FONT_HELVETICA, font_size=20, color=COLOR_MINT, weight=HEAVY, max_width=3.0).align_to(p1_box, LEFT).shift(RIGHT * 0.35 + DOWN * 0.22)
        p1_old = clean_text("Was: $15.00/1M (-92%)", font=FONT_HELVETICA, font_size=13, color="#EF4444", weight=BOLD, max_width=3.0).align_to(p1_box, RIGHT).shift(LEFT * 0.35 + DOWN * 0.22)
        p1_grp = VGroup(p1_box, p1_lbl, p1_val, p1_old).next_to(price_title, DOWN, buff=0.3)

        p2_box = RoundedRectangle(corner_radius=0.12, width=6.6, height=1.35, color="#334155", fill_color="#080C14", fill_opacity=0.95, stroke_width=1.2)
        p2_lbl = clean_text("OUTPUT TOKENS", font=FONT_HELVETICA, font_size=12, color="#CBD5E1", weight=BOLD, max_width=3.0).align_to(p2_box, LEFT).shift(RIGHT * 0.35 + UP * 0.32)
        p2_val = clean_text("$4.40 / 1M", font=FONT_HELVETICA, font_size=20, color=COLOR_MINT, weight=HEAVY, max_width=3.0).align_to(p2_box, LEFT).shift(RIGHT * 0.35 + DOWN * 0.22)
        p2_old = clean_text("Was: $60.00/1M (-93%)", font=FONT_HELVETICA, font_size=13, color="#EF4444", weight=BOLD, max_width=3.0).align_to(p2_box, RIGHT).shift(LEFT * 0.35 + DOWN * 0.22)
        p2_grp = VGroup(p2_box, p2_lbl, p2_val, p2_old).next_to(p1_grp, DOWN, buff=0.2)

        # Availability Tier Pills
        t1 = RoundedRectangle(corner_radius=0.08, width=2.0, height=0.45, color=COLOR_CYAN, fill_color="#0F172A", fill_opacity=0.8, stroke_width=1.2)
        t1_txt = clean_text("API TIER 1-5", font=FONT_HELVETICA, font_size=10, color=COLOR_CYAN, weight=BOLD, max_width=1.8).move_to(t1)
        t2 = RoundedRectangle(corner_radius=0.08, width=2.0, height=0.45, color=COLOR_MINT, fill_color="#0F172A", fill_opacity=0.8, stroke_width=1.2)
        t2_txt = clean_text("CHATGPT PLUS", font=FONT_HELVETICA, font_size=10, color=COLOR_MINT, weight=BOLD, max_width=1.8).move_to(t2)
        t3 = RoundedRectangle(corner_radius=0.08, width=2.0, height=0.45, color=COLOR_GOLD, fill_color="#0F172A", fill_opacity=0.8, stroke_width=1.2)
        t3_txt = clean_text("TEAM / ENTERPRISE", font=FONT_HELVETICA, font_size=9, color=COLOR_GOLD, weight=BOLD, max_width=1.8).move_to(t3)
        tiers_row = VGroup(VGroup(t1, t1_txt), VGroup(t2, t2_txt), VGroup(t3, t3_txt)).arrange(RIGHT, buff=0.25).next_to(p2_grp, DOWN, buff=0.25)

        price_group = VGroup(price_card, price_title, p1_grp, p2_grp, tiers_row)
        t_in = 0.8
        t_out = 0.35
        t_action = max(0.2, b5_dur - t_in - t_out)
        self.play(
            captions.morph_to(b5_text, highlights=b5_hl, run_time=t_in),
            FadeIn(price_group, scale=0.96),
            run_time=t_in
        )
        self.play(p1_val.animate(rate_func=there_and_back, run_time=t_action).scale(1.10))
        self.clean_transition([price_group], run_time=t_out)

        # -----------------------------------------------------------------
        # BEAT 6: Outro & The Model Verse Brand Signature (~42s - 48s)
        # -----------------------------------------------------------------
        b6_text, b6_dur, b6_hl = get_beat(
            6,
            "Follow The Model Verse for instant breakdowns of every major AI lab release.",
            5.0,
            {"The Model Verse": COLOR_MINT}
        )
        logo_icon, brand_text, sub = create_chalkboard_brand_outro(
            logo_title="THE MODEL VERSE",
            tagline="Follow for Daily AI Lab Drops",
            url="themodelverse.in",
            y_center=0.8
        )
        outro = Group(logo_icon, brand_text, sub)
        t_in = 0.8
        t_hold = max(0.2, b6_dur - t_in)
        self.play(
            captions.morph_to(b6_text, highlights=b6_hl, run_time=t_in),
            FadeIn(outro, scale=0.92),
            run_time=t_in
        )
        self.wait(t_hold)

    def _load_spec(self) -> dict:
        spec_path = os.environ.get("ACTIVE_SPEC_PATH")
        if spec_path and os.path.exists(spec_path):
            try:
                with open(spec_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "title": "OpenAI o3-mini Reasoning Breakthrough",
            "category": "tech_news",
            "beats": []
        }

    def _infer_provider(self, spec: dict) -> str:
        text = (spec.get("title", "") + " " + spec.get("id", "")).lower()
        if "openai" in text or "o3" in text or "gpt" in text:
            return "OpenAI"
        elif "anthropic" in text or "claude" in text:
            return "Anthropic"
        elif "deepmind" in text or "google" in text or "gemini" in text:
            return "Google DeepMind"
        elif "hugging" in text or "hf" in text:
            return "Hugging Face"
        elif "github" in text:
            return "GitHub"
        return "OpenAI"
