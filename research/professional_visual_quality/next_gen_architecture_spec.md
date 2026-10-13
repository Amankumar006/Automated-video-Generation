# Next-Generation Video Rendering & Automated Visual QA Architecture Specification
**Decoupled Scene Graph IR Blueprint, Pluggable Render Adapters, and Two-Tier Multimodal Gatekeeper Firewall**

**Author**: Systems Architecture & Visual Engine Working Group (`worker_m3_m4`)  
**Target Platform**: Automated High-Retention Vertical Tech Media Pipeline (`themodelverse-shorts`)  
**Target Resolution**: 1080 × 1920 (9:16 Vertical Video) @ 60 FPS (3,600 frames / 60-second broadcast short)  
**Date**: October 2026  
**Status**: Authoritative Technical Architecture & System Specification  

---

## Executive Overview & Architectural Mandate

The historical architecture of `themodelverse-shorts` suffered from structural coupling between the narrative generation logic (`pipeline/script_generator.py`, `pipeline/visual_director.py`) and the underlying rendering technology (`manim_engine/scenes/script_driven_scene.py`). This coupling introduced severe production deficiencies:
1. **Engine Lock-In**: Narrative beats and visual blueprints were entangled with Manim's imperative `Mobject` and `MovingCameraScene` API calls, preventing adoption of modern web rendering engines.
2. **Brittle Layout Math**: Bounding box placement relied on hardcoded absolute coordinate offsets (`y = -2.6` for formulas, `y = -3.85` for subtitles) that lacked container flow awareness, producing text collisions and platform safe-zone breaches.
3. **Post-Hoc Informational QA**: Visual QA ran after the video was already encoded and muxed. Under API quota exhaustion, the critic defaulted to synthetic dummy passes (`overall_score = 8.8`), allowing defective frames to escape into production.

This specification establishes a **Decoupled, Multi-Backend Architecture** and an **Automated Two-Tier Visual QA Gatekeeper Firewall**:
- **Video Scene Graph Intermediate Representation (VSG-IR)**: A declarative, validated AST cleanly isolating narrative script state, acoustic word anchors, spatial containers, and motion tracks from graphics backends.
- **Pluggable Render Adapters**: Standardized adapter interfaces supporting **Remotion (Primary Broadcast Engine)**, **Motion Canvas (Auxiliary Math/Code Engine)**, and **Manim (Legacy Fallback Adapter)**.
- **Hot-Swappable Theme System**: Token-based styling enabling instant palette, material, and typographic transformations across four official broadcast themes.
- **Two-Tier Visual QA Gatekeeper**: A pre-render firewall combining **Tier 1 Deterministic CV Heuristics** (<50ms per frame, zero API cost) with a **Tier 2 Multimodal VLM Critic Council** (4 specialized critics enforcing a binary $\ge 8.5/10.0$ hard gate and closed-loop self-healing repair).

---

# SECTION 1: Decoupled Engine Architecture Blueprint

## 1.1 Separation of Narrative Script State from Graphics Rendering Backends

The core architectural invariant is the **Strict Decoupling Principle**:  
*The narrative script, semantic intents, acoustic timing anchors, and spatial relationships must exist as pure, backend-agnostic declarative data. No graphics library imports (`manim`, `remotion`, `three`, `canvas`) may exist upstream of the Render Adapter layer.*

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 NARRATIVE & ACOUSTIC LAYER                               │
│  arXiv Ingestion / LLM Script Generator ──► Kokoro / Sarvam / ElevenLabs TTS Narration  │
│                                                     │                                   │
│                                                     ▼                                   │
│                                      Forced Alignment (Whisper / CTC)                   │
│                                      Word-Level Timestamps & Phoneme Anchors            │
└─────────────────────────────────────────────┬───────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                VISUAL PLANNING & LAYOUT LAYER                           │
│  Visual Director: Semantic Metaphor Mapping (SVO Intent ──► Visual Primitive Blueprint) │
│  Layout Solver: Mobile 9:16 Safe-Zone Bounds Clamping & PBD Collision Pre-Relaxation   │
│  Theme Tokenizer: Injects Palette, Typography Scale, and Glassmorphic Material Tokens   │
└─────────────────────────────────────────────┬───────────────────────────────────────────┘
                                              │
                                              ▼
              ╔═════════════════════════════════════════════════════════════╗
              ║      VIDEO SCENE GRAPH INTERMEDIATE REPRESENTATION (VSG-IR) ║
              ║         Declarative JSON AST (vsg-ir-v1.schema.json)        ║
              ╚═════════════════════════════════════════════════════════════╝
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
      ┌──────────────────────────┐ ┌────────────────────┐ ┌──────────────────────────┐
      │ RemotionBroadcastAdapter │ │MotionCanvasAdapter │ │    ManimLegacyAdapter    │
      │ React 19 / CSS / ThreeJS │ │ TS Generators / 2D │ │ Python Mobject Pipeline  │
      └─────────────┬────────────┘ └──────────┬─────────┘ └─────────────┬────────────┘
                    │                         │                         │
                    └────────────────────┬────┴─────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                            FAST FRAME EXTRACTION ENGINE (<150ms)                        │
│             Headless Chromium CDP Frame Seek / WebCodecs Framebuffer Pipeline           │
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                         │
                                         ▼
              ╔═════════════════════════════════════════════════════════════╗
              ║        TWO-TIER AUTOMATED VISUAL QA GATEKEEPER FIREWALL     ║
              ║   Tier 1: Deterministic CV (<50ms) ──► Tier 2: VLM Council   ║
              ╚═════════════════════════════════════════════════════════════╝
                                         │
                         ┌───────────────┴───────────────┐
                      [ PASS ]                        [ FAIL ]
                         │                               │
                         ▼                               ▼
      ┌────────────────────────────────────┐ ┌───────────────────────────────────────┐
      │ Final Master Video Encoding        │ │ Circuit Breaker & Closed-Loop Repair  │
      │ NVENC / VideoToolbox / VAAPI       │ │ Auto Layout Patch Proposal Generator  │
      │ Hardware Line-Rate Muxing          │ │ (Re-evaluates VSG-IR AST; max 3 iter) │
      └────────────────────────────────────┘ └───────────────────────────────────────┘
