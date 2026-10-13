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
  spotlightY = 750,
  vignetteIntensity = 0.4,
}) => {
  const voidColor = theme?.colors.canvas_void || "#06080F";
  const heroAccent = theme?.colors.hero_accent || "#38BDF8";
  const secondaryAccent = theme?.colors.secondary_accent || "#10B981";

  return (
    <div
      className="absolute inset-0 w-[1080px] h-[1920px] overflow-hidden pointer-events-none select-none z-0"
      style={{ backgroundColor: voidColor }}
    >
      {/* 1. L1 Recessed Subsurface with subtle 32px Dot-Matrix Grid */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage: `radial-gradient(circle, rgba(255, 255, 255, 0.12) 1.5px, transparent 1.5px)`,
          backgroundSize: "32px 32px",
        }}
      />

      {/* 2. Primary Volumetric Hero Spotlight Glow */}
      <div
        className="absolute w-[950px] h-[950px] rounded-full blur-[150px] pointer-events-none -translate-x-1/2 -translate-y-1/2"
        style={{
          left: `${spotlightX}px`,
          top: `${spotlightY}px`,
          background: `radial-gradient(circle, ${heroAccent}33 0%, ${heroAccent}15 45%, transparent 75%)`,
          opacity: vignetteIntensity,
        }}
      />

      {/* 3. Secondary Warm/Cool Ambient Fill in Lower Third to prevent dead void */}
      <div
        className="absolute w-[1100px] h-[700px] rounded-full blur-[140px] pointer-events-none -translate-x-1/2"
        style={{
          left: "540px",
          top: "1350px",
          background: `radial-gradient(ellipse at center, ${heroAccent}2b 0%, ${secondaryAccent}22 45%, rgba(15, 23, 42, 0.35) 70%, transparent 90%)`,
        }}
      />

      {/* 4. Perspective Floor Grid in Lower Horizon (Y: 1350px - 1920px) */}
      <div
        className="absolute bottom-0 left-[-200px] right-[-200px] h-[580px] pointer-events-none opacity-60"
        style={{
          perspective: "450px",
          maskImage: "linear-gradient(to top, rgba(0,0,0,0.95) 10%, rgba(0,0,0,0.45) 70%, transparent 100%)",
          WebkitMaskImage: "linear-gradient(to top, rgba(0,0,0,0.95) 10%, rgba(0,0,0,0.45) 70%, transparent 100%)",
        }}
      >
        <div
          className="w-full h-full"
          style={{
            transform: "rotateX(68deg)",
            transformOrigin: "bottom center",
            backgroundImage: `linear-gradient(to right, rgba(56, 189, 248, 0.4) 1.5px, transparent 1.5px),
                              linear-gradient(to bottom, rgba(56, 189, 248, 0.4) 1.5px, transparent 1.5px)`,
            backgroundSize: "44px 44px",
          }}
        />
      </div>

      {/* 5. Deep Cinematic Ambient Vignette around canvas borders */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse at 50% 48%, transparent 42%, rgba(3, 7, 18, 0.75) 100%)",
        }}
      />
    </div>
  );
};

