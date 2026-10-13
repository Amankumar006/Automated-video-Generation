import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { AcousticAnchor, ThemeTokens } from "../types/vsg-ir";

export interface KineticCaptionStreamProps {
  anchors?: AcousticAnchor[];
  theme?: ThemeTokens;
  spokenTextFallback?: string;
  yPositionPx?: number;
}

export const KineticCaptionStream: React.FC<KineticCaptionStreamProps> = ({
  anchors = [],
  theme,
  spokenTextFallback = "",
  yPositionPx = 1210,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTimeSec = frame / fps;
  const heroAccent = theme?.colors.hero_accent || "#38BDF8";

  // If anchors with frame_trigger/timestamp_sec are available, synchronize word-by-word
  if (anchors && anchors.length > 0) {
    let activeIndex = anchors.findIndex((a, idx) => {
      const nextTime =
        idx < anchors.length - 1
          ? anchors[idx + 1].timestamp_sec
          : a.timestamp_sec + 0.6;
      return currentTimeSec >= a.timestamp_sec && currentTimeSec < nextTime;
    });

    if (activeIndex === -1) {
      // Hold previous word during brief micro-pauses (< 0.35s)
      for (let i = anchors.length - 1; i >= 0; i--) {
        if (currentTimeSec > anchors[i].timestamp_sec) {
          if (currentTimeSec - anchors[i].timestamp_sec < 0.35) {
            activeIndex = i;
          }
          break;
        }
      }
    }

    if (activeIndex === -1) {
      // Outside spoken range
      return null;
    }

    // Chunk into punchy 2-word groups to prevent layout jumping and safe-zone clipping
    const chunkSize = 2;
    const chunkStart = Math.floor(activeIndex / chunkSize) * chunkSize;
    const currentChunk = anchors.slice(chunkStart, chunkStart + chunkSize);

    return (
      <div
        className="absolute left-[140px] w-[760px] flex justify-center pointer-events-none select-none z-50"
        style={{ top: `${yPositionPx}px` }}
      >
        <div className="px-8 py-3.5 rounded-3xl bg-slate-950/85 border border-white/15 backdrop-blur-xl flex flex-wrap justify-center items-center gap-4 shadow-2xl">
          {currentChunk.map((anchor, idx) => {
            const globalIdx = chunkStart + idx;
            const isCurrent = globalIdx === activeIndex;

            return (
              <span
                key={`${anchor.word}-${idx}`}
                className="text-[52px] font-black uppercase tracking-tight transition-transform duration-100"
                style={{
                  color: isCurrent ? heroAccent : "#F8FAFC",
                  textShadow: isCurrent
                    ? `0 0 28px ${heroAccent}ee, 0 4px 12px rgba(0,0,0,0.9)`
                    : "0 4px 10px rgba(0,0,0,0.85)",
                  transform: isCurrent ? "scale(1.08)" : "scale(1.0)",
                }}
              >
                {anchor.word}
              </span>
            );
          })}
        </div>
      </div>
    );
  }

  // Fallback to spoken text preview pill if no word timestamps provided
  if (spokenTextFallback) {
    return (
      <div
        className="absolute left-[140px] w-[760px] flex justify-center pointer-events-none select-none z-50"
        style={{ top: `${yPositionPx}px` }}
      >
        <div className="px-7 py-3 rounded-2xl bg-slate-950/80 border border-white/15 backdrop-blur-md shadow-xl text-center">
          <span className="text-[34px] font-bold text-slate-100 tracking-tight line-clamp-2">
            "{spokenTextFallback}"
          </span>
        </div>
      </div>
    );
  }

  return null;
};
