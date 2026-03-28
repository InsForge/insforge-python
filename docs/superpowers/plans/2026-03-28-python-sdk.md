# InsForge Python SDK Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an async-first, stateless Python SDK for InsForge OSS covering every approved non-realtime operation in the local OpenAPI files for auth, database, storage, functions, ai, email, and metadata.

**Architecture:** The SDK centers on a single async `InsforgeClient` with focused sub-clients per API domain. A shared transport layer handles `X-API-Key`, optional per-request bearer auth, JSON/multipart requests, and OpenAPI error normalization without storing any session or token state between calls.

**Tech Stack:** Python 3.11+, httpx, pydantic v2, pytest, pytest-asyncio, respx

---

## File Structure

### Runtime package

- Create: `pyproject.toml`
- Create: `README.md`
- Create: `insforge/__init__.py`
- Create: `insforge/client.py`
- Create: `insforge/exceptions.py`
- Create: `insforge/types.py`
- Create: `insforge/_base_client.py`
- Create: `insforge/_utils.py`
- Create: `insforge/auth/__init__.py`
- Create: `insforge/auth/client.py`
- Create: `insforge/auth/models.py`
- Create: `insforge/database/__init__.py`
- Create: `insforge/database/client.py`
- Create: `insforge/database/query.py`
- Create: `insforge/database/models.py`
- Create: `insforge/storage/__init__.py`
- Create: `insforge/storage/client.py`
- Create: `insforge/storage/models.py`
- Create: `insforge/functions/__init__.py`
- Create: `insforge/functions/client.py`
- Create: `insforge/functions/models.py`
- Create: `insforge/ai/__init__.py`
- Create: `insforge/ai/client.py`
- Create: `insforge/ai/models.py`
- Create: `insforge/email/__init__.py`
- Create: `insforge/email/client.py`
- Create: `insforge/email/models.py`
- Create: `insforge/metadata/__init__.py`
- Create: `insforge/metadata/client.py`
- Create: `insforge/metadata/models.py`

### Tests

- Create: `tests/conftest.py`
- Create: `tests/test_client.py`
- Create: `tests/test_exceptions.py`
- Create: `tests/auth/test_auth_client.py`
- Create: `tests/database/test_database_query.py`
- Create: `tests/database/test_database_admin.py`
- Create: `tests/storage/test_storage_client.py`
- Create: `tests/functions/test_functions_client.py`
- Create: `tests/ai/test_ai_client.py`
- Create: `tests/email/test_email_client.py`
- Create: `tests/metadata/test_metadata_client.py`

### Design docs

- Existing: `docs/superpowers/specs/2026-03-28-python-sdk-design.md`
- Create: `docs/superpowers/plans/2026-03-28-python-sdk.md`

### Responsibility map

- `insforge/_base_client.py`: shared request execution, auth/header assembly, error parsing, JSON/multipart helpers
- `insforge/client.py`: top-level `InsforgeClient`, lifecycle management, sub-client wiring
- `insforge/types.py`: common type aliases and transport protocol shapes
- `insforge/exceptions.py`: SDK exception hierarchy
- `insforge/_utils.py`: URL normalization and serialization helpers
- `insforge/*/models.py`: per-domain request/response models
- `insforge/*/client.py`: per-domain API wrappers
- `insforge/database/query.py`: PostgREST-style query builder
- `tests/*`: transport-level behavior and per-domain contract tests using mocked HTTP responses

### Approved OpenAPI coverage

- `oss_openapi/auth.yaml`: full coverage, including public config, profiles, config admin endpoints, user registration/login/session endpoints, admin auth endpoints, anon token generation, email verification/reset flows, and OAuth provider/config/exchange endpoints
- `oss_openapi/records.yaml` and `oss_openapi/tables.yaml`: full coverage
- `oss_openapi/storage.yaml`: full coverage, including bucket admin endpoints, object upload/download/delete, and upload/download strategy endpoints
- `oss_openapi/functions.yaml`: full coverage, including admin CRUD and runtime execution endpoints under `/functions/{slug}`
- `oss_openapi/ai.yaml`: full coverage, including configurations, usage, credits, models, chat completion, image generation, and embeddings
- `oss_openapi/email.yaml`: full coverage
- `oss_openapi/metadata.yaml`: full coverage

