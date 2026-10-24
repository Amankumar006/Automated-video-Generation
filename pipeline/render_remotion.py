"""
The Model Verse — Headless Remotion Broadcast Rendering CLI
Consumes declarative VSG-IR JSON AST files and renders broadcast MP4 video or still frames.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.adapters.remotion_adapter import RemotionBroadcastAdapter
from pipeline.adapters.base_adapter import RenderOptions
from pipeline.vsg.schema import VideoSceneGraphIR
from pipeline.vsg.linter import VSGASTLinter

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [RenderRemotion] %(message)s"
)
logger = logging.getLogger("render_remotion")


def main():
    parser = argparse.ArgumentParser(description="Render VSG-IR AST using Remotion Broadcast Engine")
    parser.add_argument("--input-vsg", "-i", type=str, required=True, help="Path to VSG-IR JSON file")
    parser.add_argument("--output", "-o", type=str, default="output/render_remotion.mp4", help="Output video or still path")
    parser.add_argument("--still-frame", "-f", type=int, default=None, help="Render a single frame index instead of full video")
    parser.add_argument("--skip-lint", action="store_true", help="Skip pre-render AST linting")
    parser.add_argument("--crf", type=int, default=18, help="H.264 CRF quality level (default: 18)")
    parser.add_argument("--concurrency", type=int, default=None, help="Remotion render concurrency")

    args = parser.parse_args()

    vsg_path = Path(args.input_vsg)
    if not vsg_path.exists():
        logger.error(f"Input VSG file not found: {vsg_path}")
        sys.exit(1)

    with open(vsg_path, "r", encoding="utf-8") as f:
        vsg_raw = json.load(f)

    # Validate against Pydantic schema
    vsg = VideoSceneGraphIR.model_validate(vsg_raw)

    # Run AST linter unless skipped
    if not args.skip_lint:
        linter = VSGASTLinter()
        lint_report, solved_vsg = linter.lint_and_solve(vsg)
        if not lint_report.passed:
            logger.error(f"❌ VSG-IR Linting Failed with {len(lint_report.violations)} violations!")
            for v in lint_report.violations:
                logger.error(f"  - [{v.severity}] {v.rule}: {v.message}")
            sys.exit(1)
        vsg = solved_vsg
        logger.info(f"✅ Pre-render AST Lint passed: 0 critical collisions or safe-zone breaches.")

    adapter = RemotionBroadcastAdapter()
    manifest = adapter.compile_scene_graph(vsg)

    if args.still_frame is not None:
        logger.info(f"📸 Seeking and rendering still frame {args.still_frame}...")
        frame_bgr = adapter.render_frame(args.still_frame, manifest)
        out_path = Path(args.output)
        if out_path.suffix.lower() not in [".png", ".jpg", ".jpeg"]:
            out_path = out_path.with_suffix(".png")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        import cv2
        cv2.imwrite(str(out_path), frame_bgr)
        logger.info(f"✅ Still frame saved to {out_path}")
    else:
        logger.info(f"🎬 Rendering full broadcast short to {args.output}...")
        options = RenderOptions(
            crf=args.crf,
            concurrency=args.concurrency
        )
        result = adapter.render_video(manifest, args.output, options=options)
        if not result.success:
            logger.error(f"❌ Video render failed: {result.error_message}")
            sys.exit(1)
        logger.info(
            f"🎉 Render completed in {result.wall_clock_duration_sec}s ({result.average_fps} fps): {result.output_file_path}"
        )


if __name__ == "__main__":
    main()
