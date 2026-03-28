from __future__ import annotations

from typing import Mapping

from ._utils import normalize_base_url


def build_headers(
    api_key: str,
    access_token: str | None = None,
    extra_headers: Mapping[str, str] | None = None,
) -> dict[str, str]:
    headers: dict[str, str] = {"X-API-Key": api_key}
    reserved_headers = {"authorization", "x-api-key"}

    if access_token is not None:
        headers["Authorization"] = f"Bearer {access_token}"

    for key, value in (extra_headers or {}).items():
        if key.lower() not in reserved_headers:
            headers[key] = value

    return headers


class BaseClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = normalize_base_url(base_url)
        self.api_key = api_key

    def _build_headers(
        self,
        *,
        access_token: str | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> dict[str, str]:
        return build_headers(
            api_key=self.api_key,
            access_token=access_token,
            extra_headers=extra_headers,
        )
