"""
Test suite for GitHub Trending AI & Open-Source Kernel Ingestion Engine.
Verifies:
1. GitHubTrendingFetcher initialization and header formation.
2. Curated AI kernel extraction (SGLang, vLLM, BitNet, DeepSeek, llama.cpp).
3. Fallback extraction of code blocks from repository markdown.
4. TrendingRepo data structure and conversion to auto-producer candidate spec.
5. get_trending_github_digest pipeline helper.
"""

import sys
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.github_trending_fetcher import (
    GitHubTrendingFetcher,
    TrendingRepo,
    CodeKernelSnippet,
    CURATED_AI_KERNELS,
    get_trending_github_digest
)


def test_fetcher_initialization():
    fetcher = GitHubTrendingFetcher(token="mock_token_123")
    assert fetcher.token == "mock_token_123"
    headers = fetcher._get_headers()
    assert headers["Authorization"] == "token mock_token_123"
    assert "application/vnd.github.v3+json" in headers["Accept"]


def test_curated_kernels_presence():
    assert "sgl-project/sglang" in CURATED_AI_KERNELS
    assert "vllm-project/vllm" in CURATED_AI_KERNELS
    assert "microsoft/bitnet" in CURATED_AI_KERNELS
    assert "deepseek-ai/deepseek-v3" in CURATED_AI_KERNELS
    assert "ggerganov/llama.cpp" in CURATED_AI_KERNELS

    sgl = CURATED_AI_KERNELS["sgl-project/sglang"]
    assert sgl.language == "python"
    assert len(sgl.lines) >= 4
    assert "RADIX" in sgl.trace_register.upper()

    vllm = CURATED_AI_KERNELS["vllm-project/vllm"]
    assert vllm.language == "cuda"
    assert "block_tables" in "".join(vllm.lines)


def test_extract_kernel_curated_match():
    fetcher = GitHubTrendingFetcher()
    kernel = fetcher.extract_kernel_from_readme("vllm-project/vllm", "Fast LLM serving")
    assert kernel.language == "cuda"
    assert "paged_attention" in "".join(kernel.lines)


def test_extract_kernel_markdown_fallback():
    fetcher = GitHubTrendingFetcher()
    readme_sample = """
    # Awesome Model
    Fast fused kernel implementation:
    ```python
    def fused_forward(x, weights):
        hidden = matmul_ternary(x, weights)
        return silu_activation(hidden)
    ```
    """
    kernel = fetcher.extract_kernel_from_readme("unknown/cool-model", readme_sample)
    assert kernel.language == "python"
    assert len(kernel.lines) >= 3
    assert any("fused_forward" in l for l in kernel.lines)


def test_trending_repo_to_spec_candidate():
    snippet = CodeKernelSnippet(
        filename="kernel.py",
        language="python",
        lines=["def run():", "    return 42"],
        highlight_lines=[1],
        trace_register="⚡ REG_OK",
        explanation="Testing snippet"
    )
    repo = TrendingRepo(
        repo_name="org/awesome-cuda",
        title="Awesome CUDA: 10x faster GEMM",
        description="High throughput ternary GEMM kernel",
        stars=15420,
        language="C++",
        url="https://github.com/org/awesome-cuda",
        topics=["cuda", "kernel", "llm"],
        code_kernel=snippet
    )
    cand = repo.to_spec_candidate()
    assert cand["id"] == "gh_org_awesome_cuda"
    assert cand["title"] == "Awesome CUDA: 10x faster GEMM"
    assert cand["domain_taxonomy"] == "hardware_efficiency"
    assert "code_snippet" in cand
    assert cand["code_snippet"]["filename"] == "kernel.py"
    assert cand["repo_metadata"]["stars"] == 15420
    assert "recommended_hook" in cand["editorial_notes"]


def test_get_trending_github_digest():
    candidates = get_trending_github_digest(limit=3)
    assert len(candidates) == 3
    for c in candidates:
        assert str(c["id"]).startswith("gh_")
        assert "code_snippet" in c
        assert isinstance(c["code_snippet"]["lines"], list)
        assert len(c["code_snippet"]["lines"]) > 0
        assert "repo_metadata" in c
        assert c["repo_metadata"]["stars"] > 1000
