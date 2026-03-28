# InsForge Python SDK Design

**Date:** 2026-03-28

**Status:** Approved for implementation after user review

## Goal

Build a Python SDK for InsForge OSS from the OpenAPI specs in `oss_openapi`, following the same high-level module split as the Kotlin and Swift SDKs, but adapted for server-side Python usage:

- async support is required
- realtime is out of scope for v1
- the SDK is stateless with respect to user sessions
- the SDK defaults to `api_key`-based server usage
- per-user bearer tokens are passed explicitly per request and are never cached in memory or persisted locally

## Scope

### Included in v1

- `auth`
- `database`
  - `records`
  - `tables`
  - `rpc`
- `storage`
- `functions`
- `ai`
- `email`
- `metadata`

### Excluded from v1

- `realtime`
- `secrets`
- `logs`
- `health`
- OAuth browser helpers
- PKCE helpers
- local token/session storage
- automatic token refresh and retry

## Product Positioning

This SDK is a server-side integration SDK, not a client/mobile SDK.

That means:

- initialization uses `api_key`, not `anon_key`
- the SDK does not own authentication state
- auth endpoints return their documented response payloads to the caller, but the SDK does not store any token or session state from them
- downstream API calls that need user identity must receive `access_token` explicitly on each request
- if a caller does not provide `access_token`, the SDK must not send `Authorization: Bearer ...`
- management/admin endpoints should work naturally with `api_key`

This avoids token leakage across concurrent requests and matches typical backend service usage where a web handler extracts a user token from the inbound request and passes it through to the SDK call that needs it.

## API Shape

## Top-Level Client

The top-level entry point is `InsforgeClient`.

Example:

```python
from insforge import InsforgeClient

client = InsforgeClient(
    base_url="https://project.example.com",
    api_key="ins_xxx",
)
```

The client exposes sub-clients as properties:

```python
client.auth
client.database
client.storage
client.functions
client.ai
client.email
client.metadata
```

The top-level client owns:

- normalized `base_url`
- `api_key`
- shared async HTTP transport
- shared JSON and multipart helpers
- request building and error handling

It does not own:

- current user session
- access token cache
- refresh token cache
- auth persistence

## Authentication Model

Every request can optionally receive `access_token`.

Rules:

- always send `X-API-Key: <api_key>` by default
- only send `Authorization: Bearer <access_token>` when `access_token` is explicitly passed to that method call
- if `access_token` is omitted, the request is anonymous from a bearer-token perspective
- token-issuing auth methods return token-bearing payloads directly to the caller, while config/profile auth methods return their documented payloads; none of these responses mutate local auth state
- the SDK never stores or mutates authentication state after auth calls complete

This applies to `auth`, `database`, `storage`, `functions`, `ai`, `email`, and any other module with bearer-auth endpoints.

## Sync And Async Support

The implementation is async-first.

Primary interface:

- `InsforgeClient` backed by `httpx.AsyncClient`

Optional compatibility layer:

- thin synchronous wrapper may be added after async coverage is complete

For v1 implementation priority, the async API must be complete. Sync support is secondary and should not duplicate the full implementation stack.

## Module Design

## Auth

`AuthClient` provides explicit calls to auth/profile endpoints from `auth.yaml`.

Representative methods:

- `get_public_config()`
- `sign_up(...)`
- `sign_in_with_password(...)`
- `refresh_token(...)`
- `sign_out(access_token=...)`
- `get_profile(user_id, access_token=None)`
- `update_current_profile(profile, access_token=...)`

Design rules:

- token-issuing auth methods return token-bearing payloads directly to the caller, and non-token auth/profile methods return their documented response models
- no token persistence
- no in-memory mutation of the parent client
- bearer-protected auth/profile endpoints receive `access_token` explicitly
- if a caller omits `access_token`, the SDK sends no `Authorization` header

## Database

`DatabaseClient` has two layers.

### Query Builder Layer

This covers `records.yaml` and follows the Kotlin/Swift style closely.

Example:

