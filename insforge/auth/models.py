from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SignInResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    access_token: str = Field(alias="accessToken")
    refresh_token: str = Field(alias="refreshToken")


class CurrentProfileResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    user_id: str = Field(alias="userId")
    profile: dict[str, Any]
