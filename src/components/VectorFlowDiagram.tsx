import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { ThemeTokens, BoundingBoxPx } from "../types/vsg-ir";

export interface FlowStep {
  id: string;
  label: string;
  sublabel?: string;
  isActive?: boolean;
}

export interface VectorFlowDiagramProps {
  id?: string;
  theme?: ThemeTokens;
  bounds?: BoundingBoxPx;
  title?: string;
  steps?: FlowStep[];
}

export const VectorFlowDiagram: React.FC<VectorFlowDiagramProps> = ({
  id,
  theme,
  bounds,
  title = "Inference Execution Pipeline",
  steps = [
    { id: "s1", label: "Prompt Ingestion", sublabel: "BPE Tokenizer" },
    { id: "s2", label: "KV Cache Lookup", sublabel: "MLA Decompress" },
    { id: "s3", label: "Sparse MoE Gating", sublabel: "Top-8 Dispatch", isActive: true },
    { id: "s4", label: "Logit Sampling", sublabel: "Next Token Output" },
  ],
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const heroAccent = theme?.colors.hero_accent || "#38BDF8";

  const pulse = interpolate(
    frame % Math.round(1.2 * fps),
    [0, Math.round(0.6 * fps), Math.round(1.2 * fps)],
    [0.7, 1.0, 0.7]
  );

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
      className="p-6 rounded-3xl bg-slate-950/85 border-2 border-slate-700/80 backdrop-blur-2xl shadow-2xl flex flex-col gap-4 select-none z-20"
    >
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <h3 className="text-[24px] font-extrabold text-white tracking-tight">
          {title}
        </h3>
        <span
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: heroAccent, opacity: pulse }}
        />
      </div>

      <div className="flex flex-col gap-3">
        {steps.map((step, idx) => {
          const active = !!step.isActive;
          return (
            <React.Fragment key={step.id}>
              <div
                className={`p-4 rounded-2xl flex items-center justify-between border transition-all ${
                  active
                    ? "bg-slate-900 border-2 shadow-[0_0_24px_rgba(56,189,248,0.3)]"
                    : "bg-slate-900/50 border-slate-800"
                }`}
                style={{
                  borderColor: active ? heroAccent : undefined,
                }}
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`w-7 h-7 rounded-full flex items-center justify-center font-mono font-bold text-[14px] ${
                      active
                        ? "bg-white text-black"
                        : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {idx + 1}
                  </span>
                  <div>
                    <h4
                      className={`text-[20px] font-bold ${
                        active ? "text-white" : "text-slate-300"
                      }`}
                    >
                      {step.label}
                    </h4>
                    {step.sublabel && (
                      <p className="text-[15px] font-mono text-slate-400">
                        {step.sublabel}
                      </p>
                    )}
                  </div>
                </div>

                {active && (
                  <span
                    className="px-2.5 py-0.5 rounded-full text-[13px] font-mono font-bold uppercase"
                    style={{
                      backgroundColor: `${heroAccent}22`,
                      color: heroAccent,
                      border: `1px solid ${heroAccent}66`,
                    }}
                  >
                    ACTIVE STAGE
                  </span>
                )}
              </div>

              {idx < steps.length - 1 && (
                <div className="flex justify-center -my-1">
                  <div
                    className="w-1 h-3 rounded-full"
                    style={{ backgroundColor: active ? heroAccent : "#334155" }}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
