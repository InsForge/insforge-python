from __future__ import annotations

from .._base_client import BaseClient
from .models import ApiKeyMetadata
from .models import AppMetadata
from .models import DatabaseMetadata


class MetadataClient:
    def __init__(self, client: BaseClient) -> None:
        self._client = client

    async def get_app_metadata(
        self,
        *,
        access_token: str | None = None,
    ) -> AppMetadata:
        payload = await self._client._request_json(
            "GET",
            "/api/metadata",
            access_token=access_token,
        )
        return AppMetadata.model_validate(payload)

    async def get_database_metadata(
        self,
        *,
        access_token: str | None = None,
    ) -> DatabaseMetadata:
        payload = await self._client._request_json(
            "GET",
            "/api/metadata/database",
            access_token=access_token,
        )
        return DatabaseMetadata.model_validate(payload)

    async def get_api_key(
        self,
        *,
        access_token: str | None = None,
    ) -> ApiKeyMetadata:
        payload = await self._client._request_json(
            "GET",
            "/api/metadata/api-key",
            access_token=access_token,
        )
        return ApiKeyMetadata.model_validate(payload)