```

---

## 1.2 Video Scene Graph Intermediate Representation (VSG-IR) Schema

The **VSG-IR** is an immutable, strictly validated declarative AST format. It fully parameterizes project metadata, canvas dimensions, visual design tokens, narrative beats, acoustic word anchors, hierarchical scene graph nodes, layout containers, and kinetic motion tracks.

### 1.2.1 Formal VSG-IR JSON Schema Specification (`vsg-ir-v1.schema.json`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "VideoSceneGraphIR",
  "description": "Authoritative Declarative AST for Next-Gen Video Synthesis",
  "type": "object",
  "required": ["version", "metadata", "theme", "beats"],
  "properties": {
    "version": { "type": "string", "enum": ["1.0.0"] },
    "metadata": {
      "type": "object",
      "required": ["project_id", "title", "canvas", "audio"],
      "properties": {
        "project_id": { "type": "string" },
        "title": { "type": "string" },
        "domain_taxonomy": { "type": "string" },
        "aspect_ratio": { "type": "string", "enum": ["9:16", "16:9", "1:1"] },
        "canvas": {
          "type": "object",
          "required": ["width_px", "height_px", "fps", "duration_seconds", "total_frames"],
          "properties": {
            "width_px": { "type": "integer", "default": 1080 },
            "height_px": { "type": "integer", "default": 1920 },
            "fps": { "type": "integer", "default": 60 },
            "duration_seconds": { "type": "number" },
            "total_frames": { "type": "integer" }
          }
        },
        "audio": {
          "type": "object",
          "required": ["master_voiceover_path", "sample_rate_hz"],
          "properties": {
            "master_voiceover_path": { "type": "string" },
            "background_music_path": { "type": "string" },
            "sample_rate_hz": { "type": "integer", "default": 24000 },
            "music_ducking_db": { "type": "number", "default": -18.0 }
          }
        }
      }
    },
    "theme": {
      "type": "object",
      "required": ["theme_id", "colors", "materials", "typography"],
      "properties": {
        "theme_id": { "type": "string", "enum": ["cyber_cyan", "neon_violet", "solar_amber", "dark_obsidian"] },
        "colors": {
          "type": "object",
          "required": ["canvas_void", "surface_primary", "surface_border", "text_primary", "text_secondary", "hero_accent", "secondary_accent"],
          "properties": {
            "canvas_void": { "type": "string" },
            "surface_recessed": { "type": "string" },
            "surface_primary": { "type": "string" },
            "surface_elevated": { "type": "string" },
            "surface_border": { "type": "string" },
            "text_primary": { "type": "string" },
            "text_secondary": { "type": "string" },
            "text_tertiary": { "type": "string" },
            "hero_accent": { "type": "string" },
            "secondary_accent": { "type": "string" },
            "status_gain": { "type": "string" },
            "status_loss": { "type": "string" },
            "status_warning": { "type": "string" }
          }
        },
        "materials": {
          "type": "object",
          "required": ["card_blur_px", "border_radius_px", "border_width_px", "shadow_elevation"],
          "properties": {
            "card_blur_px": { "type": "number", "default": 24 },
            "border_radius_px": { "type": "number", "default": 20 },
            "border_width_px": { "type": "number", "default": 1.5 },
            "shadow_elevation": { "type": "string" },
            "vignette_intensity": { "type": "number", "default": 0.35 }
          }
        },
        "typography": {
          "type": "object",
          "required": ["font_family_display", "font_family_code", "font_family_math"],
          "properties": {
            "font_family_display": { "type": "string" },
            "font_family_code": { "type": "string" },
            "font_family_math": { "type": "string" },
            "open_type_features": { "type": "string" }
          }
        }
      }
    },
    "beats": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["beat_id", "time_range", "narrative", "acoustic_anchors", "layout_containers"],
        "properties": {
          "beat_id": { "type": "integer" },
          "time_range": {
            "type": "object",
            "required": ["start_sec", "end_sec", "start_frame", "end_frame"],
            "properties": {
              "start_sec": { "type": "number" },
              "end_sec": { "type": "number" },
              "start_frame": { "type": "integer" },
              "end_frame": { "type": "integer" }
            }
          },
          "narrative": {
            "type": "object",
            "required": ["spoken_text", "intent", "visual_metaphor", "primary_focus_node_id"],
            "properties": {
              "spoken_text": { "type": "string" },
              "intent": { "type": "string" },
              "visual_metaphor": { "type": "string" },
              "primary_focus_node_id": { "type": "string" },
              "everyday_analogy": { "type": "string" }
            }
          },
          "acoustic_anchors": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["word", "timestamp_sec", "frame_trigger"],
              "properties": {
                "word": { "type": "string" },
                "timestamp_sec": { "type": "number" },
                "frame_trigger": { "type": "integer" },
                "linked_node_id": { "type": "string" },
                "linked_action": { "type": "string", "enum": ["ENTER", "HIGHLIGHT", "MORPH", "EXIT"] }
              }
            }
          },
          "layout_containers": {
            "type": "array",
            "items": {
              "$ref": "#/definitions/LayoutContainer"
            }
          }
        }
      }
    }
  },
  "definitions": {
    "LayoutContainer": {
      "type": "object",
      "required": ["container_id", "band", "bounds", "nodes"],
      "properties": {
        "container_id": { "type": "string" },
        "band": { "type": "string", "enum": ["BAND_1_HEADER", "BAND_2_THESIS", "BAND_3_STAGE", "BAND_4_CAPTIONS"] },
        "bounds": {
          "type": "object",
          "required": ["x_min_px", "y_min_px", "width_px", "height_px"],
          "properties": {
            "x_min_px": { "type": "number" },
            "y_min_px": { "type": "number" },
            "width_px": { "type": "number" },
            "height_px": { "type": "number" }
          }
        },
        "nodes": {
          "type": "array",
          "items": { "$ref": "#/definitions/VisualNode" }
        }
      }
    },
    "VisualNode": {
      "type": "object",
      "required": ["id", "node_type", "props", "motion_track"],
      "properties": {
        "id": { "type": "string" },
        "node_type": {
          "type": "string",
          "enum": ["MetricPill", "GlassHUDCard", "KineticCaptionStream", "MoERouterMatrix", "AttentionHeatmap", "SyntaxCodeBlock", "HorizontalRaceBars", "VectorFlowDiagram", "PaperFigureEmbed"]
        },
        "props": { "type": "object" },
        "motion_track": {
          "type": "object",
          "required": ["enter"],
          "properties": {
            "enter": {
              "type": "object",
              "required": ["type", "start_frame", "duration_frames", "easing"],
              "properties": {
                "type": { "type": "string", "enum": ["EASE_OUT_EXPO", "SPRING_DAMPED", "FADE_DOWN", "ZOOM_SNAP"] },
                "start_frame": { "type": "integer" },
                "duration_frames": { "type": "integer" },
                "easing": { "type": "string" },
                "spring_stiffness": { "type": "number" },
                "spring_damping": { "type": "number" }
              }
            },
            "focal_highlight": {
              "type": "object",
              "properties": {
                "trigger_frame": { "type": "integer" },
                "duration_frames": { "type": "integer" },
                "scale_multiplier": { "type": "number", "default": 1.08 },
                "glow_hex": { "type": "string" }
              }
            },
            "exit": {
              "type": "object",
              "properties": {
                "type": { "type": "string" },
                "start_frame": { "type": "integer" },
                "duration_frames": { "type": "integer" }
              }
            }
          }
        }
      }
    }
  }
}
```

---

### 1.2.2 Production-Ready VSG-IR Instance Example

