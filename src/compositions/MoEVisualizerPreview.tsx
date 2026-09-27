import React from "react";
import { AbsoluteFill } from "remotion";
import { DeepSeekV3MoEVisualizer } from "../components/DeepSeekV3MoEVisualizer";
import { KineticCaptions } from "../components/KineticCaptions";
import { DEEPSEEK_V3_SPEC } from "../data/deepseek-v3";
import { WordToken } from "../types/aligner";

// Sample aligned words for testing captions
const SAMPLE_WORDS: WordToken[] = [
  { word: "DeepSeek-V3", start: 0.1, end: 0.8 },
  { word: "activates", start: 0.85, end: 1.3 },
  { word: "only", start: 1.35, end: 1.6 },
  { word: "37", start: 1.65, end: 1.9 },
  { word: "billion", start: 1.95, end: 2.3 },
  { word: "parameters", start: 2.35, end: 2.9 },
  { word: "per", start: 2.95, end: 3.1 },
  { word: "token", start: 3.15, end: 3.5 },
  { word: "across", start: 3.55, end: 3.85 },
  { word: "256", start: 3.9, end: 4.3 },
  { word: "routed", start: 4.35, end: 4.7 },
  { word: "experts", start: 4.75, end: 5.2 },
];

export interface MoEVisualizerPreviewProps {
  showSafeZoneOverlay?: boolean;
}

export const MoEVisualizerPreview: React.FC<MoEVisualizerPreviewProps> = ({
  showSafeZoneOverlay = false,
}) => {
  return (
    <AbsoluteFill className="bg-[#06080F]">
      {/* 1. Main Architecture Visualizer */}
      <DeepSeekV3MoEVisualizer
        spec={DEEPSEEK_V3_SPEC}
        tokenText="intelligence"
        selectedExpertIds={[14, 42, 88, 102, 137, 189, 210, 244]}
      />

      {/* 2. Kinetic Captions Layer */}
      <KineticCaptions words={SAMPLE_WORDS} />

      {/* 3. Development Safe-Zone Inspection Overlay */}
      {showSafeZoneOverlay && (
        <AbsoluteFill className="pointer-events-none z-50">
          {/* Top Unsafe margin (0 - 300px) */}
          <div className="absolute top-0 left-0 w-full h-[300px] bg-red-500/15 border-b-2 border-red-500/40 flex items-center justify-center">
            <span className="text-red-300 font-mono text-[22px]">
              Top Safe Margin (Search / Status: 0–300px)
            </span>
          </div>

          {/* Bottom Unsafe margin (1540 - 1920px) */}
          <div className="absolute top-[1540px] left-0 w-full h-[380px] bg-red-500/15 border-t-2 border-red-500/40 flex items-center justify-center">
            <span className="text-red-300 font-mono text-[22px]">
              Bottom Safe Margin (Platform Controls: 1540–1920px)
            </span>
          </div>

          {/* Right Unsafe margin (920 - 1080px) */}
          <div className="absolute top-[300px] left-[920px] w-[160px] h-[1240px] bg-red-500/15 border-l-2 border-red-500/40 flex items-center justify-center">
            <span
              className="text-red-300 font-mono text-[18px] rotate-90"
              style={{ whiteSpace: "nowrap" }}
            >
              Action Bar Margin (920–1080px)
            </span>
          </div>

          {/* Usable Safe Box Outline (160 to 920, 300 to 1540) */}
          <div className="absolute top-[300px] left-[160px] w-[760px] h-[1240px] border-2 border-dashed border-emerald-400/50 pointer-events-none" />
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
