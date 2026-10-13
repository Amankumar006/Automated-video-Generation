"""
The Model Verse — Base Render Adapter Specification
Defines the abstract interface and data structures for pluggable rendering engines.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union
import numpy as np

from pipeline.vsg.schema import VideoSceneGraphIR


@dataclass
class RenderOptions:
    """Configuration options for frame and video rendering."""
    width_px: int = 1080
    height_px: int = 1920
    fps: int = 60
    crf: int = 18
    codec: str = "h264"
    concurrency: Optional[int] = None
    quality: str = "high"
    pixel_format: str = "yuv420p"
    hardware_acceleration: bool = True
    timeout_sec: int = 600
    extra_flags: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RenderResult:
    """Outcome metadata of a video rendering job."""
    output_file_path: str
    total_frames: int
    wall_clock_duration_sec: float
    average_fps: float
    peak_memory_mb: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class CompiledSceneManifest:
    """Compiled artifacts ready for the graphics execution backend."""
    manifest_id: str
    engine_name: str
    entry_point: str
    props_file_path: str
    total_frames: int
    duration_sec: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class RenderAdapter(abc.ABC):
    """
    Abstract interface for video rendering backends.
    Isolates the VSG-IR declarative AST from specific graphics libraries.
    """

    @property
    @abc.abstractmethod
    def engine_name(self) -> str:
        """Name of the rendering backend (e.g. 'remotion', 'manim', 'motion-canvas')."""
        pass

    @property
    @abc.abstractmethod
    def supports_frame_seek(self) -> bool:
        """Whether this adapter supports sub-200ms single frame seeking."""
        pass

    @abc.abstractmethod
    def compile_scene_graph(
        self,
        vsg: Union[VideoSceneGraphIR, Dict[str, Any]],
        output_dir: Optional[Union[str, Path]] = None
    ) -> CompiledSceneManifest:
        """
        Compiles the declarative VSG-IR AST into backend-specific runtime assets and manifest.
        """
        pass

    @abc.abstractmethod
    def render_frame(
        self,
        frame_index: int,
        manifest: CompiledSceneManifest
    ) -> np.ndarray:
        """
        Renders a single frame at frame_index directly to a BGR NumPy array (H, W, 3).
        Required for Tier 1 CV Gatekeeper and Tier 2 VLM verification.
        """
        pass

    @abc.abstractmethod
    def render_video(
        self,
        manifest: CompiledSceneManifest,
        output_path: str,
        options: Optional[RenderOptions] = None
    ) -> RenderResult:
        """
        Renders the full composition to a broadcast-grade video file (MP4).
        """
        pass
