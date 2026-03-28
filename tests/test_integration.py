"""Integration tests against a live Insforge instance.

Required environment variables:
    INSFORGE_API_KEY          - project API key
    INSFORGE_API_BASE_URL     - base URL of the Insforge instance
    INSFORGE_TEST_EMAIL       - test user email
    INSFORGE_TEST_PASSWORD    - test user password
    INSFORGE_FUNCTION_SLUG    - slug of an existing function (e.g. server-time)
    INSFORGE_TABLE_NAME       - name of an existing table (e.g. todos)

Run:
    INSFORGE_API_KEY=... INSFORGE_API_BASE_URL=... python -m pytest tests/test_integration.py -v
"""

from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio

from insforge import InsforgeClient
from insforge.auth.models import PublicAuthConfigResponse, SignInResponse
from insforge.functions.models import FunctionMetadata

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

API_KEY = os.environ.get("INSFORGE_API_KEY", "")
BASE_URL = os.environ.get("INSFORGE_API_BASE_URL", "")
TEST_EMAIL = os.environ.get("INSFORGE_TEST_EMAIL", "")
TEST_PASSWORD = os.environ.get("INSFORGE_TEST_PASSWORD", "")
FUNCTION_SLUG = os.environ.get("INSFORGE_FUNCTION_SLUG", "server-time")
TABLE_NAME = os.environ.get("INSFORGE_TABLE_NAME", "todos")

pytestmark = pytest.mark.skipif(
    not all([API_KEY, BASE_URL, TEST_EMAIL, TEST_PASSWORD]),
    reason="Integration env vars not set",
)


@pytest_asyncio.fixture
async def client():
    async with InsforgeClient(base_url=BASE_URL, api_key=API_KEY) as c:
        yield c


@pytest_asyncio.fixture
async def access_token(client: InsforgeClient) -> str:
    session = await client.auth.sign_in_with_password(
        email=TEST_EMAIL, password=TEST_PASSWORD,
    )
    return session.access_token


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_public_config(client: InsforgeClient):
    config = await client.auth.get_public_config()
    assert isinstance(config, PublicAuthConfigResponse)


@pytest.mark.asyncio
async def test_sign_in_with_password(client: InsforgeClient):
    session = await client.auth.sign_in_with_password(
        email=TEST_EMAIL, password=TEST_PASSWORD,
    )
    assert isinstance(session, SignInResponse)
    assert session.access_token
    assert session.refresh_token


@pytest.mark.asyncio
async def test_get_current_session(client: InsforgeClient, access_token: str):
    session = await client.auth.get_current_session(access_token=access_token)
    assert session.user.email == TEST_EMAIL


@pytest.mark.asyncio
async def test_refresh_token(client: InsforgeClient):
    session = await client.auth.sign_in_with_password(
        email=TEST_EMAIL, password=TEST_PASSWORD,
    )
    refreshed = await client.auth.refresh(refresh_token=session.refresh_token)
    assert refreshed.access_token


@pytest.mark.asyncio
async def test_get_profile(client: InsforgeClient, access_token: str):
    session = await client.auth.get_current_session(access_token=access_token)
    profile = await client.auth.get_profile(session.user.id)
    assert profile.id == session.user.id


# ---------------------------------------------------------------------------
# Database CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_database_insert_select_update_delete(client: InsforgeClient, access_token: str):
    tag = uuid.uuid4().hex[:8]
    title = f"sdk-test-{tag}"

    # Insert
    inserted = await client.database.from_(TABLE_NAME).insert(
        [{"title": title, "is_completed": False}],
        return_representation=True,
        access_token=access_token,
    )
    assert len(inserted) == 1
    row = inserted[0]
    assert row["title"] == title
    row_id = row["id"]

    # Select
    rows = await client.database.from_(TABLE_NAME) \
        .select("id,title,is_completed") \
        .eq("id", row_id) \
        .execute(access_token=access_token)
    assert isinstance(rows, list)
    assert len(rows) == 1
    assert rows[0]["title"] == title

    # Update
    updated = await client.database.from_(TABLE_NAME) \
        .eq("id", row_id) \
        .update({"is_completed": True}, return_representation=True, access_token=access_token)
    assert len(updated) == 1
    assert updated[0]["is_completed"] is True

    # Delete
    deleted = await client.database.from_(TABLE_NAME) \
        .eq("id", row_id) \
        .delete(return_representation=True, access_token=access_token)
    assert any(r["id"] == row_id for r in deleted)

    # Verify gone
    remaining = await client.database.from_(TABLE_NAME) \
        .eq("id", row_id) \
        .execute(access_token=access_token)
    assert remaining == [] or remaining == {}


@pytest.mark.asyncio
async def test_database_query_filters(client: InsforgeClient, access_token: str):
    tag = uuid.uuid4().hex[:8]
    rows_data = [
        {"title": f"filter-a-{tag}", "is_completed": False},
        {"title": f"filter-b-{tag}", "is_completed": True},
    ]
    inserted = await client.database.from_(TABLE_NAME).insert(
        rows_data, return_representation=True, access_token=access_token,
    )
    ids = [r["id"] for r in inserted]

    try:
        # neq filter
        result = await client.database.from_(TABLE_NAME) \
            .in_("id", ids) \
            .eq("is_completed", True) \
            .execute(access_token=access_token)
        assert len(result) == 1
        assert result[0]["is_completed"] is True

        # order + limit
        result = await client.database.from_(TABLE_NAME) \
            .in_("id", ids) \
            .order("title") \
            .limit(1) \
            .execute(access_token=access_token)
        assert len(result) == 1
        assert "filter-a" in result[0]["title"]
    finally:
        # cleanup
        for rid in ids:
            await client.database.from_(TABLE_NAME) \
                .eq("id", rid) \
                .delete(access_token=access_token)


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invoke_function(client: InsforgeClient):
    result = await client.functions.invoke(FUNCTION_SLUG)
    assert result is not None


@pytest.mark.asyncio
async def test_invoke_hello_world(client: InsforgeClient):
    result = await client.functions.invoke("hello-world")
    assert result is not None


@pytest.mark.asyncio
async def test_list_functions(client: InsforgeClient, access_token: str):
    fns = await client.functions.list_functions(access_token=access_token)
    assert isinstance(fns, list)
    slugs = [f.slug for f in fns]
    assert FUNCTION_SLUG in slugs


@pytest.mark.asyncio
async def test_get_function_details(client: InsforgeClient, access_token: str):
    fn = await client.functions.get_function(FUNCTION_SLUG, access_token=access_token)
    assert fn.slug == FUNCTION_SLUG
    assert fn.code  # should include source


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_app_metadata(client: InsforgeClient):
    meta = await client.metadata.get_app_metadata()
    assert meta.name or meta.version  # at least one populated


@pytest.mark.asyncio
async def test_get_database_metadata(client: InsforgeClient):
    meta = await client.metadata.get_database_metadata()
    table_names = [t.name for t in meta.tables]
    assert TABLE_NAME in table_names


# ---------------------------------------------------------------------------
# Database Table Admin
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_tables(client: InsforgeClient, access_token: str):
    tables = await client.database.list_tables(access_token=access_token)
    assert TABLE_NAME in tables


@pytest.mark.asyncio
async def test_get_table_schema(client: InsforgeClient, access_token: str):
    schema = await client.database.get_table_schema(TABLE_NAME, access_token=access_token)
    col_names = [c.name for c in schema.columns]
    assert "id" in col_names
    assert "title" in col_names
