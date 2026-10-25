import React from "react";
import { AbsoluteFill, Audio, staticFile } from "remotion";
import { SpeculativeDecodingVisualizer } from "../components/SpeculativeDecodingVisualizer";
import { NaturalCaptions, CaptionPhrase } from "../components/NaturalCaptions";

const SPECULATIVE_PHRASES: CaptionPhrase[] = [
  { text: "Here is the trick", start: 0.02, end: 0.755 },
  { text: "behind speculative decoding", start: 0.755, end: 2.255 },
  { text: "A small draft model", start: 2.255, end: 3.15 },
  { text: "quickly guesses several next tokens", start: 3.15, end: 4.945 },
  { text: "like the next token is", start: 4.945, end: 5.979 },
  { text: "Then the larger model checks", start: 5.979, end: 7.335 },
  { text: "that whole guess in one parallel pass", start: 7.335, end: 9.11 },
  { text: "If the guesses match, we keep them all", start: 9.11, end: 10.805 },
  { text: "If one is wrong, we discard only that token", start: 10.805, end: 12.81 },
  { text: "and continue from there", start: 12.81, end: 14.0 },
  { text: "So the big model still protects the answer", start: 14.0, end: 15.975 },
  { text: "while the small model saves repeated expensive steps", start: 15.975, end: 18.605 },
  { text: "Same quality, fewer slow trips", start: 18.605, end: 19.96 },
];

export const SpeculativeDecodingPreview: React.FC = () => (
  <AbsoluteFill className="bg-[#081018]">
    <Audio src={staticFile("audio/speculative_decoding_long_kokoro.wav")} volume={1} />
    <SpeculativeDecodingVisualizer />
    <NaturalCaptions phrases={SPECULATIVE_PHRASES} />
  </AbsoluteFill>
);
