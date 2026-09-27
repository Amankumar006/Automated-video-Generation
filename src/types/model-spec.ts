import { z } from "zod";

export const VerifiedModelSpecSchema = z.object({
  slug: z.string(),
  modelName: z.string(),
  creator: z.string(),
  architectureType: z.enum(["Dense", "DeepSeekMoE", "MixtralMoE", "StateSpace"]),
  totalParams: z.string().describe("Total parameter count, e.g. 671B"),
  activeParams: z.string().describe("Active parameter count per token, e.g. 37B"),
  routedExperts: z.number().int().describe("Number of routed experts in MoE pool, e.g. 256"),
  sharedExperts: z.number().int().describe("Number of always-active shared experts, e.g. 1"),
  activeRoutedPerToken: z.number().int().describe("Number of routed experts activated per token, e.g. 8"),
  routingAffinity: z.string().describe("Mathematical gating formula, e.g. Sigmoid Affinity + Load-Balancing Bias"),
  contextWindow: z.string().describe("Supported context length, e.g. 128k"),
  benchmarks: z.record(z.string(), z.number()).describe("Verified benchmark results, e.g. MMLU-Pro, SWE-bench"),
  vramRequirements: z.object({
    fp8: z.string().describe("VRAM required in FP8 precision"),
    int4: z.string().describe("VRAM required in INT4 precision"),
  }),
});

export type VerifiedModelSpec = z.infer<typeof VerifiedModelSpecSchema>;
