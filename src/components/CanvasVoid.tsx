import React from "react";
import { ThemeTokens } from "../types/vsg-ir";

export interface CanvasVoidProps {
  theme?: ThemeTokens;
  spotlightX?: number;
  spotlightY?: number;
  vignetteIntensity?: number;
}

export const CanvasVoid: React.FC<CanvasVoidProps> = ({
  theme,
  spotlightX = 540,
  spotlightY = 800,
  vignetteIntensity = 0.35,
}) => {
  const voidColor = theme?.colors.canvas_void || "#06080F";
  const heroAccent = theme?.colors.hero_accent || "#38BDF8";

  return (
    <div
      className="absolute inset-0 w-[1080px] h-[1920px] overflow-hidden pointer-events-none select-none z-0"
      style={{ backgroundColor: voidColor }}
    >
      {/* 1. L1 Recessed Subsurface with subtle 32px Dot-Matrix Grid */}
      <div
        className="absolute inset-0 opacity-25"
        style={{
          backgroundImage: `radial-gradient(circle, rgba(255, 255, 255, 0.12) 1.5px, transparent 1.5px)`,
          backgroundSize: "32px 32px",
        }}
      />

      {/* 2. Volumetric Focal Spotlight Vignette */}
      <div
        className="absolute w-[800px] h-[800px] rounded-full blur-[140px] pointer-events-none -translate-x-1/2 -translate-y-1/2"
        style={{
          left: `${spotlightX}px`,
          top: `${spotlightY}px`,
          background: `radial-gradient(circle, ${heroAccent}26 0%, transparent 70%)`,
          opacity: vignetteIntensity,
        }}
      />

      {/* 3. Deep Cinematic Ambient Vignette around canvas borders */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 45%, rgba(0, 0, 0, 0.65) 100%)",
        }}
      />
    </div>
  );
};
