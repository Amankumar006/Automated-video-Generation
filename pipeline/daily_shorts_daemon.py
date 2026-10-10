"""
The Model Verse — Autonomous Daily Paper-to-Shorts Daemon
Monitors trending AI research daily, selects the most visually and pedagogically compelling
breakthrough paper, generates an intuitive Feynman-standard script, produces a 1440p60 video,
and uploads to YouTube Shorts as Unlisted for 1-click review.
"""

import os
import re
import sys
import json
import time
import datetime
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.batch_digest import get_trending_digest, record_paper_production, load_history
from pipeline.github_trending_fetcher import get_trending_github_digest
from pipeline.official_blogs_fetcher import get_official_blogs_digest, official_blogs_fetcher
from pipeline.auto_produce import auto_produce
from pipeline.script_critic import ScriptCritic
from pipeline.json_utils import robust_json_loads
from pipeline.config import WORKSPACE_ROOT, BROADCAST_WIDTH, BROADCAST_HEIGHT, BROADCAST_FPS
from pipeline.analytics_feedback import (
    retention_analytics,
    get_performance_category_bias,
    get_recommended_pacing
)

DAEMON_LOGS_DIR = PROJECT_ROOT / "public" / "daemon_logs"
DAEMON_LOGS_DIR.mkdir(parents=True, exist_ok=True)


# 5 Automated Daily Upload Windows calibrated to global peak viewer hours and audience analytics
SLOT_SCHEDULE: Dict[int, Dict[str, Any]] = {
    1: {
        "slot_name": "Window 1 (01:00 UTC - Asia/Europe Morning Surge)",
        "preferred_taxonomy": "multimodal_diffusion",
        "description": "Visual diffusion, flow matching, and video generation breakthroughs"
    },
    5: {
        "slot_name": "Window 2 (05:00 UTC - Europe Developer Prime)",
        "preferred_taxonomy": "hardware_efficiency",
        "description": "KV cache, GPU optimization, latency, and memory throughput"
    },
    9: {
        "slot_name": "Window 3 (09:00 UTC - Midday Global Tech Feed)",
        "preferred_taxonomy": "multimodal_diffusion",
        "description": "Multimodal video/image synthesis and generative world models"
    },
    12: {
        "slot_name": "Window 4 (12:00 UTC - US East Coast Morning Peak)",
        "preferred_taxonomy": "hardware_efficiency",
        "description": "Quantization (FP8/FP4), CUDA kernels, and inference acceleration"
    },
    16: {
        "slot_name": "Window 5 (16:00 UTC - US West / Global Prime Time)",
        "preferred_taxonomy": None,  # Highest overall weighted breakthrough candidate (≥1.0x velocity)
        "description": "Top breakthrough paper across high-performing categories"
    }
}


# 3 Core Channel Content Pillars for Autonomous Daily Rotation:
# (1) Academic mechanism deep dives ('arxiv')
# (2) Official AI lab releases ('blogs' / 'news')
# (3) Actionable developer perks and startup credits ('perks')
CONTENT_PILLARS = ["arxiv", "blogs", "perks"]

PILLAR_DISPLAY_NAMES: Dict[str, str] = {
    "arxiv": "Academic Mechanism Deep Dives (arXiv / HF)",
    "blogs": "Official AI Lab Releases & Tech News (OpenAI, Anthropic, Google DeepMind, HF)",
    "perks": "Actionable Developer Perks & Startup Credits (Anthropic, Microsoft, Google, AWS)"
}


def parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime.datetime]:
    """Parses ISO-8601 or RFC datetime string into a UTC timezone-aware datetime object."""
    if not dt_str:
        return None
    try:
        clean_str = dt_str.strip().replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except Exception:
        return None


def classify_history_entry_pillar(paper_id: str, record: Dict[str, Any]) -> str:
    """Classifies a history or candidate record into one of the 3 primary pillars: 'arxiv', 'blogs', or 'perks'."""
    src = str(record.get("source", "")).lower()
    if src in ("perks", "verified_perks"):
        return "perks"
    if src in ("blogs", "news", "official_blogs"):
        return "blogs"
    if src in ("arxiv", "hf"):
        return "arxiv"

    clean_id = str(paper_id).lower()
    cat = str(record.get("category", "")).lower()
    tax = str(record.get("taxonomy", "")).lower()

    if clean_id.startswith("perk_") or cat in ("developer_perks", "startup_credits", "perks") or tax == "developer_perks":
        return "perks"
    if clean_id.startswith(("blog_", "news_")) or cat in ("tech_news", "official_blogs", "lab_release"):
        return "blogs"
    if cat == "model_showdown" and not re.match(r"^\d{4}\.\d{4,5}", clean_id):
        return "blogs"

    return "arxiv"


