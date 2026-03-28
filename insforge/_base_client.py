from __future__ import annotations

from typing import Any
from typing import Mapping
from urllib.parse import urlsplit

import httpx

from .exceptions import InsforgeHTTPError
from ._utils import normalize_base_url


def build_headers(
    api_key: str,
    access_token: str | None = None,
    extra_headers: Mapping[str, str] | None = None,
) -> dict[str, str]:
    headers: dict[str, str] = {"X-API-Key": api_key}
    reserved_headers = {"authorization", "x-api-key"}

    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    for key, value in (extra_headers or {}).items():
        if key.lower() not in reserved_headers:
            headers[key] = value

    return headers


class BaseClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = normalize_base_url(base_url)
        self.api_key = api_key
        self.http_client = httpx.AsyncClient()

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

    def _build_url(self, path: str) -> httpx.URL:
        parsed_path = urlsplit(path)
        normalized_path = parsed_path.path.lstrip("/")
        base_path = self.base_url.path.rstrip("/")

        if base_path:
            full_path = f"{base_path}/{normalized_path}"
        else:
            full_path = f"/{normalized_path}"

        query = parsed_path.query.encode() if parsed_path.query else None

        return self.base_url.copy_with(path=full_path, query=query)

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
        json: Any = None,
        access_token: str | None = None,
        extra_headers: Mapping[str, str] | None = None,
        exception_cls: type[InsforgeHTTPError] = InsforgeHTTPError,
    ) -> object:
        response = await self._request(
            method,
            path,
            params=params,
            json=json,
            access_token=access_token,
            extra_headers=extra_headers,
            exception_cls=exception_cls,
        )

        return response.json()

    async def _request_content(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
        json: Any = None,
        access_token: str | None = None,
        extra_headers: Mapping[str, str] | None = None,
        exception_cls: type[InsforgeHTTPError] = InsforgeHTTPError,
    ) -> object:
        response = await self._request(
            method,
            path,
            params=params,
            json=json,
            access_token=access_token,
            extra_headers=extra_headers,
            exception_cls=exception_cls,
        )

        content_type = response.headers.get("content-type", "").split(";", maxsplit=1)[0].strip().lower()

        if content_type.startswith("text/"):
            return response.text

        if content_type.endswith("+json") or content_type == "application/json":
            return response.json()

        return response.content

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
        json: Any = None,
        access_token: str | None = None,
        extra_headers: Mapping[str, str] | None = None,
        exception_cls: type[InsforgeHTTPError] = InsforgeHTTPError,
    ) -> httpx.Response:
        response = await self.http_client.request(
            method,
            self._build_url(path),
            params=params,
            json=json,
            headers=self._build_headers(
                access_token=access_token,
                extra_headers=extra_headers,
            ),
        )

        if response.is_error:
            raise exception_cls.from_response(method, path, response)

        return response

    async def aclose(self) -> None:
        await self.http_client.aclose()

    async def __aenter__(self) -> "BaseClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()