### Task 1: Project Bootstrap And Shared Package Surface

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `insforge/__init__.py`
- Create: `insforge/client.py`
- Create: `insforge/types.py`
- Create: `tests/conftest.py`
- Test: `tests/test_client.py`

- [ ] **Step 1: Write the failing tests for package bootstrap and top-level client construction**

```python
from insforge import InsforgeClient


def test_client_normalizes_base_url() -> None:
    client = InsforgeClient(base_url="https://example.com/", api_key="ins_test")
    assert str(client.base_url) == "https://example.com"


def test_client_stores_base_url_and_api_key() -> None:
    client = InsforgeClient(base_url="https://example.com", api_key="ins_test")
    assert str(client.base_url) == "https://example.com"
    assert client.api_key == "ins_test"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_client.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'insforge'`

- [ ] **Step 3: Write minimal package bootstrap implementation**

```python
from .client import InsforgeClient

__all__ = ["InsforgeClient"]
```

```python
class InsforgeClient:
    def __init__(self, *, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
```

```toml
[project]
name = "insforge"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["httpx>=0.28.0", "pydantic>=2.7.0"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml README.md insforge/__init__.py insforge/client.py insforge/types.py tests/conftest.py tests/test_client.py
git commit -m "chore: bootstrap python sdk package"
```

### Task 2: Shared Transport, Stateless Auth Headers, And Exceptions

**Files:**
- Create: `insforge/_base_client.py`
- Create: `insforge/_utils.py`
- Create: `insforge/exceptions.py`
- Modify: `insforge/client.py`
- Create: `tests/test_exceptions.py`
- Modify: `tests/test_client.py`

- [ ] **Step 1: Write the failing tests for request headers and error parsing**

```python
import httpx

from insforge._base_client import build_headers
from insforge.exceptions import InsforgeHTTPError


def test_build_headers_includes_api_key_without_authorization() -> None:
    headers = build_headers(api_key="ins_test")
    assert headers["X-API-Key"] == "ins_test"
    assert "Authorization" not in headers


def test_build_headers_uses_explicit_access_token_only() -> None:
    headers = build_headers(api_key="ins_test", access_token="user_token")
    assert headers["Authorization"] == "Bearer user_token"


def test_build_headers_rejects_authorization_override() -> None:
    headers = build_headers(api_key="ins_test", extra_headers={"Authorization": "Bearer wrong"})
    assert "Authorization" not in headers


def test_http_error_parses_openapi_error_payload() -> None:
    response = httpx.Response(401, json={"error": "UNAUTHORIZED", "message": "Invalid token", "statusCode": 401, "nextAction": "Login again"})
    exc = InsforgeHTTPError.from_response("GET", "/api/test", response)
    assert exc.status_code == 401
    assert exc.error == "UNAUTHORIZED"
    assert exc.message == "Invalid token"
    assert exc.next_action == "Login again"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_client.py tests/test_exceptions.py -v`
Expected: FAIL with missing request helpers and exception types

- [ ] **Step 3: Write minimal shared transport and exception implementation**

```python
def build_headers(api_key: str, access_token: str | None = None, extra_headers: dict[str, str] | None = None) -> dict[str, str]:
    headers = {"X-API-Key": api_key}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    for key, value in (extra_headers or {}).items():
        if key.lower() != "authorization":
            headers[key] = value
    return headers
```

```python
class InsforgeHTTPError(Exception):
    @classmethod
    def from_response(cls, method: str, path: str, response: httpx.Response) -> "InsforgeHTTPError":
        payload = response.json()
        return cls(
            status_code=response.status_code,
            error=payload.get("error", "UNKNOWN_ERROR"),
            message=payload.get("message", f"{method} {path} failed"),
            next_action=payload.get("nextAction") or payload.get("nextActions"),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_client.py tests/test_exceptions.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add insforge/_base_client.py insforge/_utils.py insforge/exceptions.py insforge/client.py tests/test_client.py tests/test_exceptions.py
git commit -m "feat: add shared transport and error handling"
```

### Task 3: Core Auth Models And Stateless Auth Client

