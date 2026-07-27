import asyncio

import httpx
import pytest
from pydantic import ValidationError

from insforge import InsforgeClient
from insforge.auth.models import AuthConfigUpdateRequest
from insforge.auth.models import AuthSendOtpRequest
from insforge.auth.models import AuthUserCreateRequest
from insforge.auth.models import AuthVerifyOtpRequest
from insforge.exceptions import InsforgeAuthError


def test_sign_in_with_password_returns_tokens_without_mutating_client_state() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                json={
                    "accessToken": "access",
                    "refreshToken": "refresh",
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.auth.sign_in_with_password(
                email="a@example.com",
                password="secret",
            )

            assert client.api_key == "ins_test"
            assert not hasattr(client, "access_token")
            assert not hasattr(client, "refresh_token")
            return result, captured

    result, captured = asyncio.run(scenario())

    assert result.access_token == "access"
    assert result.refresh_token == "refresh"
    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.com/api/auth/sessions"
    assert captured["kwargs"]["params"] == {"client_type": "server"}
    assert captured["kwargs"]["json"] == {"email": "a@example.com", "password": "secret"}
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"


def test_update_current_profile_sends_bearer_token() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                json={
                    "userId": "u1",
                    "profile": {"name": "Ada"},
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.auth.update_current_profile(
                {"name": "Ada"},
                access_token="user_token",
            )

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "PATCH"
    assert captured["url"] == "https://example.com/api/auth/profiles/current"
    assert captured["kwargs"]["json"] == {"profile": {"name": "Ada"}}
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer user_token"
    assert result.user_id == "u1"
    assert result.profile == {"name": "Ada"}


def test_public_config_and_profile_endpoints_do_not_send_authorization() -> None:
    async def scenario() -> tuple[dict[str, object], dict[str, object], object, object]:
        calls: list[dict[str, object]] = []

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            call = {"method": method, "url": str(url), "kwargs": kwargs}
            calls.append(call)

            if str(url).endswith("/api/auth/public-config"):
                return httpx.Response(
                    200,
                    json={
                        "oAuthProviders": ["google"],
                        "customOAuthProviders": ["corp"],
                        "requireEmailVerification": True,
                        "passwordMinLength": 12,
                    },
                )

            return httpx.Response(
                200,
                json={
                    "id": "user-1",
                    "profile": {"name": "Ada"},
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            public_config = await client.auth.get_public_config()
            profile = await client.auth.get_profile("user-1")

            return calls[0], calls[1], public_config, profile

    public_call, profile_call, public_config, profile = asyncio.run(scenario())

    assert public_call["method"] == "GET"
    assert public_call["url"] == "https://example.com/api/auth/public-config"
    assert public_call["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert "Authorization" not in public_call["kwargs"]["headers"]
    assert public_config.o_auth_providers == ["google"]
    assert public_config.custom_o_auth_providers == ["corp"]
    assert public_config.require_email_verification is True
    assert public_config.password_min_length == 12

    assert profile_call["method"] == "GET"
    assert profile_call["url"] == "https://example.com/api/auth/profiles/user-1"
    assert profile_call["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert "Authorization" not in profile_call["kwargs"]["headers"]
    assert profile.id == "user-1"
    assert profile.profile == {"name": "Ada"}


def test_auth_config_and_user_management_endpoints_request_expected_payloads() -> None:
    async def scenario() -> tuple[list[dict[str, object]], object, object, object, object]:
        calls: list[dict[str, object]] = []

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            calls.append({"method": method, "url": str(url), "kwargs": kwargs})

            if method == "GET" and str(url).endswith("/api/auth/config"):
                return httpx.Response(
                    200,
                    json={
                        "id": "cfg-1",
                        "requireEmailVerification": True,
                        "passwordMinLength": 10,
                        "allowedRedirectUrls": ["https://app.example.com"],
                    },
                )

            if method == "PUT":
                return httpx.Response(
                    200,
                    json={
                        "id": "cfg-1",
                        "requireEmailVerification": False,
                        "passwordMinLength": 8,
                        "allowedRedirectUrls": ["https://new.example.com"],
                    },
                )

            if method == "GET" and str(url).endswith("/api/auth/users"):
                return httpx.Response(
                    200,
                    json={
                        "data": [
                            {
                                "id": "u1",
                                "email": "a@example.com",
                                "profile": {"name": "Ada"},
                                "metadata": {"source": "import"},
                                "emailVerified": True,
                                "providers": ["password"],
                            }
                        ],
                        "pagination": {"offset": 0, "limit": 10, "total": 1},
                    },
                )

            if method == "POST":
                return httpx.Response(
                    200,
                    json={
                        "user": {
                            "id": "u2",
                            "email": "b@example.com",
                            "profile": {"name": "Bea"},
                            "emailVerified": False,
                        },
                        "accessToken": "access",
                        "refreshToken": "refresh",
                        "requireEmailVerification": False,
                    },
                )

            return httpx.Response(200, json={"message": "Users deleted successfully", "deletedCount": 2})

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            auth_config = await client.auth.get_config(access_token="admin_token")
            updated_config = await client.auth.update_config(
                {"requireEmailVerification": False, "allowedRedirectUrls": ["https://new.example.com"]},
                access_token="admin_token",
            )
            users = await client.auth.list_users(
                offset=5,
                limit=2,
                search="ada",
                access_token="admin_token",
            )
            created_user = await client.auth.create_user(
                email="b@example.com",
                password="secret123",
                name="Bea",
                redirect_to="https://app.example.com/sign-in",
            )
            deleted_users = await client.auth.delete_users(
                ["u1", "u2"],
                access_token="admin_token",
            )

            return calls, auth_config, updated_config, users, created_user, deleted_users

    calls, auth_config, updated_config, users, created_user, deleted_users = asyncio.run(scenario())

    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == "https://example.com/api/auth/config"
    assert calls[0]["kwargs"]["headers"]["Authorization"] == "Bearer admin_token"
    assert calls[0]["kwargs"]["headers"]["X-API-Key"] == "ins_test"

    assert calls[1]["method"] == "PUT"
    assert calls[1]["kwargs"]["json"] == {
        "requireEmailVerification": False,
        "allowedRedirectUrls": ["https://new.example.com"],
    }
    assert calls[1]["kwargs"]["headers"]["Authorization"] == "Bearer admin_token"

    assert calls[2]["method"] == "GET"
    assert calls[2]["kwargs"]["params"] == {"offset": "5", "limit": "2", "search": "ada"}
    assert calls[2]["kwargs"]["headers"]["Authorization"] == "Bearer admin_token"

    assert calls[3]["method"] == "POST"
    assert calls[3]["url"] == "https://example.com/api/auth/users"
    assert calls[3]["kwargs"]["params"] == {"client_type": "server"}
    assert calls[3]["kwargs"]["json"] == {
        "email": "b@example.com",
        "password": "secret123",
        "name": "Bea",
        "redirectTo": "https://app.example.com/sign-in",
    }
    assert "Authorization" not in calls[3]["kwargs"]["headers"]

    assert calls[4]["method"] == "DELETE"
    assert calls[4]["kwargs"]["json"] == {"userIds": ["u1", "u2"]}
    assert calls[4]["kwargs"]["headers"]["Authorization"] == "Bearer admin_token"

    assert auth_config.id == "cfg-1"
    assert auth_config.require_email_verification is True
    assert auth_config.password_min_length == 10
    assert auth_config.allowed_redirect_urls == ["https://app.example.com"]

    assert updated_config.require_email_verification is False
    assert updated_config.allowed_redirect_urls == ["https://new.example.com"]

    assert users.data[0].id == "u1"
    assert users.pagination.offset == 0
    assert users.pagination.total == 1

    assert created_user.user.email == "b@example.com"
    assert created_user.access_token == "access"
    assert created_user.refresh_token == "refresh"

    assert deleted_users.deleted_count == 2
    assert deleted_users.message == "Users deleted successfully"


def test_session_refresh_logout_current_and_admin_endpoints_request_expected_payloads() -> None:
    async def scenario() -> tuple[list[dict[str, object]], object, object, object, object, object, object]:
        calls: list[dict[str, object]] = []

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            calls.append({"method": method, "url": str(url), "kwargs": kwargs})

            if str(url).endswith("/api/auth/sessions/current"):
                return httpx.Response(200, json={"user": {"id": "u1", "email": "a@example.com", "role": "authenticated"}})

            if str(url).endswith("/api/auth/refresh"):
                return httpx.Response(
                    200,
                    json={
                        "user": {
                            "id": "u1",
                            "email": "a@example.com",
                            "profile": {"name": "Ada"},
                            "emailVerified": True,
                        },
                        "accessToken": "new-access",
                        "refreshToken": "new-refresh",
                    },
                )

            if str(url).endswith("/api/auth/logout"):
                return httpx.Response(200, json={"success": True, "message": "Logged out successfully"})

            if str(url).endswith("/api/auth/admin/sessions/exchange"):
                return httpx.Response(200, json={"user": {"id": "admin-1", "email": "admin@example.com"}, "accessToken": "admin-access"})

            if str(url).endswith("/api/auth/admin/sessions"):
                return httpx.Response(200, json={"user": {"id": "admin-1", "email": "admin@example.com"}, "accessToken": "admin-login"})

            return httpx.Response(
                200,
                json={
                    "accessToken": "anon-access",
                    "message": "Anonymous token generated successfully (never expires)",
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            current_session = await client.auth.get_current_session(access_token="user_token")
            refreshed = await client.auth.refresh(refresh_token="refresh-token")
            logout = await client.auth.logout()
            admin_login = await client.auth.admin_sign_in(email="admin@example.com", password="secret")
            exchange = await client.auth.exchange_admin_session(code="auth-code")
            anon = await client.auth.create_anon_token(access_token="admin_token")

            return calls, current_session, refreshed, logout, admin_login, exchange, anon

    calls, current_session, refreshed, logout, admin_login, exchange, anon = asyncio.run(scenario())

    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == "https://example.com/api/auth/sessions/current"
    assert calls[0]["kwargs"]["headers"]["Authorization"] == "Bearer user_token"
    assert calls[0]["kwargs"]["headers"]["X-API-Key"] == "ins_test"

    assert calls[1]["method"] == "POST"
    assert calls[1]["kwargs"]["params"] == {"client_type": "server"}
    assert calls[1]["kwargs"]["json"] == {"refreshToken": "refresh-token"}
    assert "Authorization" not in calls[1]["kwargs"]["headers"]

    assert calls[2]["method"] == "POST"
    assert calls[2]["url"] == "https://example.com/api/auth/logout"
    assert "Authorization" not in calls[2]["kwargs"]["headers"]

    assert calls[3]["method"] == "POST"
    assert calls[3]["url"] == "https://example.com/api/auth/admin/sessions"
    assert calls[3]["kwargs"]["json"] == {"email": "admin@example.com", "password": "secret"}
    assert "Authorization" not in calls[3]["kwargs"]["headers"]

    assert calls[4]["method"] == "POST"
    assert calls[4]["url"] == "https://example.com/api/auth/admin/sessions/exchange"
    assert calls[4]["kwargs"]["json"] == {"code": "auth-code"}
    assert "Authorization" not in calls[4]["kwargs"]["headers"]

    assert calls[5]["method"] == "POST"
    assert calls[5]["url"] == "https://example.com/api/auth/tokens/anon"
    assert calls[5]["kwargs"]["headers"]["Authorization"] == "Bearer admin_token"

    assert current_session.user.id == "u1"
    assert current_session.user.email == "a@example.com"
    assert current_session.user.role == "authenticated"

    assert refreshed.user.email == "a@example.com"
    assert refreshed.access_token == "new-access"
    assert refreshed.refresh_token == "new-refresh"

    assert logout.success is True
    assert logout.message == "Logged out successfully"

    assert admin_login.user.id == "admin-1"
    assert admin_login.access_token == "admin-login"

    assert exchange.user.email == "admin@example.com"
    assert exchange.access_token == "admin-access"

    assert anon.access_token == "anon-access"
    assert anon.message == "Anonymous token generated successfully (never expires)"


def test_sign_in_with_password_raises_insforge_auth_error_on_failure() -> None:
    async def scenario() -> None:
        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            return httpx.Response(
                401,
                json={
                    "error": "UNAUTHORIZED",
                    "message": "Invalid credentials",
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            await client.auth.sign_in_with_password(
                email="a@example.com",
                password="secret",
            )

    with pytest.raises(InsforgeAuthError) as exc_info:
        asyncio.run(scenario())

    assert exc_info.value.error == "UNAUTHORIZED"
    assert exc_info.value.message == "Invalid credentials"


def test_email_verification_and_reset_password_json_endpoints_request_expected_payloads() -> None:
    async def scenario() -> tuple[list[dict[str, object]], object, object, object, object, object]:
        calls: list[dict[str, object]] = []

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            calls.append({"method": method, "url": str(url), "kwargs": kwargs})

            if str(url).endswith("/api/auth/email/send-verification"):
                return httpx.Response(202, json={"success": True, "message": "Verification email sent"})

            if str(url).endswith("/api/auth/email/verify"):
                return httpx.Response(
                    200,
                    json={
                        "user": {
                            "id": "u1",
                            "email": "a@example.com",
                            "profile": {"name": "Ada"},
                            "emailVerified": True,
                        },
                        "accessToken": "access",
                        "refreshToken": "refresh",
                    },
                )

            if str(url).endswith("/api/auth/email/send-reset-password"):
                return httpx.Response(202, json={"success": True, "message": "Reset email sent"})

            if str(url).endswith("/api/auth/email/exchange-reset-password-token"):
                return httpx.Response(200, json={"token": "reset-token", "expiresAt": "2026-03-28T12:34:56Z"})

            return httpx.Response(200, json={"message": "Password reset successfully"})

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            send_verification = await client.auth.send_email_verification(
                email="a@example.com",
                redirect_to="https://app.example.com/sign-in",
            )
            verify = await client.auth.verify_email(
                email="a@example.com",
                otp="123456",
            )
            send_reset = await client.auth.send_reset_password_email(
                email="a@example.com",
                redirect_to="https://app.example.com/reset-password",
            )
            exchange = await client.auth.exchange_reset_password_token(
                email="a@example.com",
                code="123456",
            )
            reset = await client.auth.reset_password(
                new_password="new-password",
                token="reset-token",
            )

            return calls, send_verification, verify, send_reset, exchange, reset

    calls, send_verification, verify, send_reset, exchange, reset = asyncio.run(scenario())

    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == "https://example.com/api/auth/email/send-verification"
    assert calls[0]["kwargs"]["json"] == {
        "email": "a@example.com",
        "redirectTo": "https://app.example.com/sign-in",
    }
    assert calls[0]["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert "Authorization" not in calls[0]["kwargs"]["headers"]

    assert calls[1]["method"] == "POST"
    assert calls[1]["url"] == "https://example.com/api/auth/email/verify"
    assert calls[1]["kwargs"]["params"] == {"client_type": "server"}
    assert calls[1]["kwargs"]["json"] == {"email": "a@example.com", "otp": "123456"}
    assert calls[1]["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert "Authorization" not in calls[1]["kwargs"]["headers"]

    assert calls[2]["method"] == "POST"
    assert calls[2]["url"] == "https://example.com/api/auth/email/send-reset-password"
    assert calls[2]["kwargs"]["json"] == {
        "email": "a@example.com",
        "redirectTo": "https://app.example.com/reset-password",
    }
    assert calls[2]["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert "Authorization" not in calls[2]["kwargs"]["headers"]

    assert calls[3]["method"] == "POST"
    assert calls[3]["url"] == "https://example.com/api/auth/email/exchange-reset-password-token"
    assert calls[3]["kwargs"]["json"] == {"email": "a@example.com", "code": "123456"}
    assert calls[3]["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert "Authorization" not in calls[3]["kwargs"]["headers"]

    assert calls[4]["method"] == "POST"
    assert calls[4]["url"] == "https://example.com/api/auth/email/reset-password"
    assert calls[4]["kwargs"]["json"] == {"newPassword": "new-password", "otp": "reset-token"}
    assert calls[4]["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert "Authorization" not in calls[4]["kwargs"]["headers"]

    assert send_verification.success is True
    assert send_verification.message == "Verification email sent"

    assert verify.user.email == "a@example.com"
    assert verify.access_token == "access"
    assert verify.refresh_token == "refresh"

    assert send_reset.success is True
    assert send_reset.message == "Reset email sent"

    assert exchange.token == "reset-token"
    assert exchange.expires_at.isoformat() == "2026-03-28T12:34:56+00:00"

    assert reset.message == "Password reset successfully"


def test_auth_email_json_endpoints_omit_optional_redirect_and_raise_auth_errors() -> None:
    async def scenario() -> tuple[dict[str, object], dict[str, object]]:
        captured_send: dict[str, object] = {}
        captured_verify: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            if str(url).endswith("/api/auth/email/send-verification"):
                captured_send["method"] = method
                captured_send["url"] = str(url)
                captured_send["kwargs"] = kwargs
                return httpx.Response(202, json={"success": True, "message": "Verification email sent"})

            captured_verify["method"] = method
            captured_verify["url"] = str(url)
            captured_verify["kwargs"] = kwargs
            return httpx.Response(401, json={"error": "INVALID_OTP", "message": "Verification code expired"})

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            response = await client.auth.send_email_verification(email="a@example.com")
            assert response.success is True

            try:
                await client.auth.verify_email(email="a@example.com", otp="123456")
            except InsforgeAuthError as exc:
                assert exc.error == "INVALID_OTP"
                assert exc.message == "Verification code expired"
            else:
                raise AssertionError("verify_email should raise InsforgeAuthError on 401")

            return captured_send, captured_verify

    captured_send, captured_verify = asyncio.run(scenario())

    assert captured_send["kwargs"]["json"] == {"email": "a@example.com"}
    assert "Authorization" not in captured_send["kwargs"]["headers"]
    assert captured_verify["kwargs"]["params"] == {"client_type": "server"}


def test_sign_in_with_otp_posts_email_and_returns_generic_payload() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                202,
                json={
                    "success": True,
                    "message": "If sign-in is available for this email, we have sent a verification code.",
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.auth.sign_in_with_otp(email="user@example.com")

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.com/api/auth/email/send-otp"
    assert captured["kwargs"]["json"] == {"email": "user@example.com"}
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert "Authorization" not in captured["kwargs"]["headers"]
    assert result.success is True
    assert result.message == "If sign-in is available for this email, we have sent a verification code."


def test_verify_otp_posts_method_otp_to_sessions_and_returns_session() -> None:
    async def scenario() -> tuple[object, dict[str, object]]:
        captured: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            captured["method"] = method
            captured["url"] = str(url)
            captured["kwargs"] = kwargs
            return httpx.Response(
                200,
                json={
                    "user": {
                        "id": "u1",
                        "email": "user@example.com",
                        "emailVerified": True,
                    },
                    "accessToken": "access",
                    "refreshToken": "refresh",
                },
            )

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            result = await client.auth.verify_otp(
                email="user@example.com",
                otp="123456",
                name="Ada Lovelace",
            )

            return result, captured

    result, captured = asyncio.run(scenario())

    assert captured["method"] == "POST"
    assert captured["url"] == "https://example.com/api/auth/sessions"
    assert captured["kwargs"]["params"] == {"client_type": "server"}
    assert captured["kwargs"]["json"] == {
        "email": "user@example.com",
        "otp": "123456",
        "name": "Ada Lovelace",
        "method": "otp",
    }
    assert captured["kwargs"]["headers"]["X-API-Key"] == "ins_test"
    assert "Authorization" not in captured["kwargs"]["headers"]
    assert result.user.email == "user@example.com"
    assert result.access_token == "access"
    assert result.refresh_token == "refresh"


def test_verify_otp_omits_optional_name_and_raises_auth_error() -> None:
    async def scenario() -> tuple[dict[str, object], dict[str, object]]:
        captured_ok: dict[str, object] = {}
        captured_fail: dict[str, object] = {}

        async def fake_request(method: str, url: httpx.URL, **kwargs: object) -> httpx.Response:
            if not captured_ok:
                captured_ok["method"] = method
                captured_ok["url"] = str(url)
                captured_ok["kwargs"] = kwargs
                return httpx.Response(200, json={"accessToken": "access", "refreshToken": "refresh"})

            captured_fail["method"] = method
            captured_fail["url"] = str(url)
            captured_fail["kwargs"] = kwargs
            return httpx.Response(401, json={"error": "INVALID_OTP", "message": "Verification code expired"})

        async with InsforgeClient(
            base_url="https://example.com",
            api_key="ins_test",
        ) as client:
            client.http_client.request = fake_request  # type: ignore[method-assign]
            await client.auth.verify_otp(email="user@example.com", otp="123456")

            try:
                await client.auth.verify_otp(email="user@example.com", otp="000000")
            except InsforgeAuthError as exc:
                assert exc.error == "INVALID_OTP"
                assert exc.message == "Verification code expired"
            else:
                raise AssertionError("verify_otp should raise InsforgeAuthError on 401")

            return captured_ok, captured_fail

    captured_ok, captured_fail = asyncio.run(scenario())

    assert captured_ok["kwargs"]["json"] == {
        "email": "user@example.com",
        "otp": "123456",
        "method": "otp",
    }
    assert captured_fail["kwargs"]["params"] == {"client_type": "server"}


def test_send_otp_and_verify_otp_reject_empty_fields() -> None:
    with pytest.raises(ValidationError):
        AuthSendOtpRequest(email="")
    with pytest.raises(ValidationError):
        AuthVerifyOtpRequest(email="user@example.com", otp="")


def test_create_user_rejects_empty_email_and_password() -> None:
    with pytest.raises(ValidationError):
        AuthUserCreateRequest(email="", password="secret")
    with pytest.raises(ValidationError):
        AuthUserCreateRequest(email="a@b.com", password="")


def test_config_update_rejects_empty_payload() -> None:
    with pytest.raises(ValidationError):
        AuthConfigUpdateRequest()


def test_config_update_rejects_invalid_verify_method() -> None:
    with pytest.raises(ValidationError):
        AuthConfigUpdateRequest(verify_email_method="sms")  # type: ignore[arg-type]


def test_config_update_rejects_invalid_password_min_length() -> None:
    with pytest.raises(ValidationError):
        AuthConfigUpdateRequest(password_min_length=2)
    with pytest.raises(ValidationError):
        AuthConfigUpdateRequest(password_min_length=200)
