from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.minio import get_file
from app.models.user import User, UserRole
from app.repositories.stop_card import StopCardRepository
from app.routers.deps import get_current_user

router = APIRouter(prefix="/photos", tags=["photos"])


@router.get("/{key:path}")
async def proxy_photo(
    key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    card = await StopCardRepository(db).get_by_photo_key(key)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фото не найдено")
    can_access = (
        current_user.role in (UserRole.admin, UserRole.safety_engineer)
        or card.reporter_id == current_user.id
        or card.violator_id == current_user.id
        or (
            current_user.role == UserRole.manager
            and current_user.section_id == card.section_id
        )
    )
    if not can_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к фото")
    try:
        data, content_type = await get_file(key)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фото не найдено")
    return Response(content=data, media_type=content_type)
