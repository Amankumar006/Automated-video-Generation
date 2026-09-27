import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { WordToken } from "../types/aligner";

export interface KineticCaptionsProps {
  words: WordToken[];
}

export const KineticCaptions: React.FC<KineticCaptionsProps> = ({ words }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  if (!words || words.length === 0) return null;

  // 1. Find active word, or hold previous word during micro-pauses (< 0.4s) to prevent flicker
  let activeIndex = words.findIndex(
    (w: WordToken) => currentTime >= w.start && currentTime <= w.end
  );

  if (activeIndex === -1) {
    // Find the most recent previous word
    for (let i = words.length - 1; i >= 0; i--) {
      if (currentTime > words[i].end) {
        if (currentTime - words[i].end < 0.4) {
          activeIndex = i;
        }
        break;
      }
    }
  }

  // If outside speech window entirely, render nothing
  if (activeIndex === -1) return null;

  // 2. Chunk into stable groups of 3 words to prevent layout reflow jumping
  const chunkSize = 3;
  const chunkStart = Math.floor(activeIndex / chunkSize) * chunkSize;
  const currentChunk = words.slice(chunkStart, chunkStart + chunkSize);

  return (
    <div className="absolute top-[1280px] left-[160px] w-[760px] flex justify-center pointer-events-none z-50 select-none">
      <div className="px-8 py-4 rounded-3xl bg-black/80 border border-white/15 backdrop-blur-md flex flex-wrap justify-center gap-4 shadow-2xl">
        {currentChunk.map((item, idx) => {
          const isCurrent =
            currentTime >= item.start && currentTime <= item.end;
          return (
            <span
              key={idx}
              className="text-[64px] font-black uppercase tracking-tight"
              style={{
                color: isCurrent ? "#38BDF8" : "#F8FAFC",
                textShadow: isCurrent
                  ? "0 0 25px rgba(56, 189, 248, 0.95), 0 4px 10px rgba(0,0,0,0.9)"
                  : "0 4px 10px rgba(0,0,0,0.9)",
                transform: isCurrent ? "scale(1.08)" : "scale(1.0)",
              }}
            >
              {item.word}
            </span>
          );
        })}
      </div>
    </div>
  );
};