```json
{
  "version": "1.0.0",
  "metadata": {
    "project_id": "deepseek_v3_moe_architecture",
    "title": "DeepSeek-V3: Multi-Head Latent Attention & Sparse MoE",
    "domain_taxonomy": "frontier_ai_architectures",
    "aspect_ratio": "9:16",
    "canvas": {
      "width_px": 1080,
      "height_px": 1920,
      "fps": 60,
      "duration_seconds": 54.0,
      "total_frames": 3240
    },
    "audio": {
      "master_voiceover_path": "public/audio/deepseek_v3_narration_master.wav",
      "background_music_path": "public/audio/dark_ambient_cyber_bed.mp3",
      "sample_rate_hz": 24000,
      "music_ducking_db": -18.5
    }
  },
  "theme": {
    "theme_id": "cyber_cyan",
    "colors": {
      "canvas_void": "#06080F",
      "surface_recessed": "#0B101D",
      "surface_primary": "rgba(15, 23, 42, 0.82)",
      "surface_elevated": "rgba(30, 41, 59, 0.92)",
      "surface_border": "rgba(255, 255, 255, 0.08)",
      "text_primary": "#F8FAFC",
      "text_secondary": "#94A3B8",
      "text_tertiary": "#64748B",
      "hero_accent": "#38BDF8",
      "secondary_accent": "#10B981",
      "status_gain": "#10B981",
      "status_loss": "#EF4444",
      "status_warning": "#F59E0B"
    },
    "materials": {
      "card_blur_px": 24,
      "border_radius_px": 20,
      "border_width_px": 1.5,
      "shadow_elevation": "0 24px 48px -12px rgba(0, 0, 0, 0.70), 0 0 32px rgba(56, 189, 248, 0.12)",
      "vignette_intensity": 0.35
    },
    "typography": {
      "font_family_display": "Inter, -apple-system, sans-serif",
      "font_family_code": "JetBrains Mono, monospace",
      "font_family_math": "KaTeX_Main, Latin Modern Math, serif",
      "open_type_features": "cv05 1, cv08 1, zero 1, tnum 1"
    }
  },
  "beats": [
    {
      "beat_id": 1,
      "time_range": {
        "start_sec": 0.0,
        "end_sec": 7.2,
        "start_frame": 0,
        "end_frame": 432
      },
      "narrative": {
        "spoken_text": "DeepSeek-V3 executes 671 billion parameters, but activates only 37 billion per token.",
        "intent": "Hook viewer with parameter scale paradox (massive model, tiny active inference compute).",
        "visual_metaphor": "Hero metric comparison card with high-luminance active parameter count and sparse node matrix.",
        "primary_focus_node_id": "hero_metric_card"
      },
      "acoustic_anchors": [
        { "word": "DeepSeek-V3", "timestamp_sec": 0.15, "frame_trigger": 7, "linked_node_id": "header_brand_badge", "linked_action": "ENTER" },
        { "word": "671 billion", "timestamp_sec": 1.80, "frame_trigger": 106, "linked_node_id": "hero_metric_card", "linked_action": "HIGHLIGHT" },
        { "word": "37 billion", "timestamp_sec": 3.90, "frame_trigger": 232, "linked_node_id": "hero_metric_card", "linked_action": "MORPH" }
      ],
      "layout_containers": [
        {
          "container_id": "c_band_1",
          "band": "BAND_1_HEADER",
          "bounds": { "x_min_px": 140, "y_min_px": 220, "width_px": 800, "height_px": 70 },
          "nodes": [
            {
              "id": "header_brand_badge",
              "node_type": "MetricPill",
              "props": {
                "icon": "cpu",
                "label": "DEEPSEEK-V3 ARCHITECTURE LAB",
                "accent_color": "#38BDF8",
                "pill_variant": "specular_glass"
              },
              "motion_track": {
                "enter": {
                  "type": "FADE_DOWN",
                  "start_frame": 0,
                  "duration_frames": 22,
                  "easing": "cubic-bezier(0.16, 1, 0.3, 1)"
                }
              }
            }
          ]
        },
        {
          "container_id": "c_band_2",
          "band": "BAND_2_THESIS",
          "bounds": { "x_min_px": 140, "y_min_px": 310, "width_px": 800, "height_px": 150 },
          "nodes": [
            {
              "id": "thesis_headline_card",
              "node_type": "GlassHUDCard",
              "props": {
                "headline": "THE 37B SECRET",
                "subhead": "Sparse dynamic routing activates < 6% compute per token",
                "max_words": 10
              },
              "motion_track": {
                "enter": {
                  "type": "EASE_OUT_EXPO",
                  "start_frame": 18,
                  "duration_frames": 26,
                  "easing": "cubic-bezier(0.16, 1, 0.3, 1)"
                }
              }
            }
          ]
        },
        {
          "container_id": "c_band_3",
          "band": "BAND_3_STAGE",
          "bounds": { "x_min_px": 140, "y_min_px": 480, "width_px": 800, "height_px": 680 },
          "nodes": [
            {
              "id": "hero_metric_card",
              "node_type": "GlassHUDCard",
              "props": {
                "title": "ACTIVE INFERENCE FOOTPRINT",
                "metric_value": "37B",
                "total_value": "/ 671B TOTAL",
                "stat_pill": "94.5% COMPUTE SAVINGS",
                "glow_color": "#38BDF8"
              },
              "motion_track": {
                "enter": {
                  "type": "SPRING_DAMPED",
                  "start_frame": 90,
                  "duration_frames": 36,
                  "easing": "spring",
                  "spring_stiffness": 140,
                  "spring_damping": 16
                },
                "focal_highlight": {
                  "trigger_frame": 230,
                  "duration_frames": 40,
                  "scale_multiplier": 1.05,
                  "glow_hex": "#38BDF8"
                }
              }
            }
          ]
        },
        {
          "container_id": "c_band_4",
          "band": "BAND_4_CAPTIONS",
          "bounds": { "x_min_px": 140, "y_min_px": 1220, "width_px": 800, "height_px": 140 },
          "nodes": [
            {
              "id": "spoken_kinetic_captions",
              "node_type": "KineticCaptionStream",
              "props": {
                "karaoke_highlight_hex": "#38BDF8",
                "font_size_px": 60,
                "chunk_size_words": 3
              },
              "motion_track": {
                "enter": { "type": "FADE_DOWN", "start_frame": 0, "duration_frames": 10, "easing": "linear" }
              }
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 1.3 Pluggable Render Adapters

The architecture defines a strict, typed TypeScript interface that every graphics backend must implement:

```typescript
export interface RenderOptions {
  outputFilePath: string;
  fps: number;
  width: number;
  height: number;
  concurrency?: number;
  crf?: number;
  codec?: "h264" | "h265" | "prores";
}

export interface RenderResult {
  outputFilePath: string;
  totalFrames: number;
  wallClockDurationSec: number;
  averageFps: number;
  peakMemoryMb: number;
}

export interface RenderAdapter {
  readonly engineName: string;
  readonly supportsFrameSeek: boolean;
  
  /**
   * Compiles the declarative VSG-IR AST into backend-specific runtime assets.
   */
  compileSceneGraph(vsg: VideoSceneGraphIR): Promise<CompiledSceneManifest>;

