"""Shared Interface Contracts between The Model Verse Shorts and Project Aether.

This module provides clean, decoupled shared contracts enabling Project Aether
(3D cinematic virtual studio) to consume The Model Verse Shorts educational scripts
and 2D Manim/arXiv visual assets without circular runtime dependencies.

Core Components:
1. EducationalAssetRole: Semantic roles for 2D assets inside 3D shots.
2. EducationalAssetConditioningPackage: Container for SVG, raster, or video assets
   used as visual conditioning for Aether Complexity Levels 1-4.
3. HybridRenderMode: Multi-engine render allocation (2D Manim, 3D Aether, composite).
4. DualEnginePipelineConfig: Full configuration for dual-engine render workflows.
5. ScriptToFilmSceneAdapter: Bidirectional translation between 6-beat VideoSpec
   and Aether DirectorProductionBrief / FilmScene structures.
"""

from __future__ import annotations

from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aether.compiler.schemas import (
    AudioRequirement,
    ComplexityLevel,
    ProviderTarget,
    ShotRequirement,
    SpatialRepresentationPackage,
)
from aether.director.schemas import (
    DirectorProductionBrief,
    FilmScene,
)

# Safe decoupled import of Model Verse Shorts schemas
try:
    from pipeline.schemas import BeatSpec, SFXCue, VideoCategory, VideoSpec
except ImportError:  # pragma: no cover
    BeatSpec = None  # type: ignore
    SFXCue = None  # type: ignore
    VideoCategory = None  # type: ignore
    VideoSpec = None  # type: ignore


class EducationalAssetRole(str, Enum):
    """Specifies the visual conditioning role of a 2D asset in a 3D Aether shot."""
    LEVEL_1_REFERENCE_IMAGE = "LEVEL_1_REFERENCE_IMAGE"      # Image conditioning anchor (Level 1)
    LEVEL_2_KEYFRAME_START = "LEVEL_2_KEYFRAME_START"        # Start keyframe for interpolation (Level 2)
    LEVEL_2_KEYFRAME_END = "LEVEL_2_KEYFRAME_END"            # End keyframe for interpolation (Level 2)
    LEVEL_3_TRAJECTORY_GUIDE = "LEVEL_3_TRAJECTORY_GUIDE"    # 2D motion/pose trajectory guide (Level 3)
    LEVEL_4_SURFACE_TEXTURE = "LEVEL_4_SURFACE_TEXTURE"      # 3D surface/projection texture (Level 4)
    PICTURE_IN_PICTURE_OVERLAY = "PIP_OVERLAY"              # 2D Manim HUD overlay composited on 3D plate
    BACKGROUND_PROJECTION_PLATE = "BACKGROUND_PLATE"        # Projected on virtual stage screen/display
    CHALKBOARD_HUD = "CHALKBOARD_HUD"                        # Floating technical HUD chalkboard card

    def __str__(self) -> str:
        return self.value


