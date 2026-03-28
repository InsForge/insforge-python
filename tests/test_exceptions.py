import httpx

from insforge.exceptions import InsforgeHTTPError


def test_http_error_parses_openapi_error_payload() -> None:
    response = httpx.Response(
        401,
        json={
            "error": "UNAUTHORIZED",
            "message": "Invalid token",
            "statusCode": 401,
            "nextAction": "Login again",
        },
    )

    exc = InsforgeHTTPError.from_response("GET", "/api/test", response)

    assert exc.status_code == 401
    assert exc.error == "UNAUTHORIZED"
    assert exc.message == "Invalid token"
    assert exc.next_action == "Login again"


def test_http_error_normalizes_next_actions_field() -> None:
    response = httpx.Response(
        400,
        json={
            "error": "BAD_REQUEST",
            "message": "Check input",
            "nextActions": "Fix request",
        },
    )

    exc = InsforgeHTTPError.from_response("POST", "/api/test", response)

    assert exc.next_action == "Fix request"
