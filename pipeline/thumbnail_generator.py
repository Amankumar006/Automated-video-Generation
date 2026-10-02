"""
The Model Verse — Auto-Thumbnail / YouTube Shorts Poster Generator
Generates high-CTR 1080x1920 vertical posters with 3Blue1Brown chalkboard aesthetics,
glowing hook badges, authentic LaTeX vector formulas, and safe-zone compliance.
"""

import os
import sys
import json
import glob
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from PIL import Image, ImageDraw, ImageFont, ImageFilter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.config import (
    WORKSPACE_ROOT, BG_CARBON, COLOR_MINT, COLOR_CYAN,
    COLOR_GOLD, COLOR_DANGER, COLOR_SLATE, COLOR_CARD_BG
)

# Output directory for thumbnails
THUMBNAILS_DIR = PROJECT_ROOT / "public" / "thumbnails"
MATH_PNG_DIR = PROJECT_ROOT / "public" / "math_pngs"
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
MATH_PNG_DIR.mkdir(parents=True, exist_ok=True)

# System Font Search
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Bold.ttf"
]
MONO_CANDIDATES = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/SFMono-Regular.otf",
    "/Library/Fonts/Courier New Bold.ttf"
]

def get_font(size: int, is_mono: bool = False) -> ImageFont.FreeTypeFont:
    candidates = MONO_CANDIDATES if is_mono else FONT_CANDIDATES
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

# -------------------------------------------------------------
# Category & Topic Profiles (Pre-tuned High-CTR Configurations)
# -------------------------------------------------------------

CATEGORY_PROFILES = {
    "benchmark_news": {
        "pill_label": "BENCHMARK NEWS",
        "theme_color": (245, 158, 11),       # Gold
        "glow_color": (245, 158, 11, 180),
        "default_badge": "27x CHEAPER THAN o1",
        "badge_icon": "bolt",
        "default_svg": "grpo_formula.svg",
        "stat_label_1": "AIME 2024 ACCURACY:",
        "stat_val_1": "79.8% (#1 SOTA)",
        "stat_label_2": "INFERENCE COST:",
        "stat_val_2": "$0.55 vs $15.00"
    },
    "architecture_breakdown": {
        "pill_label": "ARCHITECTURE BREAKDOWN",
        "theme_color": (16, 185, 129),       # Mint
        "glow_color": (16, 185, 129, 180),
        "default_badge": "94.5% COMPUTE SAVED",
        "badge_icon": "rocket",
        "default_svg": "efficiency_math.svg",
        "stat_label_1": "ACTIVE PARAMETERS:",
        "stat_val_1": "37B / 671B (5.5%)",
        "stat_label_2": "ROUTING LATENCY:",
        "stat_val_2": "TOP-8 LASERS"
    },
    "mechanism_deepdive": {
        "pill_label": "MECHANISM DEEP DIVE",
        "theme_color": (0, 240, 255),        # Cyan
        "glow_color": (0, 240, 255, 180),
        "default_badge": "3x FASTER ATTENTION",
        "badge_icon": "bolt",
        "default_svg": "attention_equation.svg",
        "stat_label_1": "VRAM COMPLEXITY:",
        "stat_val_1": "O(1) SRAM TILES",
        "stat_label_2": "HARDWARE SPEED:",
        "stat_val_2": "HOPPER ASYNC TMA"
    },
    "model_showdown": {
        "pill_label": "MODEL SHOWDOWN",
        "theme_color": (255, 51, 102),       # Danger / Neon Red
        "glow_color": (255, 51, 102, 180),
        "default_badge": "OPEN WEIGHTS SHOCK",
        "badge_icon": "flame",
        "default_svg": "cost_disparity_r1.svg",
        "stat_label_1": "BENCHMARK PARITY:",
        "stat_val_1": "MATH-500: 97.3%",
        "stat_label_2": "API COST SPREAD:",
        "stat_val_2": "96% SAVINGS"
    }
}

