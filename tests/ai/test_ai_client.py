import asyncio

import httpx

from insforge import InsforgeClient
from insforge.ai.models import AIConfiguration
from insforge.ai.models import AIConfigurationCreateResponse
from insforge.ai.models import AIConfigurationDeleteResponse
from insforge.ai.models import AIConfigurationUpdateResponse
from insforge.ai.models import AICreditsResponse
from insforge.ai.models import AIChatCompletionResponse
from insforge.ai.models import AIEmbeddingsResponse
from insforge.ai.models import AIListModelsResponse
from insforge.ai.models import AIImageGenerationResponse
from insforge.ai.models import AIUsageSummary


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


def test_create_ai_configuration_sends_request_body_and_returns_typed_model() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(201, json={"id": "cfg-2", "message": "created"})

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.ai.create_configuration(
                input_modality=["text"],
                output_modality=["text"],
                provider="openrouter",
                model_id="openai/gpt-4o-mini",
                system_prompt="You are helpful.",
                access_token="admin_token",
            )
            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.com/api/ai/configurations"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer admin_token"
    assert captured["kwargs"]["json"] == {
        "inputModality": ["text"],
        "outputModality": ["text"],
        "provider": "openrouter",
        "modelId": "openai/gpt-4o-mini",
        "systemPrompt": "You are helpful.",
    }
    assert isinstance(result, AIConfigurationCreateResponse)
    assert result.id == "cfg-2"


def test_update_and_delete_ai_configuration_return_typed_models() -> None:
    async def scenario() -> tuple[object, object, dict[str, object], dict[str, object]]:
        update_captured: dict[str, object] = {}
        delete_captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            if method == "PATCH":
                update_captured["method"] = method
                update_captured["url"] = str(url)
                update_captured["kwargs"] = kwargs
                return httpx.Response(200, json={"message": "updated"})

            delete_captured["method"] = method
            delete_captured["url"] = str(url)
            delete_captured["kwargs"] = kwargs
            return httpx.Response(200, json={"message": "deleted"})

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            updated = await client.ai.update_configuration(
                "cfg-2",
                system_prompt="Be concise.",
                access_token="admin_token",
            )
            deleted = await client.ai.delete_configuration(
                "cfg-2",
                access_token="admin_token",
            )
            return updated, deleted, update_captured, delete_captured

    updated, deleted, update_captured, delete_captured = asyncio.run(scenario())

    assert update_captured["method"] == "PATCH"
    assert update_captured["url"] == "https://example.com/api/ai/configurations/cfg-2"
    assert update_captured["kwargs"]["json"] == {"systemPrompt": "Be concise."}
    assert update_captured["kwargs"]["headers"]["Authorization"] == "Bearer admin_token"
    assert isinstance(updated, AIConfigurationUpdateResponse)
    assert updated.message == "updated"

    assert delete_captured["method"] == "DELETE"
    assert delete_captured["url"] == "https://example.com/api/ai/configurations/cfg-2"
    assert delete_captured["kwargs"]["headers"]["Authorization"] == "Bearer admin_token"
    assert isinstance(deleted, AIConfigurationDeleteResponse)
    assert deleted.message == "deleted"


def test_get_ai_usage_summary_returns_typed_model() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                json={
                    "totalRequests": 7,
                    "totalTokens": 1234,
                    "totalCost": 0.42,
                    "byModel": {
                        "openai/gpt-4o-mini": {
                            "requests": 7,
                            "tokens": 1234,
                            "cost": 0.42,
                        }
                    },
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.ai.get_usage_summary(
                config_id="cfg-2",
                access_token="admin_token",
            )
            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "GET"
    assert captured["url"] == "https://example.com/api/ai/usage/summary"
    assert captured["kwargs"]["params"] == {"configId": "cfg-2"}
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer admin_token"
    assert isinstance(result, AIUsageSummary)
    assert result.total_requests == 7
    assert result.by_model["openai/gpt-4o-mini"].requests == 7


def test_get_ai_credits_and_models_return_typed_models() -> None:
    async def scenario() -> tuple[object, object]:
        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            if str(url).endswith("/api/ai/credits"):
                return httpx.Response(200, json={"credits": 9.5, "usage": 1.25})

            return httpx.Response(
                200,
                json={
                    "text": [
                        {
                            "provider": "openrouter",
                            "configured": True,
                            "models": [
                                {
                                    "id": "openai/gpt-4o-mini",
                                    "name": "GPT-4o mini",
                                    "created": 123,
                                    "description": "Fast model",
                                }
                            ],
                        }
                    ],
                    "image": [],
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            credits = await client.ai.get_credits(access_token="admin_token")
            models = await client.ai.list_models(access_token="admin_token")
            return credits, models

    credits, models = asyncio.run(scenario())

    assert isinstance(credits, AICreditsResponse)
    assert credits.credits == 9.5
    assert credits.usage == 1.25
    assert isinstance(models, AIListModelsResponse)
    assert models.text[0].provider == "openrouter"
    assert models.text[0].models[0].id == "openai/gpt-4o-mini"


def test_chat_completion_sends_request_body_and_returns_typed_model() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                json={
                    "text": "Hello there",
                    "metadata": {
                        "model": "openai/gpt-4o-mini",
                        "usage": {
                            "promptTokens": 3,
                            "completionTokens": 4,
                            "totalTokens": 7,
                        },
                    },
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.ai.chat_completion(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": "Say hi"}],
                access_token="client_token",
            )
            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.com/api/ai/chat/completion"
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer client_token"
    assert captured["kwargs"]["json"] == {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": "Say hi"}],
        "stream": False,
    }
    assert isinstance(result, AIChatCompletionResponse)
    assert result.text == "Hello there"
    assert result.metadata.model == "openai/gpt-4o-mini"


def test_generate_images_sends_request_body_and_returns_typed_model() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                json={
                    "model": "openai/dall-e-3",
                    "images": [
                        {
                            "type": "image_url",
                            "image_url": {"url": "https://example.com/image.png"},
                        }
                    ],
                    "count": 1,
                    "nextActions": "Images have been generated successfully.",
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.ai.generate_images(
                model="openai/dall-e-3",
                prompt="A red fox in a snowy forest",
                access_token="client_token",
            )
            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.com/api/ai/image/generation"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer client_token"
    assert captured["kwargs"]["json"] == {
        "model": "openai/dall-e-3",
        "prompt": "A red fox in a snowy forest",
    }
    assert isinstance(result, AIImageGenerationResponse)
    assert result.count == 1
    assert result.images[0].image_url.url == "https://example.com/image.png"


def test_generate_embeddings_sends_request_body_and_returns_typed_model() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                json={
                    "object": "list",
                    "data": [
                        {
                            "object": "embedding",
                            "embedding": [0.1, 0.2],
                            "index": 0,
                        }
                    ],
                    "metadata": {
                        "model": "google/gemini-embedding-001",
                        "usage": {
                            "promptTokens": 2,
                            "completionTokens": 0,
                            "totalTokens": 2,
                        },
                    },
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.ai.generate_embeddings(
                model="google/gemini-embedding-001",
                input=["hello", "world"],
                access_token="client_token",
            )
            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.com/api/ai/embeddings"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer client_token"
    assert captured["kwargs"]["json"] == {
        "model": "google/gemini-embedding-001",
        "input": ["hello", "world"],
    }
    assert isinstance(result, AIEmbeddingsResponse)
    assert result.data[0].embedding == [0.1, 0.2]
    assert result.metadata.model == "google/gemini-embedding-001"
