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

    name: str
    record_count: int = Field(alias="recordCount")


class DatabaseMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    tables: list[DatabaseMetadataTable] = Field(default_factory=list)
    total_tables: int = Field(alias="totalTables")
    total_records: int = Field(alias="totalRecords")
    database_size: str = Field(alias="databaseSize")
    last_updated: datetime = Field(alias="lastUpdated")
