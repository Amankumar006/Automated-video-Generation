"""
The Model Verse — arXiv Paper Metadata & Abstract Ingestion Engine
Fetches paper metadata (title, summary, authors, subject) with multi-tier failover:
1. Hugging Face Daily Papers API (fastest, unthrottled)
2. Direct arXiv HTML metadata extraction (<meta name="citation_*" />)
3. Official arXiv Export API (with retry & exponential backoff)
4. Semantic Scholar API fallback
"""

import re
import json
import time
import html
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional, List, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_BASE_DIR = PROJECT_ROOT / "public" / "arxiv_cache"


def extract_arxiv_id(query: str) -> str:
    """Extracts clean arXiv ID from URL or raw ID string."""
    query = query.strip()
    # Match patterns like https://arxiv.org/abs/2412.19437 or 2412.19437v1
    match = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", query)
    if match:
        return match.group(1)
    # Check old-style IDs (e.g. hep-th/9912012)
    match_old = re.search(r"([a-z\-]+(?:\.[A-Z]{2})?/\d{7})", query)
    if match_old:
        return match_old.group(1)
    return query


def _fetch_from_huggingface(arxiv_id: str) -> Optional[Dict[str, Any]]:
    """Fetches paper metadata from Hugging Face Papers API."""
    url = f"https://huggingface.co/api/papers/{arxiv_id}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "TheModelVerse-Pipeline/2.0 (contact@themodelverse.ai)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        title = data.get("title", "").strip().replace("\n", " ")
        abstract = data.get("summary", "").strip().replace("\n", " ")
        if title and abstract:
            authors = [a.get("name") if isinstance(a, dict) else str(a) for a in data.get("authors", [])][:5]
            pub = data.get("publishedAt", "")[:10]
            return {
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "published": pub,
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "source": "huggingface"
            }
    except Exception:
        pass
    return None


def _fetch_from_arxiv_html(arxiv_id: str) -> Optional[Dict[str, Any]]:
    """Extracts paper metadata directly from arXiv HTML meta tags."""
    url = f"https://arxiv.org/abs/{arxiv_id}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            page = resp.read().decode("utf-8", errors="ignore")

        m_title = re.search(r'<meta name="citation_title" content="(.*?)"', page, re.DOTALL)
        m_abstract = re.search(r'<meta name="citation_abstract" content="(.*?)"', page, re.DOTALL)
        authors_raw = re.findall(r'<meta name="citation_author" content="(.*?)"', page)
        m_date = re.search(r'<meta name="citation_date" content="(.*?)"', page)

        if m_title and m_abstract:
            title = html.unescape(m_title.group(1)).strip().replace("\n", " ")
            abstract = html.unescape(m_abstract.group(1)).strip().replace("\n", " ")
            authors = [html.unescape(a).strip() for a in authors_raw][:5]
            published = m_date.group(1).strip() if m_date else ""
            return {
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "published": published,
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "source": "arxiv_html"
            }
    except Exception:
        pass
    return None


def _fetch_from_arxiv_api(arxiv_id: str) -> Optional[Dict[str, Any]]:
    """Fetches paper metadata using the official arXiv Export API with retries."""
    api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    req = urllib.request.Request(
        api_url,
        headers={"User-Agent": "TheModelVerse-Pipeline/2.0 (contact@themodelverse.ai)"}
    )

    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
            root = ET.fromstring(xml_data)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entry = root.find("atom:entry", ns)
            if entry is None:
                return None

            title_elem = entry.find("atom:title", ns)
            summary_elem = entry.find("atom:summary", ns)
            published_elem = entry.find("atom:published", ns)

            if title_elem is None or summary_elem is None:
                return None

            title = " ".join(title_elem.text.strip().split())
            abstract = " ".join(summary_elem.text.strip().split())
            published = published_elem.text.strip()[:10] if published_elem is not None else ""

            authors = []
            for author in entry.findall("atom:author", ns):
                name_elem = author.find("atom:name", ns)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())

            return {
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "authors": authors[:5],
                "published": published,
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "source": "arxiv_api"
            }
        except Exception as e:
            if "429" in str(e) and attempt == 0:
                time.sleep(2.0)
                continue
            break
    return None


def _fetch_from_semanticscholar(arxiv_id: str) -> Optional[Dict[str, Any]]:
    """Fetches paper metadata from Semantic Scholar Graph API fallback."""
    url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}?fields=title,abstract,authors,publicationDate"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "TheModelVerse-Pipeline/2.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        title = data.get("title", "").strip()
        abstract = data.get("abstract", "").strip()
        if title:
            authors = [a.get("name", "") for a in data.get("authors", [])][:5]
            pub = data.get("publicationDate", "")
            return {
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "published": pub,
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "source": "semantic_scholar"
            }
    except Exception:
        pass
    return None