  /**
   * Renders a single frame at frameIndex directly to an in-memory buffer in <150ms.
   * Required for the Automated Visual QA Gatekeeper.
   */
  renderFrame(frameIndex: number, manifest: CompiledSceneManifest): Promise<Buffer>;

  /**
   * Renders the full composition to a broadcast-grade video file.
   */
  renderVideo(manifest: CompiledSceneManifest, options: RenderOptions): Promise<RenderResult>;
}
```

### 1.3.1 `RemotionBroadcastAdapter` (Primary Engine)
- **Role**: Master Broadcast Engine.
- **Implementation**:
  - Compiles the VSG-IR JSON AST into a dynamic React 19 component tree rendered inside `<Composition />`.
  - Maps `VisualNode` types directly to Tailwind v4 styled components (`<GlassHUDCard />`, `<MetricPill />`, `<KineticCaptions />`).
  - Utilizes `@remotion/google-fonts` to preload Inter and JetBrains Mono synchronously, eliminating FOUT (Flash of Unstyled Text).
  - Employs Chromium's CDP via `@remotion/renderer` (`renderStill()`) to capture arbitrary frames in **sub-120ms** for instant QA verification.
  - Multi-threaded video export with hardware acceleration flags (`h264_videotoolbox` on macOS Metal, `h264_nvenc` on Linux).

### 1.3.2 `MotionCanvasAdapter` (Auxiliary Math/Code Engine)
- **Role**: Micro-Token Code Refactoring Engine.
- **Implementation**:
  - Consumes VSG-IR nodes of type `SyntaxCodeBlock` or `VectorFlowDiagram`.
  - Transpiles nodes into `@motion-canvas/2d` generator functions utilizing the Lezer AST code parser.
  - Emits frame buffers via Vite headless puppeteer capture for seamless vector morphs.

### 1.3.3 `ManimLegacyAdapter` (Legacy Fallback Adapter)
- **Role**: Backward Compatibility Adapter.
- **Implementation**:
  - Maps VSG-IR beats into Manim `ScriptDrivenScene` instances.
  - Translates `GlassHUDCard` into `CleanText` + `TechCard` mobjects.
  - Generates low-priority draft renders when legacy regression suites are executed.

---

## 1.4 Hot-Swappable Visual Theme System

Themes are defined as pure JSON token structures that parameterize colors, surface opacities, corner radii, blur metrics, and font pairings. A short can change themes instantly by altering `"theme_id"` in the VSG-IR metadata without modifying a single line of layout or rendering code.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   HOT-SWAPPABLE BROADCAST THEME MATRIX                                      │
├───────────────────┬──────────────┬──────────────┬──────────────┬──────────────┬─────────────────────────────┤
│ Theme Token       │ Cyber Cyan   │ Neon Violet  │ Solar Amber  │ Dark Obsidian│ Architectural Domain        │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼─────────────────────────────┤
│ canvas_void       │ #06080F      │ #0A0612      │ #0D0A05      │ #050508      │ Deep chromatic carbon floor │
│ surface_primary   │ rgba(15,23,42│ rgba(24,14,38│ rgba(30,22,12│ rgba(18,18,22│ 82% Frosted glass panel fill│
│ surface_border    │ rgba(255,255,│ rgba(255,255,│ rgba(255,255,│ rgba(255,255,│ 1.5px 90-degree key hairline│
│ hero_accent       │ #38BDF8      │ #A855F7      │ #F59E0B      │ #E2E8F0      │ Primary focal glow & stroke │
│ secondary_accent  │ #10B981      │ #EC4899      │ #EA580C      │ #38BDF8      │ Complementary data accent   │
│ card_blur_px      │ 24 px        │ 28 px        │ 20 px        │ 32 px        │ Subpixel Gaussian blur      │
│ Target Domain     │ Frontier AI  │ Deep Reason  │ Hardware     │ Keynote Exec │ Content Taxonomy Focus      │
└───────────────────┴──────────────┴──────────────┴──────────────┴──────────────┴─────────────────────────────┘
```

---

# SECTION 2: Automated Visual QA & Multimodal Gatekeeper Specification

To prevent visual collisions, unreadable text, motion jitter, and platform UI occlusions from ever reaching public broadcast, the rendering pipeline is fortified with a **Two-Tier Synchronous Visual QA Gatekeeper**.

```
                           [ Rendered Candidate Frame Buffer ]
                                          │
                                          ▼
   ╔═══════════════════════════════════════════════════════════════════════════╗
   ║ TIER 1: DETERMINISTIC COMPUTER VISION (CV) HEURISTICS (Zero API Cost)     ║
   ║ Execution Time: < 50ms per frame | Local OpenCV / C++ / NumPy Kernel      ║
   ║                                                                           ║
   ║ 1. Farneback / Lucas-Kanade Optical Flow Motion Jitter & Strobing         ║
   ║    - Dense flow variance: sigma^2_a > 15.0 px/frame^2 triggers REJECT     ║
   ║    - Frame-to-frame SSIM drop > 0.22 without scene cut triggers REJECT    ║
   ║                                                                           ║
   ║ 2. WCAG AAA Relative Luminance & Pixel Contrast Ratio Analyzer            ║
   ║    - Subpixel sRGB gamma decompression to linear luminance L             ║
   ║    - Body Text / Equations: Contrast Ratio < 7.0:1 triggers REJECT        ║
   ║    - Large Headlines (>= 36px): Contrast Ratio < 4.5:1 triggers REJECT    ║
   ║                                                                           ║
   ║ 3. Axis-Aligned Bounding Box (AABB) & Text Collision Solver               ║
   ║    - Multi-body collision detection: IoU(B_i, B_j) > 0.0 triggers REJECT  ║
   ║    - Computes Minimum Translation Vectors (MTV) via PBD                   ║
   ║                                                                           ║
   ║ 4. Mobile 9:16 Safe-Zone Binary Exclusion Mask Checker                    ║
   ║    - Strict 1080x1920 UI Exclusion Mask (Top 0-220, Bottom 1420-1920,     ║
   ║      Right rail 920-1080px between 220-1420px)                            ║
   ║    - Any content intersection with mask (M = 1) triggers REJECT           ║
   ╚═══════════════════════════════════════════════════════════════════════════╝
                                          │
                         ┌────────────────┴────────────────┐
                      [ FAIL ]                          [ PASS ]
                         │                                 │
                         ▼                                 ▼
              ┌─────────────────────┐   ╔══════════════════════════════════════╗
              │ Emit Deterministic  │   ║ TIER 2: MULTIMODAL VLM CRITIC COUNCIL║
              │ Numeric PBD Patch   │   ║ (Gemini 3.8 / Gemma 4 / Ollama Cloud)║
              │ to VSG-IR AST       │   ║                                      ║
              └─────────────────────┘   ║ Critic 1: Aesthetic Quality Critic   ║
                                        ║ Critic 2: Typographic Hierarchy Crit ║
                                        ║ Critic 3: Cognitive Density Critic   ║
                                        ║ Critic 4: Temporal Audio-Sync Critic ║
                                        ╚══════════════════════════════════════╝
                                                           │
                                          ┌────────────────┴────────────────┐
                                       [ FAIL ]                          [ PASS ]
                                          │                                 │
                                          ▼                                 ▼
                               ┌─────────────────────┐            ┌───────────────────┐
                               │ Closed-Loop Repair  │            │ Approved for Final│
                               │ Diagnostic Ledger   │            │ Hardware Assembly │
                               │ (Max 3 iterations)  │            │ (Master Encoding) │
                               └─────────────────────┘            └───────────────────┘
```

