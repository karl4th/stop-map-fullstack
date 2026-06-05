import asyncio

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.minio import upload_file
from app.models.user import User
from app.repositories.stop_card import StopCardRepository
from app.repositories.stop_card_photo import StopCardPhotoRepository
from app.repositories.user import UserRepository
from app.routers.deps import require_manager_or_admin
from app.schemas.stop_card import StopCardResponse
from app.services.stop_card import StopCardService

router = APIRouter(prefix="/stop-cards", tags=["manager-stop-cards"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _service(db: AsyncSession = Depends(get_db)) -> StopCardService:
    return StopCardService(
        StopCardRepository(db),
        StopCardPhotoRepository(db),
        UserRepository(db),
    )


def _assert_section(card, current_user: User) -> None:
    if current_user.role.value != "admin" and card.section_id != current_user.section_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этой стоп-карте")


@router.get("", response_model=list[StopCardResponse])
async def list_stop_cards(
    svc: StopCardService = Depends(_service),
    current_user: User = Depends(require_manager_or_admin),
):
    if current_user.role.value == "admin":
        return await svc.repo.get_all()
    return await svc.get_by_section(current_user.section_id)


@router.get("/{stop_card_id}", response_model=StopCardResponse)
async def get_stop_card(
    stop_card_id: int,
    svc: StopCardService = Depends(_service),
    current_user: User = Depends(require_manager_or_admin),
):
    try:
        card = await svc.get_by_id(stop_card_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    _assert_section(card, current_user)
    return card


@router.patch("/{stop_card_id}/acknowledge", response_model=StopCardResponse)
async def acknowledge(
    stop_card_id: int,
    svc: StopCardService = Depends(_service),
    current_user: User = Depends(require_manager_or_admin),
):
    try:
        card = await svc.get_by_id(stop_card_id)
        _assert_section(card, current_user)
        return await svc.acknowledge(stop_card_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{stop_card_id}/fix", response_model=StopCardResponse)
async def submit_fix(
    stop_card_id: int,
    fix_description: str = Form(...),
    photos: list[UploadFile] = File(default=[]),
    svc: StopCardService = Depends(_service),
    current_user: User = Depends(require_manager_or_admin),
):
    try:
        card = await svc.get_by_id(stop_card_id)
        _assert_section(card, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    for photo in photos:
        if photo.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неподдерживаемый формат: {photo.content_type}",
            )

    async def _upload(photo: UploadFile) -> str:
        ext = photo.content_type.split("/")[-1]
        data = await photo.read()
        return await upload_file(data, photo.content_type, ext)

    after_keys = list(await asyncio.gather(*[_upload(p) for p in photos])) if photos else []

    try:
        return await svc.submit_fix(stop_card_id, current_user.id, fix_description, after_keys)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