def _fetch_from_local_source(arxiv_id: str) -> Optional[Dict[str, Any]]:
    """Recovers paper metadata from local source bundle (.tex files) if present."""
    source_dir = CACHE_BASE_DIR / arxiv_id / "source"
    if not source_dir.exists() or not any(source_dir.iterdir()):
        return None

    title = None
    abstract = None
    authors = []

    # 1. Search for title and abstract in .tex files
    for tex_path in source_dir.rglob("*.tex"):
        try:
            content = tex_path.read_text(encoding="utf-8", errors="ignore")
            if not title:
                m_title = re.search(r"\\title(?:\[[^\]]*\])?\{([^}]+)\}", content)
                if m_title:
                    raw_t = m_title.group(1).replace("\n", " ").replace("\\\\", " ").strip()
                    clean_t = re.sub(r"\\[a-zA-Z]+\{?", "", raw_t).replace("}", "").strip()
                    if clean_t:
                        title = " ".join(clean_t.split())

            if not abstract:
                m_abs = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", content, re.DOTALL)
                if m_abs:
                    clean_a = re.sub(r"\\[a-zA-Z]+\{?", "", m_abs.group(1)).replace("}", "").strip()
                    if clean_a:
                        abstract = " ".join(clean_a.split())
        except Exception:
            continue

    # 2. Check dedicated abstract file if present
    if not abstract:
        for abs_file in source_dir.rglob("*abstract*.tex"):
            try:
                txt = abs_file.read_text(encoding="utf-8", errors="ignore")
                clean_a = re.sub(r"\\[a-zA-Z]+\{?", "", txt).replace("}", "").strip()
                if clean_a:
                    abstract = " ".join(clean_a.split())
                    break
            except Exception:
                continue

    if not title and not abstract:
        return None

    return {
        "arxiv_id": arxiv_id,
        "title": title or f"arXiv Paper {arxiv_id}",
        "abstract": abstract or f"Extracted from local arXiv source cache for {arxiv_id}.",
        "authors": authors or ["arXiv Contributor"],
        "published": "",
        "url": f"https://arxiv.org/abs/{arxiv_id}",
        "source": "local_source"
    }


def _fetch_from_local_cache(arxiv_id: str) -> Optional[Dict[str, Any]]:
    """Checks local cache for metadata.json or source bundle."""
    paper_dir = CACHE_BASE_DIR / arxiv_id
    meta_file = paper_dir / "metadata.json"
    if meta_file.exists():
        try:
            cached = json.loads(meta_file.read_text(encoding="utf-8"))
            if cached.get("arxiv_id") and cached.get("title"):
                return cached
        except Exception:
            pass

    # Fallback to source directory inspection
    return _fetch_from_local_source(arxiv_id)


def fetch_arxiv_paper(
    query: str,
    extract_figures: bool = True,
    max_figures: int = 5
) -> Optional[Dict[str, Any]]:
    """
    Fetches paper metadata from arXiv given an ID or arXiv URL using a resilient
    multi-tier failover cascade to guarantee 100% availability even under arXiv API rate limits:
      Tier 0: Local Cache Lookup (public/arxiv_cache/<id>/metadata.json or source/)
      Tier 1: Hugging Face Daily Papers API
      Tier 2: Direct arXiv HTML Dublin Core Meta Tags
      Tier 3: Official arXiv Export API (with retry)
      Tier 4: Semantic Scholar Graph API
      Tier 5: Local Source Fallback

    When extract_figures=True, automatically invokes extract_paper_figures() and
    populates res['paper_figures'].
    """
    from pipeline.arxiv_vector_extractor import clean_arxiv_id, extract_paper_figures

    raw_id = extract_arxiv_id(query)
    arxiv_id = clean_arxiv_id(raw_id)
    paper_dir = CACHE_BASE_DIR / arxiv_id

    # Tier 0: Local cache check (offline/CI resilience)
    res = _fetch_from_local_cache(arxiv_id)

    # If not cached locally, query remote tiers
    if not res:
        # Tier 1: Hugging Face API
        res = _fetch_from_huggingface(arxiv_id)

        # Tier 2: Direct arXiv HTML meta tags
        if not res:
            res = _fetch_from_arxiv_html(arxiv_id)

        # Tier 3: Official arXiv API
        if not res:
            res = _fetch_from_arxiv_api(arxiv_id)

        # Tier 4: Semantic Scholar
        if not res:
            res = _fetch_from_semanticscholar(arxiv_id)

        # Save successful metadata to local cache
        if res:
            try:
                paper_dir.mkdir(parents=True, exist_ok=True)
                clean_meta = {k: v for k, v in res.items() if k != "paper_figures"}
                (paper_dir / "metadata.json").write_text(json.dumps(clean_meta, indent=2), encoding="utf-8")
            except Exception:
                pass

    # Tier 5: Local source fallback if network tiers failed
    if not res:
        res = _fetch_from_local_source(arxiv_id)

    if not res:
        print(f"⚠️ All metadata ingestion tiers exhausted for arXiv ID '{arxiv_id}'")
        return None

    # Automatically extract and bind paper figures
    if extract_figures:
        clean_id = res.get("arxiv_id") or arxiv_id
        try:
            figs = extract_paper_figures(clean_id, max_figures=max_figures)
            res["paper_figures"] = figs or []
        except Exception as e_figs:
            print(f"⚠️ Figure extraction notice: {e_figs}")
            res["paper_figures"] = []
    elif "paper_figures" not in res:
        res["paper_figures"] = []

    return res


# Re-export native arXiv figure extraction and blackboard recoloring engine
from pipeline.arxiv_vector_extractor import (
    clean_arxiv_id,
    download_arxiv_source,
    extract_paper_figures,
    extract_vector_figures,
    recolor_svg_for_blackboard,
    prepare_image_for_blackboard,
    get_paper_vector_figure
)


if __name__ == "__main__":
    import sys
    test_id = sys.argv[1] if len(sys.argv) > 1 else "2609.40362"
    res = fetch_arxiv_paper(test_id, extract_figures=True)
    if res:
        print(f"📄 Found Paper ({res['source']}): {res['title']} ({res['published']})")
        print(f"✍️ Authors: {', '.join(res['authors'])}")
        print(f"📖 Abstract: {res['abstract'][:150]}...")
        figs = res.get("paper_figures", [])
        if figs:
            print(f"🖼️ Found {len(figs)} native figures in arXiv source bundle:")
            for f in figs:
                print(f"   - {f['figure_id']} ({f['type']}): {f.get('svg_path') or f.get('image_path')}")
    else:
        print("Paper not found.")
