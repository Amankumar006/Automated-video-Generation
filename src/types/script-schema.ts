import { z } from "zod";

export const SceneTypeSchema = z.enum([
  "HOOK_TITLE",
  "ARCHITECTURE_OVERVIEW",
  "ROUTING_DEEPDIVE",
  "BENCHMARK_SHOWDOWN",
  "OUTRO_LOOP",
]);

export type SceneType = z.infer<typeof SceneTypeSchema>;

export const SceneNarrationSchema = z.object({
  sceneId: SceneTypeSchema,
  narrationText: z.string().describe("Concise 8-12 second voiceover script for this scene."),
  highlightTokens: z.array(z.string()).describe("Key phrases to emphasize visually."),
});

export type SceneNarration = z.infer<typeof SceneNarrationSchema>;

export const VideoNarrationProjectSchema = z.object({
  slug: z.string(),
  headlineHook: z.string().describe("Punchy 3-word title hook for mobile, e.g. 'THE 37B SECRET'"),
  scenes: z.array(SceneNarrationSchema).length(5),
  infiniteLoopEndingPhrase: z.string().describe("Closing half-sentence that loops seamlessly into headlineHook."),
});

export type VideoNarrationProject = z.infer<typeof VideoNarrationProjectSchema>;
