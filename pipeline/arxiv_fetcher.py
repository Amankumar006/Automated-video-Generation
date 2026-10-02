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
from typing import Dict, Optional, List, Any


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


def fetch_arxiv_paper(query: str) -> Optional[Dict[str, Any]]:
    """
    Fetches paper metadata from arXiv given an ID or arXiv URL using a resilient
    multi-tier failover cascade to guarantee 100% availability even under arXiv API rate limits:
      Tier 1: Hugging Face Daily Papers API
      Tier 2: Direct arXiv HTML Dublin Core Meta Tags
      Tier 3: Official arXiv Export API (with retry)
      Tier 4: Semantic Scholar Graph API
    """
    arxiv_id = extract_arxiv_id(query)

    # Tier 1: Hugging Face API
    res = _fetch_from_huggingface(arxiv_id)
    if res:
        return res

    # Tier 2: Direct arXiv HTML meta tags
    res = _fetch_from_arxiv_html(arxiv_id)
    if res:
        return res

    # Tier 3: Official arXiv API
    res = _fetch_from_arxiv_api(arxiv_id)
    if res:
        return res

    # Tier 4: Semantic Scholar
    res = _fetch_from_semanticscholar(arxiv_id)
    if res:
        return res

    print(f"⚠️ All metadata ingestion tiers exhausted for arXiv ID '{arxiv_id}'")
    return None


if __name__ == "__main__":
    import sys
    test_id = sys.argv[1] if len(sys.argv) > 1 else "2609.40362"
    res = fetch_arxiv_paper(test_id)
    if res:
        print(f"📄 Found Paper ({res['source']}): {res['title']} ({res['published']})")
        print(f"✍️ Authors: {', '.join(res['authors'])}")
        print(f"📖 Abstract: {res['abstract'][:150]}...")
    else:
        print("Paper not found.")
