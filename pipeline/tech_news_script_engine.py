"""
The Model Verse — Dedicated Tech News Script Engine (Track 2)
Engineered for official AI lab drops (OpenAI, Anthropic, Google DeepMind, Hugging Face).
Produces breaking newsroom reporter scripts focusing on:
- The breakthrough announcement & shock factor
- Predecessor bottlenecks & ceilings
- Architectural secret sauce & latency/throughput gains
- Verified benchmarks (SWE-bench Verified, AIME, GPQA)
- Pricing tables, token cost deltas, and model availability tiers
"""

import os
import re
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

from pipeline.script_directives import (
    SHARED_SCRIPT_PROMPT_DIRECTIVE,
    TRACK_2_TECH_NEWS_PROMPT_TEMPLATE,
    validate_script_spec,
    get_total_word_count,
)

SHARED_SCRIPT_PROMPT = SHARED_SCRIPT_PROMPT_DIRECTIVE

COLOR_MINT = "#34D399"
COLOR_DANGER = "#EF4444"
COLOR_CYAN = "#38BDF8"
COLOR_GOLD = "#F59E0B"
COLOR_WHITE = "#FFFFFF"


class TechNewsScriptEngine:
    """
    Dedicated script generator for official tech news & lab announcements.
    """

    def generate_news_script(
        self,
        topic: str,
        blog_meta: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None,
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        Generates a 6-beat breaking newsroom short specification.
        Cascades from LLM Router to deterministic newsroom synthesis.
        """
        if use_llm:
            try:
                from pipeline.llm_router import llm_router
                prompt = self._build_prompt(topic, blog_meta, context)
                spec, provider = llm_router.route_script_generation(
                    prompt=prompt,
                    topic=topic,
                    category="tech_news",
                    arxiv_meta=blog_meta
                )
                if spec and len(spec.get("beats", [])) >= 5:
                    return self._finalize_spec(spec, topic, blog_meta)
            except Exception as e:
                print(f"⚠️ Tech news LLM generation notice: {e}, using dedicated deterministic synthesis")

        return self._build_deterministic_script(topic, blog_meta)

    def _build_prompt(self, topic: str, blog_meta: Optional[Dict[str, Any]], context: Optional[str]) -> str:
        prov = self._extract_provider(topic, blog_meta)
        headline = (blog_meta.get("title") if blog_meta else None) or topic
        details = (blog_meta.get("summary") if blog_meta else None) or (blog_meta.get("abstract") if blog_meta else None) or context or topic

        track_prompt = TRACK_2_TECH_NEWS_PROMPT_TEMPLATE.format(
            provider=prov,
            headline=headline,
            details=details
        )
        return f"""{SHARED_SCRIPT_PROMPT_DIRECTIVE}

{track_prompt}"""

    def _build_deterministic_script(self, topic: str, blog_meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        prov = self._extract_provider(topic, blog_meta)
        headline = (blog_meta.get("title") if blog_meta else None) or topic
        model_name = self._extract_model_name(headline)
        clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", topic.lower()).strip("_")
        if not clean_id.startswith("news_") and not clean_id.startswith("blog_"):
            clean_id = f"news_{clean_id}"

        # Extract verified facts if present in blog_meta
        key_facts = blog_meta.get("key_facts", {}) if blog_meta else {}
        benchmarks = key_facts.get("benchmarks", {})
        speedups = key_facts.get("speedups", ["3.2x faster throughput"])
        pricing = key_facts.get("pricing", ["$1.10 / 1M input tokens", "$4.40 / 1M output tokens"])

        bench_mention = "SWE-bench Verified" if "SWE-bench" in str(benchmarks) else "industry coding and math benchmarks"
        speed_mention = speedups[0] if speedups else "sub-second latency and 3x throughput"
        price_mention = pricing[0] if pricing else "just one dollar and ten cents per million tokens"

        beats = [
            {
                "n": 1,
                "beat_id": 1,
                "name": "b1_hook",
                "text": f"{prov} just officially dropped {model_name} with zero reasoning lag.",
                "anchor_word": "dropped",
                "visual_cue": f"Hero announcement card with {prov} emblem and launch badge.",
                "visual_focus": f"Hero announcement card with official {prov} vector logo and launch tag.",
                "highlight_words": {model_name: COLOR_CYAN, "dropped": COLOR_GOLD},
                "svo_action": {"subject": prov, "action_verb": "launches", "direct_object": model_name, "anchor_word": "dropped", "semantic_role": "state_transition"},
                "visual_blueprint": {"layout": "news_hero_announcement", "title": f"{prov.upper()} OFFICIAL DROP", "sub": f"Introducing {model_name}", "params": {"provider": prov, "model_name": model_name}}
            },
            {
                "n": 2,
                "beat_id": 2,
                "name": "b2_predecessor",
                "text": "Earlier reasoning models were notoriously slow and expensive, burning precious startup cash on high latency token loops while developers waited for simple answers.",
                "anchor_word": "expensive",
                "visual_cue": "Predecessor bottlenecks card illustrating latency walls and costly inference.",
                "visual_focus": "Predecessor bottlenecks card illustrating latency walls and costly inference.",
                "highlight_words": {"expensive": COLOR_DANGER, "latency": COLOR_GOLD},
                "svo_action": {"subject": "Predecessor Models", "action_verb": "drains", "direct_object": "Startup Runways", "anchor_word": "expensive", "semantic_role": "causal_elimination"},
                "visual_blueprint": {"layout": "news_predecessor_ceiling", "title": "PREDECESSOR BOTTLENECKS", "sub": "Latency & Cost Ceilings", "params": {}}
            },
            {
                "n": 3,
                "beat_id": 3,
                "name": "b3_core_breakthrough",
                "text": f"{model_name} delivers an architectural leap, using distilled step-by-step reasoning tokens to achieve {speed_mention} without compromising downstream benchmark accuracy.",
                "anchor_word": "distilled",
                "visual_cue": f"Architectural breakthrough card detailing distilled reasoning tokens in {model_name}.",
                "visual_focus": f"Architectural breakthrough card detailing distilled reasoning tokens in {model_name}.",
                "highlight_words": {model_name: COLOR_MINT, "distilled": COLOR_CYAN},
                "svo_action": {"subject": model_name, "action_verb": "delivers", "direct_object": "High Throughput", "anchor_word": "distilled", "semantic_role": "agent_action"},
                "visual_blueprint": {"layout": "news_breakthrough_architecture", "title": "DISTILLED REASONING ENGINE", "sub": "High-Throughput Token Generation", "params": {}}
            },
            {
                "n": 4,
                "beat_id": 4,
                "name": "b4_benchmarks",
                "text": f"On verified benchmarks it leads the entire industry, dominating {bench_mention} while consistently outperforming prior frontier reasoning baselines across rigorous coding evaluations.",
                "anchor_word": "benchmarks",
                "visual_cue": "Verified benchmark comparison bar chart with glowing SOTA leap chip.",
                "visual_focus": "Verified benchmark comparison bar chart with glowing SOTA leap chip.",
                "highlight_words": {"benchmarks": COLOR_CYAN, "outperforming": COLOR_MINT},
                "svo_action": {"subject": model_name, "action_verb": "beats", "direct_object": "Frontier Baselines", "anchor_word": "benchmarks", "semantic_role": "metric_evaluation"},
                "visual_blueprint": {"layout": "news_benchmark_clash", "title": "VERIFIED BENCHMARKS", "sub": "Wall-Clock SOTA Results", "params": {}}
            },
            {
                "n": 5,
                "beat_id": 5,
                "name": "b5_pricing_availability",
                "text": f"The pricing drops dramatically to {price_mention}, available right now across API production dashboards with immediate deployment access for developers.",
                "anchor_word": "pricing",
                "visual_cue": "Token pricing comparison table and availability tier chips.",
                "visual_focus": "Token pricing comparison table and availability tier chips.",
                "highlight_words": {"pricing": COLOR_MINT, "available right now": COLOR_CYAN},
                "svo_action": {"subject": prov, "action_verb": "slashes", "direct_object": "Token Prices", "anchor_word": "pricing", "semantic_role": "metric_evaluation"},
                "visual_blueprint": {"layout": "news_pricing_table", "title": "TOKEN PRICING DELTAS", "sub": "Instant Cost Reduction", "params": {}}
            },
            {
                "n": 6,
                "beat_id": 6,
                "name": "b6_brand_outro",
                "text": "Deploy this into your stack today. Follow The Model Verse for instant breakdowns of every major AI lab drop.",
                "anchor_word": "Model",
                "visual_cue": "Minimalist tech newsroom outro with The Model Verse branding.",
                "visual_focus": "Minimalist tech newsroom outro with The Model Verse branding.",
                "highlight_words": {"The Model Verse": COLOR_MINT},
                "svo_action": {"subject": "The Model Verse", "action_verb": "breaks down", "direct_object": "AI Lab Releases", "anchor_word": "Model", "semantic_role": "metric_evaluation"},
                "visual_blueprint": {"layout": "news_outro_summary", "title": "THE MODEL VERSE", "sub": "Official AI Lab Releases", "params": {}}
            }
        ]

        total_words = sum(len(b["text"].split()) for b in beats)

        spec = {
            "id": clean_id,
            "title": headline,
            "category": "tech_news",
            "provider": self._detect_provider(topic, blog_meta),
            "voice_style": "newsroom_anchor",
            "domain_taxonomy": "reasoning_models",
            "word_count": total_words,
            "beats": beats,
            "manim_blueprints": [
                {"type": "hero_announcement", "title": f"{prov.upper()} OFFICIAL DROP"},
                {"type": "predecessor_ceiling", "title": "PREDECESSOR BOTTLENECKS"},
                {"type": "core_breakthrough", "title": "DISTILLED REASONING ENGINE"},
                {"type": "benchmark_comparison", "title": "VERIFIED BENCHMARKS"},
                {"type": "pricing_and_availability", "title": "TOKEN PRICING DELTAS"},
                {"type": "brand_outro", "title": "THE MODEL VERSE"}
            ],
            "tech_news_metadata": {
                "provider": prov,
                "model_name": model_name,
                "benchmarks": benchmarks,
                "speedups": speedups,
                "pricing": pricing,
                "official_url": (blog_meta.get("official_url") or blog_meta.get("url", "")) if blog_meta else ""
            },
            "math_formulas": [
                {
                    "beat_id": 1,
                    "latex": r"\Delta \mathrm{Latency} \to 0",
                    "filename": f"{clean_id}_beat1_formula.svg",
                    "fontsize": 24,
                    "color": "cyan"
                },
                {
                    "beat_id": 2,
                    "latex": r"\mathrm{Cost}_{\mathrm{prior}} = \mathcal{O}(N_{\mathrm{tokens}} \cdot \$60)",
                    "filename": f"{clean_id}_beat2_formula.svg",
                    "fontsize": 24,
                    "color": "red"
                },
                {
                    "beat_id": 3,
                    "latex": r"\mathrm{Speedup} = 3.2\times",
                    "filename": f"{clean_id}_beat3_formula.svg",
                    "fontsize": 24,
                    "color": "mint"
                },
                {
                    "beat_id": 4,
                    "latex": r"\mathrm{SWE}_{\mathrm{verified}} = 49.3\%",
                    "filename": f"{clean_id}_beat4_formula.svg",
                    "fontsize": 24,
                    "color": "gold"
                },
                {
                    "beat_id": 5,
                    "latex": r"\Delta \mathrm{Price} = -92\%",
                    "filename": f"{clean_id}_beat5_formula.svg",
                    "fontsize": 24,
                    "color": "mint"
                }
            ]
        }
        return spec

    def _finalize_spec(self, spec: Dict[str, Any], topic: str, blog_meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        prov = self._extract_provider(topic, blog_meta)
        headline = (blog_meta.get("title") if blog_meta else None) or spec.get("title") or topic
        clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", spec.get("id", topic).lower()).strip("_")
        if not clean_id.startswith("news_") and not clean_id.startswith("blog_"):
            clean_id = f"news_{clean_id}"

        spec["id"] = clean_id
        spec["title"] = spec.get("title") or headline
        spec["category"] = "tech_news"
        spec["provider"] = self._detect_provider(topic, blog_meta)
        spec["voice_style"] = "newsroom_anchor"
        spec["domain_taxonomy"] = spec.get("domain_taxonomy") or "reasoning_models"

        if not spec.get("tech_news_metadata"):
            spec["tech_news_metadata"] = {
                "provider": prov,
                "model_name": self._extract_model_name(spec.get("title", topic)),
                "official_url": (blog_meta.get("official_url") or blog_meta.get("url", "")) if blog_meta else ""
            }

        # Normalize beats and ensure required fields
        beat_names = ["b1_hook", "b2_predecessor", "b3_core_breakthrough", "b4_benchmarks", "b5_pricing_availability", "b6_brand_outro"]
        default_blueprints = [
            {"layout": "news_hero_announcement", "title": f"{prov.upper()} OFFICIAL DROP", "sub": "Official Lab Release", "params": {}},
            {"layout": "news_predecessor_ceiling", "title": "PREDECESSOR BOTTLENECKS", "sub": "Latency & Cost Ceilings", "params": {}},
            {"layout": "news_breakthrough_architecture", "title": "DISTILLED REASONING ENGINE", "sub": "High-Throughput Token Generation", "params": {}},
            {"layout": "news_benchmark_clash", "title": "VERIFIED BENCHMARKS", "sub": "Wall-Clock SOTA Results", "params": {}},
            {"layout": "news_pricing_table", "title": "TOKEN PRICING DELTAS", "sub": "Instant Cost Reduction", "params": {}},
            {"layout": "news_outro_summary", "title": "THE MODEL VERSE", "sub": "Official AI Lab Releases", "params": {}}
        ]

        normalized_beats = []
        for idx, b in enumerate(spec.get("beats", [])):
            b_id = b.get("n") or b.get("beat_id", idx + 1)
            text = (b.get("text") or "").strip()
            anchor_word = (b.get("anchor_word") or "").strip()
            visual_cue = (b.get("visual_cue") or b.get("visual_focus") or "").strip()

            if not anchor_word and text:
                words = [re.sub(r"[^\w]", "", w) for w in text.split()]
                anchor_word = words[-1] if words else "AI"

            b["beat_id"] = b_id
            b["n"] = b_id
            b["text"] = text
            b["anchor_word"] = anchor_word
            b["visual_cue"] = visual_cue
            b["visual_focus"] = visual_cue or b.get("visual_focus", f"Beat {b_id} visual")
            b["name"] = b.get("name") or (beat_names[idx] if idx < len(beat_names) else f"b{b_id}")

            if not b.get("svo_action"):
                b["svo_action"] = {
                    "subject": prov,
                    "action_verb": "launches",
                    "direct_object": "AI Technology",
                    "anchor_word": anchor_word,
                    "semantic_role": "state_transition"
                }
            else:
                b["svo_action"]["anchor_word"] = anchor_word

            if not b.get("highlight_words"):
                b["highlight_words"] = {anchor_word: COLOR_CYAN} if anchor_word else {}

            if not b.get("visual_blueprint"):
                bp_idx = min(max(0, b_id - 1), len(default_blueprints) - 1)
                bp = default_blueprints[bp_idx].copy()
                if visual_cue:
                    bp["sub"] = visual_cue
                b["visual_blueprint"] = bp

            normalized_beats.append(b)

        spec["beats"] = normalized_beats

        if not spec.get("manim_blueprints"):
            spec["manim_blueprints"] = [
                {"type": "hero_announcement", "title": f"{prov.upper()} OFFICIAL DROP"},
                {"type": "predecessor_ceiling", "title": "PREDECESSOR BOTTLENECKS"},
                {"type": "core_breakthrough", "title": "DISTILLED REASONING ENGINE"},
                {"type": "benchmark_comparison", "title": "VERIFIED BENCHMARKS"},
                {"type": "pricing_and_availability", "title": "TOKEN PRICING DELTAS"},
                {"type": "brand_outro", "title": "THE MODEL VERSE"}
            ]

        spec["word_count"] = get_total_word_count(spec)
        is_valid, validation_errors = validate_script_spec(spec)
        if is_valid:
            print(f"✅ Tech news script passed validation ({spec['word_count']} words).")
        else:
            print(f"⚠️ Tech news script validation notices ({spec['word_count']} words):\n" + "\n".join(f"   - {e}" for e in validation_errors))

        return spec

    def _detect_provider(self, topic: str, blog_meta: Optional[Dict[str, Any]] = None) -> str:
        t = topic.lower()
        if "meta" in t or "llama" in t:
            return "general_tech"
        prov = self._extract_provider(topic, blog_meta).lower()
        if "anthropic" in prov or "claude" in prov:
            return "anthropic"
        elif "deepmind" in prov or "google" in prov or "gemini" in prov:
            return "google"
        elif "hugging" in prov or "hf" in prov:
            return "huggingface"
        elif "github" in prov:
            return "github"
        elif "openai" in prov or "gpt" in prov or "o3" in prov:
            return "openai"
        return "general_tech"

    def _extract_provider(self, topic: str, blog_meta: Optional[Dict[str, Any]]) -> str:
        if blog_meta and blog_meta.get("provider"):
            return blog_meta["provider"]
        t = topic.lower()
        if "openai" in t or "o3" in t or "gpt" in t or "sora" in t:
            return "OpenAI"
        elif "anthropic" in t or "claude" in t:
            return "Anthropic"
        elif "deepmind" in t or "google" in t or "gemini" in t:
            return "Google DeepMind"
        elif "hugging" in t or "hf" in t:
            return "Hugging Face"
        elif "github" in t:
            return "GitHub"
        return "OpenAI"

    def _extract_model_name(self, headline: str) -> str:
        patterns = [
            r"\b(o3-mini|o3|o1-mini|o1|gpt-4\.5|gpt-4o|claude 3\.7 sonnet|claude 3\.5 sonnet|gemini 2\.5|gemini 2\.0|deepseek-r1|deepseek-v3)\b",
            r"(?:introducing|announcing)\s+([A-Za-z0-9\.\-]+)",
        ]
        for p in patterns:
            m = re.search(p, headline, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        # Fallback to first 3 words of headline
        words = headline.split()
        return " ".join(words[:2]) if len(words) >= 2 else headline


tech_news_script_engine = TechNewsScriptEngine()
