from __future__ import annotations

from datetime import datetime
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class AIConfiguration(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str
    modality: str
    provider: str
    model_id: str = Field(alias="modelId")
    system_prompt: str | None = Field(default=None, alias="systemPrompt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


Modality = Literal["text", "image"]


class AIConfigurationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    input_modality: list[Modality] = Field(min_length=1, alias="inputModality")
    output_modality: list[Modality] = Field(min_length=1, alias="outputModality")
    provider: str = Field(min_length=1)
    model_id: str = Field(min_length=1, alias="modelId")
    system_prompt: str | None = Field(default=None, alias="systemPrompt")


class AIConfigurationCreateResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str
    message: str | None = None


class AIConfigurationUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    system_prompt: str | None = Field(default=None, alias="systemPrompt")


class AIConfigurationUpdateResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str | None = None


class AIConfigurationDeleteResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str | None = None


class AIUsageSummaryByModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    requests: int | None = None
    tokens: int | None = None
    cost: float | None = None


class AIUsageSummary(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    total_requests: int | None = Field(default=None, alias="totalRequests")
    total_tokens: int | None = Field(default=None, alias="totalTokens")
    total_cost: float | None = Field(default=None, alias="totalCost")
    by_model: dict[str, AIUsageSummaryByModel] = Field(default_factory=dict, alias="byModel")


class AIUsageRecord(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str | None = None
    config_id: str | None = Field(default=None, alias="configId")
    model_id: str | None = Field(default=None, alias="modelId")
    prompt_tokens: int | None = Field(default=None, alias="promptTokens")
    completion_tokens: int | None = Field(default=None, alias="completionTokens")
    total_tokens: int | None = Field(default=None, alias="totalTokens")
    cost: float | None = None
    created_at: datetime | None = Field(default=None, alias="createdAt")
    provider: str | None = None
    model: str | None = None
    input_modality: list[str] | None = Field(default=None, alias="inputModality")
    output_modality: list[str] | None = Field(default=None, alias="outputModality")


class AICreditsResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    credits: float | None = None
    usage: float | None = None


class AIChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    role: Literal["user", "assistant", "system", "tool"]
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = Field(default=None, alias="tool_calls")
    tool_call_id: str | None = Field(default=None, alias="tool_call_id")


class AIChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    model: str = Field(min_length=1)
    messages: list[AIChatMessage] = Field(min_length=1)
    stream: bool = False


class AIChatCompletionUsage(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    prompt_tokens: int | None = Field(default=None, alias="promptTokens")
    completion_tokens: int | None = Field(default=None, alias="completionTokens")
    total_tokens: int | None = Field(default=None, alias="totalTokens")


class AIChatCompletionMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    model: str | None = None
    usage: AIChatCompletionUsage | None = None


class AIChatCompletionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    text: str | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list, alias="tool_calls")
    annotations: list[dict[str, Any]] = Field(default_factory=list)
    metadata: AIChatCompletionMetadata | None = None


class AIImageGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    model: str = Field(min_length=1)
    prompt: str = Field(min_length=1)


class AIImageURL(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    url: str | None = None


class AIImageMessage(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    type: str | None = None
    image_url: AIImageURL | None = Field(default=None, alias="image_url")


class AIImageGenerationUsage(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    prompt_tokens: int | None = Field(default=None, alias="promptTokens")
    completion_tokens: int | None = Field(default=None, alias="completionTokens")
    total_tokens: int | None = Field(default=None, alias="totalTokens")


class AIImageGenerationMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    model: str | None = None
    revised_prompt: str | None = Field(default=None, alias="revisedPrompt")
    usage: AIImageGenerationUsage | None = None


class AIImageGenerationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    model: str | None = None
    images: list[AIImageMessage] = Field(default_factory=list)
    text: str | None = None
    count: int | None = None
    metadata: AIImageGenerationMetadata | None = None
    next_actions: str | None = Field(default=None, alias="nextActions")


class AIEmbeddingsRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    model: str = Field(min_length=1)
    input: str | list[str]
    encoding_format: Literal["float", "base64"] | None = Field(default=None, alias="encoding_format")
    dimensions: int | None = Field(default=None, ge=0)


class AIEmbeddingObject(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    object: str | None = None
    embedding: list[float] = Field(default_factory=list)
    index: int | None = None


class AIEmbeddingsUsage(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    prompt_tokens: int | None = Field(default=None, alias="promptTokens")
    completion_tokens: int | None = Field(default=None, alias="completionTokens")
    total_tokens: int | None = Field(default=None, alias="totalTokens")


class AIEmbeddingsMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    model: str | None = None
    usage: AIEmbeddingsUsage | None = None


class AIEmbeddingsResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    object: str | None = None
    data: list[AIEmbeddingObject] = Field(default_factory=list)
    metadata: AIEmbeddingsMetadata | None = None


class OpenRouterModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    name: str | None = None
    created: int | None = None
    description: str | None = None
    architecture: dict[str, Any] | None = None
    top_provider: dict[str, Any] | None = Field(default=None, alias="topProvider")
    pricing: dict[str, Any] | None = None
    context_length: int | None = None
    max_completion_tokens: int | None = None
    per_request_limits: dict[str, Any] | None = None
    supported_parameters: list[str] | None = None


class AIModelGroup(BaseModel):
    model_config = ConfigDict(extra="ignore")

    provider: str | None = None
    configured: bool | None = None
    models: list[OpenRouterModel] = Field(default_factory=list)


class AIListModelsResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    text: list[AIModelGroup] = Field(default_factory=list)
    image: list[AIModelGroup] = Field(default_factory=list)
