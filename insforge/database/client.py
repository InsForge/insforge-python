from __future__ import annotations

from .._base_client import BaseClient
from .._utils import quote_path_segment
from .models import DatabaseCreateTableRequest
from .models import DatabaseTableCreateColumn
from .models import DatabaseTableMutationResponse
from .models import DatabaseTableSchemaAddColumn
from .models import DatabaseTableSchemaAddForeignKey
from .models import DatabaseTableSchemaRenameRequest
from .models import DatabaseTableSchemaUpdateColumn
from .models import DatabaseTableSchemaUpdateRequest
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
            f"/api/database/tables/{quote_path_segment(table_name)}/schema",
            access_token=access_token,
        )
        return DatabaseTableSchemaResponse.model_validate(payload)

    async def create_table(
        self,
        *,
        table_name: str,
        columns: list[DatabaseTableCreateColumn | dict[str, object]],
        rls_enabled: bool | None = None,
        access_token: str | None = None,
    ) -> DatabaseTableMutationResponse:
        payload = DatabaseCreateTableRequest(
            table_name=table_name,
            columns=columns,
            rls_enabled=rls_enabled,
        ).model_dump(by_alias=True, exclude_none=True)
        response = await self._client._request_json(
            "POST",
            "/api/database/tables",
            json=payload,
            access_token=access_token,
        )
        return DatabaseTableMutationResponse.model_validate(response)

    async def update_table_schema(
        self,
        table_name: str,
        *,
        add_columns: list[DatabaseTableSchemaAddColumn | dict[str, object]] | None = None,
        drop_columns: list[str] | None = None,
        update_columns: list[DatabaseTableSchemaUpdateColumn | dict[str, object]] | None = None,
        add_foreign_keys: list[DatabaseTableSchemaAddForeignKey | dict[str, object]] | None = None,
        drop_foreign_keys: list[str] | None = None,
        rename_table: DatabaseTableSchemaRenameRequest | dict[str, object] | None = None,
        access_token: str | None = None,
    ) -> DatabaseTableMutationResponse:
        if not any(
            value is not None
            for value in (
                add_columns,
                drop_columns,
                update_columns,
                add_foreign_keys,
                drop_foreign_keys,
                rename_table,
            )
        ):
            raise ValueError("update_table_schema requires at least one schema operation")

        payload = DatabaseTableSchemaUpdateRequest(
            add_columns=add_columns,
            drop_columns=drop_columns,
            update_columns=update_columns,
            add_foreign_keys=add_foreign_keys,
            drop_foreign_keys=drop_foreign_keys,
            rename_table=rename_table,
        ).model_dump(by_alias=True, exclude_none=True)
        response = await self._client._request_json(
            "PATCH",
            f"/api/database/tables/{quote_path_segment(table_name)}/schema",
            json=payload,
            access_token=access_token,
        )
        return DatabaseTableMutationResponse.model_validate(response)

    async def delete_table(
        self,
        table_name: str,
        *,
        access_token: str | None = None,
    ) -> DatabaseTableMutationResponse:
        response = await self._client._request_json(
            "DELETE",
            f"/api/database/tables/{quote_path_segment(table_name)}",
            access_token=access_token,
        )
        return DatabaseTableMutationResponse.model_validate(response)