---

## 2.1 Tier 1: Deterministic Computer Vision (CV) Heuristics (<50ms per frame)

Deterministic heuristics run locally via OpenCV/NumPy, intercepting low-level geometric and optical rendering bugs in **under 50 milliseconds** before invoking multimodal LLM APIs.

### 2.1.1 Optical Flow Motion Jitter & Strobing Detector
- **Problem**: Keyframe interpolation glitches, abrupt easing cutoffs, and subpixel rounding errors induce perceptible strobing, high-frequency edge jerk, and micro-flicker.
- **Mathematical Formulation**:
  Given consecutive grayscale frames $I_t(x, y)$ and $I_{t+1}(x, y)$:
  1. Compute dense optical flow $\mathbf{u}(x, y) = (u, v)$ via Gunnar Farneback's quadratic polynomial expansion:
     $$\mathbf{u} = \operatorname{calcOpticalFlowFarneback}(I_t, I_{t+1}, \text{pyr\_scale}=0.5, \text{levels}=3, \text{winsize}=15, \text{iterations}=3, \text{poly\_n}=5, \text{poly\_sigma}=1.2)$$
  2. Compute spatial flow magnitude and variance:
     $$\|\mathbf{u}\| = \sqrt{u^2 + v^2}, \quad \mu_{\|\mathbf{u}\|} = \frac{1}{N}\sum_{x,y} \|\mathbf{u}\|, \quad \sigma^2_{\|\mathbf{u}\|} = \frac{1}{N}\sum_{x,y} (\|\mathbf{u}\| - \mu_{\|\mathbf{u}\|})^2$$
  3. Compute temporal acceleration $\mathbf{a}_t$ and Jerk $\mathbf{j}_t$:
     $$\mathbf{a}_t = \frac{\mathbf{u}_{t+1} - \mathbf{u}_t}{\Delta t}, \quad \mathbf{j}_t = \frac{\mathbf{a}_{t+1} - \mathbf{a}_t}{\Delta t}$$
  4. Track sparse feature points on text edges via Lucas-Kanade:
     $$\mathbf{p}_{t+1} = \operatorname{calcOpticalFlowPyrLK}(I_t, I_{t+1}, \operatorname{goodFeaturesToTrack}(I_t, \text{maxCorners}=150))$$
- **Hard-Gate Rejection Thresholds**:
  - **Global Strobing**: Frame-to-frame SSIM drops by $> 0.22$ across fewer than 3 frames without a declared scene wipe in the VSG-IR AST.
  - **Motion Jitter / Jerk**: Acceleration variance $\sigma^2_a > 15.0\text{ px/frame}^2$ accompanied by a flow spike ratio $\frac{\|\mathbf{u}_t\|}{\operatorname{median}(\|\mathbf{u}\|)} > 3.8$.

---

### 2.1.2 WCAG AAA Relative Luminance & Pixel Contrast Ratio Analyzer
- **Problem**: Low-contrast text (e.g., slate body text on translucent dark-blue cards) causes severe readability loss on mobile devices under direct ambient sunlight.
- **Mathematical Formulation**:
  1. Decompress 8-bit non-linear sRGB channel values $C_{srgb} \in [0, 255]$ to linear light values $C_{linear} \in [0.0, 1.0]$:
     $$C = \frac{C_{srgb}}{255.0}, \quad C_{linear} = \begin{cases} \frac{C}{12.92} & \text{if } C \le 0.04045 \\ \left(\frac{C + 0.055}{1.055}\right)^{2.4} & \text{if } C > 0.04045 \end{cases}$$
  2. Compute relative luminance $L$ according to ITU-R BT.709:
     $$L = 0.2126 R_{linear} + 0.7152 G_{linear} + 0.0722 B_{linear}$$
  3. Compute the contrast ratio $CR$ between foreground text glyphs ($L_1$) and the backing surface envelope ($L_2$, where $L_1 > L_2$):
     $$CR = \frac{L_1 + 0.05}{L_2 + 0.05}$$
- **Hard-Gate Rejection Thresholds**:
  - **Normal Body Text & Math Formulas**: $CR \ge 7.0:1$ (WCAG AAA standard). Any value $< 7.0$ triggers a **Hard Gate Rejection**.
  - **Large Headlines ($\ge 36\text{px}$) & Badges**: $CR \ge 4.5:1$ (WCAG AA large standard). Any value $< 4.5$ triggers a **Hard Gate Rejection**.
  - **Kinetic Karaoke Subtitles**: $CR \ge 8.5:1$ against the background blur vignette.

---

### 2.1.3 Spatial Collision & Text-Overlap Bounding Box Solver
- **Problem**: Dynamic headline strings, expanded formulas, and multi-node diagrams collide vertically with adjacent HUD cards or subtitles.
- **Mathematical Formulation**:
  Each entity $E_i$ possesses an Axis-Aligned Bounding Box $B_i = [x_{min}^i, y_{min}^i, x_{max}^i, y_{max}^i]$.
  1. Collision condition:
     $$\operatorname{Collision}(B_i, B_j) \iff (x_{max}^i > x_{min}^j) \land (x_{min}^i < x_{max}^j) \land (y_{max}^i > y_{min}^j) \land (y_{min}^i < y_{max}^j)$$
  2. Intersection over Union:
     $$\operatorname{IoU}(B_i, B_j) = \frac{\operatorname{Area}(B_i \cap B_j)}{\operatorname{Area}(B_i \cup B_j)}$$
  3. Minimum Translation Vector (MTV) via Position-Based Dynamics (PBD):
     $$\Delta x = \min(x_{max}^i - x_{min}^j, x_{max}^j - x_{min}^i), \quad \Delta y = \min(y_{max}^i - y_{min}^j, y_{max}^j - y_{min}^i)$$
     $$\mathbf{d} = \arg\min(|\Delta x|, |\Delta y|)$$
     Relaxation applied proportionally to inverse mass $w_i = \frac{1}{m_i}$ (text cards have higher mobility than central schematics):
     $$\Delta \mathbf{p}_i = -\frac{w_i}{w_i + w_j} \mathbf{d}, \quad \Delta \mathbf{p}_j = +\frac{w_j}{w_i + w_j} \mathbf{d}$$
