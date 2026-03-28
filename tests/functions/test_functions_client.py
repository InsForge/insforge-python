import asyncio

import httpx
import pytest
from pydantic import ValidationError

from insforge import InsforgeClient
from insforge.functions.models import FunctionDeleteResponse
from insforge.functions.models import FunctionDetails
from insforge.functions.models import FunctionMutationResponse
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
                json={
                    "functions": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "slug": "hello-world",
                            "name": "Hello World Function",
                            "description": "Returns a greeting message",
                            "status": "active",
                            "createdAt": "2024-01-21T10:30:00Z",
                            "updatedAt": "2024-01-21T10:35:00Z",
                            "deployedAt": "2024-01-21T10:35:00Z",
                        }
                    ],
                },
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


def test_create_function_uses_api_path_and_returns_typed_mutation_response() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                201,
                json={
                    "success": True,
                    "function": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "slug": "hello-world",
                        "name": "Hello World Function",
                        "description": "Returns a greeting message",
                        "status": "active",
                        "created_at": "2024-01-21T10:30:00Z",
                        "updated_at": "2024-01-21T10:35:00Z",
                        "deployed_at": "2024-01-21T10:35:00Z",
                    },
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.functions.create_function(
                name="Hello World Function",
                slug="hello-world",
                code="export default async function () { return new Response('hi'); }",
                description="Returns a greeting message",
                status="active",
                access_token="admin_token",
            )
            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.com/api/functions"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer admin_token"
    assert captured["kwargs"]["json"] == {
        "name": "Hello World Function",
        "slug": "hello-world",
        "code": "export default async function () { return new Response('hi'); }",
        "description": "Returns a greeting message",
        "status": "active",
    }
    assert isinstance(result, FunctionMutationResponse)
    assert result.success is True
    assert isinstance(result.function, FunctionMetadata)
    assert result.function.slug == "hello-world"


def test_update_function_uses_api_path_and_returns_typed_mutation_response() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "function": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "slug": "hello-world",
                        "name": "Hello World Function v2",
                        "description": "Returns a greeting message",
                        "status": "active",
                        "created_at": "2024-01-21T10:30:00Z",
                        "updated_at": "2024-01-21T11:00:00Z",
                        "deployed_at": "2024-01-21T10:35:00Z",
                    },
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.functions.update_function(
                "hello-world",
                name="Hello World Function v2",
                code="export default async function () { return new Response('hi'); }",
                description="Returns a greeting message",
                status="active",
                access_token="admin_token",
            )
            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "PUT"
    assert captured["url"] == "https://example.com/api/functions/hello-world"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer admin_token"
    assert captured["kwargs"]["json"] == {
        "name": "Hello World Function v2",
        "code": "export default async function () { return new Response('hi'); }",
        "description": "Returns a greeting message",
        "status": "active",
    }
    assert isinstance(result, FunctionMutationResponse)
    assert result.success is True
    assert result.function.name == "Hello World Function v2"


def test_delete_function_uses_api_path_and_returns_typed_delete_response() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "message": "Function hello-world deleted successfully",
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.functions.delete_function(
                "hello-world",
                access_token="admin_token",
            )
            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "DELETE"
    assert captured["url"] == "https://example.com/api/functions/hello-world"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer admin_token"
    assert captured["kwargs"].get("json") is None
    assert isinstance(result, FunctionDeleteResponse)
    assert result.success is True
    assert result.message == "Function hello-world deleted successfully"


def test_create_function_rejects_invalid_inputs() -> None:
    async def scenario() -> None:
        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            await client.functions.create_function(
                name="",
                slug="Bad Slug!",
                code="",
                status="invalid",  # type: ignore[arg-type]
                access_token="admin_token",
            )

    with pytest.raises(ValidationError):
        asyncio.run(scenario())


def test_update_function_requires_at_least_one_field() -> None:
    async def scenario() -> None:
        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            await client.functions.update_function("hello-world", access_token="admin_token")

    with pytest.raises(ValueError):
        asyncio.run(scenario())
