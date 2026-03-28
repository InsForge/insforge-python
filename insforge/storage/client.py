from __future__ import annotations

from collections.abc import Mapping

import httpx

from .._base_client import BaseClient
from ..exceptions import InsforgeHTTPError
from .._utils import quote_path_segment
from .models import StorageBucketListResponse
from .models import StorageDeleteObjectResponse
from .models import StorageObjectResponse


class StorageClient:
    def __init__(self, client: BaseClient) -> None:
        self._client = client

    def _object_url_path(self, bucket_name: str, object_key: str) -> str:
        return (
            "/api/storage/buckets/"
            f"{quote_path_segment(bucket_name)}"
            "/objects/"
            f"{quote_path_segment(object_key, preserve_slashes=True)}"
        )

    async def list_buckets(self, *, access_token: str | None = None) -> StorageBucketListResponse:
        payload = await self._client._request_json(
            "GET",
            "/api/storage/buckets",
            access_token=access_token,
        )
        return StorageBucketListResponse.model_validate(payload)

    async def upload_object(
        self,
        bucket_name: str,
        object_key: str,
        data: bytes,
        *,
        content_type: str | None = None,
        access_token: str | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> StorageObjectResponse:
        path = self._object_url_path(bucket_name, object_key)
        response = await self._client.http_client.request(
            "PUT",
            self._client._build_url(path),
            files={"file": (object_key, data, content_type or "application/octet-stream")},
            headers=self._client._build_headers(
                access_token=access_token,
                extra_headers=extra_headers,
            ),
        )

        if response.is_error:
            raise InsforgeHTTPError.from_response(
                "PUT",
                path,
                response,
            )

        return StorageObjectResponse.model_validate(response.json())

    async def download_object(
        self,
        bucket_name: str,
        object_key: str,
        *,
        access_token: str | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> bytes:
        path = self._object_url_path(bucket_name, object_key)
        response = await self._client.http_client.request(
            "GET",
            self._client._build_url(path),
            headers=self._client._build_headers(
                access_token=access_token,
                extra_headers=extra_headers,
            ),
        )

        if response.is_error:
            raise InsforgeHTTPError.from_response(
                "GET",
                path,
                response,
            )

        return response.content

    async def delete_object(
        self,
        bucket_name: str,
        object_key: str,
        *,
        access_token: str | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> StorageDeleteObjectResponse:
        path = self._object_url_path(bucket_name, object_key)
        payload = await self._client._request_json(
            "DELETE",
            path,
            access_token=access_token,
            extra_headers=extra_headers,
        )
        return StorageDeleteObjectResponse.model_validate(payload)
