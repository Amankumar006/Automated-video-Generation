"""Living mechanism visuals for official AI product/news explainers.

The scene keeps the historical ``TechNewsScene`` API, but its visual language is
diagrammatic: information moves through lanes, loops, race tracks, benchmark
bars, and rollout timelines. Narration supplies the explanation; the canvas
shows the mechanism or state change instead of repeating prose in cards.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

from manim import *

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from manim_engine.base_scene import BaseShortScene
from manim_engine.primitives.chalkboard_captions import ChalkboardCaptions
from manim_engine.primitives.outro_card import create_chalkboard_brand_outro
from manim_engine.primitives.typography import clean_text
from pipeline.config import FONT_HELVETICA, COLOR_CYAN, COLOR_GOLD, COLOR_MINT

COLOR_GRID = "#1E293B"
COLOR_MUTED = "#94A3B8"
COLOR_WHITE = "#F8FAFC"
COLOR_PURPLE = "#A78BFA"


class TechNewsScene(BaseShortScene):
    """Six-beat tech-news explainer with non-card, mechanism-first visuals."""

    def construct(self):
        self.setup_canvas("TECH NEWS DISPATCH")
        captions = ChalkboardCaptions(self, y_pos=-3.45, default_font_size=21)
        spec = self._load_spec()
        meta = spec.get("metadata", {})
        news_meta = spec.get("tech_news_metadata", {})
        provider = news_meta.get("provider") or meta.get("provider") or self._infer_provider(spec)
        model_name = self._model_name(spec, news_meta)

        def beat(bid, fallback, duration, highlights=None):
            for item in spec.get("beats", []):
                if item.get("beat_id") == bid:
                    return (item.get("text", fallback), float(item.get("slot_duration", item.get("audio_duration", duration))), item.get("highlight_words", highlights or {}), item.get("visual_blueprint", {}) or {}, item)
            return fallback, duration, highlights or {}, {}, {}

        def role(bid, text, blueprint):
            explicit = blueprint.get("semantic_role") if isinstance(blueprint, dict) else None
            if explicit:
                return explicit
            low = text.lower()
            if any(k in low for k in ("benchmark", "score", "leaderboard", "baseline", "percent", "%")):
                return "benchmark"
            if any(k in low for k in ("api", "available", "access", "pricing", "price", "weights")):
                return "availability"
            if any(k in low for k in ("post-training", "post training", "agent", "training compute", "reward")):
                return "training_loop"
            if any(k in low for k in ("context", "token window", "latency", "faster", "speed", "throughput", "memory")):
                return "context_speed"
            return {1: "launch", 2: "context_speed", 3: "training_loop", 4: "benchmark", 5: "availability", 6: "product"}.get(bid, "product")

        b1, d1, h1, bp1, _ = beat(1, f"Here is what just changed with {model_name}.", 7.5, {model_name: COLOR_CYAN})
        hero = self._launch_visual(provider, model_name, bp1)
        self._play_beat(captions, b1, h1, hero[0], d1, pulse=hero[1])

        b2, d2, h2, bp2, _ = beat(2, "Post-training teaches the model to check its own work before it answers.", 7.5, {"post-training": COLOR_CYAN, "agent": COLOR_MINT})
        visual2 = self._post_training_loop(bp2) if role(2, b2, bp2) == "training_loop" else self._speed_race(b2, news_meta, bp2)
        self._play_beat(captions, b2, h2, visual2[0], d2, pulse=visual2[1])

        b3, d3, h3, bp3, _ = beat(3, "The model keeps a much longer working memory, so earlier context stays in reach.", 8.0, {"context": COLOR_CYAN, "faster": COLOR_MINT})
        visual3 = self._context_lanes(bp3) if role(3, b3, bp3) == "context_speed" else self._post_training_loop(bp3)
        self._play_beat(captions, b3, h3, visual3[0], d3, pulse=visual3[1])

        b4, d4, h4, bp4, raw4 = beat(4, "On the published tests, the new model clears real baselines.", 8.0, {"published tests": COLOR_CYAN})
        visual4 = self._benchmark_bars(b4, news_meta, model_name, bp4, raw4) if role(4, b4, bp4) == "benchmark" else self._speed_race(b4, news_meta, bp4)
        self._play_beat(captions, b4, h4, visual4[0], d4, pulse=visual4[1])

        b5, d5, h5, bp5, _ = beat(5, "You can follow the release from announcement to API and production access.", 8.0, {"API": COLOR_CYAN, "available": COLOR_MINT})
        visual5 = self._availability_timeline(b5, news_meta, bp5) if role(5, b5, bp5) == "availability" else self._benchmark_bars(b5, news_meta, model_name, bp5, {})
        self._play_beat(captions, b5, h5, visual5[0], d5, pulse=visual5[1])

        b6, d6, h6, bp6, _ = beat(6, "K3.1 Pro turns long-horizon work into a product feature.", 8.0, {"product feature": COLOR_CYAN})
        feature = self._product_feature(model_name)
        self._play_beat(captions, b6, h6, feature[0], d6, pulse=feature[1])

        logo_icon, brand_text, sub = create_chalkboard_brand_outro(logo_title="THE MODEL VERSE", tagline="Follow for Daily AI Lab Drops", url="themodelverse.in", y_center=0.3)
        outro = Group(logo_icon, brand_text, sub)
        self.play(FadeIn(outro, scale=0.94), captions.hide(run_time=0.25), run_time=0.45)
        self.wait(0.6)

    def _play_beat(self, captions, text, highlights, group, duration, pulse=None):
        enter = min(0.7, max(0.35, duration * 0.12))
        leave = min(0.35, max(0.2, duration * 0.06))
        active = max(0.25, duration - enter - leave)
        self.play(captions.morph_to(text, highlights=highlights, run_time=enter), FadeIn(group, shift=UP * 0.12), run_time=enter)
        self.play(pulse.animate(rate_func=there_and_back, run_time=active).scale(1.06)) if pulse is not None else self.wait(active)
        self.clean_transition([group], run_time=leave)

    def _launch_visual(self, provider, model_name, blueprint):
        asset_backplate = self._asset_backplate(provider, model_name, blueprint)
        title = clean_text(model_name, font=FONT_HELVETICA, font_size=29, color=COLOR_WHITE, weight=HEAVY, max_width=7.4).move_to([0, 4.35, 0])
        source = clean_text(f"{provider.upper()}  /  RELEASE SIGNAL", font=FONT_HELVETICA, font_size=12, color=COLOR_CYAN, weight=BOLD).move_to([0, 5.05, 0])
        core = Circle(radius=0.72, color=COLOR_CYAN, stroke_width=3).move_to([0, 1.35, 0])
        core_label = clean_text("MODEL", font=FONT_HELVETICA, font_size=13, color=COLOR_WHITE, weight=BOLD).move_to(core)
        rays = VGroup(*[Line([0, 0, 0], [0.52 * np.cos(a), 0.52 * np.sin(a), 0], color=COLOR_MINT, stroke_width=2).move_to(core.get_center()) for a in np.linspace(0, TAU, 8, endpoint=False)])
        token_stream = VGroup(*[self._token_tile(i, COLOR_GOLD if i % 3 == 0 else COLOR_CYAN) for i in range(9)])
        token_stream.arrange(RIGHT, buff=0.16).move_to([0, -0.15, 0])
        arrows = VGroup(*[Arrow(tile.get_bottom(), core.get_top(), buff=0.12, color=COLOR_CYAN, stroke_width=1.7, max_tip_length_to_length_ratio=0.18) for tile in token_stream])
        signal = DashedLine([-3.5, 2.8, 0], [3.5, 2.8, 0], dash_length=0.12, color=COLOR_GRID)
        signal_label = clean_text("PROMPT  →  ROUTE  →  ANSWER", font=FONT_HELVETICA, font_size=12, color=COLOR_MUTED, weight=BOLD).next_to(signal, UP, buff=0.16)
        return Group(asset_backplate, source, title, signal, signal_label, token_stream, arrows, rays, core, core_label), token_stream

    def _asset_backplate(self, provider, model_name, blueprint):
        """Add one restrained photographic layer behind the launch mechanism.

        A story may provide a local ``asset_path`` in its blueprint. The
        bundled server-rack image is a conservative infrastructure fallback;
        it is atmosphere, never narrated evidence. Keeping it behind the
        vectors preserves legibility and avoids the old stacked-card look.
        """
        params = blueprint.get("params", {}) if isinstance(blueprint, dict) else {}
        candidate = params.get("asset_path")
        if not candidate and isinstance(blueprint, dict):
            candidate = blueprint.get("asset_path")
        if not candidate:
            candidate = PROJECT_ROOT / "public" / "assets" / "broll" / "datacenter_server_rack.jpg"
        path = Path(candidate)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.exists() or path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            return VGroup()

        try:
            image = ImageMobject(str(path))
            image.scale_to_fit_width(7.55)
            if image.height > 5.25:
                image.scale_to_fit_height(5.25)
            image.move_to([0, 1.15, -3])
            image.set_opacity(0.34)
            tint = RoundedRectangle(
                corner_radius=0.18,
                width=image.width + 0.18,
                height=image.height + 0.18,
                stroke_color=COLOR_CYAN,
                stroke_width=1.1,
                fill_color="#06111D",
                fill_opacity=0.48,
            ).move_to(image.get_center()).set_z_index(-2)
            label = clean_text(
                f"{provider.upper()}  /  COMPUTE FLOOR",
                font=FONT_HELVETICA,
                font_size=10,
                color=COLOR_MUTED,
                weight=BOLD,
            ).move_to(image.get_bottom() + UP * 0.22).set_z_index(-1)
            image.set_z_index(-3)
            return Group(tint, image, label)
        except Exception as exc:
            print(f"⚠️ Could not load tech-news asset '{path}': {exc}")
            return VGroup()

    def _context_lanes(self, blueprint):
        title = clean_text("1M TOKEN CONTEXT", font=FONT_HELVETICA, font_size=24, color=COLOR_CYAN, weight=HEAVY).move_to([0, 4.6, 0])
        sub = clean_text("old context stays addressable", font=FONT_HELVETICA, font_size=13, color=COLOR_MUTED, weight=BOLD).next_to(title, DOWN, buff=0.16)
        lanes, moving = VGroup(), VGroup()
        for row in range(6):
            y = 2.95 - row * 0.72
            line = Line([-3.45, y, 0], [3.45, y, 0], color=COLOR_GRID, stroke_width=2)
            blocks = VGroup(*[Rectangle(width=0.34, height=0.22, color=COLOR_GRID, fill_color=COLOR_GRID, fill_opacity=0.9, stroke_width=0).move_to([-3.15 + col * 0.43, y, 0]) for col in range(15)])
            active = VGroup(*[Rectangle(width=0.34, height=0.22, color=COLOR_CYAN, fill_color=COLOR_CYAN, fill_opacity=1, stroke_width=0).move_to([-2.9 + (col + row) * 0.43, y, 0]) for col in range(2)])
            lanes.add(VGroup(line, blocks))
            moving.add(active)
        window = DashedLine([-1.35, -1.05, 0], [-1.35, 3.25, 0], dash_length=0.12, color=COLOR_GOLD, stroke_width=2)
        window_label = clean_text("attention window", font=FONT_HELVETICA, font_size=12, color=COLOR_GOLD, weight=BOLD).rotate(PI / 2).next_to(window, LEFT, buff=0.16)
        tag_old = clean_text("earlier tokens", font=FONT_HELVETICA, font_size=12, color=COLOR_MUTED, weight=BOLD).move_to([-2.45, -1.65, 0])
        tag_new = clean_text("new request", font=FONT_HELVETICA, font_size=12, color=COLOR_MINT, weight=BOLD).move_to([2.2, -1.65, 0])
        speed = clean_text("HIGHSPEED  ·  2–3× REPORTED", font=FONT_HELVETICA, font_size=13, color=COLOR_MINT, weight=HEAVY).move_to([0, -2.1, 0])
        return VGroup(title, sub, lanes, moving, window, window_label, tag_old, tag_new, speed), moving

    def _post_training_loop(self, blueprint):
        title = clean_text("POST-TRAINING LOOP", font=FONT_HELVETICA, font_size=24, color=COLOR_MINT, weight=HEAVY).move_to([0, 4.55, 0])
        labels = [("THINK", COLOR_CYAN), ("CHECK", COLOR_GOLD), ("REWARD", COLOR_MINT), ("UPDATE", COLOR_PURPLE)]
        nodes, points = VGroup(), [np.array([-2.35, 1.15, 0]), np.array([0, 2.7, 0]), np.array([2.35, 1.15, 0]), np.array([0, -0.55, 0])]
        for point, (label, color) in zip(points, labels):
            node = Circle(radius=0.58, color=color, stroke_width=3).move_to(point)
            txt = clean_text(label, font=FONT_HELVETICA, font_size=11, color=color, weight=BOLD).move_to(point)
            nodes.add(VGroup(node, txt))
        arrows = VGroup(*[Arrow(points[i], points[(i + 1) % 4], buff=0.66, color=COLOR_MUTED, stroke_width=2, max_tip_length_to_length_ratio=0.15) for i in range(4)])
        center = clean_text("better\nanswers", font=FONT_HELVETICA, font_size=16, color=COLOR_WHITE, weight=HEAVY, line_spacing=0.8).move_to([0, 1.05, 0])
        loop_dot = Dot(points[0], radius=0.08, color=COLOR_WHITE)
        return VGroup(title, arrows, nodes, center, loop_dot), loop_dot

    def _speed_race(self, text, news_meta, blueprint):
        title = clean_text("HIGHSPEED INFERENCE", font=FONT_HELVETICA, font_size=24, color=COLOR_GOLD, weight=HEAVY).move_to([0, 4.55, 0])
        subtitle = clean_text("same finish line, less waiting", font=FONT_HELVETICA, font_size=13, color=COLOR_MUTED, weight=BOLD).next_to(title, DOWN, buff=0.14)
        speedups = news_meta.get("speedups", [])
        match = re.search(r"(\d+(?:\.\d+)?)\s*[xX]", text)
        ratio = float(match.group(1)) if match else (float(str(speedups[0]).rstrip("xX")) if speedups and re.match(r"\d", str(speedups[0])) else 2.0)
        ratio = max(1.2, min(ratio, 8.0))
        tracks, pulse = VGroup(), None
        for idx, (label, color) in enumerate((("PREVIOUS", COLOR_MUTED), ("NEW PATH", COLOR_MINT))):
            y = 2.05 - idx * 1.55
            name = clean_text(label, font=FONT_HELVETICA, font_size=13, color=color, weight=BOLD).move_to([-2.85, y + 0.35, 0])
            rail = Line([-1.55, y, 0], [3.35, y, 0], color=COLOR_GRID, stroke_width=6)
            finish = Line([3.35, y - 0.35, 0], [3.35, y + 0.35, 0], color=COLOR_GOLD, stroke_width=2)
            finish_label = clean_text("ANSWER", font=FONT_HELVETICA, font_size=10, color=COLOR_GOLD, weight=BOLD).rotate(PI / 2).next_to(finish, RIGHT, buff=0.12)
            distance = 3.7 if idx else 2.0
            trace = Line([-1.55, y, 0], [-1.55 + distance, y, 0], color=color, stroke_width=8)
            marker = Dot(trace.get_end(), radius=0.13, color=color)
            value = clean_text(f"{ratio:.1f}×" if idx else "1×", font=FONT_HELVETICA, font_size=18, color=color, weight=HEAVY).next_to(trace, UP, buff=0.16)
            tracks.add(VGroup(name, rail, finish, finish_label, trace, marker, value))
            if idx:
                pulse = marker
        return VGroup(title, subtitle, tracks), pulse

    def _benchmark_bars(self, text, news_meta, model_name, blueprint, raw_beat=None):
        title = clean_text("PUBLISHED BENCHMARKS", font=FONT_HELVETICA, font_size=24, color=COLOR_CYAN, weight=HEAVY).move_to([0, 4.55, 0])
        subtitle = clean_text("higher is better · source values only", font=FONT_HELVETICA, font_size=12, color=COLOR_MUTED, weight=BOLD).next_to(title, DOWN, buff=0.14)
        values = self._benchmark_values(text, news_meta, model_name, raw_beat)
        rows = VGroup()
        for idx, (label, value, color) in enumerate(values[:4]):
            y = 2.65 - idx * 1.05
            name = clean_text(label, font=FONT_HELVETICA, font_size=12, color=COLOR_WHITE, weight=BOLD, max_width=1.75).move_to([-2.85, y, 0])
            base = Line([-1.75, y, 0], [2.75, y, 0], color=COLOR_GRID, stroke_width=10)
            fill = Line([-1.75, y, 0], [-1.75 + 4.5 * value / 100.0, y, 0], color=color, stroke_width=10)
            score = clean_text(f"{value:g}%", font=FONT_HELVETICA, font_size=18, color=color, weight=HEAVY).move_to([3.35, y, 0])
            rows.add(VGroup(name, base, fill, score))
        if not values:
            rows.add(clean_text("No published score in this release", font=FONT_HELVETICA, font_size=16, color=COLOR_MUTED, weight=BOLD).move_to([0, 1.1, 0]))
        return VGroup(title, subtitle, rows), (rows[-1] if len(rows) else None)

    def _product_feature(self, model_name):
        title = clean_text("LONG-HORIZON WORK  →  PRODUCT", font=FONT_HELVETICA, font_size=22, color=COLOR_CYAN, weight=HEAVY).move_to([0, 4.55, 0])
        sub = clean_text("one capability, three useful surfaces", font=FONT_HELVETICA, font_size=13, color=COLOR_MUTED, weight=BOLD).next_to(title, DOWN, buff=0.14)
        points = [(-2.65, 1.1, "LONG TASK", COLOR_GOLD), (0, 1.1, model_name.upper(), COLOR_CYAN), (2.65, 1.1, "REAL WORK", COLOR_MINT)]
        nodes = VGroup()
        for x, y, label, color in points:
            node = Circle(radius=0.55, color=color, stroke_width=3).move_to([x, y, 0])
            txt = clean_text(label, font=FONT_HELVETICA, font_size=10, color=color, weight=BOLD, max_width=1.0).move_to(node)
            nodes.add(VGroup(node, txt))
        arrows = VGroup(
            Arrow([-2.05, 1.1, 0], [-0.62, 1.1, 0], buff=0.12, color=COLOR_MUTED, stroke_width=2),
            Arrow([0.62, 1.1, 0], [2.05, 1.1, 0], buff=0.12, color=COLOR_MUTED, stroke_width=2),
        )
        note = clean_text("Kimi Code  ·  Kimi Work  ·  API", font=FONT_HELVETICA, font_size=14, color=COLOR_WHITE, weight=BOLD).move_to([0, -0.55, 0])
        pulse = nodes[1][0]
        return VGroup(title, sub, arrows, nodes, note), pulse

    def _availability_timeline(self, text, news_meta, blueprint):
        title = clean_text("FROM ANNOUNCEMENT TO ACCESS", font=FONT_HELVETICA, font_size=22, color=COLOR_GOLD, weight=HEAVY).move_to([0, 4.55, 0])
        timeline = Line([-3.2, 1.2, 0], [3.2, 1.2, 0], color=COLOR_GRID, stroke_width=4)
        nodes = VGroup()
        for idx, (label, color) in enumerate((("ANNOUNCED", COLOR_CYAN), ("API", COLOR_MINT), ("WEB", COLOR_GOLD), ("PRODUCTION", COLOR_PURPLE))):
            x = -3.0 + idx * 2.0
            node = Circle(radius=0.22, color=color, fill_color=color, fill_opacity=1, stroke_width=2).move_to([x, 1.2, 0])
            caption = clean_text(label, font=FONT_HELVETICA, font_size=11, color=color, weight=BOLD, max_width=1.55).move_to([x, 0.45 if idx % 2 == 0 else 2.0, 0])
            nodes.add(VGroup(node, caption))
        route = CurvedArrow([-3.0, 1.2, 0], [3.0, 1.2, 0], angle=-PI / 5, color=COLOR_CYAN, stroke_width=2)
        status = clean_text("availability is a sequence, not a single switch", font=FONT_HELVETICA, font_size=14, color=COLOR_WHITE, weight=BOLD).move_to([0, -0.6, 0])
        source = clean_text("VERIFY THE RELEASE CHANNEL BEFORE YOU SHIP", font=FONT_HELVETICA, font_size=11, color=COLOR_MUTED, weight=BOLD).move_to([0, -1.25, 0])
        return VGroup(title, timeline, route, nodes, status, source), nodes[-1]

    # Compatibility helpers retained for routing and existing tests.
    def _derive_pain_points(self, text: str, hl: dict) -> List[Tuple[str, str]]:
        low = text.lower()
        candidates = []
        if any(w in low for w in ("cost", "expensive", "price", "bills", "burn", "compute")):
            candidates.append(("EXPENSIVE INFERENCE COST", "Token spend constrains useful work"))
        if any(w in low for w in ("latency", "slow", "delay", "lag", "wait")):
            candidates.append(("HIGH LATENCY", "Slow generation blocks interaction"))
        if any(w in low for w in ("memory", "context", "vram", "kv cache")):
            candidates.append(("MEMORY PRESSURE", "Working state competes for hardware memory"))
        if any(w in low for w in ("concurrency", "queue", "server", "rate limit")):
            candidates.append(("QUEUEING", "Traffic turns useful work into waiting"))
        for word in hl:
            if len(candidates) >= 3:
                break
            candidates.append((f"{word.upper()} BOTTLENECK", f"Earlier systems spend more effort on {word.lower()}"))
        for item in (("DEPLOYMENT FRICTION", "Complex infrastructure slows iteration"), ("REASONING DRIFT", "Long tasks can lose the thread")):
            if len(candidates) >= 3:
                break
            if item[0] not in {x[0] for x in candidates}:
                candidates.append(item)
        return candidates[:3]

    def _derive_breakthrough_metrics(self, text: str, news_meta: dict, hl: dict):
        speedups = news_meta.get("speedups", [])
        speed = re.search(r"(\d+(?:\.\d+)?)\s*[xX]", text)
        pct = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
        if speed:
            hero, sub = f"{speed.group(1).upper()}X FASTER", "THROUGHPUT VS PREDECESSOR"
        elif pct:
            hero, sub = f"{pct.group(1)}% GAIN", "PUBLISHED EFFICIENCY RESULT"
        elif speedups:
            hero, sub = str(speedups[0]).upper(), "BENCHMARKED PERFORMANCE LEAP"
        else:
            hero, sub = "FRONTIER LEAP", "ENGINEERED FOR REAL-TIME WORK"
        words = list(hl) or ["context", "reasoning"]
        return hero, sub, ("CORE", str(words[0])[:18]), ("IMPACT", str(words[1] if len(words) > 1 else "speed")[:18])

    def _derive_benchmarks_or_capabilities(self, text: str, news_meta: dict, model_name: str, title_mob: Mobject):
        values = self._benchmark_values(text, news_meta, model_name)
        if values:
            rows = VGroup(*[VGroup(clean_text(f"{label}: {value:g}%", font=FONT_HELVETICA, font_size=14, color=color, weight=BOLD)) for label, value, color in values[:2]])
            return rows, rows[-1]
        return VGroup(clean_text("MECHANISM", font=FONT_HELVETICA, font_size=14, color=COLOR_MINT, weight=BOLD), clean_text("IMPACT", font=FONT_HELVETICA, font_size=14, color=COLOR_CYAN, weight=BOLD)), None

    def _derive_pricing_or_deployment(self, text: str, news_meta: dict, title_mob: Mobject):
        timeline, target = self._availability_timeline(text, news_meta, {})
        return timeline, target

    def _benchmark_values(self, text, news_meta, model_name, raw_beat=None):
        values = []
        blueprint = (raw_beat or {}).get("visual_blueprint", {}) if isinstance(raw_beat, dict) else {}
        contestants = blueprint.get("contestants", []) if isinstance(blueprint, dict) else []
        for contestant in contestants:
            if not isinstance(contestant, dict):
                continue
            try:
                value = float(contestant.get("value"))
            except (TypeError, ValueError):
                continue
            label = str(contestant.get("name") or "RESULT").upper()[:18]
            color = str(contestant.get("color") or COLOR_MINT)
            values.append((label, value, color))
        if values:
            return [(label, max(0, min(100, value)), color) for label, value, color in values[:4]]
        benchmarks = news_meta.get("benchmarks", {}) or {}
        for key, raw in benchmarks.items() if isinstance(benchmarks, dict) else []:
            match = re.search(r"(\d+(?:\.\d+)?)", str(raw))
            if match:
                values.append((str(key).upper()[:18], float(match.group(1)), COLOR_MINT))
        if not values:
            names = re.findall(r"(?:SWE-bench|AIME|GPQA|HumanEval|MATH|MMLU|ARC|LiveCode)", text, flags=re.IGNORECASE)
            pcts = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*%", text)]
            for idx, score in enumerate(pcts):
                values.append(((names[idx] if idx < len(names) else f"RESULT {idx + 1}").upper(), score, COLOR_MINT if idx == 0 else COLOR_CYAN))
        return [(label, max(0, min(100, value)), color) for label, value, color in values[:4]]

    def _token_tile(self, index: int, color: str):
        return RoundedRectangle(corner_radius=0.05, width=0.5, height=0.3, color=color, fill_color=color, fill_opacity=0.85, stroke_width=1)

    def _model_name(self, spec: dict, news_meta: dict) -> str:
        raw = news_meta.get("model_name") or spec.get("title") or "Frontier AI Release"
        if news_meta.get("model_name"):
            return str(raw)
        match = re.search(r"\b(o\d(?:-mini|-preview)?|gpt-[\w.]+|claude-[\w.]+|gemini-[\w.]+|deepseek-[\w.]+|kimi-[\w.]+|llama-[\w.]+)\b", str(raw), re.IGNORECASE)
        return match.group(1) if match else str(raw).split("—")[0].split(":")[0].strip()[:30]

    def _load_spec(self) -> dict:
        spec_path = os.environ.get("ACTIVE_SPEC_PATH")
        if spec_path and os.path.exists(spec_path):
            try:
                with open(spec_path, "r", encoding="utf-8") as handle:
                    return json.load(handle)
            except (OSError, json.JSONDecodeError):
                pass
        return {"title": "OpenAI o3-mini Reasoning Breakthrough", "category": "tech_news", "beats": []}

    def _infer_provider(self, spec: dict) -> str:
        text = (spec.get("title", "") + " " + spec.get("id", "")).lower()
        if "openai" in text or "o3" in text or "gpt" in text or "codex" in text:
            return "OpenAI"
        if "anthropic" in text or "claude" in text:
            return "Anthropic"
        if "deepmind" in text or "google" in text or "gemini" in text:
            return "Google DeepMind"
        if "hugging" in text or "hf" in text:
            return "Hugging Face"
        if "github" in text:
            return "GitHub"
        if "meta" in text or "llama" in text:
            return "Meta"
        if "microsoft" in text or "azure" in text:
            return "Microsoft"
        if "kimi" in text or "moonshot" in text:
            return "Moonshot AI"
        return "AI Frontier"
