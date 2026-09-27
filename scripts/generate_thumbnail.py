"""
The Model Verse — YouTube Shorts Poster & Thumbnail CLI
Command-line interface for generating 1080x1920 high-CTR posters.
"""

import os
import sys
import json
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.thumbnail_generator import thumbnail_generator, THUMBNAILS_DIR

def find_best_keyframe(spec_id: str) -> str:
    """Finds the most iconic extracted keyframe for a given short."""
    cands = [
        PROJECT_ROOT / f"frames_{spec_id}",
        PROJECT_ROOT / f"frames_{spec_id.split('_')[0]}",
    ]
    for d in PROJECT_ROOT.glob("frames_*"):
        if any(part in d.name for part in spec_id.split("_") if len(part) >= 4):
            cands.append(d)

    for frames_dir in cands:
        if frames_dir.exists() and frames_dir.is_dir():
            # Preference order for highest visual impact:
            priority_names = [
                "04_leaderboard_race.png",
                "05_cost_shockwave.png",
                "05_top8_lasers.png",
                "04_routing_mechanism.png",
                "05_efficiency_synthesis.png",
                "03_modular_constellation.png",
                "03_moe_constellation.png",
                "05_payoff_throughput.png",
                "04_o1_query_fetch.png",
                "04_benchmark_race.png",
                "03_pure_rl_tree.png"
            ]
            for p_name in priority_names:
                kf = frames_dir / p_name
                if kf.exists():
                    return str(kf)

            # Fallback to any frame
            pngs = sorted(frames_dir.glob("*.png"))
            if len(pngs) >= 4:
                return str(pngs[3]) # Middle frame usually has the most complex graphic
            elif pngs:
                return str(pngs[0])

    return None

def process_spec_file(spec_path: Path, custom_badge: str = None, keyframe_override: str = None) -> str:
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    spec_id = spec.get("id", spec_path.stem)
    base_kf = keyframe_override or find_best_keyframe(spec_id)
    out_path = str(THUMBNAILS_DIR / f"{spec_id}_poster.png")

    print(f"\n🎨 Generating YouTube Shorts Poster for '{spec.get('title', spec_id)}'...")
    if base_kf:
        print(f"   🖼️ Base Keyframe: {Path(base_kf).name}")
    else:
        print(f"   📐 Base Canvas: Procedural Chalkboard Grid")

    poster = thumbnail_generator.generate(
        spec=spec,
        base_keyframe_path=base_kf,
        output_path=out_path,
        custom_badge=custom_badge
    )
    return poster

def main():
    parser = argparse.ArgumentParser(description="The Model Verse — YouTube Shorts Poster Generator")
    parser.add_argument("--spec", help="Path to script template JSON")
    parser.add_argument("--topic", help="Topic name or prompt (e.g. 'DeepSeek-R1', 'FlashAttention-3')")
    parser.add_argument("--keyframe", help="Path to base keyframe PNG image")
    parser.add_argument("--badge", help="Override hook badge text (e.g. '27x CHEAPER THAN o1')")
    parser.add_argument("--all", action="store_true", help="Generate posters for all available script templates")
    args = parser.parse_args()

    if args.all:
        templates = sorted((PROJECT_ROOT / "pipeline" / "templates").glob("*.json"))
        print(f"\n🚀 Generating posters for {len(templates)} templates...")
        generated = []
        for t in templates:
            try:
                res = process_spec_file(t, custom_badge=args.badge)
                generated.append(res)
            except Exception as e:
                print(f"❌ Failed for {t.name}: {e}")
        print(f"\n🎉 Successfully generated {len(generated)} poster thumbnails in {THUMBNAILS_DIR}/!\n")
        return

    spec_file = None
    if args.spec:
        spec_file = Path(args.spec)
    elif args.topic:
        templates_dir = PROJECT_ROOT / "pipeline" / "templates"
        topic_lower = args.topic.lower()
        for p in templates_dir.glob("*.json"):
            if topic_lower in p.stem.lower() or any(w in p.stem.lower() for w in topic_lower.split() if len(w) >= 4):
                spec_file = p
                break

    if not spec_file or not spec_file.exists():
        parser.error("Please specify a valid --spec file or --topic, or run with --all.")

    poster_path = process_spec_file(spec_file, custom_badge=args.badge, keyframe_override=args.keyframe)
    print(f"✅ Poster ready at: {poster_path}\n")

if __name__ == "__main__":
    main()
