import asyncio
import re
from pathlib import Path
import tomllib

import httpx
import pytest

from insforge import InsforgeClient
from insforge.exceptions import InsforgeHTTPError
from insforge.storage.models import StorageDownloadResult


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


def test_storage_methods_merge_extra_headers() -> None:
    async def scenario() -> list[dict[str, object]]:
        captured: list[dict[str, object]] = []

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured.append({"method": method, "headers": kwargs.get("headers"), "files": kwargs.get("files")})
            if method == "PUT":
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
            if method == "GET":
                return httpx.Response(
                    200,
                    content=b"bytes",
                    headers={"Content-Type": "image/png"},
                )
            return httpx.Response(200, json={"message": "Object deleted"})

        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            await client.storage.upload_object("avatars", "me.png", b"data", extra_headers={"X-Custom": "value"})
            await client.storage.download_object("avatars", "me.png", extra_headers={"X-Custom": "value"})
            await client.storage.delete_object("avatars", "me.png", extra_headers={"X-Custom": "value"})
            return captured

    captures = asyncio.run(scenario())
    assert captures[0]["headers"]["X-Custom"] == "value"
    assert captures[1]["headers"]["X-Custom"] == "value"
    assert captures[2]["headers"]["X-Custom"] == "value"


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


def test_download_object_returns_bytes_and_headers() -> None:
    async def scenario() -> tuple[StorageDownloadResult, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                content=b"png-bytes",
                headers={"Content-Type": "image/png", "Content-Length": "9"},
            )

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
    assert result.content == b"png-bytes"
    assert result.content_length is not None


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
    assert result.content == b"plain-bytes"


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


def test_bucket_admin_endpoints_and_object_listing() -> None:
    async def scenario() -> tuple[list[dict[str, object]], object]:
        calls: list[dict[str, object]] = []

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            calls.append({"method": method, "url": str(url), "kwargs": kwargs})
            if method == "POST" and url.path.endswith("/api/storage/buckets"):
                return httpx.Response(201, json={"message": "Bucket created successfully", "bucketName": "avatars"})
            if method == "PATCH":
                return httpx.Response(200, json={"message": "Bucket visibility updated", "bucket": "avatars", "isPublic": True})
            if method == "DELETE":
                return httpx.Response(200, json={"message": "Bucket deleted successfully", "nextActions": "foo"})
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "bucket": "avatars",
                            "key": "file.png",
                            "size": 10,
                            "mimeType": "image/png",
                            "uploadedAt": "2024-01-01T00:00:00Z",
                            "url": "/api/storage/buckets/avatars/objects/file.png",
                        }
                    ],
                    "pagination": {"offset": 0, "limit": 1, "total": 1},
                },
            )

        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            bucket = await client.storage.create_bucket(bucket_name="avatars", is_public=True)
            updated = await client.storage.update_bucket("avatars", is_public=True)
            deleted = await client.storage.delete_bucket("avatars")
            objects = await client.storage.list_objects("avatars", prefix="file", limit=1, offset=0, search="file")
            return calls, (bucket, updated, deleted, objects)

    calls, results = asyncio.run(scenario())
    bucket, updated, deleted, objects = results

    assert calls[0]["method"] == "POST"
    assert calls[0]["kwargs"]["json"] == {"bucketName": "avatars", "isPublic": True}
    assert bucket.bucket_name == "avatars"

    assert calls[1]["method"] == "PATCH"
    assert calls[1]["kwargs"]["json"] == {"isPublic": True}
    assert updated.bucket == "avatars"

    assert calls[2]["method"] == "DELETE"
    assert deleted.message == "Bucket deleted successfully"
    assert deleted.next_actions == "foo"

    assert calls[3]["method"] == "GET"
    assert calls[3]["kwargs"]["params"] == {"prefix": "file", "limit": "1", "offset": "0", "search": "file"}
    assert objects.data[0].key == "file.png"