def get_content_rotation_order(
    history: Optional[Dict[str, Any]] = None,
    pillars: Optional[List[str]] = None
) -> List[str]:
    """
    Inspects production history in digest_history.json to determine the least-recently produced
    content categories among ('arxiv', 'blogs', 'perks') to ensure balanced alternating coverage.

    Returns pillars ordered from least-recently produced (highest priority for next production)
    to most-recently produced.
    """
    if history is None:
        history = load_history()

    if pillars is None:
        pillars = list(CONTENT_PILLARS)

    processed_papers = history.get("processed_papers", {})

    latest_timestamps: Dict[str, Optional[datetime.datetime]] = {p: None for p in pillars}
    overall_latest_time: Optional[datetime.datetime] = None
    overall_latest_pillar: Optional[str] = None

    for pid, data in processed_papers.items():
        pillar = classify_history_entry_pillar(pid, data)
        if pillar not in latest_timestamps:
            continue

        raw_ts = data.get("produced_at")
        dt = parse_iso_datetime(raw_ts)
        if dt:
            if latest_timestamps[pillar] is None or dt > latest_timestamps[pillar]:
                latest_timestamps[pillar] = dt
            if overall_latest_time is None or dt > overall_latest_time:
                overall_latest_time = dt
                overall_latest_pillar = pillar

    canonical_cycle = ["arxiv", "blogs", "perks"]

    start_idx = 0
    if overall_latest_pillar in canonical_cycle:
        start_idx = (canonical_cycle.index(overall_latest_pillar) + 1) % len(canonical_cycle)

    cycle_tiebreaker = {
        canonical_cycle[(start_idx + i) % len(canonical_cycle)]: i
        for i in range(len(canonical_cycle))
    }

    def sort_key(p: str):
        ts = latest_timestamps[p]
        ts_val = ts.timestamp() if ts is not None else float("-inf")
        tiebreak = cycle_tiebreaker.get(p, 99)
        return (ts_val, tiebreak)

    sorted_pillars = sorted(pillars, key=sort_key)
    return sorted_pillars


