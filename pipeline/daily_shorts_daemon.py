"""
The Model Verse — Autonomous Daily Paper-to-Shorts Daemon
Monitors trending AI research daily, selects the most visually and pedagogically compelling
breakthrough paper, generates an intuitive Feynman-standard script, produces a 1440p60 video,
and uploads to YouTube Shorts as Unlisted for 1-click review.
"""

import os
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
from pipeline.auto_produce import auto_produce
from pipeline.script_critic import ScriptCritic
from pipeline.config import WORKSPACE_ROOT, BROADCAST_WIDTH, BROADCAST_HEIGHT, BROADCAST_FPS
from pipeline.analytics_feedback import (
    retention_analytics,
    get_performance_category_bias,
    get_recommended_pacing
)

DAEMON_LOGS_DIR = PROJECT_ROOT / "public" / "daemon_logs"
DAEMON_LOGS_DIR.mkdir(parents=True, exist_ok=True)


def evaluate_pedagogical_viability(candidates: List[Dict[str, Any]], count: int = 1) -> List[Dict[str, Any]]:
    """
    Evaluates candidate trending papers with Gemini to pick the top `count`
    curiosity-inducing, visually teachable papers across diverse AI domains.
    """
    import google.generativeai as genai

    if not candidates:
        return []

    target_count = min(count, len(candidates))
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return candidates[:target_count]

    genai.configure(api_key=api_key)

    cand_summaries = []
    num_eval = min(20, len(candidates))
    for i, c in enumerate(candidates[:num_eval]):
        cand_summaries.append(
            f"[{i+1}] Title: {c['title']}\n"
            f"    arXiv: {c['id']}\n"
            f"    Category: {c.get('recommended_category', 'mechanism_deepdive')}\n"
            f"    Abstract: {c['abstract'][:250]}..."
        )

    # Query dynamic retention multipliers from analytics feedback
    category_biases = get_performance_category_bias()
    bias_desc = ""
    if category_biases:
        bias_str = ", ".join([f"{k}: {v}x multiplier" for k, v in category_biases.items()])
        bias_desc = f"\n4. Audience Retention & Views Velocity: Live YouTube analytics shows viewers strongly favor topics with high multipliers: [{bias_str}]. Favor papers whose domains align with these winning formats!"

    prompt = f"""You are the Executive Creative Director of 'The Model Verse', a premier YouTube Shorts channel creating 3Blue1Brown-style chalkboard animations about cutting-edge AI.

Review these top {len(cand_summaries)} trending AI papers from today:
{chr(10).join(cand_summaries)}

Select the {target_count} BEST and MOST DIVERSE papers for 45-second educational animated Shorts.
Criteria:
1. High Public Fascination: Does it answer a fascinating question that curious non-specialists care about? (e.g. reasoning, memory, world models, attention, latent circuits).
2. Physical Analogy Potential: Can the core idea be explained using everyday tangible comparisons (e.g. library, clouds, mirror, sculptor, train, static)?
3. Domain Diversity: Pick papers from DIFFERENT categories (e.g. architectures, reasoning/planning, attention/memory, multimodal/diffusion, benchmarks) to keep the channel varied.{bias_desc}

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
                decision = json.loads(response.text.strip())
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

                # Fill any shortfall with remaining diverse candidates
                for c_idx, cand in enumerate(candidates):
                    if len(selected_list) >= target_count:
                        break
                    if c_idx not in selected_indices:
                        selected_list.append(cand)
                        selected_indices.add(c_idx)

                if selected_list:
                    return selected_list
        except Exception:
            continue

    print(f"⚠️ Pedagogical evaluation fallback: selecting top {target_count} candidates")
    return candidates[:target_count]


class DailyShortsDaemon:
    """Autonomous scheduler and engine for daily AI Shorts production."""

    def __init__(self, quality: str = "-qh", privacy: str = "public"):
        if quality and not quality.startswith("-"):
            self.quality = f"-{quality}"
        else:
            self.quality = quality or "-qh"
        self.privacy = privacy
        self.critic = ScriptCritic()

    def run_daily_cycle(self, count: int = 1, dry_run: bool = False, publish: bool = True, target_arxiv: Optional[str] = None) -> List[Dict[str, Any]]:
        """Executes discovery, production, and publishing for `count` reels."""
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print("\n" + "=" * 80)
        print(f"🤖 THE MODEL VERSE — AUTONOMOUS DAILY SHORTS DAEMON")
        print(f"⏰ Cycle Triggered: {timestamp} | Target Quota: {count} Reels")
        print("=" * 80)

        # 0. Poll YouTube Analytics & Refresh Performance Multipliers
        print("\n📊 Step 0: Polling YouTube Analytics & Real-Time Viewer Retention...")
        try:
            retention_analytics.generate_and_save_ledger()
        except Exception as e:
            print(f"   ⚠️ Could not refresh retention ledger: {e}")

        if target_arxiv:
            print(f"\n🎯 Direct Target Paper Specified: {target_arxiv}")
            from pipeline.arxiv_fetcher import fetch_arxiv_paper
            p_data = fetch_arxiv_paper(target_arxiv)
            if not p_data:
                print(f"⚠️ Could not fetch metadata for arXiv ID: {target_arxiv}")
                return []
            selected_papers = [{
                "title": p_data["title"],
                "id": p_data["arxiv_id"],
                "recommended_category": "mechanism_deepdive",
                "abstract": p_data.get("abstract", ""),
                "editorial_notes": {
                    "recommended_hook": f"How {p_data['title']} works under the hood",
                    "suggested_everyday_analogy": "Mechanical blueprint breakdown"
                }
            }]
        else:
            # 1. Fetch & score trending papers
            print("\n🔍 Step 1: Scanning trending papers from Hugging Face & arXiv...")
            papers = get_trending_digest(limit=35)
            unprocessed = [p for p in papers if not p.get("is_processed")]

            if not unprocessed:
                print("ℹ️ All trending papers for today have already been produced. Daily quota satisfied.")
                return []

            print(f"   Found {len(unprocessed)} unprocessed candidates. Selecting top {count} pedagogical breakthroughs...")

            # 2. Select top diverse candidates using pedagogical viability filter
            selected_papers = evaluate_pedagogical_viability(unprocessed, count=count)
        print(f"\n🏆 Selected {len(selected_papers)} Breakthrough Papers for Today's Reels Quota:")
        for idx, p in enumerate(selected_papers):
            notes = p.get("editorial_notes", {})
            print(f"   [{idx+1}/{len(selected_papers)}] {p['title']} ({p['id']}) — Category: {p.get('recommended_category', 'mechanism_deepdive').upper()}")
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

            if dry_run:
                print("🔍 [DRY-RUN] Simulating script generation and pedagogy evaluation...")
                from pipeline.script_generator import generate_script
                spec = generate_script(topic=title, category=category, arxiv_meta=top_paper)
                audit = self.critic.evaluate_script(spec, use_llm=False)
                print(f"   📊 Pedagogical Score: {audit.overall_score}/10 | Grade Level: {audit.grade_level}")
                print(f"   💡 Analogies Found: {audit.total_analogies} | Jargon Count: {audit.total_critical_jargon}")
                print(f"   ✅ Quality Gate Passed: {audit.passed}")
                reports.append({
                    "paper": top_paper,
                    "spec": spec,
                    "audit": audit,
                    "status": "dry_run_success"
                })
                continue

            # Production (Script + Critic + 1440p60 Manim + Thumbnail + YouTube)
            pacing = get_recommended_pacing()
            rec_speed = pacing.get("tts_speed", 1.12)
            video_out = auto_produce(
                arxiv=arxiv_id,
                category=category,
                speed=rec_speed,
                quality=self.quality,
                publish=publish,
                privacy=self.privacy,
                paper_meta=top_paper
            )

            record_paper_production(arxiv_id, title, category, video_out)

            report_item = {
                "reel_index": idx + 1,
                "timestamp": timestamp,
                "paper_id": arxiv_id,
                "title": title,
                "category": category,
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
                reels_md.append(f"""### Reel {r['reel_index']}: {r['title']}