```python
posts = await client.database.from_("posts") \
    .select("id,title") \
    .eq("status", "active") \
    .order("createdAt", desc=True) \
    .limit(20) \
    .execute(access_token=user_token)
```

Supported builder operations in v1:

- `select(columns="*")`
- `eq`, `neq`, `gt`, `gte`, `lt`, `lte`
- `like`, `ilike`
- `in_`
- `is_null`
- `not_`
- `or_`
- `contains`
- `contained_by`
- `overlaps`
- `text_search`
- `order`
- `limit`
- `offset`
- `insert`
- `update`
- `delete`
- `execute`

Implementation constraints:

- builder stays lightweight and maps directly to query parameters
- request-level auth is supplied at `execute(...)` time, not attached to the builder state
- dynamic record payloads are supported as `dict[str, Any]`
- typed decoding may be added via generic helpers, but raw dict support is the baseline

### Admin Database Methods

This covers table management and RPC:

- `list_tables(...)`
- `create_table(...)`
- `get_table_schema(...)`
- `update_table_schema(...)`
- `delete_table(...)`
- `rpc(name, args=None, access_token=None)`

Auth rules:

- admin methods default to `api_key`
- bearer token can still be passed explicitly when needed by the backend

## Storage

`StorageClient` exposes bucket and object operations.

Bucket-level operations:

- `list_buckets(...)`
- `create_bucket(...)`
- `update_bucket(...)`
- `delete_bucket(...)`

Object-level operations:

- `list_objects(bucket_name, ...)`
- `upload_object(bucket_name, object_name, data, content_type=None, access_token=None)`
- `download_object(bucket_name, object_name, access_token=None)`
- `delete_object(bucket_name, object_name, access_token=None)`
- any additional list/move/copy operations present in the spec

Implementation details:

- upload accepts `bytes`, file-like objects, and optionally filesystem paths if that fits the API shape
- binary responses should return raw bytes or streamed responses depending on endpoint semantics
- object APIs also follow request-level token passing

## Functions

`FunctionsClient` uses explicit methods instead of a DSL.

Representative methods:

- `list_functions(...)`
- `create_function(...)`
- `get_function(slug, ...)`
- `update_function(slug, ...)`
- `delete_function(slug, ...)`
- `invoke(slug, body=None, headers=None, access_token=None)`

Invocation rule:

- if `access_token` is omitted, do not send an `Authorization` header
- invocation remains anonymous except for the always-present `X-API-Key`

## AI

`AIClient` starts with explicit admin/configuration and usage methods from `ai.yaml`.

Representative methods:

- `create_configuration(...)`
- `list_configurations(...)`
- `update_configuration(...)`
- `delete_configuration(...)`
- `get_usage_summary(...)`
- `get_usage(...)`
- `get_usage_by_configuration(...)`

If additional generation/chat endpoints exist in the remaining OpenAPI content, they should also be exposed as explicit methods rather than a builder abstraction.

## Email

`EmailClient` is a small explicit wrapper around `email.yaml`.

Representative method:

- `send_raw(...)`

This endpoint accepts `access_token` explicitly. If the caller omits it, the SDK sends no `Authorization` header and leaves authorization enforcement to the backend.

## Metadata

`MetadataClient` wraps `metadata.yaml`.

Representative methods:

- `get_app_metadata(...)`
- `get_database_metadata(...)`
- `get_api_key(...)`

## Data Models

Use `pydantic` v2 for request and response models.

Modeling rules:

- create explicit models for stable request/response schemas from OpenAPI
- use `alias` support for mixed `camelCase` and `snake_case` API fields
- parse timestamps into `datetime`
- leave dynamic record payloads as `dict[str, Any]` unless a typed generic helper is provided
- keep models module-local where it improves readability, or split to `models.py` when a module grows

Examples of explicit models:

- auth responses and profile payloads
- table schema definitions
- function metadata/details
- AI configuration and usage responses
- storage bucket metadata

## Error Handling

All HTTP failures should be normalized into SDK exceptions.

