from __future__ import annotations

from datetime import datetime
from typing import Any
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SignInResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    access_token: str = Field(alias="accessToken")
    refresh_token: str = Field(alias="refreshToken")


class AuthEmailActionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    success: bool | None = None
    message: str | None = None


class AuthEmailVerificationRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    email: str = Field(min_length=1)
    redirect_to: str | None = Field(default=None, alias="redirectTo")


class AuthEmailVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    email: str = Field(min_length=1)
    otp: str = Field(min_length=1)


class AuthResetPasswordExchangeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    email: str = Field(min_length=1)
    code: str = Field(min_length=1)


class AuthResetPasswordExchangeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    token: str | None = None
    expires_at: datetime | None = Field(default=None, alias="expiresAt")


class AuthResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    new_password: str = Field(min_length=1, alias="newPassword")
    token: str = Field(min_length=1, alias="otp")


class CurrentProfileResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    user_id: str = Field(alias="userId")
    profile: dict[str, Any]


class PublicAuthConfigResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    o_auth_providers: list[str] = Field(default_factory=list, alias="oAuthProviders")
    custom_o_auth_providers: list[str] = Field(default_factory=list, alias="customOAuthProviders")
    require_email_verification: bool | None = Field(default=None, alias="requireEmailVerification")
    password_min_length: int | None = Field(default=None, ge=4, le=128, alias="passwordMinLength")
    require_number: bool | None = Field(default=None, alias="requireNumber")
    require_lowercase: bool | None = Field(default=None, alias="requireLowercase")
    require_uppercase: bool | None = Field(default=None, alias="requireUppercase")
    require_special_char: bool | None = Field(default=None, alias="requireSpecialChar")
    verify_email_method: Literal["code", "link"] | None = Field(default=None, alias="verifyEmailMethod")
    reset_password_method: Literal["code", "link"] | None = Field(default=None, alias="resetPasswordMethod")


class ProfileResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str
    profile: dict[str, Any] | None = None


class AuthConfigResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str | None = None
    require_email_verification: bool | None = Field(default=None, alias="requireEmailVerification")
    password_min_length: int | None = Field(default=None, ge=4, le=128, alias="passwordMinLength")
    require_number: bool | None = Field(default=None, alias="requireNumber")
    require_lowercase: bool | None = Field(default=None, alias="requireLowercase")
    require_uppercase: bool | None = Field(default=None, alias="requireUppercase")
    require_special_char: bool | None = Field(default=None, alias="requireSpecialChar")
    verify_email_method: Literal["code", "link"] | None = Field(default=None, alias="verifyEmailMethod")
    reset_password_method: Literal["code", "link"] | None = Field(default=None, alias="resetPasswordMethod")
    allowed_redirect_urls: list[str] = Field(default_factory=list, alias="allowedRedirectUrls")
    created_at: datetime | None = Field(default=None, alias="createdAt")
    updated_at: datetime | None = Field(default=None, alias="updatedAt")


class AuthConfigUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    require_email_verification: bool | None = Field(default=None, alias="requireEmailVerification")
    password_min_length: int | None = Field(default=None, ge=4, le=128, alias="passwordMinLength")
    require_number: bool | None = Field(default=None, alias="requireNumber")
    require_lowercase: bool | None = Field(default=None, alias="requireLowercase")
    require_uppercase: bool | None = Field(default=None, alias="requireUppercase")
    require_special_char: bool | None = Field(default=None, alias="requireSpecialChar")
    verify_email_method: Literal["code", "link"] | None = Field(default=None, alias="verifyEmailMethod")
    reset_password_method: Literal["code", "link"] | None = Field(default=None, alias="resetPasswordMethod")
    allowed_redirect_urls: list[str] | None = Field(default=None, alias="allowedRedirectUrls")

    @model_validator(mode="before")
    def require_field(cls, values):
        fields = (
            "requireEmailVerification", "require_email_verification",
            "passwordMinLength", "password_min_length",
            "requireNumber", "require_number",
            "requireLowercase", "require_lowercase",
            "requireUppercase", "require_uppercase",
            "requireSpecialChar", "require_special_char",
            "verifyEmailMethod", "verify_email_method",
            "resetPasswordMethod", "reset_password_method",
            "allowedRedirectUrls", "allowed_redirect_urls",
        )
        if not any(values.get(f) is not None for f in fields):
            raise ValueError("update_config requires at least one field")
        return values


class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str | None = None
    email: str | None = None
    profile: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    email_verified: bool | None = Field(default=None, alias="emailVerified")
    providers: list[str] | None = None
    created_at: datetime | None = Field(default=None, alias="createdAt")
    updated_at: datetime | None = Field(default=None, alias="updatedAt")


class AuthUserCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    email: str = Field(min_length=1)
    password: str = Field(min_length=1)
    name: str | None = None
    redirect_to: str | None = Field(default=None, alias="redirectTo")


class AuthPagination(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    offset: int | None = None
    limit: int | None = None
    total: int | None = None


class AuthUsersResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    data: list[UserResponse] = Field(default_factory=list)
    pagination: AuthPagination | None = None


class AuthDeleteUsersRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    user_ids: list[str] = Field(min_length=1, alias="userIds")


class AuthDeleteUsersResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    message: str | None = None
    deleted_count: int | None = Field(default=None, alias="deletedCount")


class AuthCurrentSessionUser(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str | None = None
    email: str | None = None
    role: str | None = None


class AuthCurrentSessionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    user: AuthCurrentSessionUser


class AuthSessionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    user: UserResponse | None = None
    access_token: str | None = Field(default=None, alias="accessToken")
    csrf_token: str | None = Field(default=None, alias="csrfToken")
    refresh_token: str | None = Field(default=None, alias="refreshToken")
    require_email_verification: bool | None = Field(default=None, alias="requireEmailVerification")


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    refresh_token: str = Field(min_length=1, alias="refreshToken")


class AdminSessionExchangeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    code: str = Field(min_length=1)


class LogoutResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    success: bool | None = None
    message: str | None = None


class AnonymousTokenResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    access_token: str | None = Field(default=None, alias="accessToken")
    message: str | None = None
