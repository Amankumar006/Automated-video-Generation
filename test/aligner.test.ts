import { describe, it, expect } from "vitest";
import { foldCharactersToWords, ElevenLabsTimestamps } from "../src/types/aligner.js";

describe("foldCharactersToWords", () => {
  it("folds standard character timestamps into discrete words", () => {
    // "AI model"
    const mockData: ElevenLabsTimestamps = {
      characters: ["A", "I", " ", "m", "o", "d", "e", "l"],
      character_start_times_seconds: [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35],
      character_end_times_seconds:   [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4],
    };

    const result = foldCharactersToWords(mockData);

    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({
      word: "AI",
      start: 0.0,
      end: 0.1,
    });
    expect(result[1]).toEqual({
      word: "model",
      start: 0.15,
      end: 0.4,
    });
  });

  it("handles leading, trailing, and multiple consecutive whitespace characters", () => {
    // "   DeepSeek   "
    const mockData: ElevenLabsTimestamps = {
      characters: [" ", " ", "D", "e", "e", "p", "S", "e", "e", "k", " ", " "],
      character_start_times_seconds: [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55],
      character_end_times_seconds:   [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6],
    };

    const result = foldCharactersToWords(mockData);

    expect(result).toHaveLength(1);
    expect(result[0]).toEqual({
      word: "DeepSeek",
      start: 0.1,
      end: 0.5,
    });
  });

  it("preserves punctuation inside word tokens", () => {
    // "MoE, 256!"
    const mockData: ElevenLabsTimestamps = {
      characters: ["M", "o", "E", ",", " ", "2", "5", "6", "!"],
      character_start_times_seconds: [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4],
      character_end_times_seconds:   [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45],
    };

    const result = foldCharactersToWords(mockData);

    expect(result).toHaveLength(2);
    expect(result[0].word).toBe("MoE,");
    expect(result[1].word).toBe("256!");
  });

  it("returns empty array when given empty input", () => {
    const result = foldCharactersToWords({
      characters: [],
      character_start_times_seconds: [],
      character_end_times_seconds: [],
    });

    expect(result).toEqual([]);
  });
});