Exception hierarchy:

- `InsforgeError`
- `InsforgeHTTPError`
- `InsforgeAuthError`
- `InsforgeValidationError`
- `InsforgeSerializationError`

`InsforgeHTTPError` should preserve:

- `status_code`
- `error`
- `message`
- `next_action` or `next_actions`
- raw response payload when parsing fails

Behavior rules:

- prefer parsing the OpenAPI-style error object
- gracefully handle inconsistent field names such as `nextAction` vs `nextActions`
- include the request method/path in exception messages where useful

## Request Construction Rules

The shared request layer should:

- normalize `base_url` without double slashes
- inject `X-API-Key`
- inject bearer auth only when `access_token` is passed
- ignore or reject caller-supplied `Authorization` inside ad hoc header overrides so bearer identity is controlled only by the dedicated `access_token` argument
- support JSON body requests
- support multipart/file upload requests
- support raw binary downloads
- encode query params safely, including repeated values and PostgREST filters
- expose timeout and optional extra headers overrides
- use a stateless transport configuration without persistent cookies or any session/token cache beyond the lifetime of the individual HTTP request

The request layer should not:

- mutate global auth state
- retry token refresh automatically
- infer user identity from previous calls

## Package Layout

Proposed package layout:

```text
insforge/
  __init__.py
  client.py
  exceptions.py
  types.py
  _base_client.py
  _utils.py
  auth/
    __init__.py
    client.py
    models.py
  database/
    __init__.py
    client.py
    query.py
    models.py
  storage/
    __init__.py
    client.py
    models.py
  functions/
    __init__.py
    client.py
    models.py
  ai/
    __init__.py
    client.py
    models.py
  email/
    __init__.py
    client.py
    models.py
  metadata/
    __init__.py
    client.py
    models.py
tests/
  ...
```

This keeps modules focused and mirrors the domain structure already used by the other SDKs.

## Testing Strategy

Testing must follow TDD during implementation.

Coverage targets for v1:

- client initialization and header construction
- request-level auth behavior
  - `api_key` always included
  - bearer omitted when `access_token` is absent
  - bearer included only for the specific call when `access_token` is present
- error parsing and exception mapping
- representative success and failure tests for each module
- database query builder URL/query generation
- multipart upload request formation for storage
- header and response handling for functions invocation

Testing approach:

- use `pytest`
- use `pytest-asyncio`
- use `respx` or equivalent HTTPX mocking for transport-level assertions

Because this repository starts empty, the test suite should validate behavior through mocked HTTP responses rather than depending on a live InsForge backend.

## Documentation

v1 should include:

- package README with install and quick-start examples
- async usage examples
- explicit examples showing request-level `access_token`
- note explaining stateless server-side auth behavior

Important examples:

- anonymous function invocation
- authenticated database query with `access_token`
- auth sign-in returning tokens without local persistence
- admin table/storage operation using only `api_key`

## Implementation Boundaries

To keep v1 practical:

- prefer explicit methods over meta-programmed code generation
- do not attempt to generate the SDK directly from OpenAPI at runtime
- wrap every non-realtime operation present in the local `oss_openapi/*.yaml` files
- follow the Kotlin/Swift client split, but adapt semantics to Python server usage
- avoid introducing sync and async dual implementations unless the sync layer is very thin

## Open Questions Resolved

- Realtime support: excluded from v1
- Async support: required
- Token persistence: forbidden
- In-memory auth state: forbidden
- Default auth at initialization: `api_key`
- Per-request bearer behavior: explicit only
- Missing `access_token` on `functions.invoke(...)`: no `Authorization` header sent

## Acceptance Criteria

The design is successful if the resulting SDK:

- cleanly wraps all non-realtime OpenAPI modules
- exposes an idiomatic async Python API
- is safe for multi-user backend services because it is stateless
- allows admin calls with `api_key`
- allows per-request user impersonation by passing `access_token`
- never caches auth state across calls
- has a tested database query builder and tested transport/auth behavior
