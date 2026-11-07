"""
The Model Verse — Test Dynamic Word-by-Word Subtitle Rendering
Renders a 9:16 vertical short sequence demonstrating dynamic word-by-word
subtitle appearance using exact acoustic word timings.
"""

from manim import *
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from pipeline.config import (
    FONT_HELVETICA, COLOR_MINT, COLOR_GOLD, COLOR_CYAN,
    VIDEO_WIDTH, VIDEO_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT, BG_CARBON
)
from pipeline.subtitle_generator import generate_phrase_chunks

config.pixel_width = 540
config.pixel_height = 960
config.frame_width = FRAME_WIDTH
config.frame_height = FRAME_HEIGHT
config.background_color = BG_CARBON

SAMPLE_BEAT = {
    "beat_id": 1,
    "anchor_word": "bombshell",
    "word_timings": [
        {"word": "OpenAI", "start": 0.3, "end": 0.65},
        {"word": "just", "start": 0.65, "end": 0.90},
        {"word": "dropped", "start": 0.90, "end": 1.25},
        {"word": "a", "start": 1.25, "end": 1.40},
        {"word": "bombshell:", "start": 1.40, "end": 2.05},
        {"word": "GPT-6", "start": 2.15, "end": 2.65},
        {"word": "Cyber", "start": 2.65, "end": 3.00},
        {"word": "is", "start": 3.00, "end": 3.15},
        {"word": "officially", "start": 3.15, "end": 3.65},
        {"word": "here.", "start": 3.65, "end": 4.10},
    ]
}