class EducationalAssetConditioningPackage(BaseModel):
    """Encapsulates a 2D Manim or arXiv educational asset for conditioning Aether shots."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    asset_id: str = Field(..., description="Unique asset identifier e.g. 'fig_01_arch'")
    role: EducationalAssetRole = Field(
        EducationalAssetRole.LEVEL_1_REFERENCE_IMAGE,
        description="Visual conditioning role within the Aether shot",
    )
    file_uri: str = Field(..., description="File path or URI to the SVG, image, or video asset")
    source_beat_id: Optional[int] = Field(None, description="Source beat index (1-6) this asset belongs to")
    media_type: str = Field("image/png", description="MIME type ('image/png', 'image/svg+xml', 'video/mp4')")
    spatial_bounds: Optional[List[float]] = Field(
        None,
        description="Normalized placement [x1, y1, x2, y2] in [0.0, 1.0]",
    )
    caption: Optional[str] = Field(None, description="Technical caption or figure title")
    complexity_level_target: Optional[ComplexityLevel] = Field(
        None,
        description="Target Aether complexity level (1-4)",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata and render tags")

    @field_validator("spatial_bounds")
    @classmethod
    def _validate_spatial_bounds(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        if v is not None:
            if len(v) != 4:
                raise ValueError(f"spatial_bounds must contain exactly 4 floats [x1, y1, x2, y2], got {len(v)}")
            for coord in v:
                if not (0.0 <= coord <= 1.0):
                    raise ValueError(f"spatial_bounds coordinates must be in [0.0, 1.0], got {coord}")
            if v[0] >= v[2] or v[1] >= v[3]:
                raise ValueError(
                    f"spatial_bounds must define positive area with x1 < x2 and y1 < y2, got {v}"
                )
        return v

    def is_vector(self) -> bool:
        """Checks if the asset is vector format (SVG)."""
        uri = self.file_uri.lower()
        return uri.endswith(".svg") or "svg" in self.media_type.lower()

    def is_raster(self) -> bool:
        """Checks if the asset is raster image format (PNG, JPG, WebP)."""
        uri = self.file_uri.lower()
        return (
            uri.endswith((".png", ".jpg", ".jpeg", ".webp"))
            or "image/" in self.media_type.lower()
        ) and not self.is_vector()

    def is_video(self) -> bool:
        """Checks if the asset is video format (MP4, WebM)."""
        uri = self.file_uri.lower()
        return uri.endswith((".mp4", ".mov", ".webm")) or "video/" in self.media_type.lower()

    @classmethod
    def from_figure_dict(
        cls,
        fig: Dict[str, Any],
        beat_id: Optional[int] = None,
        role: EducationalAssetRole = EducationalAssetRole.LEVEL_1_REFERENCE_IMAGE,
        prefer_vector: bool = False,
    ) -> EducationalAssetConditioningPackage:
        """Constructs a package from pipeline.arxiv_vector_extractor.extract_paper_figures output."""
        svg_path = fig.get("svg_path")
        image_path = fig.get("image_path")

        if prefer_vector and svg_path:
            file_uri = str(svg_path)
            media_type = "image/svg+xml"
        elif image_path:
            file_uri = str(image_path)
            media_type = "image/png"
        elif svg_path:
            file_uri = str(svg_path)
            media_type = "image/svg+xml"
        else:
            file_uri = str(fig.get("file_path", fig.get("uri", "")))
            media_type = "image/png"

        asset_id = (
            fig.get("asset_id")
            or f"fig_{fig.get('page_num', 1)}_{Path(file_uri).stem}"
            if file_uri
            else "fig_unknown"
        )
        caption = fig.get("caption")
        score = fig.get("score")

        meta = {
            "page_num": fig.get("page_num"),
            "original_type": fig.get("original_type"),
            "score": score,
            "svg_path": svg_path,
            "image_path": image_path,
        }

        # Map role to target complexity level
        role_to_level = {
            EducationalAssetRole.LEVEL_1_REFERENCE_IMAGE: ComplexityLevel.REFERENCE_IMAGE,
            EducationalAssetRole.LEVEL_2_KEYFRAME_START: ComplexityLevel.KEYFRAMES_INTERPOLATION,
            EducationalAssetRole.LEVEL_2_KEYFRAME_END: ComplexityLevel.KEYFRAMES_INTERPOLATION,
            EducationalAssetRole.LEVEL_3_TRAJECTORY_GUIDE: ComplexityLevel.TWOD_TRAJECTORY_POSE,
            EducationalAssetRole.LEVEL_4_SURFACE_TEXTURE: ComplexityLevel.THREED_BLOCKING,
        }
        level_target = role_to_level.get(role)

        return cls(
            asset_id=asset_id,
            role=role,
            file_uri=file_uri,
            source_beat_id=beat_id,
            media_type=media_type,
            caption=caption,
            complexity_level_target=level_target,
            metadata=meta,
        )

    def apply_to_shot(self, shot_req: ShotRequirement) -> ShotRequirement:
        """Applies this conditioning package onto an Aether ShotRequirement."""
        meta = shot_req.metadata.setdefault("conditioning_packages", [])
        meta.append(self.model_dump(mode="json"))

        if self.role == EducationalAssetRole.LEVEL_1_REFERENCE_IMAGE:
            shot_req.first_frame_uri = self.file_uri
            shot_req.metadata["reference_image_uri"] = self.file_uri
            shot_req.metadata["conditioning_asset_id"] = self.asset_id
        elif self.role == EducationalAssetRole.LEVEL_2_KEYFRAME_START:
            shot_req.first_frame_uri = self.file_uri
        elif self.role == EducationalAssetRole.LEVEL_2_KEYFRAME_END:
            shot_req.last_frame_uri = self.file_uri
        elif self.role == EducationalAssetRole.LEVEL_3_TRAJECTORY_GUIDE:
            shot_req.metadata["trajectory_guide_uri"] = self.file_uri
            shot_req.metadata["pose_conditioning_uri"] = self.file_uri
        elif self.role == EducationalAssetRole.LEVEL_4_SURFACE_TEXTURE:
            shot_req.metadata["surface_texture_uri"] = self.file_uri
        elif self.role == EducationalAssetRole.PICTURE_IN_PICTURE_OVERLAY:
            shot_req.metadata["pip_overlay"] = {
                "uri": self.file_uri,
                "bounds": self.spatial_bounds or [0.65, 0.05, 0.95, 0.35],
                "media_type": self.media_type,
            }
        elif self.role == EducationalAssetRole.BACKGROUND_PROJECTION_PLATE:
            shot_req.metadata["projection_plate"] = {
                "uri": self.file_uri,
                "bounds": self.spatial_bounds or [0.10, 0.10, 0.90, 0.90],
                "media_type": self.media_type,
            }
        elif self.role == EducationalAssetRole.CHALKBOARD_HUD:
            shot_req.metadata["chalkboard_hud"] = {
                "uri": self.file_uri,
                "bounds": self.spatial_bounds or [0.05, 0.12, 0.95, 0.88],
                "media_type": self.media_type,
            }

        if self.caption and not shot_req.target_focal_intent:
            shot_req.target_focal_intent = f"Technical demonstration of {self.caption}"

        return shot_req


class HybridRenderMode(str, Enum):
    """Specifies engine allocation and compositing mode for short production."""
    PURE_MANIM_2D = "PURE_MANIM_2D"                  # 100% 2D Manim CE programmatic vector graphics
    PURE_AETHER_3D = "PURE_AETHER_3D"                # 100% 3D Aether generative virtual studio
    HYBRID_COMPOSITE = "HYBRID_COMPOSITE"            # 3D cinematic plate with 2D Manim HUD overlay
    DUAL_STREAM_PIP = "DUAL_STREAM_PIP"              # Picture-in-picture concurrent dual stream
    SEQUENTIAL_ALTERNATING = "SEQUENTIAL_ALTERNATING"# Alternating beats between 2D and 3D engines

    def __str__(self) -> str:
        return self.value


class DualEnginePipelineConfig(BaseModel):
    """Configuration for orchestrating dual-engine (Manim + Aether) pipelines."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    default_mode: HybridRenderMode = Field(
        HybridRenderMode.HYBRID_COMPOSITE,
        description="Default rendering mode across all beats",
    )
    beat_modes: Dict[int, HybridRenderMode] = Field(
        default_factory=dict,
        description="Per-beat override rendering mode (1-indexed beat numbers)",
    )
    overlay_alpha: float = Field(0.9, ge=0.0, le=1.0, description="Opacity of 2D overlay when composited")
    hud_safe_bounds: List[float] = Field(
        default_factory=lambda: [0.05, 0.12, 0.95, 0.88],
        description="Normalized safe margin [x1, y1, x2, y2] for 9:16 vertical video",
    )
    audio_master: str = Field(
        "hybrid_ducking",
        description="Master audio provider: 'manim_tts', 'aether_foley', 'hybrid_ducking', or 'none'",
    )
    blend_mode: str = Field(
        "screen",
        description="Compositing blend mode: 'screen', 'over', 'add', 'none'",
    )
    resolution: str = Field("1440x2560", description="Master canvas resolution")
    framerate: int = Field(60, ge=24, le=120, description="Master canvas framerate (FPS)")

    @field_validator("hud_safe_bounds")
    @classmethod
    def _validate_hud_safe_bounds(cls, v: List[float]) -> List[float]:
        if len(v) != 4:
            raise ValueError(f"hud_safe_bounds must contain exactly 4 floats [x1, y1, x2, y2], got {len(v)}")
        for coord in v:
            if not (0.0 <= coord <= 1.0):
                raise ValueError(f"hud_safe_bounds coordinates must be in [0.0, 1.0], got {coord}")
        if v[0] >= v[2] or v[1] >= v[3]:
            raise ValueError(
                f"hud_safe_bounds must define positive area with x1 < x2 and y1 < y2, got {v}"
            )
        return v

    @field_validator("audio_master")
    @classmethod
    def _validate_audio_master(cls, v: str) -> str:
        allowed = {"manim_tts", "aether_foley", "hybrid_ducking", "none"}
        if v.lower() not in allowed:
            raise ValueError(f"audio_master must be one of {allowed}, got '{v}'")
        return v.lower()

    @field_validator("blend_mode")
    @classmethod
    def _validate_blend_mode(cls, v: str) -> str:
        allowed = {"screen", "over", "add", "none"}
        if v.lower() not in allowed:
            raise ValueError(f"blend_mode must be one of {allowed}, got '{v}'")
        return v.lower()

    @field_validator("beat_modes")
    @classmethod
    def _validate_beat_modes(cls, v: Dict[int, HybridRenderMode]) -> Dict[int, HybridRenderMode]:
        for k in v.keys():
            if not isinstance(k, int) or k < 1:
                raise ValueError(f"beat_modes keys must be positive integers (>= 1), got {k}")
        return v

    def get_beat_mode(self, beat_id: int) -> HybridRenderMode:
        """Returns the render mode for a specific beat, falling back to default."""
        return self.beat_modes.get(beat_id, self.default_mode)

    def is_hybrid(self) -> bool:
        """Returns True if any beat or default uses a composite or mixed mode."""
        if self.default_mode in (
            HybridRenderMode.HYBRID_COMPOSITE,
            HybridRenderMode.DUAL_STREAM_PIP,
            HybridRenderMode.SEQUENTIAL_ALTERNATING,
        ):
            return True
        return any(
            mode in (
                HybridRenderMode.HYBRID_COMPOSITE,
                HybridRenderMode.DUAL_STREAM_PIP,
                HybridRenderMode.SEQUENTIAL_ALTERNATING,
            )
            for mode in self.beat_modes.values()
        )


