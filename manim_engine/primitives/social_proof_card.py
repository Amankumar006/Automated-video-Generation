"""
The Model Verse — Floating 3D Social Proof Receipts & Partner App Tile Primitives
Visual components for high-converting social proof cards (Twitter/X & Reddit testimonials)
and partner perk application tiles matching the reference video standard.
"""

from typing import Optional, List, Dict, Any
from manim import *
import sys
import textwrap
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.config import FONT_HELVETICA
from manim_engine.primitives.typography import clean_text

COLOR_CARD_BG = "#0B101D"
COLOR_CARD_BORDER = "#1E293B"
COLOR_TWITTER_BLUE = "#1D9BF0"
COLOR_MINT = "#34D399"
COLOR_AMBER = "#F59E0B"
COLOR_PURPLE = "#A855F7"


def create_social_proof_card(
    author: str = "Alex Bowers",
    handle: str = "@alex_dev",
    text: str = "Got approved for the Claude Startups Program in 24 hours! $1,000 credits already in our console 🔥",
    time_str: str = "2h ago",
    likes: str = "412",
    reposts: str = "89",
    platform: str = "X / Twitter",
    width: float = 7.4,
    height: float = 3.2,
    accent_color: str = COLOR_TWITTER_BLUE,
    author_name: Optional[str] = None,
    post_text: Optional[str] = None,
    avatar_letter: Optional[str] = None,
    metric_text: Optional[str] = None
) -> VGroup:
    """
    Constructs a floating social proof receipt card styled as an X/Twitter post.
    """
    if author_name:
        author = author_name
    if post_text:
        text = post_text
    card_bg = RoundedRectangle(
        corner_radius=0.18,
        width=width,
        height=height,
        color="#334155",
        fill_color=COLOR_CARD_BG,
        fill_opacity=0.96,
        stroke_width=1.8
    )

    # Top platform pill
    platform_pill = RoundedRectangle(
        corner_radius=0.08,
        width=2.2,
        height=0.32,
        color=accent_color,
        fill_color="#0F172A",
        fill_opacity=0.8,
        stroke_width=1.0
    ).align_to(card_bg, UP).shift(DOWN * 0.18 + LEFT * (width / 2 - 1.4))
    platform_txt = clean_text(
        f"VERIFIED {platform.upper()}",
        font=FONT_HELVETICA,
        font_size=10,
        color=accent_color,
        weight=BOLD,
        max_width=2.0
    ).move_to(platform_pill)
    top_badge = VGroup(platform_pill, platform_txt)

    # Avatar circle
    initials = avatar_letter if avatar_letter else ("".join([w[0] for w in author.split()[:2]]).upper() or "DEV")
    avatar_bg = Circle(radius=0.32, color=accent_color, fill_color="#1E293B", fill_opacity=1.0, stroke_width=1.5)
    avatar_bg.align_to(card_bg, LEFT).shift(RIGHT * 0.45 + UP * 0.4)
    avatar_txt = clean_text(initials, font=FONT_HELVETICA, font_size=13, color=WHITE, weight=BOLD).move_to(avatar_bg)
    avatar = VGroup(avatar_bg, avatar_txt)

    # Author & Handle
    author_txt = clean_text(author, font=FONT_HELVETICA, font_size=16, color=WHITE, weight=BOLD, max_width=width - 2.8)
    verified_badge = clean_text("✔", font=FONT_HELVETICA, font_size=12, color=accent_color, weight=HEAVY)
    name_row = VGroup(author_txt, verified_badge).arrange(RIGHT, buff=0.10).next_to(avatar, RIGHT, buff=0.25).shift(UP * 0.12)

    handle_txt = clean_text(
        f"{handle} • {time_str}" if not metric_text else f"{handle} • {metric_text}",
        font=FONT_HELVETICA,
        font_size=12,
        color="#CBD5E1",
        weight=MEDIUM,
        max_width=width - 2.8
    )
    handle_txt.next_to(name_row, DOWN, buff=0.08).align_to(name_row, LEFT)

    # Tweet / Receipt Text
    body_txt = clean_text(
        text,
        font=FONT_HELVETICA,
        font_size=13,
        color="#E2E8F0",
        weight=MEDIUM,
        line_spacing=0.85,
        wrap_width=38,
        max_width=width - 0.9
    )
    body_txt.align_to(card_bg, LEFT).shift(RIGHT * 0.45 + DOWN * 0.45)

    # Engagement row (Likes & Reposts)
    like_icon = clean_text(f"❤️ {likes} Likes", font=FONT_HELVETICA, font_size=11, color="#F43F5E", weight=SEMIBOLD)
    repost_icon = clean_text(f"🔁 {reposts} Reposts", font=FONT_HELVETICA, font_size=11, color="#10B981", weight=SEMIBOLD)
    engage_row = VGroup(like_icon, repost_icon).arrange(RIGHT, buff=0.45).align_to(card_bg, LEFT).shift(RIGHT * 0.45 + DOWN * 1.15)

    return VGroup(card_bg, top_badge, avatar, name_row, handle_txt, body_txt, engage_row)


def create_partner_app_tile(
    name: str = "Claude API",
    benefit: str = "$1,000 Credits",
    sub_text: str = "Sonnet 3.5 & Opus",
    accent_color: str = COLOR_MINT,
    width: float = 3.55,
    height: float = 2.4,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    badge: Optional[str] = None
) -> VGroup:
    """
    Constructs an app tile displaying a specific developer perk / grant component.
    """
    if title:
        name = title
    if subtitle:
        sub_text = subtitle
    if badge:
        benefit = badge
    box = RoundedRectangle(
        corner_radius=0.16,
        width=width,
        height=height,
        color=accent_color,
        fill_color=COLOR_CARD_BG,
        fill_opacity=0.95,
        stroke_width=1.6
    )

    name_txt = clean_text(
        name.upper(),
        font=FONT_HELVETICA,
        font_size=13,
        color="#CBD5E1",
        weight=BOLD,
        max_width=width - 0.5
    )
    name_txt.align_to(box, UP).shift(DOWN * 0.35)

    val_txt = clean_text(
        benefit,
        font=FONT_HELVETICA,
        font_size=20,
        color=accent_color,
        weight=HEAVY,
        max_width=width - 0.5
    )
    val_txt.next_to(name_txt, DOWN, buff=0.20)

    sub_txt = clean_text(
        sub_text,
        font=FONT_HELVETICA,
        font_size=11,
        color="#E2E8F0",
        weight=MEDIUM,
        max_width=width - 0.5
    )
    sub_txt.next_to(val_txt, DOWN, buff=0.18)

    return VGroup(box, name_txt, val_txt, sub_txt)
