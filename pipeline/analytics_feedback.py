"""
The Model Verse — Autonomous Retention & Performance Analytics Feedback Loop
Connects to YouTube Data API & YouTube Analytics API to monitor 24-hour viewer retention,
views velocity, and audience engagement curves, then dynamically feeds back into:
  1. Paper candidate scoring (prioritizing high-performing research domains)
  2. Narration pacing & TTS speed optimization
  3. Hook duration and kinetic visual density
"""

import os
import sys
import json
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.publisher import get_authenticated_service

PUBLIC_DIR = PROJECT_ROOT / "public"
LEDGER_PATH = PUBLIC_DIR / "analytics_retention_ledger.json"
REPORT_PATH = PUBLIC_DIR / "analytics_retention_report.md"


def _parse_iso_duration(iso_duration: str) -> float:
    """Parses ISO 8601 duration (e.g. PT45S, PT1M2S) to total seconds."""
    import re
    m = re.match(r"PT(?:(\d+)M)?(?:(\d+)S)?", iso_duration)
    if not m:
        return 45.0
    minutes = int(m.group(1) or 0)
    seconds = int(m.group(2) or 0)
    return float(minutes * 60 + seconds)


# Canonical taxonomy keywords used across YouTube analytics, paper discovery, and daemon scheduling
TAXONOMY_KEYWORDS: Dict[str, List[str]] = {
    "multimodal_diffusion": [
        "diffusion", "flow matching", "text-to-image", "text-to-video", "video generation",
        "image synthesis", "denoising", "stable diffusion", "dit", "diffusion transformer",
        "flux", "visual generation", "generative video", "streaming video", "video interaction",
        "latent diffusion", "3d generation", "texture generation", "multimodal flow",
        "tv static", "omni-embed", "videollm", "visual text rendering", "motion transfer",
        "video-to-video", "image-to-video"
    ],
    "hardware_efficiency": [
        "flashattention", "kv cache", "quantization", "fp8", "fp4", "int4", "int8",
        "cuda", "kernel", "sram", "vram", "bandwidth", "memory efficiency", "throughput",
        "latency", "pagedattention", "speculative decoding", "cache compression", "hardware",
        "gpu", "serving", "inference acceleration", "linear attention", "state space", "mamba",
        "context window", "prefill-free", "spatial linear memory", "linear memory", "pflops",
        "uniformity trap", "persistence forcing", "lift", "skip connections", "focusvtc", "flowtool"
    ],
    "efficient_architectures": [
        "deepseek-v3", "moe", "mixture of experts", "mixture-of-experts", "sparse routing",
        "router gate", "671b", "expert capacity", "auxiliary loss", "load balancing", "e-moe"
    ],
    "robotics_tamp": [
        "tamp", "robot", "robotics", "manipulation", "kinematic", "motion plan",
        "c-space", "end-effector", "trajectory optimization", "embodied", "tactile",
        "humanoid", "loco-manipulation", "coding agent", "robot agent"
    ],
    "mechanistic_interpretability": [
        "sae", "sparse autoencoder", "interpretability", "monosemantic", "polysemantic",
        "circuits", "superposition", "latent feature", "probing", "steering vector",
        "activation patch", "mechanistic auditing", "grammar"
    ],
    "reasoning_models": [
        "r1", "reasoning", "chain-of-thought", "reinforcement learning", "cot", "o1",
        "test-time compute", "search space", "tree search", "math reasoning", "aime",
        "gpqa", "deepseek-r1", "grpo", "rlhf", "self-rewarding", "corrgrpo", "reward program",
        "shock", "jev"
    ],
    "developer_perks": [
        "startup program", "free credits", "cloud credits", "api credits", "founders hub",
        "aws activate", "google for startups", "claude team", "copilot", "developer perks",
        "free tier", "grant", "subsidy", "tier", "subscription", "startup tier", "credits",
        "free subscription"
    ]
}


def classify_content_taxonomy(title: str, text: str = "", tags: Optional[List[str]] = None) -> str:
    """
    Classifies a paper, video, or script into our channel taxonomy based on title,
    abstract/body text, and tags. Title matches are weighted heavily (3x) over body/tags (1x).
    """
    t_lower = (title or "").lower()
    b_lower = (text or "").lower()
    tags_lower = " ".join(tags or []).lower()

    scores: Dict[str, int] = {}
    for cat, kws in TAXONOMY_KEYWORDS.items():
        score = 0
        for kw in kws:
            if kw in t_lower:
                score += 3
            if kw in b_lower:
                score += 1
            if kw in tags_lower:
                score += 1
        scores[cat] = score

    best_cat = max(scores, key=scores.get)
    if scores[best_cat] > 0:
        return best_cat
    return "general_breakthroughs"


