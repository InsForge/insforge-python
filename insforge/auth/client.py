from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._base_client import BaseClient
from .._utils import quote_path_segment
from ..exceptions import InsforgeAuthError
from .models import AdminSessionExchangeRequest
from .models import AnonymousTokenResponse
from .models import AuthConfigResponse
from .models import AuthConfigUpdateRequest
from .models import AuthCurrentSessionResponse
from .models import AuthDeleteUsersRequest
from .models import AuthDeleteUsersResponse
from .models import AuthSessionResponse
from .models import AuthUserCreateRequest
from .models import AuthUsersResponse
from .models import CurrentProfileResponse
from .models import LogoutResponse
from .models import ProfileResponse
from .models import PublicAuthConfigResponse
from .models import RefreshRequest
from .models import SignInResponse
from .models import UserResponse


SERVER_CLIENT_TYPE_PARAMS = {"client_type": "server"}


class AuthClient:
    def __init__(self, client: BaseClient) -> None:
        self._client = client

    async def sign_in_with_password(
        self,
        *,
        email: str,
        password: str,
    ) -> SignInResponse:
        payload = await self._client._request_json(
            "POST",
            "/api/auth/sessions",
            params=SERVER_CLIENT_TYPE_PARAMS,
            json={"email": email, "password": password},
            exception_cls=InsforgeAuthError,
        )
        return SignInResponse.model_validate(payload)

    async def get_public_config(self) -> PublicAuthConfigResponse:
        payload = await self._client._request_json("GET", "/api/auth/public-config")
        return PublicAuthConfigResponse.model_validate(payload)

    async def get_profile(self, user_id: str) -> ProfileResponse:
        payload = await self._client._request_json(
            "GET",
            f"/api/auth/profiles/{quote_path_segment(user_id)}",
        )
        return ProfileResponse.model_validate(payload)

    async def get_config(
        self,
        *,
        access_token: str | None = None,
    ) -> AuthConfigResponse:
        payload = await self._client._request_json(
            "GET",
            "/api/auth/config",
            access_token=access_token,
        )
        return AuthConfigResponse.model_validate(payload)

    async def update_config(
        self,
        config: Mapping[str, Any],
        *,
        access_token: str | None = None,
    ) -> AuthConfigResponse:
        payload = AuthConfigUpdateRequest.model_validate(config).model_dump(
            by_alias=True,
            exclude_none=True,
        )
        response = await self._client._request_json(
            "PUT",
            "/api/auth/config",
            json=payload,
            access_token=access_token,
            exception_cls=InsforgeAuthError,
        )
        return AuthConfigResponse.model_validate(response)

    async def list_users(
        self,
        *,
        offset: int | str | None = None,
        limit: int | str | None = None,
        search: str | None = None,
        access_token: str | None = None,
    ) -> AuthUsersResponse:
        params: dict[str, str] = {}
        if offset is not None:
            params["offset"] = str(offset)
        if limit is not None:
            params["limit"] = str(limit)
        if search is not None:
            params["search"] = search

        payload = await self._client._request_json(
            "GET",
            "/api/auth/users",
            params=params or None,
            access_token=access_token,
        )
        return AuthUsersResponse.model_validate(payload)

    async def create_user(
        self,
        *,
        email: str,
        password: str,
        name: str | None = None,
        redirect_to: str | None = None,
    ) -> AuthSessionResponse:
        payload = AuthUserCreateRequest(
            email=email,
            password=password,
            name=name,
            redirect_to=redirect_to,
        ).model_dump(by_alias=True, exclude_none=True)
        response = await self._client._request_json(
            "POST",
            "/api/auth/users",
            params=SERVER_CLIENT_TYPE_PARAMS,
            json=payload,
            exception_cls=InsforgeAuthError,
        )
        return AuthSessionResponse.model_validate(response)

    async def delete_users(
        self,
        user_ids: list[str],
        *,
        access_token: str | None = None,
    ) -> AuthDeleteUsersResponse:
        payload = AuthDeleteUsersRequest(user_ids=user_ids).model_dump(by_alias=True)
        response = await self._client._request_json(
            "DELETE",
            "/api/auth/users",
            json=payload,
            access_token=access_token,
        )
        return AuthDeleteUsersResponse.model_validate(response)

    async def get_user(
        self,
        user_id: str,
        *,
        access_token: str | None = None,
    ) -> UserResponse:
        payload = await self._client._request_json(
            "GET",
            f"/api/auth/users/{quote_path_segment(user_id)}",
            access_token=access_token,
        )
        return UserResponse.model_validate(payload)

    async def refresh(
        self,
        *,
        refresh_token: str,
    ) -> AuthSessionResponse:
        payload = await self._client._request_json(
            "POST",
            "/api/auth/refresh",
            params=SERVER_CLIENT_TYPE_PARAMS,
            json=RefreshRequest(refresh_token=refresh_token).model_dump(by_alias=True),
            exception_cls=InsforgeAuthError,
        )
        return AuthSessionResponse.model_validate(payload)

    async def logout(self) -> LogoutResponse:
        payload = await self._client._request_json("POST", "/api/auth/logout")
        return LogoutResponse.model_validate(payload)

    async def get_current_session(
        self,
        *,
        access_token: str | None = None,
    ) -> AuthCurrentSessionResponse:
        payload = await self._client._request_json(
            "GET",
            "/api/auth/sessions/current",
            access_token=access_token,
        )
        return AuthCurrentSessionResponse.model_validate(payload)

    async def admin_sign_in(
        self,
        *,
        email: str,
        password: str,
    ) -> AuthSessionResponse:
        payload = await self._client._request_json(
            "POST",
            "/api/auth/admin/sessions",
            json={"email": email, "password": password},
            exception_cls=InsforgeAuthError,
        )
        return AuthSessionResponse.model_validate(payload)

    async def exchange_admin_session(
        self,
        *,
        code: str,
    ) -> AuthSessionResponse:
        payload = await self._client._request_json(
            "POST",
            "/api/auth/admin/sessions/exchange",
            json=AdminSessionExchangeRequest(code=code).model_dump(by_alias=True),
            exception_cls=InsforgeAuthError,
        )
        return AuthSessionResponse.model_validate(payload)

    async def create_anon_token(
        self,
        *,
        access_token: str | None = None,
    ) -> AnonymousTokenResponse:
        payload = await self._client._request_json(
            "POST",
            "/api/auth/tokens/anon",
            access_token=access_token,
        )
        return AnonymousTokenResponse.model_validate(payload)

    async def update_current_profile(
        self,
        profile: Mapping[str, Any],
        *,
        access_token: str,
    ) -> CurrentProfileResponse:
        payload = await self._client._request_json(
            "PATCH",
            "/api/auth/profiles/current",
            json={"profile": dict(profile)},
            access_token=access_token,
            exception_cls=InsforgeAuthError,
        )
        return CurrentProfileResponse.model_validate(payload)
