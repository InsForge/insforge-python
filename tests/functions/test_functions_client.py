import asyncio

import httpx

from insforge import InsforgeClient
from insforge.functions.models import FunctionDetails
from insforge.functions.models import FunctionMetadata


def test_invoke_without_access_token_is_anonymous_and_returns_json_object() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(200, json={"message": "hi", "received": {"name": "Ada"}})

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.functions.invoke("hello-world", body={"name": "Ada"})
            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.com/functions/hello-world"
    assert captured["kwargs"]["json"] == {"name": "Ada"}
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert "Authorization" not in captured["kwargs"]["headers"]
    assert result == {"message": "hi", "received": {"name": "Ada"}}


def test_invoke_with_access_token_sets_authorization_header() -> None:
    async def scenario() -> dict[str, object]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(200, json={"message": "hi"})

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.functions.invoke(
                "hello-world",
                body={"name": "Ada"},
                access_token="user_token",
            )
            assert result == {"message": "hi"}
            return captured

    captured = asyncio.run(scenario())

    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.com/functions/hello-world"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer user_token"


def test_invoke_returns_plain_text_for_text_responses() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                content=b"hello from runtime",
                headers={"Content-Type": "text/plain; charset=utf-8"},
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.functions.invoke("hello-world")
            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.com/functions/hello-world"
    assert result == "hello from runtime"


def test_invoke_returns_bytes_for_binary_responses() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                content=b"\x89PNG\r\n\x1a\n",
                headers={"Content-Type": "image/png"},
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.functions.invoke("hello-world")
            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.com/functions/hello-world"
    assert result == b"\x89PNG\r\n\x1a\n"


def test_list_functions_uses_api_path_and_returns_typed_models() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "slug": "hello-world",
                        "name": "Hello World Function",
                        "description": "Returns a greeting message",
                        "status": "active",
                        "created_at": "2024-01-21T10:30:00Z",
                        "updated_at": "2024-01-21T10:35:00Z",
                        "deployed_at": "2024-01-21T10:35:00Z",
                    }
                ],
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.functions.list_functions(access_token="admin_token")
            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "GET"
    assert captured["url"] == "https://example.com/api/functions"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer admin_token"
    assert len(result) == 1
    assert isinstance(result[0], FunctionMetadata)
    assert result[0].slug == "hello-world"
    assert result[0].name == "Hello World Function"


def test_get_function_uses_api_path_and_returns_full_function_details() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                json={
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "slug": "hello-world",
                    "name": "Hello World Function",
                    "description": "Returns a greeting message",
                    "code": "export default async function () { return new Response('hi'); }",
                    "status": "active",
                    "created_at": "2024-01-21T10:30:00Z",
                    "updated_at": "2024-01-21T10:35:00Z",
                    "deployed_at": None,
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.functions.get_function("hello-world", access_token="admin_token")
            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "GET"
    assert captured["url"] == "https://example.com/api/functions/hello-world"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer admin_token"
    assert isinstance(result, FunctionDetails)
    assert result.slug == "hello-world"
    assert result.code.startswith("export default")
