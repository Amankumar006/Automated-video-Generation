/**
 * The Model Verse — Video Scene Graph Intermediate Representation (VSG-IR v1.0.0)
 * Authoritative TypeScript Type Declarations for Next-Gen Remotion Broadcast Engine.
 */

export type AspectRatio = "9:16" | "16:9" | "1:1";

export type ThemeId = "cyber_cyan" | "neon_violet" | "solar_amber" | "dark_obsidian";

export type BandType =
  | "BAND_1_HEADER"
  | "BAND_2_THESIS"
  | "BAND_3_STAGE"
  | "BAND_4_CAPTIONS";

export type NodeType =
  | "MetricPill"
  | "GlassHUDCard"
  | "KineticCaptionStream"
  | "MoERouterMatrix"
  | "AttentionHeatmap"
  | "SyntaxCodeBlock"
  | "HorizontalRaceBars"
  | "VectorFlowDiagram"
  | "PaperFigureEmbed"
  | "EquationChassis"
  | "ComparisonSplit";

export type MotionType =
  | "EASE_OUT_EXPO"
  | "SPRING_DAMPED"
  | "FADE_DOWN"
  | "ZOOM_SNAP"
  | "SLIDE_UP"
  | "FADE_OUT";

export type LinkedSemanticAction = "ENTER" | "HIGHLIGHT" | "MORPH" | "EXIT";

export interface CanvasMetadata {
  width_px: number;
  height_px: number;
  fps: number;
  duration_seconds: number;
  total_frames: number;
}

export interface AudioMetadata {
  master_voiceover_path: string;
  background_music_path?: string;
  sample_rate_hz: number;
  music_ducking_db: number;
}

export interface ProjectMetadata {
  project_id: string;
  title: string;
  domain_taxonomy: string;
  aspect_ratio: AspectRatio;
  canvas: CanvasMetadata;
  audio: AudioMetadata;
}

export interface ThemeColors {
  canvas_void: string;
  surface_recessed: string;
  surface_primary: string;
  surface_elevated: string;
  surface_border: string;
  text_primary: string;
  text_secondary: string;
  text_tertiary: string;
  hero_accent: string;
  secondary_accent: string;
  status_gain: string;
  status_loss: string;
  status_warning: string;
}

export interface ThemeMaterials {
  card_blur_px: number;
  border_radius_px: number;
  border_width_px: number;
  shadow_elevation: string;
  vignette_intensity: number;
}

export interface ThemeTypography {
  font_family_display: string;
  font_family_code: string;
  font_family_math: string;
  open_type_features: string;
}

export interface ThemeTokens {
  theme_id: ThemeId;
  colors: ThemeColors;
  materials: ThemeMaterials;
  typography: ThemeTypography;
}

export interface BoundingBoxPx {
  x_min_px: number;
  y_min_px: number;
  width_px: number;
  height_px: number;
}

export interface EnterMotion {
  type: MotionType;
  start_frame: number;
  duration_frames: number;
  easing?: string;
  spring_stiffness?: number;
  spring_damping?: number;
}

export interface FocalHighlight {
  trigger_frame: number;
  duration_frames: number;
  scale_multiplier?: number;
  glow_hex?: string;
}

export interface ExitMotion {
  type: MotionType;
  start_frame: number;
  duration_frames: number;
}

export interface MotionTrack {
  enter: EnterMotion;
  focal_highlight?: FocalHighlight;
  exit?: ExitMotion;
}

export interface VisualNode {
  id: string;
  node_type: NodeType;
  props: Record<string, any>;
  bounds?: BoundingBoxPx;
  motion_track: MotionTrack;
}

export interface LayoutContainer {
  container_id: string;
  band: BandType;
  bounds: BoundingBoxPx;
  nodes: VisualNode[];
}

export interface TimeRange {
  start_sec: number;
  end_sec: number;
  start_frame: number;
  end_frame: number;
}

export interface NarrativeInfo {
  spoken_text: string;
  intent: string;
  visual_metaphor: string;
  primary_focus_node_id: string;
  everyday_analogy?: string;
}

export interface AcousticAnchor {
  word: string;
  timestamp_sec: number;
  frame_trigger: number;
  linked_node_id?: string;
  linked_action?: LinkedSemanticAction;
}

export interface BeatAST {
  beat_id: number;
  time_range: TimeRange;
  narrative: NarrativeInfo;
  acoustic_anchors: AcousticAnchor[];
  layout_containers: LayoutContainer[];
}

export interface VideoSceneGraphIR {
  version: "1.0.0";
  metadata: ProjectMetadata;
  theme: ThemeTokens;
  beats: BeatAST[];
}
