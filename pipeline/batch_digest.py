"""
The Model Verse — Autonomous Daily Trending Scraper & Scheduler CLI
Discovers, scores, and auto-produces shorts from trending arXiv and Hugging Face papers.
"""

import os
import sys
import json
import time
import argparse
import datetime
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.arxiv_fetcher import extract_arxiv_id
from pipeline.auto_produce import auto_produce
from pipeline.analytics_feedback import classify_content_taxonomy, get_performance_category_bias

HISTORY_FILE = PROJECT_ROOT / "pipeline" / "digest_history.json"

# Semantic classification keyword weights
MECHANISM_KEYWORDS = {
    "attention": 14, "kv cache": 16, "memory": 10, "quantization": 14, "fp8": 15, "fp4": 15,
    "kernel": 12, "cuda": 12, "flashattention": 18, "speculative decoding": 16,
    "context window": 12, "linear attention": 14, "state space": 14, "mamba": 14,
    "throughput": 10, "latency": 10, "vram": 12, "bandwidth": 12, "pagedattention": 16,
    "cache compression": 16, "spatial memory": 14, "denoising": 14, "diffusion step": 14
}

ARCHITECTURE_KEYWORDS = {
    "mixture of experts": 16, "moe": 16, "sparse": 12, "router": 12, "transformer": 10,
    "deepseek": 14, "llama": 12, "qwen": 12, "foundation model": 10, "distillation": 12,
    "parameters": 10, "hybrid architecture": 14, "multimodal": 12, "diffusion transformer": 16,
    "flow matching": 16, "video generation": 16, "image synthesis": 14, "visual generation": 14,
    "generative video": 16, "world models": 14
}

BENCHMARK_KEYWORDS = {
    "sota": 16, "benchmark": 14, "leaderboard": 16, "aime": 18, "swe-bench": 16,
    "math-500": 16, "gpqa": 15, "codeforces": 16, "reinforcement learning": 14,
    "grpo": 18, "rlhf": 12, "cost reduction": 14, "open weights": 15, "reasoning": 14,
    "accuracy": 10, "outperforms": 12, "breakthrough": 12
}

SHOWDOWN_KEYWORDS = {
    "versus": 16, " vs ": 16, "comparison": 14, "empirical study": 10,
    "dense vs sparse": 18, "scaling laws": 12, "competitive with": 14
}

def load_history() -> Dict[str, Any]:
    """Loads historical log of processed papers."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"processed_papers": {}}

def save_history(history: Dict[str, Any]):
    """Persists historical log of processed papers."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def record_paper_production(arxiv_id: str, title: str, category: str, video_path: str, source: Optional[str] = None):
    """Logs a completed paper production to history."""
    history = load_history()
    clean_id = extract_arxiv_id(arxiv_id)
    if not source:
        clean_lower = clean_id.lower()
        cat_lower = category.lower()
        if clean_lower.startswith("perk_") or cat_lower in ("developer_perks", "startup_credits", "perks"):
            source = "perks"
        elif clean_lower.startswith(("blog_", "news_")) or cat_lower in ("tech_news", "official_blogs", "lab_release"):
            source = "blogs"
        elif clean_lower.startswith("gh_") or "github" in cat_lower:
            source = "github"
        else:
            source = "arxiv"
    history["processed_papers"][clean_id] = {
        "title": title,
        "category": category,
        "source": source,
        "produced_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "video_path": video_path,
        "status": "completed"
    }
    save_history(history)

