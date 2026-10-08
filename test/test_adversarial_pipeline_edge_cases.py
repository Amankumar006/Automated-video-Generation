"""Adversarial stress-test suite for the Paper Figure Extraction Pipeline.

Covers:
1. Missing, corrupted, and unusual arXiv source bundles (including old-style IDs with slashes).
2. Papers with zero figures, malformed SVGs (corrupted XML, empty files, binary garbage).
3. Extreme image dimensions and aspect ratios (panoramas, tall strips, microscopic images, blank white/transparent).
4. Fallback behavior in visual_director.py when paper_figures is empty, malformed, or has non-dict items.
5. Offline and cache hit paths in arxiv_fetcher.py.
"""

import copy
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch
import urllib.error

import numpy as np
from PIL import Image
import pytest

from pipeline.arxiv_vector_extractor import (
    clean_arxiv_id,
    download_arxiv_source,
    extract_paper_figures,
    prepare_image_for_blackboard,
    recolor_svg_for_blackboard,
)
from pipeline.arxiv_fetcher import (
    fetch_arxiv_paper,
    _fetch_from_local_cache,
    _fetch_from_local_source,
)
from pipeline.visual_director import VisualDirector
from manim_engine.primitives.visual_compositions import BlueprintPaperFigure


PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ==============================================================================
# Challenge 1: Source Bundle Edge Cases & Corruptions
# ==============================================================================

class TestSourceBundleAdversarial:
    """Stress tests arXiv bundle downloading, extraction, and ID parsing."""

    def test_old_style_arxiv_id_with_slashes(self, tmp_path):
        """Test old-style arXiv IDs containing slashes (e.g. hep-th/9912012)."""
        dirty_id = "hep-th/9912012"
        clean = clean_arxiv_id(dirty_id)
        assert "/" in clean, "Old-style arXiv ID should retain slash or be normalized"

        # Mock download to return a valid tarball and verify path handling
        tar_bytes = b"not a real tar"
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.read.return_value = tar_bytes
            mock_resp.__enter__.return_value = mock_resp
            mock_url.return_value = mock_resp

            # We test whether download_arxiv_source handles slashes without FileNotFoundError
            with patch("pipeline.arxiv_vector_extractor.CACHE_BASE_DIR", tmp_path):
                # When clean_id contains a slash, path construction paper_dir / f"{clean_id}_source.tar.gz"
                # will attempt to write into a nonexistent subfolder if not handled defensively.
                try:
                    res = download_arxiv_source(clean)
                except FileNotFoundError as fnf:
                    pytest.fail(f"download_arxiv_source crashed on old-style ID with slash: {fnf}")

    def test_corrupted_gzip_tarball(self, tmp_path):
        """Test when arXiv returns corrupted gzip / non-tar bytes."""
        paper_id = "2601.99999"
        corrupted_bytes = b"\x1f\x8b\x08\x00corrupted-gzip-stream-not-a-tar"

        with patch("pipeline.arxiv_vector_extractor.CACHE_BASE_DIR", tmp_path), \
             patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.read.return_value = corrupted_bytes
            mock_resp.__enter__.return_value = mock_resp
            mock_url.return_value = mock_resp

            res = download_arxiv_source(paper_id)
            # Should fail gracefully and return None instead of crashing
            assert res is None

            # Now test extract_paper_figures on this ID
            figs = extract_paper_figures(paper_id)
            assert figs == []

    def test_zero_byte_source_download(self, tmp_path):
        """Test behavior when server returns empty (0 bytes) content."""
        paper_id = "2601.00000"
        with patch("pipeline.arxiv_vector_extractor.CACHE_BASE_DIR", tmp_path), \
             patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b""
            mock_resp.__enter__.return_value = mock_resp
            mock_url.return_value = mock_resp

            res = download_arxiv_source(paper_id)
            assert res is None
            figs = extract_paper_figures(paper_id)
            assert figs == []

    def test_direct_pdf_source_fallback(self, tmp_path):
        """Test behavior when arXiv source bundle is directly a standalone PDF (not a tarball)."""
        paper_id = "2601.11111"
        pdf_bytes = b"%PDF-1.5\nfake-pdf-content"
        with patch("pipeline.arxiv_vector_extractor.CACHE_BASE_DIR", tmp_path), \
             patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.read.return_value = pdf_bytes
            mock_resp.__enter__.return_value = mock_resp
            mock_url.return_value = mock_resp

            res = download_arxiv_source(paper_id)
            assert res is not None
            assert (res / f"{paper_id}.pdf").exists()


