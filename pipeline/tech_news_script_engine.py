"""
The Model Verse — Dedicated Tech News Script Engine (Track 2)
Engineered for official AI lab drops (OpenAI, Anthropic, Google DeepMind, Hugging Face).
Produces source-grounded newsroom scripts focusing on:
- The announcement and its concrete consequence
- The problem or tradeoff named by the source
- The mechanism or capability actually described
- Evidence that is present in the source metadata
- Pricing and availability only when explicitly reported
"""

import re
from typing import Dict, Any, Optional, List

COLOR_MINT = "#34D399"
COLOR_CYAN = "#38BDF8"
COLOR_GOLD = "#F59E0B"
COLOR_WHITE = "#FFFFFF"

# These are explanatory metaphors, not additional product claims.  They give
# the viewer one familiar mental model while leaving source facts untouched.
_ANALOGY_BY_SIGNAL = (
    (re.compile(r"\b(context|token|window|memory|long[- ]horizon)\b", re.I),
     "Think of it like keeping an entire bookshelf open instead of fetching one book at a time."),
    (re.compile(r"\b(agent|tool|workflow|planner|task|route)\b", re.I),
     "Think of it like handing a teammate a checklist instead of one instruction at a time."),
    (re.compile(r"\b(speed|fast|latency|response|faster|slow)\b", re.I),
     "It is like moving from one checkout line to an express lane: the job is the same, but the wait changes."),
)
_GENERIC_BEFORE_OPENING = re.compile(
    r"^\s*before\s+(?:you|your|we|the\s+next|another|updating|deploying|training|rendering|scaling)\b",
    re.I,
)


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
        abstract = (blog_meta.get("abstract") if blog_meta else None) or context or ""
        source_facts = self._normalise_facts(blog_meta)

        return f"""You are the Principal Tech News Reporter for 'The Model Verse' (themodelverse.in).
Generate a human, conversational 6-beat YouTube Shorts script covering an official AI release:
Provider: {prov}
Headline: {headline}
Details: {abstract}
Verified source fields: {source_facts}

Voice & Newsroom Persona:
- Tone: Clear, curious, authoritative, and human. Sound like a reporter explaining why the release matters to a smart developer.
- Strictly ban academic paper clichés ("Today we explore", "In this paper", "Researchers have proposed").
- Never use a generic "Before..." opening. Start with the event, a concrete consequence, or a useful question.
- Do not invent benchmarks, prices, speedups, architecture details, availability, or superlatives. If a fact is missing, say that it was not reported in the supplied source.
- Use the supplied evidence verbatim enough to preserve its meaning, but rewrite it into natural spoken language.

6-Beat Structure (Exactly 125-155 words total):
Beat 1 (0-3s, Hook): The release is real and the most concrete headline detail.
Beat 2 (3-12s, Why it matters): The user problem, limitation, or open question named by the source.
Beat 3 (12-24s, What changed): The architecture, capability, or product behavior explicitly described.
Beat 4 (24-35s, Evidence): The reported benchmark, comparison, or a transparent "not reported" caveat.
Beat 5 (35-44s, Practical check): Pricing, access, or an explicit limitation; never fill gaps with defaults.
Beat 6 (44-50s, Takeaway): A useful conclusion and a natural, brief follow invitation.

Output ONLY valid JSON matching this schema:
{{
  "id": "slug_id",
  "title": "{headline}",
  "category": "tech_news",
  "domain_taxonomy": "reasoning_models",
  "beats": [
    {{
      "beat_id": 1,
      "text": "...",
      "visual_focus": "Hero announcement card with {prov} emblem.",
      "highlight_words": {{"{headline.split()[0]}": "{COLOR_CYAN}"}},
      "svo_action": {{"subject": "{prov}", "action_verb": "launches", "direct_object": "New Model", "anchor_word": "dropped"}},
      "visual_blueprint": {{"layout": "news_hero_announcement", "title": "{headline.upper()}", "sub": "Official Lab Release", "params": {{}}}}
    }}
  ]
}}
"""

    def _build_deterministic_script(self, topic: str, blog_meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        prov = self._extract_provider(topic, blog_meta)
        headline = (blog_meta.get("title") if blog_meta else None) or topic
        model_name = self._extract_model_name(headline)
        clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", topic.lower()).strip("_")
        if not clean_id.startswith("news_") and not clean_id.startswith("blog_"):
            clean_id = f"news_{clean_id}"

        facts = self._normalise_facts(blog_meta)
        benchmarks = facts["benchmarks"]
        speedups = facts["speedups"]
        pricing = facts["pricing"]
        summary = facts["summary"]
        architecture = facts["architecture"]
        availability = facts["availability"]

        hook_detail = summary or self._first_value(speedups) or "the release details are now public"
        why_detail = (
            self._first_value(facts["limitations"], facts["problem"])
            or "the source leaves the comparison open, so the useful test is how it behaves in your own workload"
        )
        mechanism_detail = architecture or self._first_value(facts["capabilities"]) or (
            "the supplied release record does not describe a new internal mechanism"
        )
        evidence_detail = self._format_facts(benchmarks, "No benchmark result is reported in the supplied source metadata.")
        practical_parts = [self._format_facts(pricing, ""), self._format_facts(availability, "")]
        practical_detail = "; ".join(part for part in practical_parts if part)
        if not practical_detail:
            practical_detail = "Pricing and access details are not reported in the supplied source metadata"

        beats = [
            {
                "beat_id": 1,
                "name": "b1_hook",
                "text": f"{prov} just put {model_name} in front of developers. The release note says {hook_detail}.",
                "visual_focus": f"A release signal travels from the official {prov} source into a developer workflow; no static announcement card.",
                "highlight_words": {model_name: COLOR_CYAN, prov: COLOR_GOLD},
                "svo_action": {"subject": prov, "action_verb": "launches", "direct_object": model_name, "anchor_word": "dropped", "semantic_role": "state_transition"},
                "visual_blueprint": {"layout": "news_hero_announcement", "title": f"{prov.upper()} RELEASE", "sub": model_name, "params": {"provider": prov, "model_name": model_name, "detail": hook_detail}}
            },
            {
                "beat_id": 2,
                "name": "b2_predecessor",
                "text": f"Why should anyone care? {why_detail}.",
                "visual_focus": "A measurable constraint narrows the path through a developer workflow; show the named problem, not a generic bottleneck card.",
                "highlight_words": {"Why should anyone care?": COLOR_GOLD},
                "svo_action": {"subject": model_name, "action_verb": "answers", "direct_object": "a developer question", "anchor_word": "care", "semantic_role": "problem_framing"},
                "visual_blueprint": {"layout": "news_predecessor_ceiling", "title": "THE PRACTICAL QUESTION", "sub": "What the source actually says", "params": {"detail": why_detail}}
            },
            {
                "beat_id": 3,
                "name": "b3_core_breakthrough",
                "text": f"What changed is more specific: {model_name} {mechanism_detail}.",
                "visual_focus": "Animate the reported capability or mechanism as a transformation through the system, with no invented internals.",
                "highlight_words": {model_name: COLOR_MINT, "What changed": COLOR_CYAN},
                "svo_action": {"subject": model_name, "action_verb": "changes", "direct_object": "the reported workflow", "anchor_word": "changed", "semantic_role": "mechanism_explanation"},
                "visual_blueprint": {"layout": "news_breakthrough_architecture", "title": "WHAT CHANGED", "sub": "Source-grounded mechanism", "params": {"detail": mechanism_detail}}
            },
            {
                "beat_id": 4,
                "name": "b4_benchmarks",
                "text": f"Here is the evidence: {evidence_detail}",
                "visual_focus": "Draw only the reported benchmark values as proportional bars, or visibly mark the evidence gap when no score is supplied.",
                "highlight_words": {"evidence": COLOR_CYAN},
                "svo_action": {"subject": model_name, "action_verb": "reports", "direct_object": "measured evidence", "anchor_word": "evidence", "semantic_role": "metric_evaluation"},
                "visual_blueprint": {"layout": "news_benchmark_clash", "title": "THE EVIDENCE", "sub": "Reported results only", "params": {"benchmarks": benchmarks}}
            },
            {
                "beat_id": 5,
                "name": "b5_pricing_availability",
                "text": f"For a real deployment, check this first: {practical_detail}",
                "visual_focus": "Trace the release into an API or product path and expose the reported price/access state without implying a discount that was not published.",
                "highlight_words": {"real deployment": COLOR_MINT, "check this first": COLOR_CYAN},
                "svo_action": {"subject": "The release record", "action_verb": "defines", "direct_object": "the deployment check", "anchor_word": "deployment", "semantic_role": "practical_tradeoff"},
                "visual_blueprint": {"layout": "news_pricing_table", "title": "THE DEPLOYMENT CHECK", "sub": "Price and access from the source", "params": {"pricing": pricing, "availability": availability}}
            },
            {
                "beat_id": 6,
                "name": "b6_brand_outro",
                "text": f"So the takeaway is simple: evaluate {model_name} against the job you actually need done. Follow The Model Verse for the next clear breakdown.",
                "visual_focus": "A clean workflow returns to the original question, with a restrained Model Verse sign-off.",
                "highlight_words": {"The Model Verse": COLOR_MINT},
                "svo_action": {"subject": "The Model Verse", "action_verb": "clarifies", "direct_object": "AI releases", "anchor_word": "takeaway", "semantic_role": "takeaway"},
                "visual_blueprint": {"layout": "news_outro_summary", "title": "THE MODEL VERSE", "sub": "Clearer AI news", "params": {"model_name": model_name}}
            }
        ]

        spec = {
            "id": clean_id,
            "title": headline,
            "category": "tech_news",
            "provider": self._detect_provider(topic, blog_meta),
            "voice_style": "newsroom_anchor",
            "domain_taxonomy": "reasoning_models",
            "beats": beats,
            "manim_blueprints": [
                {"type": "hero_announcement", "title": f"{prov.upper()} OFFICIAL DROP"},
                {"type": "predecessor_ceiling", "title": "PREDECESSOR BOTTLENECKS"},
                {"type": "core_breakthrough", "title": "DISTILLED REASONING ENGINE"},
                {"type": "benchmark_comparison", "title": "VERIFIED BENCHMARKS"},
                {"type": "pricing_and_availability", "title": "TOKEN PRICING DELTAS"},
                {"type": "brand_outro", "title": "THE MODEL VERSE"}
            ],
            "domain_taxonomy": "reasoning_models",
            "beats": beats,
            "tech_news_metadata": {
                "provider": prov,
                "model_name": model_name,
                "benchmarks": benchmarks,
                "speedups": speedups,
                "pricing": pricing,
                "official_url": (blog_meta.get("official_url") or blog_meta.get("url", "")) if blog_meta else ""
            },
            "math_formulas": self._build_fact_formulas(clean_id, benchmarks, speedups, pricing)
        }
        return self._finalize_spec(spec, topic, blog_meta)

    def _normalise_facts(self, blog_meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Read facts from both current and legacy fetcher shapes without adding defaults."""
        meta = blog_meta or {}
        nested = meta.get("key_facts") or {}
        return {
            "summary": self._clean_fact(meta.get("summary") or meta.get("abstract") or nested.get("summary")),
            "benchmarks": meta.get("benchmarks") or nested.get("benchmarks") or {},
            "speedups": self._as_values(meta.get("speedups") or nested.get("speedups")),
            "pricing": meta.get("pricing") or nested.get("pricing") or {},
            "availability": self._as_values(meta.get("availability") or nested.get("availability")),
            "architecture": self._clean_fact(meta.get("architecture") or nested.get("architecture") or meta.get("method")),
            "limitations": self._as_values(meta.get("limitations") or nested.get("limitations")),
            "problem": self._as_values(meta.get("problem") or nested.get("problem") or meta.get("pain_points")),
            "capabilities": self._as_values(meta.get("capabilities") or nested.get("capabilities")),
        }

    @staticmethod
    def _clean_fact(value: Any) -> str:
        if value is None:
            return ""
        return re.sub(r"\s+", " ", str(value)).strip().rstrip(".")

    def _as_values(self, value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, dict):
            return [f"{key}: {self._clean_fact(item)}" for key, item in value.items() if self._clean_fact(item)]
        if isinstance(value, (list, tuple, set)):
            return [self._clean_fact(item) for item in value if self._clean_fact(item)]
        cleaned = self._clean_fact(value)
        return [cleaned] if cleaned else []

    @staticmethod
    def _first_value(*groups: Any) -> str:
        for group in groups:
            if isinstance(group, str) and group.strip():
                return group.strip().rstrip(".")
            if isinstance(group, (list, tuple)) and group:
                return str(group[0]).strip().rstrip(".")
        return ""

    def _format_facts(self, facts: Any, fallback: str) -> str:
        values = self._as_values(facts)
        if not values:
            return fallback
        if len(values) == 1:
            return values[0]
        return "; ".join(values[:3])

    def _build_fact_formulas(
        self,
        clean_id: str,
        benchmarks: Any,
        speedups: List[str],
        pricing: Any,
    ) -> List[Dict[str, Any]]:
        """Create formula overlays only from explicit source facts."""
        formulas: List[Dict[str, Any]] = []
        benchmark_values = self._as_values(benchmarks)
        if benchmark_values:
            formulas.append({"beat_id": 4, "latex": r"\mathrm{Reported\ evidence}", "filename": f"{clean_id}_beat4_formula.svg", "fontsize": 24, "color": "gold"})
        if speedups:
            formulas.append({"beat_id": 3, "latex": r"\mathrm{Reported\ capability}", "filename": f"{clean_id}_beat3_formula.svg", "fontsize": 24, "color": "mint"})
        if self._as_values(pricing):
            formulas.append({"beat_id": 5, "latex": r"\mathrm{Price/access\ as\ reported}", "filename": f"{clean_id}_beat5_formula.svg", "fontsize": 24, "color": "cyan"})
        return formulas

    def _finalize_spec(self, spec: Dict[str, Any], topic: str, blog_meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        spec["category"] = "tech_news"
        if not spec.get("tech_news_metadata"):
            prov = self._extract_provider(topic, blog_meta)
            spec["tech_news_metadata"] = {
                "provider": prov,
                "model_name": self._extract_model_name(spec.get("title", topic)),
                "official_url": (blog_meta.get("official_url") or blog_meta.get("url", "")) if blog_meta else ""
            }
        self._apply_narration_contract(spec)
        return spec

    def _apply_narration_contract(self, spec: Dict[str, Any]) -> None:
        """Apply final narration quality rules to both LLM and fallback output.

        This is deliberately a small, deterministic post-pass: it does not
        rewrite source facts or invent metrics. It only repairs a repetitive
        opening and adds one topic-matched mental model when the script has no
        concrete explanatory analogy at all.
        """
        beats = spec.get("beats") or []
        if not beats:
            return

        first_text = str(beats[0].get("text") or "").strip()
        before_repaired = False
        if _GENERIC_BEFORE_OPENING.match(first_text):
            remainder = re.sub(r"^\s*before\s+", "", first_text, count=1, flags=re.I).strip()
            beats[0]["text"] = f"Here is the actual update: {remainder}"
            before_repaired = True

        all_text = " ".join(str(beat.get("text") or "") for beat in beats)
        has_analogy = bool(re.search(r"\b(?:think of it like|it is like|it's like|imagine)\b", all_text, re.I))
        analogy_added = False
        if not has_analogy:
            analogy = next(
                (phrase for signal, phrase in _ANALOGY_BY_SIGNAL if signal.search(all_text)),
                "Think of it like a map: the useful part is finding the route you need, not collecting more paper.",
            )
            target = next((beat for beat in beats if beat.get("beat_id") == 2), beats[min(1, len(beats) - 1)])
            target_text = str(target.get("text") or "").strip().rstrip(".")
            target["text"] = f"{target_text}. {analogy}"
            analogy_added = True

        spec["narration_contract"] = {
            "generic_before_repaired": before_repaired,
            "analogy_added": analogy_added,
            "analogy_required": True,
        }

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
