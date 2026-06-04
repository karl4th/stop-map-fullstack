import asyncio
import io
import uuid
from functools import partial

from minio import Minio

from app.core.config import settings

_client: Minio | None = None


def get_minio() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
    return _client


def ensure_bucket() -> None:
    client = get_minio()
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)


async def upload_file(data: bytes, content_type: str, ext: str) -> str:
    key = f"stop-cards/{uuid.uuid4()}.{ext}"
    client = get_minio()
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        partial(
            client.put_object,
            settings.MINIO_BUCKET,
            key,
            io.BytesIO(data),
            len(data),
            content_type=content_type,
        ),
    )
    return key


async def get_file(key: str) -> tuple[bytes, str]:
    client = get_minio()
    loop = asyncio.get_running_loop()

    def _download():
        response = client.get_object(settings.MINIO_BUCKET, key)
        data = response.read()
        content_type = response.headers.get("content-type", "image/jpeg")
        response.close()
        response.release_conn()
        return data, content_type

    return await loop.run_in_executor(None, _download)
