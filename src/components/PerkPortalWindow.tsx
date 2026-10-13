import React from "react";
import { spring, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { ThemeTokens, BoundingBoxPx } from "../types/vsg-ir";

export interface PerkChecklistItem {
  label: string;
  isCompleted?: boolean;
}

export interface PerkPortalWindowProps {
  id?: string;
  theme?: ThemeTokens;
  bounds?: BoundingBoxPx;
  portalUrl?: string;
  programTitle?: string;
  creditValue?: string;
  partnerName?: string;
  checklist?: PerkChecklistItem[];
  ctaButtonText?: string;
  showCursorClick?: boolean;
}

export const PerkPortalWindow: React.FC<PerkPortalWindowProps> = ({
  id,
  theme,
  bounds,
  portalUrl = "anthropic.com/startups",
  programTitle = "Claude Startups Accelerator",
  creditValue = "$1,000 FREE CREDITS",
  partnerName = "Anthropic & AWS Activate",
  checklist = [
    { label: "Raised under $5M in funding", isCompleted: true },
    { label: "Valid company domain & work email", isCompleted: true },
    { label: "Building production AI application", isCompleted: true },
  ],
  ctaButtonText = "Claim Credits Now",
  showCursorClick = true,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const heroAccent = theme?.colors.hero_accent || "#38BDF8";
  const gainColor = theme?.colors.status_gain || "#10B981";

  // Entrance spring
  const scale = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 110 },
  });

  // Animated cursor travel & click
  const cursorProgress = interpolate(
    frame,
    [Math.round(0.5 * fps), Math.round(1.6 * fps)],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const isClicked = frame > Math.round(1.5 * fps);

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
      className="rounded-3xl bg-slate-950/90 border-2 border-slate-700/80 backdrop-blur-2xl shadow-2xl flex flex-col overflow-hidden select-none z-20"
    >
      {/* 1. macOS Browser Chrome Bar */}
      <div className="px-5 py-3.5 bg-slate-900/95 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-3.5 h-3.5 rounded-full bg-rose-500/80 border border-rose-600" />
          <div className="w-3.5 h-3.5 rounded-full bg-amber-500/80 border border-amber-600" />
          <div className="w-3.5 h-3.5 rounded-full bg-emerald-500/80 border border-emerald-600" />
        </div>

        {/* URL Pill */}
        <div className="px-4 py-1 rounded-full bg-slate-950/80 border border-white/10 flex items-center gap-2 text-[14px] font-mono text-slate-300">
          <svg
            className="w-3.5 h-3.5 text-emerald-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            />
          </svg>
          <span className="font-semibold text-slate-200">{portalUrl}</span>
        </div>

        <span className="text-[12px] font-mono font-bold text-slate-400 uppercase tracking-widest">
          PORTAL
        </span>
      </div>

      {/* 2. Hero Credit Value Banner */}
      <div className="p-6 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex flex-col">
            <span className="text-[14px] font-mono font-bold text-slate-400 uppercase tracking-wider">
              {partnerName}
            </span>
            <h3 className="text-[28px] font-black text-white tracking-tight leading-snug">
              {programTitle}
            </h3>
          </div>
          <div
            className="px-3.5 py-1.5 rounded-full font-mono text-[16px] font-black uppercase tracking-wider shadow-lg"
            style={{
              backgroundColor: `${gainColor}25`,
              color: gainColor,
              border: `1.5px solid ${gainColor}80`,
            }}
          >
            VERIFIED PERK
          </div>
        </div>

        {/* Big Highlight Value Card */}
        <div
          className="p-5 rounded-2xl border-2 flex items-center justify-between"
          style={{
            background: `radial-gradient(ellipse at center, ${heroAccent}20 0%, rgba(15, 23, 42, 0.9) 100%)`,
            borderColor: `${heroAccent}60`,
          }}
        >
          <div className="flex flex-col">
            <span className="text-[13px] font-mono font-bold text-sky-300 uppercase tracking-wider">
              Total Package Grant
            </span>
            <span className="text-[44px] font-black tracking-tight text-white leading-none mt-1">
              {creditValue}
            </span>
          </div>
          <div className="text-right flex flex-col items-end">
            <span className="text-[14px] font-mono font-bold text-emerald-400">
              100% SUBSIDIZED
            </span>
            <span className="text-[12px] font-mono text-slate-400">
              1-Year Duration
            </span>
          </div>
        </div>

        {/* 3. Eligibility Criteria Checklist */}
        <div className="flex flex-col gap-2.5 mt-1">
          <span className="text-[14px] font-mono font-bold text-slate-400 uppercase tracking-wider">
            Fast Eligibility Checklist
          </span>
          <div className="flex flex-col gap-2">
            {checklist.map((item, idx) => (
              <div
                key={idx}
                className="flex items-center gap-3 p-2.5 rounded-xl bg-slate-900/80 border border-white/5 text-[16px] font-mono"
              >
                <div
                  className="w-5 h-5 rounded-full flex items-center justify-center font-bold text-[12px]"
                  style={{
                    backgroundColor: `${gainColor}33`,
                    color: gainColor,
                    border: `1px solid ${gainColor}88`,
                  }}
                >
                  ✓
                </div>
                <span className="text-slate-200 font-semibold">{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 4. Interactive CTA Button with Click Effect */}
        <div className="relative mt-2 flex justify-center">
          <div
            className={`w-full py-4 rounded-2xl font-mono text-[20px] font-black uppercase tracking-wider flex items-center justify-center gap-3 transition-transform duration-150 ${
              isClicked ? "scale-[0.98] brightness-110" : "scale-100"
            }`}
            style={{
              background: `linear-gradient(135deg, ${heroAccent} 0%, #0284C7 100%)`,
              color: "#030712",
              boxShadow: isClicked
                ? `0 0 24px ${heroAccent}aa, inset 0 2px 4px rgba(255,255,255,0.4)`
                : `0 8px 24px ${heroAccent}40`,
            }}
          >
            <span>{ctaButtonText}</span>
            <span className="text-[22px]">→</span>
          </div>

          {/* Animated Cursor */}
          {showCursorClick && (
            <div
              className="absolute pointer-events-none transition-all duration-75"
              style={{
                left: `${200 + cursorProgress * 140}px`,
                top: `${cursorProgress * 18}px`,
                transform: isClicked ? "scale(0.85)" : "scale(1.0)",
              }}
            >
              <svg
                className="w-8 h-8 drop-shadow-[0_4px_12px_rgba(0,0,0,0.8)] text-white fill-white"
                viewBox="0 0 24 24"
              >
                <path d="M3 3l7 18 3-7 7-3L3 3z" />
              </svg>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
