import asyncio

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.minio import get_file as minio_get_file, upload_file
from app.models.user import UserRole
from app.repositories.stop_card import StopCardRepository
from app.repositories.stop_card_photo import StopCardPhotoRepository
from app.repositories.user import UserRepository
from app.routers.deps import verify_bot_token
from app.schemas.bot import (
    BotEngineerDecisionRequest,
    BotManagerActionRequest,
    BotStopCardRequest,
    ManagerTelegramResponse,
    SafetyEngineerTelegramResponse,
)
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


# ── Создать стоп-карту ────────────────────────────────────────────────────────

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


# ── Загрузить фото к стоп-карте (фото ДО от работника) ───────────────────────

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


# ── Менеджер: принять стоп-карту ─────────────────────────────────────────────

@router.patch("/stop-cards/{stop_card_id}/bot-acknowledge", response_model=StopCardResponse)
async def bot_acknowledge(
    stop_card_id: int,
    body: BotManagerActionRequest,
    svc: StopCardService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    manager = await svc.user_repo.get_by_telegram_id(body.telegram_id)
    if manager is None or manager.role not in (UserRole.manager, UserRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")
    try:
        return await svc.acknowledge(stop_card_id, manager.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ── Менеджер: загрузить устранение (фото ПОСЛЕ + описание) ───────────────────

@router.post("/stop-cards/{stop_card_id}/bot-fix", response_model=StopCardResponse)
async def bot_fix(
    stop_card_id: int,
    telegram_id: int = Form(...),
    fix_description: str = Form(...),
    photos: list[UploadFile] = File(default=[]),
    svc: StopCardService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    manager = await svc.user_repo.get_by_telegram_id(telegram_id)
    if manager is None or manager.role not in (UserRole.manager, UserRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")

    for photo in photos:
        if photo.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неподдерживаемый тип файла: {photo.content_type}",
            )

    async def _upload(p: UploadFile) -> str:
        ext = p.content_type.split("/")[-1]
        data = await p.read()
        return await upload_file(data, p.content_type, ext)

    after_keys = list(await asyncio.gather(*[_upload(p) for p in photos])) if photos else []

    try:
        return await svc.submit_fix(stop_card_id, manager.id, fix_description, after_keys)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ── Инженер ОТ и ТБ: решение ─────────────────────────────────────────────────

@router.patch("/stop-cards/{stop_card_id}/bot-engineer", response_model=StopCardResponse)
async def bot_engineer_decision(
    stop_card_id: int,
    body: BotEngineerDecisionRequest,
    svc: StopCardService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    engineer = await svc.user_repo.get_by_telegram_id(body.telegram_id)
    if engineer is None or engineer.role not in (UserRole.safety_engineer, UserRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")
    try:
        if body.action == "approve":
            return await svc.safety_approve(stop_card_id, engineer.id, body.note)
        elif body.action == "reject":
            return await svc.safety_reject(stop_card_id, engineer.id, body.note)
        elif body.action == "revision":
            return await svc.safety_revision(stop_card_id, engineer.id, body.note)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неизвестное действие")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ── Вспомогательные ──────────────────────────────────────────────────────────

@router.get("/stop-cards/{stop_card_id}", response_model=StopCardResponse)
async def get_stop_card(
    stop_card_id: int,
    svc: StopCardService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    try:
        return await svc.get_by_id(stop_card_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


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


@router.get("/stop-cards/for-manager/{telegram_id}", response_model=list[StopCardResponse])
async def cards_for_manager(
    telegram_id: int,
    svc: StopCardService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    manager = await svc.user_repo.get_by_telegram_id(telegram_id)
    if manager is None or manager.role not in (UserRole.manager, UserRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")
    all_cards = await svc.repo.get_all()
    return [
        c for c in all_cards
        if c.section_id == manager.section_id
        and c.status.value in ("created", "under_review", "in_progress", "safety_check")
    ]


@router.get("/stop-cards/for-engineer", response_model=list[StopCardResponse])
async def cards_for_engineer(
    telegram_id: int,
    svc: StopCardService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    engineer = await svc.user_repo.get_by_telegram_id(telegram_id)
    if engineer is None or engineer.role not in (UserRole.safety_engineer, UserRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")
    return await svc.get_for_safety_check()


@router.get("/photos/{minio_key:path}")
async def get_photo(
    minio_key: str,
    _: None = Depends(verify_bot_token),
):
    try:
        data, content_type = await minio_get_file(minio_key)
        return Response(content=data, media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


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
