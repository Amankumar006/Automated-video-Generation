import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { ThemeTokens, BoundingBoxPx } from "../types/vsg-ir";

export interface PricingDeltaComparisonProps {
  id?: string;
  theme?: ThemeTokens;
  bounds?: BoundingBoxPx;
  title?: string;
  subtitle?: string;
  oldTierName?: string;
  oldPrice?: string;
  oldLatency?: string;
  newTierName?: string;
  newPrice?: string;
  newLatency?: string;
  savingsPercentage?: string;
  efficiencyMultiplier?: string;
}

export const PricingDeltaComparison: React.FC<PricingDeltaComparisonProps> = ({
  id,
  theme,
  bounds,
  title = "API Cost & Latency Disruption",
  subtitle = "Next-generation model economics breakdown",
  oldTierName = "Incumbent / Previous Gen",
  oldPrice = "$15.00 / 1M",
  oldLatency = "8.4s Latency",
  newTierName = "Frontier Distilled / New Tier",
  newPrice = "$1.10 / 1M",
  newLatency = "2.1s Latency",
  savingsPercentage = "92.6% CHEAPER",
  efficiencyMultiplier = "4.0x FASTER",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const heroAccent = theme?.colors.hero_accent || "#38BDF8";
  const gainColor = theme?.colors.status_gain || "#10B981";

  const scale = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 110 },
  });

  const containerStyle: React.CSSProperties = {
    position: bounds ? "absolute" : "relative",
    ...(bounds && {
      left: `${bounds.x_min_px}px`,
      top: `${bounds.y_min_px}px`,
      width: `${bounds.width_px}px`,
      height: bounds.height_px > 0 ? `${bounds.height_px}px` : "auto",
    }),
    transform: `scale(${scale})`,
  };

  return (
    <div
      id={id}
      style={containerStyle}
      className="p-6 rounded-3xl bg-slate-950/90 border-2 border-slate-700/80 backdrop-blur-2xl shadow-2xl flex flex-col gap-4 select-none z-20"
    >
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <div>
          <h3 className="text-[26px] font-black text-white tracking-tight">
            {title}
          </h3>
          <p className="text-[16px] font-medium text-slate-400">{subtitle}</p>
        </div>
        <span className="px-3 py-1 rounded-full text-[14px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 uppercase">
          {savingsPercentage}
        </span>
      </div>

      {/* Side by Side Comparison Cards */}
      <div className="grid grid-cols-2 gap-4 mt-1">
        {/* Old Tier */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-rose-500/30 flex flex-col justify-between gap-3 opacity-80">
          <div>
            <span className="text-[13px] font-mono text-rose-400 uppercase font-bold">
              {oldTierName}
            </span>
            <div className="mt-2 text-[32px] font-mono font-bold text-slate-400 line-through">
              {oldPrice}
            </div>
          </div>
          <div className="pt-2 border-t border-white/5 text-[14px] font-mono text-slate-400">
            {oldLatency}
          </div>
        </div>

        {/* New Tier (Hero) */}
        <div
          className="p-4 rounded-2xl border-2 flex flex-col justify-between gap-3 shadow-[0_0_24px_rgba(56,189,248,0.2)]"
          style={{
            backgroundColor: "rgba(15, 23, 42, 0.95)",
            borderColor: `${heroAccent}80`,
          }}
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="text-[13px] font-mono uppercase font-black text-sky-300">
                {newTierName}
              </span>
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-black bg-emerald-500 text-slate-950">
                ACTIVE
              </span>
            </div>
            <div className="mt-2 text-[36px] font-mono font-black text-white leading-none">
              {newPrice}
            </div>
          </div>
          <div className="pt-2 border-t border-white/10 flex items-center justify-between text-[14px] font-mono">
            <span className="text-emerald-400 font-bold">{newLatency}</span>
            <span className="text-[12px] font-bold text-sky-400">
              {efficiencyMultiplier}
            </span>
          </div>
        </div>
      </div>

      {/* Payoff Banner */}
      <div className="p-3.5 rounded-xl bg-slate-900/90 border border-white/10 flex items-center justify-between text-[15px] font-mono">
        <span className="text-slate-300 font-semibold">Net Impact:</span>
        <span className="text-emerald-400 font-bold">
          Scale 10x more requests within same GPU/API budget
        </span>
      </div>
    </div>
  );
};
