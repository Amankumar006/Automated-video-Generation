import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { ThemeTokens, BoundingBoxPx } from "../types/vsg-ir";

export interface NewsMetricItem {
  label: string;
  value: string;
  deltaText?: string;
  isPositive?: boolean;
}

export interface NewsAnnouncementBannerProps {
  id?: string;
  theme?: ThemeTokens;
  bounds?: BoundingBoxPx;
  labName?: string;
  announcementHeadline?: string;
  releaseDate?: string;
  modelVersion?: string;
  metrics?: NewsMetricItem[];
  canonicalUrl?: string;
}

export const NewsAnnouncementBanner: React.FC<NewsAnnouncementBannerProps> = ({
  id,
  theme,
  bounds,
  labName = "OpenAI Newsroom",
  announcementHeadline = "o3-mini Released Globally with High Reasoning Effort",
  releaseDate = "OFFICIAL DROP",
  modelVersion = "o3-mini",
  metrics = [
    { label: "Math & Code", value: "88.2%", deltaText: "+7.4% vs o1-mini", isPositive: true },
    { label: "Token Pricing", value: "$1.10", deltaText: "-63% Cost Cut", isPositive: true },
    { label: "Inference Latency", value: "3.2s", deltaText: "2.8x Faster", isPositive: true },
    { label: "Context Window", value: "200K", deltaText: "Full Multimodal", isPositive: true },
  ],
  canonicalUrl = "openai.com/index/openai-o3-mini",
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
      {/* 1. Lab Branding Header & Pulse Beacon */}
      <div className="flex items-center justify-between border-b border-white/10 pb-3.5">
        <div className="flex items-center gap-3">
          <div className="w-3.5 h-3.5 rounded-full bg-rose-500 animate-pulse shadow-[0_0_12px_rgba(244,63,94,0.8)]" />
          <span className="text-[20px] font-mono font-black uppercase tracking-wider text-white">
            {labName}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-full text-[14px] font-mono font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40 uppercase">
            {releaseDate}
          </span>
          <span
            className="px-3 py-1 rounded-full text-[14px] font-mono font-black uppercase"
            style={{
              backgroundColor: `${heroAccent}20`,
              color: heroAccent,
              border: `1px solid ${heroAccent}60`,
            }}
          >
            {modelVersion}
          </span>
        </div>
      </div>

      {/* 2. Headline */}
      <h3 className="text-[30px] font-black tracking-tight text-white leading-snug">
        {announcementHeadline}
      </h3>

      {/* 3. 4-Up High-Impact Specifications Grid */}
      <div className="grid grid-cols-2 gap-3.5 mt-1">
        {metrics.map((metric, idx) => (
          <div
            key={idx}
            className="p-3.5 rounded-2xl bg-slate-900/90 border border-slate-700/60 flex flex-col gap-1"
          >
            <span className="text-[14px] font-mono text-slate-400 uppercase font-semibold">
              {metric.label}
            </span>
            <div className="flex items-baseline justify-between mt-0.5">
              <span className="text-[32px] font-mono font-black text-white leading-none">
                {metric.value}
              </span>
              {metric.deltaText && (
                <span
                  className="text-[13px] font-mono font-bold"
                  style={{
                    color: metric.isPositive ? gainColor : "#EF4444",
                  }}
                >
                  {metric.deltaText}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* 4. Canonical Citation Footer */}
      <div className="mt-1 pt-3 border-t border-white/10 flex items-center justify-between text-[13px] font-mono text-slate-400">
        <span>Verified Primary Source:</span>
        <span className="text-sky-300 font-semibold">{canonicalUrl}</span>
      </div>
    </div>
  );
};
