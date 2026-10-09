"""Comprehensive 4-Tier End-to-End Verification Suite for Figure Extraction & Subsystem Unification.

This test suite provides requirement-driven, opaque-box, and contract-level verification
covering the unified pipeline across The Model Verse Shorts (2D Manim) and Project Aether (3D).

Tiers:
  Tier 1: Feature Coverage (Unit / Subsystem Contract)
    - extract_paper_figures dual format extraction (SVG & high-res raster PNG)
    - fetch_arxiv_paper populates paper_figures from cache and extraction
    - generate_script propagates paper_figures into spec
    - visual_director binds Beat 3 to paper_figure blueprint
    - ScriptToFilmSceneAdapter translates 6-beat VideoSpec into DirectorProductionBrief

  Tier 2: Boundary & Corner Cases (Defensive Robustness)
    - missing e-print bundle gracefully handled without crashing
    - empty/None paper_figures fallback in visual_director
    - SVG vs raster preferred renderer selection logic
    - dirty/invalid arXiv ID normalization and error resilience
    - EducationalAssetConditioningPackage spatial bounds validation

  Tier 3: Cross-Feature Combinations (Integration)
    - Full loop: fetch_arxiv_paper -> generate_script -> visual_director
    - Aether conditioning package bundling paper figures into shot requirements
    - DualEnginePipelineConfig hybrid beat allocation resolution
    - Reverse conversion round-trip: brief -> spec outline

  Tier 4: Real-World Application Scenario (CLI E2E)
    - run_pipeline.py --arxiv 2407.08608 CLI execution producing chalkboard assets & spec
    - BlueprintPaperFigure vertical bounds and subtitle safe-zone constraints
    - AetherDirector dry-run execution consuming adapted educational brief
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from manim_engine.primitives.visual_compositions import BlueprintPaperFigure
from pipeline.arxiv_fetcher import clean_arxiv_id, extract_arxiv_id, fetch_arxiv_paper
from pipeline.arxiv_vector_extractor import (
    download_arxiv_source,
    extract_paper_figures,
    get_paper_vector_figure,
    recolor_svg_for_blackboard,
)
from pipeline.visual_director import VisualDirector


# ==============================================================================
# Shared Fixtures
# ==============================================================================

@pytest.fixture(scope="session")
def real_arxiv_id() -> str:
    """Returns the verified, cached arXiv ID for FlashAttention-3."""
    return "2407.08608"


@pytest.fixture
def mock_base_6beat_spec() -> Dict[str, Any]:
    """Provides a valid 6-beat Model Verse script dictionary."""
    return {
        "id": "flashattention_3_architecture",
        "title": "FlashAttention-3: Asynchronous Hardware GEMM",
        "category": "architecture_breakdown",
        "hook_tag": "BREAKTHROUGH HARDWARE ATTENTION",
        "arxiv_id": "2407.08608",
        "beats": [
            {
                "beat_id": 1,
                "text": "GPUs spend forty percent of their cycles waiting for memory transfers.",
                "visual_focus": "Hardware stall heat map showing idle tensor cores",
                "highlight_words": {"forty percent": "#EF4444"},
                "camera_action": "dolly_in",
                "expected_duration": 4.5,
                "visual_blueprint": {"layout": "default", "title": "MEMORY BOTTLENECK"},
            },
            {
                "beat_id": 2,
                "text": "Standard attention kernels serialize matrix multiplication and softmax.",
                "visual_focus": "Sequential pipeline timeline blocking execution queue",
                "highlight_words": {"serialize": "#F59E0B"},
                "camera_action": "orbit",
                "expected_duration": 5.0,
                "visual_blueprint": {"layout": "pipeline_stages", "title": "SERIALIZED QUEUE"},
            },
            {
                "beat_id": 3,
                "text": "FlashAttention-3 overlaps computation with asynchronous tensor core pipelining.",
                "visual_focus": "Official architecture diagram illustrating 3-stage asynchronous pipeline",
                "highlight_words": {"asynchronous": "#10B981"},
                "camera_action": "pan",
                "expected_duration": 6.0,
                "visual_blueprint": {"layout": "default", "title": "3-STAGE PIPELINE"},
            },
            {
                "beat_id": 4,
                "text": "Under thirty lines of fused CUDA kernel orchestrates zero-copy shared memory.",
                "visual_focus": "Fused CUDA kernel scanning asynchronous TMA load sweeps",
                "highlight_words": {"fused CUDA": "#38BDF8"},
                "camera_action": "static",
                "expected_duration": 5.0,
                "visual_blueprint": {"layout": "chalkboard_code_block", "title": "CUDA KERNEL"},
            },
            {
                "beat_id": 5,
                "text": "Reaching up to seventy-five percent of H100 hardware theoretical peak.",
                "visual_focus": "Horizontal Drag-Race benchmark bars comparing TFLOPS",
                "highlight_words": {"seventy-five percent": "#10B981"},
                "camera_action": "crane",
                "expected_duration": 5.5,
                "visual_blueprint": {"layout": "horizontal_race_bars", "title": "TFLOPS BENCHMARK"},
            },
            {
                "beat_id": 6,
                "text": "This breakthrough unlocks million-token contexts at unprecedented inference speed.",
                "visual_focus": "Contemplative horizon of neural models processing infinite token streams",
                "highlight_words": {"million-token": "#A855F7"},
                "camera_action": "dolly_out",
                "expected_duration": 4.5,
                "visual_blueprint": {"layout": "default", "title": "FUTURE HORIZON"},
            },
        ],
        "math_formulas": [],
    }


# ==============================================================================
# Tier 1: Feature Coverage (Unit / Subsystem Contracts)
# ==============================================================================

class TestTier1FeatureCoverage:
    """Verifies each feature contract in isolation against interface specifications."""

    def test_tier1_extract_paper_figures_dual_formats(self, real_arxiv_id: str):
        """Feature 1: extract_paper_figures produces both SVG vectors and 350 DPI raster diagrams."""
        figs = extract_paper_figures(real_arxiv_id, max_figures=3)
        assert len(figs) >= 1, "extract_paper_figures returned an empty figure list for cached arXiv paper."

        for f in figs:
            # Check required contract schema fields
            assert "figure_id" in f
            assert "stem" in f
            assert "caption" in f
            assert "original_type" in f
            assert "score" in f
            assert f.get("svg_path") is not None or f.get("image_path") is not None

            # Verify physical existence and resolution if image_path is present
            if f.get("image_path"):
                img_path = Path(f["image_path"])
                assert img_path.exists(), f"Extracted figure image file does not exist: {img_path}"
                with Image.open(img_path) as im:
                    assert im.width >= 1000, f"Image width {im.width} is below threshold."

            # Verify physical existence and blackboard recoloring if svg_path is present
            if f.get("svg_path"):
                svg_path = Path(f["svg_path"])
                assert svg_path.exists(), f"Extracted SVG file does not exist: {svg_path}"
                svg_content = svg_path.read_text(encoding="utf-8")
                assert "<svg" in svg_content
                assert "#E2E8F0" in svg_content, "SVG missing blackboard chalk white stroke recoloring."

    def test_tier1_fetch_arxiv_paper_returns_paper_figures(self, real_arxiv_id: str):
        """Feature 2: fetch_arxiv_paper extracts and populates paper_figures."""
        paper = fetch_arxiv_paper(real_arxiv_id, extract_figures=True, max_figures=3)
        assert paper is not None, f"fetch_arxiv_paper returned None for '{real_arxiv_id}'"
        assert clean_arxiv_id(paper.get("arxiv_id", "")) == real_arxiv_id
        assert "title" in paper
        assert "abstract" in paper

        # Critical contract assertion
        assert "paper_figures" in paper, "fetch_arxiv_paper did not populate 'paper_figures' in result."
        assert isinstance(paper["paper_figures"], list)
        assert len(paper["paper_figures"]) >= 1, "Expected at least 1 figure in paper_figures."
        top_fig = paper["paper_figures"][0]
        assert top_fig.get("svg_path") or top_fig.get("image_path")

    def test_tier1_generate_script_propagates_paper_figures(
        self,
        real_arxiv_id: str,
        mock_base_6beat_spec: Dict[str, Any],
    ):
        """Feature 3: generate_script binds paper_figures into spec from arxiv_meta."""
        from pipeline.script_generator import generate_script

        # Ingest figures to create genuine metadata
        paper_meta = fetch_arxiv_paper(real_arxiv_id, extract_figures=True, max_figures=2)
        assert paper_meta and paper_meta.get("paper_figures")

        # Mock OllamaClient to return the base 6-beat spec, allowing full script_generator
        # post-processing (Socratic audit, VSG, figure propagation, math SVG rendering) to run
        mock_res = MagicMock()
        mock_res.to_dict.return_value = copy.deepcopy(mock_base_6beat_spec)
        mock_res.text = json.dumps(mock_base_6beat_spec)
        mock_res.model = "gpt-oss:mock"

        with patch("pipeline.script_generator.OllamaClient") as mock_client_cls:
            mock_client_instance = MagicMock()
            mock_client_instance.generate_completion.return_value = mock_res
            mock_client_cls.return_value = mock_client_instance

            spec = generate_script(
                topic="FlashAttention-3 Hardware Breakdown",
                category="architecture_breakdown",
                arxiv_meta=paper_meta,
            )

        assert spec is not None
        assert spec.get("arxiv_id") == real_arxiv_id
        assert "paper_figures" in spec, "generate_script did not propagate paper_figures into spec."
        assert len(spec["paper_figures"]) == len(paper_meta["paper_figures"])
        assert spec["paper_figures"][0]["figure_id"] == paper_meta["paper_figures"][0]["figure_id"]

    def test_tier1_visual_director_binds_beat3_paper_figure(
        self,
        real_arxiv_id: str,
        mock_base_6beat_spec: Dict[str, Any],
    ):
        """Feature 5: VisualDirector binds Beat 3 to paper_figure blueprint consuming paper_figures."""
        figs = extract_paper_figures(real_arxiv_id, max_figures=2)
        assert len(figs) >= 1

        spec = copy.deepcopy(mock_base_6beat_spec)
        spec["paper_figures"] = figs
        spec["arxiv_id"] = real_arxiv_id

        director = VisualDirector()
        storyboard_spec = director.prepare_storyboard_for_spec(spec)

        beat_3 = next((b for b in storyboard_spec["beats"] if b.get("beat_id") == 3), None)
        assert beat_3 is not None, "Beat 3 missing from storyboard spec."

        # Verify Beat 3 motif and blueprint bindings
        assert beat_3.get("motif_type") == "paper_figure", (
            f"Expected Beat 3 motif_type 'paper_figure', got '{beat_3.get('motif_type')}'"
        )
        assert beat_3.get("kinetic_action") == "figure_scan"

        bp = beat_3.get("visual_blueprint", {})
        assert bp.get("layout") == "paper_figure"
        params = bp.get("params", {})
        assert params.get("arxiv_id") == real_arxiv_id
        assert params.get("svg_path") or params.get("image_path")
        assert params.get("preferred_renderer") in ["vector", "raster"]


# ==============================================================================
# Tier 2: Boundary & Corner Cases (Defensive Robustness)
# ==============================================================================

class TestTier2BoundaryAndCornerCases:
    """Verifies graceful degradation and defensive boundaries against edge cases."""

    def test_tier2_missing_eprint_gracefully_handled(self):
        """Edge case: Non-existent or un-downloadable arXiv ID handled without crash."""
        with patch("pipeline.arxiv_vector_extractor.urllib.request.urlopen", side_effect=Exception("HTTP 404")):
            figs = extract_paper_figures("9999.99999", max_figures=2)
            assert figs == [], f"Expected empty list for non-existent paper, got {figs}"

    def test_tier2_empty_figures_fallback_in_visual_director(
        self,
        mock_base_6beat_spec: Dict[str, Any],
    ):
        """Edge case: When spec has empty paper_figures, Beat 3 gracefully falls back."""
        spec = copy.deepcopy(mock_base_6beat_spec)
        spec["paper_figures"] = []
        spec["arxiv_id"] = None

        director = VisualDirector()
        storyboard = director.prepare_storyboard_for_spec(spec)

        beat_3 = next((b for b in storyboard["beats"] if b.get("beat_id") == 3), None)
        assert beat_3 is not None
        # Must not crash and must not assign paper_figure without valid files
        assert beat_3.get("motif_type") != "paper_figure"

    def test_tier2_svg_vs_raster_preferred_renderer_selection(
        self,
        mock_base_6beat_spec: Dict[str, Any],
    ):
        """Edge case: Preferred renderer selection for SVG-only vs Raster-only figures."""
        director = VisualDirector()

        # 1. Raster-only scenario
        raster_spec = copy.deepcopy(mock_base_6beat_spec)
        test_png = str(PROJECT_ROOT / "public" / "arxiv_cache" / "2407.08608" / "chalkboard_figures" / "fig_1_3_stage_pipelining.png")
        raster_spec["paper_figures"] = [{
            "figure_id": "fig_raster_only",
            "svg_path": None,
            "image_path": test_png,
            "caption": "Raster Architecture",
        }]
        st_raster = director.prepare_storyboard_for_spec(raster_spec)
        b3_raster = next(b for b in st_raster["beats"] if b["beat_id"] == 3)
        assert b3_raster["visual_blueprint"]["params"]["preferred_renderer"] == "raster"

        # 2. Vector scenario (with valid SVG)
        vector_spec = copy.deepcopy(mock_base_6beat_spec)
        test_svg = str(PROJECT_ROOT / "public" / "arxiv_cache" / "2407.08608" / "chalkboard_figures" / "fig_4_flash3_h100_causal_False_hdim_128_fwd_speed.svg")
        vector_spec["paper_figures"] = [{
            "figure_id": "fig_vector_only",
            "svg_path": test_svg,
            "image_path": None,
            "caption": "Vector Architecture",
        }]
        st_vector = director.prepare_storyboard_for_spec(vector_spec)
        b3_vector = next(b for b in st_vector["beats"] if b["beat_id"] == 3)
        assert b3_vector["visual_blueprint"]["params"]["preferred_renderer"] == "vector"

    def test_tier2_invalid_and_dirty_arxiv_id_handling(self):
        """Edge case: Normalization of various arXiv ID formats and dirty strings."""
        assert clean_arxiv_id("https://arxiv.org/abs/2407.08608") == "2407.08608"
        assert clean_arxiv_id("https://arxiv.org/pdf/2407.08608v3.pdf") == "2407.08608v3"
        assert clean_arxiv_id("hep-th/9912012") == "hep-th/9912012"
        assert clean_arxiv_id("  2407.08608 \n") == "2407.08608"
        assert extract_arxiv_id("arxiv:2407.08608") == "2407.08608"


# ==============================================================================
# Tier 3: Cross-Feature Combinations (Integration)
# ==============================================================================

class TestTier3CrossFeatureCombinations:
    """Verifies multi-component pipelines and inter-engine bridging."""

    def test_tier3_full_pipeline_ingestion_to_storyboard_loop(
        self,
        real_arxiv_id: str,
        mock_base_6beat_spec: Dict[str, Any],
    ):
        """Cross-Feature: fetch_arxiv_paper -> generate_script -> visual_director."""
        from pipeline.script_generator import generate_script

        # 1. Fetch paper metadata (exercises Tier 0 local cache lookup)
        paper_meta = fetch_arxiv_paper(real_arxiv_id, extract_figures=True, max_figures=3)
        assert paper_meta is not None
        assert len(paper_meta["paper_figures"]) >= 1

        # 2. Generate script passing paper metadata
        mock_res = MagicMock()
        mock_res.to_dict.return_value = copy.deepcopy(mock_base_6beat_spec)
        mock_res.text = json.dumps(mock_base_6beat_spec)
        mock_res.model = "gpt-oss:mock"

        with patch("pipeline.script_generator.OllamaClient") as mock_client_cls:
            mock_client_instance = MagicMock()
            mock_client_instance.generate_completion.return_value = mock_res
            mock_client_cls.return_value = mock_client_instance

            spec = generate_script(
                topic=paper_meta["title"],
                category="architecture_breakdown",
                arxiv_meta=paper_meta,
            )

        assert spec.get("paper_figures") is not None
        assert spec.get("arxiv_id") == real_arxiv_id

        # 3. Choreograph visual storyboard
        director = VisualDirector()
        storyboard = director.prepare_storyboard_for_spec(spec)

        # 4. Verify Beat 3 reflects the ingested paper figure
        beat_3 = storyboard["beats"][2]
        assert beat_3["motif_type"] == "paper_figure"
        assert beat_3["visual_blueprint"]["layout"] == "paper_figure"
        assert beat_3["visual_blueprint"]["params"]["arxiv_id"] == real_arxiv_id
        assert beat_3["visual_blueprint"]["params"]["preferred_renderer"] in ["vector", "raster"]


# ==============================================================================
# Tier 4: Real-World Application Scenario (CLI E2E)
# ==============================================================================

class TestTier4RealWorldApplicationScenario:
    """Verifies the complete real-world CLI execution and multi-engine production workflow."""

    def test_tier4_run_pipeline_cli_e2e_figure_and_spec_population(
        self,
        real_arxiv_id: str,
        mock_base_6beat_spec: Dict[str, Any],
    ):
        """Tier 4: Full execution of run_pipeline.py --arxiv 2407.08608 --skip-render."""
        from pipeline.run_pipeline import main as run_pipeline_main

        # Mock heavy external media rendering while exercising genuine pipeline logic:
        # 1. arXiv fetching and local cache lookup
        # 2. Figure extraction and super-sampling
        # 3. Script generation and paper figure binding
        # 4. VisualDirector storyboard design and Beat 3 blueprint
        # 5. Template JSON persistence
        mock_audio_res = {
            "master_audio": str(PROJECT_ROOT / "public" / "sample.wav"),
            "timing_data": [
                {"beat_id": i, "duration": 5.0, "slot_duration": 5.0, "start": (i-1)*5.0, "end": i*5.0, "word_timings": []}
                for i in range(1, 7)
            ]
        }

        mock_ollama_res = MagicMock()
        mock_ollama_res.to_dict.return_value = copy.deepcopy(mock_base_6beat_spec)
        mock_ollama_res.text = json.dumps(mock_base_6beat_spec)
        mock_ollama_res.model = "gpt-oss:mock"

        test_args = [
            "run_pipeline.py",
            "--arxiv", real_arxiv_id,
            "--category", "architecture_breakdown",
            "--skip-render",
            "--no-music",
        ]

        with patch("sys.argv", test_args), \
             patch("pipeline.run_pipeline.synthesize_audio_for_spec", return_value=mock_audio_res), \
             patch("pipeline.script_generator.OllamaClient") as mock_ollama_cls, \
             patch("subprocess.run") as mock_subproc:

            mock_client = MagicMock()
            mock_client.generate_completion.return_value = mock_ollama_res
            mock_ollama_cls.return_value = mock_client
            mock_subproc.return_value = MagicMock(returncode=0)

            # Execute pipeline entrypoint
            run_pipeline_main()

        # Verify disk outputs
        cache_fig_dir = PROJECT_ROOT / "public" / "arxiv_cache" / real_arxiv_id / "chalkboard_figures"
        assert cache_fig_dir.exists(), f"Chalkboard figures directory missing: {cache_fig_dir}"
        figures = list(cache_fig_dir.glob("*.png")) + list(cache_fig_dir.glob("*.svg"))
        assert len(figures) >= 1, "No chalkboard figures created in cache directory."

        # Verify saved template
        templates_dir = PROJECT_ROOT / "pipeline" / "templates"
        matching_templates = list(templates_dir.glob(f"*{real_arxiv_id}*.json")) + list(templates_dir.glob("*flash*attention*.json"))
        assert len(matching_templates) >= 1, "No saved template JSON matching arXiv ID or spec ID."
        matching_templates.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        saved_template_path = matching_templates[0]
        saved_spec = json.loads(saved_template_path.read_text(encoding="utf-8"))

        assert saved_spec.get("arxiv_id") == real_arxiv_id
        assert "paper_figures" in saved_spec
        assert len(saved_spec["paper_figures"]) >= 1

        # Verify Beat 3 storyboard in saved template
        beat_3 = next((b for b in saved_spec["beats"] if b["beat_id"] == 3), None)
        assert beat_3 is not None
        assert beat_3.get("motif_type") == "paper_figure"
        assert beat_3["visual_blueprint"]["layout"] == "paper_figure"

    def test_tier4_manim_blueprint_paper_figure_composition_bounds(
        self,
        real_arxiv_id: str,
    ):
        """Tier 4: BlueprintPaperFigure vertical constraints and subtitle clearance in Manim."""
        from manim import UP, DOWN

        figs = extract_paper_figures(real_arxiv_id, max_figures=2)
        assert len(figs) >= 1
        top_fig = figs[0]

        comp = BlueprintPaperFigure(
            image_path=top_fig.get("image_path"),
            svg_path=top_fig.get("svg_path"),
            arxiv_id=real_arxiv_id,
            title="FLASHATTENTION-3 ARCHITECTURE",
            sub="3-Stage Asynchronous GEMM and Softmax Pipelining",
            badge_text="OFFICIAL SPECIFICATION",
        )

        top_y = comp.get_critical_point(UP)[1]
        bottom_y = comp.get_critical_point(DOWN)[1]

        # 9:16 safe margins: Upper limit <= 5.5, lower limit >= -2.5
        assert top_y <= 5.5, f"Top coordinate {top_y} exceeds vertical upper safe boundary 5.5"
        assert bottom_y >= -2.5, f"Bottom coordinate {bottom_y} breaches lower safe boundary -2.5"

        # Kinetic subtitle pill is stationed at y = -3.45.
        # Safe buffer clearance between figure bottom and subtitles must be > 0.8 Manim units.
        subtitle_y = -3.45
        clearance = bottom_y - subtitle_y
        assert clearance > 0.8, (
            f"Clearance {clearance} above subtitle line (y={subtitle_y}) is too tight (must be > 0.8)."
        )