- **Hard-Gate Rejection Threshold**:
  - Any pair of distinct visual nodes with $\operatorname{IoU} > 0.0$ triggers an **Immediate Zero-Tolerance Rejection**.

---

### 2.1.4 Mobile 9:16 Safe-Zone Mask Violation Checker
- **Problem**: Native mobile user interface overlays on YouTube Shorts, TikTok, and Instagram Reels occlude content placed near screen borders.
- **Mathematical Formulation**:
  On a $1080 \times 1920$ canvas, define an 8-bit binary exclusion mask $M(x, y) \in \{0, 1\}$, where $1$ denotes unsafe territory:
  - **Top Exclusion Zone**: $Y \in [0, 220\text{px}]$ across $X \in [0, 1080\text{px}]$ (Platform status bar, search icon, audio selector).
  - **Bottom Exclusion Zone**: $Y \in [1420, 1920\text{px}]$ across $X \in [0, 1080\text{px}]$ (Creator avatar, handle, subscribe pill, video title, sound marquee, platform navigation bar).
  - **Right Rail Exclusion Zone**: $X \in [920, 1080\text{px}]$ between $Y \in [220, 1420\text{px}]$ (Interactive Like, Dislike, Comment, Share, and Remix icon stack).
  - **Sacred Usable Safe Zone**:
    $$X \in [140, 900\text{px}], \quad Y \in [220, 1400\text{px}] \quad (\text{Dimensions: } 760\text{px W} \times 1180\text{px H})$$
- **Mask Intersection Audit**:
  Let $B_k$ be the bounding box of visual node $k$. The violation energy is:
  $$\Omega_k = \iint_{(x,y) \in B_k} M(x, y)\,dx\,dy$$
- **Hard-Gate Rejection Threshold**:
  - If $\Omega_k > 0$ for any critical text glyph, equation token, or data card, the frame triggers an **Immediate Hard Rejection**.

---

## 2.2 Tier 2: Multimodal VLM Critic Council

Frames passing all Tier 1 CV heuristics proceed to Tier 2: an ensemble of **Four Specialized Multimodal VLM Critics** evaluated against strict scoring rubrics.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   THE 4-CRITIC VLM COUNCIL TOPOLOGY                                         │
├────────────────────┬──────────────────────────────────┬─────────────────────────────────────────────────────┤
│ Critic Persona     │ Specialization                   │ Audited Dimensions                                  │
├────────────────────┼──────────────────────────────────┼─────────────────────────────────────────────────────┤
│ Critic 1: Aesthetic│ Broadcast Art Direction          │ 4-tier elevation, glassmorphism blur ratio (24px),  │
│ Quality Critic     │ (Fireship / High-End Tech Media) │ specular hairline borders, lighting vignettes.      │
├────────────────────┼──────────────────────────────────┼─────────────────────────────────────────────────────┤
│ Critic 2: Typo-    │ Principal Design Director        │ Proportional scale hierarchy (Headline vs Subhead), │
│ graphic & Hierarchy│ (Apple Keynote Design Labs)      │ OpenType tabular figures, line leading, kerning.    │
├────────────────────┼──────────────────────────────────┼─────────────────────────────────────────────────────┤
│ Critic 3: Cognitive│ Educational Pedagogy Auditor     │ Rule of One focal target, density caps (<=12 words/ │
│ Density Critic     │ (Grant Sanderson / 3Blue1Brown)  │ card), visual-script semantic metaphor grounding.   │
├────────────────────┼──────────────────────────────────┼─────────────────────────────────────────────────────┤
│ Critic 4: Temporal │ Audio-Visual Sync Supervisor     │ Frame-Ahead Rule (-0.04s trigger lead), 1.2s static │
│ Sync Critic        │ (Kinetic Motion Timing)          │ comprehension buffer, cubic-bezier easing curves.   │
└────────────────────┴──────────────────────────────────┴─────────────────────────────────────────────────────┘
```

---

### 2.2.1 Concrete VLM Critic Prompt Templates

#### Critic 1: Aesthetic Quality Critic Prompt
```text
System: You are an elite Broadcast Art Director specializing in premium dark-mode cybernetic tech media (in the visual style of Fireship and high-end tech documentaries).
Your mandate is to ruthlessly grade the aesthetic finish, material depth, and color harmony of the rendered video keyframe.

