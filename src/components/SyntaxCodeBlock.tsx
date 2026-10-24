import React from "react";
import { ThemeTokens, BoundingBoxPx } from "../types/vsg-ir";

export interface CodeLine {
  num: number;
  tokens: { text: string; type?: "keyword" | "function" | "number" | "string" | "comment" | "plain" }[];
}

export interface SyntaxCodeBlockProps {
  id?: string;
  theme?: ThemeTokens;
  bounds?: BoundingBoxPx;
  filename?: string;
  language?: string;
  lines?: CodeLine[];
  rawCode?: string;
}

export const SyntaxCodeBlock: React.FC<SyntaxCodeBlockProps> = ({
  id,
  theme,
  bounds,
  filename = "kernel_moe.cu",
  language = "CUDA",
  lines,
  rawCode,
}) => {
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

  // Fallback parsed lines if rawCode passed
  const displayLines: CodeLine[] =
    lines ||
    (rawCode
      ? rawCode.split("\n").slice(0, 6).map((line, idx) => ({
          num: idx + 1,
          tokens: [{ text: line.slice(0, 36), type: "plain" }],
        }))
      : [
          {
            num: 1,
            tokens: [
              { text: "__global__ void ", type: "keyword" },
              { text: "moe_router", type: "function" },
              { text: "(", type: "plain" },
            ],
          },
          {
            num: 2,
            tokens: [
              { text: "  const float* ", type: "keyword" },
              { text: "hidden_states", type: "plain" },
              { text: ",", type: "plain" },
            ],
          },
          {
            num: 3,
            tokens: [
              { text: "  int* ", type: "keyword" },
              { text: "topk_indices", type: "plain" },
              { text: " // k=8", type: "comment" },
            ],
          },
          {
            num: 4,
            tokens: [
              { text: ") {", type: "plain" },
            ],
          },
          {
            num: 5,
            tokens: [
              { text: "  int tid = ", type: "keyword" },
              { text: "threadIdx.x", type: "function" },
              { text: ";", type: "plain" },
            ],
          },
          {
            num: 6,
            tokens: [
              { text: "  warp_topk_gemm", type: "function" },
              { text: "(tid, 256);", type: "number" },
            ],
          },
        ]);

  const getTokenColor = (type?: string) => {
    switch (type) {
      case "keyword":
        return "#EC4899"; // hyper fuchsia
      case "function":
        return heroAccent; // cyan
      case "number":
        return "#F59E0B"; // amber
      case "string":
        return "#10B981"; // neon mint
      case "comment":
        return "#64748B"; // slate muted
      default:
        return "#F1F5F9"; // crisp light
    }
  };

  return (
    <div
      id={id}
      style={containerStyle}
      className="rounded-3xl bg-slate-950/90 border-2 border-slate-700/80 backdrop-blur-2xl shadow-2xl overflow-hidden select-none z-20"
    >
      {/* Window Title Bar with Traffic Lights */}
      <div className="flex items-center justify-between px-6 py-3.5 bg-slate-900/80 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <div className="w-3.5 h-3.5 rounded-full bg-red-500/80" />
          <div className="w-3.5 h-3.5 rounded-full bg-yellow-500/80" />
          <div className="w-3.5 h-3.5 rounded-full bg-green-500/80" />
          <span className="ml-3 text-[18px] font-mono font-bold text-slate-300">
            {filename}
          </span>
        </div>
        <span className="px-2.5 py-0.5 rounded-md bg-slate-800 text-[14px] font-mono font-bold uppercase text-slate-400">
          {language}
        </span>
      </div>

      {/* Code Lines Body */}
      <div className="p-6 font-mono text-[24px] leading-[1.5] space-y-2">
        {displayLines.map((line) => (
          <div key={line.num} className="flex items-start gap-4">
            <span className="w-8 text-right text-slate-600 select-none text-[20px]">
              {line.num}
            </span>
            <div className="flex-1 overflow-hidden whitespace-pre">
              {line.tokens.map((tok, tIdx) => (
                <span
                  key={tIdx}
                  style={{ color: getTokenColor(tok.type) }}
                  className="font-medium"
                >
                  {tok.text}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
