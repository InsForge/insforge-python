from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DatabaseQueryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    data: list[dict[str, Any]] = Field(default_factory=list)


class DatabaseTableForeignKey(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    table: str
    column: str
    on_delete: str = Field(alias="on_delete")


class DatabaseTableColumn(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str
    type: str
    nullable: bool
    unique: bool
    default: str | None = None
    is_primary_key: bool = Field(alias="isPrimaryKey")
    foreign_key: DatabaseTableForeignKey | None = Field(default=None, alias="foreignKey")


class DatabaseTableSchemaResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    table_name: str
    columns: list[DatabaseTableColumn] = Field(default_factory=list)
