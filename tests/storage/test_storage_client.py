import asyncio
from pathlib import Path
import tomllib

import httpx
import pytest

from insforge import InsforgeClient
from insforge.exceptions import InsforgeHTTPError


def test_pyproject_includes_storage_package_metadata() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())

    assert "insforge.storage" in pyproject["tool"]["setuptools"]["packages"]


def test_list_buckets_uses_api_key_only_by_default_and_returns_bucket_names() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(200, json={"buckets": ["avatars", "documents"]})

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.storage.list_buckets()

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "GET"
    assert captured["url"] == "https://example.com/api/storage/buckets"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert "Authorization" not in captured["kwargs"]["headers"]
    assert result.buckets == ["avatars", "documents"]


def test_upload_object_uses_put_multipart_form_upload() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                201,
                json={
                    "bucket": "avatars",
                    "key": "me.png",
                    "size": 9,
                    "mimeType": "image/png",
                    "uploadedAt": "2024-01-21T10:30:00Z",
                    "url": "/api/storage/buckets/avatars/objects/me.png",
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.storage.upload_object(
                "avatars",
                "me.png",
                b"png-bytes",
                content_type="image/png",
            )

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "PUT"
    assert captured["url"] == "https://example.com/api/storage/buckets/avatars/objects/me.png"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert captured["kwargs"]["files"]["file"] == ("me.png", b"png-bytes", "image/png")
    assert result.key == "me.png"


def test_upload_object_encodes_reserved_characters_in_object_key() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                201,
                json={
                    "bucket": "avatars",
                    "key": "a#b.txt",
                    "size": 9,
                    "mimeType": "text/plain",
                    "uploadedAt": "2024-01-21T10:30:00Z",
                    "url": "/api/storage/buckets/avatars/objects/a%23b.txt",
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.storage.upload_object("avatars", "a#b.txt", b"data")

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["url"] == "https://example.com/api/storage/buckets/avatars/objects/a%23b.txt"
    assert result.key == "a#b.txt"


def test_download_object_returns_raw_bytes() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(200, content=b"png-bytes")

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.storage.download_object("avatars", "me.png")

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "GET"
    assert captured["url"] == "https://example.com/api/storage/buckets/avatars/objects/me.png"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert result == b"png-bytes"


def test_download_object_encodes_reserved_characters_in_object_key() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(200, content=b"plain-bytes")

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.storage.download_object("avatars", "a?b.txt")

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["url"] == "https://example.com/api/storage/buckets/avatars/objects/a%3Fb.txt"
    assert result == b"plain-bytes"


def test_delete_object_uses_delete_and_returns_success_payload() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(200, json={"message": "Object deleted successfully"})

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.storage.delete_object("avatars", "me.png")

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "DELETE"
    assert captured["url"] == "https://example.com/api/storage/buckets/avatars/objects/me.png"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert result.message == "Object deleted successfully"


def test_upload_object_raises_insforge_http_error_on_failure() -> None:
    async def scenario() -> None:
        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            return httpx.Response(
                500,
                json={
                    "error": "UPLOAD_FAILED",
                    "message": "Upload failed",
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            await client.storage.upload_object("avatars", "me.png", b"png-bytes")

    with pytest.raises(InsforgeHTTPError) as exc_info:
        asyncio.run(scenario())

    assert exc_info.value.status_code == 500
