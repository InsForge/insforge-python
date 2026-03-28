import asyncio

import httpx

from insforge import InsforgeClient
from insforge.database.models import DatabaseTableSchemaResponse


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
