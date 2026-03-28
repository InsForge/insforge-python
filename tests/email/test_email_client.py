import asyncio

import httpx

from insforge import InsforgeClient


def test_send_raw_uses_explicit_access_token_and_request_body() -> None:
    async def scenario() -> dict[str, object]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(200, json={"message": "queued"})

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.email.send_raw(
                to="a@example.com",
                subject="Hi",
                html="<p>Hello</p>",
                access_token="user_token",
            )
            assert result == {"message": "queued"}
            return captured

    captured = asyncio.run(scenario())

    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.com/api/email/send-raw"
    assert captured["kwargs"]["json"] == {
        "to": "a@example.com",
        "subject": "Hi",
        "html": "<p>Hello</p>",
    }
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer user_token"

