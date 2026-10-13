"""
The Model Verse — Video Scene Graph Intermediate Representation (VSG-IR v1.0.0)
Authoritative declarative AST isolating narrative script state, acoustic word anchors,
spatial layout containers, and kinetic motion tracks from graphics rendering backends.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, Field, model_validator, computed_field


# =============================================================================
# 1. CORE ENUMERATIONS
# =============================================================================

class AspectRatio(str, Enum):
    RATIO_9_16 = "9:16"
    RATIO_16_9 = "16:9"
    RATIO_1_1 = "1:1"


class ThemeId(str, Enum):
    CYBER_CYAN = "cyber_cyan"
    NEON_VIOLET = "neon_violet"
    SOLAR_AMBER = "solar_amber"
    DARK_OBSIDIAN = "dark_obsidian"


class BandType(str, Enum):
    BAND_1_HEADER = "BAND_1_HEADER"
    BAND_2_THESIS = "BAND_2_THESIS"
    BAND_3_STAGE = "BAND_3_STAGE"
    BAND_4_CAPTIONS = "BAND_4_CAPTIONS"


class NodeType(str, Enum):
    METRIC_PILL = "MetricPill"
    GLASS_HUD_CARD = "GlassHUDCard"
    KINETIC_CAPTION_STREAM = "KineticCaptionStream"
    MOE_ROUTER_MATRIX = "MoERouterMatrix"
    ATTENTION_HEATMAP = "AttentionHeatmap"
    SYNTAX_CODE_BLOCK = "SyntaxCodeBlock"
    HORIZONTAL_RACE_BARS = "HorizontalRaceBars"
    VECTOR_FLOW_DIAGRAM = "VectorFlowDiagram"
    PAPER_FIGURE_EMBED = "PaperFigureEmbed"
    EQUATION_CHASSIS = "EquationChassis"
    COMPARISON_SPLIT = "ComparisonSplit"


class MotionType(str, Enum):
    EASE_OUT_EXPO = "EASE_OUT_EXPO"
    SPRING_DAMPED = "SPRING_DAMPED"
    FADE_DOWN = "FADE_DOWN"
    ZOOM_SNAP = "ZOOM_SNAP"
    SLIDE_UP = "SLIDE_UP"
    FADE_OUT = "FADE_OUT"


class LinkedSemanticAction(str, Enum):
    ENTER = "ENTER"
    HIGHLIGHT = "HIGHLIGHT"
    MORPH = "MORPH"
    EXIT = "EXIT"


# =============================================================================
# 2. CANVAS & AUDIO METADATA
# =============================================================================

class CanvasMetadata(BaseModel):
    width_px: int = Field(default=1080, description="Canvas width in pixels")
    height_px: int = Field(default=1920, description="Canvas height in pixels")
    fps: int = Field(default=60, description="Target frame rate")
    duration_seconds: float = Field(..., gt=0.0, description="Total video duration in seconds")
    total_frames: int = Field(..., gt=0, description="Total frame count at specified fps")

    @model_validator(mode="after")
    def validate_frames(self) -> "CanvasMetadata":
        expected = int(round(self.duration_seconds * self.fps))
        if self.total_frames <= 0 or abs(self.total_frames - expected) > 2:
            self.total_frames = expected
        return self


class AudioMetadata(BaseModel):
    master_voiceover_path: str = Field(..., description="Path or URI to master voice narration WAV/MP3")
    background_music_path: Optional[str] = Field(default=None, description="Path to background score")
    sample_rate_hz: int = Field(default=24000, description="Audio sampling rate in Hz")
    music_ducking_db: float = Field(default=-18.0, description="Audio ducking during spoken voice in dB")


class ProjectMetadata(BaseModel):
    project_id: str = Field(..., description="Unique alphanumeric identifier for the video short")
    title: str = Field(..., description="Human-readable project title")
    domain_taxonomy: str = Field(default="frontier_ai_architectures", description="Subject area taxonomy")
    aspect_ratio: AspectRatio = Field(default=AspectRatio.RATIO_9_16, description="Video aspect ratio")
    canvas: CanvasMetadata
    audio: AudioMetadata


# =============================================================================
# 3. DESIGN TOKENS & THEME SYSTEM
# =============================================================================

class ThemeColors(BaseModel):
    canvas_void: str = Field(default="#06080F", description="Deepest canvas background hex")
    surface_recessed: str = Field(default="#0B101D", description="Recessed container surface hex")
    surface_primary: str = Field(default="rgba(15, 23, 42, 0.82)", description="Standard glassmorphic card backdrop")
    surface_elevated: str = Field(default="rgba(30, 41, 59, 0.92)", description="Elevated card or active element surface")
    surface_border: str = Field(default="rgba(255, 255, 255, 0.08)", description="Translucent card border")
    text_primary: str = Field(default="#F8FAFC", description="Primary text color hex")
    text_secondary: str = Field(default="#94A3B8", description="Secondary label color hex")
    text_tertiary: str = Field(default="#64748B", description="Muted telemetry label hex")
    hero_accent: str = Field(default="#38BDF8", description="Hero visual accent hex")
    secondary_accent: str = Field(default="#10B981", description="Secondary accent hex")
    status_gain: str = Field(default="#10B981", description="Performance speedup/gain hex")
    status_loss: str = Field(default="#EF4444", description="Bottleneck/latency loss hex")
    status_warning: str = Field(default="#F59E0B", description="Resource caution hex")


class ThemeMaterials(BaseModel):
    card_blur_px: float = Field(default=24.0, description="CSS backdrop blur filter in pixels")
    border_radius_px: float = Field(default=20.0, description="Corner radius in pixels")
    border_width_px: float = Field(default=1.5, description="Border width in pixels")
    shadow_elevation: str = Field(
        default="0 24px 48px -12px rgba(0, 0, 0, 0.70), 0 0 32px rgba(56, 189, 248, 0.12)",
        description="Multi-layer drop shadow and specular glow"
    )
    vignette_intensity: float = Field(default=0.35, ge=0.0, le=1.0, description="Vignette darkening factor")


class ThemeTypography(BaseModel):
    font_family_display: str = Field(default="Inter, -apple-system, sans-serif", description="Headline font stack")
    font_family_code: str = Field(default="JetBrains Mono, monospace", description="Code and telemetry font stack")
    font_family_math: str = Field(default="KaTeX_Main, Latin Modern Math, serif", description="Mathematical equation font stack")
    open_type_features: str = Field(default="cv05 1, cv08 1, zero 1, tnum 1", description="OpenType feature flags")


class ThemeTokens(BaseModel):
    theme_id: ThemeId = Field(default=ThemeId.CYBER_CYAN)
    colors: ThemeColors = Field(default_factory=ThemeColors)
    materials: ThemeMaterials = Field(default_factory=ThemeMaterials)
    typography: ThemeTypography = Field(default_factory=ThemeTypography)


# Preset Themes
THEME_CYBER_CYAN = ThemeTokens(
    theme_id=ThemeId.CYBER_CYAN,
    colors=ThemeColors(
        canvas_void="#06080F",
        surface_recessed="#0B101D",
        surface_primary="rgba(15, 23, 42, 0.82)",
        surface_elevated="rgba(30, 41, 59, 0.92)",
        surface_border="rgba(255, 255, 255, 0.08)",
        hero_accent="#38BDF8",
        secondary_accent="#10B981"
    )
)

THEME_NEON_VIOLET = ThemeTokens(
    theme_id=ThemeId.NEON_VIOLET,
    colors=ThemeColors(
        canvas_void="#0A0612",
        surface_recessed="#140C24",
        surface_primary="rgba(24, 16, 44, 0.82)",
        surface_elevated="rgba(42, 28, 76, 0.92)",
        surface_border="rgba(168, 85, 247, 0.15)",
        hero_accent="#A855F7",
        secondary_accent="#EC4899"
    )
)

THEME_SOLAR_AMBER = ThemeTokens(
    theme_id=ThemeId.SOLAR_AMBER,
    colors=ThemeColors(
        canvas_void="#0D0904",
        surface_recessed="#1A1208",
        surface_primary="rgba(32, 22, 10, 0.82)",
        surface_elevated="rgba(56, 38, 18, 0.92)",
        surface_border="rgba(245, 158, 11, 0.15)",
        hero_accent="#F59E0B",
        secondary_accent="#F97316"
    )
)

THEME_DARK_OBSIDIAN = ThemeTokens(
    theme_id=ThemeId.DARK_OBSIDIAN,
    colors=ThemeColors(
        canvas_void="#08080A",
        surface_recessed="#111114",
        surface_primary="rgba(20, 20, 24, 0.85)",
        surface_elevated="rgba(34, 34, 40, 0.95)",
        surface_border="rgba(255, 255, 255, 0.06)",
        hero_accent="#60A5FA",
        secondary_accent="#94A3B8"
    )
)


# =============================================================================
# 4. SPATIAL BOUNDS & MOTION
# =============================================================================

class BoundingBoxPx(BaseModel):
    x_min_px: float = Field(..., description="Left coordinate in pixels")
    y_min_px: float = Field(..., description="Top coordinate in pixels")
    width_px: float = Field(..., gt=0.0, description="Width in pixels")
    height_px: float = Field(..., gt=0.0, description="Height in pixels")

    @computed_field
    @property
    def x_max_px(self) -> float:
        return self.x_min_px + self.width_px

    @computed_field
    @property
    def y_max_px(self) -> float:
        return self.y_min_px + self.height_px

    @computed_field
    @property
    def area_px(self) -> float:
        return self.width_px * self.height_px

    def intersects(self, other: "BoundingBoxPx") -> bool:
        """Determines if two Axis-Aligned Bounding Boxes overlap."""
        return not (
            self.x_max_px <= other.x_min_px or
            self.x_min_px >= other.x_max_px or
            self.y_max_px <= other.y_min_px or
            self.y_min_px >= other.y_max_px
        )

    def intersection_iou(self, other: "BoundingBoxPx") -> float:
        """Calculates Intersection over Union (IoU)."""
        x_left = max(self.x_min_px, other.x_min_px)
        y_top = max(self.y_min_px, other.y_min_px)
        x_right = min(self.x_max_px, other.x_max_px)
        y_bottom = min(self.y_max_px, other.y_max_px)

        if x_right <= x_left or y_bottom <= y_top:
            return 0.0

        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        union_area = self.area_px + other.area_px - intersection_area
        return intersection_area / union_area if union_area > 0 else 0.0


class EnterMotion(BaseModel):
    type: MotionType = Field(default=MotionType.EASE_OUT_EXPO)
    start_frame: int = Field(..., ge=0)
    duration_frames: int = Field(default=24, gt=0)
    easing: str = Field(default="cubic-bezier(0.16, 1, 0.3, 1)")
    spring_stiffness: Optional[float] = Field(default=140.0)
    spring_damping: Optional[float] = Field(default=16.0)


class FocalHighlight(BaseModel):
    trigger_frame: int = Field(..., ge=0)
    duration_frames: int = Field(default=30, gt=0)
    scale_multiplier: float = Field(default=1.08, ge=1.0, le=1.3)
    glow_hex: Optional[str] = Field(default=None)


class ExitMotion(BaseModel):
    type: MotionType = Field(default=MotionType.FADE_OUT)
    start_frame: int = Field(..., ge=0)
    duration_frames: int = Field(default=18, gt=0)


class MotionTrack(BaseModel):
    enter: EnterMotion
    focal_highlight: Optional[FocalHighlight] = None
    exit: Optional[ExitMotion] = None


# =============================================================================
# 5. SCENE GRAPH NODES & CONTAINERS
# =============================================================================

class VisualNode(BaseModel):
    id: str = Field(..., description="Unique node ID in the scene graph")
    node_type: NodeType = Field(..., description="Typological visual component type")
    props: Dict[str, Any] = Field(default_factory=dict, description="Component-specific properties")
    bounds: Optional[BoundingBoxPx] = Field(default=None, description="Computed or relaxed spatial bounds")
    motion_track: MotionTrack = Field(..., description="Kinematic motion and animation track")


class LayoutContainer(BaseModel):
    container_id: str = Field(..., description="Container identifier")
    band: BandType = Field(..., description="Universal vertical layout band")
    bounds: BoundingBoxPx = Field(..., description="Container boundary on the 1080x1920 canvas")
    nodes: List[VisualNode] = Field(default_factory=list, description="Visual nodes assigned to this container")


# =============================================================================
# 6. NARRATIVE BEATS & ACOUSTIC TIMING
# =============================================================================

class TimeRange(BaseModel):
    start_sec: float = Field(..., ge=0.0)
    end_sec: float = Field(..., gt=0.0)
    start_frame: int = Field(..., ge=0)
    end_frame: int = Field(..., gt=0)

    @model_validator(mode="after")
    def validate_duration(self) -> "TimeRange":
        if self.end_sec <= self.start_sec:
            raise ValueError(f"end_sec ({self.end_sec}) must be greater than start_sec ({self.start_sec})")
        if self.end_frame <= self.start_frame:
            raise ValueError(f"end_frame ({self.end_frame}) must be greater than start_frame ({self.start_frame})")
        return self


class NarrativeInfo(BaseModel):
    spoken_text: str = Field(..., description="Exact voiceover script segment")
    intent: str = Field(..., description="Pedagogical and dramatic intent of this beat")
    visual_metaphor: str = Field(..., description="Primary visual concept or metaphor")
    primary_focus_node_id: str = Field(..., description="ID of node holding primary viewer gaze")
    everyday_analogy: Optional[str] = Field(default=None, description="Optional relatable real-world comparison")


class AcousticAnchor(BaseModel):
    word: str = Field(..., description="Spoken word or phrase triggering visual synchronization")
    timestamp_sec: float = Field(..., ge=0.0, description="Exact timestamp from forced phoneme alignment")
    frame_trigger: int = Field(..., ge=0, description="Exact frame index to fire animation")
    linked_node_id: Optional[str] = Field(default=None, description="Node reacting to acoustic anchor")
    linked_action: Optional[LinkedSemanticAction] = Field(default=None, description="Action triggered on node")


class BeatAST(BaseModel):
    beat_id: int = Field(..., ge=1, le=12, description="1-indexed beat sequence number")
    time_range: TimeRange
    narrative: NarrativeInfo
    acoustic_anchors: List[AcousticAnchor] = Field(default_factory=list)
    layout_containers: List[LayoutContainer] = Field(default_factory=list)

    def get_node(self, node_id: str) -> Optional[VisualNode]:
        """Looks up a visual node across all layout containers in this beat."""
        for container in self.layout_containers:
            for node in container.nodes:
                if node.id == node_id:
                    return node
        return None

    def all_nodes(self) -> List[VisualNode]:
        """Returns flat list of all nodes in this beat."""
        nodes = []
        for c in self.layout_containers:
            nodes.extend(c.nodes)
        return nodes


# =============================================================================
# 7. ROOT VSG-IR AST SPECIFICATION
# =============================================================================

class VideoSceneGraphIR(BaseModel):
    """
    Authoritative Video Scene Graph Intermediate Representation (VSG-IR).
    Completely isolates script state from rendering backends.
    """
    version: Literal["1.0.0"] = Field(default="1.0.0", description="VSG-IR specification version")
    metadata: ProjectMetadata
    theme: ThemeTokens = Field(default_factory=lambda: THEME_CYBER_CYAN)
    beats: List[BeatAST] = Field(..., min_length=1, description="Sequential narrative beats")

    def get_beat(self, beat_id: int) -> Optional[BeatAST]:
        for b in self.beats:
            if b.beat_id == beat_id:
                return b
        return None

    def all_nodes(self) -> List[VisualNode]:
        result = []
        for b in self.beats:
            result.extend(b.all_nodes())
        return result

    @classmethod
    def from_json(cls, json_str: str) -> "VideoSceneGraphIR":
        return cls.model_validate_json(json_str)

    def to_json(self, indent: int = 2) -> str:
        return self.model_dump_json(indent=indent)

    @classmethod
    def export_json_schema(cls) -> Dict[str, Any]:
        return cls.model_json_schema()