class ScriptToFilmSceneAdapter:
    """Adapts The Model Verse educational script specifications into Aether film scenes."""

    # Canonical mapping from 6-beat educational structure to cinematic camera, locations, and complexity
    BEAT_CINEMATIC_MAPPING: Dict[int, Dict[str, Any]] = {
        1: {  # Hook Beat
            "scene_id": "SC_001_HOOK",
            "narrative_label": "The Paradox / Opening Hook",
            "location": "Frontier Research Lab / Hardware Datacenter",
            "lighting": "Dramatic volumetric blue rim lighting with flickering terminal displays",
            "camera_movement": "dolly_in",
            "complexity_level": ComplexityLevel.TWOD_TRAJECTORY_POSE,
            "focal_intent": "Establishing tech protagonist in research lab",
            "emotional_beat": "intense curiosity and urgency",
        },
        2: {  # Bottleneck / Problem Beat
            "scene_id": "SC_002_BOTTLENECK",
            "narrative_label": "The Core Bottleneck / Failure Mode",
            "location": "High-Tech Cleanroom / Silicon Foundry",
            "lighting": "High-contrast warning amber emergency strobe",
            "camera_movement": "orbit",
            "complexity_level": ComplexityLevel.THREED_BLOCKING,
            "focal_intent": "Focus on hardware bottleneck and thermal limits",
            "emotional_beat": "analytical tension and technical barrier",
        },
        3: {  # Core Mechanism / Paper Figure Beat
            "scene_id": "SC_003_MECHANISM",
            "narrative_label": "The Breakthrough Mechanism / Architecture",
            "location": "Holographic Projection Stage / Virtual Whiteboard",
            "lighting": "Clean neutral studio illumination with neon cyan holographic highlights",
            "camera_movement": "pan",
            "complexity_level": ComplexityLevel.REFERENCE_IMAGE,
            "focal_intent": "Holographic schematic of novel neural architecture",
            "emotional_beat": "breakthrough revelation and structural clarity",
        },
        4: {  # Implementation / Code Beat
            "scene_id": "SC_004_CODE",
            "narrative_label": "Implementation / Code Execution",
            "location": "Autonomous Robotics Pod / Supercomputer Terminal",
            "lighting": "Subdued carbon ambiance with bright phosphor code reflections",
            "camera_movement": "static",
            "complexity_level": ComplexityLevel.KEYFRAMES_INTERPOLATION,
            "focal_intent": "Terminal display showing kernel execution sweep",
            "emotional_beat": "pragmatic precision and code mastery",
        },
        5: {  # Benchmark / Showdown Beat
            "scene_id": "SC_005_SHOWDOWN",
            "narrative_label": "Empirical Showdown / Pareto Frontier",
            "location": "Benchmark Arena / Virtual Testing Range",
            "lighting": "Vibrant split arena illumination (mint green vs coral red)",
            "camera_movement": "crane",
            "complexity_level": ComplexityLevel.THREED_BLOCKING,
            "focal_intent": "Split comparison arena with dynamic radar charts",
            "emotional_beat": "competitive showdown and decisive victory",
        },
        6: {  # Outro / Payoff Beat
            "scene_id": "SC_006_OUTRO",
            "narrative_label": "Future Horizon / Final Payoff",
            "location": "Infinite Horizon / Minimalist Architectural Gallery",
            "lighting": "Golden hour soft volumetric gradient",
            "camera_movement": "dolly_out",
            "complexity_level": ComplexityLevel.PROMPT_ONLY,
            "focal_intent": "Wide contemplative vista framing future implications",
            "emotional_beat": "inspirational conclusion and open frontier",
        },
    }

    @classmethod
    def extract_conditioning_assets(
        cls,
        spec: Union[Dict[str, Any], Any],
        prefer_vector: bool = False,
    ) -> List[EducationalAssetConditioningPackage]:
        """Extracts conditioning packages from a VideoSpec or dictionary."""
        packages: List[EducationalAssetConditioningPackage] = []

        raw_dict = spec if isinstance(spec, dict) else (
            spec.model_dump(mode="json") if hasattr(spec, "model_dump") else getattr(spec, "__dict__", {})
        )

        # Look in paper_figures top-level
        figures = raw_dict.get("paper_figures") or []
        if not figures and isinstance(raw_dict.get("metadata"), dict):
            figures = raw_dict["metadata"].get("paper_figures") or []

        for i, fig in enumerate(figures):
            if isinstance(fig, dict):
                # Beat 3 is typically the mechanism / paper figure beat
                pkg = EducationalAssetConditioningPackage.from_figure_dict(
                    fig=fig,
                    beat_id=3 if i == 0 else None,
                    role=(
                        EducationalAssetRole.LEVEL_1_REFERENCE_IMAGE
                        if i == 0
                        else EducationalAssetRole.PICTURE_IN_PICTURE_OVERLAY
                    ),
                    prefer_vector=prefer_vector,
                )
                packages.append(pkg)

        # Also inspect individual beats for custom visual blueprints / assets
        beats = raw_dict.get("beats") or []
        for beat in beats:
            b_dict = beat if isinstance(beat, dict) else (
                beat.model_dump(mode="json") if hasattr(beat, "model_dump") else getattr(beat, "__dict__", {})
            )
            beat_id = b_dict.get("beat_id")
            bp = b_dict.get("visual_blueprint")
            if isinstance(bp, dict):
                params = bp.get("params") or {}
                svg_p = params.get("svg_path")
                img_p = params.get("image_path")
                if svg_p or img_p:
                    fig_dict = {
                        "asset_id": f"beat_{beat_id}_blueprint",
                        "svg_path": svg_p,
                        "image_path": img_p,
                        "caption": params.get("caption", b_dict.get("visual_focus")),
                    }
                    pkg = EducationalAssetConditioningPackage.from_figure_dict(
                        fig=fig_dict,
                        beat_id=beat_id,
                        role=EducationalAssetRole.LEVEL_1_REFERENCE_IMAGE,
                        prefer_vector=prefer_vector,
                    )
                    packages.append(pkg)

        return packages

    @classmethod
    def _coerce_beat_id(cls, raw_id: Any, fallback_index: Optional[int] = None) -> int:
        """Safely coerces beat_id to a positive integer, falling back to index or 1."""
        if raw_id is not None:
            if isinstance(raw_id, int):
                return max(1, raw_id)
            if isinstance(raw_id, str):
                clean_str = raw_id.strip()
                if clean_str.isdigit():
                    return max(1, int(clean_str))
                try:
                    val = float(clean_str)
                    if val.is_integer():
                        return max(1, int(val))
                except (ValueError, TypeError):
                    pass
        if fallback_index is not None:
            if isinstance(fallback_index, int):
                return max(1, fallback_index)
            if isinstance(fallback_index, str) and fallback_index.strip().isdigit():
                return max(1, int(fallback_index.strip()))
        return 1

    @classmethod
    def convert_beat_to_shot(
        cls,
        beat: Union[Dict[str, Any], Any],
        spec_title: str = "",
        beat_index: Optional[int] = None,
        conditioning_assets: Optional[List[EducationalAssetConditioningPackage]] = None,
        aspect_ratio: str = "9:16",
    ) -> ShotRequirement:
        """Converts an individual BeatSpec or dictionary into an Aether ShotRequirement."""
        b_dict = beat if isinstance(beat, dict) else (
            beat.model_dump(mode="json") if hasattr(beat, "model_dump") else getattr(beat, "__dict__", {})
        )

        beat_id = cls._coerce_beat_id(b_dict.get("beat_id"), fallback_index=beat_index or 1)
        cfg = cls.BEAT_CINEMATIC_MAPPING.get(beat_id, {
            "scene_id": f"SC_{beat_id:03d}",
            "location": "Virtual Studio Stage",
            "lighting": "Balanced cinematic illumination",
            "camera_movement": "pan",
            "complexity_level": ComplexityLevel.TWOD_TRAJECTORY_POSE,
            "focal_intent": "General overview",
            "emotional_beat": "focused inquiry",
        })

        spoken_text = b_dict.get("text", "")
        visual_focus = b_dict.get("visual_focus", "")
        camera_action = b_dict.get("camera_action") or cfg.get("camera_movement", "pan")

        # Duration handling
        exp_dur = b_dict.get("expected_duration")
        if exp_dur is not None:
            try:
                target_duration = max(1.0, float(exp_dur))
            except (ValueError, TypeError):
                target_duration = 5.0
        else:
            target_duration = 5.0

        audio_req = AudioRequirement(
            dialogue=bool(spoken_text),
            dialogue_transcript=spoken_text if spoken_text else None,
            foley=True,
            foley_cues=["ambient_hum", "tech_whoosh"],
            score=True,
            score_mood="tense_intellectual_synth",
        )

        narrative = f"{visual_focus}."
        if spoken_text:
            narrative += f" Spoken voiceover: \"{spoken_text}\""

        shot_req = ShotRequirement(
            shot_id=f"SHOT_{beat_id:03d}",
            target_duration=target_duration,
            aspect_ratio=aspect_ratio,
            resolution="1080p",
            audio=audio_req,
            emotional_beat=cfg.get("emotional_beat"),
            target_focal_intent=cfg.get("focal_intent"),
            camera_movement=camera_action,
            continuity_critical=(beat_id > 1),
            metadata={
                "source_beat_id": beat_id,
                "visual_focus": visual_focus,
                "topic": spec_title,
                "narrative_description": narrative,
            },
        )

        # Apply matching conditioning assets if available
        if conditioning_assets:
            for asset in conditioning_assets:
                if asset.source_beat_id == beat_id:
                    asset.apply_to_shot(shot_req)

        return shot_req

    @classmethod
    def convert_beat_to_film_scene(
        cls,
        beat: Union[Dict[str, Any], Any],
        spec_title: str = "",
        beat_index: Optional[int] = None,
        conditioning_assets: Optional[List[EducationalAssetConditioningPackage]] = None,
        aspect_ratio: str = "9:16",
    ) -> FilmScene:
        """Converts an individual BeatSpec or dictionary into an Aether FilmScene."""
        b_dict = beat if isinstance(beat, dict) else (
            beat.model_dump(mode="json") if hasattr(beat, "model_dump") else getattr(beat, "__dict__", {})
        )

        beat_id = cls._coerce_beat_id(b_dict.get("beat_id"), fallback_index=beat_index or 1)
        cfg = cls.BEAT_CINEMATIC_MAPPING.get(beat_id, {
            "scene_id": f"SC_{beat_id:03d}",
            "narrative_label": f"Beat {beat_id}",
            "location": "Virtual Studio Stage",
            "lighting": "Balanced cinematic illumination",
            "camera_movement": "pan",
            "complexity_level": ComplexityLevel.TWOD_TRAJECTORY_POSE,
            "focal_intent": "General overview",
            "emotional_beat": "focused inquiry",
        })

        shot = cls.convert_beat_to_shot(
            beat=b_dict,
            spec_title=spec_title,
            beat_index=beat_id,
            conditioning_assets=conditioning_assets,
            aspect_ratio=aspect_ratio,
        )

        visual_focus = b_dict.get("visual_focus", "")
        narrative_beat = f"Beat {beat_id} ({cfg.get('narrative_label', 'Action')}): {visual_focus}"

        # Resolve explicit complexity level from beat dict or conditioning asset
        explicit_complexity = b_dict.get("complexity_level")
        if explicit_complexity is None and conditioning_assets:
            for asset in conditioning_assets:
                if asset.source_beat_id == beat_id and asset.complexity_level_target is not None:
                    explicit_complexity = asset.complexity_level_target
                    break

        if explicit_complexity is not None:
            try:
                complexity_val = int(explicit_complexity)
            except (ValueError, TypeError):
                complexity_val = int(cfg.get("complexity_level", ComplexityLevel.TWOD_TRAJECTORY_POSE))
        else:
            complexity_val = int(cfg.get("complexity_level", ComplexityLevel.TWOD_TRAJECTORY_POSE))

        return FilmScene(
            scene_id=cfg["scene_id"],
            narrative_beat=narrative_beat,
            location=cfg["location"],
            environment_parameters={
                "lighting": cfg["lighting"],
                "topic": spec_title,
                "beat_id": beat_id,
            },
            characters=[{"character_id": "lead_researcher", "name": "Principal Investigator"}],
            props=[{"prop_id": "holographic_console", "name": "Holographic Neural Console"}],
            shot_list_requirements=[shot],
            duration=shot.target_duration,
            metadata={
                "source_beat_id": beat_id,
                "complexity_level": complexity_val,
            },
        )

    @classmethod
    def convert_spec_to_scenes(
        cls,
        spec: Union[Dict[str, Any], Any],
        conditioning_assets: Optional[List[EducationalAssetConditioningPackage]] = None,
        aspect_ratio: str = "9:16",
    ) -> List[FilmScene]:
        """Converts all beats in a VideoSpec into structured FilmScenes."""
        raw_dict = spec if isinstance(spec, dict) else (
            spec.model_dump(mode="json") if hasattr(spec, "model_dump") else getattr(spec, "__dict__", {})
        )
        spec_title = raw_dict.get("title", "Untitled Technical Short")
        beats = raw_dict.get("beats", [])

        # Auto-extract conditioning assets if not explicitly passed
        if conditioning_assets is None:
            conditioning_assets = cls.extract_conditioning_assets(raw_dict)

        scenes: List[FilmScene] = []
        for i, beat in enumerate(beats, start=1):
            scene = cls.convert_beat_to_film_scene(
                beat=beat,
                spec_title=spec_title,
                beat_index=i,
                conditioning_assets=conditioning_assets,
                aspect_ratio=aspect_ratio,
            )
            scenes.append(scene)

        return scenes

    @classmethod
    def convert_spec_to_brief(
        cls,
        spec: Union[Dict[str, Any], Any],
        visual_style: str = "photorealistic cinematic tech documentary",
        target_models: Optional[List[str]] = None,
        conditioning_assets: Optional[List[EducationalAssetConditioningPackage]] = None,
        target_duration: Optional[float] = None,
        budget_limit: float = 100.0,
        speculative_draft: bool = True,
        aspect_ratio: str = "9:16",
    ) -> DirectorProductionBrief:
        """Converts a VideoSpec or dictionary into an executive DirectorProductionBrief."""
        raw_dict = spec if isinstance(spec, dict) else (
            spec.model_dump(mode="json") if hasattr(spec, "model_dump") else getattr(spec, "__dict__", {})
        )

        title = raw_dict.get("title", "Untitled Technical Short")
        hook_tag = raw_dict.get("hook_tag", "")
        category = raw_dict.get("category", "architecture_breakdown")
        if hasattr(category, "value"):
            cat_val = category.value
        else:
            cat_val = str(category)

        # Extract conditioning assets if not provided
        if conditioning_assets is None:
            conditioning_assets = cls.extract_conditioning_assets(raw_dict)

        scenes = cls.convert_spec_to_scenes(
            spec=raw_dict,
            conditioning_assets=conditioning_assets,
            aspect_ratio=aspect_ratio,
        )

        calc_duration = sum(s.duration for s in scenes)
        effective_duration = float(target_duration or (calc_duration if calc_duration > 0 else 30.0))

        logline = (
            f"Autonomous cinematic documentary on '{title}' ({cat_val}). "
            f"Hook: {hook_tag}. Translating technical paper mechanics into high-stakes cinematic storytelling."
        )

        return DirectorProductionBrief(
            title=title,
            logline=logline,
            target_duration=effective_duration,
            aspect_ratio=aspect_ratio,
            visual_style=visual_style,
            target_models=target_models or ["veo_3_1", "kling_3_0", "runway_gen_4_5", "comfyui_cogvideox"],
            budget_limit=budget_limit,
            speculative_draft=speculative_draft,
            scenes=scenes,
            metadata={
                "source_spec_id": raw_dict.get("id", "spec_001"),
                "category": cat_val,
                "hook_tag": hook_tag,
                "conditioning_assets_count": len(conditioning_assets),
                "is_adapted_educational_short": True,
            },
        )

    @classmethod
    def convert_brief_to_spec_outline(
        cls,
        brief: Union[DirectorProductionBrief, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Reverse converts a DirectorProductionBrief into a Model Verse VideoSpec-compatible outline."""
        b_dict = brief if isinstance(brief, dict) else (
            brief.model_dump(mode="json") if hasattr(brief, "model_dump") else getattr(brief, "__dict__", {})
        )

        title = b_dict.get("title", "Cinematic Short")
        scenes = b_dict.get("scenes", [])
        beats: List[Dict[str, Any]] = []

        for i, sc in enumerate(scenes, start=1):
            sc_dict = sc if isinstance(sc, dict) else getattr(sc, "__dict__", {})
            shots = sc_dict.get("shot_list_requirements", [])
            primary_shot = shots[0] if shots else {}
            if not isinstance(primary_shot, dict):
                primary_shot = primary_shot.model_dump(mode="json") if hasattr(primary_shot, "model_dump") else {}

            audio_data = primary_shot.get("audio", {})
            if hasattr(audio_data, "model_dump"):
                audio_data = audio_data.model_dump(mode="json")
            elif not isinstance(audio_data, dict):
                audio_data = getattr(audio_data, "__dict__", {})

            spoken_text = audio_data.get("dialogue_transcript") or ""
            visual_focus = primary_shot.get("target_focal_intent") or sc_dict.get("narrative_beat", f"Scene {i}")

            beats.append({
                "beat_id": i,
                "text": spoken_text,
                "visual_focus": visual_focus,
                "camera_action": primary_shot.get("camera_movement", "pan"),
                "expected_duration": float(sc_dict.get("duration", 5.0)),
            })

        meta = b_dict.get("metadata", {})
        cat = meta.get("category", "architecture_breakdown")
        hook_tag = meta.get("hook_tag", "AI Breakthrough")

        return {
            "id": meta.get("source_spec_id", f"spec_{Path(title).stem}"),
            "title": title,
            "category": cat,
            "hook_tag": hook_tag,
            "beats": beats,
            "sfx_cues": [],
            "metadata": {
                "adapted_from_brief": True,
                "visual_style": b_dict.get("visual_style"),
            },
        }
