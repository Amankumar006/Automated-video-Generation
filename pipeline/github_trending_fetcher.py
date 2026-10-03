"""
The Model Verse — GitHub Trending AI & Open-Source Kernel Ingestion Engine
Fetches viral open-source AI repositories (vLLM, SGLang, BitNet, llama.cpp, DeepSeek kernels),
extracts architectural innovations and core execution code snippets, and structures them for
high-dopamine Manim chalkboard code and AST visualizations.
"""

import os
import re
import json
import urllib.request
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class CodeKernelSnippet:
    filename: str
    language: str
    lines: List[str]
    highlight_lines: List[int] = field(default_factory=list)
    trace_register: str = ""
    explanation: str = ""


@dataclass
class TrendingRepo:
    repo_name: str
    title: str
    description: str
    stars: int
    language: str
    url: str
    topics: List[str]
    code_kernel: CodeKernelSnippet
    source: str = "github_api"

    def to_spec_candidate(self) -> Dict[str, Any]:
        """Converts repository record to an auto-producer candidate spec."""
        clean_id = re.sub(r"[^a-zA-Z0-9_]", "_", self.repo_name.replace("/", "_").replace("-", "_")).lower()
        return {
            "id": f"gh_{clean_id}",
            "title": self.title,
            "recommended_category": "mechanism_deepdive",
            "domain_taxonomy": "hardware_efficiency" if any(k in self.repo_name.lower() for k in ["vllm", "sglang", "kernel", "cuda", "bitnet"]) else "neural_attention",
            "abstract": f"{self.description} Key open-source repository: {self.repo_name} with {self.stars:,} GitHub stars.",
            "repo_metadata": {
                "repo_name": self.repo_name,
                "stars": self.stars,
                "language": self.language,
                "url": self.url
            },
            "code_snippet": asdict(self.code_kernel),
            "editorial_notes": {
                "recommended_hook": f"How {self.repo_name.split('/')[-1]} actually runs inside your GPU memory",
                "suggested_everyday_analogy": "A shared filing cabinet where identical papers are never photocopied twice"
            }
        }


# Curated high-impact architectural code snippets for viral AI repos
CURATED_AI_KERNELS = {
    "sgl-project/sglang": CodeKernelSnippet(
        filename="radix_cache.py",
        language="python",
        lines=[
            "def match_prefix(self, prompt_tokens):",
            "    node = self.root",
            "    for token in prompt_tokens:",
            "        if token in node.children:",
            "            node = node.children[token]  # Hit",
            "    return node.kv_cache_pointer"
        ],
        highlight_lines=[4, 5],
        trace_register="⚡ RADIX HIT: +2,048 TOKENS REUSED",
        explanation="RadixAttention reuses KV-cache trees across branching LLM calls for 5x throughput."
    ),
    "vllm-project/vllm": CodeKernelSnippet(
        filename="paged_attention.cu",
        language="cuda",
        lines=[
            "__global__ void paged_attention_kernel(",
            "    const float* __restrict__ Q,",
            "    const int* __restrict__ block_tables,",
            "    float* __restrict__ out) {",
            "  int block_idx = block_tables[seq_id];",
            "  fetch_kv_block(block_idx, shared_kv);",
            "}"
        ],
        highlight_lines=[5, 6],
        trace_register="⚡ ZERO VRAM FRAGMENTATION (O(1))",
        explanation="PagedAttention partitions continuous KV-cache into discrete virtual memory blocks."
    ),
    "microsoft/bitnet": CodeKernelSnippet(
        filename="bitlinear.py",
        language="python",
        lines=[
            "def forward(self, x):",
            "    # Quantize weights to {-1, 0, +1}",
            "    w_scale = self.weight.abs().mean()",
            "    w_quant = (self.weight / w_scale).round()",
            "    w_ternary = w_quant.clamp(-1, 1)",
            "    return ternary_gemm(x, w_ternary)"
        ],
        highlight_lines=[4, 5],
        trace_register="⚡ 1.58-BIT GEMM: ZERO FP16 MULTIPLY",
        explanation="BitLinear eliminates power-hungry multiplications, replacing them with simple integer additions."
    ),
    "ggerganov/llama.cpp": CodeKernelSnippet(
        filename="ggml_quants.c",
        language="c",
        lines=[
            "void dequantize_row_q4_0(",
            "    const block_q4_0* __restrict__ x,",
            "    float* __restrict__ y, int k) {",
            "  float d = x->d;  // block scale",
            "  for (int i = 0; i < 16; ++i) {",
            "    y[i] = ((x->qs[i] & 0x0F) - 8) * d;",
            "  }",
            "}"
        ],
        highlight_lines=[4, 6],
        trace_register="⚡ 4-BIT SIMD: 3.8x CPU SPEEDUP",
        explanation="llama.cpp packs two 4-bit nibbles per byte, streaming integer SIMD directly to CPU registers."
    ),
    "deepseek-ai/deepseek-v3": CodeKernelSnippet(
        filename="mla_attention.py",
        language="python",
        lines=[
            "def forward_mla(self, x):",
            "    # Multi-head Latent Compression",
            "    c_kv = self.w_dkv(x)  # Compress 8x",
            "    k_rope = self.w_k_rope(x)",
            "    k = torch.cat([self.w_uk(c_kv), k_rope])",
            "    return scaled_dot_product(q, k, v)"
        ],
        highlight_lines=[3, 5],
        trace_register="⚡ 93.3% KV-CACHE COMPRESSION",
        explanation="Multi-Head Latent Attention compresses key-value vectors into low-dimensional latent subspaces."
    )
}