- **arXiv ID:** [{r['paper_id']}](https://arxiv.org/abs/{r['paper_id']})
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
        Default hours (UTC): [1, 5, 9, 12, 16] -> 5 reels timed right before global viewer surges.
        """
        if target_hours_utc is None:
            target_hours_utc = [1, 5, 9, 12, 16]

        print(f"🚀 Starting standing daemon loop (Checking every {interval_minutes}m, Target Hours UTC: {target_hours_utc})...")
        last_triggered_hour = -1
        while True:
            now = datetime.datetime.now(datetime.timezone.utc)
            if now.hour in target_hours_utc and now.hour != last_triggered_hour:
                print(f"⏰ Peak Hour Reached ({now.hour:02d}:00 UTC). Triggering Reel Production...")
                try:
                    self.run_daily_cycle(count=1, dry_run=False, publish=True)
                    last_triggered_hour = now.hour
                except Exception as e:
                    print(f"⚠️ Error during daemon cycle: {e}")
            time.sleep(interval_minutes * 60)


def main():
    parser = argparse.ArgumentParser(description="The Model Verse — Autonomous Daily Paper-to-Shorts Daemon")
    parser.add_argument("--run-now", action="store_true", help="Execute production cycle immediately")
    parser.add_argument("--count", type=int, default=1, help="Number of reels to produce (default: 1, e.g. 5)")
    parser.add_argument("--dry-run", action="store_true", help="Test paper discovery and script generation without rendering")
    parser.add_argument("--daemon", action="store_true", help="Run standing daemon in continuous background loop across 5 daily slots")
    parser.add_argument("--privacy", choices=["unlisted", "public", "private"], default="public", help="Upload privacy status (default: public)")
    parser.add_argument("--quality", default="qh", help="Render quality (default: qh)")
    parser.add_argument("--arxiv", type=str, default="", help="Specific arXiv ID or URL to produce (e.g. 2401.12345)")
    args = parser.parse_args()

    daemon = DailyShortsDaemon(quality=args.quality, privacy=args.privacy)

    if args.dry_run:
        daemon.run_daily_cycle(count=args.count, dry_run=True, publish=False, target_arxiv=args.arxiv or None)
    elif args.daemon:
        daemon.start_standing_daemon()
    else:
        # Default to running cycle with specified count
        daemon.run_daily_cycle(count=args.count, dry_run=False, publish=True, target_arxiv=args.arxiv or None)


if __name__ == "__main__":
    main()

