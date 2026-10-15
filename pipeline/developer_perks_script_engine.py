"""
The Model Verse — Dedicated Developer Perks & Startup Credits Script Engine (Track 3)
Engineered for actionable developer perks and startup credits (e.g., Claude Startups,
OpenAI startup tier, AWS Activate, Microsoft Founders Hub, GitHub Student Pack).
Produces actionable deal guide scripts matching the reference video standard (Alex Bowers):
- Total dollar value hook
- Exact benefit package breakdown (credits + seats + tiers)
- Interactive eligibility checklist
- Step-by-step console application walkthrough
- Real community social proof receipts (Twitter / Reddit approvals)
- Urgent save call-to-action
"""

import os
import re
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

from pipeline.script_directives import (
    SHARED_SCRIPT_PROMPT_DIRECTIVE,
    TRACK_3_DEVELOPER_PERKS_PROMPT_TEMPLATE,
    validate_script_spec,
    get_total_word_count,
)

SHARED_SCRIPT_PROMPT = SHARED_SCRIPT_PROMPT_DIRECTIVE

COLOR_MINT = "#34D399"
COLOR_DANGER = "#EF4444"
COLOR_CYAN = "#38BDF8"
COLOR_GOLD = "#F59E0B"
COLOR_WHITE = "#FFFFFF"


