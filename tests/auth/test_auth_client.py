import asyncio

import httpx
import pytest

from insforge import InsforgeClient
from insforge.exceptions import InsforgeAuthError


def test_sign_in_with_password_returns_tokens_without_mutating_client_state() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                json={
                    "accessToken": "access",
                    "refreshToken": "refresh",
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.auth.sign_in_with_password(
                email="a@example.com",
                password="secret",
            )

            assert client.api_key == "ins_test"
            assert not hasattr(client, "access_token")
            assert not hasattr(client, "refresh_token")
            return result, captured

    result, captured = asyncio.run(scenario())

    assert result.access_token == "access"
    assert result.refresh_token == "refresh"
    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.com/api/auth/sessions?client_type=server"
    assert captured["kwargs"]["json"] == {"email": "a@example.com", "password": "secret"}
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"


def test_update_current_profile_sends_bearer_token() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                json={
                    "userId": "u1",
                    "profile": {"name": "Ada"},
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.auth.update_current_profile(
                {"name": "Ada"},
                access_token="user_token",
            )

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "PATCH"
    assert captured["url"] == "https://example.com/api/auth/profiles/current"
    assert captured["kwargs"]["json"] == {"profile": {"name": "Ada"}}
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer user_token"
    assert result.user_id == "u1"
    assert result.profile == {"name": "Ada"}


def test_sign_in_with_password_raises_insforge_auth_error_on_failure() -> None:
    async def scenario() -> None:
        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            return httpx.Response(
                401,
                json={
                    "error": "UNAUTHORIZED",
                    "message": "Invalid credentials",
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            await client.auth.sign_in_with_password(
                email="a@example.com",
                password="secret",
            )

    with pytest.raises(InsforgeAuthError) as exc_info:
        asyncio.run(scenario())

    assert exc_info.value.error == "UNAUTHORIZED"
    assert exc_info.value.message == "Invalid credentials"
