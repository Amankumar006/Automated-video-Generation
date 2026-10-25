"""Freeze official announcement images for source-first video visuals.

Only images discovered from the announcement's own HTML are accepted. The
resolver never searches generic stock-photo providers and never treats a
decorative image as benchmark evidence.
"""

from __future__ import annotations

import hashlib
import html
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ASSET_DIR = PROJECT_ROOT / "public" / "source_assets"
MAX_IMAGE_BYTES = 12 * 1024 * 1024


def _allowed_asset_host(source_url: str, asset_url: str) -> bool:
    source_host = (urllib.parse.urlparse(source_url).hostname or "").lower()
    asset_host = (urllib.parse.urlparse(asset_url).hostname or "").lower()
    if not source_host or not asset_host:
        return False
    # Official pages commonly serve media from a first-party subdomain, e.g.
    # kimi-img.kimi.ai for kimi.ai. Do not accept unrelated image hosts.
    source_base = source_host.removeprefix("www.")
    return (
        asset_host == source_host
        or asset_host == source_base
        or asset_host.endswith("." + source_base)
    )


def extract_official_image_candidates(page_html: str, source_url: str) -> List[str]:
    """Return first-party image candidates in priority order."""
    candidates: List[str] = []
    patterns = (
        r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)',
        r'<link[^>]+rel=["\'][^"\']*image_src[^"\']*["\'][^>]+href=["\']([^"\']+)',
        r'<img[^>]+src=["\']([^"\']+)',
    )
    for pattern in patterns:
        for raw in re.findall(pattern, page_html, re.IGNORECASE):
            candidate = urllib.parse.urljoin(source_url, html.unescape(raw).strip())
            parsed = urllib.parse.urlparse(candidate)
            if parsed.scheme == "https" and _allowed_asset_host(source_url, candidate) and candidate not in candidates:
                candidates.append(candidate)
    return candidates


def resolve_official_source_image(
    source_url: str,
    slug: str,
    timeout: int = 8,
) -> Optional[Dict[str, str]]:
    """Fetch and freeze the first usable official image from an announcement."""
    if not source_url or os.getenv("OFFLINE_MODE", "").lower() in {"1", "true", "yes"}:
        return None
    try:
        request = urllib.request.Request(
            source_url,
            headers={"User-Agent": "TheModelVerse/1.0 (+source-asset-resolver)"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            page_html = response.read(2_000_000).decode("utf-8", errors="ignore")
        candidates = extract_official_image_candidates(page_html, source_url)
        if not candidates:
            return None

        for image_url in candidates:
            try:
                image_request = urllib.request.Request(
                    image_url,
                    headers={"User-Agent": "TheModelVerse/1.0 (+source-asset-resolver)"},
                )
                with urllib.request.urlopen(image_request, timeout=timeout) as response:
                    content_type = (response.headers.get("Content-Type") or "").lower()
                    payload = response.read(MAX_IMAGE_BYTES + 1)
                if len(payload) > MAX_IMAGE_BYTES or not content_type.startswith("image/"):
                    continue
                suffix = ".webp" if "webp" in content_type else ".png" if "png" in content_type else ".jpg"
                digest = hashlib.sha256(payload).hexdigest()[:12]
                safe_slug = re.sub(r"[^a-z0-9_-]+", "_", slug.lower()).strip("_") or "announcement"
                output = SOURCE_ASSET_DIR / f"{safe_slug}_{digest}{suffix}"
                SOURCE_ASSET_DIR.mkdir(parents=True, exist_ok=True)
                if not output.exists():
                    output.write_bytes(payload)
                return {"role": "hero", "path": str(output), "source_url": image_url}
            except Exception:
                continue
    except Exception as exc:
        print(f"⚠️ Official source asset unavailable for {source_url}: {exc}")
    return None
