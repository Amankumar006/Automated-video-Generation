"""
The Model Verse — arXiv Paper Metadata & Abstract Ingestion Engine
Fetches paper metadata (title, summary, authors, subject) using the official arXiv API.
"""

import re
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Optional

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

def fetch_arxiv_paper(query: str) -> Optional[Dict[str, str]]:
    """
    Fetches paper metadata from arXiv given an ID or arXiv URL.
    Returns dict with title, abstract, authors, published date, and arxiv_id.
    """
    arxiv_id = extract_arxiv_id(query)
    api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    req = urllib.request.Request(api_url, headers={"User-Agent": "TheModelVerse-Pipeline/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            xml_data = response.read()
    except Exception as e:
        print(f"⚠️ Error querying arXiv API for '{arxiv_id}': {e}")
        return None

    try:
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
            "url": f"https://arxiv.org/abs/{arxiv_id}"
        }
    except Exception as e:
        print(f"⚠️ Error parsing arXiv XML for '{arxiv_id}': {e}")
        return None

if __name__ == "__main__":
    import sys
    test_id = sys.argv[1] if len(sys.argv) > 1 else "2412.19437"
    res = fetch_arxiv_paper(test_id)
    if res:
        print(f"📄 Found Paper: {res['title']} ({res['published']})")
        print(f"✍️ Authors: {', '.join(res['authors'])}")
        print(f"📖 Abstract: {res['abstract'][:150]}...")
    else:
        print("Paper not found.")
