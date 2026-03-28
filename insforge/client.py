from __future__ import annotations

from ._base_client import BaseClient
from .auth.client import AuthClient
from .ai.client import AIClient
from .database.client import DatabaseClient
from .email.client import EmailClient
from .functions.client import FunctionsClient
from .metadata.client import MetadataClient
from .storage.client import StorageClient


class InsforgeClient(BaseClient):
    def __init__(self, base_url: str, api_key: str) -> None:
        super().__init__(base_url=base_url, api_key=api_key)
        self.ai = AIClient(self)
        self.auth = AuthClient(self)
        self.database = DatabaseClient(self)
        self.email = EmailClient(self)
        self.functions = FunctionsClient(self)
        self.metadata = MetadataClient(self)
        self.storage = StorageClient(self)
