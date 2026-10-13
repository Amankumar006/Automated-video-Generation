import React from "react";
import { ThemeTokens, BoundingBoxPx } from "../types/vsg-ir";

export interface GlassHUDCardProps {
  id?: string;
  theme?: ThemeTokens;
  bounds?: BoundingBoxPx;
  title?: string;
  subtitle?: string;
  badge?: string;
  badgeColor?: string;
  bodyText?: string;
  isHeroFocus?: boolean;
  elevation?: "L2" | "L3" | "L4";
  children?: React.ReactNode;
}

export const GlassHUDCard: React.FC<GlassHUDCardProps> = ({
  id,
  theme,
  bounds,
  title,
  subtitle,
  badge,
  badgeColor,
  bodyText,
  isHeroFocus = false,
  elevation = "L2",
  children,
}) => {
  const surfacePrimary = theme?.colors.surface_primary || "rgba(15, 23, 42, 0.82)";
  const heroAccent = theme?.colors.hero_accent || "#38BDF8";
  const blurPx = theme?.materials.card_blur_px ?? 24;
  const radiusPx = theme?.materials.border_radius_px ?? 20;

  const cardStyle: React.CSSProperties = {
    position: bounds ? "absolute" : "relative",
    ...(bounds && {
      left: `${bounds.x_min_px}px`,
      top: `${bounds.y_min_px}px`,
      width: `${bounds.width_px}px`,
      height: bounds.height_px > 0 ? `${bounds.height_px}px` : "auto",
    }),
    backgroundColor: surfacePrimary,
    backdropFilter: `blur(${blurPx}px)`,
    WebkitBackdropFilter: `blur(${blurPx}px)`,
    borderRadius: `${radiusPx}px`,
    borderWidth: "1.5px",
    borderStyle: "solid",
    borderColor: isHeroFocus
      ? `${heroAccent}99`
      : "rgba(255, 255, 255, 0.14)",
    boxShadow: isHeroFocus
      ? `0 24px 48px -12px rgba(0, 0, 0, 0.75), 0 0 35px -5px ${heroAccent}40`
      : "0 24px 48px -12px rgba(0, 0, 0, 0.65)",
    transition: "transform 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
  };

  return (
    <div
      id={id}
      style={cardStyle}
      className={`p-6 flex flex-col justify-between overflow-hidden select-none z-10 ${
        isHeroFocus ? "scale-[1.02]" : "opacity-95"
      }`}
    >
      {/* Overhead Keylight Hairline Glow */}
      <div
        className="absolute top-0 left-0 right-0 h-[1.5px] pointer-events-none"
        style={{
          background: isHeroFocus
            ? `linear-gradient(90deg, transparent 0%, ${heroAccent} 50%, transparent 100%)`
            : "linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.25) 50%, transparent 100%)",
        }}
      />

      {/* Header with Title and Optional Badge */}
      {(title || badge) && (
        <div className="flex items-center justify-between gap-3 mb-3">
          {title && (
            <h3 className="text-[32px] font-extrabold tracking-tight text-white leading-tight">
              {title}
            </h3>
          )}
          {badge && (
            <span
              className="px-3 py-1 rounded-full text-[18px] font-mono font-bold tracking-widest uppercase"
              style={{
                backgroundColor: badgeColor
                  ? `${badgeColor}22`
                  : "rgba(56, 189, 248, 0.15)",
                color: badgeColor || heroAccent,
                border: `1px solid ${badgeColor ? `${badgeColor}66` : `${heroAccent}44`}`,
              }}
            >
              {badge}
            </span>
          )}
        </div>
      )}

      {subtitle && (
        <h4 className="text-[22px] font-bold text-slate-300 tracking-normal mb-2 leading-snug">
          {subtitle}
        </h4>
      )}

      {bodyText && (
        <p className="text-[20px] font-medium text-slate-300/90 leading-relaxed line-clamp-3">
          {bodyText}
        </p>
      )}

      {children && <div className="mt-3 flex-1 flex flex-col">{children}</div>}
    </div>
  );
};
