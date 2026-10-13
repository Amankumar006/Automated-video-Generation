import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { VideoSceneGraphIR, VisualNode, LayoutContainer, BeatAST } from "../types/vsg-ir";
import { CanvasVoid } from "../components/CanvasVoid";
import { GlassHUDCard } from "../components/GlassHUDCard";
import { MetricPill } from "../components/MetricPill";
import { KineticCaptionStream } from "../components/KineticCaptionStream";
import { MoERouterMatrix } from "../components/MoERouterMatrix";
import { AttentionHeatmap } from "../components/AttentionHeatmap";
import { SyntaxCodeBlock } from "../components/SyntaxCodeBlock";
import { HorizontalRaceBars } from "../components/HorizontalRaceBars";
import { VectorFlowDiagram } from "../components/VectorFlowDiagram";

export interface BroadcastCompositionProps {
  vsg?: VideoSceneGraphIR;
  showSafeZoneOverlay?: boolean;
}

export const BroadcastComposition: React.FC<BroadcastCompositionProps> = ({
  vsg,
  showSafeZoneOverlay = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // If no VSG provided, render high-aesthetic fallback preview short
  const defaultTheme = vsg?.theme || {
    theme_id: "cyber_cyan" as const,
    colors: {
      canvas_void: "#06080F",
      surface_recessed: "#0B101D",
      surface_primary: "rgba(15, 23, 42, 0.82)",
      surface_elevated: "rgba(30, 41, 59, 0.92)",
      surface_border: "rgba(255, 255, 255, 0.15)",
      text_primary: "#F8FAFC",
      text_secondary: "#94A3B8",
      text_tertiary: "#64748B",
      hero_accent: "#38BDF8",
      secondary_accent: "#10B981",
      status_gain: "#10B981",
      status_loss: "#EF4444",
      status_warning: "#F59E0B",
    },
    materials: {
      card_blur_px: 24,
      border_radius_px: 20,
      border_width_px: 1.5,
      shadow_elevation: "0 24px 48px -12px rgba(0, 0, 0, 0.65)",
      vignette_intensity: 0.35,
    },
    typography: {
      font_family_display: "Inter",
      font_family_code: "JetBrains Mono",
      font_family_math: "KaTeX Main",
      open_type_features: "cv05=1, cv08=1, zero=1, tnum=1",
    },
  };

  const beats: BeatAST[] = vsg?.beats || [
    {
      beat_id: 1,
      time_range: { start_sec: 0, end_sec: 10, start_frame: 0, end_frame: 600 },
      narrative: {
        spoken_text: "DeepSeek V3 routes 8 routed experts dynamically per token.",
        intent: "Introduce architecture routing efficiency",
        visual_metaphor: "MoERouterMatrix",
        primary_focus_node_id: "moe_matrix",
      },
      acoustic_anchors: [
        { word: "DEEPSEEK", timestamp_sec: 0.2, frame_trigger: 12 },
        { word: "V3", timestamp_sec: 0.8, frame_trigger: 48 },
        { word: "ROUTES", timestamp_sec: 1.4, frame_trigger: 84 },
        { word: "EXPERTS", timestamp_sec: 2.0, frame_trigger: 120 },
      ],
      layout_containers: [
        {
          container_id: "c_stage",
          band: "BAND_3_STAGE",
          bounds: { x_min_px: 140, y_min_px: 500, width_px: 800, height_px: 680 },
          nodes: [
            {
              id: "moe_matrix",
              node_type: "MoERouterMatrix",
              props: {
                tokenText: "frontier_token",
                totalExperts: 256,
                activeRouted: 8,
              },
              motion_track: {
                enter: { type: "SPRING_DAMPED", start_frame: 0, duration_frames: 30 },
              },
            },
          ],
        },
      ],
    },
  ];

  // Find active beat for current frame
  let currentBeat = beats.find(
    (b) => frame >= b.time_range.start_frame && frame <= b.time_range.end_frame
  );
  if (!currentBeat && beats.length > 0) {
    currentBeat = beats[beats.length - 1];
  }

  const projectTitle = vsg?.metadata?.title || "NEXT-GEN BROADCAST ENGINE";
  const domainTaxonomy = vsg?.metadata?.domain_taxonomy || "SYSTEMS ARCHITECTURE";

  // Node dispatcher
  const renderNode = (node: VisualNode, containerBounds?: any) => {
    const nodeBounds = node.bounds || containerBounds;
    switch (node.node_type) {
      case "GlassHUDCard":
        return (
          <GlassHUDCard
            key={node.id}
            id={node.id}
            theme={defaultTheme}
            bounds={nodeBounds}
            isHeroFocus={currentBeat?.narrative.primary_focus_node_id === node.id}
            {...node.props}
          />
        );
      case "MetricPill":
        return (
          <MetricPill
            key={node.id}
            id={node.id}
            theme={defaultTheme}
            bounds={nodeBounds}
            {...node.props}
          />
        );
      case "MoERouterMatrix":
        return (
          <MoERouterMatrix
            key={node.id}
            id={node.id}
            theme={defaultTheme}
            bounds={nodeBounds}
            {...node.props}
          />
        );
      case "AttentionHeatmap":
        return (
          <AttentionHeatmap
            key={node.id}
            id={node.id}
            theme={defaultTheme}
            bounds={nodeBounds}
            {...node.props}
          />
        );
      case "SyntaxCodeBlock":
        return (
          <SyntaxCodeBlock
            key={node.id}
            id={node.id}
            theme={defaultTheme}
            bounds={nodeBounds}
            {...node.props}
          />
        );
      case "HorizontalRaceBars":
        return (
          <HorizontalRaceBars
            key={node.id}
            id={node.id}
            theme={defaultTheme}
            bounds={nodeBounds}
            {...node.props}
          />
        );
      case "VectorFlowDiagram":
        return (
          <VectorFlowDiagram
            key={node.id}
            id={node.id}
            theme={defaultTheme}
            bounds={nodeBounds}
            {...node.props}
          />
        );
      default:
        return (
          <GlassHUDCard
            key={node.id}
            id={node.id}
            theme={defaultTheme}
            bounds={nodeBounds}
            title={node.node_type}
            bodyText={JSON.stringify(node.props)}
          />
        );
    }
  };

  return (
    <div className="relative w-[1080px] h-[1920px] overflow-hidden select-none font-sans text-white">
      {/* 0. Canvas Void Background */}
      <CanvasVoid theme={defaultTheme} />

      {/* 1. BAND 1: HEADER & DOMAIN BADGE (Y: 220px to 300px) */}
      <div className="absolute top-[230px] left-[140px] w-[760px] flex items-center justify-between z-40">
        <div className="flex items-center gap-3">
          <div
            className="w-3 h-3 rounded-full shadow-[0_0_12px_rgba(56,189,248,0.9)]"
            style={{ backgroundColor: defaultTheme.colors.hero_accent }}
          />
          <span
            className="text-[20px] font-mono font-bold tracking-widest uppercase"
            style={{ color: defaultTheme.colors.hero_accent }}
          >
            THE MODEL VERSE
          </span>
        </div>
        <span className="px-3.5 py-1 rounded-full bg-slate-900/90 border border-slate-700 text-[18px] font-mono font-bold text-slate-300 uppercase tracking-wider">
          {domainTaxonomy}
        </span>
      </div>

      {/* 2. BAND 2: THESIS & SCENE HEADLINE (Y: 310px to 470px) */}
      <div className="absolute top-[310px] left-[140px] w-[760px] z-40">
        <h1 className="text-[52px] font-black tracking-tight leading-[1.15] text-white line-clamp-2">
          {projectTitle}
        </h1>
        {currentBeat?.narrative.intent && (
          <p className="mt-2 text-[24px] font-medium text-slate-300 leading-snug line-clamp-2">
            {currentBeat.narrative.intent}
          </p>
        )}
      </div>

      {/* 3. BAND 3: PRIMARY VISUAL STAGE (Y: 480px to 1180px) */}
      <div className="absolute inset-0 z-30 pointer-events-none">
        {currentBeat?.layout_containers?.map((container) => (
          <div key={container.container_id} className="absolute inset-0 pointer-events-none">
            {container.nodes.map((node) => renderNode(node, container.bounds))}
          </div>
        ))}
      </div>

      {/* 4. BAND 4: KINETIC SPOKEN CAPTIONS (Y: 1200px to 1400px) */}
      <KineticCaptionStream
        anchors={currentBeat?.acoustic_anchors}
        spokenTextFallback={currentBeat?.narrative.spoken_text}
        theme={defaultTheme}
        yPositionPx={1210}
      />

      {/* 5. DEBUG / QA SAFE-ZONE OVERLAY (If enabled) */}
      {showSafeZoneOverlay && (
        <div className="absolute inset-0 pointer-events-none z-50">
          {/* Top exclusion */}
          <div className="absolute top-0 left-0 right-0 h-[220px] bg-red-500/20 border-b border-red-500" />
          {/* Bottom exclusion */}
          <div className="absolute bottom-0 left-0 right-0 h-[500px] bg-red-500/20 border-t border-red-500" />
          {/* Right rail exclusion */}
          <div className="absolute top-[220px] right-0 bottom-[500px] w-[160px] bg-red-500/20 border-l border-red-500" />
          {/* Sacred area */}
          <div className="absolute top-[220px] left-[140px] w-[760px] h-[1200px] border-2 border-emerald-400/60" />
        </div>
      )}
    </div>
  );
};
