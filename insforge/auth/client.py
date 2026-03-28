from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._base_client import BaseClient
from ..exceptions import InsforgeAuthError
from .models import CurrentProfileResponse, SignInResponse


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
            "/api/auth/sessions?client_type=server",
            json={"email": email, "password": password},
            exception_cls=InsforgeAuthError,
        )
        return SignInResponse.model_validate(payload)

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
