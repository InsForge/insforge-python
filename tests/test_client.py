from insforge._base_client import build_headers
from insforge import InsforgeClient


def test_client_normalizes_base_url():
    client = InsforgeClient(base_url="https://example.com/", api_key="ins_test")

    assert str(client.base_url) == "https://example.com"


def test_client_stores_base_url_and_api_key():
    client = InsforgeClient(base_url="https://example.com/", api_key="ins_test")

    assert client.api_key == "ins_test"


def test_client_preserves_base_url_path_components():
    client = InsforgeClient(
        base_url="https://api.example.com/v1/",
        api_key="ins_test",
    )

    assert str(client.base_url) == "https://api.example.com/v1"


def test_build_headers_includes_api_key_without_authorization() -> None:
    headers = build_headers(api_key="ins_test")

    assert headers["X-API-Key"] == "ins_test"
    assert "Authorization" not in headers


def test_build_headers_uses_explicit_access_token_only() -> None:
    headers = build_headers(api_key="ins_test", access_token="user_token")

    assert headers["Authorization"] == "Bearer user_token"


def test_build_headers_rejects_authorization_override() -> None:
    headers = build_headers(
        api_key="ins_test",
        extra_headers={"Authorization": "Bearer wrong", "X-Test": "1"},
    )

    assert "Authorization" not in headers
    assert headers["X-Test"] == "1"