**Files:**
- Create: `insforge/auth/__init__.py`
- Create: `insforge/auth/models.py`
- Create: `insforge/auth/client.py`
- Modify: `insforge/client.py`
- Create: `tests/auth/test_auth_client.py`

- [ ] **Step 1: Write the failing tests for registration, login, refresh, logout, session, and profile endpoints**

```python
import httpx
import pytest
import respx

from insforge import InsforgeClient


@pytest.mark.asyncio
async def test_sign_in_returns_tokens_without_mutating_client_state() -> None:
    with respx.mock(assert_all_called=True) as router:
        router.post("https://example.com/api/auth/sessions?client_type=server").mock(
            return_value=httpx.Response(200, json={"accessToken": "access", "refreshToken": "refresh"})
        )
        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            result = await client.auth.sign_in_with_password(email="a@example.com", password="secret")
            assert result.access_token == "access"
            assert result.refresh_token == "refresh"


@pytest.mark.asyncio
async def test_update_current_profile_uses_explicit_access_token() -> None:
    with respx.mock(assert_all_called=True) as router:
        route = router.patch("https://example.com/api/auth/profiles/current").mock(
            return_value=httpx.Response(200, json={"userId": "u1", "profile": {"name": "Ada"}})
        )
        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            await client.auth.update_current_profile({"name": "Ada"}, access_token="user_token")
        assert route.calls.last.request.headers["Authorization"] == "Bearer user_token"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/auth/test_auth_client.py -v`
Expected: FAIL with missing `AuthClient` and auth models

- [ ] **Step 3: Write minimal auth implementation**

```python
class AuthClient:
    async def sign_in_with_password(self, *, email: str, password: str):
        return await self._api.post("/api/auth/sessions", params={"client_type": "server"}, json={"email": email, "password": password})

    async def update_current_profile(self, profile: dict[str, object], *, access_token: str):
        return await self._api.patch("/api/auth/profiles/current", json={"profile": profile}, access_token=access_token)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/auth/test_auth_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add insforge/auth/__init__.py insforge/auth/models.py insforge/auth/client.py insforge/client.py tests/auth/test_auth_client.py
git commit -m "feat: add stateless auth client"
```

- [ ] **Step 6: Extend auth client to full `auth.yaml` coverage**

Implement and test the remaining approved auth surface in the same module set:

- `/api/auth/config` get/update
- `/api/auth/public-config`
- `/api/auth/users` create/list
- `/api/auth/users/{userId}` get
- `/api/auth/profiles/{userId}`
- `/api/auth/sessions/current`
- `/api/auth/refresh`
- `/api/auth/logout`
- `/api/auth/admin/sessions`
- `/api/auth/admin/sessions/exchange`
- `/api/auth/tokens/anon`
- `/api/auth/email/send-verification`
- `/api/auth/email/verify`
- `/api/auth/email/send-reset-password`
- `/api/auth/email/exchange-reset-password-token`
- `/api/auth/email/reset-password`
- `/api/auth/oauth/configs`
- `/api/auth/oauth/{provider}/config`
- `/api/auth/oauth/custom/configs`
- `/api/auth/oauth/custom/{key}/config`

Do not implement browser callback helpers, browser redirect endpoints, or PKCE/browser exchange helpers that the approved spec excluded from v1.

Run: `pytest tests/auth/test_auth_client.py -v`
Expected: PASS with endpoint paths matching `auth.yaml`

### Task 4: Database Query Builder For Records API

**Files:**
- Create: `insforge/database/__init__.py`
- Create: `insforge/database/models.py`
- Create: `insforge/database/query.py`
- Create: `insforge/database/client.py`
- Modify: `insforge/client.py`
- Create: `tests/database/test_database_query.py`

- [ ] **Step 1: Write the failing tests for query parameter generation and per-call auth**