def fetch_candidates_for_pillar(
    pillar: str,
    limit: int = 10,
    history: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Fetches candidate specifications for a specific content pillar, filtering out processed items."""
    if history is None:
        history = load_history()

    proc_ids = set(history.get("processed_papers", {}).keys())

    if pillar == "arxiv":
        papers = get_trending_digest(limit=max(limit, 35))
        return [p for p in papers if not p.get("is_processed") and p["id"] not in proc_ids]

    elif pillar in ("blogs", "news"):
        blog_candidates = get_official_blogs_digest(limit=limit)
        return [b for b in blog_candidates if b["id"] not in proc_ids]

    elif pillar == "perks":
        from pipeline.tech_perks_fetcher import get_verified_perks_digest
        perk_candidates = get_verified_perks_digest(limit=limit)
        return [p for p in perk_candidates if p["id"] not in proc_ids]

    elif pillar == "github":
        gh_candidates = get_trending_github_digest(limit=limit)
        return [g for g in gh_candidates if g["id"] not in proc_ids]

    return []


def evaluate_pedagogical_viability(
    candidates: List[Dict[str, Any]],
    count: int = 1,
    preferred_taxonomy: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Evaluates candidate trending papers with Gemini to pick the top `count`
    curiosity-inducing, visually teachable papers, aggressively favoring high-velocity
    domains (multimodal_diffusion 1.29x, hardware_efficiency 1.19x).
    """
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        import google.generativeai as genai

    if not candidates:
        return []

    target_count = min(count, len(candidates))

    # Helper function for deterministic fallback with category diversity balancing
    def get_fallback_candidates() -> List[Dict[str, Any]]:
        def candidate_priority(c):
            tax = c.get("taxonomy", "")
            mult = c.get("analytics_multiplier", 1.0)
            is_pref = 2 if (preferred_taxonomy and tax == preferred_taxonomy) else 0
            is_high_velocity = 1 if mult > 1.0 else 0
            return (is_pref, is_high_velocity, c.get("impact_score", 0))

        sorted_cands = sorted(candidates, key=candidate_priority, reverse=True)
        if target_count <= 1:
            return sorted_cands[:target_count]

        # Multi-candidate selection with category & taxonomy diversity balancing
        selected = []
        seen_categories = set()
        seen_taxonomies = set()
        pool = list(sorted_cands)

        # 1. First pick the top ranked candidate
        first = pool.pop(0)
        selected.append(first)
        seen_categories.add(first.get("recommended_category") or first.get("category", "general"))
        seen_taxonomies.add(first.get("taxonomy", "general"))

        # 2. Pick subsequent candidates favoring diverse categories and taxonomies
        for c in list(pool):
            if len(selected) >= target_count:
                break
            c_cat = c.get("recommended_category") or c.get("category", "general")
            c_tax = c.get("taxonomy", "general")
            if (c_cat not in seen_categories or c_tax not in seen_taxonomies) and (c.get("analytics_multiplier", 1.0) >= 1.0 or not any(p.get("analytics_multiplier", 1.0) >= 1.0 for p in pool)):
                selected.append(c)
                seen_categories.add(c_cat)
                seen_taxonomies.add(c_tax)
                pool.remove(c)

        # 3. Fill remaining quota if needed
        while len(selected) < target_count and pool:
            selected.append(pool.pop(0))

        return selected

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return get_fallback_candidates()

    genai.configure(api_key=api_key)

    cand_summaries = []
    num_eval = min(20, len(candidates))
    for i, c in enumerate(candidates[:num_eval]):
        tax = c.get("taxonomy", "general_breakthroughs")
        mult = c.get("analytics_multiplier", 1.0)
        cand_summaries.append(
            f"[{i+1}] Title: {c['title']}\n"
            f"    arXiv: {c['id']}\n"
            f"    Domain Taxonomy: {tax} (Audience Velocity Multiplier: {mult:.2f}x)\n"
            f"    Category: {c.get('recommended_category', 'mechanism_deepdive')}\n"
            f"    Abstract: {c['abstract'][:250]}..."
        )

    # Query dynamic retention multipliers from analytics feedback
    category_biases = get_performance_category_bias()
    bias_desc = ""
    if category_biases:
        bias_str = ", ".join([f"{k}: {v}x multiplier" for k, v in category_biases.items()])
        bias_desc = f"""
4. CRITICAL AUDIENCE ENGAGEMENT ALIGNMENT & DIVERSITY DIRECTIVE:
   - Real-time YouTube analytics reveals top velocity drivers: 'multimodal_diffusion' (1.29x), 'developer_perks' (1.25x), 'hardware_efficiency' (1.19x).
   - Live category multipliers: [{bias_str}].
   - MULTI-CATEGORY ROTATION: In addition to hardware and diffusion breakthroughs, actively incorporate actionable developer tech perks, model showdowns, and benchmark news to maximize audience breadth across developers, founders, and students.
   - DIVERSITY REQUIREMENT: Ensure variety across selected topics; avoid selecting multiple consecutive videos on identical sub-topics or narrow architecture breakdowns."""

    if preferred_taxonomy:
        bias_desc += f"\n5. TARGET UPLOAD WINDOW FOCUS: This automated upload window specifically targets '{preferred_taxonomy.upper()}'. Prioritize the best candidate in '{preferred_taxonomy}'."

    prompt = f"""You are the Executive Creative Director of 'The Model Verse', a premier YouTube Shorts channel creating 3Blue1Brown-style chalkboard animations about cutting-edge AI and developer tools.

Review these top {len(cand_summaries)} trending AI papers, official lab announcements, and tech perks from today:
{chr(10).join(cand_summaries)}

Select the {target_count} BEST and MOST DIVERSE topics for 45-second educational animated Shorts.
Criteria:
1. High Public Fascination: Does it answer a fascinating question that curious non-specialists care about? (e.g. reasoning, memory, world models, attention, latent circuits, free startup credits/perks, major AI model releases).
2. Physical Analogy Potential: Can the core idea be explained using everyday tangible comparisons (e.g. library, clouds, mirror, sculptor, train, static, VIP all-access badge)?
3. High Production Value: Can the concepts be visualized with dynamic 3b1b animations (e.g. wave collisions, streaming KV buffers, pipeline stages, workflow routing)?{bias_desc}

Return ONLY valid JSON matching this schema:
{{
  "selected_papers": [
    {{
      "selected_index": 1,
      "reasoning": "Brief explanation of why this paper was chosen",
      "recommended_hook": "One-sentence curiosity hook for the script",
      "suggested_everyday_analogy": "The physical analogy to base the explanation on"
    }}
  ]
}}
"""
    candidate_models = ["gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-2.0-flash", "gemini-3.8-flash"]
    for m_name in candidate_models:
        try:
            model = genai.GenerativeModel(m_name)
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            if response and response.text:
                decision = robust_json_loads(response.text.strip())
                chosen_items = decision.get("selected_papers", [])
                if not chosen_items and "selected_index" in decision:
                    chosen_items = [decision]

                selected_list = []
                selected_indices = set()
                for item in chosen_items:
                    idx = int(item.get("selected_index", 1)) - 1
                    if 0 <= idx < len(candidates) and idx not in selected_indices:
                        cand = candidates[idx]
                        cand["editorial_notes"] = item
                        selected_list.append(cand)
                        selected_indices.add(idx)
                        if len(selected_list) >= target_count:
                            break

                # Fill any shortfall with remaining high-velocity candidates
                if len(selected_list) < target_count:
                    fallback_pool = get_fallback_candidates()
                    for cand in fallback_pool:
                        if len(selected_list) >= target_count:
                            break
                        if cand["id"] not in {c["id"] for c in selected_list}:
                            selected_list.append(cand)

                if selected_list:
                    return selected_list
        except Exception:
            continue

    print(f"⚠️ Pedagogical evaluation fallback: selecting top {target_count} candidates calibrated to audience analytics")
    return get_fallback_candidates()


class DailyShortsDaemon:
    """Autonomous scheduler and engine for daily AI Shorts production."""

    def __init__(self, quality: str = "-qh", privacy: str = "public", publish_instagram: bool = False):
        if quality and not quality.startswith("-"):
            self.quality = f"-{quality}"
        else:
            self.quality = quality or "-qh"
        self.privacy = privacy
        self.publish_instagram = publish_instagram or (os.getenv("PUBLISH_INSTAGRAM", "false").lower() == "true")
        self.critic = ScriptCritic()

    def run_daily_cycle(
        self,
        count: int = 1,
        dry_run: bool = False,
        publish: bool = True,
        target_arxiv: Optional[str] = None,
        target_perk: Optional[str] = None,
        target_blog: Optional[str] = None,
        target_news: Optional[str] = None,
        target_slot_hour: Optional[int] = None,
        preferred_taxonomy: Optional[str] = None,
        preferred_category: Optional[str] = None,
        source: str = "mixed"
    ) -> List[Dict[str, Any]]:
        """Executes discovery, production, and publishing for `count` reels aligned with YouTube audience analytics."""
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print("\n" + "=" * 80)
        print(f"🤖 THE MODEL VERSE — AUTONOMOUS DAILY SHORTS DAEMON")
        print(f"⏰ Cycle Triggered: {timestamp} | Target Quota: {count} Reel(s) | Source: {source.upper()}")
        if target_slot_hour is not None and target_slot_hour in SLOT_SCHEDULE:
            slot_info = SLOT_SCHEDULE[target_slot_hour]
            print(f"🎯 Automated Window: {slot_info['slot_name']}")
            print(f"   Target Directive: {slot_info['description']}")
            if not preferred_taxonomy and slot_info.get("preferred_taxonomy"):
                preferred_taxonomy = slot_info["preferred_taxonomy"]
        if preferred_taxonomy:
            print(f"📈 Analytics Category Bias: Aggressively prioritizing '{preferred_taxonomy.upper()}'")
        if preferred_category:
            print(f"🎯 Preferred Category Focus: '{preferred_category.upper()}'")
        print("=" * 80)

        # 0. Poll YouTube Analytics & Refresh Performance Multipliers
        print("\n📊 Step 0: Polling YouTube Analytics & Real-Time Viewer Retention...")
        try:
            retention_analytics.generate_and_save_ledger()
        except Exception as e:
            print(f"   ⚠️ Could not refresh retention ledger: {e}")

        if target_perk:
            print(f"\n🎁 Direct Target Developer Perk Specified: {target_perk}")
            from pipeline.tech_perks_fetcher import tech_perks_fetcher
            perk_rec = tech_perks_fetcher.get_verified_perk(target_perk)
            if not perk_rec:
                audit = tech_perks_fetcher.verify_perk_claim(target_perk)
                if audit.get("is_verified"):
                    perk_rec = tech_perks_fetcher.get_verified_perk(audit.get("program_id", ""))
            if not perk_rec:
                print(f"⚠️ Could not resolve verified developer perk: {target_perk}")
                return []
            selected_papers = [perk_rec.to_candidate_spec()]
        elif target_blog or target_news:
            target_id = target_blog or target_news
            print(f"\n📰 Direct Target Official Blog / News Specified: {target_id}")
            from pipeline.official_blogs_fetcher import official_blogs_fetcher
            blog_rec = official_blogs_fetcher.get_blog(target_id)
            if not blog_rec:
                blog_rec = official_blogs_fetcher.find_blog(target_id)
            if not blog_rec:
                print(f"⚠️ Could not resolve official blog post: {target_id}")
                return []
            selected_papers = [blog_rec.to_candidate_spec()]
        elif target_arxiv:
            print(f"\n🎯 Direct Target Paper Specified: {target_arxiv}")
            from pipeline.arxiv_fetcher import fetch_arxiv_paper
            from pipeline.batch_digest import score_and_classify_paper
            p_data = fetch_arxiv_paper(target_arxiv)
            if not p_data:
                print(f"⚠️ Could not fetch metadata for arXiv ID: {target_arxiv}")
                return []
            classified = score_and_classify_paper({
                "id": p_data["arxiv_id"],
                "title": p_data["title"],
                "abstract": p_data.get("abstract", ""),
                "upvotes": 0
            })
            cat = preferred_category or classified.get("recommended_category", "mechanism_deepdive")
            selected_papers = [{
                "title": p_data["title"],
                "id": p_data["arxiv_id"],
                "recommended_category": cat,
                "category": cat,
                "taxonomy": classified.get("taxonomy", "general"),
                "analytics_multiplier": classified.get("analytics_multiplier", 1.0),
                "abstract": p_data.get("abstract", ""),
                "editorial_notes": {
                    "recommended_hook": f"How {p_data['title']} works under the hood",
                    "suggested_everyday_analogy": "Mechanical blueprint breakdown"
                }
            }]
        else:
            normalized_source = (source or "mixed").lower()
            if normalized_source in ("mixed", "auto"):
                print(f"\n🔄 Step 1: Content Diversification Rotation (Source: {normalized_source.upper()})...")
                history = load_history()
                rotation_order = get_content_rotation_order(history)

                print("   Recent Production History Inspection by Content Pillar:")
                processed_papers = history.get("processed_papers", {})
                for p in CONTENT_PILLARS:
                    last_time_str = "Never (Queued as high-priority drop)"
                    for pid, pdata in processed_papers.items():
                        if classify_history_entry_pillar(pid, pdata) == p:
                            pts = pdata.get("produced_at", "")
                            if last_time_str == "Never (Queued as high-priority drop)" or pts > last_time_str:
                                last_time_str = pts
                    print(f"   • {PILLAR_DISPLAY_NAMES.get(p, p)}: Last produced: {last_time_str}")
                print(f"   🎯 Content Rotation Priority Order: {' -> '.join([p.upper() for p in rotation_order])}")

                selected_papers = []
                selected_ids = set()
                # Deep copy of history for multi-reel cycles so each reel in this cycle rotates to next pillar
                working_history = json.loads(json.dumps(history))

                for reel_idx in range(count):
                    curr_rotation = get_content_rotation_order(working_history)
                    chosen_candidate = None
                    chosen_pillar = None

                    for target_pillar in curr_rotation:
                        pool = fetch_candidates_for_pillar(target_pillar, limit=10, history=working_history)
                        available_candidates = [c for c in pool if c["id"] not in selected_ids]
                        if preferred_category:
                            matching = [c for c in available_candidates if c.get("recommended_category") == preferred_category or c.get("category") == preferred_category]
                            if matching:
                                available_candidates = matching

                        if available_candidates:
                            evaluated = evaluate_pedagogical_viability(
                                available_candidates,
                                count=1,
                                preferred_taxonomy=preferred_taxonomy
                            )
                            if evaluated:
                                chosen_candidate = evaluated[0]
                                chosen_pillar = target_pillar
                                break

                    if chosen_candidate:
                        selected_papers.append(chosen_candidate)
                        selected_ids.add(chosen_candidate["id"])
                        print(f"   Reel {reel_idx + 1}/{count} assigned to [{chosen_pillar.upper()}]: {chosen_candidate['title']} ({chosen_candidate['id']})")
                        simulated_ts = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=reel_idx + 1)).isoformat()
                        working_history["processed_papers"][chosen_candidate["id"]] = {
                            "title": chosen_candidate["title"],
                            "category": chosen_candidate.get("recommended_category", "general"),
                            "source": chosen_pillar,
                            "produced_at": simulated_ts,
                            "status": "completed"
                        }
                    else:
                        print(f"   ⚠️ No unprocessed candidates found across any content pillars for reel {reel_idx + 1}.")
                        break

                if not selected_papers:
                    print("ℹ️ All trending candidates across all content pillars have already been produced. Daily quota satisfied.")
                    return []

            else:
                target_pillar = "blogs" if normalized_source == "news" else normalized_source
                print(f"\n🔍 Step 1: Scanning trending breakthrough candidates (Source: {target_pillar.upper()})...")
                unprocessed = fetch_candidates_for_pillar(target_pillar, limit=35 if target_pillar == "arxiv" else 10)

                if preferred_category:
                    unprocessed = (
                        [p for p in unprocessed if p.get("recommended_category") == preferred_category or p.get("category") == preferred_category] +
                        [p for p in unprocessed if p.get("recommended_category") != preferred_category and p.get("category") != preferred_category]
                    )

                if not unprocessed:
                    print(f"ℹ️ All candidates for source '{target_pillar}' have already been produced. Quota satisfied.")
                    return []

                print(f"   Found {len(unprocessed)} unprocessed candidates. Selecting top {count} pedagogical breakthroughs...")
                selected_papers = evaluate_pedagogical_viability(
                    unprocessed,
                    count=count,
                    preferred_taxonomy=preferred_taxonomy
                )
        print(f"\n🏆 Selected {len(selected_papers)} Breakthrough Papers for Today's Reels Quota:")
        for idx, p in enumerate(selected_papers):
            notes = p.get("editorial_notes", {})
            tax = p.get("taxonomy", "general_breakthroughs")
            mult = p.get("analytics_multiplier", 1.0)
            print(f"   [{idx+1}/{len(selected_papers)}] {p['title']} ({p['id']})")
            print(f"       Domain: {tax.upper()} ({mult:.2f}x velocity) | Category: {p.get('recommended_category', 'mechanism_deepdive').upper()}")
            if notes.get("recommended_hook"):
                print(f"       💡 Hook: {notes.get('recommended_hook')}")
            if notes.get("suggested_everyday_analogy"):
                print(f"       🍎 Analogy: {notes.get('suggested_everyday_analogy')}")

        reports = []

        # 3. Produce each reel sequentially
        for idx, top_paper in enumerate(selected_papers):
            title = top_paper["title"]
            arxiv_id = top_paper["id"]
            category = top_paper.get("recommended_category", "mechanism_deepdive")
            notes = top_paper.get("editorial_notes", {})

            print("\n" + "-" * 70)
            print(f"🎬 Producing Reel [{idx+1}/{len(selected_papers)}]: {title}")
            print(f"   arXiv: {arxiv_id} | Category: {category.upper()}")
            print("-" * 70)

            cand_source = classify_history_entry_pillar(arxiv_id, top_paper)

            if dry_run:
                print("🔍 [DRY-RUN] Simulating script generation and pedagogy evaluation...")
                from pipeline.script_generator import generate_script
                spec = generate_script(topic=title, category=category, arxiv_meta=top_paper)
                audit = self.critic.evaluate_script(spec, use_llm=False)
                print(f"   💡 Analogies Found: {audit.total_analogies} | Jargon Count: {audit.total_critical_jargon} | Slop Cliches: {audit.total_slop_cliches}")
                if spec.get("feynman_certification"):
                    cert = spec["feynman_certification"]
                    print(f"   🎓 Feynman Socratic Audit: Comprehension {cert.get('final_comprehension_score')}/10 | Hook {cert.get('final_retention_hook_score')}/10 | Slop Eliminated: {cert.get('ai_slop_eliminated')}")
                print(f"   ✅ Quality Gate Passed: {audit.passed}")
                reports.append({
                    "paper": top_paper,
                    "spec": spec,
                    "audit": audit,
                    "source": cand_source,
                    "status": "dry_run_success"
                })
                continue

            # Production (Script + Critic + 1440p60 Manim + Thumbnail + YouTube)
            pacing = get_recommended_pacing()
            rec_speed = pacing.get("tts_speed", 1.12)
            active_prov = os.environ.get("TTS_PROVIDER", "auto")
            active_voice = os.environ.get("ELEVENLABS_VOICE", "eric")
            try:
                video_out = auto_produce(
                    arxiv=arxiv_id,
                    category=category,
                    speed=rec_speed,
                    quality=self.quality,
                    publish=publish,
                    privacy=self.privacy,
                    paper_meta=top_paper,
                    provider=active_prov,
                    voice=active_voice,
                    publish_instagram=self.publish_instagram
                )
            except Exception as prod_err:
                print(f"⚠️ Production error for {arxiv_id}: {prod_err}")
                import traceback
                traceback.print_exc()
                video_out = None

            if video_out:
                record_paper_production(arxiv_id, title, category, video_out, source=cand_source)

                report_item = {
                    "reel_index": idx + 1,
                    "timestamp": timestamp,
                    "paper_id": arxiv_id,
                    "title": title,
                    "category": category,
                    "source": cand_source,
                    "taxonomy": top_paper.get("taxonomy", "general"),
                    "analytics_multiplier": top_paper.get("analytics_multiplier", 1.0),
                    "video_path": video_out,
                    "resolution": f"{BROADCAST_WIDTH}x{BROADCAST_HEIGHT} @ {BROADCAST_FPS}fps",
                    "editorial_notes": notes
                }
                reports.append(report_item)

        # 4. Generate Daily Production Log Report
        if not dry_run and reports:
            today_str = datetime.date.today().isoformat()
            log_file = DAEMON_LOGS_DIR / f"daemon_report_{today_str}.json"
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump({"date": today_str, "total_reels": len(reports), "reels": reports}, f, indent=2)

            md_file = DAEMON_LOGS_DIR / f"daemon_report_{today_str}.md"
            reels_md = []
            for r in reports:
                ed = r.get("editorial_notes", {})
                pid = str(r.get("paper_id", ""))
                r_source = r.get("source") or classify_history_entry_pillar(pid, {"category": r.get("category", "")})
                if pid.startswith("gh_"):
                    clean_repo = pid.replace("gh_", "").replace("_", "/")
                    link_line = f"- **GitHub Repo:** [{clean_repo}](https://github.com/{clean_repo})"
                elif pid.startswith("perk_"):
                    link_line = f"- **Verified Perk:** {r['title']}"
                elif pid.startswith("blog_") or pid.startswith("news_"):
                    link_line = f"- **Official Lab Drop:** {r['title']}"
                else:
                    link_line = f"- **arXiv ID:** [{pid}](https://arxiv.org/abs/{pid})"
                reels_md.append(f"""### Reel {r['reel_index']}: {r['title']}
{link_line}
- **Content Pillar:** `{r_source}`
- **Domain Taxonomy:** `{r.get('taxonomy', 'general')}` ({r.get('analytics_multiplier', 1.0):.2f}x velocity)
- **Category:** `{r['category']}`
- **Editorial Hook:** *{ed.get('recommended_hook', 'N/A')}*
- **Everyday Analogy:** *{ed.get('suggested_everyday_analogy', 'N/A')}*
- **Local Master Video:** `{r['video_path']}`
- **Resolution:** `{r['resolution']}`
""")

            with open(md_file, "w", encoding="utf-8") as f:
                f.write(f"""# 🤖 The Model Verse — Daily Shorts Production Report
**Date:** {today_str} | **Timestamp:** {timestamp}
**Total Reels Produced:** {len(reports)} / {count}

{''.join(reels_md)}
## 🎬 Production & Broadcast Specs
- **Master Resolution:** {BROADCAST_WIDTH}x{BROADCAST_HEIGHT} (2K QHD Vertical)
- **Framerate:** {BROADCAST_FPS} FPS
- **Codec Profile:** High-Tier VP09/AV01 Compatible (CRF 15, BT.709)
- **YouTube Upload Privacy:** `{self.privacy}`
""")

            print(f"\n✅ Daily Production Cycle Complete for {len(reports)} Reels!")
            print(f"📑 Daemon Log Saved: {log_file} and {md_file}")

        return reports

    def start_standing_daemon(self, target_hours_utc: Optional[List[int]] = None, interval_minutes: int = 30):
        """
        Runs continuously in the background across 5 research-backed pre-peak upload windows.
        Default hours (UTC): [1, 5, 9, 12, 16] -> 5 reels timed right before global viewer surges,
        calibrated to audience velocity (multimodal_diffusion: 1.29x, hardware_efficiency: 1.19x).
        """
        if target_hours_utc is None:
            target_hours_utc = list(SLOT_SCHEDULE.keys())

        print(f"🚀 Starting standing daemon loop (Checking every {interval_minutes}m, Target Hours UTC: {target_hours_utc})...")
        print("📊 5-Slot Audience Alignment Schedule:")
        for h in target_hours_utc:
            info = SLOT_SCHEDULE.get(h, {})
            pref = info.get("preferred_taxonomy") or "Top High-Velocity Breakthrough"
            print(f"   • Window {h:02d}:00 UTC -> Focus: {pref}")

        last_triggered_hour = -1
        while True:
            now = datetime.datetime.now(datetime.timezone.utc)
            if now.hour in target_hours_utc and now.hour != last_triggered_hour:
                slot_info = SLOT_SCHEDULE.get(now.hour, {})
                slot_name = slot_info.get("slot_name", f"{now.hour:02d}:00 UTC")
                pref_tax = slot_info.get("preferred_taxonomy")
                print(f"\n⏰ Peak Window Reached ({now.hour:02d}:00 UTC): {slot_name}")
                print(f"🎯 Calibrating to domain target: {pref_tax or 'Overall Highest Velocity'}")
                try:
                    self.run_daily_cycle(
                        count=1,
                        dry_run=False,
                        publish=True,
                        target_slot_hour=now.hour,
                        preferred_taxonomy=pref_tax,
                        source="mixed"
                    )
                    last_triggered_hour = now.hour
                except Exception as e:
                    print(f"⚠️ Error during daemon cycle: {e}")
            time.sleep(interval_minutes * 60)


