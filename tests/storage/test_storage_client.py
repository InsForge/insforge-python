import asyncio

import httpx

from insforge import InsforgeClient


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
