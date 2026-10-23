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
        <h1 className="text-[52px] font-black tracking-tight leading-tight mt-2 text-white">
          DeepSeekMoE Routing
        </h1>
        <div className="mt-3 px-6 py-2 rounded-full bg-slate-900 border border-slate-700 text-[26px] font-mono text-slate-300">
          <span className="text-[#38BDF8] font-bold">{spec.activeParams}</span>{" "}
          Active / {spec.totalParams} Total
        </div>
      </div>

      <div className="absolute top-[150px] left-[160px] w-[760px] text-center text-[22px] font-mono font-semibold tracking-[0.28em] text-slate-300">
        THE MODEL VERSE // MIXTURE-OF-EXPERTS
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
      <div className="absolute top-[650px] left-[160px] w-[760px] h-[145px] rounded-3xl bg-slate-900/90 border-2 border-[#38BDF8] flex flex-col items-center justify-start pt-9 shadow-[0_0_40px_rgba(56,189,248,0.25)] z-10">
        <span className="text-[24px] font-mono text-[#38BDF8] uppercase tracking-wider font-bold">
          {spec.routingAffinity}
        </span>
        <span className="text-[32px] font-black text-white mt-1">
          Top-{spec.activeRoutedPerToken} from {spec.routedExperts} Routed Experts
        </span>
        <div className="absolute top-2 left-1/2 -translate-x-1/2 flex items-end gap-2 h-6">
          {selectedExpertIds.map((expertId, idx) => (
            <div
              key={expertId}
              className="w-8 rounded-sm bg-cyan-400"
              style={{
                height: `${10 + (idx % 4) * 4}px`,
                opacity: interpolate(
                  routeProgress,
                  [0.35 + idx * 0.05, 0.65 + idx * 0.04],
                  [0.2, 1],
                  { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
                ),
              }}
            />
          ))}
          <span className="ml-2 text-[15px] font-mono font-bold text-cyan-300">
            TOP-8 CUTOFF
          </span>
        </div>
      </div>

      {/* 1 SHARED EXPERT HUD (Y = 810px) - Always active in DeepSeek-V3 */}
      <div className="absolute top-[825px] left-[160px] w-[760px] h-[85px] rounded-2xl bg-emerald-950/60 border-2 border-emerald-500/80 flex items-center justify-between px-8 z-10">
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

      {/* Explicit routing trace: token -> gate -> selected expert lanes. */}
      <div className="absolute inset-0 pointer-events-none z-[5]">
        <div className="absolute top-[605px] left-1/2 -translate-x-1/2 h-[45px] border-l-2 border-dashed border-cyan-400/70" />
        <div className="absolute top-[795px] left-1/2 -translate-x-1/2 h-[165px] border-l-2 border-dashed border-cyan-400/45" />
        <svg
          className="absolute top-[960px] left-[160px] w-[760px] h-[330px] overflow-visible"
          viewBox="0 0 760 330"
          aria-hidden="true"
        >
          {selectedExpertIds.map((expertId, idx) => {
            const column = expertId % 16;
            const row = Math.floor(expertId / 16);
            const targetX = 35.2 + column * 43.3;
            const targetY = 22 + row * 17.1;
            const startX = 230 + idx * 45;
            const bendX = startX + (targetX - startX) * 0.45;
            const pathProgress = interpolate(
              routeProgress,
              [0.45 + idx * 0.04, 0.72 + idx * 0.03],
              [0, 1],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            );
            return (
              <path
                key={expertId}
                d={`M ${startX} 0 C ${bendX} 20, ${bendX} ${targetY - 20}, ${targetX} ${targetY}`}
                stroke="#38BDF8"
                strokeOpacity={0.35 + pathProgress * 0.65}
                strokeWidth="4"
                strokeDasharray="8 6"
                strokeDashoffset={`${(1 - pathProgress) * 80}`}
                fill="none"
              />
            );
          })}
        </svg>
      </div>

      {/* 256-ROUTED EXPERT MATRIX GRID (Y = 920px to 1320px) */}
      <div className="absolute top-[920px] left-[160px] w-[760px] flex flex-col items-center">
        <span className="relative z-20 bg-[#06080F] px-4 text-[26px] font-mono text-slate-300 uppercase tracking-widest mb-3">
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
            const selectedRank = selectedExpertIds.indexOf(idx);
            const opacity = isSelected
              ? interpolate(
                  routeProgress,
                  [0.45 + selectedRank * 0.04, 0.72 + selectedRank * 0.03],
                  [0.35, 1],
                  { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
                )
              : 0.25;
            const bg = isSelected ? "#38BDF8" : "#334155";
            const shadow =
              isSelected && routeProgress > 0.55 + selectedRank * 0.03
                ? "0 0 12px #38BDF8"
                : "none";

            return (
              <div
                key={idx}
                className="w-full h-full rounded-[3px]"
                style={{
                  backgroundColor: bg,
                  opacity: isSelected ? opacity : 0.36,
                  boxShadow: shadow,
                }}
              />
            );
          })}
        </div>

        {/* Selected expert callout tags */}
        <div className="mt-4 h-[34px] w-[760px] flex flex-nowrap items-center justify-center gap-1 overflow-visible">
          {selectedExpertIds.map((expertId, idx) => (
            <span
              key={idx}
              className="px-2 py-1 rounded-lg bg-[#0ea5e9]/25 border border-[#38BDF8]/70 text-[#7DD3FC] text-[18px] font-mono font-bold whitespace-nowrap"
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

      {/* Compact state register uses the lower safe area without competing with captions. */}
      <div className="absolute top-[1510px] left-[160px] w-[760px] flex items-center justify-center gap-5 text-slate-300">
        <span className="text-[26px] font-mono font-bold text-slate-200">256 CANDIDATES</span>
        <span className="text-[26px] text-cyan-400">→</span>
        <span className="text-[26px] font-mono font-bold text-cyan-300">8 ACTIVE</span>
        <span className="text-[26px] text-emerald-400">→</span>
        <span className="text-[26px] font-mono font-bold text-emerald-300">1 SHARED</span>
      </div>
    </div>
  );
};