# -------------------------------------------------------------
# Vector Icon Drawer
# -------------------------------------------------------------

def draw_vector_icon(draw: ImageDraw.ImageDraw, icon_type: str, cx: int, cy: int, color: Tuple[int, int, int, int], scale: float = 1.0):
    if icon_type == "bolt":
        pts = [
            (cx - 5*scale, cy - 18*scale),
            (cx + 8*scale, cy - 18*scale),
            (cx - 1*scale, cy - 2*scale),
            (cx + 12*scale, cy - 2*scale),
            (cx - 10*scale, cy + 18*scale),
            (cx - 3*scale, cy + 3*scale),
            (cx - 12*scale, cy + 3*scale)
        ]
        draw.polygon(pts, fill=color)
    elif icon_type == "rocket":
        # Streamlined vector rocket
        pts = [
            (cx, cy - 18*scale),
            (cx + 8*scale, cy - 6*scale),
            (cx + 8*scale, cy + 8*scale),
            (cx + 14*scale, cy + 14*scale),
            (cx + 4*scale, cy + 12*scale),
            (cx, cy + 16*scale),
            (cx - 4*scale, cy + 12*scale),
            (cx - 14*scale, cy + 14*scale),
            (cx - 8*scale, cy + 8*scale),
            (cx - 8*scale, cy - 6*scale)
        ]
        draw.polygon(pts, fill=color)
    elif icon_type == "flame":
        pts = [
            (cx, cy - 18*scale),
            (cx + 9*scale, cy - 6*scale),
            (cx + 12*scale, cy + 4*scale),
            (cx + 6*scale, cy + 16*scale),
            (cx - 6*scale, cy + 16*scale),
            (cx - 12*scale, cy + 4*scale),
            (cx - 9*scale, cy - 6*scale)
        ]
        draw.polygon(pts, fill=color)
    else:
        # Default star / diamond
        pts = [
            (cx, cy - 16*scale),
            (cx + 12*scale, cy),
            (cx, cy + 16*scale),
            (cx - 12*scale, cy)
        ]
        draw.polygon(pts, fill=color)

# -------------------------------------------------------------
# LaTeX SVG to Transparent PNG Renderer
# -------------------------------------------------------------

def render_math_svg_to_png(svg_path: Path, output_width: int = 860) -> Optional[Path]:
    """Renders a Computer Modern math SVG to a transparent PNG using Manim."""
    if not svg_path.exists():
        return None

    cache_name = f"{svg_path.stem}_{output_width}.png"
    cached_path = MATH_PNG_DIR / cache_name
    if cached_path.exists():
        return cached_path

    try:
        from manim import Scene, SVGMobject, config, WHITE

        config.pixel_width = output_width
        config.pixel_height = int(output_width * 0.32)
        config.frame_width = 8.6
        config.frame_height = 8.6 * 0.32
        config.transparent = True

        class MathSvgScene(Scene):
            def construct(self):
                svg = SVGMobject(str(svg_path))
                svg.set_color(WHITE)
                svg.scale_to_fit_width(8.0)
                self.add(svg)

        scene = MathSvgScene()
        scene.render()

        # Find Manim output file
        cands = list((PROJECT_ROOT / "media" / "images").glob("MathSvgScene*.png"))
        if cands:
            cands.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            im = Image.open(cands[0])
            im.save(cached_path)
            return cached_path
    except Exception as e:
        print(f"⚠️ Manim SVG conversion failed ({e}). Proceeding without math plate.")

    return None

# -------------------------------------------------------------
# Main Thumbnail Generator
# -------------------------------------------------------------

