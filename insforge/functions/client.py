from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from typing import Literal

from .._base_client import BaseClient
from .._utils import quote_path_segment
from .models import FunctionCreateRequest
from .models import FunctionDetails
from .models import FunctionDeleteResponse
from .models import FunctionMutationResponse
from .models import FunctionMetadata
from .models import FunctionUpdateRequest


class FunctionsClient:
    def __init__(self, client: BaseClient) -> None:
        self._client = client

    async def create_function(
        self,
        *,
        name: str,
        slug: str | None = None,
        code: str,
        description: str | None = None,
        status: Literal["draft", "active"] | None = None,
        access_token: str | None = None,
    ) -> FunctionMutationResponse:
        payload = FunctionCreateRequest(
            name=name,
            slug=slug,
            code=code,
            description=description,
            status=status,
        ).model_dump(exclude_none=True)
        response = await self._client._request_json(
            "POST",
            "/api/functions",
            json=payload,
            access_token=access_token,
        )
        return FunctionMutationResponse.model_validate(response)

    async def update_function(
        self,
        slug: str,
        *,
        name: str | None = None,
        code: str | None = None,
        description: str | None = None,
        status: Literal["draft", "active", "error"] | None = None,
        access_token: str | None = None,
    ) -> FunctionMutationResponse:
        payload = FunctionUpdateRequest(
            name=name,
            code=code,
            description=description,
            status=status,
        ).model_dump(exclude_none=True)
        response = await self._client._request_json(
            "PUT",
            f"/api/functions/{quote_path_segment(slug)}",
            json=payload,
            access_token=access_token,
        )
        return FunctionMutationResponse.model_validate(response)

    async def delete_function(
        self,
        slug: str,
        *,
        access_token: str | None = None,
    ) -> FunctionDeleteResponse:
        response = await self._client._request_json(
            "DELETE",
            f"/api/functions/{quote_path_segment(slug)}",
            access_token=access_token,
        )
        return FunctionDeleteResponse.model_validate(response)

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
