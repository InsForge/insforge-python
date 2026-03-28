from __future__ import annotations

from dataclasses import dataclass, replace

from .._base_client import BaseClient


@dataclass(frozen=True, slots=True)
class DatabaseQuery:
    _client: BaseClient
    _table_name: str
    _select: str | None = None
    _filters: tuple[tuple[str, str], ...] = ()
    _limit: int | None = None

    def select(self, columns: str) -> "DatabaseQuery":
        return replace(self, _select=columns)

    def eq(self, column: str, value: str) -> "DatabaseQuery":
        return replace(self, _filters=self._filters + ((column, f"eq.{value}"),))

    def limit(self, value: int) -> "DatabaseQuery":
        return replace(self, _limit=value)

    async def execute(self, *, access_token: str | None = None) -> object:
        params: dict[str, str] = {}

        if self._select is not None:
            params["select"] = self._select

        for column, value in self._filters:
            params[column] = value

        if self._limit is not None:
            params["limit"] = str(self._limit)

        return await self._client._request_json(
            "GET",
            f"/api/database/records/{self._table_name}",
            params=params or None,
            access_token=access_token,
        )