def fetch_hf_daily_papers(date_str: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
    """Fetches trending papers from Hugging Face Daily Papers API."""
    url = "https://huggingface.co/api/daily_papers"
    if date_str:
        url += f"?date={date_str}"

    req = urllib.request.Request(url, headers={"User-Agent": "TheModelVerse-Pipeline/1.0"})
    papers = []
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for item in data[:limit]:
            p = item.get("paper", item)
            clean_id = extract_arxiv_id(p.get("id", ""))
            if clean_id:
                papers.append({
                    "id": clean_id,
                    "title": p.get("title", "").strip().replace("\n", " "),
                    "abstract": p.get("summary", "").strip().replace("\n", " "),
                    "upvotes": int(item.get("upvotes", p.get("upvotes", 0))),
                    "published_at": item.get("publishedAt", p.get("publishedAt", "")),
                    "authors": [a.get("name") if isinstance(a, dict) else str(a) for a in p.get("authors", [])][:5],
                    "source": "huggingface",
                    "url": f"https://arxiv.org/abs/{clean_id}"
                })
        return papers
    except Exception as e:
        print(f"⚠️ Hugging Face Daily Papers API error ({e}), falling back to arXiv API...")
        return []

def fetch_arxiv_trending(limit: int = 30) -> List[Dict[str, Any]]:
    """Fetches recent AI/ML papers from official arXiv API as fallback."""
    url = f"http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL&sortBy=submittedDate&sortOrder=descending&max_results={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "TheModelVerse-Pipeline/1.0"})
    papers = []
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            id_val = entry.find("atom:id", ns).text.strip().split("/abs/")[-1]
            title = " ".join(entry.find("atom:title", ns).text.strip().split())
            summary = " ".join(entry.find("atom:summary", ns).text.strip().split())
            published = entry.find("atom:published", ns).text.strip()[:10]
            authors = [a.find("atom:name", ns).text.strip() for a in entry.findall("atom:author", ns) if a.find("atom:name", ns) is not None]
            clean_id = extract_arxiv_id(id_val)
            papers.append({
                "id": clean_id,
                "title": title,
                "abstract": summary,
                "upvotes": 0,
                "published_at": published,
                "authors": authors[:5],
                "source": "arxiv",
                "url": f"https://arxiv.org/abs/{clean_id}"
            })
        return papers
    except Exception as e:
        print(f"⚠️ arXiv API query error: {e}")
        return []

def score_and_classify_paper(paper: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes breakthrough impact score and classifies paper into one of 4 categories:
    architecture_breakdown | model_showdown | mechanism_deepdive | benchmark_news
    """
    title_lower = paper["title"].lower()
    abstract_lower = paper["abstract"].lower()
    text = f"{title_lower} {abstract_lower}"

    mech_score = sum(weight for kw, weight in MECHANISM_KEYWORDS.items() if kw in text)
    arch_score = sum(weight for kw, weight in ARCHITECTURE_KEYWORDS.items() if kw in text)
    bench_score = sum(weight for kw, weight in BENCHMARK_KEYWORDS.items() if kw in text)
    show_score = sum(weight for kw, weight in SHOWDOWN_KEYWORDS.items() if kw in text)

    # Community upvote multiplier
    upvotes = paper.get("upvotes", 0)
    vote_boost = min(40, upvotes * 3)

    # Determine recommended category
    scores = {
        "mechanism_deepdive": mech_score,
        "benchmark_news": bench_score,
        "model_showdown": show_score,
        "architecture_breakdown": arch_score
    }
    best_cat = max(scores, key=scores.get)
    max_cat_score = scores[best_cat]

    # Total score combining relevance + community velocity
    total_score = max_cat_score + vote_boost

    # Bonus for title matches (higher precision)
    for kw in list(MECHANISM_KEYWORDS.keys()) + list(ARCHITECTURE_KEYWORDS.keys()) + list(BENCHMARK_KEYWORDS.keys()):
        if kw in title_lower:
            total_score += 10

    # 4. Integrate Live YouTube Analytics Multipliers (Option 2)
    taxonomy = classify_content_taxonomy(paper["title"], paper.get("abstract", ""))
    category_biases = get_performance_category_bias()
    multiplier = category_biases.get(taxonomy, 1.0)

    raw_impact_score = round(total_score, 1)
    weighted_impact_score = round(raw_impact_score * multiplier, 1)

    paper_out = dict(paper)
    paper_out["raw_impact_score"] = raw_impact_score
    paper_out["taxonomy"] = taxonomy
    paper_out["analytics_multiplier"] = multiplier
    paper_out["impact_score"] = weighted_impact_score
    paper_out["recommended_category"] = best_cat
    paper_out["category_scores"] = scores
    return paper_out

def get_trending_digest(date_str: Optional[str] = None, limit: int = 25) -> List[Dict[str, Any]]:
    """Gets sorted list of scored and classified trending papers."""
    papers = fetch_hf_daily_papers(date_str, limit=limit)
    if not papers:
        papers = fetch_arxiv_trending(limit=limit)

    history = load_history()
    processed_ids = set(history.get("processed_papers", {}).keys())

    scored_papers = []
    for p in papers:
        sp = score_and_classify_paper(p)
        sp["is_processed"] = sp["id"] in processed_ids
        scored_papers.append(sp)

    # Sort descending by impact score
    scored_papers.sort(key=lambda x: (not x["is_processed"], x["impact_score"]), reverse=True)
    return scored_papers

def display_digest(papers: List[Dict[str, Any]], top_n: int = 10):
    """Renders a formatted terminal table of trending papers with analytics multipliers."""
    print("\n" + "=" * 110)
    print("🔥 THE MODEL VERSE — DAILY TRENDING AI RESEARCH DIGEST (ANALYTICS ALIGNED)")
    print("=" * 110)
    print(f"{'RANK':<5} {'ARXIV ID':<13} {'SCORE':<7} {'MULT':<6} {'TAXONOMY':<25} {'CATEGORY':<21} {'STATUS':<9} {'TITLE'}")
    print("-" * 110)

    for i, p in enumerate(papers[:top_n], start=1):
        status = "✅ DONE" if p["is_processed"] else "⚡ READY"
        mult_str = f"{p.get('analytics_multiplier', 1.0):.2f}x"
        tax_str = p.get("taxonomy", "general").replace("_", " ").title()[:24]
        cat_str = p.get("recommended_category", "mechanism_deepdive").replace("_", " ").title()[:20]
        title_trunc = p["title"] if len(p["title"]) <= 33 else p["title"][:30] + "..."
        print(f"#{i:<4} {p['id']:<13} {p['impact_score']:<7.1f} {mult_str:<6} {tax_str:<25} {cat_str:<21} {status:<9} {title_trunc}")
    print("=" * 110 + "\n")

def run_cron_cycle(quality: str = "-qh", publish: bool = False, privacy: str = "unlisted"):
    """
    Heartbeat cycle for automated cron schedules:
    Checks if a video was produced in the last 20 hours; if not, produces the top paper.
    """
    history = load_history()
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # Check recent productions
    recent_count = 0
    for p_id, info in history.get("processed_papers", {}).items():
        prod_time_str = info.get("produced_at")
        if prod_time_str:
            try:
                prod_time = datetime.datetime.fromisoformat(prod_time_str)
                if (now - prod_time).total_seconds() < 20 * 3600:
                    recent_count += 1
            except Exception:
                pass

    if recent_count > 0:
        print(f"🕒 Cron Heartbeat: Daily quota met ({recent_count} short produced in past 20 hours). Standing by.")
        return

    print("🚀 Cron Heartbeat: No video produced in last 20 hours. Scanning trending digest...")
    papers = get_trending_digest(limit=25)
    unprocessed = [p for p in papers if not p["is_processed"]]

    if not unprocessed:
        print("⚠️ No new unprocessed papers found today.")
        return

    top_paper = unprocessed[0]
    print(f"🏆 Top Candidate Selected: {top_paper['title']} (arXiv: {top_paper['id']})")
    print(f"   Score: {top_paper['impact_score']} | Category: {top_paper['recommended_category'].upper()}")

    # Execute full-pipeline production
    video_out = auto_produce(
        arxiv=top_paper["id"],
        category=top_paper["recommended_category"],
        quality=quality,
        publish=publish,
        privacy=privacy
    )

    record_paper_production(top_paper["id"], top_paper["title"], top_paper["recommended_category"], video_out)
    print(f"✅ Daily Cron Production Complete: {video_out}")

def main():
    parser = argparse.ArgumentParser(description="The Model Verse — Autonomous Daily Trending Scraper & Scheduler")
    parser.add_argument("--list", action="store_true", help="List top trending papers for today")
    parser.add_argument("--limit", type=int, default=10, help="Number of papers to list (default: 10)")
    parser.add_argument("--date", help="Specific date for trending digest (YYYY-MM-DD)")
    parser.add_argument("--auto", action="store_true", help="Automatically produce a short for the #1 trending paper")
    parser.add_argument("--paper-id", help="Manually produce a specific paper from digest by arXiv ID")
    parser.add_argument("--category", choices=["architecture_breakdown", "model_showdown", "mechanism_deepdive", "benchmark_news"], help="Override detected category")
    parser.add_argument("--quality", default="-qh", choices=["-ql", "-qm", "-qh"], help="Manim render quality (default: -qh)")
    parser.add_argument("--publish", action="store_true", help="Upload produced video to YouTube Shorts")
    parser.add_argument("--privacy", choices=["unlisted", "public", "private"], default="unlisted", help="Upload privacy status (default: unlisted)")
    parser.add_argument("--dry-run-publish", action="store_true", help="Preview YouTube Shorts metadata without uploading")
    parser.add_argument("--cron", action="store_true", help="Run in automated daily cron mode")
    args = parser.parse_args()

    # Pre-populate history with existing master videos if empty
    history = load_history()
    if not history.get("processed_papers"):
        history["processed_papers"]["2407.08608"] = {
            "title": "FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-precision",
            "category": "mechanism_deepdive",
            "produced_at": "2026-09-25T14:57:07Z",
            "video_path": "final_flashattention_3_mechanism_deepdive_mechanism_deepdive.mp4",
            "status": "completed"
        }
        history["processed_papers"]["2501.12948"] = {
            "title": "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning",
            "category": "benchmark_news",
            "produced_at": "2026-09-26T11:36:28Z",
            "video_path": "final_deepseek-r1_benchmark_news_benchmark_news.mp4",
            "status": "completed"
        }
        history["processed_papers"]["2412.19437"] = {
            "title": "DeepSeek-V3 Technical Report",
            "category": "architecture_breakdown",
            "produced_at": "2026-09-24T23:33:00Z",
            "video_path": "final_deepseek-v3_architecture_breakdown.mp4",
            "status": "completed"
        }
        save_history(history)

    if args.cron:
        run_cron_cycle(quality=args.quality, publish=args.publish, privacy=args.privacy)
        return

    if args.auto:
        papers = get_trending_digest(date_str=args.date, limit=25)
        unprocessed = [p for p in papers if not p["is_processed"]]
        if not unprocessed:
            print("⚠️ All top papers have already been produced!")
            return
        target = unprocessed[0]
        cat = args.category or target["recommended_category"]
        print(f"\n🚀 Autonomous Auto-Production triggered for #1 trending paper:")
        print(f"   Title: {target['title']}")
        print(f"   arXiv ID: {target['id']} | Category: {cat.upper()} | Score: {target['impact_score']}")
        
        video_out = auto_produce(
            arxiv=target["id"],
            category=cat,
            quality=args.quality,
            publish=args.publish,
            privacy=args.privacy,
            dry_run_publish=args.dry_run_publish
        )
        record_paper_production(target["id"], target["title"], cat, video_out)
        return

    if args.paper_id:
        papers = get_trending_digest(date_str=args.date, limit=50)
        match = [p for p in papers if extract_arxiv_id(p["id"]) == extract_arxiv_id(args.paper_id)]
        if match:
            target = match[0]
            cat = args.category or target["recommended_category"]
        else:
            target = {"id": args.paper_id, "title": f"Paper {args.paper_id}"}
            cat = args.category or "mechanism_deepdive"

        print(f"\n🚀 Manual Production triggered for arXiv: {target['id']}")
        video_out = auto_produce(
            arxiv=target["id"],
            category=cat,
            quality=args.quality,
            publish=args.publish,
            privacy=args.privacy,
            dry_run_publish=args.dry_run_publish
        )
        record_paper_production(target["id"], target.get("title", ""), cat, video_out)
        return

    # Default action: list trending digest
    papers = get_trending_digest(date_str=args.date, limit=args.limit * 2)
    display_digest(papers, top_n=args.limit)

if __name__ == "__main__":
    main()
