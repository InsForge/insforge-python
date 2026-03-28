from __future__ import annotations

from ._base_client import BaseClient
from .auth.client import AuthClient


class InsforgeClient(BaseClient):
    def __init__(self, base_url: str, api_key: str) -> None:
        super().__init__(base_url=base_url, api_key=api_key)
        self.auth = AuthClient(self)