```python
import httpx
import pytest
import respx

from insforge import InsforgeClient


@pytest.mark.asyncio
async def test_select_query_builds_postgrest_filters() -> None:
    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://example.com/api/database/records/posts").mock(
            return_value=httpx.Response(200, json=[{"id": "1", "title": "Hello"}], headers={"X-Total-Count": "1"})
        )
        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            await client.database.from_("posts").select("id,title").eq("status", "active").limit(1).execute()
        request = route.calls.last.request
        assert request.url.params["select"] == "id,title"
        assert request.url.params["status"] == "eq.active"
        assert request.url.params["limit"] == "1"


@pytest.mark.asyncio
async def test_execute_with_access_token_adds_authorization_header() -> None:
    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://example.com/api/database/records/posts").mock(
            return_value=httpx.Response(200, json=[])
        )
        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            await client.database.from_("posts").select("*").execute(access_token="user_token")
        assert route.calls.last.request.headers["Authorization"] == "Bearer user_token"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/database/test_database_query.py -v`
Expected: FAIL with missing `DatabaseClient` and `QueryBuilder`

- [ ] **Step 3: Write minimal database query builder implementation**

```python
class QueryBuilder:
    def eq(self, column: str, value: object) -> "QueryBuilder":
        self._params[column] = f"eq.{value}"
        return self

    async def execute(self, *, access_token: str | None = None) -> list[dict[str, object]]:
        return await self._api.get(self._path, params=self._params, access_token=access_token)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/database/test_database_query.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add insforge/database/__init__.py insforge/database/models.py insforge/database/query.py insforge/database/client.py insforge/client.py tests/database/test_database_query.py
git commit -m "feat: add database query builder"
```

### Task 5: Database Admin APIs And OpenAPI Coverage Check For RPC

**Files:**
- Modify: `insforge/database/models.py`
- Modify: `insforge/database/client.py`
- Create: `tests/database/test_database_admin.py`

- [ ] **Step 1: Write the failing tests for table management**

```python
import httpx
import pytest
import respx

from insforge import InsforgeClient


@pytest.mark.asyncio
async def test_list_tables_uses_api_key_only_by_default() -> None:
    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://example.com/api/database/tables").mock(
            return_value=httpx.Response(200, json=["posts", "comments"])
        )
        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            tables = await client.database.list_tables()
        assert tables == ["posts", "comments"]
        assert "Authorization" not in route.calls.last.request.headers


@pytest.mark.asyncio
async def test_get_table_schema_reads_schema_endpoint() -> None:
    with respx.mock(assert_all_called=True) as router:
        router.get("https://example.com/api/database/tables/posts/schema").mock(
            return_value=httpx.Response(200, json={"table_name": "posts", "columns": []})
        )
        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            schema = await client.database.get_table_schema("posts")
        assert schema.table_name == "posts"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/database/test_database_admin.py -v`
Expected: FAIL with missing admin table methods

- [ ] **Step 3: Write minimal admin database implementation**

```python
class DatabaseClient:
    async def list_tables(self) -> list[str]:
        return await self._api.get("/api/database/tables")

    async def get_table_schema(self, table_name: str):
        return await self._api.get(f"/api/database/tables/{table_name}/schema")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/database/test_database_admin.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add insforge/database/models.py insforge/database/client.py tests/database/test_database_admin.py
git commit -m "feat: add database table admin apis"
```

- [ ] **Step 6: Extend database client to full `records.yaml` and `tables.yaml` coverage**

Implement and test the remaining approved database surface:

- record operations: `neq`, `gt`, `gte`, `lt`, `lte`, `like`, `ilike`, `in_`, `is_null`, `not_`, `or_`, `contains`, `contained_by`, `overlaps`, `text_search`, `order`, `offset`, `insert`, `update`, `delete`
- table operations: `create_table`, `update_table_schema`, `delete_table`

Run: `pytest tests/database/test_database_query.py tests/database/test_database_admin.py -v`
Expected: PASS with all paths grounded in `records.yaml` and `tables.yaml`

- [ ] **Step 7: Verify whether RPC is in local OpenAPI before implementing it**

Run: `rg -n "/rpc/" oss_openapi/*.yaml`
Expected: no matches, which means RPC is not currently specified in local OpenAPI files

If the command still returns no matches:

- stop execution on RPC work
- surface the missing contract to the human before adding any inferred `rpc` endpoint or narrowing scope

If the command returns a valid RPC contract:

- add `rpc` implementation and tests using the exact documented path and payloads

### Task 6: Storage Client With Bucket, Object, And Strategy Operations

