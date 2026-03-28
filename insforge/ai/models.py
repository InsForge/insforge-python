from __future__ import annotations

from datetime import datetime
from typing import Any

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


class AIConfigurationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    input_modality: list[str] = Field(alias="inputModality")
    output_modality: list[str] = Field(alias="outputModality")
    provider: str
    model_id: str = Field(alias="modelId")
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
