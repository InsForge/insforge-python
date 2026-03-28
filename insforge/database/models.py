from __future__ import annotations

from typing import Any
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DatabaseQueryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    data: list[dict[str, Any]] = Field(default_factory=list)


class DatabaseTableForeignKey(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    constraint_name: str | None = Field(default=None, alias="constraint_name")
    reference_table: str = Field(alias="referenceTable")
    reference_column: str = Field(alias="referenceColumn")
    on_delete: str = Field(default="NO ACTION", alias="onDelete")
    on_update: str | None = Field(default=None, alias="onUpdate")


class DatabaseTableColumn(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str = Field(alias="columnName")
    type: str
    nullable: bool = Field(alias="isNullable")
    unique: bool = Field(alias="isUnique")
    default_value: str | None = Field(default=None, alias="defaultValue")
    is_primary_key: bool = Field(alias="isPrimaryKey")
    foreign_key: DatabaseTableForeignKey | None = Field(default=None, alias="foreignKey")


class DatabaseTableSchemaResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    table_name: str = Field(alias="tableName")
    columns: list[DatabaseTableColumn] = Field(default_factory=list)
    record_count: int | str | None = Field(default=None, alias="recordCount")


ColumnType = Literal["string", "datetime", "integer", "float", "boolean", "uuid", "json", "file"]
ForeignKeyAction = Literal["CASCADE", "SET NULL", "NO ACTION", "RESTRICT"]


class DatabaseTableCreateForeignKey(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    table: str = Field(min_length=1)
    column: str = Field(min_length=1)
    on_delete: ForeignKeyAction = Field(default="NO ACTION", alias="onDelete")


class DatabaseTableCreateColumn(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str = Field(min_length=1)
    type: ColumnType
    nullable: bool
    unique: bool | None = None
    default_value: str | None = Field(default=None, alias="defaultValue")
    foreign_key: DatabaseTableCreateForeignKey | None = Field(default=None, alias="foreignKey")


class DatabaseCreateTableRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    table_name: str = Field(min_length=1, alias="tableName")
    columns: list[DatabaseTableCreateColumn] = Field(min_length=1)
    rls_enabled: bool | None = Field(default=None, alias="rlsEnabled")


class DatabaseTableSchemaAddColumn(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    column_name: str = Field(min_length=1, alias="columnName")
    type: ColumnType
    is_nullable: bool | None = Field(default=None, alias="isNullable")
    is_unique: bool | None = Field(default=None, alias="isUnique")
    default_value: str | None = Field(default=None, alias="defaultValue")


class DatabaseTableSchemaUpdateColumn(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    column_name: str = Field(min_length=1, alias="columnName")
    new_column_name: str | None = Field(default=None, min_length=1, max_length=64, alias="newColumnName")
    default_value: str | None = Field(default=None, alias="defaultValue")


class DatabaseTableSchemaUpdateForeignKey(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    reference_table: str = Field(min_length=1, alias="referenceTable")
    reference_column: str = Field(min_length=1, alias="referenceColumn")
    on_delete: ForeignKeyAction | None = Field(default=None, alias="onDelete")
    on_update: ForeignKeyAction | None = Field(default=None, alias="onUpdate")


class DatabaseTableSchemaAddForeignKey(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    column_name: str = Field(min_length=1, alias="columnName")
    foreign_key: DatabaseTableSchemaUpdateForeignKey = Field(alias="foreignKey")


class DatabaseTableSchemaRenameRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    new_table_name: str = Field(min_length=1, max_length=64, alias="newTableName")


class DatabaseTableSchemaUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    add_columns: list[DatabaseTableSchemaAddColumn] | None = Field(default=None, alias="addColumns")
    drop_columns: list[str] | None = Field(default=None, alias="dropColumns")
    update_columns: list[DatabaseTableSchemaUpdateColumn] | None = Field(default=None, alias="updateColumns")
    add_foreign_keys: list[DatabaseTableSchemaAddForeignKey] | None = Field(default=None, alias="addForeignKeys")
    drop_foreign_keys: list[str] | None = Field(default=None, alias="dropForeignKeys")
    rename_table: DatabaseTableSchemaRenameRequest | None = Field(default=None, alias="renameTable")

    @model_validator(mode="before")
    def require_operation(cls, values):
        fields = (
            "addColumns", "add_columns",
            "dropColumns", "drop_columns",
            "updateColumns", "update_columns",
            "addForeignKeys", "add_foreign_keys",
            "dropForeignKeys", "drop_foreign_keys",
            "renameTable", "rename_table",
        )
        if not any(values.get(f) is not None for f in fields):
            raise ValueError("update_table_schema requires at least one schema operation")
        return values


class DatabaseTableMutationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    message: str
    table_name: str = Field(alias="tableName")
    operations: list[str] = Field(default_factory=list)