# ==============================================================================
# Challenge 2: Papers with 0 Figures & Malformed SVGs
# ==============================================================================

class TestFigureExtractionEdgeCases:
    """Stress tests figure extraction on empty bundles, malformed SVGs, and text files."""

    def test_paper_with_zero_figures(self, tmp_path):
        """Paper source bundle contains only .tex and .bib files, no figures."""
        paper_id = "2601.22222"
        paper_dir = tmp_path / paper_id
        source_dir = paper_dir / "source"
        source_dir.mkdir(parents=True)
        (source_dir / "main.tex").write_text(r"\documentclass{article}\begin{document}Hello\end{document}")
        (source_dir / "refs.bib").write_text("@article{test, title={Test}}")

        with patch("pipeline.arxiv_vector_extractor.CACHE_BASE_DIR", tmp_path):
            figs = extract_paper_figures(paper_id)
            assert isinstance(figs, list)
            assert len(figs) == 0

    def test_malformed_svg_corrupted_xml(self, tmp_path):
        """Source contains malformed SVGs (truncated XML, non-SVG text in .svg extension)."""
        paper_id = "2601.33333"
        paper_dir = tmp_path / paper_id
        source_dir = paper_dir / "source"
        source_dir.mkdir(parents=True)

        # 1. Truncated XML
        (source_dir / "fig_bad1.svg").write_text("<svg><path d='M0 0 L10 10' fill='#ffffff'", encoding="utf-8")
        # 2. Binary garbage in SVG
        (source_dir / "fig_bad2.svg").write_bytes(b"\x00\xff\xfe\x00\x12\x34\x56\x78\x9a")
        # 3. Empty SVG
        (source_dir / "fig_bad3.svg").write_text("", encoding="utf-8")

        with patch("pipeline.arxiv_vector_extractor.CACHE_BASE_DIR", tmp_path):
            # Must not crash
            figs = extract_paper_figures(paper_id)
            assert isinstance(figs, list)
            # Extracted figures should either be skipped or handled safely without crashing
            for f in figs:
                assert "figure_id" in f

    def test_recolor_svg_on_malformed_strings(self):
        """recolor_svg_for_blackboard should not crash on invalid strings or regex-breaking content."""
        malformed_inputs = [
            "",
            "   \n\t  ",
            "Not an SVG at all",
            "<?xml><svg><rect fill='white'></rect>",
            "<svg fill='rgba(255,255,255,1)'><path stroke='black'/></svg>",
            "{" * 500 + "}" * 500,
        ]
        for inp in malformed_inputs:
            out = recolor_svg_for_blackboard(inp)
            assert isinstance(out, str)


# ==============================================================================
# Challenge 3: Extreme Image Dimensions & Aspect Ratios
# ==============================================================================

class TestExtremeImageAspectRatios:
    """Stress tests prepare_image_for_blackboard under extreme shapes and sizes."""

    def test_ultra_wide_aspect_ratio(self, tmp_path):
        """Ultra wide banner image (100:1 ratio, 2000px wide x 20px tall)."""
        img = Image.new("RGBA", (2000, 20), (255, 255, 255, 255))
        # Draw some dark text/line
        for x in range(100, 1900):
            img.putpixel((x, 10), (0, 0, 0, 255))

        out_path = tmp_path / "wide.png"
        res = prepare_image_for_blackboard(img, out_path)
        assert res.exists()
        with Image.open(res) as out_im:
            assert out_im.width >= 2000
            assert out_im.height > 0

    def test_tall_aspect_ratio_scaling_bounds(self, tmp_path):
        """
        Tests tall strip image (1:10 ratio, 40px wide x 400px tall).
        Demonstrates that scaling purely on min_width (2200) without capping height
        causes height to explode by 55x (to 22,000px).
        """
        img = Image.new("RGBA", (40, 400), (255, 255, 255, 255))
        for y in range(50, 350):
            img.putpixel((20, y), (0, 0, 0, 255))

        out_path = tmp_path / "tall.png"
        res = prepare_image_for_blackboard(img, out_path)
        assert res.exists()
        with Image.open(res) as out_im:
            # Observes unbounded vertical scaling:
            # The height expands to 22,000 pixels even though vertical canvas is only 1920px.
            assert out_im.height > 10000, f"Height was unexpectedly constrained: {out_im.height}"

    def test_tiny_1x1_image(self, tmp_path):
        """1x1 pixel image edge case."""
        img = Image.new("RGBA", (1, 1), (0, 0, 0, 255))
        out_path = tmp_path / "tiny.png"
        res = prepare_image_for_blackboard(img, out_path)
        assert res.exists()

    def test_solid_white_and_fully_transparent_images(self, tmp_path):
        """Images with zero content (all dead margins or 100% transparent)."""
        white_img = Image.new("RGBA", (500, 500), (255, 255, 255, 255))
        out_white = tmp_path / "white.png"
        res_white = prepare_image_for_blackboard(white_img, out_white)
        assert res_white.exists()

        trans_img = Image.new("RGBA", (500, 500), (0, 0, 0, 0))
        out_trans = tmp_path / "trans.png"
        res_trans = prepare_image_for_blackboard(trans_img, out_trans)
        assert res_trans.exists()