**Files:**
- Create: `insforge/storage/__init__.py`
- Create: `insforge/storage/models.py`
- Create: `insforge/storage/client.py`
- Modify: `insforge/client.py`
- Create: `tests/storage/test_storage_client.py`

- [ ] **Step 1: Write the failing tests for bucket listing and binary upload**

```python
import httpx
import pytest
import respx

from insforge import InsforgeClient


@pytest.mark.asyncio
async def test_list_buckets_returns_bucket_names() -> None:
    with respx.mock(assert_all_called=True) as router:
        router.get("https://example.com/api/storage/buckets").mock(
            return_value=httpx.Response(200, json={"buckets": ["avatars", "documents"]})
        )
        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            result = await client.storage.list_buckets()
        assert result.buckets == ["avatars", "documents"]


@pytest.mark.asyncio
async def test_upload_object_sends_bytes_and_content_type() -> None:
    with respx.mock(assert_all_called=True) as router:
        route = router.put("https://example.com/api/storage/buckets/avatars/objects/me.png").mock(
            return_value=httpx.Response(201, json={"message": "uploaded"})
        )
        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            await client.storage.upload_object("avatars", "me.png", b"png-bytes", content_type="image/png")
        assert b"png-bytes" in route.calls.last.request.content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/storage/test_storage_client.py -v`
Expected: FAIL with missing storage client

- [ ] **Step 3: Write minimal storage implementation**

```python
class StorageClient:
    async def list_buckets(self):
        return await self._api.get("/api/storage/buckets")

    async def upload_object(self, bucket_name: str, object_name: str, data: bytes, *, content_type: str | None = None, access_token: str | None = None):
        files = {"file": (object_name, data, content_type or "application/octet-stream")}
        return await self._api.put(f"/api/storage/buckets/{bucket_name}/objects/{object_name}", files=files, access_token=access_token)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/storage/test_storage_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add insforge/storage/__init__.py insforge/storage/models.py insforge/storage/client.py insforge/client.py tests/storage/test_storage_client.py
git commit -m "feat: add storage client"
```

- [ ] **Step 6: Extend storage client to full `storage.yaml` coverage**

Implement and test the remaining approved storage surface:

- auto-key upload via `POST /api/storage/buckets/{bucketName}/objects`
- upload strategy via `POST /api/storage/buckets/{bucketName}/upload-strategy`
- confirm upload via `POST /api/storage/buckets/{bucketName}/objects/{objectKey}/confirm-upload`
- download strategy via `POST /api/storage/buckets/{bucketName}/objects/{objectKey}/download-strategy`
- object download and delete endpoints with the exact path/param names from `storage.yaml`
- bucket create, update, and delete endpoints
- object listing endpoint

Run: `pytest tests/storage/test_storage_client.py -v`
Expected: PASS with exact URL coverage from `storage.yaml`

### Task 7: Functions Client With Admin CRUD And Runtime Execution

**Files:**
- Create: `insforge/functions/__init__.py`
- Create: `insforge/functions/models.py`
- Create: `insforge/functions/client.py`
- Modify: `insforge/client.py`
- Create: `tests/functions/test_functions_client.py`

- [ ] **Step 1: Write the failing tests for list and invoke behavior**

```python
import httpx
import pytest
import respx

from insforge import InsforgeClient


@pytest.mark.asyncio
async def test_invoke_without_access_token_is_anonymous() -> None:
    with respx.mock(assert_all_called=True) as router:
        route = router.post("https://example.com/functions/hello-world").mock(
            return_value=httpx.Response(200, json={"message": "hi"})
        )
        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            await client.functions.invoke("hello-world", body={"name": "Ada"})
        assert "Authorization" not in route.calls.last.request.headers


@pytest.mark.asyncio
async def test_invoke_with_access_token_sets_authorization() -> None:
    with respx.mock(assert_all_called=True) as router:
        route = router.post("https://example.com/functions/hello-world").mock(
            return_value=httpx.Response(200, json={"message": "hi"})
        )
        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            await client.functions.invoke("hello-world", body={"name": "Ada"}, access_token="user_token")
        assert route.calls.last.request.headers["Authorization"] == "Bearer user_token"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/functions/test_functions_client.py -v`
