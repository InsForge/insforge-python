import asyncio

import httpx

from insforge import InsforgeClient
from insforge.database.models import DatabaseTableSchemaResponse
from insforge.database.models import DatabaseTableMutationResponse


def test_list_tables_uses_api_key_only_by_default() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(200, json=["posts", "comments"])

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.database.list_tables()

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "GET"
    assert captured["url"] == "https://example.com/api/database/tables"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert "Authorization" not in captured["kwargs"]["headers"]
    assert result == ["posts", "comments"]


def test_get_table_schema_returns_typed_model_from_schema_endpoint() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                json={
                    "table_name": "posts",
                    "columns": [
                        {
                            "name": "id",
                            "type": "uuid",
                            "nullable": False,
                            "unique": True,
                            "default": "gen_random_uuid()",
                            "isPrimaryKey": True,
                            "foreignKey": None,
                        }
                    ],
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.database.get_table_schema("posts")

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "GET"
    assert captured["url"] == "https://example.com/api/database/tables/posts/schema"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert "Authorization" not in captured["kwargs"]["headers"]
    assert isinstance(result, DatabaseTableSchemaResponse)
    assert result.table_name == "posts"
    assert len(result.columns) == 1
    assert result.columns[0].name == "id"


def test_create_table_uses_post_schema_endpoint_and_serializes_request_body() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                201,
                json={
                    "message": "Table created successfully",
                    "tableName": "posts",
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.database.create_table(
                table_name="posts",
                columns=[
                    {
                        "name": "id",
                        "type": "uuid",
                        "nullable": False,
                        "unique": True,
                        "default_value": "gen_random_uuid()",
                    },
                    {
                        "name": "user_id",
                        "type": "uuid",
                        "nullable": False,
                        "foreign_key": {
                            "table": "auth.users",
                            "column": "id",
                            "on_delete": "CASCADE",
                        },
                    },
                ],
                rls_enabled=True,
                access_token="user_token",
            )

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.com/api/database/tables"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer user_token"
    assert captured["kwargs"]["json"] == {
        "tableName": "posts",
        "columns": [
            {
                "name": "id",
                "type": "uuid",
                "nullable": False,
                "unique": True,
                "defaultValue": "gen_random_uuid()",
            },
            {
                "name": "user_id",
                "type": "uuid",
                "nullable": False,
                "foreignKey": {
                    "table": "auth.users",
                    "column": "id",
                    "onDelete": "CASCADE",
                },
            },
        ],
        "rlsEnabled": True,
    }
    assert isinstance(result, DatabaseTableMutationResponse)
    assert result.message == "Table created successfully"
    assert result.table_name == "posts"


def test_update_table_schema_uses_patch_schema_endpoint_and_serializes_request_body() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                json={
                    "message": "Table schema updated successfully",
                    "tableName": "posts",
                    "operations": ["added 1 columns", "renamed 1 columns"],
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.database.update_table_schema(
                "posts",
                add_columns=[
                    {
                        "column_name": "published_at",
                        "type": "datetime",
                        "is_nullable": True,
                        "is_unique": False,
                    }
                ],
                update_columns=[
                    {
                        "column_name": "title",
                        "new_column_name": "headline",
                        "default_value": "draft",
                    }
                ],
                add_foreign_keys=[
                    {
                        "column_name": "user_id",
                        "foreign_key": {
                            "reference_table": "auth.users",
                            "reference_column": "id",
                            "on_delete": "RESTRICT",
                            "on_update": "CASCADE",
                        },
                    }
                ],
                drop_columns=["obsolete"],
                drop_foreign_keys=["legacy_user_id"],
                rename_table={"new_table_name": "articles"},
                access_token="user_token",
            )

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "PATCH"
    assert captured["url"] == "https://example.com/api/database/tables/posts/schema"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer user_token"
    assert captured["kwargs"]["json"] == {
        "addColumns": [
            {
                "columnName": "published_at",
                "type": "datetime",
                "isNullable": True,
                "isUnique": False,
            }
        ],
        "dropColumns": ["obsolete"],
        "updateColumns": [
            {
                "columnName": "title",
                "newColumnName": "headline",
                "defaultValue": "draft",
            }
        ],
        "addForeignKeys": [
            {
                "columnName": "user_id",
                "foreignKey": {
                    "referenceTable": "auth.users",
                    "referenceColumn": "id",
                    "onDelete": "RESTRICT",
                    "onUpdate": "CASCADE",
                },
            }
        ],
        "dropForeignKeys": ["legacy_user_id"],
        "renameTable": {"newTableName": "articles"},
    }
    assert isinstance(result, DatabaseTableMutationResponse)
    assert result.message == "Table schema updated successfully"
    assert result.table_name == "posts"
    assert result.operations == ["added 1 columns", "renamed 1 columns"]


def test_delete_table_uses_delete_endpoint_and_returns_mutation_response() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                json={
                    "message": "Table deleted successfully",
                    "tableName": "posts",
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.database.delete_table("posts", access_token="user_token")

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "DELETE"
    assert captured["url"] == "https://example.com/api/database/tables/posts"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer user_token"
    assert captured["kwargs"]["json"] is None
    assert isinstance(result, DatabaseTableMutationResponse)
    assert result.message == "Table deleted successfully"
    assert result.table_name == "posts"
