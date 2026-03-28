from __future__ import annotations

from .._base_client import BaseClient
from .models import SendRawEmailRequest


class EmailClient:
    def __init__(self, client: BaseClient) -> None:
        self._client = client

    async def send_raw(
        self,
        *,
        to: str | list[str],
        subject: str,
        html: str,
        access_token: str | None = None,
        cc: str | list[str] | None = None,
        bcc: str | list[str] | None = None,
        from_: str | None = None,
        reply_to: str | None = None,
    ) -> dict[str, object]:
        payload = SendRawEmailRequest(
            to=to,
            subject=subject,
            html=html,
            cc=cc,
            bcc=bcc,
            from_=from_,
            reply_to=reply_to,
        ).model_dump(by_alias=True, exclude_none=True)
        result = await self._client._request_json(
            "POST",
            "/api/email/send-raw",
            json=payload,
            access_token=access_token,
        )
        return result  # runtime response is an empty/small JSON object
