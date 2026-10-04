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
from PIL import Image, ImageFilter, ImageDraw
import numpy as np

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
    # 1. Remove solid white or near-white background rectangles and paths
    cleaned = re.sub(
        r'<(?:rect|path)[^>]*fill=\"(?:#ffffff|#fff|white|rgb\(100%,100%,100%\)|#fafafa|#f8f9fa)\"[^>]*/>',
        '',
        raw_svg,
        flags=re.IGNORECASE
    )

    # 2. Style block and attribute fills/strokes
    cleaned = re.sub(
        r'fill:\s*(?:#000000|#000|black|rgb\(0%,0%,0%\)|#111111|#1a1a1a|#222222)',
        'fill:#E2E8F0',
        cleaned,
        flags=re.IGNORECASE
    )
    cleaned = re.sub(
        r'stroke:\s*(?:#000000|#000|black|rgb\(0%,0%,0%\)|#111111|#1a1a1a|#222222)',
        'stroke:#E2E8F0',
        cleaned,
        flags=re.IGNORECASE
    )

    # 3. Direct stroke and fill XML attributes to chalk white (#E2E8F0)
    cleaned = re.sub(
        r'(stroke|fill)=\"(?:#000000|#000|black|rgb\(0%,0%,0%\)|#111111|#1a1a1a|#222222)\"',
        r'\1="#E2E8F0"',
        cleaned,
        flags=re.IGNORECASE
    )

    # 4. Enhance blues/navies to signature cyan (#38BDF8)
    cleaned = re.sub(
        r'(stroke|fill)=\"(?:#0000ff|blue|#1e40af|#1d4ed8|#2563eb|#3b82f6)\"',
        f'\\1="{accent_color}"',
        cleaned,
        flags=re.IGNORECASE
    )

    # 5. Enhance greens to emerald (#10B981)
    cleaned = re.sub(
        r'(stroke|fill)=\"(?:#008000|green|#047857|#059669|#10b981)\"',
        r'\1="#10B981"',
        cleaned,
        flags=re.IGNORECASE
    )

    return cleaned