class ShortsThumbnailGenerator:
    """Produces 1080x1920 high-CTR YouTube Shorts poster thumbnails."""

    def __init__(self):
        self.width = 1080
        self.height = 1920

    def generate(
        self,
        spec: Dict[str, Any],
        base_keyframe_path: Optional[str] = None,
        output_path: Optional[str] = None,
        custom_badge: Optional[str] = None,
        custom_formula_svg: Optional[str] = None
    ) -> str:
        W, H = self.width, self.height
        spec_id = spec.get("id", "short")
        category = spec.get("category", "mechanism_deepdive")
        profile = CATEGORY_PROFILES.get(category, CATEGORY_PROFILES["mechanism_deepdive"])

        if not output_path:
            output_path = str(THUMBNAILS_DIR / f"{spec_id}_poster.png")

        # 1. Base Canvas Preparation
        if base_keyframe_path and os.path.exists(base_keyframe_path):
            base_img = Image.open(base_keyframe_path).convert("RGBA")
            if base_img.size != (W, H):
                base_img = base_img.resize((W, H), Image.Resampling.LANCZOS)
        else:
            # Standalone procedural chalkboard canvas
            base_img = Image.new("RGBA", (W, H), (10, 13, 20, 255))
            grid_draw = ImageDraw.Draw(base_img)
            # Dot matrix coordinate grid
            for gx in range(40, W, 40):
                for gy in range(40, H, 40):
                    grid_draw.point((gx, gy), fill=(255, 255, 255, 18))

        # 2. Chalkboard Safe-Zone & Contrast Vignette
        mask = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        m_draw = ImageDraw.Draw(mask)

        # Solid top header zone (0 to 450px)
        m_draw.rectangle([(0, 0), (W, 430)], fill=(10, 13, 20, 255))
        # Gradient transition (430 to 580px)
        for y in range(430, 580):
            a = int(255 * (1.0 - ((y - 430) / 150.0) ** 1.3))
            m_draw.line([(0, y), (W, y)], fill=(10, 13, 20, a))

        # Lower-mid transition (1150 to 1380px)
        for y in range(1150, 1380):
            a = int(255 * (((y - 1150) / 230.0) ** 1.3))
            m_draw.line([(0, y), (W, y)], fill=(10, 13, 20, a))
        # Solid bottom UI safe zone (1380 to 1920px)
        m_draw.rectangle([(0, 1380), (W, H)], fill=(10, 13, 20, 255))

        base_img = Image.alpha_composite(base_img, mask)

        # 3. Typography & Badges
        font_title = get_font(78)
        font_subtitle = get_font(38)
        font_badge = get_font(48)
        font_meta = get_font(26, is_mono=True)
        font_brand = get_font(30)
        font_stat_val = get_font(36)

        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        theme_col = profile["theme_color"]
        glow_col = profile["glow_color"]

        # --- Top Brand Bar (Y = 60 to 110) ---
        draw.rounded_rectangle([60, 60, 96, 96], radius=8, fill=(16, 185, 129, 255))
        draw.text((68, 65), "M", font=font_brand, fill=(10, 13, 20, 255))
        draw.text((110, 68), "THE MODEL VERSE", font=font_brand, fill=(248, 250, 252, 255))

        # Category Pill
        cat_text = profile["pill_label"]
        cat_bbox = font_meta.getbbox(cat_text)
        cat_w = cat_bbox[2] - cat_bbox[0] + 32
        draw.rounded_rectangle(
            [W - 60 - cat_w, 60, W - 60, 98],
            radius=19,
            fill=(17, 24, 39, 240),
            outline=(*theme_col, 255),
            width=2
        )
        draw.text((W - 60 - cat_w + 16, 66), cat_text, font=font_meta, fill=(*theme_col, 255))

        # --- Hero Title Headline (Y = 135 to 275) ---
        title = spec.get("title", spec_id).upper()
        # Parse model name vs topic
        if ":" in title:
            model_part, topic_part = title.split(":", 1)
        elif " - " in title:
            model_part, topic_part = title.split(" - ", 1)
        else:
            words = title.split()
            model_part = words[0] if len(words) > 0 else title
            topic_part = " ".join(words[1:]) if len(words) > 1 else ""

        model_part = model_part.strip()
        topic_part = topic_part.strip()

        # Title shadow & text
        draw.text((64, 139), model_part, font=font_title, fill=(0, 0, 0, 220))
        draw.text((60, 135), model_part, font=font_title, fill=(0, 240, 255, 255))

        draw.text((63, 228), topic_part or "ARCHITECTURE & MATHEMATICS", font=font_subtitle, fill=(0, 0, 0, 220))
        draw.text((60, 225), topic_part or "ARCHITECTURE & MATHEMATICS", font=font_subtitle, fill=(248, 250, 252, 255))

        meta = spec.get("metadata", {})

        # --- Hero Stat / Hook Badge (Y = 300 to 410) ---
        badge_candidate = (
            custom_badge
            or meta.get("efficiency_badge")
            or meta.get("payoff_badge")
            or (f"{meta['payoff_stat']} {meta['payoff_label']}" if "payoff_stat" in meta and "payoff_label" in meta else None)
            or profile["default_badge"]
        )
        # Clean leading emoji symbols for cleaner vector icon placement
        badge_text = badge_candidate.replace("⚡", "").replace("🔥", "").replace("🚀", "").strip()

        pill_rect = (60, 300, W - 60, 410)

        # Outer Neon Glow
        glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(glow_layer)
        g_draw.rounded_rectangle(pill_rect, radius=55, fill=glow_col)
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=24))
        base_img = Image.alpha_composite(base_img, glow_layer)

        # Pill Foreground
        draw.rounded_rectangle(
            pill_rect,
            radius=55,
            fill=(*theme_col, 255),
            outline=(254, 240, 138, 255) if theme_col == (245, 158, 11) else (255, 255, 255, 220),
            width=3
        )

        # Dynamically scale badge font if text is long
        badge_font_sz = 48
        cur_font_badge = font_badge
        bb = cur_font_badge.getbbox(badge_text)
        bw, bh = bb[2] - bb[0], bb[3] - bb[1]
        icon_space = 45
        while (bw + icon_space > W - 180) and badge_font_sz > 30:
            badge_font_sz -= 3
            cur_font_badge = get_font(badge_font_sz)
            bb = cur_font_badge.getbbox(badge_text)
            bw, bh = bb[2] - bb[0], bb[3] - bb[1]

        bx = (W - bw - icon_space) // 2 + icon_space
        by = pill_rect[1] + (pill_rect[3] - pill_rect[1] - bh) // 2 - 4

        # Draw Vector Icon
        icon_cx = bx - 28
        icon_cy = by + bh // 2 + 2
        draw_vector_icon(draw, profile["badge_icon"], icon_cx, icon_cy, (10, 13, 20, 255), scale=1.3)
        draw.text((bx, by), badge_text, font=cur_font_badge, fill=(10, 13, 20, 255))

        # --- Frosted Math Formula Plate (Y = 1140 to 1350) ---
        svg_filename = custom_formula_svg
        if not svg_filename:
            formulas = spec.get("math_formulas", [])
            if formulas:
                # 1. Pick the first valid formula svg that already exists on disk
                for f_info in formulas:
                    fn = f_info.get("filename") or f_info.get("svg_filename") or ""
                    if fn and (PROJECT_ROOT / "public" / "math_svgs" / fn).exists():
                        svg_filename = fn
                        break

                # 2. If not yet rendered on disk, dynamically render the paper's primary formula on-the-fly!
                if not svg_filename:
                    for f_info in formulas:
                        latex_str = f_info.get("latex", "")
                        target_fn = f_info.get("filename") or f_info.get("svg_filename") or f"{clean_id}_thumb_formula.svg"
                        if latex_str:
                            try:
                                from scripts.generate_math_svgs import render_math_to_svg
                                render_math_to_svg(latex_str, target_fn, fontsize=24)
                                if (PROJECT_ROOT / "public" / "math_svgs" / target_fn).exists():
                                    svg_filename = target_fn
                                    break
                            except Exception as e:
                                print(f"⚠️ Thumbnail on-the-fly math render failed: {e}")

        if not svg_filename:
            svg_filename = profile.get("default_svg")

        math_svg_path = PROJECT_ROOT / "public" / "math_svgs" / svg_filename
        rendered_png = render_math_svg_to_png(math_svg_path, output_width=860)

        if rendered_png and rendered_png.exists():
            plate_rect = (60, 1140, W - 60, 1360)
            
            # Subtle cyan/gold plate glow
            p_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            pg_draw = ImageDraw.Draw(p_glow)
            pg_draw.rounded_rectangle(plate_rect, radius=18, fill=(*theme_col, 80))
            p_glow = p_glow.filter(ImageFilter.GaussianBlur(radius=15))
            base_img = Image.alpha_composite(base_img, p_glow)

            draw.rounded_rectangle(
                plate_rect,
                radius=18,
                fill=(17, 24, 39, 255),
                outline=(*theme_col, 160),
                width=2
            )

            math_img = Image.open(rendered_png).convert("RGBA")
            mw, mh = math_img.size
            target_mw = 860
            target_mh = int(mh * (target_mw / mw))
            math_resized = math_img.resize((target_mw, target_mh), Image.Resampling.LANCZOS)
            mx = (W - target_mw) // 2
            my = plate_rect[1] + (plate_rect[3] - plate_rect[1] - target_mh) // 2
            overlay.paste(math_resized, (mx, my), math_resized)

        # --- Impact Metrics Footer (Y = 1390 to 1570) ---
        stat_l1 = (
            (meta.get("model_a_stat_label") or meta.get("payoff_label") or profile.get("stat_label_1", "PRIMARY METRIC:"))
            .upper()
        )
        if not stat_l1.endswith(":"):
            stat_l1 += ":"
        stat_v1 = meta.get("model_a_stat") or meta.get("payoff_stat") or profile.get("stat_val_1", "SOTA BREAKTHROUGH")

        stat_l2 = (
            (meta.get("scale_label") or profile.get("stat_label_2", "ARCHITECTURE:"))
            .upper()
        )
        if not stat_l2.endswith(":"):
            stat_l2 += ":"
        stat_v2 = meta.get("scale_metric") or meta.get("solution_title") or profile.get("stat_val_2", "THE MODEL VERSE")

        # Format label and val neatly with dynamic offset
        bb_l1 = font_meta.getbbox(stat_l1)
        bb_l2 = font_meta.getbbox(stat_l2)
        val_x = max(460, 60 + max(bb_l1[2] - bb_l1[0], bb_l2[2] - bb_l2[0]) + 30)

        draw.text((60, 1400), stat_l1, font=font_meta, fill=(148, 163, 184, 255))
        draw.text((val_x, 1395), stat_v1, font=font_stat_val, fill=(16, 185, 129, 255))

        draw.text((60, 1475), stat_l2, font=font_meta, fill=(148, 163, 184, 255))
        draw.text((val_x, 1470), stat_v2, font=font_stat_val, fill=(*theme_col, 255))

        draw.line([(60, 1545), (W - 60, 1545)], fill=(31, 41, 55, 255), width=2)
        arxiv_id = spec.get("arxiv_id", "")
        cite_str = f"themodelverse.in • arXiv:{arxiv_id}" if arxiv_id else "themodelverse.in • Full Breakdown"
        draw.text((60, 1565), cite_str, font=font_meta, fill=(100, 116, 139, 255))

        # --- Final Composite & Export ---
        final_img = Image.alpha_composite(base_img, overlay).convert("RGB")
        final_img.save(output_path, "PNG", quality=95)

        # Also save optimized JPEG (< 2MB) for YouTube API
        jpg_path = output_path.replace(".png", ".jpg")
        final_img.save(jpg_path, "JPEG", quality=90, optimize=True)

        print(f"📸 YouTube Shorts Poster generated: {output_path}")
        return output_path

# Global singleton
thumbnail_generator = ShortsThumbnailGenerator()