class DeveloperPerksScriptEngine:
    """
    Dedicated script generator for developer perks, startup grants, and free credits.
    """

    def generate_perks_script(
        self,
        topic: str,
        perk_meta: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None,
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        Generates a 6-beat actionable deal guide short specification.
        Cascades from LLM Router to deterministic deal guide synthesis.
        """
        if use_llm:
            try:
                from pipeline.llm_router import llm_router
                prompt = self._build_prompt(topic, perk_meta, context)
                spec, provider = llm_router.route_script_generation(
                    prompt=prompt,
                    topic=topic,
                    category="developer_perks",
                    arxiv_meta=perk_meta
                )
                if spec and len(spec.get("beats", [])) >= 5:
                    return self._finalize_spec(spec, topic, perk_meta)
            except Exception as e:
                print(f"⚠️ Developer perks LLM generation notice: {e}, using dedicated deterministic synthesis")

        return self._build_deterministic_script(topic, perk_meta)

    def _build_prompt(self, topic: str, perk_meta: Optional[Dict[str, Any]], context: Optional[str]) -> str:
        prov = self._extract_provider(topic, perk_meta)
        headline = (perk_meta.get("title") if perk_meta else None) or (perk_meta.get("headline") if perk_meta else None) or topic
        val_str = self._extract_dollar_value(topic, perk_meta)
        details = (perk_meta.get("summary") if perk_meta else None) or (perk_meta.get("abstract") if perk_meta else None) or context or topic

        track_prompt = TRACK_3_DEVELOPER_PERKS_PROMPT_TEMPLATE.format(
            provider=prov,
            headline=headline,
            val_str=val_str,
            details=details
        )
        return f"""{SHARED_SCRIPT_PROMPT_DIRECTIVE}

{track_prompt}"""

    def _build_deterministic_script(self, topic: str, perk_meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        prov = self._extract_provider(topic, perk_meta)
        headline = (perk_meta.get("title") if perk_meta else None) or (perk_meta.get("headline") if perk_meta else None) or topic
        val_str = self._extract_dollar_value(topic, perk_meta)
        val_num_match = re.search(r"\$([\d,]+)", val_str)
        val_usd = int(val_num_match.group(1).replace(",", "")) if val_num_match else 2800

        clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", topic.lower()).strip("_")
        if not clean_id.startswith("perk_"):
            clean_id = f"perk_{clean_id}"

        # Extract eligibility and steps if available
        eligibility = perk_meta.get("eligibility_criteria", []) if perk_meta else []
        steps = perk_meta.get("step_by_step_application", []) if perk_meta else []
        official_url = perk_meta.get("official_url") or f"console.{prov.lower().replace(' ', '')}.com/startups"

        beats = [
            {
                "n": 1,
                "beat_id": 1,
                "name": "b1_dollar_value_hook",
                "text": f"Stop paying for AI APIs: {prov} offers {val_str} in free credits.",
                "anchor_word": "credits",
                "visual_cue": f"Hero value card highlighting {val_str} free developer credits and {prov} badge.",
                "visual_focus": f"Hero value card highlighting {val_str} free developer credits and {prov} badge.",
                "highlight_words": {prov: COLOR_CYAN, val_str: COLOR_MINT, "credits": COLOR_GOLD},
                "svo_action": {"subject": "Developers", "action_verb": "claim", "direct_object": "Startup Credits", "anchor_word": "credits", "semantic_role": "agent_action"},
                "visual_blueprint": {"layout": "perks_hero_value", "title": f"{prov.upper()} STARTUP PROGRAM", "sub": f"{val_str} Official Grant", "params": {"provider": prov, "value": val_str}}
            },
            {
                "n": 2,
                "beat_id": 2,
                "name": "b2_bundle_breakdown",
                "text": "Here is the exact bundle breakdown: one thousand dollars in direct model credits plus one full free year of Claude Team for five developer seats.",
                "anchor_word": "bundle",
                "visual_cue": "Split-screen perk package tiles displaying API credit balance and Team seats.",
                "visual_focus": "Split-screen perk package tiles displaying API credit balance and Team seats.",
                "highlight_words": {"one thousand dollars": COLOR_MINT, "Claude Team": COLOR_CYAN, "five developer seats": COLOR_GOLD},
                "svo_action": {"subject": prov, "action_verb": "grants", "direct_object": "Team Seats", "anchor_word": "bundle", "semantic_role": "agent_action"},
                "visual_blueprint": {"layout": "perks_package_tiles", "title": "PERK PACKAGE BREAKDOWN", "sub": "Direct Model Credits & Seats", "params": {}}
            },
            {
                "n": 3,
                "beat_id": 3,
                "name": "b3_eligibility_criteria",
                "text": "Eligibility requires three simple things: an early-stage incorporated startup, a live landing page with custom domain, and an active prototype or GitHub repository.",
                "anchor_word": "Eligibility",
                "visual_cue": "Interactive eligibility checklist with animated green checkmarks popping in.",
                "visual_focus": "Interactive eligibility checklist with animated green checkmarks popping in.",
                "highlight_words": {"early-stage incorporated startup": COLOR_CYAN, "custom domain": COLOR_MINT, "GitHub repository": COLOR_GOLD},
                "svo_action": {"subject": "Founders", "action_verb": "qualifies", "direct_object": "Eligibility Checklist", "anchor_word": "Eligibility", "semantic_role": "state_transition"},
                "visual_blueprint": {"layout": "perks_eligibility_checklist", "title": "ELIGIBILITY CHECKLIST", "sub": "Three Simple Requirements", "params": {}}
            },
            {
                "n": 4,
                "beat_id": 4,
                "name": "b4_console_walkthrough",
                "text": f"To apply, head to {official_url.replace('https://', '').split('?')[0]}, link your GitHub repository, fill in three short team questions, and submit your application for review.",
                "anchor_word": "submit",
                "visual_cue": "Simulated developer console form with animated cursor gliding and clicking submit.",
                "visual_focus": "Simulated developer console form with animated cursor gliding and clicking submit.",
                "highlight_words": {"GitHub repository": COLOR_GOLD, "three short team questions": COLOR_CYAN, "submit": COLOR_MINT},
                "svo_action": {"subject": "Cursor", "action_verb": "submits", "direct_object": "Console Application", "anchor_word": "submit", "semantic_role": "agent_action"},
                "visual_blueprint": {"layout": "perks_console_walkthrough", "title": "CONSOLE APPLICATION", "sub": "Three-Minute Verification", "params": {"url": official_url}}
            },
            {
                "n": 5,
                "beat_id": 5,
                "name": "b5_social_proof",
                "text": "Community founders on social channels report swift verifications, with verified credit balances appearing directly inside the developer production billing dashboard.",
                "anchor_word": "verifications",
                "visual_cue": "Floating 3D Twitter and Reddit social proof receipt cards with glowing like counters.",
                "visual_focus": "Floating 3D Twitter and Reddit social proof receipt cards with glowing like counters.",
                "highlight_words": {"swift verifications": COLOR_GOLD, "verified credit balances": COLOR_MINT, "billing dashboard": COLOR_CYAN},
                "svo_action": {"subject": "Founders", "action_verb": "confirms", "direct_object": "Fast Approvals", "anchor_word": "verifications", "semantic_role": "metric_evaluation"},
                "visual_blueprint": {"layout": "perks_social_proof_receipt", "title": "COMMUNITY SOCIAL PROOF", "sub": "Real Founder Receipts", "params": {}}
            },
            {
                "n": 6,
                "beat_id": 6,
                "name": "b6_save_bookmark_cta",
                "text": "Save this video and follow The Model Verse for daily developer perks and free startup grants.",
                "anchor_word": "Model",
                "visual_cue": "Actionable save bookmark banner and The Model Verse brand signature.",
                "visual_focus": "Actionable save bookmark banner and The Model Verse brand signature.",
                "highlight_words": {"Save this video": COLOR_GOLD, "The Model Verse": COLOR_MINT},
                "svo_action": {"subject": "The Model Verse", "action_verb": "curates", "direct_object": "Developer Perks", "anchor_word": "Model", "semantic_role": "metric_evaluation"},
                "visual_blueprint": {"layout": "perks_action_outro", "title": "THE MODEL VERSE", "sub": "Daily Developer Perks & Tools", "params": {}}
            }
        ]

        total_words = sum(len(b["text"].split()) for b in beats)

        spec = {
            "id": clean_id,
            "title": headline,
            "category": "developer_perks",
            "provider": prov.lower(),
            "voice_style": "actionable_insider",
            "domain_taxonomy": "developer_perks",
            "word_count": total_words,
            "beats": beats,
            "manim_blueprints": [
                {"type": "dollar_value_hero", "title": f"{prov.upper()} STARTUP PROGRAM"},
                {"type": "bundle_breakdown", "title": "PERK PACKAGE BREAKDOWN"},
                {"type": "eligibility_checklist", "title": "ELIGIBILITY CHECKLIST"},
                {"type": "console_walkthrough", "title": "CONSOLE APPLICATION"},
                {"type": "social_proof_receipts", "title": "COMMUNITY SOCIAL PROOF"},
                {"type": "save_bookmark_cta", "title": "THE MODEL VERSE"}
            ],
            "perk_metadata": {
                "provider": prov,
                "headline": headline,
                "value_usd": val_usd,
                "official_url": official_url,
                "eligibility_criteria": eligibility,
                "step_by_step_application": steps
            },
            "math_formulas": [
                {
                    "beat_id": 1,
                    "latex": r"\mathrm{Grant} = " + val_str.replace(",", "{,}").replace("$", r"\$"),
                    "filename": f"{clean_id}_beat1_formula.svg",
                    "fontsize": 26,
                    "color": "mint"
                },
                {
                    "beat_id": 2,
                    "latex": r"\mathrm{Bundle} = \$1{,}000 + 5 \cdot \mathrm{Team}",
                    "filename": f"{clean_id}_beat2_formula.svg",
                    "fontsize": 24,
                    "color": "cyan"
                },
                {
                    "beat_id": 3,
                    "latex": r"\mathrm{Criteria} = \{ \text{Seed}, \text{Domain}, \text{Repo} \}",
                    "filename": f"{clean_id}_beat3_formula.svg",
                    "fontsize": 22,
                    "color": "gold"
                },
                {
                    "beat_id": 4,
                    "latex": r"\Delta t_{\mathrm{apply}} \leq 3\,\mathrm{min}",
                    "filename": f"{clean_id}_beat4_formula.svg",
                    "fontsize": 24,
                    "color": "cyan"
                },
                {
                    "beat_id": 5,
                    "latex": r"t_{\mathrm{approval}} < 48\,\mathrm{hours}",
                    "filename": f"{clean_id}_beat5_formula.svg",
                    "fontsize": 24,
                    "color": "mint"
                }
            ]
        }
        return spec

    def _finalize_spec(self, spec: Dict[str, Any], topic: str, perk_meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        prov = self._extract_provider(topic, perk_meta)
        headline = (perk_meta.get("title") if perk_meta else None) or (perk_meta.get("headline") if perk_meta else None) or spec.get("title") or topic
        clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", spec.get("id", topic).lower()).strip("_")
        if not clean_id.startswith("perk_"):
            clean_id = f"perk_{clean_id}"

        spec["id"] = clean_id
        spec["title"] = spec.get("title") or headline
        spec["category"] = "developer_perks"
        spec["provider"] = prov.lower()
        spec["voice_style"] = "actionable_insider"
        spec["domain_taxonomy"] = spec.get("domain_taxonomy") or "developer_perks"

        if not spec.get("perk_metadata"):
            spec["perk_metadata"] = {
                "provider": prov,
                "headline": spec.get("title", topic),
                "value_usd": perk_meta.get("value_usd", 2800) if perk_meta else 2800,
                "official_url": (perk_meta.get("official_url", "")) if perk_meta else ""
            }

        beat_names = ["b1_dollar_value_hook", "b2_bundle_breakdown", "b3_eligibility_criteria", "b4_console_walkthrough", "b5_social_proof", "b6_save_bookmark_cta"]
        val_str = self._extract_dollar_value(topic, perk_meta)
        default_blueprints = [
            {"layout": "perks_hero_value", "title": f"{prov.upper()} STARTUP PROGRAM", "sub": f"{val_str} Official Grant", "params": {"provider": prov, "value": val_str}},
            {"layout": "perks_package_tiles", "title": "PERK PACKAGE BREAKDOWN", "sub": "Direct Model Credits & Seats", "params": {}},
            {"layout": "perks_eligibility_checklist", "title": "ELIGIBILITY CHECKLIST", "sub": "Three Simple Requirements", "params": {}},
            {"layout": "perks_console_walkthrough", "title": "CONSOLE APPLICATION", "sub": "Three-Minute Verification", "params": {}},
            {"layout": "perks_social_proof_receipt", "title": "COMMUNITY SOCIAL PROOF", "sub": "Real Founder Receipts", "params": {}},
            {"layout": "perks_action_outro", "title": "THE MODEL VERSE", "sub": "Daily Developer Perks & Tools", "params": {}}
        ]

        normalized_beats = []
        for idx, b in enumerate(spec.get("beats", [])):
            b_id = b.get("n") or b.get("beat_id", idx + 1)
            text = (b.get("text") or "").strip()
            anchor_word = (b.get("anchor_word") or "").strip()
            visual_cue = (b.get("visual_cue") or b.get("visual_focus") or "").strip()

            if not anchor_word and text:
                words = [re.sub(r"[^\w]", "", w) for w in text.split()]
                anchor_word = words[-1] if words else "Credits"

            b["beat_id"] = b_id
            b["n"] = b_id
            b["text"] = text
            b["anchor_word"] = anchor_word
            b["visual_cue"] = visual_cue
            b["visual_focus"] = visual_cue or b.get("visual_focus", f"Beat {b_id} visual")
            b["name"] = b.get("name") or (beat_names[idx] if idx < len(beat_names) else f"b{b_id}")

            if not b.get("svo_action"):
                b["svo_action"] = {
                    "subject": "Developers",
                    "action_verb": "claim",
                    "direct_object": "Free Credits",
                    "anchor_word": anchor_word,
                    "semantic_role": "agent_action"
                }
            else:
                b["svo_action"]["anchor_word"] = anchor_word

            if not b.get("highlight_words"):
                b["highlight_words"] = {anchor_word: COLOR_MINT} if anchor_word else {}

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
                {"type": "dollar_value_hero", "title": f"{prov.upper()} STARTUP PROGRAM"},
                {"type": "bundle_breakdown", "title": "PERK PACKAGE BREAKDOWN"},
                {"type": "eligibility_checklist", "title": "ELIGIBILITY CHECKLIST"},
                {"type": "console_walkthrough", "title": "CONSOLE APPLICATION"},
                {"type": "social_proof_receipts", "title": "COMMUNITY SOCIAL PROOF"},
                {"type": "save_bookmark_cta", "title": "THE MODEL VERSE"}
            ]

        spec["word_count"] = get_total_word_count(spec)
        is_valid, validation_errors = validate_script_spec(spec)
        if is_valid:
            print(f"✅ Developer perks script passed validation ({spec['word_count']} words).")
        else:
            print(f"⚠️ Developer perks script validation notices ({spec['word_count']} words):\n" + "\n".join(f"   - {e}" for e in validation_errors))

        return spec

    def _extract_dollar_value(self, topic: str, perk_meta: Optional[Dict[str, Any]] = None) -> str:
        candidates = []
        if perk_meta and perk_meta.get("value"):
            candidates.append(str(perk_meta["value"]))
        candidates.append(topic)
        for cand in candidates:
            m = re.search(r"\$([\d,]+)(\+)?", cand)
            if m:
                num_clean = m.group(1).replace(",", "")
                plus = "+" if m.group(2) or "+" in cand else ""
                try:
                    num_val = int(num_clean)
                    return f"${num_val:,}{plus}"
                except ValueError:
                    return f"${m.group(1)}{plus}"
        val_usd = perk_meta.get("value_usd") if perk_meta else None
        if val_usd:
            return f"${int(val_usd):,}"
        return "$1,000+"

    def _extract_provider(self, topic: str, perk_meta: Optional[Dict[str, Any]]) -> str:
        if perk_meta and perk_meta.get("provider"):
            return perk_meta["provider"]
        t = topic.lower()
        if "anthropic" in t or "claude" in t:
            return "Anthropic"
        elif "openai" in t:
            return "OpenAI"
        elif "microsoft" in t or "founders" in t or "azure" in t:
            return "Microsoft"
        elif "google" in t:
            return "Google Cloud"
        elif "aws" in t or "amazon" in t:
            return "AWS"
        elif "github" in t:
            return "GitHub"
        elif "cloudflare" in t:
            return "Cloudflare"
        return "Anthropic"


developer_perks_script_engine = DeveloperPerksScriptEngine()
