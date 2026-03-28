from __future__ import annotations

import httpx
from urllib.parse import quote


def normalize_base_url(base_url: str) -> httpx.URL:
    url = httpx.URL(base_url)
    return url.copy_with(path=url.path.rstrip("/"))


def quote_path_segment(value: str, *, preserve_slashes: bool = False) -> str:
    safe_chars = "/" if preserve_slashes else ""
    return quote(value, safe=safe_chars)