class DynamicWordKaraokeScene(Scene):
    __test__ = False
    """
    Style 1: Karaoke Progressive Glow
    Phrase chunk is anchored at y = -3.45.
    Upcoming words are dimmed; active spoken word glows in Neon Cyan / Gold;
    past words remain crisp white.
    """
    def construct(self):
        # 1. Living carbon background
        bg_dots = [
            Dot(point=[x * 0.95, y * 0.95, 0], radius=0.02, color="#1E293B", fill_opacity=0.35)
            for x in range(-4, 5) for y in range(-7, 8)
        ]
        self.add(VGroup(*bg_dots))

        # Title pill
        header = Text("KARAOKE PROGRESSIVE GLOW", font=FONT_HELVETICA, font_size=16, color="#94A3B8", weight=BOLD).move_to([0, 6.5, 0])
        self.add(header)

        # 2. Subtitle container setup
        caption_chunks = generate_phrase_chunks([SAMPLE_BEAT])
        caption_target_y = -3.45
        caption_container = VGroup().move_to([0, caption_target_y, 0])
        caption_container.set_z_index(60)
        self.add(caption_container)

        state = {
            "chunk_idx": -1,
            "word_idx": -1,
            "word_mobjects": [],
            "pill_bg": None,
            "group": None
        }

        def update_caption(mob, dt):
            t = self.renderer.time
            matched = False

            for c_i, c in enumerate(caption_chunks):
                if c["start"] <= t < c["end"]:
                    matched = True
                    c_words = c.get("words", [])
                    highlight = c.get("highlight_word", "").strip(".,!?;:").lower()
                    h_color = c.get("highlight_color", COLOR_GOLD)

                    # Determine active word within this chunk
                    active_w_idx = -1
                    for w_i, w in enumerate(c_words):
                        if t >= w["start"]:
                            active_w_idx = w_i

                    # Need full rebuild if new chunk
                    if state["chunk_idx"] != c_i:
                        state["chunk_idx"] = c_i
                        state["word_idx"] = active_w_idx
                        state["word_mobjects"] = []

                        # Build individual word text mobjects
                        for w_i, w in enumerate(c_words):
                            raw_w = w["word"]
                            clean_w = raw_w.strip(".,!?;:").lower()
                            is_hl = (clean_w == highlight)
                            
                            if w_i < active_w_idx:
                                col = WHITE
                                op = 0.95
                            elif w_i == active_w_idx:
                                col = h_color if is_hl else COLOR_CYAN
                                op = 1.0
                            else:
                                col = "#475569"
                                op = 0.50

                            w_txt = Text(
                                raw_w,
                                font=FONT_HELVETICA,
                                font_size=20,
                                weight=BOLD,
                                color=col
                            )
                            w_txt.set_opacity(op)
                            state["word_mobjects"].append(w_txt)

                        txt_group = VGroup(*state["word_mobjects"]).arrange(RIGHT, buff=0.12)
                        if txt_group.width > 6.4:
                            txt_group.scale_to_fit_width(6.4)

                        pill_w = min(6.8, txt_group.width + 0.65)
                        pill_h = 0.76
                        bg = RoundedRectangle(
                            corner_radius=0.20,
                            width=pill_w,
                            height=pill_h,
                            fill_color="#080C14",
                            fill_opacity=0.92,
                            stroke_color="#334155",
                            stroke_width=1.4
                        )
                        cam_center = self.camera.frame.get_center() if hasattr(self.camera, "frame") else ORIGIN
                        state["group"] = VGroup(bg, txt_group).move_to([cam_center[0], cam_center[1] + caption_target_y, 0])
                        mob.become(state["group"])

                    # If same chunk but new active word -> update colors & opacities
                    elif state["word_idx"] != active_w_idx:
                        state["word_idx"] = active_w_idx
                        word_mobs = []
                        for w_i, w in enumerate(c_words):
                            raw_w = w["word"]
                            clean_w = raw_w.strip(".,!?;:").lower()
                            is_hl = (clean_w == highlight)

                            if w_i < active_w_idx:
                                col = WHITE
                                op = 0.95
                            elif w_i == active_w_idx:
                                col = h_color if is_hl else COLOR_CYAN
                                op = 1.0
                            else:
                                col = "#475569"
                                op = 0.45

                            w_txt = Text(
                                raw_w,
                                font=FONT_HELVETICA,
                                font_size=20,
                                weight=BOLD,
                                color=col
                            )
                            w_txt.set_opacity(op)
                            word_mobs.append(w_txt)

                        txt_group = VGroup(*word_mobs).arrange(RIGHT, buff=0.12)
                        if txt_group.width > 6.4:
                            txt_group.scale_to_fit_width(6.4)

                        pill_w = min(6.8, txt_group.width + 0.65)
                        pill_h = 0.76
                        bg = RoundedRectangle(
                            corner_radius=0.20,
                            width=pill_w,
                            height=pill_h,
                            fill_color="#080C14",
                            fill_opacity=0.92,
                            stroke_color="#334155",
                            stroke_width=1.4
                        )
                        cam_center = self.camera.frame.get_center() if hasattr(self.camera, "frame") else ORIGIN
                        mob.become(VGroup(bg, txt_group).move_to([cam_center[0], cam_center[1] + caption_target_y, 0]))
                    break

            if not matched and state["chunk_idx"] != -1:
                state["chunk_idx"] = -1
                state["word_idx"] = -1
                state["word_mobjects"] = []
                mob.become(VGroup())

        caption_container.add_updater(update_caption)
        self.wait(4.5)


