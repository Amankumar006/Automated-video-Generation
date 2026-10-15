import React from "react";
import { ThemeTokens, BoundingBoxPx } from "../types/vsg-ir";

export interface MetricPillProps {
  id?: string;
  theme?: ThemeTokens;
  bounds?: BoundingBoxPx;
  value?: string | number;
  label?: string;
  unit?: string;
  delta?: string;
  status?: "gain" | "loss" | "warning" | "neutral";
  size?: "hero" | "standard" | "compact";
}

export const MetricPill: React.FC<MetricPillProps> = ({
  id,
  theme,
  bounds,
  value = "0",
  label = "METRIC",
  unit,
  delta,
  status = "neutral",
  size = "standard",
}) => {
  const heroAccent = theme?.colors.hero_accent || "#38BDF8";
  const gainColor = theme?.colors.status_gain || "#10B981";
  const lossColor = theme?.colors.status_loss || "#EF4444";
  const warnColor = theme?.colors.status_warning || "#F59E0B";

  const statusColor =
    status === "gain"
      ? gainColor
      : status === "loss"
      ? lossColor
      : status === "warning"
      ? warnColor
      : heroAccent;

  const isHero = size === "hero";
  const isCompact = size === "compact";

  const containerStyle: React.CSSProperties = {
    position: bounds ? "absolute" : "relative",
    ...(bounds && {
      left: `${bounds.x_min_px}px`,
      top: `${bounds.y_min_px}px`,
      width: `${bounds.width_px}px`,
      height: bounds.height_px > 0 ? `${bounds.height_px}px` : "auto",
    }),
    fontVariantNumeric: "tabular-nums",
  };

  return (
    <div
      id={id}
      style={containerStyle}
      className={`rounded-2xl border flex flex-col justify-center select-none backdrop-blur-md ${
        isHero
          ? "px-8 py-6 bg-slate-900/90 border-slate-700 shadow-2xl"
          : isCompact
          ? "px-4 py-2 bg-slate-900/80 border-slate-700/80"
          : "px-6 py-4 bg-slate-900/85 border-slate-700/90 shadow-lg"
      }`}
    >
      <div className="flex items-baseline justify-between gap-4">
        <div className="flex items-baseline gap-2">
          <span
            className={`font-mono font-black tracking-tight text-white ${
              isHero ? "text-[72px]" : isCompact ? "text-[28px]" : "text-[44px]"
            }`}
            style={{
              textShadow: `0 0 20px ${statusColor}33`,
            }}
          >
            {value}
          </span>
          {unit && (
            <span
              className={`font-mono font-bold uppercase ${
                isHero ? "text-[28px]" : "text-[20px]"
              }`}
              style={{ color: statusColor }}
            >
              {unit}
            </span>
          )}
        </div>

        {delta && (
          <span
            className="px-2.5 py-1 rounded-full text-[16px] font-mono font-bold tracking-wider"
            style={{
              backgroundColor: `${statusColor}22`,
              color: statusColor,
              border: `1px solid ${statusColor}44`,
            }}
          >
            {delta}
          </span>
        )}
      </div>

      <span
        className={`font-mono tracking-wider uppercase font-semibold text-slate-400 mt-1 ${
          isHero ? "text-[20px]" : "text-[16px]"
        }`}
      >
        {label}
      </span>
    </div>
  );
};