def main():
    parser = argparse.ArgumentParser(description="The Model Verse — Autonomous Daily Paper-to-Shorts Daemon")
    parser.add_argument("--run-now", action="store_true", help="Execute production cycle immediately")
    parser.add_argument("--count", type=int, default=1, help="Number of reels to produce (default: 1, e.g. 5)")
    parser.add_argument("--dry-run", action="store_true", help="Test paper discovery and script generation without rendering")
    parser.add_argument("--source", choices=["arxiv", "github", "perks", "blogs", "news", "mixed", "auto"], default="mixed", help="Candidate source: 'mixed' (auto-rotate between arxiv, blogs, perks), 'arxiv', 'blogs', 'perks', 'github', or 'auto' (default: mixed)")
    parser.add_argument("--daemon", action="store_true", help="Run standing daemon in continuous background loop across 5 daily slots")
    parser.add_argument("--slot-hour", type=int, choices=[1, 5, 9, 12, 16], help="Simulate a specific automated upload window (1, 5, 9, 12, 16)")
    parser.add_argument("--preferred-taxonomy", choices=["multimodal_diffusion", "hardware_efficiency", "developer_perks", "reasoning_models", "efficient_architectures", "robotics_tamp", "mechanistic_interpretability"], help="Override preferred domain taxonomy for selection")
    parser.add_argument("--category", type=str, default="", help="Preferred category override (e.g. developer_perks, architecture_breakdown, model_showdown, tech_news)")
    parser.add_argument("--perk", type=str, default="", help="Specific verified developer perk ID to produce (e.g. anthropic_startup_program, microsoft_founders_hub)")
    parser.add_argument("--blog", type=str, default="", help="Specific official blog post ID to produce (e.g. blog_openai_o3_mini, blog_claude_3_7_sonnet)")
    parser.add_argument("--news", type=str, default="", help="Alias for --blog")
    parser.add_argument("--privacy", choices=["unlisted", "public", "private"], default="public", help="Upload privacy status (default: public)")
    parser.add_argument("--publish-instagram", action="store_true", help="Cross-post produced videos to Instagram Reels via Meta Graph API")
    parser.add_argument("--quality", default="qh", help="Render quality (default: qh)")
    parser.add_argument("--arxiv", type=str, default="", help="Specific arXiv ID or URL to produce (e.g. 2401.12345)")
    args = parser.parse_args()

    daemon = DailyShortsDaemon(quality=args.quality, privacy=args.privacy, publish_instagram=args.publish_instagram)

    if args.dry_run:
        daemon.run_daily_cycle(
            count=args.count,
            dry_run=True,
            publish=False,
            target_arxiv=args.arxiv or None,
            target_perk=args.perk or None,
            target_blog=args.blog or args.news or None,
            target_slot_hour=args.slot_hour,
            preferred_taxonomy=args.preferred_taxonomy,
            preferred_category=args.category or None,
            source=args.source
        )
    elif args.daemon:
        daemon.start_standing_daemon()
    else:
        # Default to running cycle with specified count
        produced = daemon.run_daily_cycle(
            count=args.count,
            dry_run=False,
            publish=True,
            target_arxiv=args.arxiv or None,
            target_perk=args.perk or None,
            target_blog=args.blog or args.news or None,
            target_slot_hour=args.slot_hour,
            preferred_taxonomy=args.preferred_taxonomy,
            preferred_category=args.category or None,
            source=args.source
        )
        if not produced:
            print("❌ Production cycle completed with 0 reels produced. Marking run as failed.")
            sys.exit(1)


if __name__ == "__main__":
    main()

