import asyncio

import httpx

from insforge import InsforgeClient


def test_database_query_builder_executes_select_eq_and_limit_with_bearer_token() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(200, json={"data": []})

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await (
                client.database.from_("posts")
                .select("id,title")
                .eq("status", "active")
                .limit(1)
                .execute(access_token="user_token")
            )

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "GET"
    assert captured["url"] == "https://example.com/api/database/records/posts"
    assert captured["kwargs"]["params"] == {
        "select": "id,title",
        "status": "eq.active",
        "limit": "1",
    }
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer user_token"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert result == {"data": []}
