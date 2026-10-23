import React from "react";
import { AbsoluteFill, Audio, staticFile } from "remotion";
import { SpeculativeDecodingVisualizer } from "../components/SpeculativeDecodingVisualizer";
import { KineticCaptions } from "../components/KineticCaptions";
import { WordToken } from "../types/aligner";

const SPECULATIVE_WORDS: WordToken[] = [
  { word: "A", start: 0.01, end: 0.14 },
  { word: "fast", start: 0.14, end: 0.42 },
  { word: "draft", start: 0.42, end: 0.68 },
  { word: "model", start: 0.68, end: 1.035 },
  { word: "guesses", start: 1.035, end: 1.385 },
  { word: "the", start: 1.385, end: 1.655 },
  { word: "next", start: 1.655, end: 1.815 },
  { word: "tokens.", start: 1.815, end: 2.2 },
  { word: "A", start: 2.2, end: 2.295 },
  { word: "bigger", start: 2.295, end: 2.695 },
  { word: "model", start: 2.695, end: 2.985 },
  { word: "checks", start: 2.985, end: 3.36 },
  { word: "the", start: 3.36, end: 3.59 },
  { word: "guess", start: 3.59, end: 3.815 },
  { word: "in", start: 3.815, end: 4.008 },
  { word: "one", start: 4.008, end: 4.155 },
  { word: "batch.", start: 4.155, end: 4.516 },
  { word: "Correct", start: 4.516, end: 4.96 },
  { word: "guesses", start: 4.96, end: 5.485 },
  { word: "skip", start: 5.485, end: 5.72 },
  { word: "expensive", start: 5.72, end: 6.285 },
  { word: "work.", start: 6.285, end: 6.483 },
  { word: "That", start: 6.483, end: 6.65 },
  { word: "is", start: 6.65, end: 6.825 },
  { word: "speculative", start: 6.825, end: 7.625 },
  { word: "decoding.", start: 7.625, end: 8.07 },
];

export const SpeculativeDecodingPreview: React.FC = () => (
  <AbsoluteFill className="bg-[#081018]">
    <Audio src={staticFile("audio/speculative_decoding_kokoro.wav")} volume={1} />
    <SpeculativeDecodingVisualizer />
    <KineticCaptions words={SPECULATIVE_WORDS} />
  </AbsoluteFill>
);
