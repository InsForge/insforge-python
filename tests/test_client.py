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