class GitHubTrendingFetcher:
    """
    Fetches trending open-source AI repositories and extracts core
    code execution kernels for automated video shorts production.
    """

    SEARCH_API_URL = "https://api.github.com/search/repositories"

    AI_TOPIC_QUERIES = [
        "topic:llm+stars:>1000",
        "topic:inference+language:python",
        "topic:cuda+stars:>500",
        "topic:deep-learning+pushed:>2024-01-01"
    ]

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": "TheModelVerse-Pipeline/2.0 (contact@themodelverse.ai)",
            "Accept": "application/vnd.github.v3+json"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def extract_kernel_from_readme(self, repo_name: str, readme_text: str) -> CodeKernelSnippet:
        """Parses README markdown to locate the primary Python or CUDA code snippet."""
        # Check if known curated kernel exists
        repo_lower = repo_name.lower().strip()
        for k, snippet in CURATED_AI_KERNELS.items():
            if k in repo_lower or repo_lower in k:
                return snippet

        # Fallback: Extract code block from README
        match = re.search(r"```(python|cuda|c\+\+|cpp)\s*([\s\S]*?)```", readme_text, re.IGNORECASE)
        if match:
            lang = match.group(1).lower()
            raw_lines = [l.rstrip() for l in match.group(2).splitlines() if l.strip()]
            # Filter clean lines
            valid_lines = [l[:36] for l in raw_lines if not l.startswith(("#", "//", "import", "from"))][:6]
            if len(valid_lines) >= 3:
                return CodeKernelSnippet(
                    filename="core_kernel.py" if "py" in lang else "kernel.cu",
                    language=lang,
                    lines=valid_lines,
                    highlight_lines=[1, 2],
                    trace_register="⚡ OPEN-SOURCE EXECUTION KERNEL",
                    explanation=f"Core algorithmic loop extracted from {repo_name}."
                )

        # Default fallback snippet
        return CodeKernelSnippet(
            filename="kernel_pipeline.py",
            language="python",
            lines=[
                "def execute_step(tensor_in):",
                "    stream = init_cuda_stream()",
                "    out = fused_forward_pass(tensor_in)",
                "    return synchronize(stream, out)"
            ],
            highlight_lines=[2, 3],
            trace_register="⚡ FUSED HARDWARE PIPELINE",
            explanation=f"High-efficiency computational pipeline for {repo_name}."
        )

    def fetch_trending_repos(self, limit: int = 5) -> List[TrendingRepo]:
        """
        Queries GitHub API for top trending AI/ML repositories,
        falling back gracefully to curated breakthroughs on rate limit.
        """
        results: List[TrendingRepo] = []
        req_url = f"{self.SEARCH_API_URL}?q=topic:llm+stars:>1000&sort=stars&order=desc&per_page={limit}"

        try:
            req = urllib.request.Request(req_url, headers=self._get_headers())
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("items", [])
                for item in items[:limit]:
                    full_name = item.get("full_name", "")
                    desc = item.get("description") or f"Open-source AI innovation: {full_name}"
                    stars = item.get("stargazers_count", 0)
                    lang = item.get("language") or "Python"
                    url = item.get("html_url", "")
                    topics = item.get("topics", [])
                    kernel = self.extract_kernel_from_readme(full_name, desc)
                    
                    results.append(TrendingRepo(
                        repo_name=full_name,
                        title=f"{full_name.split('/')[-1]}: {desc[:48].strip()}",
                        description=desc,
                        stars=stars,
                        language=lang,
                        url=url,
                        topics=topics,
                        code_kernel=kernel,
                        source="github_search_api"
                    ))
        except Exception as e:
            print(f"⚠️ GitHub API query notice ({e}). Falling back to curated trending AI breakthroughs.")

        # If API returned fewer items than requested or hit rate limit, augment with curated SOTA
        if len(results) < limit:
            curated_defaults = [
                ("sgl-project/sglang", "SGLang: Fast Serving Framework for LLMs and VLMs", 14500, "Python", ["llm", "inference", "radix-attention"]),
                ("vllm-project/vllm", "vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention", 42000, "Python", ["llm", "paged-attention", "cuda"]),
                ("microsoft/bitnet", "BitNet: 1-bit LLMs for Fast Hardware Inference", 18500, "Python", ["1-bit", "quantization", "efficiency"]),
                ("deepseek-ai/deepseek-v3", "DeepSeek-V3: Multi-Head Latent Attention Open Weights", 68000, "Python", ["moe", "mla", "open-weights"]),
                ("ggerganov/llama.cpp", "llama.cpp: Port of Facebook's LLaMA model in C/C++", 72000, "C++", ["cpu", "quantization", "inference"])
            ]
            seen_names = {r.repo_name for r in results}
            for name, desc, stars, lang, topics in curated_defaults:
                if name not in seen_names and len(results) < limit:
                    kernel = CURATED_AI_KERNELS.get(name, self.extract_kernel_from_readme(name, desc))
                    results.append(TrendingRepo(
                        repo_name=name,
                        title=f"{name.split('/')[-1]}: {desc[:48].strip()}",
                        description=desc,
                        stars=stars,
                        language=lang,
                        url=f"https://github.com/{name}",
                        topics=topics,
                        code_kernel=kernel,
                        source="curated_trending"
                    ))

        return results[:limit]


def get_trending_github_digest(limit: int = 5) -> List[Dict[str, Any]]:
    """Helper entrypoint for daily shorts daemon to ingest trending open-source AI candidates."""
    fetcher = GitHubTrendingFetcher()
    repos = fetcher.fetch_trending_repos(limit=limit)
    return [r.to_spec_candidate() for r in repos]
