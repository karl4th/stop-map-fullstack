import asyncio

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.minio import get_file as minio_get_file, upload_file
from app.core.telegram import notify
from app.models.stop_card import StopCardStatus
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
from app.schemas.stop_card import StopCardPublicResponse
from app.services.stop_card import StopCardService

router = APIRouter(tags=["bot-stop-cards"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
IMAGE_SIGNATURES = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/webp": (b"RIFF",),
}
EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def _detect_image_content_type(data: bytes) -> str | None:
    if data.startswith(IMAGE_SIGNATURES["image/jpeg"]):
        return "image/jpeg"
    if data.startswith(IMAGE_SIGNATURES["image/png"]):
        return "image/png"
    if data.startswith(IMAGE_SIGNATURES["image/webp"]) and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _service(db: AsyncSession = Depends(get_db)) -> StopCardService:
    return StopCardService(
        StopCardRepository(db),
        StopCardPhotoRepository(db),
        UserRepository(db),
    )


async def _read_photo(photo: UploadFile) -> tuple[bytes, str, str]:
    if photo.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неподдерживаемый тип файла: {photo.content_type}",
        )
    data = await photo.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Файл слишком большой",
        )
    content_type = _detect_image_content_type(data)
    if content_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл не похож на изображение",
        )
    if content_type != photo.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Тип файла не совпадает с содержимым",
        )
    return data, content_type, EXTENSIONS[content_type]


def _assert_photo_count(photos: list[UploadFile]) -> None:
    if len(photos) > settings.MAX_UPLOAD_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Можно загрузить не более {settings.MAX_UPLOAD_FILES} фото",
        )


# ── Создать стоп-карту ────────────────────────────────────────────────────────

@router.post("/stop-cards", response_model=StopCardPublicResponse, status_code=status.HTTP_201_CREATED)
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

@router.post("/stop-cards/{stop_card_id}/photos", response_model=StopCardPublicResponse)
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

    _assert_photo_count(photos)

    async def _read_and_upload(photo: UploadFile) -> str:
        data, content_type, ext = await _read_photo(photo)
        return await upload_file(data, content_type, ext)

    keys = await asyncio.gather(*[_read_and_upload(p) for p in photos])
    await svc.photo_repo.create_many(stop_card_id, list(keys), photo_type="before")
    return await svc.get_by_id(stop_card_id)


# ── Менеджер: принять стоп-карту ─────────────────────────────────────────────

