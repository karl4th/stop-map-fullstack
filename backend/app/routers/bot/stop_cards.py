import asyncio

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.minio import upload_file
from app.repositories.stop_card import StopCardRepository
from app.repositories.stop_card_photo import StopCardPhotoRepository
from app.repositories.user import UserRepository
from app.routers.deps import verify_bot_token
from app.schemas.bot import BotStopCardRequest, ManagerTelegramResponse, SafetyEngineerTelegramResponse
from app.schemas.stop_card import StopCardResponse
from app.services.stop_card import StopCardService

router = APIRouter(tags=["bot-stop-cards"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _service(db: AsyncSession = Depends(get_db)) -> StopCardService:
    return StopCardService(
        StopCardRepository(db),
        StopCardPhotoRepository(db),
        UserRepository(db),
    )


@router.post("/stop-cards", response_model=StopCardResponse, status_code=status.HTTP_201_CREATED)
async def create_stop_card(
    body: BotStopCardRequest,
    svc: StopCardService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    reporter = await svc.user_repo.get_by_telegram_id(body.reporter_telegram_id)
    if reporter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    if reporter.status.value != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь не активирован")

    return await svc.create(
        reporter_id=reporter.id,
        violator_name=body.violator_name,
        section_id=body.section_id,
        description=body.description,
        minio_keys=[],
    )


@router.post("/stop-cards/{stop_card_id}/photos", response_model=StopCardResponse)
async def upload_photos(
    stop_card_id: int,
    photos: list[UploadFile] = File(...),
    svc: StopCardService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    try:
        await svc.get_by_id(stop_card_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    for photo in photos:
        if photo.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неподдерживаемый тип файла: {photo.content_type}",
            )

    async def _read_and_upload(photo: UploadFile) -> str:
        ext = photo.content_type.split("/")[-1]
        data = await photo.read()
        return await upload_file(data, photo.content_type, ext)

    keys = await asyncio.gather(*[_read_and_upload(p) for p in photos])
    await svc.photo_repo.create_many(stop_card_id, list(keys), photo_type="before")
    return await svc.get_by_id(stop_card_id)


@router.get("/stop-cards/my/{telegram_id}", response_model=list[StopCardResponse])
async def my_stop_cards(
    telegram_id: int,
    svc: StopCardService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    reporter = await svc.user_repo.get_by_telegram_id(telegram_id)
    if reporter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return await svc.get_by_reporter(reporter.id)


@router.get("/sections/{section_id}/managers", response_model=list[ManagerTelegramResponse])
async def get_managers(
    section_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_bot_token),
):
    managers = await UserRepository(db).get_managers_by_section(section_id)
    return [m for m in managers if m.telegram_id is not None]


@router.get("/safety-engineers", response_model=list[SafetyEngineerTelegramResponse])
async def get_safety_engineers(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_bot_token),
):
    engineers = await UserRepository(db).get_safety_engineers()
    return [e for e in engineers if e.telegram_id is not None]
