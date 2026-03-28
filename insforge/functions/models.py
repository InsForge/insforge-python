from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class FunctionMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    slug: str
    name: str
    description: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    deployed_at: datetime | None = None


class FunctionDetails(FunctionMetadata):
    code: str


class FunctionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    slug: str | None = None
    code: str
    description: str | None = None
    status: str | None = None


class FunctionUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    code: str | None = None
    description: str | None = None
    status: str | None = None


class FunctionMutationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    success: bool
    function: FunctionMetadata


class FunctionDeleteResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    success: bool
    message: str | None = None
