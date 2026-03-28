from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class AppMetadataDatabase(BaseModel):
    model_config = ConfigDict(extra="ignore")

    host: str | None = None
    port: int | None = None
    database: str | None = None
    ssl: bool | None = None


class AppMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str | None = None
    version: str | None = None
    environment: str | None = None
    database: AppMetadataDatabase | None = None
    uptime: float | None = None
    timestamp: datetime | None = None


class DatabaseMetadataTable(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str = Field(alias="tableName")
    record_count: int = Field(alias="recordCount")


class DatabaseMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    tables: list[DatabaseMetadataTable] = Field(default_factory=list)
    total_size_in_gb: float | None = Field(default=None, alias="totalSizeInGB")
    hint: str | None = None


class ApiKeyMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    api_key: str = Field(alias="apiKey")
