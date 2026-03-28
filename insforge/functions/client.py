from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._base_client import BaseClient
from .._utils import quote_path_segment
from .models import FunctionDetails
from .models import FunctionMetadata


class FunctionsClient:
    def __init__(self, client: BaseClient) -> None:
        self._client = client

    async def list_functions(self, *, access_token: str | None = None) -> list[FunctionMetadata]:
        payload = await self._client._request_json(
            "GET",
            "/api/functions",
            access_token=access_token,
        )
        return [FunctionMetadata.model_validate(item) for item in payload]

    async def get_function(
        self,
        slug: str,
        *,
        access_token: str | None = None,
    ) -> FunctionDetails:
        payload = await self._client._request_json(
            "GET",
            f"/api/functions/{quote_path_segment(slug)}",
            access_token=access_token,
        )
        return FunctionDetails.model_validate(payload)

    async def invoke(
        self,
        slug: str,
        *,
        body: Mapping[str, Any] | None = None,
        access_token: str | None = None,
    ) -> object:
        return await self._client._request_content(
            "POST",
            f"/functions/{quote_path_segment(slug)}",
            json=dict(body) if body is not None else None,
            access_token=access_token,
        )
