from __future__ import annotations

import httpx


def normalize_base_url(base_url: str) -> httpx.URL:
    url = httpx.URL(base_url)
    return url.copy_with(path=url.path.rstrip("/"))