def test_upload_auto_and_strategy_endpoints() -> None:
    async def scenario() -> tuple[list[dict[str, object]], object, object, object]:
        calls: list[dict[str, object]] = []

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            calls.append({"method": method, "url": str(url), "kwargs": kwargs})
            if method == "PUT":
                return httpx.Response(
                    201,
                    json={
                        "bucket": "avatars",
                        "key": url.path.rsplit("/objects/", 1)[-1],
                        "size": 10,
                        "mimeType": "image/jpeg",
                        "uploadedAt": "2024-01-01T00:00:00Z",
                        "url": str(url.path),
                    },
                )
            if url.path.endswith("/confirm-upload"):
                return httpx.Response(
                    201,
                    json={
                        "bucket": "avatars",
                        "key": "auto.jpg",
                        "size": 10,
                        "mimeType": "image/jpeg",
                        "uploadedAt": "2024-01-01T00:00:00Z",
                        "url": "/api/storage/buckets/avatars/objects/auto.jpg",
                    },
                )
            if url.path.endswith("/upload-strategy"):
                return httpx.Response(
                    200,
                    json={
                        "method": "presigned",
                        "uploadUrl": "https://example.com/upload",
                        "key": "auto.jpg",
                        "confirmRequired": True,
                        "confirmUrl": "/confirm",
                        "expiresAt": "2025-01-01T00:00:00Z",
                    },
                )
            return httpx.Response(
                200,
                json={"method": "direct", "url": "/download", "expiresAt": "2025-01-01T00:00:00Z"},
            )

        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            auto = await client.storage.upload_object_auto("avatars", data=b"bytes", filename="auto.jpg")
            confirm = await client.storage.confirm_upload("avatars", "auto.jpg", size=10, etag="etag123")
            upload_strategy = await client.storage.get_upload_strategy("avatars", filename="auto.jpg", content_type="image/jpeg", size=10)
            download_strategy = await client.storage.get_download_strategy("avatars", "auto.jpg", expires_in=3600)
            return calls, auto, confirm, upload_strategy, download_strategy

    calls, auto, confirm, upload_strategy, download_strategy = asyncio.run(scenario())

    # upload_object_auto mints a unique key client-side and uploads via the
    # standard PUT route — the backend no longer generates keys.
    assert calls[0]["method"] == "PUT"
    assert re.search(r"/objects/auto-\d+-[a-z0-9]{6}\.jpg$", calls[0]["url"])
    assert re.fullmatch(r"auto-\d+-[a-z0-9]{6}\.jpg", auto.key)

    assert calls[1]["method"] == "POST" and calls[1]["url"].endswith("/confirm-upload")
    assert calls[1]["kwargs"]["json"] == {"size": 10, "etag": "etag123"}
    assert confirm.key == "auto.jpg"

    assert calls[2]["method"] == "POST" and calls[2]["url"].endswith("/upload-strategy")
    assert calls[2]["kwargs"]["json"] == {
        "filename": "auto.jpg",
        "contentType": "image/jpeg",
        "size": 10,
    }
    assert upload_strategy.method == "presigned"

    assert calls[3]["method"] == "POST" and calls[3]["url"].endswith("/download-strategy")
    assert calls[3]["kwargs"]["json"] == {"expiresIn": 3600}
    assert download_strategy.method == "direct"


