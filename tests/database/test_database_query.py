import asyncio

import httpx

from insforge import InsforgeClient


def test_database_query_builder_maps_common_read_operators_and_pagination() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(200, json=[])

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await (
                client.database.from_("posts")
                .select("id,title")
                .eq("status", "active")
                .neq("category", "archived")
                .gt("score", 10)
                .gte("rank", 20)
                .lt("views", 100)
                .lte("likes", 50)
                .like("title", "%guide%")
                .ilike("slug", "%getting-started%")
                .in_("id", ["1", "2", "3"])
                .is_null("deleted_at")
                .order("createdAt", desc=True)
                .limit(25)
                .offset(50)
                .execute(access_token="user_token")
            )

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "GET"
    assert captured["url"] == "https://example.com/api/database/records/posts"
    assert captured["kwargs"]["params"] == {
        "select": "id,title",
        "status": "eq.active",
        "category": "neq.archived",
        "score": "gt.10",
        "rank": "gte.20",
        "views": "lt.100",
        "likes": "lte.50",
        "title": "like.%guide%",
        "slug": "ilike.%getting-started%",
        "id": "in.(1,2,3)",
        "deleted_at": "is.null",
        "order": "createdAt.desc",
        "limit": "25",
        "offset": "50",
    }
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer user_token"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert result == []


def test_database_query_builder_serializes_boolean_and_null_filter_values() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(200, json=[])

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await (
                client.database.from_("posts")
                .eq("published", True)
                .neq("archived", False)
                .eq("deleted_reason", None)
                .in_("status", ["draft", "published"])
                .execute()
            )

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["kwargs"]["params"] == {
        "published": "eq.true",
        "archived": "neq.false",
        "deleted_reason": "eq.null",
        "status": "in.(draft,published)",
    }
    assert "Authorization" not in captured["kwargs"]["headers"]
    assert result == []


def test_database_query_is_null_does_not_expose_inverse_form() -> None:
    query = InsforgeClient(base_url="https://example.com", api_key="ins_test").database.from_("posts")

    try:
        query.is_null("deleted_at", False)  # type: ignore[call-arg]
    except TypeError:
        pass
    else:
        raise AssertionError("is_null should not accept a boolean flag")


def test_database_query_insert_sends_array_body_and_prefer_return_representation() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(201, json=[{"id": "1", "title": "Hello"}])

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.database.from_("posts").insert(
                [{"title": "Hello", "published": True}],
                return_representation=True,
                access_token="user_token",
            )

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.com/api/database/records/posts"
    assert "params" not in captured["kwargs"] or captured["kwargs"]["params"] is None
    assert captured["kwargs"]["json"] == [{"title": "Hello", "published": True}]
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer user_token"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert captured["kwargs"]["headers"]["Prefer"] == "return=representation"
    assert result == [{"id": "1", "title": "Hello"}]


def test_database_query_update_and_delete_use_prefer_and_handle_empty_delete_response() -> None:
    async def scenario() -> tuple[object, object, dict[str, object], dict[str, object]]:
        update_captured: dict[str, object] = {}
        delete_captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            if method == "PATCH":
                update_captured["method"] = method
                update_captured["url"] = str(url)
                update_captured["kwargs"] = kwargs
                return httpx.Response(200, json=[{"id": "1", "title": "Updated"}])

            delete_captured["method"] = method
            delete_captured["url"] = str(url)
            delete_captured["kwargs"] = kwargs
            return httpx.Response(204)

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            updated = await (
                client.database.from_("posts")
                .eq("id", "1")
                .update({"title": "Updated"}, return_representation=True, access_token="user_token")
            )
            deleted = await client.database.from_("posts").eq("id", "1").delete(access_token="user_token")

            return updated, deleted, update_captured, delete_captured

    updated, deleted, update_captured, delete_captured = asyncio.run(scenario())

    assert update_captured["method"] == "PATCH"
    assert update_captured["url"] == "https://example.com/api/database/records/posts"
    assert update_captured["kwargs"]["params"] == {"id": "eq.1"}
    assert update_captured["kwargs"]["json"] == {"title": "Updated"}
    assert update_captured["kwargs"]["headers"]["Authorization"] == "Bearer user_token"
    assert update_captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert update_captured["kwargs"]["headers"]["Prefer"] == "return=representation"
    assert updated == [{"id": "1", "title": "Updated"}]

    assert delete_captured["method"] == "DELETE"
    assert delete_captured["url"] == "https://example.com/api/database/records/posts"
    assert delete_captured["kwargs"]["params"] == {"id": "eq.1"}
    assert "json" not in delete_captured["kwargs"] or delete_captured["kwargs"]["json"] is None
    assert delete_captured["kwargs"]["headers"]["Authorization"] == "Bearer user_token"
    assert delete_captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert "Prefer" not in delete_captured["kwargs"]["headers"]
    assert deleted == []