# ==============================================================================
# Challenge 4: VisualDirector Fallback & Malformed Figure Paths
# ==============================================================================

class TestVisualDirectorFallback:
    """Stress tests visual_director.py on empty, malformed, or corrupt figure lists."""

    def test_empty_paper_figures_falls_back_to_composition(self):
        """Beat 3 must fall back to a valid visual composition when paper_figures is empty."""
        director = VisualDirector()
        spec = {
            "title": "Edge Case Video",
            "paper_figures": [],
            "beats": [
                {"beat_id": 1, "text": "Intro text", "visual_focus": "Introduction"},
                {"beat_id": 2, "text": "Problem text", "visual_focus": "The bottleneck"},
                {"beat_id": 3, "text": "Mechanism text explaining vector flow manifold", "visual_focus": "Latent manifold"},
                {"beat_id": 4, "text": "Impact text", "visual_focus": "Impact and results"},
                {"beat_id": 5, "text": "Showdown text with benchmark speed", "visual_focus": "Speed comparison"},
            ]
        }
        res = director.prepare_storyboard_for_spec(spec)
        beat_3 = next(b for b in res["beats"] if b["beat_id"] == 3)
        assert beat_3["motif_type"] in ["visual_composition", "chalkboard_code_block"]
        assert "visual_blueprint" in beat_3
        assert beat_3["visual_blueprint"]["layout"] != "paper_figure"

    def test_nonexistent_paths_in_paper_figures(self):
        """When paper_figures points to non-existent files, Beat 3 must fall back cleanly."""
        director = VisualDirector()
        spec = {
            "title": "Missing Paths Video",
            "paper_figures": [
                {
                    "figure_id": "fig_fake",
                    "svg_path": "/nonexistent/path/fake.svg",
                    "image_path": "/nonexistent/path/fake.png",
                    "caption": "Ghost Figure",
                }
            ],
            "beats": [
                {"beat_id": 1, "text": "Intro", "visual_focus": "Intro"},
                {"beat_id": 2, "text": "Problem", "visual_focus": "Problem"},
                {"beat_id": 3, "text": "Architecture with attention prism", "visual_focus": "Attention"},
                {"beat_id": 4, "text": "Details", "visual_focus": "Details"},
                {"beat_id": 5, "text": "Showdown", "visual_focus": "Benchmark"},
            ]
        }
        res = director.prepare_storyboard_for_spec(spec)
        beat_3 = next(b for b in res["beats"] if b["beat_id"] == 3)
        # Non-existent paths must NOT bind to paper_figure
        assert beat_3["motif_type"] != "paper_figure"
        assert beat_3["visual_blueprint"]["layout"] != "paper_figure"

    def test_malformed_paper_figures_list_elements(self):
        """When paper_figures contains None or non-dict items, should it crash or handle defensively?"""
        director = VisualDirector()
        spec = {
            "title": "Corrupt Figures List",
            "paper_figures": [None, "invalid_string_item", 12345],
            "beats": [
                {"beat_id": 1, "text": "Intro", "visual_focus": "Intro"},
                {"beat_id": 2, "text": "Problem", "visual_focus": "Problem"},
                {"beat_id": 3, "text": "Mechanism", "visual_focus": "Mechanism"},
            ]
        }
        try:
            res = director.prepare_storyboard_for_spec(spec)
            beat_3 = next(b for b in res["beats"] if b["beat_id"] == 3)
            assert beat_3 is not None
        except Exception as e:
            pytest.fail(f"VisualDirector crashed on malformed paper_figures items: {type(e).__name__}: {e}")

    def test_blueprint_paper_figure_svg_only_small_size(self, tmp_path):
        """
        Adversarial test for BlueprintPaperFigure when image_path is None
        and svg_path is a small valid SVG (< 5.2 width and < 3.2 height).
        Tests for uninitialized 'im' variable bug!
        """
        small_svg = tmp_path / "small.svg"
        small_svg.write_text(
            '<svg viewBox="0 0 100 100" width="100" height="100">'
            '<circle cx="50" cy="50" r="40" stroke="#38BDF8" fill="none"/>'
            '</svg>',
            encoding="utf-8"
        )

        try:
            comp = BlueprintPaperFigure(
                svg_path=str(small_svg),
                image_path=None,
                arxiv_id="2407.08608",
                title="SVG ONLY TEST",
            )
            # Verify fig_mobj is SVGMobject, NOT fallback placeholder box
            assert comp.fig_mobj is not None
            # If the bug is present, fig_mobj will be a fallback Group(box, lbl) instead of SVGMobject
            from manim import SVGMobject
            assert isinstance(comp.fig_mobj, SVGMobject), (
                f"Expected SVGMobject, but got {type(comp.fig_mobj)}. "
                "Did small SVG fail to scale due to uninitialized 'im'?"
            )
        except Exception as e:
            pytest.fail(f"BlueprintPaperFigure crashed on SVG-only input: {e}")