Evaluation Rubric (Score strictly from 1.0 to 10.0):
1. Depth Layering: Are there at least 3 distinct visual depth planes (background ambient dot-grid -> hero schematic -> foreground HUD cards/subtitles)?
2. Material Authenticity: Does the frame utilize refined glassmorphism (translucent elevated surfaces, frosted backdrop-blur, and subtle 1px specular border highlights), or does it look like flat, unstyled 1990s vector clipart?
3. Chromatic Restraint: Does the frame follow the 60-30-10 palette rule (60% dark charcoal carbon #06080F, 30% structural surfaces #0F172A, 10% electric accent #38BDF8 or #A855F7)? Reject garish rainbow clashes or flat grey boxes.

Hard Rejection Triggers (Score < 7.0):
- Flat, unstyled grey rectangles (#1F2937 or #222222) lacking blur or specular highlights.
- Pure pitch-black OLED background (#000000) lacking volumetric spotlight vignettes.
- Un-antialiased or jagged vector edges.

Output Format: Strictly valid JSON matching the Gatekeeper Critic Schema.
```

#### Critic 2: Typographic & Hierarchy Critic Prompt
```text
System: You are a Principal Design Director specializing in high-retention tech media typography (in the style of Apple Keynote design systems and Alex Bowers).
Your mandate is to audit typographic scale, hierarchy, leading, and kerning.

Layout Context:
- Detected Headlines: {detected_headlines}
- Detected Body Text: {detected_body_text}
- Metric Counters: {metric_counters}

Evaluation Rubric (Score strictly from 1.0 to 10.0):
1. Proportional Hierarchy: Is there an unmistakable proportional scale between Title (52-60px), Subhead (36-42px), and Data Pills (20-24px)? Font weights must be differentiated (800 for title, 600 for subhead).
2. Word Wrap & Kerning: Are there awkward line wraps, orphan words, or cramped line-height (leading must be 1.15x for titles, 1.35x for body)?
3. Tabular & Code Alignment: Are numbers and metric counters set in clean tabular monospace without kerning wobble? Is code syntax highlighted with authentic tokens?

Hard Rejection Triggers (Score < 7.0):
- Subpixel kerning dropouts ("THE MO DEL").
- Text strings overflowing their bounding cards.
- Equations shrunken below 18px equivalent scale.

Output Format: Strictly valid JSON matching the Gatekeeper Critic Schema.
```

#### Critic 3: Cognitive Density Critic Prompt
```text
System: You are a Lead Pedagogy Auditor and Cognitive Load Researcher (following John Sweller's Cognitive Load Theory and Grant Sanderson / 3Blue1Brown principles).
Your mandate is to evaluate whether the visual layout eliminates cognitive clutter and directly communicates the technical mechanism spoken in the script.

Narrative Context:
- Spoken Audio: "{spoken_text}"
- Intended Technical Metaphor: "{intended_visual_metaphor}"
- Primary Focal Node: "{primary_focus_node_id}"

Evaluation Rubric (Score strictly from 1.0 to 10.0):
1. Rule of One Focal Target: Does exactly ONE primary element command visual focus (highlighted at 100% opacity + glow), while non-active elements dim to 30%?
2. Density Cap: Does any card contain more than 12 words? Are there more than 2 distinct text blocks competing on screen?
3. Semantic Grounding: Does the on-screen graphic directly depict the technical concept (e.g. true sparse routing paths, real attention matrices, actual manifold curves)? Reject generic metaphorical disconnects (e.g. stock gears, floating spheres).

Hard Rejection Triggers (Score < 7.0):
- Wall of text: Any single card containing > 14 words.
- More than 1 competing focal headline on screen at the same instant.
- Abstract decorative geometric slop with zero technical explanatory power.

Output Format: Strictly valid JSON matching the Gatekeeper Critic Schema.
```

#### Critic 4: Temporal Sync Critic Prompt
```text
System: You are an Audio-Visual Synchronization Supervisor.
Your mandate is to audit whether kinetic animations and camera transitions are tightly synchronized with spoken narrative word anchors.

Timing Context:
- Beat Duration: {beat_duration}s
- Acoustic Anchor Word: "{anchor_word}" at timestamp {anchor_timestamp}s
- Visual Action Trigger: {action_trigger_timestamp}s (Lead/Lag Offset: {offset_sec}s)

Evaluation Rubric (Score strictly from 1.0 to 10.0):
1. Frame-Ahead Adherence: Did the visual motion trigger exactly 0.04s (1-2 frames) BEFORE the auditory onset of the anchor word (-0.08s <= offset <= 0.00s)?
2. Comprehension Buffer: Is there at least a 1.2-second static observation window after motion completes before the scene transitions to the next beat?
3. Motion Physics: Does motion utilize organic cubic-bezier easing (ease-out-expo) or damped springs rather than robotic linear motion?

Hard Rejection Triggers (Score < 7.0):
- Visual action triggers > 0.20s AFTER the word has been vocalized (perceptible auditory-visual lag).
- Animation cuts away before the viewer has 1 second to parse the resulting state.
- Jerky, un-eased linear motion cuts.

Output Format: Strictly valid JSON matching the Gatekeeper Critic Schema.
```

---

### 2.2.2 JSON Schema Output for Critic Evaluations

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GatekeeperCriticEvaluation",
  "type": "object",
  "required": ["critic_id", "beat_id", "frame_index", "scores", "composite_score", "passed_hard_gate", "detected_defects", "prescribed_patches"],
  "properties": {
    "critic_id": { "type": "string", "enum": ["AestheticQualityCritic", "TypographicHierarchyCritic", "CognitiveDensityCritic", "TemporalSyncCritic"] },
    "beat_id": { "type": "integer" },
    "frame_index": { "type": "integer" },
    "timestamp_sec": { "type": "number" },
    "scores": {
      "type": "object",
      "required": ["dimension_1", "dimension_2", "dimension_3"],
      "properties": {
        "dimension_1": { "type": "number", "minimum": 1.0, "maximum": 10.0 },
        "dimension_2": { "type": "number", "minimum": 1.0, "maximum": 10.0 },
        "dimension_3": { "type": "number", "minimum": 1.0, "maximum": 10.0 }
      }
    },
    "composite_score": { "type": "number", "minimum": 1.0, "maximum": 10.0 },
    "passed_hard_gate": { "type": "boolean" },
    "detected_defects": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["defect_category", "severity", "description"],
        "properties": {
          "defect_category": { "type": "string" },
          "severity": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
          "target_node_id": { "type": "string" },
          "description": { "type": "string" }
        }
      }
    },
    "prescribed_patches": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["action", "target_path", "patch_value", "rationale"],
        "properties": {
          "action": { "type": "string", "enum": ["TRANSLATE", "RESCALE", "TRUNCATE_TEXT", "REDUCE_DENSITY", "RETIME_TRIGGER"] },
          "target_path": { "type": "string" },
          "patch_value": {},
          "rationale": { "type": "string" }
        }
      }
    }
  }
}
```

---

### 2.2.3 Quantitative Scoring Rubrics & Binary Hard-Gate Pass/Fail Thresholds

The council enforces an uncompromising **Binary Hard-Gate Standard**:

$$\text{Composite VLM Score} = 0.25 S_{\text{aesthetic}} + 0.25 S_{\text{typography}} + 0.30 S_{\text{density}} + 0.20 S_{\text{sync}}$$

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   BINARY HARD-GATE PASS / FAIL THRESHOLDS                                   │
├──────────────────────────────┬────────┬───────────────┬──────────────────────┬──────────────────────────────┤
│ Evaluation Pillar            │ Weight │ Min Pass Score│ Hard Rejection Cond. │ Diagnostic Action            │
├──────────────────────────────┼────────┼───────────────┼──────────────────────┼──────────────────────────────┤
│ Pillar 1: Aesthetic Quality  │ 25%    │ >= 8.0 / 10.0 │ Score < 7.0          │ Restyle glass blur & palette │
│ Pillar 2: Typography & Scale │ 25%    │ >= 8.5 / 10.0 │ Score < 7.5          │ Reflow leading / wrap text   │
│ Pillar 3: Cognitive Density  │ 30%    │ >= 8.5 / 10.0 │ Score < 7.5          │ Truncate words / isolate node│
│ Pillar 4: Temporal AV Sync   │ 20%    │ >= 8.5 / 10.0 │ Score < 7.5          │ Shift trigger by -0.04s lead │
├──────────────────────────────┼────────┼───────────────┼──────────────────────┼──────────────────────────────┤
│ OVERALL COMPOSITE GATE       │ 100%   │ >= 8.5 / 10.0 │ Composite < 8.5 OR   │ HALT EXPORT; TRIGGER CLOSED- │
│                              │        │               │ Any Pillar Hard Fail │ LOOP REPAIR GENERATOR        │
└──────────────────────────────┴────────┴───────────────┴──────────────────────┴──────────────────────────────┘
```

**Zero-Tolerance Gate Rule**: Any score $< 8.5$ halts the pipeline. The video is prohibited from proceeding to final encoding until all gates pass.

---

## 2.3 Hard-Gate Circuit Breaker & Automatic Layout Patch Proposal Generator

When a frame fails either Tier 1 CV heuristics or Tier 2 VLM critics, the **Circuit Breaker** halts the build pipeline and routes the frame to the **Automatic Layout Patch Proposal Generator**.

### 2.3.1 Closed-Loop Repair Lifecycle (Max 3 Iterations)

```
       [ Candidate Frame Extraction (t_seek < 120ms) ]
                              │
                              ▼
           [ Tier 1 CV & Tier 2 VLM Gate Audits ]
                              │
                    ┌─────────┴─────────┐
                 [ PASS ]            [ FAIL ]
                    │                   │
                    ▼                   ▼
           [ Approve Frame ]   [ Circuit Breaker Tripped ]
                                        │
                                        ▼
                             [ Check Iteration Count ]
                                        │
                         ┌──────────────┴──────────────┐
                    (Iter < 3)                    (Iter >= 3)
                         │                             │
                         ▼                             ▼
              [ Generate AST Patches ]       [ Hard Fallback Routine ]
              - PBD Translations (MTV)       - Merge secondary cards
              - Scale down (0.92x)           - Suppress decorative badge
              - Text word truncations        - Enforce safe-zone clamp
                         │                             │
                         ▼                             ▼
              [ Apply Patches to VSG-IR ]    [ Re-Evaluate Frame ]
                         │
                         ▼
              [ Fast CDP Re-Render (<150ms) ]
```

### 2.3.2 Production Diagnostic Ledger Example

```json
{
  "diagnostic_ledger_id": "diag_ds3_b1_iter1",
  "beat_id": 1,
  "frame_index": 92,
  "timestamp_sec": 1.53,
  "gatekeeper_status": "CIRCUIT_BREAKER_TRIPPED_REPAIRING",
  "tier_1_cv_violations": [
    {
      "violation_type": "AABB_COLLISION",
      "primary_node_id": "thesis_headline_card",
      "secondary_node_id": "hero_metric_card",
      "iou_value": 0.084,
      "details": "Bottom border of thesis card overlaps top boundary of hero metric card by 38px.",
      "prescribed_repair": {
        "action": "TRANSLATE",
        "target_path": "beats[0].layout_containers[2].bounds.y_min_px",
        "delta_y_px": 44,
        "rationale": "Apply PBD Minimum Translation Vector to clear vertical overlap."
      }
    }
  ],
  "tier_2_vlm_violations": [
    {
      "critic_id": "CognitiveDensityCritic",
      "pillar_score": 7.2,
      "details": "Subhead contains 15 words; exceeds density threshold of 12 words.",
      "prescribed_repair": {
        "action": "TRUNCATE_TEXT",
        "target_path": "beats[0].layout_containers[1].nodes[0].props.subhead",
        "patch_value": "Sparse dynamic routing activates < 6% compute per token",
        "rationale": "Truncate subhead text to 9 words to eliminate cognitive overload."
      }
    }
  ],
  "applied_ast_mutations": [
    { "op": "replace", "path": "beats[0].layout_containers[2].bounds.y_min_px", "value": 524 },
    { "op": "replace", "path": "beats[0].layout_containers[1].nodes[0].props.subhead", "value": "Sparse dynamic routing activates < 6% compute per token" }
  ],
  "repair_iteration": 1,
  "max_allowed_iterations": 3
}
```

The repair engine mutates the in-memory VSG-IR AST and re-renders only the target frame via Remotion's CDP seek interface in **sub-120ms**, executing the entire self-healing loop in **under 1.5 seconds**.

---

# SECTION 3: Production Pipeline Integration & Verification Matrix

## 3.1 Pipeline Execution Architecture in `pipeline/run_pipeline.py`

In the next-generation pipeline, Visual QA is integrated as an essential compilation phase rather than a post-export afterthought:

```python
# pipeline/run_pipeline.py (Architectural Blueprint)

def compile_and_render_short(spec_input: dict) -> str:
    # 1. Narrative & Acoustic Synthesis
    script_beats = generate_narrative_script(spec_input)
    audio_manifest = synthesize_and_align_audio(script_beats)
    
    # 2. Compile to Authoritative VSG-IR Declarative AST
    vsg_ir = visual_director.compile_to_vsg_ir(script_beats, audio_manifest, theme_id="cyber_cyan")
    
    # 3. Instantiate Pluggable Render Adapter
    adapter = RemotionBroadcastAdapter()
    compiled_manifest = adapter.compile_scene_graph(vsg_ir)
    
    # 4. PRE-RENDER GATEKEEPER AUDIT (Extract Keyframes at Anchor Timestamps)
    sample_frames = extract_critical_keyframes(vsg_ir)
    for frame_idx in sample_frames:
        frame_buffer = adapter.render_frame(frame_idx, compiled_manifest)
        
        # Tier 1: Deterministic CV Heuristics (<50ms)
        cv_result = cv_gatekeeper.evaluate(frame_buffer, vsg_ir, frame_idx)
        if not cv_result.passed:
            vsg_ir = apply_pbd_patches(vsg_ir, cv_result.patches)
            compiled_manifest = adapter.compile_scene_graph(vsg_ir)
            frame_buffer = adapter.render_frame(frame_idx, compiled_manifest)
            
        # Tier 2: Multimodal VLM Critic Council (>=8.5 threshold)
        vlm_result = vlm_council.evaluate(frame_buffer, vsg_ir, frame_idx)
        if vlm_result.composite_score < 8.5:
            vsg_ir = apply_vlm_patches(vsg_ir, vlm_result.patches)
            compiled_manifest = adapter.compile_scene_graph(vsg_ir)
    
    # 5. HARDWARE-ACCELERATED MASTER VIDEO ENCODING
    # Only invoked once ALL keyframes have passed the Visual QA Gatekeeper
    final_video_path = adapter.render_video(
        compiled_manifest, 
        options={"codec": "h264", "hardwareAcceleration": "if-possible"}
    )
    return final_video_path
```

---

## 3.2 Verification & Acceptance Matrix

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   ARCHITECTURAL VERIFICATION CHECKLIST                                      │
├───────────────────────────────────┬───────────────────────────────────┬─────────────────────────────────────┤
│ Architectural Requirement         │ Verification Method               │ Success Criterion                   │
├───────────────────────────────────┼───────────────────────────────────┼─────────────────────────────────────┤
│ Decoupled Script State            │ Inspect `vsg_ir_schema.json`      │ 0% references to graphics libraries │
│ Instant Frame Extraction Latency  │ Benchmark `adapter.renderFrame()` │ Latency < 150ms per frame           │
│ Deterministic CV Evaluation Time  │ Benchmark `cv_gatekeeper.py`      │ Latency < 50ms per frame            │
│ WCAG AAA Contrast Ratio           │ Pixel luminance subpixel sample   │ CR >= 7.0:1 for normal body text    │
│ Collision-Free Layout             │ Bounding box AABB check           │ IoU = 0.0 across all visual nodes   │
│ Mobile 9:16 Safe-Zone Bounds      │ Mask energy audit                 │ 0% text intersection with UI mask   │
│ Multimodal Critic Council Gate    │ VLM evaluation report             │ Composite Score >= 8.5 / 10.0       │
│ Closed-Loop Repair Convergence    │ Diagnostic ledger simulation      │ Resolves defects in <= 3 iterations │
│ Full Video Export Throughput      │ Hardware encode benchmark (60s)   │ Sustained >= 60 FPS (>1.0x line-rate│
└───────────────────────────────────┴───────────────────────────────────┴─────────────────────────────────────┘
```

---
*End of Next-Generation Architecture Specification.*
