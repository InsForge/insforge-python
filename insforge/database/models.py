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


class DatabaseTableCreateForeignKey(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    table: str
    column: str
    on_delete: str = Field(default="NO ACTION", alias="onDelete")


class DatabaseTableCreateColumn(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str
    type: str
    nullable: bool
    unique: bool | None = None
    default_value: str | None = Field(default=None, alias="defaultValue")
    foreign_key: DatabaseTableCreateForeignKey | None = Field(default=None, alias="foreignKey")


class DatabaseCreateTableRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    table_name: str = Field(alias="tableName")
    columns: list[DatabaseTableCreateColumn]
    rls_enabled: bool | None = Field(default=None, alias="rlsEnabled")


class DatabaseTableSchemaAddColumn(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    column_name: str = Field(alias="columnName")
    type: str
    is_nullable: bool | None = Field(default=None, alias="isNullable")
    is_unique: bool | None = Field(default=None, alias="isUnique")
    default_value: str | None = Field(default=None, alias="defaultValue")


class DatabaseTableSchemaUpdateColumn(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    column_name: str = Field(alias="columnName")
    new_column_name: str | None = Field(default=None, alias="newColumnName")
    default_value: str | None = Field(default=None, alias="defaultValue")


class DatabaseTableSchemaUpdateForeignKey(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    reference_table: str = Field(alias="referenceTable")
    reference_column: str = Field(alias="referenceColumn")
    on_delete: str | None = Field(default=None, alias="onDelete")
    on_update: str | None = Field(default=None, alias="onUpdate")


class DatabaseTableSchemaAddForeignKey(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    column_name: str = Field(alias="columnName")
    foreign_key: DatabaseTableSchemaUpdateForeignKey = Field(alias="foreignKey")


class DatabaseTableSchemaRenameRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    new_table_name: str = Field(alias="newTableName")


class DatabaseTableSchemaUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    add_columns: list[DatabaseTableSchemaAddColumn] | None = Field(default=None, alias="addColumns")
    drop_columns: list[str] | None = Field(default=None, alias="dropColumns")
    update_columns: list[DatabaseTableSchemaUpdateColumn] | None = Field(default=None, alias="updateColumns")
    add_foreign_keys: list[DatabaseTableSchemaAddForeignKey] | None = Field(default=None, alias="addForeignKeys")
    drop_foreign_keys: list[str] | None = Field(default=None, alias="dropForeignKeys")
    rename_table: DatabaseTableSchemaRenameRequest | None = Field(default=None, alias="renameTable")


class DatabaseTableMutationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    message: str
    table_name: str = Field(alias="tableName")
    operations: list[str] = Field(default_factory=list)