def prepare_image_for_blackboard(
    img_input: Any,
    output_path: Path,
    min_width: int = 2200,
    accent_color: str = "#38BDF8"
) -> Path:
    """
    Transforms any academic paper diagram or plot (PDF render, PNG, JPG)
    into a razor-sharp, high-contrast, fully legible 3Blue1Brown chalkboard or studio plate asset:
      1. Crops empty white/transparent margins to maximize screen readability.
      2. Super-samples to >=2200px width using high-fidelity Lanczos filtering to eliminate blurriness.
      3. Performs intelligent presentation selection:
         - If the diagram contains shaded pastel/colored blocks (e.g. architecture diagrams):
           composites onto a clean, rounded academic studio plate (#FFFFFF) with rounded corners
           to preserve the author's exact colors and ensure black text inside boxes remains 100% readable.
         - If the diagram is a plot, chart, or line drawing:
           inverts white background to transparent, maps dark text/axes/ticks to chalk white (#F8FAFC),
           and smoothly inverts anti-aliasing edges without halos.
      4. Applies fine unsharp mask sharpening for tack-sharp typography.
    """
    try:
        if isinstance(img_input, (str, Path)):
            im = Image.open(str(img_input)).convert("RGBA")
        else:
            im = img_input.convert("RGBA")

        arr = np.array(im)
        r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]

        # 1. Crop dead margins around content
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        sat = np.maximum(r, np.maximum(g, b)) - np.minimum(r, np.minimum(g, b))
        content_mask = (a > 30) & ~((lum > 248) & (sat < 15))

        if np.any(content_mask):
            ymin, ymax = np.where(content_mask)[0].min(), np.where(content_mask)[0].max()
            xmin, xmax = np.where(content_mask)[1].min(), np.where(content_mask)[1].max()
            h, w = arr.shape[:2]
            pad_x = max(int((xmax - xmin) * 0.02), 6)
            pad_y = max(int((ymax - ymin) * 0.02), 6)
            xmin = max(0, xmin - pad_x)
            ymin = max(0, ymin - pad_y)
            xmax = min(w, xmax + pad_x)
            ymax = min(h, ymax + pad_y)
            im = im.crop((xmin, ymin, xmax, ymax))

        # 2. Super-sample to high resolution (>= min_width)
        cur_w, cur_h = im.size
        if cur_w < min_width:
            scale = max(min_width / max(cur_w, 1), 1.0)
            new_w = int(cur_w * scale)
            new_h = int(cur_h * scale)
            im = im.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 3. Analyze whether diagram contains colored fills (architecture boxes)
        arr = np.array(im).astype(float)
        r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        sat = np.maximum(r, np.maximum(g, b)) - np.minimum(r, np.minimum(g, b))

        colored_fill = (lum > 140) & (lum < 235) & (sat > 25) & (a > 100)
        has_pastel_blocks = (np.mean(colored_fill) > 0.035)

        if has_pastel_blocks:
            # Studio Plate Mode: composite onto a clean rounded white card
            # Preserves author's exact pastel colors and makes black text 100% readable
            pad_x = 70
            pad_y = 50
            plate = Image.new("RGBA", (im.width + pad_x * 2, im.height + pad_y * 2), (255, 255, 255, 255))
            plate.paste(im, (pad_x, pad_y), im)
            mask = Image.new("L", plate.size, 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, plate.size[0], plate.size[1]], radius=28, fill=255)
            plate.putalpha(mask)
            plate = plate.filter(ImageFilter.UnsharpMask(radius=1.5, percent=140, threshold=2))
            plate.save(output_path, "PNG")
            return output_path
        else:
            # Chalkboard Dark Mode: transparent background, chalk white text
            is_white_bg = (lum > 225) & (sat < 25) & (a > 50)
            is_dark_text = (lum < 95) & (sat < 30) & (a > 50)
            is_edge = (lum >= 95) & (lum < 200) & (sat < 25) & (a > 50)

            out = arr.copy()
            out[is_white_bg, 3] = 0
            out[is_dark_text, 0] = 248
            out[is_dark_text, 1] = 250
            out[is_dark_text, 2] = 252

            # Smooth anti-aliased edge inversion
            new_edge_lum = 255.0 - lum[is_edge]
            out[is_edge, 0] = new_edge_lum
            out[is_edge, 1] = new_edge_lum
            out[is_edge, 2] = new_edge_lum

            out_im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
            out_im = out_im.filter(ImageFilter.UnsharpMask(radius=1.5, percent=130, threshold=2))
            out_im.save(output_path, "PNG")
            return output_path

    except Exception as e:
        print(f"⚠️ High-res chalkboard image preparation notice for {output_path.name}: {e}")
        if isinstance(img_input, (str, Path)):
            return Path(img_input)
        return output_path


