from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any

from .._base_client import BaseClient


@dataclass(frozen=True, slots=True)
class DatabaseQuery:
    _client: BaseClient
    _table_name: str
    _params: tuple[tuple[str, str], ...] = ()

    def _with_param(self, key: str, value: str) -> "DatabaseQuery":
        return replace(self, _params=self._params + ((key, value),))

    def _build_params(self) -> dict[str, str]:
        return {key: value for key, value in self._params}

    def select(self, columns: str = "*") -> "DatabaseQuery":
        return self._with_param("select", columns)

    def eq(self, column: str, value: object) -> "DatabaseQuery":
        return self._with_param(column, f"eq.{value}")

    def neq(self, column: str, value: object) -> "DatabaseQuery":
        return self._with_param(column, f"neq.{value}")

    def gt(self, column: str, value: object) -> "DatabaseQuery":
        return self._with_param(column, f"gt.{value}")

    def gte(self, column: str, value: object) -> "DatabaseQuery":
        return self._with_param(column, f"gte.{value}")

    def lt(self, column: str, value: object) -> "DatabaseQuery":
        return self._with_param(column, f"lt.{value}")

    def lte(self, column: str, value: object) -> "DatabaseQuery":
        return self._with_param(column, f"lte.{value}")

    def like(self, column: str, value: object) -> "DatabaseQuery":
        return self._with_param(column, f"like.{value}")

    def ilike(self, column: str, value: object) -> "DatabaseQuery":
        return self._with_param(column, f"ilike.{value}")

    def in_(self, column: str, values: Sequence[object]) -> "DatabaseQuery":
        joined_values = ",".join(str(value) for value in values)
        return self._with_param(column, f"in.({joined_values})")

    def is_null(self, column: str, value: bool = True) -> "DatabaseQuery":
        return self._with_param(column, "is.null" if value else "not.is.null")

    def order(self, column: str, desc: bool = False) -> "DatabaseQuery":
        direction = "desc" if desc else "asc"
        return self._with_param("order", f"{column}.{direction}")

    def limit(self, value: int) -> "DatabaseQuery":
        return self._with_param("limit", str(value))

    def offset(self, value: int) -> "DatabaseQuery":
        return self._with_param("offset", str(value))

    async def execute(self, *, access_token: str | None = None) -> object:
        return await self._client._request_json(
            "GET",
            f"/api/database/records/{self._table_name}",
            params=self._build_params() or None,
            access_token=access_token,
        )

    async def insert(
        self,
        rows: list[dict[str, Any]],
        *,
        return_representation: bool = False,
        access_token: str | None = None,
    ) -> list[dict[str, Any]]:
        response = await self._client._request(
            "POST",
            f"/api/database/records/{self._table_name}",
            params=self._build_params() or None,
            json=rows,
            access_token=access_token,
            extra_headers={"Prefer": "return=representation"} if return_representation else None,
        )
        payload = response.json()
        return payload if isinstance(payload, list) else []

    async def update(
        self,
        values: dict[str, Any],
        *,
        return_representation: bool = False,
        access_token: str | None = None,
    ) -> list[dict[str, Any]]:
        response = await self._client._request(
            "PATCH",
            f"/api/database/records/{self._table_name}",
            params=self._build_params() or None,
            json=values,
            access_token=access_token,
            extra_headers={"Prefer": "return=representation"} if return_representation else None,
        )
        payload = response.json()
        return payload if isinstance(payload, list) else []

    async def delete(
        self,
        *,
        return_representation: bool = False,
        access_token: str | None = None,
    ) -> list[dict[str, Any]]:
        response = await self._client._request(
            "DELETE",
            f"/api/database/records/{self._table_name}",
            params=self._build_params() or None,
            access_token=access_token,
            extra_headers={"Prefer": "return=representation"} if return_representation else None,
        )

        if response.status_code == 204:
            return []

        payload = response.json()
        return payload if isinstance(payload, list) else []
