from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class SendRawEmailRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    to: str | list[str]
    subject: str
    html: str
    cc: str | list[str] | None = None
    bcc: str | list[str] | None = None
    from_: str | None = Field(default=None, alias="from")
    reply_to: str | None = Field(default=None, alias="replyTo")