def extract_paper_figures(arxiv_id: str, max_figures: int = 5) -> List[Dict[str, Any]]:
    """
    Discovers native vector figures (PDF, EPS, SVG) and high-res architecture images
    in the extracted arXiv source, converts them to standalone chalkboard assets,
    and recolors them for the 3Blue1Brown carbon chalkboard.
    """
    clean_id = clean_arxiv_id(arxiv_id)
    source_dir = download_arxiv_source(clean_id)
    if not source_dir:
        return []

    output_dir = CACHE_BASE_DIR / clean_id / "chalkboard_figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find candidate figure files
    candidate_extensions = [".pdf", ".svg", ".eps", ".png", ".jpg", ".jpeg"]
    found_files = []
    for root, _, files in os.walk(source_dir):
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in candidate_extensions:
                # Exclude full paper PDFs if named like arxiv id
                if f == f"{clean_id}.pdf":
                    continue
                found_files.append(Path(root) / f)

    # Heuristic scoring prioritizing architectural diagrams, benchmarks, and overviews
    def figure_score(p: Path) -> int:
        score = 0
        s = str(p).lower()
        stem = p.stem.lower()

        # Primary architecture keywords
        if any(k in stem for k in ["arch", "overview", "framework", "pipeline", "pipelin", "model", "method", "system", "fig1", "fig_1", "figure1", "schematic", "workflow", "stage"]):
            score += 90
        elif any(k in stem for k in ["speed", "perf", "benchmark", "comparison", "eval", "result", "recall", "acc", "throughput", "latency"]):
            score += 75
        elif any(k in s for k in ["fig", "image", "diagram", "stages", "flow", "plot"]):
            score += 45

        # Penalize tiny icon files or giant multi-megabyte bundles
        size = p.stat().st_size
        if size < 4000:
            score -= 50
        elif size > 8_000_000:
            score -= 20
        elif 8000 < size < 2_500_000:
            score += 25

        # Extension weights (vector formats get top priority)
        ext = p.suffix.lower()
        if ext == ".svg":
            score += 40
        elif ext == ".pdf":
            score += 35
        elif ext in [".png", ".jpg", ".jpeg"]:
            score += 25
        return score

    found_files.sort(key=figure_score, reverse=True)

    extracted_figures = []
    fig_idx = 1
    for p in found_files:
        if fig_idx > max_figures:
            break

        ext = p.suffix.lower()
        svg_target = output_dir / f"fig_{fig_idx}_{p.stem}.svg"
        img_target = output_dir / f"fig_{fig_idx}_{p.stem}.png"

        if ext == ".pdf":
            try:
                doc = pymupdf.open(p)
                if len(doc) > 0:
                    page = doc[0]
                    # 1. High-DPI 350 DPI Rasterization (1800 - 2800px) for razor-sharp typography
                    pix = page.get_pixmap(dpi=350, alpha=True)
                    raw_high_res = Image.frombytes("RGBA", [pix.width, pix.height], pix.samples)
                    prepared_path = prepare_image_for_blackboard(raw_high_res, img_target)

                    # 2. Vector SVG Recoloring
                    raw_svg = page.get_svg_image(text_as_path=True)
                    recolored = recolor_svg_for_blackboard(raw_svg)
                    svg_target.write_text(recolored, encoding="utf-8")

                    extracted_figures.append({
                        "figure_id": f"fig_{fig_idx}",
                        "stem": p.stem,
                        "source_file": str(p),
                        "svg_path": str(svg_target),
                        "image_path": str(prepared_path),
                        "type": "vector_pdf",
                        "score": figure_score(p)
                    })
                    print(f"   📊 Processed high-res 350 DPI vector figure: {p.name} -> {img_target.name}")
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
                    "image_path": None,
                    "type": "native_svg",
                    "score": figure_score(p)
                })
                print(f"   📊 Recolored native SVG figure: {p.name} -> {svg_target.name}")
                fig_idx += 1
            except Exception as e:
                print(f"⚠️ Error processing SVG figure {p.name}: {e}")

        elif ext in [".png", ".jpg", ".jpeg"]:
            try:
                prepared_path = prepare_image_for_blackboard(p, img_target)
                extracted_figures.append({
                    "figure_id": f"fig_{fig_idx}",
                    "stem": p.stem,
                    "source_file": str(p),
                    "svg_path": None,
                    "image_path": str(prepared_path),
                    "type": "raster_image",
                    "score": figure_score(p)
                })
                print(f"   🖼️ Super-sampled high-res raster diagram: {p.name} -> {img_target.name}")
                fig_idx += 1
            except Exception as e:
                print(f"⚠️ Error processing image figure {p.name}: {e}")

    return extracted_figures


# Backward compatibility alias
extract_vector_figures = extract_paper_figures


def get_paper_vector_figure(arxiv_id: Optional[str], index: int = 0) -> Optional[str]:
    """
    Returns the path to the converted high-resolution chalkboard PNG or SVG figure
    for the given paper, prioritizing high-DPI rasterization for crisp typography,
    or None if unavailable.
    """
    if not arxiv_id:
        return None
    figs = extract_paper_figures(arxiv_id, max_figures=index + 1)
    if figs and len(figs) > index:
        return figs[index].get("image_path") or figs[index].get("svg_path")
    return None
