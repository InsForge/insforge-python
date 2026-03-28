from __future__ import annotations

import httpx


class InsforgeClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        url = httpx.URL(base_url)
        self.base_url = url.copy_with(path=url.path.rstrip("/"))
        self.api_key = api_key
