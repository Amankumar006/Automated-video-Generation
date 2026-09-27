import { VerifiedModelSpec } from "../types/model-spec.js";

export const DEEPSEEK_V3_SPEC: VerifiedModelSpec = {
  slug: "deepseek-v3",
  modelName: "DeepSeek-V3",
  creator: "DeepSeek AI",
  architectureType: "DeepSeekMoE",
  totalParams: "671B",
  activeParams: "37B",
  routedExperts: 256,
  sharedExperts: 1,
  activeRoutedPerToken: 8,
  routingAffinity: "Sigmoid Affinity + Bias Gate",
  contextWindow: "128k",
  benchmarks: {
    "MMLU-Pro": 75.9,
    "SWE-bench": 49.2,
    "MATH-500": 90.2,
    "GPQA Diamond": 59.1,
  },
  vramRequirements: {
    fp8: "360GB",
    int4: "180GB",
  },
};
