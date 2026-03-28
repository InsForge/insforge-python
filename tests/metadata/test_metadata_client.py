import asyncio

import httpx

from insforge import InsforgeClient
from insforge.metadata.models import AppMetadata
from insforge.metadata.models import ApiKeyMetadata
from insforge.metadata.models import DatabaseMetadata


def test_get_app_metadata_uses_api_key_by_default() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                json={
                    "name": "Insforge Backend",
                    "version": "2.0.0",
                    "environment": "production",
                    "database": {
                        "host": "db.example.com",
                        "port": 5432,
                        "database": "insforge",
                        "ssl": True,
                    },
                    "uptime": 86400,
                    "timestamp": "2026-03-28T00:00:00Z",
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.metadata.get_app_metadata()
            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "GET"
    assert captured["url"] == "https://example.com/api/metadata"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert "Authorization" not in captured["kwargs"]["headers"]
    assert isinstance(result, AppMetadata)
    assert result.name == "Insforge Backend"
    assert result.database.host == "db.example.com"


def test_get_database_metadata_uses_explicit_access_token() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                json={
                    "tables": [
                        {"name": "posts", "recordCount": 42},
                        {"name": "comments", "recordCount": 57},
                    ],
                    "totalTables": 2,
                    "totalRecords": 99,
                    "databaseSize": "128 MB",
                    "lastUpdated": "2026-03-28T00:00:00Z",
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.metadata.get_database_metadata(access_token="admin_token")
            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "GET"
    assert captured["url"] == "https://example.com/api/metadata/database"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer admin_token"
    assert isinstance(result, DatabaseMetadata)
    assert result.total_records == 99
    assert result.tables[0].name == "posts"


def test_get_api_key_returns_typed_model() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(200, json={"apiKey": "ins_1234567890abcdef"})

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.metadata.get_api_key(access_token="admin_token")
            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "GET"
    assert captured["url"] == "https://example.com/api/metadata/api-key"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer admin_token"
    assert isinstance(result, ApiKeyMetadata)
    assert result.api_key == "ins_1234567890abcdef"
