"""
The Model Verse — Native ArXiv Vector Figure Extractor & Blackboard Recolor Engine
Downloads e-print LaTeX bundles from arXiv, extracts native vector diagrams (PDF, EPS, SVG),
and recolors vector paths for signature 3Blue1Brown carbon chalkboard (#0A0D14) rendering.
"""

import os
import re
import tarfile
import urllib.request
from pathlib import Path
from typing import List, Dict, Any, Optional
import pymupdf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_BASE_DIR = PROJECT_ROOT / "public" / "arxiv_cache"


def clean_arxiv_id(query: str) -> str:
    """Normalizes an arXiv query or URL into a clean ID."""
    query = query.strip()
    match = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", query)
    if match:
        return match.group(1)
    match_old = re.search(r"([a-z\-]+(?:\.[A-Z]{2})?/\d{7})", query)
    if match_old:
        return match_old.group(1)
    return query


def download_arxiv_source(arxiv_id: str) -> Optional[Path]:
    """
    Downloads and extracts the arXiv source bundle (.tar.gz) into the local cache.
    Returns the Path to the extracted source folder.
    """
    clean_id = clean_arxiv_id(arxiv_id)
    paper_dir = CACHE_BASE_DIR / clean_id
    source_dir = paper_dir / "source"

    if source_dir.exists() and any(source_dir.iterdir()):
        return source_dir

    paper_dir.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(parents=True, exist_ok=True)

    url = f"https://arxiv.org/e-print/{clean_id}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "TheModelVerse-Pipeline/2.0 (contact@themodelverse.ai)"}
    )

    print(f"📥 Fetching arXiv e-print source bundle for '{clean_id}'...")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read()
    except Exception as e:
        print(f"⚠️ Failed to download arXiv e-print bundle: {e}")
        return None

    tar_path = paper_dir / f"{clean_id}_source.tar.gz"
    tar_path.write_bytes(content)

    try:
        with tarfile.open(tar_path) as tar:
            tar.extractall(source_dir)
        print(f"✅ Extracted arXiv source to: {source_dir}")
        return source_dir
    except Exception as e:
        print(f"⚠️ Tarball extraction failed (might be standalone PDF): {e}")
        # If source is a single PDF directly
        if content[:4] == b"%PDF":
            pdf_path = source_dir / f"{clean_id}.pdf"
            pdf_path.write_bytes(content)
            return source_dir
        return None


def recolor_svg_for_blackboard(raw_svg: str, accent_color: str = "#38BDF8") -> str:
    """
    Transforms a standard white-background paper SVG into a signature 3Blue1Brown
    chalkboard asset with high-contrast chalk strokes and luminous accents.
    """
    # 1. Remove solid white or near-white background rectangles
    cleaned = re.sub(
        r'<rect[^>]*fill=\"(?:#ffffff|#fff|white|rgb\(100%,100%,100%\)|#fafafa|#f8f9fa)\".*?/>',
        '',
        raw_svg,
        flags=re.IGNORECASE
    )

    # 2. Convert dark/black strokes and fills to chalk white (#E2E8F0)
    cleaned = re.sub(
        r'(stroke|fill)=\"(?:#000000|#000|black|rgb\(0%,0%,0%\)|#111111|#1a1a1a|#222222)\"',
        r'\1="#E2E8F0"',
        cleaned,
        flags=re.IGNORECASE
    )

    # 3. Enhance blues/navies to signature cyan (#38BDF8)
    cleaned = re.sub(
        r'(stroke|fill)=\"(?:#0000ff|blue|#1e40af|#1d4ed8|#2563eb|#3b82f6)\"',
        f'\\1="{accent_color}"',
        cleaned,
        flags=re.IGNORECASE
    )

    # 4. Enhance greens to emerald (#10B981)
    cleaned = re.sub(
        r'(stroke|fill)=\"(?:#008000|green|#047857|#059669|#10b981)\"',
        r'\1="#10B981"',
        cleaned,
        flags=re.IGNORECASE
    )

    return cleaned


def extract_vector_figures(arxiv_id: str, max_figures: int = 5) -> List[Dict[str, Any]]:
    """
    Discovers native vector figures (PDF, EPS, SVG) in the extracted arXiv source,
    converts them to standalone SVGs, and recolors them for the 3b1b chalkboard.
    """
    clean_id = clean_arxiv_id(arxiv_id)
    source_dir = download_arxiv_source(clean_id)
    if not source_dir:
        return []

    output_dir = CACHE_BASE_DIR / clean_id / "chalkboard_figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find candidate figure files
    candidate_extensions = [".pdf", ".svg", ".eps", ".png"]
    found_files = []
    for root, _, files in os.walk(source_dir):
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in candidate_extensions:
                # Exclude full paper PDFs if named like arxiv id
                if f == f"{clean_id}.pdf":
                    continue
                found_files.append(Path(root) / f)

    # Sort candidates by file size or heuristic priority
    # Prefer files in 'fig' or 'figure' folders
    def figure_score(p: Path) -> int:
        score = 0
        s = str(p).lower()
        if "fig" in s or "image" in s:
            score += 50
        if p.suffix.lower() == ".pdf":
            score += 30
        elif p.suffix.lower() == ".svg":
            score += 25
        # Prefer moderate sized vector files (avoid tiny icons or giant bitmaps)
        size = p.stat().st_size
        if 5000 < size < 1_500_000:
            score += 20
        return score

    found_files.sort(key=figure_score, reverse=True)

    extracted_figures = []
    fig_idx = 1
    for p in found_files:
        if fig_idx > max_figures:
            break

        ext = p.suffix.lower()
        svg_target = output_dir / f"fig_{fig_idx}_{p.stem}.svg"

        if ext == ".pdf":
            try:
                doc = pymupdf.open(p)
                if len(doc) > 0:
                    raw_svg = doc[0].get_svg_image(text_as_path=True)
                    recolored = recolor_svg_for_blackboard(raw_svg)
                    svg_target.write_text(recolored, encoding="utf-8")
                    extracted_figures.append({
                        "figure_id": f"fig_{fig_idx}",
                        "stem": p.stem,
                        "source_file": str(p),
                        "svg_path": str(svg_target),
                        "type": "vector_pdf"
                    })
                    print(f"   📊 Converted & recolored vector PDF figure: {p.name} -> {svg_target.name}")
                    fig_idx += 1
            except Exception as e:
                print(f"⚠️ Error processing PDF figure {p.name}: {e}")

        elif ext == ".svg":
            try:
                raw_svg = p.read_text(encoding="utf-8", errors="ignore")
                recolored = recolor_svg_for_blackboard(raw_svg)
                svg_target.write_text(recolored, encoding="utf-8")
                extracted_figures.append({
                    "figure_id": f"fig_{fig_idx}",
                    "stem": p.stem,
                    "source_file": str(p),
                    "svg_path": str(svg_target),
                    "type": "native_svg"
                })
                print(f"   📊 Recolored native SVG figure: {p.name} -> {svg_target.name}")
                fig_idx += 1
            except Exception as e:
                print(f"⚠️ Error processing SVG figure {p.name}: {e}")

    return extracted_figures


def get_paper_vector_figure(arxiv_id: Optional[str], index: int = 0) -> Optional[str]:
    """
    Returns the path to the converted chalkboard SVG figure for the given paper,
    or None if unavailable.
    """
    if not arxiv_id:
        return None
    figs = extract_vector_figures(arxiv_id, max_figures=index + 1)
    if figs and len(figs) > index:
        return figs[index]["svg_path"]
    return None
