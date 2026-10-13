import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { ThemeTokens, BoundingBoxPx } from "../types/vsg-ir";

export interface MoERouterMatrixProps {
  id?: string;
  theme?: ThemeTokens;
  bounds?: BoundingBoxPx;
  tokenText?: string;
  totalExperts?: number;
  activeRouted?: number;
  sharedExperts?: number;
  activeExpertIds?: number[];
  routerStrategy?: string;
}

export const MoERouterMatrix: React.FC<MoERouterMatrixProps> = ({
  id,
  theme,
  bounds,
  tokenText = "token_embedding",
  totalExperts = 256,
  activeRouted = 8,
  sharedExperts = 1,
  activeExpertIds = [4, 12, 19, 27, 34, 45, 52, 61],
  routerStrategy = "Top-K Sigmoid Router",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const heroAccent = theme?.colors.hero_accent || "#38BDF8";
  const secAccent = theme?.colors.secondary_accent || "#10B981";

  // Entrance spring
  const scale = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 100 },
  });

  // Routing wave pulse progress (0.0s to 1.5s loop or clamp)
  const waveProgress = interpolate(
    frame % Math.round(2 * fps),
    [0, Math.round(1.5 * fps)],
    [0, 1],
    { extrapolateRight: "clamp" }
  );

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

  // Generate a display grid of 64 representative cells
  const gridCells = Array.from({ length: 64 }, (_, i) => i + 1);

  return (
    <div
      id={id}
      style={containerStyle}
      className="p-6 rounded-3xl bg-slate-950/85 border-2 border-slate-700/80 backdrop-blur-2xl shadow-2xl flex flex-col gap-4 select-none z-20"
    >
      {/* 1. Header & Router Badge */}
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <div className="flex items-center gap-3">
          <div
            className="w-3.5 h-3.5 rounded-full animate-ping"
            style={{ backgroundColor: heroAccent }}
          />
          <span className="text-[22px] font-mono font-bold tracking-wider uppercase text-slate-200">
            {routerStrategy}
          </span>
        </div>
        <div className="px-3 py-1 rounded-full bg-slate-900 border border-slate-700 text-[18px] font-mono text-slate-300">
          Token: <span className="font-bold text-white font-mono">"{tokenText}"</span>
        </div>
      </div>

      {/* 2. Top-K Dispatch Telemetry */}
      <div className="flex items-center justify-between bg-slate-900/60 rounded-xl px-4 py-2 border border-white/5 text-[18px] font-mono">
        <span className="text-slate-400">
          Activating: <strong className="text-white font-black">{activeRouted}</strong> of{" "}
          {totalExperts} Experts
        </span>
        <span style={{ color: secAccent }} className="font-bold">
          +{sharedExperts} Shared (Always Active)
        </span>
      </div>

      {/* 3. Expert Silicon Grid (64 micro-cores visualization) */}
      <div className="grid grid-cols-8 gap-2 p-3 bg-black/40 rounded-2xl border border-white/5">
        {gridCells.map((cid) => {
          const isActive = activeExpertIds.includes(cid);
          return (
            <div
              key={cid}
              className={`h-7 rounded-md transition-all duration-200 flex items-center justify-center text-[12px] font-mono font-bold ${
                isActive
                  ? "border border-white/80 shadow-[0_0_12px_rgba(56,189,248,0.8)]"
                  : "bg-slate-800/40 border border-slate-700/30 text-slate-500"
              }`}
              style={{
                backgroundColor: isActive ? heroAccent : undefined,
                color: isActive ? "#05070E" : undefined,
                opacity: isActive ? 1.0 : 0.35 + 0.15 * Math.sin(cid + waveProgress * 6),
              }}
            >
              {cid}
            </div>
          );
        })}
      </div>

      {/* 4. Shared Expert Chassis */}
      <div className="flex items-center justify-between px-4 py-2.5 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-[18px] font-mono">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
          <span className="text-emerald-200 font-bold">Shared Expert Core</span>
        </div>
        <span className="text-emerald-400 font-bold tracking-wider text-[16px]">
          100% ROUTING EFFICIENCY
        </span>
      </div>
    </div>
  );
};
