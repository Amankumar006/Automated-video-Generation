"""
The Model Verse — YouTube Shorts Publisher & Mobile Title Linter
Integrates skills/yt-package (title.py) into the YouTube Shorts publishing workflow.
Lints titles against mobile Shorts constraints (< 45-50 chars), flags vague buzzwords,
ensures front-loaded curiosity, and handles automated video uploads via YouTube Data API v3.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SKILLS_YT_PACKAGE_DIR = PROJECT_ROOT / "skills" / "yt-package"
if str(SKILLS_YT_PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(SKILLS_YT_PACKAGE_DIR))

try:
    import title as title_skill
except ImportError:
    title_skill = None

# Mobile Shorts constraints
MOBILE_SHORTS_MAX_CHARS = 50
MOBILE_SHORTS_OPTIMAL_CHARS = 45
DESKTOP_SEARCH_MAX_CHARS = 60
HARD_LIMIT_CHARS = 100

_BASE_VAGUE = title_skill.VAGUE if title_skill is not None else {
    "amazing", "incredible", "insane", "crazy", "huge", "massive",
    "ultimate", "best", "powerful", "secret", "revolutionary",
    "mindblowing", "epic", "perfect", "complete", "everything"
}
VAGUE_BUZZWORDS: Set[str] = set(_BASE_VAGUE) | {"gamechanger"}

_BASE_STOP = title_skill.STOP if title_skill is not None else {
    "the", "a", "an", "of", "for", "to", "in", "on", "and", "or",
    "is", "are", "with", "your", "you", "my", "i", "this", "that", "it"
}
STOP_WORDS: Set[str] = set(_BASE_STOP) | {"we", "our", "us", "video", "today", "here"}

CURIOSITY_TRIGGERS: Set[str] = {
    "how", "why", "what", "which", "vs", "shock", "shocks", "broke",
    "break", "cut", "cuts", "saved", "saves", "secret", "fix", "fixes",
    "explained", "reveal", "reveals", "proves", "hidden"
}


def words(text: str) -> List[str]:
    if title_skill is not None:
        try:
            return title_skill.words(text)
        except Exception:
            pass
    return re.findall(r"[a-z0-9']+", text.lower())


def lint_title(
    title: str,
    thumbnail_text: Optional[str] = None,
    max_mobile_chars: int = MOBILE_SHORTS_MAX_CHARS
) -> Dict[str, Any]:
    """
    Lints a video title for mobile Shorts constraints (< 45-50 characters to prevent UI truncation).
    Flags vague buzzwords, checks shouting, front-loaded curiosity, and concrete numbers.
    """
    t = title.strip()
    n = len(t)
    issues: List[Tuple[str, str]] = []
    good: List[str] = []

    # 1. Length constraints (Mobile Shorts cutoff priority)
    if n > HARD_LIMIT_CHARS:
        issues.append(("hard_limit", f"{n} characters exceeds YouTube's hard limit of {HARD_LIMIT_CHARS}"))
    elif n > DESKTOP_SEARCH_MAX_CHARS:
        issues.append(("desktop_truncation", f"{n} characters exceeds desktop cutoff ({DESKTOP_SEARCH_MAX_CHARS})"))

    if n > max_mobile_chars:
        issues.append(("mobile_truncation", f"{n} characters exceeds mobile Shorts cutoff ({max_mobile_chars} chars); UI will truncate"))
    elif n > MOBILE_SHORTS_OPTIMAL_CHARS:
        good.append(f"{n} characters is within mobile cutoff ({max_mobile_chars} chars)")
    else:
        good.append(f"{n} characters fits cleanly within mobile Shorts safe zone (<= {MOBILE_SHORTS_OPTIMAL_CHARS} chars)")

    # 2. Vague buzzwords detection
    w_list = words(t)
    vague_found = [w for w in w_list if w in VAGUE_BUZZWORDS]
    if vague_found:
        issues.append(("vague", f"Contains vague buzzwords: {', '.join(sorted(set(vague_found)))}. Swap for concrete metrics or names"))
    else:
        good.append("Clean technical vocabulary without vague buzzwords")

    # 3. Front-loaded curiosity and core subject
    front_3 = [w for w in w_list[:3] if w not in STOP_WORDS]
    if not front_3:
        issues.append(("front_load", "The first three words are filler/stop words; move the subject or curiosity trigger forward"))
    else:
        good.append("Front-loaded with subject or curiosity trigger")

    # Curiosity triggers and open questions
    has_curiosity = any(w in CURIOSITY_TRIGGERS for w in w_list) or t.endswith("?") or "?" in t
    if has_curiosity:
        good.append("Front-loads high curiosity loop or open question")
    else:
        issues.append(("low_curiosity", "Lacks an explicit curiosity trigger (e.g. Why, How, vs, shock)"))

    # 4. Concrete figures (numbers, percentages, multipliers)
    nums = re.findall(r"\b(\d+[\d,.]*(?:%|x|PFLOPS|TFLOPS|GB|MB|k|m|s)?|\$\d+)\b", t, re.I)
    if nums:
        good.append(f"Carries concrete figure ({', '.join(nums[:3])})")
    else:
        issues.append(("no_number", "No concrete number, metric, or multiplier"))

    # 5. Shouting (excessive all-caps words)
    caps = [w for w in t.split() if len(w) > 2 and w.isupper() and not any(c.isdigit() for c in w) and w != "#SHORTS"]
    if len(caps) > 2:
        issues.append(("shouting", f"{len(caps)} all-caps words; reads as spam"))
    elif caps:
        good.append(f"{len(caps)} all-caps word for emphasis")

    # 6. Thumbnail pairing check (if thumbnail text is provided)
    if thumbnail_text:
        tw = set(w_list) - STOP_WORDS
        thw = set(words(thumbnail_text)) - STOP_WORDS
        shared = tw & thw
        if shared:
            issues.append(("duplicate_thumb", f"Thumbnail repeats title words ({', '.join(sorted(shared))})"))
        else:
            good.append("Thumbnail and title carry complementary, non-duplicate words")
        if len(words(thumbnail_text)) > 4:
            issues.append(("thumb_length", f"{len(words(thumbnail_text))} words on thumbnail; 3-4 is maximum for mobile feed"))

    # Calculate overall title score (0-100)
    penalty = 0
    for kind, _ in issues:
        if kind in ("hard_limit", "mobile_truncation", "vague"):
            penalty += 20
        elif kind in ("desktop_truncation", "shouting", "front_load"):
            penalty += 12
        else:
            penalty += 6

    bonus = min(30, 6 * len(good))
    score = max(0, min(100, 100 - penalty + bonus))
    passed = not any(k in ("hard_limit", "mobile_truncation", "vague") for k, _ in issues)

    return {
        "title": t,
        "chars": n,
        "score": score,
        "passed": passed,
        "issues": issues,
        "good": good
    }


def optimize_title_for_mobile(
    title: str,
    max_chars: int = MOBILE_SHORTS_MAX_CHARS
) -> str:
    """
    Optimizes a title to satisfy mobile Shorts constraints (< 45-50 chars).
    Strips vague buzzwords, compresses filler, and trims at word boundary.
    """
    t = title.strip()

    # Strip vague buzzwords
    for v in sorted(VAGUE_BUZZWORDS, key=len, reverse=True):
        t = re.sub(rf"\b{v}\b", "", t, flags=re.I)

    # Clean double spaces
    t = re.sub(r"\s+", " ", t).strip()

    # Extract #Shorts tag if present
    has_shorts = bool(re.search(r"#shorts\b", t, re.I))
    t_clean = re.sub(r"#shorts\b", "", t, flags=re.I).strip()

    tag = " #Shorts" if has_shorts else ""
    available_chars = max(0, max_chars - len(tag))

    if len(t_clean) > available_chars:
        # If available_chars is too small to fit anything with the tag, drop the tag if needed
        if available_chars < 5 and max_chars >= 5:
            tag = ""
            available_chars = max_chars

        if available_chars > 0:
            sliced = t_clean[:available_chars]
            if " " in sliced:
                trimmed = sliced.rsplit(" ", 1)[0].rstrip(":, -")
            else:
                trimmed = sliced.rstrip(":, -")
            t_clean = trimmed
        else:
            t_clean = t_clean[:max_chars]

    res = f"{t_clean}{tag}".strip()
    if len(res) > max_chars:
        res = res[:max_chars].rstrip(":, -")
    return res


# Delegate core publishing operations to pipeline/publisher.py
from pipeline.publisher import (
    get_authenticated_service,
    upload_short,
    generate_shorts_metadata as _base_generate_shorts_metadata
)


def generate_shorts_metadata(
    spec: Dict[str, Any],
    video_path: str,
    enforce_mobile_title_lint: bool = True
) -> Dict[str, Any]:
    """
    Generates viral metadata for YouTube Shorts and lints the title
    for mobile Shorts constraints (< 45-50 characters, front-loaded curiosity).
    """
    meta = _base_generate_shorts_metadata(spec, video_path)
    current_title = meta.get("title", "")

    # Execute Mobile Title Linting
    lint_report = lint_title(current_title)

    if enforce_mobile_title_lint and not lint_report["passed"]:
        # Auto-optimize title to fit inside mobile Shorts cutoff
        optimized = optimize_title_for_mobile(current_title, max_chars=MOBILE_SHORTS_MAX_CHARS)
        meta["title"] = optimized
        lint_report = lint_title(optimized)

    meta["title_lint"] = lint_report
    return meta


def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description="The Model Verse — YouTube Shorts Title Linter & Publisher")
    parser.add_argument("--title", help="Video title to lint or optimize")
    parser.add_argument("--thumb", help="Optional thumbnail text to check duplicate words")
    parser.add_argument("--optimize", action="store_true", help="Auto-optimize title to fit mobile Shorts cutoff")
    parser.add_argument("--max-chars", type=int, default=MOBILE_SHORTS_MAX_CHARS, help="Max title characters (default: 50)")
    parser.add_argument("--json", action="store_true", help="Output JSON result")
    args = parser.parse_args()

    if not args.title:
        parser.error("--title is required.")

    title = args.title
    if args.optimize:
        title = optimize_title_for_mobile(title, max_chars=args.max_chars)

    report = lint_title(title, thumbnail_text=args.thumb, max_mobile_chars=args.max_chars)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"\n  Title: \"{report['title']}\"")
        print(f"  Length: {report['chars']} chars | Score: {report['score']}/100 | Passed: {report['passed']}")
        for kind, msg in report["issues"]:
            print(f"    ❌ [{kind}] {msg}")
        for msg in report["good"]:
            print(f"    ✅ {msg}")
        print()


if __name__ == "__main__":
    main()
