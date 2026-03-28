from __future__ import annotations

from dataclasses import dataclass

import httpx


class InsforgeError(Exception):
    """Base error for the Insforge SDK."""


@dataclass(slots=True)
class _HTTPErrorPayload:
    error: str
    message: str
    next_action: str | None
    raw_payload: object | None


class InsforgeHTTPError(InsforgeError):
    def __init__(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        error: str,
        message: str,
        next_action: str | None = None,
        raw_payload: object | None = None,
    ) -> None:
        self.method = method
        self.path = path
        self.status_code = status_code
        self.error = error
        self.message = message
        self.next_action = next_action
        self.raw_payload = raw_payload
        super().__init__(str(self))

    def __str__(self) -> str:
        return f"{self.method} {self.path} failed with {self.status_code}: {self.error} - {self.message}"

    @classmethod
    def from_response(
        cls,
        method: str,
        path: str,
        response: httpx.Response,
    ) -> "InsforgeHTTPError":
        payload = cls._parse_payload(response)
        return cls(
            method=method,
            path=path,
            status_code=response.status_code,
            error=payload.error,
            message=payload.message,
            next_action=payload.next_action,
            raw_payload=payload.raw_payload,
        )

    @staticmethod
    def _parse_payload(response: httpx.Response) -> _HTTPErrorPayload:
        try:
            payload = response.json()
        except ValueError:
            return _HTTPErrorPayload(
                error="UNKNOWN_ERROR",
                message=response.text or f"HTTP {response.status_code}",
                next_action=None,
                raw_payload=response.text,
            )

        if not isinstance(payload, dict):
            return _HTTPErrorPayload(
                error="UNKNOWN_ERROR",
                message=f"HTTP {response.status_code}",
                next_action=None,
                raw_payload=payload,
            )

        return _HTTPErrorPayload(
            error=str(payload.get("error", "UNKNOWN_ERROR")),
            message=str(payload.get("message", f"HTTP {response.status_code}")),
            next_action=payload.get("nextAction") or payload.get("nextActions"),
            raw_payload=payload,
        )


class InsforgeAuthError(InsforgeHTTPError):
    pass


class InsforgeValidationError(InsforgeError):
    pass


class InsforgeSerializationError(InsforgeError):
    pass
