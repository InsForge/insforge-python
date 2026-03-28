from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StorageBucketListResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    buckets: list[str] = Field(default_factory=list)


class StorageObjectResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    bucket: str
    key: str
    size: int
    mime_type: str | None = Field(default=None, alias="mimeType")
    uploaded_at: datetime = Field(alias="uploadedAt")
    url: str


class StorageDeleteObjectResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str
