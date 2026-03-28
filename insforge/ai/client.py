from __future__ import annotations

from datetime import datetime
from typing import Literal

from .._base_client import BaseClient
from .._utils import quote_path_segment
from .models import AIChatCompletionRequest
from .models import AIChatCompletionResponse
from .models import AIChatMessage
from .models import AIConfiguration
from .models import AIConfigurationCreateRequest
from .models import AIConfigurationCreateResponse
from .models import AIConfigurationDeleteResponse
from .models import AIEmbeddingsRequest
from .models import AIEmbeddingsResponse
from .models import AIImageGenerationRequest
from .models import AIImageGenerationResponse
from .models import AIConfigurationUpdateRequest
from .models import AIConfigurationUpdateResponse
from .models import AICreditsResponse
from .models import AIListModelsResponse
from .models import AIUsageRecord
from .models import AIUsageSummary


class AIClient:
    def __init__(self, client: BaseClient) -> None:
        self._client = client

    @staticmethod
    def _serialize_params(**params: object) -> dict[str, str]:
        serialized: dict[str, str] = {}
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            else:
                serialized[key] = str(value)
        return serialized

    async def list_configurations(
        self,
        *,
        access_token: str | None = None,
    ) -> list[AIConfiguration]:
        payload = await self._client._request_json(
            "GET",
            "/api/ai/configurations",
            access_token=access_token,
        )
        return [AIConfiguration.model_validate(item) for item in payload]

    async def create_configuration(
        self,
        *,
        input_modality: list[Literal["text", "image"]],
        output_modality: list[Literal["text", "image"]],
        provider: str,
        model_id: str,
        system_prompt: str | None = None,
        access_token: str | None = None,
    ) -> AIConfigurationCreateResponse:
        payload = AIConfigurationCreateRequest(
            input_modality=input_modality,
            output_modality=output_modality,
            provider=provider,
            model_id=model_id,
            system_prompt=system_prompt,
        ).model_dump(by_alias=True, exclude_none=True)
        response = await self._client._request_json(
            "POST",
            "/api/ai/configurations",
            json=payload,
            access_token=access_token,
        )
        return AIConfigurationCreateResponse.model_validate(response)

    async def update_configuration(
        self,
        id: str,
        *,
        system_prompt: str | None = None,
        access_token: str | None = None,
    ) -> AIConfigurationUpdateResponse:
        payload = AIConfigurationUpdateRequest(system_prompt=system_prompt).model_dump(
            by_alias=True,
            exclude_none=True,
        )
        response = await self._client._request_json(
            "PATCH",
            f"/api/ai/configurations/{quote_path_segment(id)}",
            json=payload,
            access_token=access_token,
        )
        return AIConfigurationUpdateResponse.model_validate(response)

    async def delete_configuration(
        self,
        id: str,
        *,
        access_token: str | None = None,
    ) -> AIConfigurationDeleteResponse:
        response = await self._client._request_json(
            "DELETE",
            f"/api/ai/configurations/{quote_path_segment(id)}",
            access_token=access_token,
        )
        return AIConfigurationDeleteResponse.model_validate(response)

    async def get_usage_summary(
        self,
        *,
        config_id: str | None = None,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
        access_token: str | None = None,
    ) -> AIUsageSummary:
        params = self._serialize_params(
            configId=config_id,
            startDate=start_date,
            endDate=end_date,
        )
        payload = await self._client._request_json(
            "GET",
            "/api/ai/usage/summary",
            params=params or None,
            access_token=access_token,
        )
        return AIUsageSummary.model_validate(payload)

    async def get_usage(
        self,
        *,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        access_token: str | None = None,
    ) -> list[AIUsageRecord]:
        params = self._serialize_params(
            startDate=start_date,
            endDate=end_date,
            limit=limit,
            offset=offset,
        )
        payload = await self._client._request_json(
            "GET",
            "/api/ai/usage",
            params=params or None,
            access_token=access_token,
        )
        return [AIUsageRecord.model_validate(item) for item in payload]

    async def get_usage_by_configuration(
        self,
        config_id: str,
        *,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
        access_token: str | None = None,
    ) -> list[AIUsageRecord]:
        params = self._serialize_params(
            startDate=start_date,
            endDate=end_date,
        )
        payload = await self._client._request_json(
            "GET",
            f"/api/ai/usage/config/{quote_path_segment(config_id)}",
            params=params or None,
            access_token=access_token,
        )
        return [AIUsageRecord.model_validate(item) for item in payload]

    async def get_credits(
        self,
        *,
        access_token: str | None = None,
    ) -> AICreditsResponse:
        payload = await self._client._request_json(
            "GET",
            "/api/ai/credits",
            access_token=access_token,
        )
        return AICreditsResponse.model_validate(payload)

    async def list_models(
        self,
        *,
        access_token: str | None = None,
    ) -> AIListModelsResponse:
        payload = await self._client._request_json(
            "GET",
            "/api/ai/models",
            access_token=access_token,
        )
        return AIListModelsResponse.model_validate(payload)

    async def chat_completion(
        self,
        *,
        model: str,
        messages: list[AIChatMessage],
        access_token: str | None = None,
    ) -> AIChatCompletionResponse:
        payload = AIChatCompletionRequest(
            model=model,
            messages=messages,
        ).model_dump(by_alias=True, exclude_none=True)
        response = await self._client._request_json(
            "POST",
            "/api/ai/chat/completion",
            json=payload,
            access_token=access_token,
        )
        return AIChatCompletionResponse.model_validate(response)

    async def generate_images(
        self,
        *,
        model: str,
        prompt: str,
        access_token: str | None = None,
    ) -> AIImageGenerationResponse:
        payload = AIImageGenerationRequest(
            model=model,
            prompt=prompt,
        ).model_dump(by_alias=True, exclude_none=True)
        response = await self._client._request_json(
            "POST",
            "/api/ai/image/generation",
            json=payload,
            access_token=access_token,
        )
        return AIImageGenerationResponse.model_validate(response)

    async def generate_embeddings(
        self,
        *,
        model: str,
        input: str | list[str],
        access_token: str | None = None,
        encoding_format: Literal["float", "base64"] | None = None,
        dimensions: int | None = None,
    ) -> AIEmbeddingsResponse:
        payload = AIEmbeddingsRequest(
            model=model,
            input=input,
            encoding_format=encoding_format,
            dimensions=dimensions,
        ).model_dump(by_alias=True, exclude_none=True)
        response = await self._client._request_json(
            "POST",
            "/api/ai/embeddings",
            json=payload,
            access_token=access_token,
        )
        return AIEmbeddingsResponse.model_validate(response)
