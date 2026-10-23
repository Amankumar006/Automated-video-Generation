import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { VerifiedModelSpec } from "../types/model-spec";

export interface DeepSeekMoEVisualizerProps {
  spec: VerifiedModelSpec;
  tokenText?: string;
  selectedExpertIds?: number[];
}

const fade = (frame: number, fps: number, start: number, end: number) =>
  interpolate(frame, [start * fps, end * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

export const DeepSeekV3MoEVisualizer: React.FC<DeepSeekMoEVisualizerProps> = ({
  spec,
  tokenText = "transformer",
  selectedExpertIds = [14, 42, 88, 102, 137, 189, 210, 244],
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const hudScale = spring({ frame, fps, config: { damping: 14, stiffness: 100 } });

  const tokenProgress = fade(frame, fps, 0.05, 0.65);
  const gateIn = fade(frame, fps, 0.84, 1.05);
  const gateOut = fade(frame, fps, 2.45, 2.75);
  const gateOpacity = Math.min(gateIn, 1 - gateOut);
  const poolOpacity = fade(frame, fps, 2.65, 2.95);
  const sharedOpacity = fade(frame, fps, 3.15, 3.45);
  const outroOpacity = fade(frame, fps, 5.0, 5.3);
  const tokenY = interpolate(tokenProgress, [0, 1], [300, 430]);
  const routerProgress = fade(frame, fps, 0.58, 1.0);
  const selectedGroups = selectedExpertIds.map((id) => Math.floor(id / 8));

  return (
    <div className="relative w-[1080px] h-[1920px] overflow-hidden select-none bg-[#06080F] text-white font-sans">
      <div
        className="absolute top-1/3 left-1/2 h-[760px] w-[760px] -translate-x-1/2 -translate-y-1/2 rounded-full pointer-events-none"
        style={{ background: "radial-gradient(circle, rgba(14,165,233,.12), transparent 70%)" }}
      />

      <div className="absolute top-[120px] left-[160px] w-[760px] text-center text-[22px] font-mono font-semibold tracking-[0.28em] text-slate-300">
        THE MODEL VERSE // MIXTURE-OF-EXPERTS
      </div>

      <div
        className="absolute top-[190px] left-[160px] w-[760px] text-center"
        style={{ transform: `scale(${hudScale})` }}
      >
        <div className="text-[26px] font-mono font-semibold tracking-widest text-[#38BDF8]">
          {spec.modelName.toUpperCase()} ARCHITECTURE
        </div>
        <h1 className="mt-2 text-[52px] font-black leading-tight tracking-tight">
          How the gate routes one token
        </h1>
        <div className="mx-auto mt-3 w-fit rounded-full border border-slate-700 bg-slate-900 px-6 py-2 text-[24px] font-mono text-slate-300">
          <span className="font-bold text-[#38BDF8]">{spec.activeParams}</span> active / {spec.totalParams} total
        </div>
      </div>

      {/* Beat 1: the token is the only moving object. */}
      <div
        className="absolute left-[300px] flex h-[92px] w-[480px] items-center justify-center rounded-2xl border-2 border-cyan-300 bg-gradient-to-r from-cyan-600 to-blue-600 shadow-[0_0_30px_rgba(6,182,212,.5)]"
        style={{ top: `${tokenY}px`, opacity: 1 - gateOpacity * 0.65 }}
      >
        <span className="text-[32px] font-mono font-black text-white">Token: “{tokenText}”</span>
      </div>

      {/* The causal handoff is explicit: token → router → scoring lane. */}
      <div className="absolute left-[440px] top-[492px] h-[110px] w-[200px]" style={{ opacity: routerProgress }}>
        <div className="absolute left-[98px] top-0 h-[42px] w-[3px] bg-cyan-400/80" />
        <div className="absolute left-[79px] top-[36px] h-[42px] w-[42px] rounded-full border-2 border-cyan-200 bg-cyan-500 shadow-[0_0_24px_rgba(34,211,238,.8)]" />
        <div className="absolute left-[98px] top-[78px] h-[32px] w-[3px] bg-cyan-400/80" />
        <div className="absolute left-[128px] top-[50px] text-[18px] font-mono font-bold tracking-widest text-cyan-200">ROUTER</div>
      </div>

      {/* Beat 2: a dedicated scoring lane, with no competing elements inside it. */}
      <div
        className="absolute top-[620px] left-[160px] h-[180px] w-[760px] rounded-3xl border-2 border-[#38BDF8] bg-slate-900/95 px-8 pt-9 text-center shadow-[0_0_40px_rgba(56,189,248,.2)]"
        style={{ opacity: gateOpacity, transform: `translateY(${(1 - gateOpacity) * 22}px)` }}
      >
        <div className="absolute left-1/2 top-3 flex h-7 -translate-x-1/2 items-end gap-2">
          {selectedExpertIds.map((id, idx) => (
            <div
              key={id}
              className="w-8 rounded-sm bg-cyan-400"
              style={{
                height: `${10 + (idx % 4) * 4}px`,
                opacity: fade(frame, fps, 0.95 + idx * 0.04, 1.25 + idx * 0.04),
              }}
            />
          ))}
          <span className="ml-2 self-center text-[14px] font-mono font-bold text-cyan-300">TOP-8</span>
        </div>
        <div className="text-[24px] font-mono font-bold tracking-wider text-[#67D7FF]">1. SCORE THE TOKEN</div>
        <div className="mt-2 text-[34px] font-black text-white">Keep 8 of 256 experts</div>
        <div className="mt-1 text-[21px] font-mono text-slate-300">sigmoid affinity + bias gate</div>
      </div>

      <div className="absolute left-[500px] top-[804px] h-[34px] w-[160px]" style={{ opacity: poolOpacity }}>
        <div className="absolute left-[30px] top-0 h-[25px] border-l-2 border-dashed border-cyan-400" />
        <div className="absolute left-[23px] top-[20px] border-x-[8px] border-t-[10px] border-x-transparent border-t-cyan-400" />
        <div className="absolute left-[48px] top-[2px] whitespace-nowrap text-[18px] font-mono font-bold text-cyan-300">8 routes</div>
      </div>

      {/* Beat 3: the pool is isolated in its own region. */}
      <div className="absolute left-[160px] top-[835px] w-[760px] text-center" style={{ opacity: poolOpacity }}>
        <div className="text-[24px] font-mono font-bold tracking-widest text-slate-200">2. SELECTED EXPERTS</div>
        <div className="mt-1 text-[22px] font-mono text-slate-300">256 candidates → 32 groups → 8 active</div>
      </div>

      <div
        className="absolute left-[180px] top-[925px] h-[320px] w-[720px] rounded-3xl border border-slate-700 bg-slate-950/90 p-4"
        style={{ opacity: poolOpacity }}
      >
        <div
          className="relative grid h-full w-full gap-[9px]"
          style={{ gridTemplateColumns: "repeat(8, minmax(0, 1fr))", gridTemplateRows: "repeat(4, minmax(0, 1fr))" }}
        >
          {Array.from({ length: 32 }).map((_, idx) => {
            const rank = selectedGroups.indexOf(idx);
            const selected = rank >= 0;
            const active = selected ? fade(frame, fps, 2.15 + rank * 0.08, 2.5 + rank * 0.08) : 0.28;
            return (
              <div
                key={idx}
                className="rounded-[3px]"
                style={{
                  backgroundColor: selected ? "#38BDF8" : "#1A263A",
                  opacity: selected ? active : 0.18,
                  boxShadow: selected && active > 0.8 ? "0 0 12px #38BDF8" : "none",
                }}
              />
            );
          })}
          <svg className="pointer-events-none absolute inset-0 h-full w-full" viewBox="0 0 688 288" aria-hidden="true">
            {selectedExpertIds.map((id, rank) => {
              const group = Math.floor(id / 8);
              const column = group % 8;
              const row = Math.floor(group / 8);
              const targetX = 43 + column * 86;
              const targetY = 35 + row * 67;
              const startX = 190 + rank * 42;
              const progress = fade(frame, fps, 2.2 + rank * 0.08, 2.55 + rank * 0.08);
              return (
                <path
                  key={id}
                  d={`M ${startX} 0 C ${startX} 30, ${targetX} ${targetY - 30}, ${targetX} ${targetY}`}
                  fill="none"
                  stroke="#38BDF8"
                  strokeWidth="3"
                  strokeDasharray="7 6"
                  strokeOpacity={0.15 + progress * 0.75}
                />
              );
            })}
          </svg>
        </div>
      </div>

      <div className="absolute left-[160px] top-[1260px] flex h-[38px] w-[760px] items-center justify-center gap-2" style={{ opacity: poolOpacity }}>
        {selectedExpertIds.map((id) => (
          <span key={id} className="rounded-md border border-cyan-400/70 bg-cyan-950/60 px-2 py-1 text-[20px] font-mono font-bold text-cyan-100">E-{id}</span>
        ))}
      </div>

      {/* Beat 4: keep the shared expert visually separate from the routed pool. */}
      <div
        className="absolute left-[160px] top-[1360px] flex h-[92px] w-[760px] items-center justify-between rounded-2xl border-2 border-emerald-500/80 bg-emerald-950/70 px-8"
        style={{ opacity: sharedOpacity }}
      >
        <div className="flex items-center gap-3 text-[26px] font-bold text-emerald-200"><span className="h-4 w-4 rounded-full bg-emerald-400 shadow-[0_0_16px_rgba(52,211,153,.9)]" />1 shared expert</div>
        <div className="text-[24px] font-mono font-bold text-emerald-300">always active</div>
      </div>

      <div className="absolute left-[160px] top-[1510px] w-[760px] text-center" style={{ opacity: outroOpacity }}>
        <div className="text-[30px] font-mono font-bold text-slate-100">
          256 candidates <span className="text-cyan-400">→</span> 8 active <span className="text-emerald-400">→</span> 1 shared
        </div>
      </div>
    </div>
  );
};
