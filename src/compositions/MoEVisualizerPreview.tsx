import React from "react";
import { AbsoluteFill, Audio, staticFile } from "remotion";
import { DeepSeekV3MoEVisualizer } from "../components/DeepSeekV3MoEVisualizer";
import { KineticCaptions } from "../components/KineticCaptions";
import { DEEPSEEK_V3_SPEC } from "../data/deepseek-v3";
import { WordToken } from "../types/aligner";

// Sample aligned words for testing captions
const SAMPLE_WORDS: WordToken[] = [
  { word: "DeepSeek", start: 0.01, end: 0.74 },
  { word: "V3", start: 0.74, end: 0.92 },
  { word: "activates", start: 0.92, end: 1.77 },
  { word: "only", start: 1.77, end: 2.09 },
  { word: "37", start: 2.09, end: 2.235 },
  { word: "billion", start: 2.235, end: 2.825 },
  { word: "parameters", start: 2.825, end: 3.85 },
  { word: "per", start: 3.85, end: 4.04 },
  { word: "token", start: 4.04, end: 4.555 },
  { word: "across", start: 4.555, end: 5.065 },
  { word: "256", start: 5.065, end: 5.425 },
  { word: "routed", start: 5.425, end: 5.885 },
  { word: "experts", start: 5.885, end: 6.56 },
];

export interface MoEVisualizerPreviewProps {
  showSafeZoneOverlay?: boolean;
  audioSrc?: string;
}

export const MoEVisualizerPreview: React.FC<MoEVisualizerPreviewProps> = ({
  showSafeZoneOverlay = false,
  audioSrc,
}) => {
  return (
    <AbsoluteFill className="bg-[#06080F]">
      <Audio src={audioSrc ?? staticFile("audio/kokoro_narration.wav")} volume={1} />
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
