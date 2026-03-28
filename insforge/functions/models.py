from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator


class FunctionMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    slug: str
    name: str
    description: str | None = None
    status: Literal["draft", "active", "error"]
    created_at: datetime
    updated_at: datetime
    deployed_at: datetime | None = None


class FunctionDetails(FunctionMetadata):
    code: str


class FunctionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(min_length=1)
    slug: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]+$")
    code: str = Field(min_length=1)
    description: str | None = None
    status: Literal["draft", "active"] = Field(default="active")


class FunctionUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = Field(default=None, min_length=1)
    code: str | None = Field(default=None, min_length=1)
    description: str | None = None
    status: Literal["draft", "active", "error"] | None = None

    @field_validator("name", "code", mode="before", check_fields=False)
    def trim_empty(cls, value: str | None) -> str | None:
        if value is not None and value.strip() == "":
            raise ValueError("name and code cannot be empty when provided")
        return value

    @model_validator(mode="before")
    def require_field(cls, values):
        if not any(values.get(field) is not None for field in ("name", "code", "description", "status")):
            raise ValueError("update_function requires at least one field")
        return values


class FunctionMutationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    success: bool
    function: FunctionMetadata


class FunctionDeleteResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    success: bool
    message: str | None = None
