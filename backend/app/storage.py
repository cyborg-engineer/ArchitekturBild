from __future__ import annotations

import io
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from minio import Minio
from minio.error import MinioException, S3Error


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _guess_extension(content_type: str, filename: str | None) -> str:
    if filename and "." in filename:
        suffix = filename.rsplit(".", 1)[-1].strip().lower()
        if suffix:
            return suffix
    mapping = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
        "image/bmp": "bmp",
    }
    return mapping.get(content_type, "bin")


class MinioStorageError(RuntimeError):
    pass


@dataclass
class StoredObject:
    bucket: str
    object_key: str


class MinioStorage:
    def __init__(
        self,
        endpoint: str,
        public_endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool,
        public_secure: bool,
        presigned_expires_seconds: int,
        region: str | None = None,
    ) -> None:
        self.bucket = bucket
        self.presigned_expires_seconds = max(60, min(presigned_expires_seconds, 86_400))
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region,
        )
        self.presign_client = Minio(
            endpoint=public_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=public_secure,
            region=region,
        )
        self._ensure_bucket()

    @classmethod
    def from_env(cls) -> "MinioStorage":
        endpoint = os.getenv("MINIO_ENDPOINT", "").strip()
        public_endpoint = os.getenv("MINIO_PUBLIC_ENDPOINT", "").strip() or endpoint
        access_key = os.getenv("MINIO_ACCESS_KEY", "").strip()
        secret_key = os.getenv("MINIO_SECRET_KEY", "").strip()
        bucket = os.getenv("MINIO_BUCKET", "").strip()
        secure = _as_bool(os.getenv("MINIO_SECURE"), default=False)
        public_secure = _as_bool(os.getenv("MINIO_PUBLIC_SECURE"), default=secure)
        region = os.getenv("MINIO_REGION", "").strip() or None
        expires = int(os.getenv("MINIO_PRESIGNED_EXPIRES_SECONDS", "900"))

        missing = [
            key
            for key, value in {
                "MINIO_ENDPOINT": endpoint,
                "MINIO_ACCESS_KEY": access_key,
                "MINIO_SECRET_KEY": secret_key,
                "MINIO_BUCKET": bucket,
            }.items()
            if not value
        ]
        if missing:
            raise MinioStorageError(f"Missing MinIO configuration: {', '.join(missing)}")

        try:
            return cls(
                endpoint=endpoint,
                public_endpoint=public_endpoint,
                access_key=access_key,
                secret_key=secret_key,
                bucket=bucket,
                secure=secure,
                public_secure=public_secure,
                presigned_expires_seconds=expires,
                region=region,
            )
        except Exception as exc:
            raise MinioStorageError(f"Failed to initialize MinIO: {exc}") from exc

    def _ensure_bucket(self) -> None:
        if self.client.bucket_exists(self.bucket):
            return
        self.client.make_bucket(self.bucket)

    def store_image(
        self,
        image_bytes: bytes,
        content_type: str,
        image_sha256: str,
        filename: str | None,
    ) -> StoredObject:
        extension = _guess_extension(content_type, filename)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        object_key = f"images/{timestamp}-{image_sha256[:16]}.{extension}"
        stream = io.BytesIO(image_bytes)

        try:
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=object_key,
                data=stream,
                length=len(image_bytes),
                content_type=content_type,
            )
        except (MinioException, S3Error) as exc:
            raise MinioStorageError(f"Failed to upload image to MinIO: {exc}") from exc

        return StoredObject(bucket=self.bucket, object_key=object_key)

    def presigned_url(self, bucket: str, object_key: str) -> str:
        try:
            return self.presign_client.presigned_get_object(
                bucket_name=bucket,
                object_name=object_key,
                expires=timedelta(seconds=self.presigned_expires_seconds),
            )
        except (MinioException, S3Error) as exc:
            raise MinioStorageError(f"Failed to create MinIO presigned URL: {exc}") from exc
