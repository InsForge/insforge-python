# Insforge Python SDK

Async-first, stateless Python client for the [Insforge](https://insforge.com) platform. Covers auth, database, storage, serverless functions, AI, email, and metadata APIs.

## Requirements

- Python 3.11+

## Installation

```bash
pip install insforge
```

## Quick Start

```python
import asyncio
from insforge import InsforgeClient

async def main():
    async with InsforgeClient(base_url="https://your-project.insforge.app", api_key="ins_xxx") as client:
        # Public endpoint (API key only)
        config = await client.auth.get_public_config()

        # Sign in
        session = await client.auth.sign_in_with_password(email="user@example.com", password="secret")
        token = session.access_token

        # Authenticated request
        me = await client.auth.get_current_session(access_token=token)
        print(me.user.email)

asyncio.run(main())
```

## Modules

### Auth

User registration, sign-in, session management, email verification, password reset, admin auth, and OAuth.

```python
# Sign in
session = await client.auth.sign_in_with_password(email="...", password="...")

# Create user
user = await client.auth.create_user(email="...", password="...")

# Email verification
await client.auth.send_email_verification(email="...")
await client.auth.verify_email(email="...", otp="123456")

# Passwordless email OTP sign-in
await client.auth.sign_in_with_otp(email="...")
session = await client.auth.verify_otp(email="...", otp="123456")

# Password reset
await client.auth.send_reset_password_email(email="...")
resp = await client.auth.exchange_reset_password_token(email="...", code="123456")
await client.auth.reset_password(new_password="...", token=resp.token)

# User management (admin)
users = await client.auth.list_users(access_token=admin_token)
await client.auth.delete_users(["user-id-1"], access_token=admin_token)

# Config
await client.auth.get_config(access_token=admin_token)
await client.auth.update_config({"requireEmailVerification": True}, access_token=admin_token)
```

### Database

PostgREST-style query builder and table administration.

```python
# Query records
rows = await client.database.from_("posts") \
    .select("id,title") \
    .eq("status", "published") \
    .order("created_at", desc=True) \
    .limit(10) \
    .execute()

# Insert
await client.database.from_("posts").insert([{"title": "Hello", "status": "draft"}])

# Update with filters
await client.database.from_("posts").eq("id", 1).update({"status": "published"})

# Delete with filters
await client.database.from_("posts").eq("id", 1).delete()

# Table admin
tables = await client.database.list_tables()
schema = await client.database.get_table_schema("posts")
await client.database.create_table(
    table_name="comments",
    columns=[{"name": "id", "type": "uuid", "nullable": False}],
)
await client.database.update_table_schema("comments", add_columns=[...])
await client.database.delete_table("comments")
```

### Storage

Object upload, download, and deletion.

```python
buckets = await client.storage.list_buckets()

await client.storage.upload_object("my-bucket", "photos/cat.jpg", image_bytes, content_type="image/jpeg")

data = await client.storage.download_object("my-bucket", "photos/cat.jpg")

await client.storage.delete_object("my-bucket", "photos/cat.jpg")

# Delete multiple objects in one request (maximum 1000 keys)
response = await client.storage.delete_objects("my-bucket", ["photos/cat.jpg", "photos/dog.jpg"])
# response.results: one entry per key with status "deleted" | "notFound" | "failed"
```

### Functions

Serverless function admin and invocation.

```python
# CRUD
await client.functions.create_function(name="greet", code="export default (req) => ...", access_token=token)
fns = await client.functions.list_functions(access_token=token)
fn = await client.functions.get_function("greet", access_token=token)
await client.functions.update_function("greet", code="...", access_token=token)
await client.functions.delete_function("greet", access_token=token)

# Invoke
result = await client.functions.invoke("greet", body={"name": "World"})
```

### AI

Chat completions, image generation, embeddings, configuration, usage tracking, and credits.

```python
from insforge.ai.models import AIChatMessage

# Chat
resp = await client.ai.chat_completion(
    model="openai/gpt-4o",
    messages=[AIChatMessage(role="user", content="Hello!")],
    access_token=token,
)
print(resp.text)

# Image generation
images = await client.ai.generate_images(model="openai/dall-e-3", prompt="A cat", access_token=token)

# Embeddings
emb = await client.ai.generate_embeddings(model="openai/text-embedding-3-small", input="hello", access_token=token)

# Configuration & usage
configs = await client.ai.list_configurations(access_token=token)
summary = await client.ai.get_usage_summary(access_token=token)
credits = await client.ai.get_credits(access_token=token)
models = await client.ai.list_models(access_token=token)
```

### Email

```python
await client.email.send_raw(
    to="recipient@example.com",
    subject="Hello",
    html="<h1>Hi there</h1>",
    access_token=token,
)
```

### Metadata

```python
app = await client.metadata.get_app_metadata()
db = await client.metadata.get_database_metadata()
key = await client.metadata.get_api_key()
```

## Error Handling

```python
from insforge.exceptions import InsforgeHTTPError, InsforgeAuthError

try:
    await client.auth.sign_in_with_password(email="...", password="wrong")
except InsforgeAuthError as e:
    print(e.status_code, e.error, e.message, e.next_action)
except InsforgeHTTPError as e:
    print(e.method, e.path, e.status_code)
```

Exception hierarchy:

- `InsforgeError` - base
  - `InsforgeHTTPError` - HTTP errors (status code, parsed error/message)
    - `InsforgeAuthError` - auth-specific HTTP errors
  - `InsforgeValidationError` - Pydantic validation failures
  - `InsforgeSerializationError` - serialization failures

## Logging

The SDK uses Python's built-in `logging` module under the `insforge` logger. By default no logs are emitted. Call `setup_logging` to enable output:

```python
import insforge

# INFO — SDK initialization details and important operation results
insforge.setup_logging("INFO")

# DEBUG — full HTTP request/response (method, URL, params, status code)
insforge.setup_logging("DEBUG")
```

You can also configure the `insforge` logger directly with the standard `logging` module for more advanced setups:

```python
import logging

logging.getLogger("insforge").setLevel(logging.DEBUG)
```

## Authentication Model

The SDK is **stateless** - it never stores or caches tokens. Every method that requires user auth takes an explicit `access_token` parameter. The API key is sent as `X-API-Key` on every request automatically.

```python
# API key only (default for all requests)
config = await client.auth.get_public_config()

# API key + bearer token
me = await client.auth.get_current_session(access_token="user_jwt_here")
```

## Development

### Setup

```bash
git clone <repo-url>
cd insforge-python
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]" 2>/dev/null || pip install -e .
pip install pytest pytest-asyncio
```

### Run Tests

```bash
python -m pytest
```

### Build

```bash
pip install build
python -m build
```

This produces `dist/insforge-<version>.tar.gz` and `dist/insforge-<version>-py3-none-any.whl`.

### Release to PyPI

Publishing uses PyPI Trusted Publishing through `.github/workflows/publish.yml`; no PyPI API token is stored in GitHub. The workflow publishes both the wheel and source distribution and produces digital attestations.

1. Update `project.version` in `pyproject.toml` and merge the change to `main` after CI passes.
2. Create and push an annotated tag that exactly matches the package version with a `v` prefix:

```bash
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin vX.Y.Z
```

The tag triggers a build, metadata validation, and publication to PyPI. PEP 440 prerelease versions are supported as long as the tag exactly matches the version in `pyproject.toml`. After PyPI publication succeeds, stable `X.Y.Z` versions create a GitHub Release automatically; prerelease tags do not.

## License

See [LICENSE](LICENSE) for details.