def test_upload_object_auto_mints_key_client_side_and_uses_put() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            key = url.path.rsplit("/objects/", 1)[-1]
            return httpx.Response(
                201,
                json={
                    "bucket": "docs",
                    "key": key,
                    "size": 3,
                    "mimeType": "application/pdf",
                    "uploadedAt": "2026-01-01T00:00:00Z",
                    "url": str(url.path),
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.storage.upload_object_auto(
                "docs",
                data=b"pdf",
                filename="report.pdf",
                content_type="application/pdf",
            )
            return result, captured

    result, captured = asyncio.run(scenario())

    # Client-generated key: sanitized base + timestamp + random, preserving ext.
    assert captured["method"] == "PUT"
    assert re.fullmatch(r"report-\d+-[a-z0-9]{6}\.pdf", result.key)
    assert captured["url"].endswith(f"/api/storage/buckets/docs/objects/{result.key}")
    assert captured["kwargs"]["files"]["file"] == (result.key, b"pdf", "application/pdf")


def test_upload_object_auto_generates_distinct_keys_for_same_filename() -> None:
    async def scenario() -> list[str]:
        keys: list[str] = []

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            key = url.path.rsplit("/objects/", 1)[-1]
            keys.append(key)
            return httpx.Response(
                201,
                json={
                    "bucket": "docs",
                    "key": key,
                    "size": 3,
                    "mimeType": "application/octet-stream",
                    "uploadedAt": "2026-01-01T00:00:00Z",
                    "url": str(url.path),
                },
            )

        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            await client.storage.upload_object_auto("docs", data=b"abc", filename="photo.png")
            await client.storage.upload_object_auto("docs", data=b"abc", filename="photo.png")
            return keys

    keys = asyncio.run(scenario())

    assert len(keys) == 2
    assert keys[0] != keys[1]


def test_generate_object_key_sanitizes_base_and_falls_back_to_file() -> None:
    from insforge.storage.client import _generate_object_key

    # Non-alphanumeric characters in the base are replaced, extension kept.
    assert re.fullmatch(r"my-r-sum--v2-\d+-[a-z0-9]{6}\.pdf", _generate_object_key("my résumé v2.pdf"))
    # Base longer than 32 chars is truncated.
    key = _generate_object_key("a" * 50 + ".txt")
    assert re.fullmatch(r"a{32}-\d+-[a-z0-9]{6}\.txt", key)
    # Disallowed characters are each replaced with a dash.
    assert re.fullmatch(r"----\d+-[a-z0-9]{6}", _generate_object_key("日本語"))
    # An empty base falls back to "file".
    assert re.fullmatch(r"file-\d+-[a-z0-9]{6}", _generate_object_key(""))
    # A leading dot is not treated as an extension separator.
    assert re.fullmatch(r"-gitignore-\d+-[a-z0-9]{6}", _generate_object_key(".gitignore"))


def test_storage_encoding_for_new_admin_paths() -> None:
    async def scenario() -> list[dict[str, object]]:
        calls: list[dict[str, object]] = []

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            calls.append({"method": method, "url": str(url), "kwargs": kwargs})
            if method == "PATCH":
                return httpx.Response(200, json={"message": "Bucket visibility updated", "bucket": "av atars", "isPublic": True})
            if method == "DELETE":
                return httpx.Response(200, json={"message": "Bucket deleted successfully"})
            if url.path.endswith("/confirm-upload"):
                return httpx.Response(
                    201,
                    json={
                        "bucket": "my bucket",
                        "key": "dir/file.txt",
                        "size": 1,
                        "mimeType": "application/octet-stream",
                        "uploadedAt": "2024-01-01T00:00:00Z",
                        "url": "/api/storage/buckets/my%20bucket/objects/dir%2Ffile.txt",
                    },
                )
            if url.path.endswith("/upload-strategy"):
                return httpx.Response(
                    200,
                    json={
                        "method": "presigned",
                        "uploadUrl": "https://example.com/upload",
                        "key": "dir/file.txt",
                        "confirmRequired": True,
                        "confirmUrl": "/confirm",
                    },
                )
            if url.path.endswith("/download-strategy"):
                return httpx.Response(
                    200,
                    json={"method": "direct", "url": "/download"},
                )
            return httpx.Response(200, json={"message": "ok"})

        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            await client.storage.update_bucket("av atars", is_public=True, access_token="admin")
            await client.storage.delete_bucket("av atars", access_token="admin")
            await client.storage.confirm_upload("my bucket", "dir/file.txt", size=1, access_token="admin")
            await client.storage.get_upload_strategy("my bucket", filename="file.txt", access_token="admin")
            await client.storage.get_download_strategy("my bucket", "dir/file.txt", expires_in=10, access_token="admin")
            return calls

    calls = asyncio.run(scenario())
    assert "av%20atars" in calls[0]["url"]
    assert "av%20atars" in calls[1]["url"]
    assert "/confirm-upload" in calls[2]["url"]
    assert "/upload-strategy" in calls[3]["url"]
    assert "/download-strategy" in calls[4]["url"]
