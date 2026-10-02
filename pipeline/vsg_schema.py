"""
The Model Verse — Declarative Visual Scene Graph (VSG) & SVO Scripting Schema
Defines the Pydantic v2 data models for:
- Subject-Verb-Object (SVO) semantic action triples
- Canvas Primitive Entity Registry
- Macro and Micro-Beat hierarchical timelines
- Forced-alignment acoustic anchors & procedural SFX cues
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, Field, model_validator


# =============================================================================
# ENUMERATIONS FOR VISUAL PRIMITIVES, ACTIONS & SFX
# =============================================================================

class VisualPrimitiveType(str, Enum):
    # Robotics & TAMP
    COUPLED_CANVAS = "coupled_canvas"
    KINEMATIC_ARM = "kinematic_arm"
    AST_TREE = "ast_tree"
    SANDBOX_POD = "sandbox_pod"
    
    # Deep Learning & Mechanistic Interpretability
    SAE_CONSTELLATION = "sae_constellation"
    ATTENTION_GRID = "attention_grid"
    MOE_LATTICE = "moe_lattice"
    CONTRASTIVE_SPHERE = "contrastive_sphere"
    DIFFUSION_FIELD = "diffusion_field"
    
    # Algorithmic Search
    SEARCH_TREE = "search_tree"
    BRANCH_BOUND = "branch_bound"
    
    # Quantitative & Comparative Metrics
    DUAL_METRIC = "dual_metric"
    RADIAL_METER = "radial_meter"
    LEADERBOARD = "leaderboard"
    STAT_COUNTER = "stat_counter"
    
    # Canvas Core & Notation
    MATH_FORMULA = "math_formula"
    CHALKBOARD_HEADER = "chalkboard_header"
    CHIP_BADGE = "chip_badge"


class ActionType(str, Enum):
    SPAWN = "spawn"                  # Instantiates an entity onto canvas (FadeIn, Create, Draw)
    DESPAWN = "despawn"              # Removes entity (FadeOut, Shrink)
    TRANSFORM = "transform"          # Geometric transformation (Morph, Scale, Rotate, Translate)
    TRAVERSE = "traverse"            # Graph/Tree path activation, token packet flow
    MUTATE_STATE = "mutate_state"    # Internal state update (prune node, update capacity bar, change color)
    HIGHLIGHT = "highlight"          # Focus effect (Circumscribe, Flash, Pulse, Glow)
    CAMERA_FOCUS = "camera_focus"    # Viewport shift or zoom


class EasingFunction(str, Enum):
    SMOOTH = "smooth"
    LINEAR = "linear"
    EASE_IN_OUT_CUBIC = "ease_in_out_cubic"
    EASE_OUT_EXPO = "ease_out_expo"
    SPRING = "spring"


class SFXType(str, Enum):
    WHOOSH = "whoosh"
    POP = "pop"
    CLICK = "click"
    GLASS_PING = "glass_ping"
    SUB_IMPACT = "sub_impact"
    LASER_DISPATCH = "laser_dispatch"
    LASER = "laser"
    CHIME = "chime"
    BRAND_CHIME = "brand_chime"
    SEVER_SLICE = "sever_slice"


class DomainTaxonomy(str, Enum):
    ROBOTICS_TAMP = "robotics_tamp"
    NEURAL_SAE = "neural_sae"
    NEURAL_ATTENTION = "neural_attention"
    NEURAL_MOE = "neural_moe"
    ALGORITHMIC_SEARCH = "algorithmic_search"
    QUANTITATIVE_BENCHMARK = "quantitative_benchmark"
    GENERAL_CS = "general_cs"


# =============================================================================
# AUDIO & PHONEMIC ALIGNMENT SCHEMAS
# =============================================================================

class WordAnchor(BaseModel):
    """Millisecond-accurate token alignment generated via WhisperX / CTC."""
    word: str
    t_start: float = Field(..., description="Start timestamp in seconds")
    t_end: float = Field(..., description="End timestamp in seconds")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class AudioSyncAnchor(BaseModel):
    """Binds an animation or visual action to speech execution."""
    trigger_word: str = Field(..., description="The spoken word that triggers the action")
    target_timestamp: float = Field(..., description="Exact timestamp in seconds")
    lead_in_seconds: float = Field(
        default=0.04, 
        description="Frame-ahead lead-in (30-60ms) so visual triggers before auditory transient"
    )

    @property
    def visual_trigger_time(self) -> float:
        return max(0.0, self.target_timestamp - self.lead_in_seconds)


class SFXCue(BaseModel):
    sound_type: SFXType
    timestamp: float = Field(..., description="Timestamp in seconds for audio mix")
    volume: float = Field(default=0.4, ge=0.0, le=1.0)
    linked_action_id: Optional[str] = Field(None, description="ID of the visual action triggering this SFX")


# =============================================================================
# ENTITY SPECIFICATIONS & PARAMETERS
# =============================================================================

class MathFormulaItem(BaseModel):
    """A mathematical equation rendered to SVG and actively bound to the canvas."""
    beat_id: int
    latex: str
    filename: str
    fontsize: int = 24
    color: str = "#38BDF8"
    term_annotations: List[Dict[str, str]] = Field(default_factory=list)
    target_entity_id: Optional[str] = Field(None, description="Visual entity bound to this formula")


class VisualEntity(BaseModel):
    """A persistent or spawned visual actor on the 3b1b chalkboard canvas."""
    entity_id: str = Field(..., description="Unique persistent identifier across scenes")
    entity_type: VisualPrimitiveType
    z_index: int = Field(default=10)
    initial_position: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0], description="[x, y, z] Manim coordinates")
    initial_scale: float = 1.0
    initial_opacity: float = 1.0
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Component-specific configuration kwargs")


# =============================================================================
# CONCRETE TRANSFORMATION ACTIONS (THE SVO ENGINE)
# =============================================================================

class SVOContext(BaseModel):
    """Semantic Role Labeling metadata linking natural language to animation."""
    subject: str = Field(..., description="Agent or entity performing the action (e.g. 'Coding Agent', 'Router')")
    action_verb: str = Field(..., description="Action verb (e.g. 'prunes', 'routes', 'projects', 'synthesizes')")
    direct_object: str = Field(..., description="Target entity/substructure (e.g. 'Kinematic Trajectory', 'Latent Space')")
    anchor_word: Optional[str] = Field(None, description="Word in voiceover text that initiates this action")
    semantic_role: Literal["agent_action", "state_transition", "causal_elimination", "metric_evaluation"] = "agent_action"


class ActionPayload(BaseModel):
    """Specific parameters executed during the visual action."""
    action_verb: str
    target_sub_elements: List[str] = Field(default_factory=list, description="IDs of sub-elements affected (e.g. node IDs)")
    custom_fx: Optional[str] = Field(None, description="Visual FX: red_slash, cyan_pulse, particle_burst, sever_slice")
    target_coordinates: Optional[List[float]] = None
    target_scale: Optional[float] = None
    target_color: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class VisualAction(BaseModel):
    """An atomic transformation event executed by the dynamic scene compiler."""
    action_id: str
    target_entity_id: str = Field(..., description="Entity being acted upon")
    action_type: ActionType
    svo_context: Optional[SVOContext] = None
    
    # Timing & Easing
    t_start: float = Field(..., description="Start time in seconds")
    duration: float = Field(default=1.0, gt=0.0, description="Animation run_time in seconds")
    easing: EasingFunction = EasingFunction.SMOOTH
    
    # Audio Link
    sync_anchor: Optional[AudioSyncAnchor] = None
    
    # Concrete transformation instruction
    payload: ActionPayload

    @property
    def t_end(self) -> float:
        return round(self.t_start + self.duration, 3)


# =============================================================================
# HIERARCHICAL STORYBOARD TIMELINE
# =============================================================================

class VisualMicroBeat(BaseModel):
    """Granular 1.5s - 3.5s visual beat consisting of atomic actions."""
    micro_beat_id: str
    t_start: float
    t_end: float
    description: str
    actions: List[VisualAction] = Field(default_factory=list)
    camera_movement: Optional[Dict[str, Any]] = None


class MacroBeat(BaseModel):
    """Major narrative arc segment (e.g. Beat 2: Monolithic Bottleneck)."""
    beat_id: int
    narrative_function: Literal["hook", "bottleneck", "core_innovation", "mechanism", "quantitative_proof", "outro"]
    script_text: str
    visual_focus: str
    audio_start: float = 0.0
    audio_end: float = 0.0
    word_timestamps: List[WordAnchor] = Field(default_factory=list)
    highlight_words: Dict[str, str] = Field(default_factory=dict)
    micro_beats: List[VisualMicroBeat] = Field(default_factory=list)


class VisualStoryboard(BaseModel):
    """
    Master declarative specification consumed by Visual Engine 2.0 DynamicCompositeScene.
    Replaces static card templates with living semantic manifolds.
    """
    storyboard_id: str
    project_title: str
    category: str = "dynamic_pedagogy"
    domain_taxonomy: DomainTaxonomy = DomainTaxonomy.GENERAL_CS
    aspect_ratio: Literal["9:16", "16:9"] = "9:16"
    resolution: List[int] = Field(default_factory=lambda: [1080, 1920])
    fps: int = 30
    total_duration: float = 45.0
    hook_tag: str = "FRONTIER AI ARCHITECTURE"
    
    # Audio Assets
    narration_audio_file: Optional[str] = None
    background_music_file: Optional[str] = None
    
    # Declarative Registry of Canvas Entities
    entity_registry: List[VisualEntity] = Field(default_factory=list)
    
    # Timeline & Mathematical Formulations
    macro_beats: List[MacroBeat] = Field(default_factory=list)
    math_formulas: List[MathFormulaItem] = Field(default_factory=list)
    sfx_timeline: List[SFXCue] = Field(default_factory=list)
    
    # Extended Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_storyboard(self) -> "VisualStoryboard":
        # Ensure at least one macro beat exists
        if not self.macro_beats:
            pass
        return self


# =============================================================================
# CONVERTER: LEGACY SPEC TO VISUAL SCENE GRAPH (VSG)
# =============================================================================

def convert_legacy_spec_to_vsg(spec: Dict[str, Any]) -> VisualStoryboard:
    """
    Transforms any legacy VideoSpec JSON (from Engine 1.0/1.2) into a full
    VisualStoryboard specification. Enables backwards compatibility without code duplication.
    """
    spec_id = spec.get("id", "untitled_spec")
    title = spec.get("title", "The Model Verse")
    category = spec.get("category", "dynamic_pedagogy")
    hook_tag = spec.get("hook_tag", "AI ARCHITECTURE")
    meta = spec.get("metadata", {})
    
    # Determine Domain Taxonomy from category & metadata
    metaphor = meta.get("visual_metaphor", "").lower()
    lower_title = title.lower()
    
    if any(k in lower_title or k in metaphor for k in ["tamp", "robot", "kinematic", "motion planning", "agentic planning"]):
        domain = DomainTaxonomy.ROBOTICS_TAMP
    elif any(k in lower_title or k in metaphor for k in ["sae", "sparse autoencoder", "dictionary", "latent"]):
        domain = DomainTaxonomy.NEURAL_SAE
    elif any(k in lower_title or k in metaphor for k in ["moe", "mixture of experts", "router", "expert"]):
        domain = DomainTaxonomy.NEURAL_MOE
    elif any(k in lower_title or k in metaphor for k in ["attention", "transformer", "kv cache", "flashattention"]):
        domain = DomainTaxonomy.NEURAL_ATTENTION
    elif any(k in lower_title or k in metaphor for k in ["search", "tree", "mcts", "branch and bound", "a*"]):
        domain = DomainTaxonomy.ALGORITHMIC_SEARCH
    elif category == "model_showdown" or category == "benchmark_news":
        domain = DomainTaxonomy.QUANTITATIVE_BENCHMARK
    else:
        domain = DomainTaxonomy.GENERAL_CS
        
    # Convert math formulas
    formulas = []
    for mf in spec.get("math_formulas", []):
        formulas.append(MathFormulaItem(
            beat_id=mf.get("beat_id", 1),
            latex=mf.get("latex", ""),
            filename=mf.get("filename", ""),
            fontsize=mf.get("fontsize", 24),
            color=mf.get("color", "#38BDF8"),
            term_annotations=mf.get("term_annotations", []),
            target_entity_id=f"math_formula_{mf.get('beat_id', 1)}"
        ))
        
    # Convert SFX cues
    sfx_list = []
    for sfx in spec.get("sfx_cues", []):
        st = sfx.get("sound_type", "whoosh")
        # Validate sfx type enum
        valid_st = SFXType.WHOOSH
        for val in SFXType:
            if val.value == st:
                valid_st = val
                break
        sfx_list.append(SFXCue(
            sound_type=valid_st,
            timestamp=float(sfx.get("timestamp", 0.0)),
            volume=float(sfx.get("volume", 0.4))
        ))
        
    # Build MacroBeats
    macro_beats = []
    narrative_functions = ["hook", "bottleneck", "core_innovation", "mechanism", "quantitative_proof", "outro"]
    
    for i, b in enumerate(spec.get("beats", [])):
        b_id = b.get("beat_id", i + 1)
        func = narrative_functions[min(i, len(narrative_functions) - 1)]
        macro_beats.append(MacroBeat(
            beat_id=b_id,
            narrative_function=func,
            script_text=b.get("text", ""),
            visual_focus=b.get("visual_focus", ""),
            highlight_words=b.get("highlight_words", {})
        ))
        
    # Build Entity Registry based on Domain Taxonomy
    entity_registry = []
    
    if domain == DomainTaxonomy.ROBOTICS_TAMP:
        entity_registry.append(VisualEntity(
            entity_id="coupled_canvas",
            entity_type=VisualPrimitiveType.COUPLED_CANVAS,
            z_index=10,
            parameters={"title": title}
        ))
        entity_registry.append(VisualEntity(
            entity_id="robot_arm",
            entity_type=VisualPrimitiveType.KINEMATIC_ARM,
            z_index=15,
            initial_position=[0.0, -2.4, 0.0],
            parameters={"link_lengths": [1.5, 1.2]}
        ))
        entity_registry.append(VisualEntity(
            entity_id="ast_tree",
            entity_type=VisualPrimitiveType.AST_TREE,
            z_index=12,
            initial_position=[0.0, 2.8, 0.0]
        ))
        entity_registry.append(VisualEntity(
            entity_id="sandbox_pod",
            entity_type=VisualPrimitiveType.SANDBOX_POD,
            z_index=14,
            initial_position=[0.0, -1.0, 0.0]
        ))
    elif domain == DomainTaxonomy.NEURAL_SAE:
        entity_registry.append(VisualEntity(
            entity_id="sae_constellation",
            entity_type=VisualPrimitiveType.SAE_CONSTELLATION,
            z_index=10,
            initial_position=[0.0, 0.0, 0.0]
        ))
    elif domain == DomainTaxonomy.NEURAL_MOE:
        entity_registry.append(VisualEntity(
            entity_id="moe_lattice",
            entity_type=VisualPrimitiveType.MOE_LATTICE,
            z_index=10,
            initial_position=[0.0, 0.2, 0.0]
        ))
    elif domain == DomainTaxonomy.NEURAL_ATTENTION:
        entity_registry.append(VisualEntity(
            entity_id="attention_grid",
            entity_type=VisualPrimitiveType.ATTENTION_GRID,
            z_index=10,
            initial_position=[0.0, 0.4, 0.0]
        ))
    elif domain == DomainTaxonomy.ALGORITHMIC_SEARCH:
        entity_registry.append(VisualEntity(
            entity_id="search_tree",
            entity_type=VisualPrimitiveType.SEARCH_TREE,
            z_index=10,
            initial_position=[0.0, 1.2, 0.0]
        ))
        entity_registry.append(VisualEntity(
            entity_id="branch_bound_laser",
            entity_type=VisualPrimitiveType.BRANCH_BOUND,
            z_index=12,
            initial_position=[0.0, 0.0, 0.0]
        ))
    else:
        # Default Quantitative / Comparative
        entity_registry.append(VisualEntity(
            entity_id="dual_metric_gauge",
            entity_type=VisualPrimitiveType.DUAL_METRIC,
            z_index=10,
            initial_position=[0.0, 0.0, 0.0],
            parameters={
                "model_a_name": meta.get("model_a", "Contender A"),
                "model_a_score": meta.get("model_a_stat", "95%"),
                "model_b_name": meta.get("model_b", "Baseline"),
                "model_b_score": meta.get("model_b_stat", "45%"),
                "delta_label": meta.get("efficiency_badge", "+50% Efficiency")
            }
        ))
        
    return VisualStoryboard(
        storyboard_id=f"storyboard_{spec_id}",
        project_title=title,
        category=category,
        domain_taxonomy=domain,
        hook_tag=hook_tag,
        entity_registry=entity_registry,
        macro_beats=macro_beats,
        math_formulas=formulas,
        sfx_timeline=sfx_list,
        metadata=meta
    )
