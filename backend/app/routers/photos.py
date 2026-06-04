from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app.core.minio import get_file
from app.models.user import User
from app.routers.deps import get_current_user

router = APIRouter(prefix="/photos", tags=["photos"])


@router.get("/{key:path}")
async def proxy_photo(
    key: str,
    _: User = Depends(get_current_user),
):
    try:
        data, content_type = await get_file(key)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фото не найдено")
    return Response(content=data, media_type=content_type)
