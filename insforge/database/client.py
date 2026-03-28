from __future__ import annotations

from .._base_client import BaseClient
from .models import DatabaseTableSchemaResponse
from .query import DatabaseQuery


class DatabaseClient:
    def __init__(self, client: BaseClient) -> None:
        self._client = client

    def from_(self, table_name: str) -> DatabaseQuery:
        return DatabaseQuery(_client=self._client, _table_name=table_name)

    async def list_tables(self, *, access_token: str | None = None) -> list[str]:
        payload = await self._client._request_json(
            "GET",
            "/api/database/tables",
            access_token=access_token,
        )
        return list(payload)

    async def get_table_schema(
        self,
        table_name: str,
        *,
        access_token: str | None = None,
    ) -> DatabaseTableSchemaResponse:
        payload = await self._client._request_json(
            "GET",
            f"/api/database/tables/{table_name}/schema",
            access_token=access_token,
        )
        return DatabaseTableSchemaResponse.model_validate(payload)
