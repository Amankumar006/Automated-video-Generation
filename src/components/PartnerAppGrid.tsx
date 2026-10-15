import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { ThemeTokens, BoundingBoxPx } from "../types/vsg-ir";

export interface PartnerPerkItem {
  name: string;
  grantValue: string;
  category: string;
  highlightColor?: string;
  isHero?: boolean;
}

export interface PartnerAppGridProps {
  id?: string;
  theme?: ThemeTokens;
  bounds?: BoundingBoxPx;
  title?: string;
  subtitle?: string;
  partners?: PartnerPerkItem[];
}

export const PartnerAppGrid: React.FC<PartnerAppGridProps> = ({
  id,
  theme,
  bounds,
  title = "Active Ecosystem Grants",
  subtitle = "Stackable founder tiers available today",
  partners = [
    { name: "Anthropic Claude", grantValue: "$1,000", category: "API Credits", highlightColor: "#38BDF8", isHero: true },
    { name: "AWS Activate", grantValue: "$25,000", category: "Compute Tier", highlightColor: "#F59E0B" },
    { name: "Stripe Atlas", grantValue: "$5,000", category: "Waived Processing", highlightColor: "#8B5CF6" },
    { name: "GitHub Copilot", grantValue: "1-Yr Free", category: "Developer Seats", highlightColor: "#10B981" },
  ],
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
        <span className="px-3 py-1 rounded-full text-[14px] font-mono font-bold bg-sky-500/20 text-sky-400 border border-sky-500/40 uppercase">
          PERK MATRIX
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3.5 mt-1">
        {partners.map((partner, idx) => {
          const itemSpring = spring({
            frame: frame - idx * 4,
            fps,
            config: { damping: 14, stiffness: 120 },
          });

          const color = partner.highlightColor || heroAccent;

          return (
            <div
              key={idx}
              className={`p-4 rounded-2xl border-2 flex flex-col justify-between gap-3 transition-transform ${
                partner.isHero
                  ? "bg-slate-900 border-sky-500/60 shadow-[0_0_20px_rgba(56,189,248,0.25)]"
                  : "bg-slate-900/70 border-slate-700/60"
              }`}
              style={{
                transform: `scale(${Math.max(0, itemSpring)})`,
                opacity: Math.max(0, Math.min(1, itemSpring)),
              }}
            >
              <div className="flex items-center justify-between">
                <span className="text-[18px] font-bold text-white truncate">
                  {partner.name}
                </span>
                <span className="text-[12px] font-mono text-slate-400 uppercase">
                  {partner.category}
                </span>
              </div>

              <div className="flex items-baseline justify-between mt-1">
                <span
                  className="text-[30px] font-black font-mono leading-none"
                  style={{ color }}
                >
                  {partner.grantValue}
                </span>
                <span className="text-[12px] font-mono font-bold text-emerald-400">
                  APPROVED
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-2 pt-3 border-t border-white/10 flex items-center justify-between text-[14px] font-mono text-slate-400">
        <span>Combined Stack Value:</span>
        <span className="font-bold text-emerald-400 text-[18px]">
          $31,000+ Available Value
        </span>
      </div>
    </div>
  );
};
