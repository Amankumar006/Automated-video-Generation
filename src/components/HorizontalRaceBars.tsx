import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { ThemeTokens, BoundingBoxPx } from "../types/vsg-ir";

export interface BenchmarkItem {
  name: string;
  score: number;
  maxScore?: number;
  isHero?: boolean;
  pillTag?: string;
}

export interface HorizontalRaceBarsProps {
  id?: string;
  theme?: ThemeTokens;
  bounds?: BoundingBoxPx;
  title?: string;
  benchmarkName?: string;
  items?: BenchmarkItem[];
}

export const HorizontalRaceBars: React.FC<HorizontalRaceBarsProps> = ({
  id,
  theme,
  bounds,
  title = "MMLU-Pro Benchmark Showdown",
  benchmarkName = "Accuracy %",
  items = [
    { name: "DeepSeek-V3", score: 88.5, maxScore: 100, isHero: true, pillTag: "WINNER" },
    { name: "GPT-4o (0513)", score: 85.2, maxScore: 100 },
    { name: "Claude 3.5 Sonnet", score: 84.8, maxScore: 100 },
  ],
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const heroAccent = theme?.colors.hero_accent || "#38BDF8";
  const gainColor = theme?.colors.status_gain || "#10B981";

  const barSpring = spring({
    frame,
    fps,
    config: { damping: 16, stiffness: 120 },
  });

  const containerStyle: React.CSSProperties = {
    position: bounds ? "absolute" : "relative",
    ...(bounds && {
      left: `${bounds.x_min_px}px`,
      top: `${bounds.y_min_px}px`,
      width: `${bounds.width_px}px`,
      height: bounds.height_px > 0 ? `${bounds.height_px}px` : "auto",
    }),
  };

  return (
    <div
      id={id}
      style={containerStyle}
      className="p-6 rounded-3xl bg-slate-950/85 border-2 border-slate-700/80 backdrop-blur-2xl shadow-2xl flex flex-col gap-5 select-none z-20"
    >
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <h3 className="text-[26px] font-extrabold text-white tracking-tight">
          {title}
        </h3>
        <span className="text-[18px] font-mono font-bold text-slate-400 uppercase">
          {benchmarkName}
        </span>
      </div>

      <div className="flex flex-col gap-4">
        {items.map((item, idx) => {
          const max = item.maxScore || 100;
          const targetPct = (item.score / max) * 100;
          const currentPct = targetPct * barSpring;

          return (
            <div key={idx} className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between text-[20px] font-mono">
                <div className="flex items-center gap-2.5">
                  <span
                    className={`font-bold ${
                      item.isHero ? "text-white text-[22px]" : "text-slate-300"
                    }`}
                  >
                    {item.name}
                  </span>
                  {item.pillTag && (
                    <span
                      className="px-2 py-0.5 rounded-full text-[14px] font-bold"
                      style={{
                        backgroundColor: `${gainColor}22`,
                        color: gainColor,
                        border: `1px solid ${gainColor}66`,
                      }}
                    >
                      {item.pillTag}
                    </span>
                  )}
                </div>
                <span
                  className="font-black text-[22px]"
                  style={{ color: item.isHero ? heroAccent : "#CBD5E1" }}
                >
                  {item.score.toFixed(1)}%
                </span>
              </div>

              {/* Progress Bar Track */}
              <div className="h-6 w-full rounded-full bg-slate-900 border border-slate-800 overflow-hidden relative">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${currentPct}%`,
                    backgroundColor: item.isHero ? heroAccent : "#334155",
                    boxShadow: item.isHero
                      ? `0 0 16px ${heroAccent}88`
                      : undefined,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Engineering Efficiency & Cost Telemetry Deck */}
      <div className="mt-2 pt-4 border-t border-white/10 flex flex-col gap-3">
        <div className="flex items-center justify-between text-[16px] font-mono">
          <span className="font-bold text-slate-400 uppercase tracking-wider">
            Compute & Cost Efficiency
          </span>
          <span className="px-2.5 py-0.5 rounded-full text-[14px] font-mono font-bold bg-sky-500/20 text-sky-400 border border-sky-500/40">
            FRONTIER PARITY
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-700/60 flex flex-col gap-1">
            <span className="text-[13px] font-mono text-slate-400 uppercase">
              Training Compute
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-[24px] font-mono font-black text-white">
                2.788M
              </span>
              <span className="text-[13px] font-mono text-emerald-400 font-bold">
                (5.8x Cheaper)
              </span>
            </div>
            <span className="text-[11px] font-mono text-slate-500">
              H800 GPU Hours
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-700/60 flex flex-col gap-1">
            <span className="text-[13px] font-mono text-slate-400 uppercase">
              API Input Pricing
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-[24px] font-mono font-black text-emerald-400">
                $0.14
              </span>
              <span className="text-[13px] font-mono text-emerald-400 font-bold">
                / 1M tokens
              </span>
            </div>
            <span className="text-[11px] font-mono text-slate-500">
              vs $2.50 Industry Average
            </span>
          </div>
        </div>

        <div className="text-[13px] font-mono text-slate-500 text-center">
          Source: DeepSeek-V3 Official Benchmark Evaluation
        </div>
      </div>
    </div>
  );
};
