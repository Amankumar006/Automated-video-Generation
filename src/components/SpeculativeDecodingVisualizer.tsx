import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

const fade = (frame: number, fps: number, start: number, end: number) =>
  interpolate(frame, [start * fps, end * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

const tokens = ["the", "next", "token", "is"];

export const SpeculativeDecodingVisualizer: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const intro = spring({ frame, fps, config: { damping: 16, stiffness: 110 } });
  const draftOpacity = fade(frame, fps, 0.05, 0.35);
  const verifyOpacity = fade(frame, fps, 2.15, 2.45);
  const resultOpacity = fade(frame, fps, 4.45, 4.8);
  const outroOpacity = fade(frame, fps, 6.65, 7.0);

  return (
    <div className="relative h-[1920px] w-[1080px] overflow-hidden bg-[#081018] font-sans text-white select-none">
      <div
        className="pointer-events-none absolute left-1/2 top-[620px] h-[820px] w-[820px] -translate-x-1/2 rounded-full"
        style={{ background: "radial-gradient(circle, rgba(14,165,233,.13), transparent 68%)" }}
      />

      <div className="absolute left-[140px] top-[115px] w-[800px] text-center text-[22px] font-mono font-semibold tracking-[0.28em] text-slate-300">
        THE MODEL VERSE // INFERENCE SPEED
      </div>
      <div className="absolute left-[140px] top-[185px] w-[800px] text-center" style={{ transform: `scale(${intro})` }}>
        <div className="text-[27px] font-mono font-bold tracking-widest text-cyan-300">SPECULATIVE DECODING</div>
        <h1 className="mt-3 text-[55px] font-black leading-none tracking-tight">Let a small model guess.</h1>
        <div className="mt-4 text-[25px] font-mono text-slate-300">Then let the big model verify in one batch.</div>
      </div>

      <div className="absolute left-[140px] top-[450px] w-[800px] text-center" style={{ opacity: draftOpacity }}>
        <div className="text-[25px] font-mono font-bold tracking-widest text-cyan-300">01 · DRAFT MODEL</div>
        <div className="mt-3 text-[32px] font-black">Four cheap guesses</div>
        <div className="mt-8 flex justify-center gap-4">
          {tokens.map((token, index) => {
            const tokenIn = fade(frame, fps, 0.55 + index * 0.25, 0.8 + index * 0.25);
            return (
              <div
                key={token}
                className="flex h-[88px] w-[150px] items-center justify-center rounded-2xl border-2 border-cyan-300 bg-cyan-950/80 text-[27px] font-mono font-bold text-cyan-100 shadow-[0_0_24px_rgba(34,211,238,.35)]"
                style={{ opacity: tokenIn, transform: `translateY(${(1 - tokenIn) * 24}px)` }}
              >
                {token}
              </div>
            );
          })}
        </div>
        <div className="mx-auto mt-8 h-[3px] w-[640px] bg-gradient-to-r from-transparent via-cyan-400 to-transparent" />
      </div>

      <div className="absolute left-[140px] top-[765px] flex w-[800px] items-center justify-center gap-5" style={{ opacity: Math.min(draftOpacity, verifyOpacity) }}>
        <div className="h-[3px] w-[190px] bg-gradient-to-r from-cyan-400 to-amber-300" />
        <div className="text-[22px] font-mono font-black tracking-widest text-amber-200">BATCH CHECK →</div>
        <div className="h-[3px] w-[190px] bg-gradient-to-r from-amber-300 to-transparent" />
      </div>

      <div className="absolute left-[140px] top-[855px] w-[800px] text-center" style={{ opacity: verifyOpacity }}>
        <div className="text-[25px] font-mono font-bold tracking-widest text-amber-300">02 · VERIFIER MODEL</div>
        <div className="mt-3 text-[32px] font-black">One forward pass checks them all</div>
        <div className="relative mx-auto mt-8 h-[180px] w-[760px] rounded-3xl border-2 border-amber-300/80 bg-amber-950/40 px-8 py-7 shadow-[0_0_36px_rgba(251,191,36,.2)]">
          <div className="absolute bottom-3 right-8 text-[18px] font-mono font-bold tracking-widest text-amber-200">GREEN = REUSE · RED = RUN AGAIN</div>
          <div className="absolute left-[38px] right-[38px] top-[88px] h-[4px] bg-amber-300/70" />
          <div className="relative z-10 flex justify-center gap-4">
            {tokens.map((token, index) => {
              const check = fade(frame, fps, 2.55 + index * 0.18, 2.85 + index * 0.18);
              const accepted = index < 3;
              return (
                <div key={token} className="flex w-[150px] flex-col items-center gap-3" style={{ opacity: check }}>
                  <div className={`flex h-[60px] w-[140px] items-center justify-center rounded-xl border-2 text-[23px] font-mono font-bold ${accepted ? "border-emerald-300 bg-emerald-950 text-emerald-100" : "border-rose-300 bg-rose-950 text-rose-100"}`}>
                    {token}
                  </div>
                  <div className={`text-[24px] font-black ${accepted ? "text-emerald-300" : "text-rose-300"}`}>{accepted ? "✓ REUSE" : "↻ RUN AGAIN"}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="absolute left-[140px] top-[1260px] w-[800px] text-center" style={{ opacity: resultOpacity }}>
        <div className="text-[25px] font-mono font-bold tracking-widest text-emerald-300">03 · THE PAYOFF</div>
        <div className="mt-4 text-[39px] font-black">Reuse correct guesses.</div>
        <div className="mt-4 text-[25px] font-mono text-slate-300">Only rejected tokens need expensive work.</div>
        <div className="mx-auto mt-10 flex w-[650px] items-center justify-between rounded-2xl border border-emerald-400/70 bg-emerald-950/60 px-8 py-5 text-[30px] font-mono font-bold">
          <span className="text-slate-200">4 proposed</span><span className="text-cyan-300">→</span><span className="text-emerald-300">3 reused</span><span className="text-cyan-300">→</span><span className="text-amber-300">1 checked</span>
        </div>
      </div>

      <div className="absolute left-[140px] top-[1515px] w-[800px] text-center" style={{ opacity: outroOpacity }}>
        <div className="text-[42px] font-black text-white">Faster decoding</div>
        <div className="mt-3 text-[27px] font-mono text-cyan-300">without changing the answer</div>
      </div>
    </div>
  );
};
