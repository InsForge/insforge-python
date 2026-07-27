from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass
from typing import Any
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StorageBucketListResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    buckets: list[str] = Field(default_factory=list)


class StorageBucketResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str
    bucket_name: str = Field(alias="bucketName")


class StorageBucketUpdateResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str
    bucket: str
    is_public: bool = Field(alias="isPublic")


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


class StorageDeleteObjectResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    key: str
    status: Literal["deleted", "notFound", "failed"]
    message: str | None = None


class StorageDeleteObjectsResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    results: list[StorageDeleteObjectResult] = Field(default_factory=list)


class StoragePagination(BaseModel):
    model_config = ConfigDict(extra="ignore")

    limit: int | None = None
    offset: int | None = None
    total: int | None = None


class StoredFileList(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    data: list[StorageObjectResponse] = Field(default_factory=list)
    pagination: StoragePagination | None = None
    next_actions: str | None = Field(default=None, alias="nextActions")


class UploadStrategy(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    method: str
    upload_url: str = Field(alias="uploadUrl")
    key: str
    confirm_required: bool = Field(alias="confirmRequired")
    confirm_url: str | None = Field(default=None, alias="confirmUrl")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    fields: dict[str, Any] | None = None


class DownloadStrategy(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    method: str
    url: str
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    headers: dict[str, str] | None = None


class StorageDeleteBucketResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str
    next_actions: str | None = Field(default=None, alias="nextActions")


@dataclass
class StorageDownloadResult:
    content: bytes
    content_type: str | None = None
    content_length: str | None = None