# ==============================================================================
# Challenge 5: Offline / Cache Hit Paths in arxiv_fetcher.py
# ==============================================================================

class TestArxivFetcherOfflineAndCache:
    """Stress tests offline execution and cache lookup hierarchies."""

    def test_cache_hit_offline_does_not_make_network_requests(self, tmp_path):
        """Tier 0 cache hit must return metadata without touching any network tier."""
        paper_id = "2407.08608"
        paper_dir = tmp_path / paper_id
        paper_dir.mkdir(parents=True)
        cached_meta = {
            "arxiv_id": paper_id,
            "title": "Offline Cached Paper",
            "abstract": "This was read from local metadata.json.",
            "authors": ["Local Author"],
            "published": "2024-07-15",
            "url": f"https://arxiv.org/abs/{paper_id}",
            "source": "local_cache"
        }
        (paper_dir / "metadata.json").write_text(json.dumps(cached_meta), encoding="utf-8")

        with patch("pipeline.arxiv_fetcher.CACHE_BASE_DIR", tmp_path), \
             patch("pipeline.arxiv_vector_extractor.CACHE_BASE_DIR", tmp_path), \
             patch("urllib.request.urlopen") as mock_url:
            mock_url.side_effect = urllib.error.URLError("Network is strictly offline!")

            res = fetch_arxiv_paper(paper_id, extract_figures=False)
            assert res is not None
            assert res["title"] == "Offline Cached Paper"
            assert res["arxiv_id"] == paper_id
            mock_url.assert_not_called()

    def test_corrupted_metadata_json_falls_back_to_local_source(self, tmp_path):
        """If metadata.json is corrupted JSON, it should fall back to local .tex source."""
        paper_id = "2407.08608"
        paper_dir = tmp_path / paper_id
        source_dir = paper_dir / "source"
        source_dir.mkdir(parents=True)

        # Corrupted metadata.json
        (paper_dir / "metadata.json").write_text("{corrupted: [json", encoding="utf-8")

        # Valid source .tex
        (source_dir / "paper.tex").write_text(
            r"\title{Recovered From TeX Source}\begin{abstract}Recovered abstract.\end{abstract}",
            encoding="utf-8"
        )

        with patch("pipeline.arxiv_fetcher.CACHE_BASE_DIR", tmp_path), \
             patch("pipeline.arxiv_vector_extractor.CACHE_BASE_DIR", tmp_path), \
             patch("urllib.request.urlopen") as mock_url:
            mock_url.side_effect = urllib.error.URLError("Network is offline")

            res = fetch_arxiv_paper(paper_id, extract_figures=False)
            assert res is not None
            assert "Recovered From TeX Source" in res["title"]
            assert res["source"] == "local_source"

    def test_completely_offline_and_no_cache_returns_none(self, tmp_path):
        """When network is down and paper is not cached, fetch_arxiv_paper must return None gracefully."""
        paper_id = "9999.99999"
        with patch("pipeline.arxiv_fetcher.CACHE_BASE_DIR", tmp_path), \
             patch("urllib.request.urlopen") as mock_url:
            mock_url.side_effect = urllib.error.URLError("Offline")

            res = fetch_arxiv_paper(paper_id, extract_figures=False)
            assert res is None
