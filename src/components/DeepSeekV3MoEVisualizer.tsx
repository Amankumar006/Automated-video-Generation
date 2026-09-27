import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { VerifiedModelSpec } from "../types/model-spec";

export interface DeepSeekMoEVisualizerProps {
  spec: VerifiedModelSpec;
  tokenText?: string;
  selectedExpertIds?: number[];
}

export const DeepSeekV3MoEVisualizer: React.FC<DeepSeekMoEVisualizerProps> = ({
  spec,
  tokenText = "transformer",
  selectedExpertIds = [14, 42, 88, 102, 137, 189, 210, 244],
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Entrance spring for the header/HUD
  const hudScale = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 100 },
  });

  // Token entry motion from top of safe zone down to router (0 to 0.7s)
  const tokenY = interpolate(frame, [0, Math.round(0.7 * fps)], [340, 520], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Routing wave dispatch progress (0.7s to 1.5s)
  const routeProgress = interpolate(
    frame,
    [Math.round(0.7 * fps), Math.round(1.5 * fps)],
    [0, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  return (
    <div className="relative w-[1080px] h-[1920px] bg-[#06080F] text-white font-sans overflow-hidden select-none">
      {/* Background ambient radial glow */}
      <div
        className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full pointer-events-none"
        style={{
          background:
            "radial-gradient(circle, rgba(14, 165, 233, 0.16) 0%, rgba(6, 8, 15, 0) 70%)",
        }}
      />

      {/* TOP SAFE-ZONE HEADER (Y = 320px) */}
      <div
        className="absolute top-[320px] left-[160px] w-[760px] flex flex-col items-center text-center"
        style={{ transform: `scale(${hudScale})` }}
      >
        <span className="text-[#38BDF8] text-[28px] font-mono tracking-widest uppercase font-semibold">
          {spec.modelName.toUpperCase()} ARCHITECTURE
        </span>
        <h1 className="text-[56px] font-black tracking-tight leading-tight mt-2 text-white">
          DeepSeekMoE Routing
        </h1>
        <div className="mt-3 px-6 py-2 rounded-full bg-slate-900 border border-slate-700 text-[26px] font-mono text-slate-300">
          <span className="text-[#38BDF8] font-bold">{spec.activeParams}</span>{" "}
          Active / {spec.totalParams} Total
        </div>
      </div>

      {/* TOKEN INGESTION PILL (Y = 520px) */}
      <div
        className="absolute left-1/2 -translate-x-1/2 w-[480px] h-[85px] rounded-2xl bg-gradient-to-r from-cyan-600 to-blue-600 border-2 border-cyan-300 flex items-center justify-center shadow-[0_0_30px_rgba(6,182,212,0.5)] z-20"
        style={{ top: `${tokenY}px` }}
      >
        <span className="text-[32px] font-mono font-black text-white">
          Token: "{tokenText}"
        </span>
      </div>

      {/* ROUTING GATEWAY / AFFINITY ENGINE (Y = 650px) */}
      <div className="absolute top-[650px] left-[160px] w-[760px] h-[130px] rounded-3xl bg-slate-900/90 border-2 border-[#38BDF8] flex flex-col items-center justify-center shadow-[0_0_40px_rgba(56,189,248,0.25)] z-10">
        <span className="text-[24px] font-mono text-[#38BDF8] uppercase tracking-wider font-bold">
          {spec.routingAffinity}
        </span>
        <span className="text-[34px] font-black text-white mt-1">
          Top-{spec.activeRoutedPerToken} from {spec.routedExperts} Routed Experts
        </span>
      </div>

      {/* 1 SHARED EXPERT HUD (Y = 810px) - Always active in DeepSeek-V3 */}
      <div className="absolute top-[810px] left-[160px] w-[760px] h-[85px] rounded-2xl bg-emerald-950/60 border-2 border-emerald-500/80 flex items-center justify-between px-8 z-10">
        <div className="flex items-center space-x-3">
          <span className="w-4 h-4 rounded-full bg-emerald-400" />
          <span className="text-[26px] font-bold text-emerald-200">
            {spec.sharedExperts} Shared Expert
          </span>
        </div>
        <span className="text-[24px] font-mono font-extrabold text-emerald-400 uppercase">
          100% ALWAYS ACTIVE
        </span>
      </div>

      {/* 256-ROUTED EXPERT MATRIX GRID (Y = 920px to 1320px) */}
      <div className="absolute top-[920px] left-[160px] w-[760px] flex flex-col items-center">
        <span className="text-[22px] font-mono text-slate-400 uppercase tracking-widest mb-3">
          {spec.routedExperts} Routed Expert Pool
        </span>

        {/* 16x16 micro-tile grid representing all 256 experts */}
        <div
          className="w-[720px] h-[300px] p-4 rounded-3xl bg-slate-950/80 border border-slate-800"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(16, minmax(0, 1fr))",
            gap: "5px",
          }}
        >
          {Array.from({ length: spec.routedExperts }).map((_, idx) => {
            const isSelected = selectedExpertIds.includes(idx);
            const opacity = isSelected
              ? interpolate(routeProgress, [0.5, 1], [0.35, 1])
              : 0.25;
            const bg = isSelected ? "#38BDF8" : "#334155";
            const shadow =
              isSelected && routeProgress > 0.8
                ? "0 0 12px #38BDF8"
                : "none";

            return (
              <div
                key={idx}
                className="w-full h-full rounded-[3px]"
                style={{
                  backgroundColor: bg,
                  opacity,
                  boxShadow: shadow,
                }}
              />
            );
          })}
        </div>

        {/* Selected expert callout tags */}
        <div className="mt-4 flex flex-wrap justify-center gap-2 max-w-[720px]">
          {selectedExpertIds.map((expertId, idx) => (
            <span
              key={idx}
              className="px-3 py-1 rounded-lg bg-[#0ea5e9]/20 border border-[#38BDF8]/60 text-[#38BDF8] text-[20px] font-mono font-bold"
              style={{
                opacity: interpolate(
                  routeProgress,
                  [0.6 + idx * 0.04, 1],
                  [0, 1],
                  {
                    extrapolateLeft: "clamp",
                    extrapolateRight: "clamp",
                  }
                ),
              }}
            >
              E-{expertId}
            </span>
          ))}
        </div>
      </div>

      {/* BOTTOM SAFE-ZONE BRAND FOOTER (Y = 1460px) */}
      <div className="absolute top-[1460px] left-[160px] w-[760px] flex items-center justify-center space-x-3 text-slate-400">
        <span className="w-3 h-3 rounded-full bg-[#38BDF8]" />
        <span className="text-[26px] font-mono tracking-wider font-semibold">
          THEMODELVERSE.IN / ARCHITECTURE
        </span>
      </div>
    </div>
  );
};