Expected: FAIL with missing functions client

- [ ] **Step 3: Write minimal functions implementation**

```python
class FunctionsClient:
    async def invoke(self, slug: str, *, body: dict[str, object] | None = None, headers: dict[str, str] | None = None, access_token: str | None = None):
        return await self._api.post(f"/functions/{slug}", json=body, headers=headers, access_token=access_token)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/functions/test_functions_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add insforge/functions/__init__.py insforge/functions/models.py insforge/functions/client.py insforge/client.py tests/functions/test_functions_client.py
git commit -m "feat: add functions client"
```

- [ ] **Step 6: Extend functions client to full `functions.yaml` coverage**

Implement and test the remaining approved functions surface:

- admin endpoints under `/api/functions`
- runtime execution methods `GET`, `POST`, `PUT`, `PATCH`, and `DELETE` under `/functions/{slug}`
- response handling that permits non-JSON `*/*` payloads when the function runtime returns plain text or binary output

Run: `pytest tests/functions/test_functions_client.py -v`
Expected: PASS with `/functions/{slug}` used for invocation

### Task 8: AI, Email, And Metadata Clients

**Files:**
- Create: `insforge/ai/__init__.py`
- Create: `insforge/ai/models.py`
- Create: `insforge/ai/client.py`
- Create: `insforge/email/__init__.py`
- Create: `insforge/email/models.py`
- Create: `insforge/email/client.py`
- Create: `insforge/metadata/__init__.py`
- Create: `insforge/metadata/models.py`
- Create: `insforge/metadata/client.py`
- Modify: `insforge/client.py`
- Create: `tests/ai/test_ai_client.py`
- Create: `tests/email/test_email_client.py`
- Create: `tests/metadata/test_metadata_client.py`

- [ ] **Step 1: Write the failing tests for ai/email/metadata endpoints**

```python
import httpx
import pytest
import respx

from insforge import InsforgeClient


@pytest.mark.asyncio
async def test_list_ai_configurations_returns_models() -> None:
    with respx.mock(assert_all_called=True) as router:
        router.get("https://example.com/api/ai/configurations").mock(
            return_value=httpx.Response(200, json=[{"id": "cfg-1", "name": "assistant", "model": "openai/gpt"}])
        )
        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            result = await client.ai.list_configurations()
        assert len(result) == 1


@pytest.mark.asyncio
async def test_send_raw_email_uses_explicit_access_token_only() -> None:
    with respx.mock(assert_all_called=True) as router:
        route = router.post("https://example.com/api/email/send-raw").mock(
            return_value=httpx.Response(200, json={})
        )
        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            await client.email.send_raw(to="a@example.com", subject="Hi", html="<p>Hello</p>", access_token="user_token")
        assert route.calls.last.request.headers["Authorization"] == "Bearer user_token"


@pytest.mark.asyncio
async def test_get_metadata_uses_api_key() -> None:
    with respx.mock(assert_all_called=True) as router:
        router.get("https://example.com/api/metadata").mock(
            return_value=httpx.Response(200, json={"name": "Insforge Backend", "version": "2.0.0", "environment": "production"})
        )
        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            result = await client.metadata.get_app_metadata()
        assert result.name == "Insforge Backend"


@pytest.mark.asyncio
async def test_get_database_metadata_uses_explicit_access_token() -> None:
    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://example.com/api/metadata/database").mock(
            return_value=httpx.Response(200, json={"tables": [], "totalTables": 0, "totalRecords": 0, "databaseSize": "0 MB", "lastUpdated": "2026-03-28T00:00:00Z"})
        )
        async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
            await client.metadata.get_database_metadata(access_token="admin_token")
        assert route.calls.last.request.headers["Authorization"] == "Bearer admin_token"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/ai/test_ai_client.py tests/email/test_email_client.py tests/metadata/test_metadata_client.py -v`
Expected: FAIL with missing ai, email, and metadata clients

- [ ] **Step 3: Write minimal ai/email/metadata implementation**

```python
class EmailClient:
    async def send_raw(self, *, to: str | list[str], subject: str, html: str, access_token: str | None = None):
        payload = {"to": to, "subject": subject, "html": html}
        return await self._api.post("/api/email/send-raw", json=payload, access_token=access_token)
```

