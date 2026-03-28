import asyncio

import httpx

from insforge import InsforgeClient
from insforge.ai.models import AIConfiguration


def test_list_ai_configurations_returns_typed_models() -> None:
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
                        "id": "cfg-1",
                        "modality": "text",
                        "provider": "openrouter",
                        "modelId": "openai/gpt-4o-mini",
                        "systemPrompt": "You are helpful.",
                        "createdAt": "2026-03-28T00:00:00Z",
                        "updatedAt": "2026-03-28T00:01:00Z",
                    }
                ],
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.ai.list_configurations()
            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "GET"
    assert captured["url"] == "https://example.com/api/ai/configurations"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert "Authorization" not in captured["kwargs"]["headers"]
    assert len(result) == 1
    assert isinstance(result[0], AIConfiguration)
    assert result[0].model_id == "openai/gpt-4o-mini"
    assert result[0].provider == "openrouter"
