from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from typing import Iterable

import httpx

from .._base_client import BaseClient
from ..exceptions import InsforgeHTTPError
from .._utils import quote_path_segment
from .models import DownloadStrategy
from .models import StorageBucketListResponse
from .models import StorageBucketResponse
from .models import StorageBucketUpdateResponse
from .models import StorageDeleteBucketResponse
from .models import StorageDeleteObjectResponse
from .models import StorageDownloadResult
from .models import StorageObjectResponse
from .models import StoredFileList
from .models import UploadStrategy


class StorageClient:
    def __init__(self, client: BaseClient) -> None:
        self._client = client

    def _bucket_path(self, bucket_name: str) -> str:
        return f"/api/storage/buckets/{quote_path_segment(bucket_name)}"

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

    async def create_bucket(
        self,
        *,
        bucket_name: str,
        is_public: bool | None = None,
        access_token: str | None = None,
    ) -> StorageBucketResponse:
        payload: dict[str, Any] = {"bucketName": bucket_name}
        if is_public is not None:
            payload["isPublic"] = is_public

        response = await self._client._request_json(
            "POST",
            "/api/storage/buckets",
            json=payload,
            access_token=access_token,
        )
        return StorageBucketResponse.model_validate(response)

    async def update_bucket(
        self,
        bucket_name: str,
        *,
        is_public: bool,
        access_token: str | None = None,
    ) -> StorageBucketUpdateResponse:
        response = await self._client._request_json(
            "PATCH",
            self._bucket_path(bucket_name),
            json={"isPublic": is_public},
            access_token=access_token,
        )
        return StorageBucketUpdateResponse.model_validate(response)

    async def delete_bucket(
        self,
        bucket_name: str,
        *,
        access_token: str | None = None,
    ) -> StorageDeleteBucketResponse:
        response = await self._client._request_json(
            "DELETE",
            self._bucket_path(bucket_name),
            access_token=access_token,
        )
        return StorageDeleteBucketResponse.model_validate(response)

    async def list_objects(
        self,
        bucket_name: str,
        *,
        prefix: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        search: str | None = None,
        access_token: str | None = None,
    ) -> StoredFileList:
        params: dict[str, str] = {}
        if prefix is not None:
            params["prefix"] = prefix
        if limit is not None:
            params["limit"] = str(limit)
        if offset is not None:
            params["offset"] = str(offset)
        if search is not None:
            params["search"] = search

        payload = await self._client._request_json(
            "GET",
            f"/api/storage/buckets/{quote_path_segment(bucket_name)}/objects",
            params=params or None,
            access_token=access_token,
        )
        return StoredFileList.model_validate(payload)

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
    ) -> StorageDownloadResult:
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

        headers = response.headers
        content_type = (headers.get("Content-Type") or headers.get("content-type"))
        content_length = (
            headers.get("Content-Length")
            or headers.get("content-length")
            or str(len(response.content))
        )
        return StorageDownloadResult(
            content=response.content,
            content_type=content_type,
            content_length=content_length,
        )

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

    async def upload_object_auto(
        self,
        bucket_name: str,
        *,
        data: bytes,
        filename: str,
        content_type: str | None = None,
        access_token: str | None = None,
    ) -> StorageObjectResponse:
        path = f"/api/storage/buckets/{quote_path_segment(bucket_name)}/objects"
        response = await self._client.http_client.request(
            "POST",
            self._client._build_url(path),
            files={"file": (filename, data, content_type or "application/octet-stream")},
            headers=self._client._build_headers(access_token=access_token),
        )

        if response.is_error:
            raise InsforgeHTTPError.from_response("POST", path, response)

        return StorageObjectResponse.model_validate(response.json())

    async def confirm_upload(
        self,
        bucket_name: str,
        object_key: str,
        *,
        size: int,
        content_type: str | None = None,
        etag: str | None = None,
        access_token: str | None = None,
    ) -> StorageObjectResponse:
        payload: dict[str, Any] = {"size": size}
        if content_type is not None:
            payload["contentType"] = content_type
        if etag is not None:
            payload["etag"] = etag

        response = await self._client._request_json(
            "POST",
            f"{self._object_url_path(bucket_name, object_key)}/confirm-upload",
            json=payload,
            access_token=access_token,
        )
        return StorageObjectResponse.model_validate(response)

    async def get_upload_strategy(
        self,
        bucket_name: str,
        *,
        filename: str,
        content_type: str | None = None,
        size: int | None = None,
        access_token: str | None = None,
    ) -> UploadStrategy:
        payload: dict[str, Any] = {"filename": filename}
        if content_type is not None:
            payload["contentType"] = content_type
        if size is not None:
            payload["size"] = size

        response = await self._client._request_json(
            "POST",
            f"/api/storage/buckets/{quote_path_segment(bucket_name)}/upload-strategy",
            json=payload,
            access_token=access_token,
        )
        return UploadStrategy.model_validate(response)

    async def get_download_strategy(
        self,
        bucket_name: str,
        object_key: str,
        *,
        expires_in: int | None = None,
        access_token: str | None = None,
    ) -> DownloadStrategy:
        payload: dict[str, Any] = {}
        if expires_in is not None:
            payload["expiresIn"] = expires_in

        response = await self._client._request_json(
            "POST",
            f"{self._object_url_path(bucket_name, object_key)}/download-strategy",
            json=payload or None,
            access_token=access_token,
        )
        return DownloadStrategy.model_validate(response)
