"""Project Aether Autonomous Director Schemas.

Pydantic V2 schemas defining production briefs, film scenes, production status telemetry,
timeline ledgers, and mastered film artifacts for Project Aether v2 (Phase 10 / WBS 1.11).
"""

from __future__ import annotations

from enum import Enum
import math
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aether.compiler.schemas import ComplexityLevel, ProviderTarget, ShotRequirement
from aether.state.schemas import CharacterState, PropState, SceneState


class ProductionState(str, Enum):
    """Lifecycle states of the autonomous film production pipeline."""
    INITIALIZING = "INITIALIZING"
    WORLD_SETUP = "WORLD_SETUP"
    COMPILING_SHOTS = "COMPILING_SHOTS"
    RENDERING_AND_CRITIQUING = "RENDERING_AND_CRITIQUING"
    SURGICAL_REPAIRING = "SURGICAL_REPAIRING"
    MASTERING = "MASTERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    def __str__(self) -> str:
        return self.value


class FilmScene(BaseModel):
    """Cinematic scene structure defining location, atmosphere, characters, props, and shots."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    scene_id: str = Field(..., description="Unique scene identifier e.g. 'SC_001'")
    narrative_beat: str = Field("", description="Narrative beat / dramatic action summary")
    location: str = Field("stage", description="Physical location or setting descriptor")
    environment_parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Atmospheric parameters: lighting, particulates, weather, mood",
    )
    characters: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Characters present in the scene, states, wardrobe damage, held props",
    )
    props: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Physical props present in the scene, locations, ownership",
    )
    shot_list_requirements: List[ShotRequirement] = Field(
        default_factory=list,
        description="Structured shot requirements sequence for this scene",
    )
    duration: float = Field(0.0, ge=0.0, description="Estimated scene duration in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom scene metadata")

    @model_validator(mode="before")
    @classmethod
    def _normalize_scene(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            if "id" in d and "scene_id" not in d:
                d["scene_id"] = d["id"]
            if "beat" in d and "narrative_beat" not in d:
                d["narrative_beat"] = d["beat"]
            if "environment" in d and "environment_parameters" not in d:
                env = d["environment"]
                d["environment_parameters"] = env if isinstance(env, dict) else getattr(env, "__dict__", {})
            if "shots" in d and "shot_list_requirements" not in d:
                d["shot_list_requirements"] = d["shots"]

            # Normalize characters list
            if "characters" in d and isinstance(d["characters"], list):
                norm_chars = []
                for c in d["characters"]:
                    if isinstance(c, CharacterState):
                        norm_chars.append(c.model_dump(mode="json"))
                    elif isinstance(c, dict):
                        norm_chars.append(dict(c))
                    elif isinstance(c, str):
                        norm_chars.append({"character_id": c, "name": c.capitalize()})
                    else:
                        norm_chars.append(getattr(c, "__dict__", {}))
                d["characters"] = norm_chars

            # Normalize props list
            if "props" in d and isinstance(d["props"], list):
                norm_props = []
                for p in d["props"]:
                    if isinstance(p, PropState):
                        norm_props.append(p.model_dump(mode="json"))
                    elif isinstance(p, dict):
                        norm_props.append(dict(p))
                    elif isinstance(p, str):
                        norm_props.append({"prop_id": p, "name": p.replace("_", " ").title()})
                    else:
                        norm_props.append(getattr(p, "__dict__", {}))
                d["props"] = norm_props

            # Normalize shots list
            if "shot_list_requirements" in d and isinstance(d["shot_list_requirements"], list):
                norm_shots = []
                for s in d["shot_list_requirements"]:
                    if isinstance(s, ShotRequirement):
                        norm_shots.append(s)
                    elif isinstance(s, dict):
                        norm_shots.append(ShotRequirement(**s))
                    else:
                        norm_shots.append(s)
                d["shot_list_requirements"] = norm_shots

            return d
        return data


class DirectorProductionBrief(BaseModel):
    """Executive specification for full autonomous cinematic film generation."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    title: str = Field("Untitled Production", description="Title of cinematic project")
    logline: str = Field("", description="High-level narrative logline or premise prompt")
    target_duration: float = Field(30.0, gt=0.0, description="Target duration in seconds (e.g. 30s or 60s)")
    aspect_ratio: str = Field("9:16", description="Target aspect ratio: '9:16' (Shorts/Vertical) or '16:9' (Widescreen)")
    visual_style: str = Field("cinematic photorealistic", description="Overall visual style / aesthetic prompt modifier")
    target_models: List[str] = Field(
        default_factory=lambda: ["veo_3_1", "kling_3_0", "runway_gen_4_5", "comfyui_cogvideox"],
        description="Target model provider engines allowed during production",
    )
    max_repair_attempts: int = Field(2, ge=0, description="Maximum surgical repair attempts per shot before escalating")
    speculative_draft: bool = Field(True, description="Enable rapid 480p draft gating before full 1080p latent upscale")
    budget_limit: float = Field(100.0, ge=0.0, description="Maximum production budget limit in USD")
    scenes: List[FilmScene] = Field(default_factory=list, description="Explicit scenes list if pre-scripted")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom production tags and metadata")

    @model_validator(mode="before")
    @classmethod
    def _normalize_brief(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            # Duration parsing (e.g. "30s" -> 30.0)
            if "target_duration" in d:
                dur = d["target_duration"]
                if isinstance(dur, str):
                    clean_dur = dur.lower().replace("s", "").replace("sec", "").strip()
                    try:
                        d["target_duration"] = float(clean_dur)
                    except ValueError:
                        d["target_duration"] = 30.0
            elif "duration" in d:
                dur = d["duration"]
                if isinstance(dur, str):
                    clean_dur = dur.lower().replace("s", "").replace("sec", "").strip()
                    try:
                        d["target_duration"] = float(clean_dur)
                    except ValueError:
                        d["target_duration"] = 30.0
                else:
                    d["target_duration"] = float(dur)

            # Aspect ratio normalization
            if "aspect_ratio" in d:
                ar = str(d["aspect_ratio"]).strip().lower()
                if ar in ("9:16", "vertical", "portrait", "shorts", "reels", "tiktok"):
                    d["aspect_ratio"] = "9:16"
                elif ar in ("16:9", "horizontal", "landscape", "widescreen", "cinema"):
                    d["aspect_ratio"] = "16:9"
                elif ":" not in ar and "/" in ar:
                    d["aspect_ratio"] = ar.replace("/", ":")

            # Target models normalization
            if "target_models" in d:
                raw_models = d["target_models"]
                if isinstance(raw_models, (list, tuple)):
                    norm_models = []
                    for m in raw_models:
                        if isinstance(m, ProviderTarget):
                            norm_models.append(m.value)
                        elif hasattr(m, "value"):
                            norm_models.append(str(m.value))
                        else:
                            norm_models.append(str(m))
                    d["target_models"] = norm_models

            # Speculative draft aliases
            if "speculative" in d and "speculative_draft" not in d:
                d["speculative_draft"] = bool(d["speculative"])

            # Budget aliases
            if "budget" in d and "budget_limit" not in d:
                d["budget_limit"] = float(d["budget"])

            # Scenes normalization
            if "scenes" in d and isinstance(d["scenes"], list):
                norm_scenes = []
                for sc in d["scenes"]:
                    if isinstance(sc, FilmScene):
                        norm_scenes.append(sc)
                    elif isinstance(sc, dict):
                        norm_scenes.append(FilmScene(**sc))
                    else:
                        norm_scenes.append(sc)
                d["scenes"] = norm_scenes

            return d
        return data


class DirectorProductionStatus(BaseModel):
    """Runtime status telemetry and progress tracking for the autonomous studio."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    state: ProductionState = Field(ProductionState.INITIALIZING, description="Current production state enum")
    current_shot_index: int = Field(0, description="0-indexed currently active shot")
    total_shots: int = Field(0, description="Total planned shots count across all scenes")
    shots_passed_count: int = Field(0, description="Count of shots that passed council audit")
    repairs_performed_count: int = Field(0, description="Count of surgical repairs executed")
    estimated_total_cost: float = Field(0.0, description="Accrued production cost in USD")
    elapsed_time: float = Field(0.0, description="Elapsed wall-clock runtime in seconds")
    current_scene_id: Optional[str] = Field(None, description="Active scene identifier")
    current_shot_id: Optional[str] = Field(None, description="Active shot identifier")
    message: Optional[str] = Field(None, description="Status commentary or progress message")

    def transition_to(self, new_state: ProductionState, message: Optional[str] = None) -> None:
        """Transitions state and records progress commentary."""
        self.state = new_state
        if message:
            self.message = message


class ShotTimelineRecord(BaseModel):
    """Ledger entry recording an individual mastered shot within the film timeline."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    shot_id: str = Field(..., description="Identifier of the shot")
    scene_id: str = Field(..., description="Parent scene identifier")
    sequence_index: int = Field(0, description="Sequential shot order in timeline")
    duration: float = Field(5.0, description="Shot duration in seconds")
    provider: str = Field("veo_3_1", description="Generative provider model used")
    complexity_level: int = Field(0, description="Assigned complexity level (0-5)")
    video_uri: str = Field(..., description="Master video asset URI for this shot")
    audio_uri: Optional[str] = Field(None, description="Master audio asset URI for this shot")
    council_score: float = Field(10.0, description="Final council evaluation score")
    passed_hard_gates: bool = Field(True, description="True if all binary hard gates passed")
    repairs_count: int = Field(0, description="Number of surgical repairs performed on this shot")
    cost: float = Field(0.0, description="Estimated total generation and repair cost in USD")
    speculative_draft_passed: bool = Field(True, description="Whether rapid 480p draft passed gating")
    trace_episode_id: Optional[str] = Field(None, description="Associated Dream-RSI trace episode ID")
    continuity_passed: bool = Field(True, description="Whether transition continuity passed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Telemetry extension metadata")


class MasteredFilm(BaseModel):
    """The final completed cinematic film package assembled by AetherDirector."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    film_id: str = Field(..., description="Unique production film identifier e.g. 'FILM_AETHER_001'")
    title: str = Field(..., description="Film title")
    scenes_count: int = Field(..., description="Number of scenes in the film")
    total_shots_count: int = Field(..., description="Total number of mastered shots in timeline")
    duration_seconds: float = Field(..., description="Total film duration in seconds")
    master_video_artifact_uri: str = Field(..., description="URI or path to assembled master video artifact")
    master_audio_artifact_uri: str = Field(..., description="URI or path to assembled master audio artifact")
    total_production_cost: float = Field(..., description="Total accrued production cost in USD")
    production_timeline_ledger: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Chronological timeline ledger of all mastered shots",
    )
    dream_rsi_trace_episode_id: str = Field(..., description="Primary Dream-RSI trace episode ID")
    trace_episode_ids: List[str] = Field(
        default_factory=list,
        description="All trace episode IDs indexed into ReplaySimulatorPool",
    )
    continuity_report: Optional[Dict[str, Any]] = Field(
        None,
        description="Multi-shot continuity validation summary",
    )
    status: str = Field("COMPLETED", description="Final mastering status ('COMPLETED', 'FAILED', or 'STAGED')")
    created_at: float = Field(default_factory=time.time, description="Timestamp of production completion")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Mastering telemetry and metadata")

    def summary(self) -> str:
        """Formatted executive summary of the mastered film production."""
        lines = [
            f"=== Mastered Film: {self.title} ({self.film_id}) ===",
            f"Status: {self.status} | Duration: {self.duration_seconds:.1f}s | Scenes: {self.scenes_count} | Shots: {self.total_shots_count}",
            f"Master Video: {self.master_video_artifact_uri}",
            f"Master Audio: {self.master_audio_artifact_uri}",
            f"Total Production Cost: ${self.total_production_cost:.4f}",
            f"Dream-RSI Trace Episode ID: {self.dream_rsi_trace_episode_id}",
            f"Total Trace Episodes: {len(self.trace_episode_ids)}",
        ]
        if self.continuity_report:
            passed = self.continuity_report.get("all_transitions_valid", True)
            lines.append(f"Continuity Audit: {'PASSED' if passed else 'WARNINGS'}")
        return "\n".join(lines)