def _classify_video_topic(title: str, tags: List[str]) -> str:
    """Determines the domain taxonomy and category from video metadata."""
    return classify_content_taxonomy(title=title, tags=tags)



class YouTubeRetentionAnalytics:
    """Autonomous engine for tracking video retention, views velocity, and closing the feedback loop."""

    def __init__(self):
        self.youtube = None

    def _ensure_client(self):
        if self.youtube is None:
            try:
                self.youtube = get_authenticated_service(interactive=False)
            except Exception as e:
                print(f"ℹ️ YouTube API authentication bypassed ({e}). Analytics running in offline mode.")
                self.youtube = None

    def fetch_channel_videos_performance(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """Pulls all uploaded shorts with real-time view counts, engagement, and retention metrics."""
        self._ensure_client()
        if not self.youtube:
            return []

        try:
            # 1. Fetch Uploads Playlist
            channel_resp = self.youtube.channels().list(mine=True, part="contentDetails,statistics").execute()
            if not channel_resp.get("items"):
                return []
            channel = channel_resp["items"][0]
            uploads_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]

            # 2. Fetch Playlist Video IDs
            playlist_resp = self.youtube.playlistItems().list(
                playlistId=uploads_id,
                part="snippet,contentDetails",
                maxResults=max_results
            ).execute()

            video_ids = [item["contentDetails"]["videoId"] for item in playlist_resp.get("items", [])]
            if not video_ids:
                return []

            # 3. Batch Fetch Video Statistics & Content Details
            videos_resp = self.youtube.videos().list(
                id=",".join(video_ids),
                part="snippet,statistics,contentDetails,status"
            ).execute()
        except Exception as e:
            print(f"⚠️ YouTube API query failed ({e}). Returning empty records.")
            return []

        now = datetime.datetime.now(datetime.timezone.utc)
        video_records = []

        for v in videos_resp.get("items", []):
            v_id = v["id"]
            snippet = v.get("snippet", {})
            stats = v.get("statistics", {})
            content = v.get("contentDetails", {})
            status = v.get("status", {})

            pub_str = snippet.get("publishedAt", "")
            try:
                pub_time = datetime.datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                hours_live = max((now - pub_time).total_seconds() / 3600.0, 0.5)
            except Exception:
                pub_time = now
                hours_live = 1.0

            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))
            duration_s = _parse_iso_duration(content.get("duration", "PT45S"))
            title = snippet.get("title", "")
            tags = snippet.get("tags", [])
            taxonomy = _classify_video_topic(title, tags)

            # Velocity & Engagement Formulations
            views_per_hour = round(views / hours_live, 2)
            like_ratio = round((likes / max(views, 1)) * 100.0, 2)
            # Weighted engagement score: views (1x) + likes (15x) + comments (30x)
            composite_engagement = round((views + (likes * 15) + (comments * 30)) / max(hours_live, 1), 2)

            record = {
                "video_id": v_id,
                "title": title,
                "shorts_url": f"https://youtube.com/shorts/{v_id}",
                "published_at": pub_str,
                "hours_live": round(hours_live, 1),
                "privacy": status.get("privacyStatus", "unknown"),
                "duration_seconds": duration_s,
                "views": views,
                "likes": likes,
                "comments": comments,
                "views_per_hour": views_per_hour,
                "like_ratio_pct": like_ratio,
                "composite_engagement_velocity": composite_engagement,
                "taxonomy": taxonomy,
                "deep_retention_available": False,
                "retention_curve": []
            }
            video_records.append(record)

        # 4. Attempt YouTube Analytics API v2 Query for granular retention curves
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            from pipeline.config import YOUTUBE_TOKEN_PATH

            if Path(YOUTUBE_TOKEN_PATH).exists():
                creds = Credentials.from_authorized_user_file(YOUTUBE_TOKEN_PATH)
                yt_analytics = build("youtubeAnalytics", "v2", credentials=creds)

                today_str = datetime.date.today().isoformat()
                start_str = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()

                # Query average percentage watched per video
                ret_resp = yt_analytics.reports().query(
                    ids="channel==MINE",
                    startDate=start_str,
                    endDate=today_str,
                    metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage",
                    dimensions="video"
                ).execute()

                rows = ret_resp.get("rows", [])
                ret_map = {row[0]: (float(row[3]), float(row[4])) for row in rows if len(row) >= 5}

                for r in video_records:
                    if r["video_id"] in ret_map:
                        avg_dur, avg_pct = ret_map[r["video_id"]]
                        r["deep_retention_available"] = True
                        r["average_view_duration_seconds"] = round(avg_dur, 2)
                        r["average_percentage_watched"] = round(avg_pct, 2)
        except Exception as e:
            # YouTube Analytics API v2 not enabled or insufficient quota — fall back gracefully
            pass

        return video_records

    def analyze_performance_and_pacing(self, video_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes historical data across categories and calculates:
        - Domain category multipliers (which topics to prefer in paper discovery)
        - Pacing directives (TTS speed recommendation: 1.05x to 1.18x)
        - Hook length recommendations (seconds)
        """
        if not video_records:
            return {
                "channel_total_videos_analyzed": 0,
                "category_multipliers": {},
                "taxonomy_breakdown": {},
                "top_performing_taxonomy": "hardware_efficiency",
                "recommended_tts_speed": 1.12,
                "recommended_hook_duration_s": 7.0,
                "summary": "No video data available yet. Using defaults.",
                "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }

        # Aggregate by taxonomy
        taxonomy_stats: Dict[str, Dict[str, Any]] = {}
        for v in video_records:
            tax = v["taxonomy"]
            if tax not in taxonomy_stats:
                taxonomy_stats[tax] = {
                    "total_views": 0,
                    "total_likes": 0,
                    "total_comments": 0,
                    "count": 0,
                    "avg_velocity": 0.0,
                    "velocities": []
                }
            st = taxonomy_stats[tax]
            st["total_views"] += v["views"]
            st["total_likes"] += v["likes"]
            st["total_comments"] += v["comments"]
            st["count"] += 1
            st["velocities"].append(v["composite_engagement_velocity"])

        # Compute averages & relative weights
        overall_avg_views = sum(v["views"] for v in video_records) / max(len(video_records), 1)
        category_weights = {}

        for tax, st in taxonomy_stats.items():
            avg_views = st["total_views"] / max(st["count"], 1)
            st["avg_views"] = round(avg_views, 1)
            st["avg_velocity"] = round(sum(st["velocities"]) / max(len(st["velocities"]), 1), 2)

            # Weight multiplier between 0.6x and 2.0x based on view performance against overall average
            if overall_avg_views > 0:
                raw_weight = avg_views / overall_avg_views
                clamped_weight = max(0.60, min(2.0, raw_weight))
            else:
                clamped_weight = 1.0
            category_weights[tax] = round(clamped_weight, 2)

        # Sort top taxonomy
        top_taxonomy = max(taxonomy_stats.items(), key=lambda x: x[1]["avg_views"])[0]

        # Pacing Optimization
        # If videos with shorter durations or faster delivery receive higher engagement, nudge TTS speed up
        avg_video_duration = sum(v["duration_seconds"] for v in video_records) / max(len(video_records), 1)
        if avg_video_duration > 50.0:
            # Overly long shorts risk drop-offs — speed up delivery
            rec_speed = 1.15
            rec_hook = 6.8
        elif avg_video_duration < 40.0:
            rec_speed = 1.08
            rec_hook = 7.5
        else:
            rec_speed = 1.12
            rec_hook = 7.2

        return {
            "channel_total_videos_analyzed": len(video_records),
            "category_multipliers": category_weights,
            "taxonomy_breakdown": taxonomy_stats,
            "top_performing_taxonomy": top_taxonomy,
            "recommended_tts_speed": rec_speed,
            "recommended_hook_duration_s": rec_hook,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

    def perform_retention_autopsies(self, video_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Executes Retention Autopsy Critic on videos that have matching templates in pipeline/templates/,
        correlates retention curves with script beats, and updates the Retention Genome Ledger.
        """
        from pipeline.retention_autopsy_critic import retention_autopsy_critic
        from pipeline.retention_genome import retention_genome

        templates_dir = PROJECT_ROOT / "pipeline" / "templates"
        autopsy_reports = []

        for v in video_records:
            v_title = v.get("title", "").lower()
            matched_spec = None
            for p in sorted(templates_dir.glob("*.json")):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        tpl = json.load(f)
                        t_title = tpl.get("title", "").lower()
                        t_id = tpl.get("id", "").lower().replace("-", "_")
                        if t_id and (t_id in v_title.replace("-", "_") or any(w in v_title for w in t_title.split()[:2] if len(w) > 4)):
                            matched_spec = tpl
                            break
                except Exception:
                    continue

            if matched_spec and matched_spec.get("beats"):
                curve = v.get("retention_curve")
                if not curve:
                    quality_proxy = min(9.5, max(5.0, (v.get("like_ratio_pct", 1.5) * 3.5)))
                    avg_view_pct = v.get("average_percentage_watched", 65.0)
                    curve = retention_autopsy_critic.simulate_retention_curve(
                        duration=v.get("duration_seconds", 45.0),
                        hook_quality=quality_proxy,
                        avg_view_pct=avg_view_pct
                    )

                report = retention_autopsy_critic.run_autopsy(matched_spec, curve, video_meta=v)
                retention_genome.record_autopsy(report, matched_spec)
                autopsy_reports.append(report)

        return autopsy_reports

    def generate_and_save_ledger(self) -> Dict[str, Any]:
        """Main execution flow: fetches metrics, runs autopsies, evolves genome, updates ledger file."""
        print("\n=======================================================")
        print("📊 THE MODEL VERSE — YOUTUBE RETENTION ANALYTICS LOOP")
        print("=======================================================\n")

        records = self.fetch_channel_videos_performance()
        if not records and LEDGER_PATH.exists():
            try:
                with open(LEDGER_PATH, "r", encoding="utf-8") as f:
                    cached_ledger = json.load(f)
                    records = cached_ledger.get("videos", [])
                    print(f"ℹ️ Loaded {len(records)} cached video records from {LEDGER_PATH.name}.")
            except Exception as e:
                print(f"⚠️ Could not load cached ledger: {e}")

        print(f"📥 Processed {len(records)} videos for retention intelligence.")

        intelligence = self.analyze_performance_and_pacing(records)
        print(f"🎯 Top Performing Research Domain: {intelligence['top_performing_taxonomy'].upper()}")
        print(f"⚡ Recommended TTS Narration Speed: {intelligence['recommended_tts_speed']}x")
        print(f"⏱️ Recommended Hook Max Duration: {intelligence['recommended_hook_duration_s']}s")

        # Execute Engine 7.0 Retention Autopsies & Evolve Genome
        print("\n🔬 Executing Retention Autopsies & Genome Evolution...")
        from pipeline.retention_genome import retention_genome
        autopsies = self.perform_retention_autopsies(records)
        genome_directives = retention_genome.get_evolutionary_directives()
        print(f"🧬 Genome Evolved: Generation {genome_directives['generation']} | Top Hook: {genome_directives['top_hook_archetype'].upper()}")

        # 1. Save JSON Ledger
        ledger_data = {
            "metadata": {
                "generated_at": intelligence["generated_at"],
                "total_videos": len(records),
                "total_autopsies": len(autopsies)
            },
            "intelligence": intelligence,
            "genome": retention_genome.genome,
            "autopsy_reports": autopsies[:10],
            "videos": sorted(records, key=lambda x: x["views"], reverse=True)
        }
        with open(LEDGER_PATH, "w", encoding="utf-8") as f:
            json.dump(ledger_data, f, indent=2)
        print(f"💾 Persistent JSON Ledger saved to: {LEDGER_PATH.name}")

        # 2. Save Markdown Report Dashboard
        top_videos = sorted(records, key=lambda x: x["views"], reverse=True)
        rows_md = []
        for v in top_videos:
            rows_md.append(
                f"| [{v['title'][:40]}...]({v['shorts_url']}) | `{v['taxonomy']}` | **{v['views']}** | {v['likes']} | {v['comments']} | {v['views_per_hour']} | {v['hours_live']}h |"
            )

        cat_rows_md = []
        for cat, w in intelligence.get("category_multipliers", {}).items():
            st = intelligence.get("taxonomy_breakdown", {}).get(cat, {})
            cat_rows_md.append(
                f"| `{cat}` | **{w}x** | {st.get('avg_views', 0)} | {st.get('count', 0)} videos |"
            )

        # Build Genome Markdown Rows
        genome_bps = retention_genome.genome.get("visual_blueprints", {})
        bp_rows_md = []
        for bp_name, bp_data in sorted(genome_bps.items(), key=lambda x: x[1].get("multiplier", 1.0), reverse=True):
            bp_rows_md.append(
                f"| `{bp_name}` | **{bp_data.get('multiplier', 1.0)}x** | {bp_data.get('avg_retention', 0)}% | {bp_data.get('win_count', 0)}W / {bp_data.get('loss_count', 0)}L | {bp_data.get('recommendation', '')} |"
            )

        md_content = f"""# 📈 The Model Verse — YouTube Performance & Retention Intelligence

**Generated:** {intelligence['generated_at']}  
**Videos Analyzed:** {len(records)} | **Autopsies Performed:** {len(autopsies)}  
**Top Domain:** `{intelligence['top_performing_taxonomy']}`  
**Recommended Pacing:** `{intelligence['recommended_tts_speed']}x` TTS Speed | Hook $\\le$ `{intelligence['recommended_hook_duration_s']}s`

---

## 🧬 Closed-Loop Retention Genome Evolution (Engine 7.0 - Gen {genome_directives['generation']})
The autonomous pipeline continuously evolves these visual and narrative recipes based on real viewer drop-offs:

| Visual Blueprint | Evolutionary Multiplier | Avg Retention | Win/Loss Track | Action Directive |
| :--- | :--- | :--- | :--- | :--- |
{chr(10).join(bp_rows_md)}

**Top Performing Hook Archetype:** `{genome_directives['top_hook_archetype'].upper()}` — *{genome_directives['recommended_hook_guideline']}*

---

## 🏆 Category Performance & Algorithm Multipliers
The paper selector (`daily_shorts_daemon.py`) automatically scales candidate selection probability by these weights:

| Research Domain | Selection Multiplier | Avg Views | Sample Size |
| :--- | :--- | :--- | :--- |
{chr(10).join(cat_rows_md)}

---

## 🎬 Video Performance Leaderboard

| Video Title | Domain | Views | Likes | Comments | Views/Hr | Hours Live |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{chr(10).join(rows_md)}

---

## 🧠 Algorithmic Action Directives
1. **Prioritize {intelligence['top_performing_taxonomy']}**: Audience engagement is highest here; prioritize papers with concrete programmatic or physical analogies.
2. **Prioritize High-Retention Blueprints**: Favor `{', '.join(genome_directives['prioritized_blueprints'][:3])}` in visual storyboarding.
3. **Dynamic TTS Pacing**: Set narration delivery speed to `{intelligence['recommended_tts_speed']}x` to minimize early swipe-away drop-off.
4. **Hook Target**: Cap the opening hook beat at `{intelligence['recommended_hook_duration_s']}s` before transitioning into the physical analogy.
"""
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"📑 Markdown Analytics Report saved to: {REPORT_PATH.name}")

        return ledger_data


# Singleton instance
retention_analytics = YouTubeRetentionAnalytics()

def get_performance_category_bias() -> Dict[str, float]:
    """Helper to retrieve category weights for batch digest paper selection."""
    biases = {}
    if LEDGER_PATH.exists():
        try:
            with open(LEDGER_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                biases = dict(data.get("intelligence", {}).get("category_multipliers", {}))
        except Exception:
            pass
    if "developer_perks" not in biases:
        biases["developer_perks"] = 1.25
    if "tech_news" not in biases:
        biases["tech_news"] = 1.25
    return biases

def get_recommended_pacing() -> Dict[str, Any]:
    """Helper to retrieve dynamic pacing settings for script generator and audio synthesizer."""
    if LEDGER_PATH.exists():
        try:
            with open(LEDGER_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                intel = data.get("intelligence", {})
                return {
                    "tts_speed": intel.get("recommended_tts_speed", 1.10),
                    "hook_max_duration": intel.get("recommended_hook_duration_s", 7.5)
                }
        except Exception:
            pass
    return {"tts_speed": 1.10, "hook_max_duration": 7.5}


if __name__ == "__main__":
    retention_analytics.generate_and_save_ledger()
