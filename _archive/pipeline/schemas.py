"""
The Model Verse — Pydantic Schemas for Video Specifications & Categories
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class VideoCategory(str, Enum):
    ARCHITECTURE_BREAKDOWN = "architecture_breakdown"
    MODEL_SHOWDOWN = "model_showdown"
    MECHANISM_DEEPDIVE = "mechanism_deepdive"
    BENCHMARK_NEWS = "benchmark_news"

class SFXCue(BaseModel):
    timestamp: float = Field(..., description="Timestamp in seconds for the SFX")
    sound_type: str = Field(..., description="Type of procedural SFX: sub_impact, whoosh, click, laser, chime")
    volume: float = Field(default=0.4, description="Volume level between 0.0 and 1.0")

class BeatSpec(BaseModel):
    beat_id: int
    text: str
    visual_focus: str
    camera_action: Optional[str] = None
    expected_duration: Optional[float] = None

class VideoSpec(BaseModel):
    id: str
    title: str
    category: VideoCategory
    hook_tag: str
    beats: List[BeatSpec]
    sfx_cues: List[SFXCue] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