class DynamicWordRevealScene(Scene):
    __test__ = False
    """
    Style 2: Progressive Word-by-Word Reveal (Typewriter Pop)
    Words physically appear one by one as spoken.
    """
    def construct(self):
        bg_dots = [
            Dot(point=[x * 0.95, y * 0.95, 0], radius=0.02, color="#1E293B", fill_opacity=0.35)
            for x in range(-4, 5) for y in range(-7, 8)
        ]
        self.add(VGroup(*bg_dots))

        header = Text("PROGRESSIVE WORD-BY-WORD REVEAL", font=FONT_HELVETICA, font_size=16, color="#94A3B8", weight=BOLD).move_to([0, 6.5, 0])
        self.add(header)

        caption_chunks = generate_phrase_chunks([SAMPLE_BEAT])
        caption_target_y = -3.45
        caption_container = VGroup().move_to([0, caption_target_y, 0])
        caption_container.set_z_index(60)
        self.add(caption_container)

        state = {
            "chunk_idx": -1,
            "word_idx": -1
        }

        def update_caption(mob, dt):
            t = self.renderer.time
            matched = False

            for c_i, c in enumerate(caption_chunks):
                if c["start"] <= t < c["end"]:
                    matched = True
                    c_words = c.get("words", [])
                    highlight = c.get("highlight_word", "").strip(".,!?;:").lower()
                    h_color = c.get("highlight_color", COLOR_GOLD)

                    # Determine active word within this chunk
                    active_w_idx = -1
                    for w_i, w in enumerate(c_words):
                        if t >= w["start"]:
                            active_w_idx = w_i

                    if active_w_idx < 0:
                        mob.become(VGroup())
                        break

                    # Update only when chunk or word changes
                    if state["chunk_idx"] != c_i or state["word_idx"] != active_w_idx:
                        state["chunk_idx"] = c_i
                        state["word_idx"] = active_w_idx

                        # Build only words up to active_w_idx
                        word_mobs = []
                        for w_i in range(active_w_idx + 1):
                            raw_w = c_words[w_i]["word"]
                            clean_w = raw_w.strip(".,!?;:").lower()
                            is_hl = (clean_w == highlight)
                            is_curr = (w_i == active_w_idx)

                            if is_curr:
                                col = h_color if is_hl else COLOR_CYAN
                            else:
                                col = WHITE

                            w_txt = Text(
                                raw_w,
                                font=FONT_HELVETICA,
                                font_size=20,
                                weight=BOLD,
                                color=col
                            )
                            word_mobs.append(w_txt)

                        txt_group = VGroup(*word_mobs).arrange(RIGHT, buff=0.12)
                        if txt_group.width > 6.4:
                            txt_group.scale_to_fit_width(6.4)

                        pill_w = min(6.8, txt_group.width + 0.65)
                        pill_h = 0.76
                        bg = RoundedRectangle(
                            corner_radius=0.20,
                            width=pill_w,
                            height=pill_h,
                            fill_color="#080C14",
                            fill_opacity=0.92,
                            stroke_color="#334155",
                            stroke_width=1.4
                        )
                        cam_center = self.camera.frame.get_center() if hasattr(self.camera, "frame") else ORIGIN
                        mob.become(VGroup(bg, txt_group).move_to([cam_center[0], cam_center[1] + caption_target_y, 0]))
                    break

            if not matched and state["chunk_idx"] != -1:
                state["chunk_idx"] = -1
                state["word_idx"] = -1
                mob.become(VGroup())

        caption_container.add_updater(update_caption)
        self.wait(4.5)


def test_phrase_chunks_preserve_word_timings():
    """Verifies that generate_phrase_chunks includes word-level records in every chunk."""
    chunks = generate_phrase_chunks([SAMPLE_BEAT])
    assert len(chunks) == 2
    assert "words" in chunks[0]
    assert len(chunks[0]["words"]) == 5
    assert chunks[0]["words"][0]["word"] == "OpenAI"
    assert chunks[0]["words"][-1]["word"] == "bombshell:"
    assert "words" in chunks[1]
    assert len(chunks[1]["words"]) == 5
    assert chunks[1]["words"][0]["word"] == "GPT-6"


def test_chalkboard_captions_pill_truncates_giant_paragraphs():
    """Verifies that ChalkboardCaptions never displays a 5-line 35-word text wall."""
    from manim_engine.primitives.chalkboard_captions import ChalkboardCaptions
    dummy_scene = Scene()
    captions = ChalkboardCaptions(dummy_scene, y_pos=-3.45)
    long_text = (
        "OpenAI just dropped a bombshell: GPT-6 Cyber is officially here. "
        "It is a new model built specifically to handle the high-stakes world of cybersecurity."
    )
    pill = captions._create_pill(long_text)
    assert pill is not None
    assert len(pill) == 2  # Text + underline

