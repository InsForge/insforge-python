from __future__ import annotations

from datetime import datetime

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