@router.patch("/stop-cards/{stop_card_id}/bot-acknowledge", response_model=StopCardPublicResponse)
async def bot_acknowledge(
    stop_card_id: int,
    body: BotManagerActionRequest,
    svc: StopCardService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    actor = await svc.user_repo.get_by_telegram_id(body.telegram_id)
    if actor is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь не найден")
    try:
        card = await svc.acknowledge(stop_card_id, actor.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return card


# ── Менеджер: загрузить устранение (фото ПОСЛЕ + описание) ───────────────────

@router.post("/stop-cards/{stop_card_id}/bot-fix", response_model=StopCardPublicResponse)
async def bot_fix(
    stop_card_id: int,
    telegram_id: int = Form(...),
    fix_description: str = Form(...),
    photos: list[UploadFile] = File(default=[]),
    svc: StopCardService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    violator = await svc.user_repo.get_by_telegram_id(telegram_id)
    if violator is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")

    _assert_photo_count(photos)

    async def _upload(p: UploadFile) -> str:
        data, content_type, ext = await _read_photo(p)
        return await upload_file(data, content_type, ext)

    after_keys = list(await asyncio.gather(*[_upload(p) for p in photos])) if photos else []

    try:
        return await svc.submit_fix(stop_card_id, violator.id, fix_description, after_keys)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/stop-cards/{stop_card_id}/manager-send-to-safety", response_model=StopCardPublicResponse)
async def manager_send_to_safety(
    stop_card_id: int,
    body: BotEngineerDecisionRequest,
    svc: StopCardService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    manager = await svc.user_repo.get_by_telegram_id(body.telegram_id)
    if manager is None or manager.role not in (UserRole.manager, UserRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")
    try:
        return await svc.manager_send_to_safety(stop_card_id, manager.id, body.note)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/stop-cards/{stop_card_id}/manager-return", response_model=StopCardPublicResponse)
async def manager_return_to_violator(
    stop_card_id: int,
    body: BotEngineerDecisionRequest,
    svc: StopCardService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    manager = await svc.user_repo.get_by_telegram_id(body.telegram_id)
    if manager is None or manager.role not in (UserRole.manager, UserRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")
    if not body.note:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Комментарий обязателен")
    try:
        return await svc.manager_return_to_violator(stop_card_id, manager.id, body.note)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ── Инженер ОТ и ТБ: решение ─────────────────────────────────────────────────

@router.patch("/stop-cards/{stop_card_id}/bot-engineer", response_model=StopCardPublicResponse)
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
            card = await svc.safety_approve(stop_card_id, engineer.id, body.note)
        elif body.action == "reject":
            card = await svc.safety_reject(stop_card_id, engineer.id, body.note)
        elif body.action == "revision":
            card = await svc.safety_revision(stop_card_id, engineer.id, body.note)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неизвестное действие")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    note_line = f"\n\n💬 Комментарий: {body.note}" if body.note else ""

    # Уведомляем менеджера участка
    managers = await svc.user_repo.get_managers_by_section(card.section_id)
    for mgr in managers:
        if not mgr.telegram_id:
            continue
        if body.action == "approve":
            text = (
                f"✅ <b>Стоп-карта #{card.id} — разрешено к работе!</b>\n\n"
                f"Инженер ОТ и ТБ разрешил возобновить работы.{note_line}"
            )
        elif body.action == "reject":
            text = (
                f"⛔ <b>Стоп-карта #{card.id} — работы ЗАПРЕЩЕНЫ!</b>\n\n"
                f"Инженер ОТ и ТБ запретил работы.{note_line}"
            )
        else:  # revision
            text = (
                f"🔄 <b>Стоп-карта #{card.id} — требует доработки!</b>\n\n"
                f"Инженер ОТ и ТБ вернул карту нарушителю на доработку.{note_line}"
            )
        await notify(mgr.telegram_id, text)

    # Уведомляем нарушителя
    if card.violator_id:
        violator = await svc.user_repo.get_by_id(card.violator_id)
        if violator and violator.telegram_id:
            if body.action == "approve":
                await notify(violator.telegram_id, f"✅ <b>Стоп-карта #{card.id}</b> — работы разрешены!{note_line}")
            elif body.action == "reject":
                await notify(violator.telegram_id, f"⛔ <b>Стоп-карта #{card.id}</b> — работы запрещены!{note_line}")
            else:
                await notify(
                    violator.telegram_id,
                    f"🔄 <b>Стоп-карта #{card.id}</b> возвращена на доработку.{note_line}\n\n"
                    f"Исправьте нарушение и отправьте фото заново.",
                    inline_keyboard=[[
                        {"text": "📸 Отправить исправление", "callback_data": f"fix:{card.id}"},
                    ]],
                )

    # Уведомляем репортёра об итоге
    reporter = await svc.user_repo.get_by_id(card.reporter_id)
    if reporter and reporter.telegram_id:
        if body.action == "approve":
            await notify(reporter.telegram_id, f"✅ <b>Стоп-карта #{card.id}</b> — работы разрешены!{note_line}")
        elif body.action == "reject":
            await notify(reporter.telegram_id, f"⛔ <b>Стоп-карта #{card.id}</b> — работы запрещены!{note_line}")

    return card


# ── Вспомогательные ──────────────────────────────────────────────────────────

@router.get("/stop-cards/my/{telegram_id}", response_model=list[StopCardPublicResponse])
async def my_stop_cards(
    telegram_id: int,
    svc: StopCardService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    reporter = await svc.user_repo.get_by_telegram_id(telegram_id)
    if reporter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return await svc.get_by_reporter(reporter.id)


@router.get("/stop-cards/for-violator/{telegram_id}", response_model=list[StopCardPublicResponse])
async def cards_for_violator(
    telegram_id: int,
    svc: StopCardService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    violator = await svc.user_repo.get_by_telegram_id(telegram_id)
    if violator is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return await svc.get_filtered(
        violator_id=violator.id,
        statuses=[
            StopCardStatus.violator_fixing,
            StopCardStatus.manager_review,
            StopCardStatus.safety_check,
            StopCardStatus.approved,
            StopCardStatus.rejected,
        ],
    )


@router.get("/stop-cards/for-manager/{telegram_id}", response_model=list[StopCardPublicResponse])
async def cards_for_manager(
    telegram_id: int,
    svc: StopCardService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    manager = await svc.user_repo.get_by_telegram_id(telegram_id)
    if manager is None or manager.role not in (UserRole.manager, UserRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")
    statuses = [
        StopCardStatus.waiting_violator,
        StopCardStatus.violator_fixing,
        StopCardStatus.manager_review,
        StopCardStatus.safety_check,
    ]
    if manager.role == UserRole.admin:
        return await svc.get_filtered(statuses=statuses)
    return await svc.get_filtered(section_id=manager.section_id, statuses=statuses)


@router.get("/stop-cards/for-engineer", response_model=list[StopCardPublicResponse])
async def cards_for_engineer(
    telegram_id: int,
    svc: StopCardService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    engineer = await svc.user_repo.get_by_telegram_id(telegram_id)
    if engineer is None or engineer.role not in (UserRole.safety_engineer, UserRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")
    return await svc.get_for_safety_check()


@router.get("/stop-cards/{stop_card_id}", response_model=StopCardPublicResponse)
async def get_stop_card(
    stop_card_id: int,
    svc: StopCardService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    try:
        return await svc.get_by_id(stop_card_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/photos/{minio_key:path}")
async def get_photo(
    minio_key: str,
    _: None = Depends(verify_bot_token),
):
    try:
        data, content_type = await minio_get_file(minio_key)
        return Response(
            content=data,
            media_type=content_type,
            headers={"Cache-Control": "private, max-age=300"},
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Фото слишком большое")
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
