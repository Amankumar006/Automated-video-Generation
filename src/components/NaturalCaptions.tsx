import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";

export interface CaptionPhrase {
  text: string;
  start: number;
  end: number;
}

export const NaturalCaptions: React.FC<{ phrases: CaptionPhrase[] }> = ({ phrases }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const time = frame / fps;
  const active = phrases.find((phrase) => time >= phrase.start && time <= phrase.end);
  if (!active) return null;

  return (
    <div className="pointer-events-none absolute left-[140px] top-[1650px] z-50 flex w-[800px] justify-center select-none">
      <div className="min-h-[92px] border-t border-slate-700/80 px-6 pt-4 text-center">
        <span className="text-[35px] font-black uppercase tracking-tight text-white" style={{ textShadow: "0 4px 12px rgba(0,0,0,.95)" }}>
          {active.text}
        </span>
      </div>
    </div>
  );
};
