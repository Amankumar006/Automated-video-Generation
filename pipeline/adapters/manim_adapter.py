"""
The Model Verse — Manim Legacy Adapter
Provides backward-compatible rendering via Manim Community Edition (Python / PyCairo).
Translates VSG-IR declarative AST into Manim scene configurations.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union
import cv2
import numpy as np

from pipeline.adapters.base_adapter import (
    RenderAdapter,
    RenderOptions,
    RenderResult,
    CompiledSceneManifest,
)
from pipeline.vsg.schema import VideoSceneGraphIR

logger = logging.getLogger("manim_adapter")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [ManimAdapter] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class ManimLegacyAdapter(RenderAdapter):
    """
    Legacy fallback adapter executing Python Manim scene scripts.
    Maps VSG-IR AST into JSON parameters consumed by Manim scenes.
    """

    def __init__(
        self,
        project_root: Optional[Union[str, Path]] = None,
        default_scene_file: str = "manim_engine/scenes/architecture_scene.py",
        default_scene_class: str = "ArchitectureBreakdownScene"
    ):
        self.root_dir = Path(project_root) if project_root else PROJECT_ROOT
        self.scene_file = default_scene_file
        self.scene_class = default_scene_class

    @property
    def engine_name(self) -> str:
        return "manim"

    @property
    def supports_frame_seek(self) -> bool:
        return False

    def compile_scene_graph(
        self,
        vsg: Union[VideoSceneGraphIR, Dict[str, Any]],
        output_dir: Optional[Union[str, Path]] = None
    ) -> CompiledSceneManifest:
        """
        Compiles the VSG-IR AST into a legacy Manim JSON template.
        """
        if isinstance(vsg, VideoSceneGraphIR):
            vsg_dict = vsg.model_dump()
        elif isinstance(vsg, dict):
            vsg_dict = vsg
        else:
            raise TypeError(f"Expected VideoSceneGraphIR or dict, got {type(vsg)}")

        out_dir = Path(output_dir) if output_dir else (self.root_dir / ".manim_cache")
        out_dir.mkdir(parents=True, exist_ok=True)

        project_id = vsg_dict.get("metadata", {}).get("project_id", f"manim_{int(time.time())}")
        spec_path = out_dir / f"{project_id}_spec.json"

        # Transform VSG-IR beats into legacy format expected by Manim scenes
        legacy_spec = {
            "id": project_id,
            "title": vsg_dict.get("metadata", {}).get("title", "Legacy Short"),
            "category": vsg_dict.get("metadata", {}).get("domain_taxonomy", "architecture_breakdown"),
            "aspect_ratio": vsg_dict.get("metadata", {}).get("aspect_ratio", "9:16"),
            "beats": []
        }

        for b in vsg_dict.get("beats", []):
            time_range = b.get("time_range", {})
            legacy_spec["beats"].append({
                "beat_id": b.get("beat_id", 1),
                "text": b.get("narrative", {}).get("spoken_text", ""),
                "visual_focus": b.get("narrative", {}).get("visual_metaphor", ""),
                "start": time_range.get("start_sec", 0.0),
                "end": time_range.get("end_sec", 2.0),
                "audio_duration": time_range.get("end_sec", 2.0) - time_range.get("start_sec", 0.0),
                "visual_blueprint": {
                    "layout": b.get("narrative", {}).get("visual_metaphor", "default"),
                }
            })

        with open(spec_path, "w", encoding="utf-8") as f:
            json.dump(legacy_spec, f, indent=2)

        canvas = vsg_dict.get("metadata", {}).get("canvas", {})
        manifest = CompiledSceneManifest(
            manifest_id=project_id,
            engine_name=self.engine_name,
            entry_point=self.scene_file,
            props_file_path=str(spec_path.resolve()),
            total_frames=canvas.get("total_frames", 300),
            duration_sec=canvas.get("duration_seconds", 5.0),
            metadata={
                "scene_class": self.scene_class,
                "scene_file": self.scene_file,
            }
        )
        logger.info(f"✅ Compiled Manim legacy manifest '{project_id}' at {spec_path}")
        return manifest

    def render_frame(
        self,
        frame_index: int,
        manifest: CompiledSceneManifest
    ) -> np.ndarray:
        """
        Captures still frame. In Manim, this renders a still or produces a representative canvas.
        """
        # For fast testing or when full manim render is unnecessary, generate canvas frame
        width = 1080
        height = 1920
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        # Add deep charcoal background (#06080F in BGR is 15, 8, 6)
        frame[:] = (15, 8, 6)
        cv2.putText(
            frame,
            f"MANIM FRAME {frame_index}",
            (140, 400),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (248, 189, 56), # BGR cyan
            3
        )
        return frame

    def render_video(
        self,
        manifest: CompiledSceneManifest,
        output_path: str,
        options: Optional[RenderOptions] = None
    ) -> RenderResult:
        """
        Renders scene with Manim Community.
        """
        opts = options or RenderOptions()
        out_path = Path(output_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        t0 = time.perf_counter()
        logger.info(f"🎬 Initiating Manim render: {manifest.entry_point} -> {out_path.name}")

        env = os.environ.copy()
        env["SPEC_PATH"] = manifest.props_file_path

        cmd = [
            "python3",
            "-m",
            "manim",
            "-qh" if opts.quality == "high" else "-ql",
            manifest.entry_point,
            self.scene_class,
            "-o",
            out_path.name
        ]

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.root_dir),
                capture_output=True,
                text=True,
                env=env,
                timeout=opts.timeout_sec
            )
            wall_clock_sec = time.perf_counter() - t0

            # Find output video generated by manim
            expected_video = self.root_dir / "media" / "videos" / Path(manifest.entry_point).stem / "1080p60" / f"{self.scene_class}.mp4"
            if not expected_video.exists():
                candidates = list(self.root_dir.glob(f"media/videos/**/{self.scene_class}.mp4"))
                if candidates:
                    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                    expected_video = candidates[0]

            if expected_video.exists():
                shutil.copyfile(expected_video, out_path)
                success = True
                err = None
            else:
                success = False
                err = f"Manim render completed but output video not located. stderr: {proc.stderr[:300]}"

        except Exception as e:
            wall_clock_sec = time.perf_counter() - t0
            success = False
            err = str(e)

        avg_fps = manifest.total_frames / wall_clock_sec if (wall_clock_sec > 0 and success) else 0.0

        return RenderResult(
            output_file_path=str(out_path),
            total_frames=manifest.total_frames,
            wall_clock_duration_sec=round(wall_clock_sec, 2),
            average_fps=round(avg_fps, 2),
            success=success,
            error_message=err
        )
