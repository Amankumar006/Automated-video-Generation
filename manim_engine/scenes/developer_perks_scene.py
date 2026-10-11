"""
The Model Verse — Developer Perks & Startup Credits Scene (Category: developer_perks / perks)
UI Card & Screen Walkthrough Studio matching reference video (Alex Bowers standard):
- Split-screen layout with developer workspace backdrop
- Floating glassmorphism total dollar value cards
- Partner perk app tiles (API credits + Team seats)
- Interactive eligibility checklist with popping checkmarks
- Real console portal screenshot / form mockup
- Simulated animated cursor interaction with click ripple
- Floating 3D Twitter / Reddit social proof receipts
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
from manim_engine.primitives.lab_branding import get_lab_logo
from manim_engine.primitives.cursor_interaction import (
    create_cursor, create_click_ripple, create_input_field, create_browser_window_mockup
)
from manim_engine.primitives.social_proof_card import (
    create_social_proof_card, create_partner_app_tile
)
from pipeline.config import (
    FONT_HELVETICA, COLOR_MINT, COLOR_DANGER, COLOR_GOLD, COLOR_SLATE
)
from manim_engine.primitives.typography import clean_text

COLOR_CYAN = "#38BDF8"
COLOR_PURPLE = "#A855F7"
COLOR_CARD_BG = "#0B101D"
COLOR_BORDER = "#1E293B"


class DeveloperPerksScene(BaseShortScene):
    """
    Dedicated UI Card & Screen Walkthrough Studio for developer perks and startup credits.
    """

    def construct(self):
        self.setup_canvas("DEVELOPER PERKS")
        captions = ChalkboardCaptions(self, y_pos=-5.1, default_font_size=23)

        # 1. Load active specification
        spec = self._load_spec()
        perk_meta = spec.get("perk_metadata", {})
        provider = perk_meta.get("provider") or self._infer_provider(spec)
        headline = spec.get("title", "Developer Startup Program")
        dollar_value = perk_meta.get("value_usd") or 2800
        val_str = f"${dollar_value:,}" if isinstance(dollar_value, (int, float)) and dollar_value > 0 else "$1,000+"

        def get_beat(bid: int, def_text: str, def_dur: float, def_hl: dict = None):
            for b in spec.get("beats", []):
                if b.get("beat_id") == bid:
                    dur = float(b.get("slot_duration", b.get("audio_duration", def_dur)))
                    return b.get("text", def_text), dur, b.get("highlight_words", def_hl or {})
            return def_text, def_dur, def_hl or {}

        # -----------------------------------------------------------------
        # BEAT 1: Total Dollar Value Hero Hook (0 - ~8s)
        # -----------------------------------------------------------------
        b1_text, b1_dur, b1_hl = get_beat(
            1,
            f"Stop paying for AI APIs out of pocket: {provider} just launched their Startups Program with free credits!",
            7.5,
            {provider: COLOR_CYAN, "free credits": COLOR_MINT, "out of pocket": COLOR_DANGER}
        )

        # Top verified grant pill
        grant_pill = RoundedRectangle(
            corner_radius=0.10,
            width=5.2,
            height=0.45,
            color=COLOR_MINT,
            fill_color="#064E3B",
            fill_opacity=0.6,
            stroke_width=1.5
        ).shift(UP * 4.2)
        grant_txt = clean_text("✔ VERIFIED DEVELOPER GRANT", font=FONT_HELVETICA, font_size=13, color="#A7F3D0", weight=BOLD, max_width=4.8).move_to(grant_pill)
        pill_grp = VGroup(grant_pill, grant_txt)

        # Hero Value Container Card
        hero_box = RoundedRectangle(
            corner_radius=0.20,
            width=7.4,
            height=4.6,
            color=COLOR_MINT,
            fill_color=COLOR_CARD_BG,
            fill_opacity=0.96,
            stroke_width=2.4
        ).next_to(pill_grp, DOWN, buff=0.25)

        provider_logo = get_lab_logo(provider, size=1.5).move_to(hero_box).shift(UP * 1.1)

        val_badge = clean_text(val_str, font=FONT_HELVETICA, font_size=42, color=COLOR_MINT, weight=HEAVY)
        val_badge.next_to(provider_logo, DOWN, buff=0.25)

        val_sub = clean_text("IN FREE API CREDITS & DEVELOPER SEATS", font=FONT_HELVETICA, font_size=12, color="#CBD5E1", weight=BOLD, max_width=6.6)
        val_sub.next_to(val_badge, DOWN, buff=0.18)

        hero_prog_txt = clean_text(headline, font=FONT_HELVETICA, font_size=16, color=WHITE, weight=BOLD, max_width=6.6)
        hero_prog_txt.next_to(val_sub, DOWN, buff=0.20)

        hero_group = VGroup(pill_grp, hero_box, provider_logo, val_badge, val_sub, hero_prog_txt)
        t_in = 0.8
        t_out = 0.35
        t_action = max(0.2, b1_dur - t_in - t_out)
        self.play(
            captions.show(b1_text, highlights=b1_hl, run_time=t_in),
            FadeIn(hero_group, scale=0.95),
            run_time=t_in
        )
        self.play(val_badge.animate(rate_func=there_and_back, run_time=t_action).scale(1.08))
        self.clean_transition([hero_group], run_time=t_out)

        # -----------------------------------------------------------------
        # BEAT 2: Split-Screen Perk Package Tile Grid (~8s - ~16s)
        # -----------------------------------------------------------------
        b2_text, b2_dur, b2_hl = get_beat(
            2,
            "You get one thousand dollars in direct API credits plus a full free year of Claude Team for five seats.",
            8.0,
            {"one thousand dollars": COLOR_MINT, "Claude Team": COLOR_CYAN, "five seats": COLOR_GOLD}
        )

        grid_header = clean_text("WHAT YOU GET IN THE BUNDLE", font=FONT_HELVETICA, font_size=18, color=COLOR_CYAN, weight=HEAVY).shift(UP * 3.6)

        tile_1 = create_partner_app_tile(
            name=f"{provider} API",
            benefit="$1,000 Credits",
            sub_text="Sonnet 3.5 & Opus",
            accent_color=COLOR_MINT,
            width=3.5,
            height=2.3
        )

        tile_2 = create_partner_app_tile(
            name="Team Plan",
            benefit="1 Year Free",
            sub_text="5 Developer Seats ($1.8k)",
            accent_color=COLOR_PURPLE,
            width=3.5,
            height=2.3
        )

        top_tiles = VGroup(tile_1, tile_2).arrange(RIGHT, buff=0.35).next_to(grid_header, DOWN, buff=0.35)

        # Bottom scale tile
        tile_3 = RoundedRectangle(
            corner_radius=0.16,
            width=7.35,
            height=1.5,
            color=COLOR_GOLD,
            fill_color=COLOR_CARD_BG,
            fill_opacity=0.95,
            stroke_width=1.6
        ).next_to(top_tiles, DOWN, buff=0.3)

        t3_title = clean_text("🚀 EXPANDABLE VENTURE TIER", font=FONT_HELVETICA, font_size=13, color=COLOR_GOLD, weight=BOLD, max_width=6.5).align_to(tile_3, LEFT).shift(RIGHT * 0.4 + UP * 0.28)
        t3_sub = clean_text("VC-backed startups scale up to $100,000 in additional model credits", font=FONT_HELVETICA, font_size=11, color="#E2E8F0", weight=MEDIUM, max_width=6.5).align_to(tile_3, LEFT).shift(RIGHT * 0.4 + DOWN * 0.22)
        t3_grp = VGroup(tile_3, t3_title, t3_sub)

        tiles_group = VGroup(grid_header, top_tiles, t3_grp)
        t_in = 0.8
        t_out = 0.35
        t_action = max(0.2, b2_dur - t_in - t_out)
        self.play(
            captions.morph_to(b2_text, highlights=b2_hl, run_time=t_in),
            FadeIn(tiles_group, shift=UP * 0.25),
            run_time=t_in
        )
        self.play(
            tile_1.animate(rate_func=there_and_back, run_time=t_action).scale(1.04),
            tile_2.animate(rate_func=there_and_back, run_time=t_action).scale(1.04)
        )
        self.clean_transition([tiles_group], run_time=t_out)

        # -----------------------------------------------------------------
        # BEAT 3: Interactive Eligibility Checklist (~16s - ~24s)
        # -----------------------------------------------------------------
        b3_text, b3_dur, b3_hl = get_beat(
            3,
            "Qualifying is straightforward: you need an early-stage company, a live domain, and a working prototype.",
            8.0,
            {"early-stage company": COLOR_CYAN, "live domain": COLOR_MINT, "prototype": COLOR_GOLD}
        )

        check_box = RoundedRectangle(
            corner_radius=0.18,
            width=7.4,
            height=5.2,
            color=COLOR_CYAN,
            fill_color=COLOR_CARD_BG,
            fill_opacity=0.95,
            stroke_width=2.0
        ).shift(UP * 1.2)

        check_title = clean_text("WHO QUALIFIES? // ELIGIBILITY", font=FONT_HELVETICA, font_size=18, color=COLOR_CYAN, weight=HEAVY)
        check_title.align_to(check_box, UP).shift(DOWN * 0.45)

        criteria_items = [
            ("1. Early-Stage Startup", "<$5M Total Raised / Seed or Bootstrapped"),
            ("2. Live Website & Domain", "Active company domain (no generic gmail.com)"),
            ("3. Working Prototype / Code", "Active GitHub repo, MVP, or prototype demo")
        ]

        check_rows = []
        for t_str, s_str in criteria_items:
            row_box = RoundedRectangle(corner_radius=0.12, width=6.6, height=1.05, color="#334155", fill_color="#080C14", fill_opacity=0.92, stroke_width=1.2)
            
            # Text info
            r_title = clean_text(t_str, font=FONT_HELVETICA, font_size=14, color=WHITE, weight=BOLD, max_width=4.6).align_to(row_box, LEFT).shift(RIGHT * 0.35 + UP * 0.18)
            r_sub = clean_text(s_str, font=FONT_HELVETICA, font_size=11, color="#CBD5E1", weight=MEDIUM, max_width=4.6).align_to(row_box, LEFT).shift(RIGHT * 0.35 + DOWN * 0.18)
            
            # Popping Checkmark Badge
            chk_pill = RoundedRectangle(corner_radius=0.08, width=1.5, height=0.38, color=COLOR_MINT, fill_color="#064E3B", fill_opacity=0.8, stroke_width=1.2)
            chk_txt = clean_text("✔ PASS", font=FONT_HELVETICA, font_size=11, color="#A7F3D0", weight=BOLD).move_to(chk_pill)
            chk_badge = VGroup(chk_pill, chk_txt).align_to(row_box, RIGHT).shift(LEFT * 0.35)
            
            check_rows.append(VGroup(row_box, r_title, r_sub, chk_badge))

        rows_stack = VGroup(*check_rows).arrange(DOWN, buff=0.25).next_to(check_title, DOWN, buff=0.35)
        check_group = VGroup(check_box, check_title, rows_stack)

        t_in = 0.8
        t_out = 0.35
        self.play(
            captions.morph_to(b3_text, highlights=b3_hl, run_time=t_in),
            FadeIn(check_group, shift=UP * 0.2),
            run_time=t_in
        )
        
        # Pop in each checkmark badge
        n_rows = len(check_rows)
        t_row = min(0.45, max(0.15, (b3_dur - t_in - t_out - 0.2) / n_rows))
        for r in check_rows:
            self.play(r[3].animate(rate_func=there_and_back, run_time=t_row).scale(1.22))

        remaining_b3 = max(0.01, b3_dur - t_in - (n_rows * t_row) - t_out)
        if remaining_b3 > 0.05:
            self.wait(remaining_b3)
        self.clean_transition([check_group], run_time=t_out)

        # -----------------------------------------------------------------
        # BEAT 4: Real Portal Mockup & Simulated Cursor Interaction (~24s - ~33s)
        # -----------------------------------------------------------------
        b4_text, b4_dur, b4_hl = get_beat(
            4,
            f"To apply, head to {provider.lower()} console, link your GitHub repo, and hit submit.",
            8.0,
            {f"{provider.lower()} console": COLOR_CYAN, "GitHub repo": COLOR_GOLD, "submit": COLOR_MINT}
        )

        portal_url = perk_meta.get("official_url") or f"console.{provider.lower()}.com/startups"
        clean_url = portal_url.replace("https://", "").replace("http://", "").split("?")[0]
        if len(clean_url) > 34:
            clean_url = clean_url[:34]

        # Browser window frame
        portal_win = create_browser_window_mockup(
            url=clean_url,
            width=7.4,
            height=5.2,
            accent_color=COLOR_CYAN
        ).shift(UP * 1.2)

        # Form fields inside the portal
        f1 = create_input_field("Company Name", "NeuralFlow AI", width=6.6, height=0.72)
        f2 = create_input_field("Company Domain", "https://neuralflow.ai", width=6.6, height=0.72)
        f3 = create_input_field("GitHub Repository", "github.com/neuralflow/core", width=6.6, height=0.72)

        # Submit button
        btn_box = RoundedRectangle(
            corner_radius=0.12,
            width=6.6,
            height=0.75,
            color=COLOR_MINT,
            fill_color="#065F46",
            fill_opacity=0.95,
            stroke_width=2.0
        )
        btn_txt = clean_text("⚡ SUBMIT APPLICATION", font=FONT_HELVETICA, font_size=14, color=WHITE, weight=HEAVY, max_width=6.0).move_to(btn_box)
        submit_btn = VGroup(btn_box, btn_txt)

        form_col = VGroup(f1, f2, f3, submit_btn).arrange(DOWN, buff=0.22).move_to(portal_win).shift(DOWN * 0.25)
        portal_group = VGroup(portal_win, form_col)

        t_in = 0.7
        t_out = 0.35
        self.play(
            captions.morph_to(b4_text, highlights=b4_hl, run_time=t_in),
            FadeIn(portal_group, scale=0.96),
            run_time=t_in
        )

        # Animated cursor interaction
        cursor = create_cursor(scale=0.32, color=WHITE).move_to(f1).shift(RIGHT * 2.2 + UP * 0.1)
        self.play(FadeIn(cursor, scale=0.8), run_time=0.25)

        # Cursor glides down across inputs to the submit button
        self.play(cursor.animate(rate_func=smooth, run_time=1.0).move_to(btn_box).shift(DOWN * 0.05 + RIGHT * 0.1))

        # Button highlights on hover
        self.play(
            btn_box.animate(run_time=0.25).set_stroke(color=COLOR_GOLD, width=3.0).set_fill(color="#047857", opacity=1.0),
            cursor.animate(run_time=0.25).scale(0.92)
        )

        # Click ripple animation
        ripple = create_click_ripple(point=btn_box.get_center(), radius=0.8, color=COLOR_MINT)
        self.play(
            FadeIn(ripple, scale=0.3, run_time=0.2),
            ripple.animate(rate_func=linear, run_time=0.45).scale(1.8).set_opacity(0.0),
            btn_txt.animate(run_time=0.25).set_color(COLOR_GOLD)
        )
        self.remove(ripple)

        t_cursor_sub = 0.25 + 1.0 + 0.25 + 0.45
        remaining_b4 = max(0.01, b4_dur - t_in - t_cursor_sub - t_out)
        if remaining_b4 > 0.05:
            self.wait(remaining_b4)
        self.clean_transition([portal_group, cursor], run_time=t_out)

        # -----------------------------------------------------------------
        # BEAT 5: Floating 3D Social Proof Receipts (~33s - ~42s)
        # -----------------------------------------------------------------
        b5_text, b5_dur, b5_hl = get_beat(
            5,
            "Founders on Twitter and Reddit are getting approved in twenty-four to forty-eight hours.",
            8.0,
            {"approved": COLOR_MINT, "twenty-four hours": COLOR_GOLD, "Twitter": COLOR_CYAN}
        )

        social_header = clean_text("COMMUNITY APPROVAL RECEIPTS", font=FONT_HELVETICA, font_size=18, color=COLOR_CYAN, weight=HEAVY).shift(UP * 3.6)

        # Social proof card 1 (Twitter/X receipt)
        receipt_1 = create_social_proof_card(
            author="Alex Bowers",
            handle="@alex_dev",
            text=f"Got approved for the {provider} Startups Program in 24 hours! {val_str} credits already live in our console 🔥",
            time_str="2h ago",
            likes="412",
            reposts="89",
            platform="X / Twitter",
            width=7.4,
            height=2.8,
            accent_color="#1D9BF0"
        )

        # Social proof card 2 (Reddit testimonial snippet)
        reddit_bg = RoundedRectangle(corner_radius=0.14, width=7.4, height=1.65, color="#FF4500", fill_color=COLOR_CARD_BG, fill_opacity=0.95, stroke_width=1.6)
        r_hdr = clean_text("r/startups • 5h ago", font=FONT_HELVETICA, font_size=11, color="#CBD5E1", weight=BOLD).align_to(reddit_bg, LEFT).shift(RIGHT * 0.4 + UP * 0.38)
        r_txt = clean_text(f'"Verified approval! Applied on Tuesday, {val_str} credits active by Wednesday. Legit program."', font=FONT_HELVETICA, font_size=12, color="#E2E8F0", weight=MEDIUM, max_width=6.6)
        r_txt.next_to(r_hdr, DOWN, buff=0.15).align_to(r_hdr, LEFT)
        receipt_2 = VGroup(reddit_bg, r_hdr, r_txt)

        social_stack = VGroup(receipt_1, receipt_2).arrange(DOWN, buff=0.3).next_to(social_header, DOWN, buff=0.35)
        social_group = VGroup(social_header, social_stack)

        t_in = 0.8
        t_out = 0.35
        t_action = max(0.2, b5_dur - t_in - t_out)
        self.play(
            captions.morph_to(b5_text, highlights=b5_hl, run_time=t_in),
            FadeIn(social_group, shift=UP * 0.25),
            run_time=t_in
        )
        self.play(receipt_1.animate(rate_func=there_and_back, run_time=t_action).scale(1.03))
        self.clean_transition([social_group], run_time=t_out)

        # -----------------------------------------------------------------
        # BEAT 6: Outro & Actionable Save Call to Action (~42s - 48s)
        # -----------------------------------------------------------------
        b6_text, b6_dur, b6_hl = get_beat(
            6,
            "Save this video before the program caps, and follow The Model Verse for daily developer perks.",
            5.0,
            {"Save this video": COLOR_GOLD, "The Model Verse": COLOR_MINT}
        )

        # Actionable Save Bookmark Banner
        save_banner = RoundedRectangle(corner_radius=0.12, width=7.2, height=0.85, color=COLOR_GOLD, fill_color="#78350F", fill_opacity=0.6, stroke_width=1.8).shift(UP * 3.4)
        save_txt = clean_text("🔖 SAVE THIS REEL // BEFORE COHORT CAPS", font=FONT_HELVETICA, font_size=13, color=COLOR_GOLD, weight=HEAVY, max_width=6.8).move_to(save_banner)
        save_grp = VGroup(save_banner, save_txt)

        logo_icon, brand_text, sub = create_chalkboard_brand_outro(
            logo_title="THE MODEL VERSE",
            tagline="Follow for Daily Developer Perks",
            url="themodelverse.in",
            y_center=-0.8
        )
        outro = Group(logo_icon, brand_text, sub)
        final_group = Group(save_grp, outro)

        t_in = 0.8
        t_hold = max(0.2, b6_dur - t_in)
        self.play(
            captions.morph_to(b6_text, highlights=b6_hl, run_time=t_in),
            FadeIn(final_group, scale=0.94),
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
            "title": "Anthropic Claude Startups Program",
            "category": "developer_perks",
            "beats": []
        }

    def _infer_provider(self, spec: dict) -> str:
        text = (spec.get("title", "") + " " + spec.get("id", "")).lower()
        if "anthropic" in text or "claude" in text:
            return "Anthropic"
        elif "openai" in text:
            return "OpenAI"
        elif "microsoft" in text or "founders" in text or "azure" in text:
            return "Microsoft"
        elif "google" in text:
            return "Google Cloud"
        elif "aws" in text or "amazon" in text:
            return "AWS"
        elif "github" in text:
            return "GitHub"
        return "Anthropic"
