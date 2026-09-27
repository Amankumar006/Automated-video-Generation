export interface WordToken {
  word: string;
  start: number; // in seconds
  end: number;   // in seconds
}

export interface ElevenLabsTimestamps {
  characters: string[];
  character_start_times_seconds: number[];
  character_end_times_seconds: number[];
}

/**
 * Folds character-level timestamps (such as from ElevenLabs TTS with-timestamps endpoint)
 * into discrete word tokens with start and end timestamps.
 */
export function foldCharactersToWords(data: ElevenLabsTimestamps): WordToken[] {
  const words: WordToken[] = [];
  let currentWord = "";
  let wordStart = -1;
  let wordEnd = -1;

  const count = data.characters.length;
  for (let i = 0; i < count; i++) {
    const char = data.characters[i];
    const start = data.character_start_times_seconds[i];
    const end = data.character_end_times_seconds[i];

    // Check for whitespace boundary
    if (/\s/.test(char)) {
      if (currentWord.trim().length > 0) {
        words.push({
          word: currentWord.trim(),
          start: wordStart,
          end: wordEnd,
        });
        currentWord = "";
        wordStart = -1;
      }
    } else {
      if (wordStart === -1) {
        wordStart = start;
      }
      wordEnd = end;
      currentWord += char;
    }
  }

  // Flush remaining trailing word
  if (currentWord.trim().length > 0) {
    words.push({
      word: currentWord.trim(),
      start: wordStart,
      end: wordEnd,
    });
  }

  return words;
}
