import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { ThemeTokens, BoundingBoxPx } from "../types/vsg-ir";

export interface AttentionHeatmapProps {
  id?: string;
  theme?: ThemeTokens;
  bounds?: BoundingBoxPx;
  tokens?: string[];
  headCount?: number;
  activeHead?: number;
}

export const AttentionHeatmap: React.FC<AttentionHeatmapProps> = ({
  id,
  theme,
  bounds,
  tokens = ["The", "Model", "Verse", "Scales", "Fast"],
  headCount = 8,
  activeHead = 1,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const heroAccent = theme?.colors.hero_accent || "#38BDF8";

  const containerStyle: React.CSSProperties = {
    position: bounds ? "absolute" : "relative",
    ...(bounds && {
      left: `${bounds.x_min_px}px`,
      top: `${bounds.y_min_px}px`,
      width: `${bounds.width_px}px`,
      height: bounds.height_px > 0 ? `${bounds.height_px}px` : "auto",
    }),
  };

  // Synthetic deterministic attention weights matrix
  const matrix = tokens.map((q, i) =>
    tokens.map((k, j) => {
      if (i === j) return 0.85;
      if (j < i) return 0.45 / (i - j + 1);
      return 0.15;
    })
  );

  return (
    <div
      id={id}
      style={containerStyle}
      className="p-6 rounded-3xl bg-slate-950/85 border-2 border-slate-700/80 backdrop-blur-2xl shadow-2xl flex flex-col gap-4 select-none z-20"
    >
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <h3 className="text-[24px] font-mono font-black text-white uppercase tracking-wider">
          Multi-Head Attention Matrix
        </h3>
        <span
          className="px-3 py-1 rounded-full text-[16px] font-mono font-bold uppercase"
          style={{
            backgroundColor: `${heroAccent}22`,
            color: heroAccent,
            border: `1px solid ${heroAccent}66`,
          }}
        >
          Head {activeHead} / {headCount}
        </span>
      </div>

      <div className="flex flex-col gap-2 mt-2">
        {/* Token Column Headers */}
        <div className="grid grid-cols-6 gap-2 text-center text-[16px] font-mono text-slate-400">
          <div className="text-left font-bold text-slate-500">Q \ K</div>
          {tokens.map((tok, j) => (
            <div key={j} className="truncate font-bold">
              {tok}
            </div>
          ))}
        </div>

        {/* Matrix Rows */}
        {matrix.map((row, i) => (
          <div key={i} className="grid grid-cols-6 gap-2 items-center">
            <span className="text-[16px] font-mono font-bold text-slate-400 truncate">
              {tokens[i]}
            </span>
            {row.map((score, j) => {
              const bgAlpha = Math.min(1.0, Math.max(0.08, score));
              return (
                <div
                  key={j}
                  className="h-10 rounded-lg flex items-center justify-center text-[14px] font-mono font-bold border border-white/10"
                  style={{
                    backgroundColor: `${heroAccent}${Math.round(bgAlpha * 255).toString(16).padStart(2, "0")}`,
                    color: bgAlpha > 0.5 ? "#06080F" : "#F8FAFC",
                  }}
                >
                  {score.toFixed(2)}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
};
