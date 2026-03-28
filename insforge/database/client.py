from __future__ import annotations

from .._base_client import BaseClient
from .query import DatabaseQuery


class DatabaseClient:
    def __init__(self, client: BaseClient) -> None:
        self._client = client

    def from_(self, table_name: str) -> DatabaseQuery:
        return DatabaseQuery(_client=self._client, _table_name=table_name)
