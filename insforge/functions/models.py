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