```python
class MetadataClient:
    async def get_app_metadata(self):
        return await self._api.get("/api/metadata")

    async def get_database_metadata(self, *, access_token: str | None = None):
        return await self._api.get("/api/metadata/database", access_token=access_token)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/ai/test_ai_client.py tests/email/test_email_client.py tests/metadata/test_metadata_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add insforge/ai/__init__.py insforge/ai/models.py insforge/ai/client.py insforge/email/__init__.py insforge/email/models.py insforge/email/client.py insforge/metadata/__init__.py insforge/metadata/models.py insforge/metadata/client.py insforge/client.py tests/ai/test_ai_client.py tests/email/test_email_client.py tests/metadata/test_metadata_client.py
git commit -m "feat: add ai email and metadata clients"
```

- [ ] **Step 6: Extend AI client to full `ai.yaml` coverage**

Implement and test the remaining approved AI surface:

- `/api/ai/configurations/{id}` update/delete
- `/api/ai/usage/summary`
- `/api/ai/usage`
- `/api/ai/usage/config/{configId}`
- `/api/ai/credits`
- `/api/ai/models`
- `/api/ai/chat/completion`
- `/api/ai/image/generation`
- `/api/ai/embeddings`

Also extend metadata client to full `metadata.yaml` coverage:

- `/api/metadata/database`
- `/api/metadata/api-key`

Run: `pytest tests/ai/test_ai_client.py -v`
Run: `pytest tests/ai/test_ai_client.py tests/metadata/test_metadata_client.py -v`
Expected: PASS with explicit request models for admin and client AI endpoints and full metadata coverage

### Task 9: Final Wiring, Documentation, And Full Verification

**Files:**
- Modify: `README.md`
- Modify: `insforge/__init__.py`
- Modify: `insforge/client.py`
- Modify: `pyproject.toml`
- Modify: `tests/test_client.py`

- [ ] **Step 1: Write the failing tests for public exports and context manager lifecycle**

```python
import pytest

from insforge import InsforgeClient


@pytest.mark.asyncio
async def test_client_can_be_used_as_async_context_manager() -> None:
    async with InsforgeClient(base_url="https://example.com", api_key="ins_test") as client:
        assert client.functions is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_client.py -v`
Expected: FAIL if `__aenter__`, `__aexit__`, or final exports are incomplete

- [ ] **Step 3: Write minimal final wiring and docs**

```python
class InsforgeClient:
    async def __aenter__(self) -> "InsforgeClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()
```

```python
__all__ = ["InsforgeClient"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest -v`
Expected: PASS across the full mocked test suite

- [ ] **Step 5: Commit**

```bash
git add README.md insforge/__init__.py insforge/client.py pyproject.toml tests/test_client.py
git commit -m "docs: finalize python sdk surface and usage"
```

## Verification Notes

- Prefer `respx` assertions over ad hoc mocks so tests verify exact URL, headers, and request bodies.
- For request auth tests, assert three cases explicitly:
  - only `X-API-Key`
  - `X-API-Key` plus bearer when `access_token` is supplied
  - no implicit bearer on subsequent unrelated calls
- For transport behavior, include one test that caller-supplied extra headers do not override SDK-controlled bearer semantics.
- Do not implement RPC unless a local OpenAPI contract is located first.
- Keep object upload tests at the request-shape level unless the storage OpenAPI requires a more specific multipart field layout.

## Risks To Watch During Execution

- OpenAPI field naming is inconsistent in several files (`bucketName` vs `bucket`, `nextAction` vs `nextActions`, camelCase vs snake_case). Normalize with pydantic aliases and tolerant error parsing.
- Storage upload/download endpoints may require a different object path or multipart field name than the examples imply. Check `storage.yaml` carefully before implementation.
- Auth endpoint names for login, signup, refresh, signout, email flows, and OAuth flows need to be matched exactly to `auth.yaml`; do not infer from Swift/Kotlin names without verification.
- Database count and pagination headers should not be overdesigned in v1. Add only what the local OpenAPI explicitly supports.
- The repository is greenfield, so setup drift in `pyproject.toml` can block all tests if dependency groups and package discovery are wrong.
