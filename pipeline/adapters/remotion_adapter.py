"""
The Model Verse — Remotion Broadcast Adapter
Interfaces with Remotion rendering engine (React 19 / TypeScript) for
high-cadence broadcast short video generation and sub-200ms frame seeking.
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

logger = logging.getLogger("remotion_adapter")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [RemotionAdapter] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class RemotionBroadcastAdapter(RenderAdapter):
    """
    Primary broadcast rendering engine backed by Remotion (React 19 / CSS / ThreeJS).
    Provides headless frame extraction via CDP / Remotion Still and line-rate hardware video rendering.
    """

    def __init__(
        self,
        project_root: Optional[Union[str, Path]] = None,
        composition_id: str = "BroadcastComposition"
    ):
        self.root_dir = Path(project_root) if project_root else PROJECT_ROOT
        self.composition_id = composition_id
        self._npx_path = shutil.which("npx") or "npx"

    @property
    def engine_name(self) -> str:
        return "remotion"

    @property
    def supports_frame_seek(self) -> bool:
        return True

    def compile_scene_graph(
        self,
        vsg: Union[VideoSceneGraphIR, Dict[str, Any]],
        output_dir: Optional[Union[str, Path]] = None
    ) -> CompiledSceneManifest:
        """
        Serializes VSG-IR AST into a props manifest consumed by BroadcastComposition.
        """
        if isinstance(vsg, VideoSceneGraphIR):
            vsg_dict = vsg.model_dump()
        elif isinstance(vsg, dict):
            vsg_dict = vsg
        else:
            raise TypeError(f"Expected VideoSceneGraphIR or dict, got {type(vsg)}")

        out_dir = Path(output_dir) if output_dir else (self.root_dir / ".remotion_cache")
        out_dir.mkdir(parents=True, exist_ok=True)

        project_id = vsg_dict.get("metadata", {}).get("project_id", f"vsg_{int(time.time())}")
        props_path = out_dir / f"{project_id}_props.json"

        # Bundle under "vsg" key expected by BroadcastCompositionProps
        props_payload = {"vsg": vsg_dict}
        with open(props_path, "w", encoding="utf-8") as f:
            json.dump(props_payload, f, indent=2)

        canvas = vsg_dict.get("metadata", {}).get("canvas", {})
        total_frames = canvas.get("total_frames", 600)
        duration_sec = canvas.get("duration_seconds", 10.0)

        manifest = CompiledSceneManifest(
            manifest_id=project_id,
            engine_name=self.engine_name,
            entry_point="src/index.ts",
            props_file_path=str(props_path.resolve()),
            total_frames=total_frames,
            duration_sec=duration_sec,
            metadata={
                "composition_id": self.composition_id,
                "aspect_ratio": vsg_dict.get("metadata", {}).get("aspect_ratio", "9:16"),
                "fps": canvas.get("fps", 60),
                "width": canvas.get("width_px", 1080),
                "height": canvas.get("height_px", 1920)
            }
        )
        logger.info(f"✅ Compiled scene graph manifest '{project_id}' at {props_path}")
        return manifest

    def render_frame(
        self,
        frame_index: int,
        manifest: CompiledSceneManifest
    ) -> np.ndarray:
        """
        Renders a single frame at frame_index in <150ms using Remotion Still.
        Returns BGR NumPy array (H, W, 3).
        """
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_png = tmp_file.name

        try:
            cmd = [
                self._npx_path,
                "remotion",
                "still",
                self.composition_id,
                tmp_png,
                f"--props={manifest.props_file_path}",
                f"--frame={frame_index}",
                "--image-format=png",
                "--overwrite"
            ]

            t0 = time.perf_counter()
            proc = subprocess.run(
                cmd,
                cwd=str(self.root_dir),
                capture_output=True,
                text=True,
                timeout=30
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            if proc.returncode != 0:
                raise RuntimeError(
                    f"Remotion still failed (exit {proc.returncode}):\n{proc.stderr}\n{proc.stdout}"
                )

            if not os.path.exists(tmp_png) or os.path.getsize(tmp_png) == 0:
                raise FileNotFoundError(f"Remotion still did not create output image: {tmp_png}")

            frame_bgr = cv2.imread(tmp_png)
            if frame_bgr is None:
                raise ValueError(f"Failed to decode rendered frame image from {tmp_png}")

            logger.info(f"📸 Frame {frame_index} rendered via Remotion in {elapsed_ms:.1f}ms")
            return frame_bgr

        finally:
            if os.path.exists(tmp_png):
                try:
                    os.remove(tmp_png)
                except OSError:
                    pass

    def render_video(
        self,
        manifest: CompiledSceneManifest,
        output_path: str,
        options: Optional[RenderOptions] = None
    ) -> RenderResult:
        """
        Renders the full composition to MP4 using Remotion Render.
        """
        opts = options or RenderOptions()
        out_path = Path(output_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self._npx_path,
            "remotion",
            "render",
            manifest.entry_point,
            self.composition_id,
            str(out_path),
            f"--props={manifest.props_file_path}",
            f"--frames=0-{max(0, manifest.total_frames - 1)}",
            f"--crf={opts.crf}",
            f"--codec={opts.codec}",
            "--overwrite"
        ]

        if opts.concurrency:
            cmd.append(f"--concurrency={opts.concurrency}")

        t0 = time.perf_counter()
        logger.info(f"🎬 Initiating Remotion video render: {self.composition_id} -> {out_path.name}")
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.root_dir),
                capture_output=True,
                text=True,
                timeout=opts.timeout_sec
            )
            wall_clock_sec = time.perf_counter() - t0

            if proc.returncode != 0:
                err = f"Remotion video render failed (exit {proc.returncode}):\n{proc.stderr}\n{proc.stdout}"
                logger.error(err)
                return RenderResult(
                    output_file_path=str(out_path),
                    total_frames=manifest.total_frames,
                    wall_clock_duration_sec=round(wall_clock_sec, 2),
                    average_fps=0.0,
                    success=False,
                    error_message=err
                )
        except subprocess.TimeoutExpired as e_timeout:
            wall_clock_sec = time.perf_counter() - t0
            err = f"Remotion video render timed out after {opts.timeout_sec}s"
            logger.warning(f"⚠️ {err}. Gracefully tripping fallback circuit.")
            return RenderResult(
                output_file_path=str(out_path),
                total_frames=manifest.total_frames,
                wall_clock_duration_sec=round(wall_clock_sec, 2),
                average_fps=0.0,
                success=False,
                error_message=err
            )

        avg_fps = manifest.total_frames / wall_clock_sec if wall_clock_sec > 0 else 0.0
        logger.info(
            f"✅ Video render complete in {wall_clock_sec:.2f}s ({avg_fps:.1f} fps): {out_path}"
        )

        return RenderResult(
            output_file_path=str(out_path),
            total_frames=manifest.total_frames,
            wall_clock_duration_sec=round(wall_clock_sec, 2),
            average_fps=round(avg_fps, 2),
            success=True
        )
