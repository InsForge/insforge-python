from __future__ import annotations

from .._base_client import BaseClient
from .models import AIConfiguration


class AIClient:
    def __init__(self, client: BaseClient) -> None:
        self._client = client

    async def list_configurations(
        self,
        *,
        access_token: str | None = None,
    ) -> list[AIConfiguration]:
        payload = await self._client._request_json(
            "GET",
            "/api/ai/configurations",
            access_token=access_token,
        )
        return [AIConfiguration.model_validate(item) for item in payload]
