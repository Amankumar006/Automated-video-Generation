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

DAEMON_LOGS_DIR = PROJECT_ROOT / "public" / "daemon_logs"
DAEMON_LOGS_DIR.mkdir(parents=True, exist_ok=True)


def evaluate_pedagogical_viability(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluates candidate trending papers with Gemini to pick the most
    curiosity-inducing, visually teachable paper for a 3Blue1Brown-style short.
    """
    import google.generativeai as genai

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return candidates[0]

    genai.configure(api_key=api_key)

    cand_summaries = []
    for i, c in enumerate(candidates[:5]):
        cand_summaries.append(
            f"[{i+1}] Title: {c['title']}\n"
            f"    arXiv: {c['id']}\n"
            f"    Category: {c.get('recommended_category', 'mechanism_deepdive')}\n"
            f"    Abstract: {c['abstract'][:300]}..."
        )

    prompt = f"""You are the Executive Creative Director of 'The Model Verse', a premier YouTube Shorts channel creating 3Blue1Brown-style chalkboard animations about cutting-edge AI.

Review these top 5 trending AI papers from today:
{chr(10).join(cand_summaries)}

Select the SINGLE BEST paper for a 45-second educational animated Short.
Criteria:
1. High Public Fascination: Does it answer a fascinating question that even curious non-specialists care about? (e.g. memory, reasoning, attention, world models, neural circuits).
2. Physical Analogy Potential: Can the core idea be explained using a physical daily-life metaphor (like TV static, cloud shapes, library catalogs, cutting boards)?
3. Visual Geometry: Can Manim represent this using clear chalkboard geometry (graphs, trees, vectors, fields)?

Return ONLY valid JSON matching this schema:
{{
  "selected_index": 1,
  "reasoning": "Brief explanation of why this paper was chosen",
  "recommended_hook": "One-sentence curiosity hook for the script",
  "suggested_everyday_analogy": "The physical analogy to base the explanation on"
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
                idx = int(decision.get("selected_index", 1)) - 1
                if 0 <= idx < len(candidates):
                    selected = candidates[idx]
                    selected["editorial_notes"] = decision
                    return selected
        except Exception as e:
            continue

    print("⚠️ Pedagogical evaluation fallback: using top scoring candidate")
    return candidates[0]


class DailyShortsDaemon:
    """Autonomous scheduler and engine for daily AI Shorts production."""

    def __init__(self, quality: str = "-qh", privacy: str = "unlisted"):
        self.quality = quality
        self.privacy = privacy
        self.critic = ScriptCritic()

    def run_daily_cycle(self, dry_run: bool = False, publish: bool = True) -> Optional[Dict[str, Any]]:
        """Executes one complete daily discovery, production, and publishing cycle."""
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print("\n" + "=" * 80)
        print(f"🤖 THE MODEL VERSE — AUTONOMOUS DAILY SHORTS DAEMON")
        print(f"⏰ Cycle Triggered: {timestamp}")
        print("=" * 80)

        # 1. Fetch & score trending papers
        print("\n🔍 Step 1: Scanning trending papers from Hugging Face & arXiv...")
        papers = get_trending_digest(limit=25)
        unprocessed = [p for p in papers if not p.get("is_processed")]

        if not unprocessed:
            print("ℹ️ All trending papers for today have already been produced. Daily quota satisfied.")
            return None

        print(f"   Found {len(unprocessed)} unprocessed candidates. Selecting top pedagogical breakthrough...")

        # 2. Select top candidate using pedagogical viability filter
        top_paper = evaluate_pedagogical_viability(unprocessed)
        title = top_paper["title"]
        arxiv_id = top_paper["id"]
        category = top_paper.get("recommended_category", "mechanism_deepdive")
        notes = top_paper.get("editorial_notes", {})

        print(f"\n🏆 Selected Today's Breakthrough:")
        print(f"   📄 Title: {title}")
        print(f"   🆔 arXiv: {arxiv_id} | Category: {category.upper()}")
        if notes:
            print(f"   💡 Editorial Hook: {notes.get('recommended_hook')}")
            print(f"   🍎 Everyday Analogy: {notes.get('suggested_everyday_analogy')}")

        if dry_run:
            print("\n🔍 [DRY-RUN] Simulating script generation and pedagogy evaluation...")
            from pipeline.script_generator import generate_script
            spec = generate_script(topic=title, category=category, arxiv_meta=top_paper)
            audit = self.critic.evaluate_script(spec, use_llm=False)
            print(f"   📊 Pedagogical Score: {audit.overall_score}/10 | Grade Level: {audit.grade_level}")
            print(f"   💡 Analogies Found: {audit.total_analogies} | Jargon Count: {audit.total_critical_jargon}")
            print(f"   ✅ Quality Gate Passed: {audit.passed}")
            print("\n🎉 [DRY-RUN] Candidate evaluated successfully. Skipping render & upload.")
            return {"paper": top_paper, "spec": spec, "audit": audit}

        # 3. Produce Full Video (Script + Critic + 1440p60 Manim + Thumbnail + YouTube)
        print("\n🎬 Step 2: Launching End-to-End Autonomous Production Pipeline...")
        video_out = auto_produce(
            arxiv=arxiv_id,
            category=category,
            quality=self.quality,
            publish=publish,
            privacy=self.privacy
        )

        record_paper_production(arxiv_id, title, category, video_out)

        # 4. Generate Daily Production Log Report
        report_data = {
            "timestamp": timestamp,
            "paper_id": arxiv_id,
            "title": title,
            "category": category,
            "video_path": video_out,
            "resolution": f"{BROADCAST_WIDTH}x{BROADCAST_HEIGHT} @ {BROADCAST_FPS}fps",
            "editorial_notes": notes
        }

        log_file = DAEMON_LOGS_DIR / f"daemon_report_{datetime.date.today().isoformat()}.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        md_file = DAEMON_LOGS_DIR / f"daemon_report_{datetime.date.today().isoformat()}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(f"""# 🤖 The Model Verse — Daily Shorts Production Report
**Date:** {datetime.date.today().isoformat()} | **Timestamp:** {timestamp}

## 🏆 Selected Breakthrough Paper
- **Title:** {title}
- **arXiv ID:** [{arxiv_id}](https://arxiv.org/abs/{arxiv_id})
- **Taxonomy / Category:** `{category}`
- **Editorial Hook:** *{notes.get('recommended_hook', 'N/A')}*
- **Everyday Physical Analogy:** *{notes.get('suggested_everyday_analogy', 'N/A')}*

## 🎬 Production & Broadcast Specs
- **Master Resolution:** {BROADCAST_WIDTH}x{BROADCAST_HEIGHT} (2K QHD Vertical)
- **Framerate:** {BROADCAST_FPS} FPS
- **Codec Profile:** High-Tier VP09/AV01 Compatible (CRF 15, BT.709)
- **Local Master Video:** `{video_out}`
- **YouTube Upload Privacy:** `{self.privacy}`
""")

        print(f"\n✅ Daily Production Cycle Complete!")
        print(f"🎥 Master Video: {video_out}")
        print(f"📑 Daemon Log Saved: {log_file} and {md_file}")
        return report_data

    def start_standing_daemon(self, target_hour_utc: int = 3, interval_minutes: int = 60):
        """
        Runs continuously as a background process, checking daily at target_hour_utc (e.g. 03:00 UTC = 8:30 AM IST).
        """
        print(f"🚀 Starting standing daemon loop (Checking every {interval_minutes}m, Target: {target_hour_utc:02d}:00 UTC)...")
        while True:
            now = datetime.datetime.now(datetime.timezone.utc)
            # Check if current hour matches target and hasn't produced today
            if now.hour == target_hour_utc:
                try:
                    self.run_daily_cycle(dry_run=False, publish=True)
                except Exception as e:
                    print(f"⚠️ Error during daemon daily cycle: {e}")
            time.sleep(interval_minutes * 60)


def main():
    parser = argparse.ArgumentParser(description="The Model Verse — Autonomous Daily Paper-to-Shorts Daemon")
    parser.add_argument("--run-now", action="store_true", help="Execute one production cycle immediately")
    parser.add_argument("--dry-run", action="store_true", help="Test paper discovery and script generation without rendering")
    parser.add_argument("--daemon", action="store_true", help="Run standing daemon in continuous background loop")
    parser.add_argument("--privacy", choices=["unlisted", "public", "private"], default="unlisted", help="Upload privacy status (default: unlisted)")
    parser.add_argument("--quality", default="-qh", help="Render quality (default: -qh 60fps)")
    args = parser.parse_args()

    daemon = DailyShortsDaemon(quality=args.quality, privacy=args.privacy)

    if args.dry_run:
        daemon.run_daily_cycle(dry_run=True, publish=False)
    elif args.daemon:
        daemon.start_standing_daemon()
    else:
        # Default to running one cycle
        daemon.run_daily_cycle(dry_run=False, publish=True)


if __name__ == "__main__":
    main()
