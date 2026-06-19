from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.telegram import notify
from app.models.user import UserStatus
from app.repositories.section import SectionRepository
from app.repositories.stop_card import StopCardRepository
from app.repositories.stop_card_photo import StopCardPhotoRepository
from app.repositories.user import UserRepository
from app.routers.deps import verify_bot_token
from app.schemas.bot import BotRegisterRequest, BotUserApprovalRequest
from app.schemas.section import SectionResponse
from app.schemas.user import UserResponse
from app.services.stop_card import StopCardService
from app.services.user import UserService

router = APIRouter(tags=["bot-users"])


def _service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


async def _link_pending_cards(db: AsyncSession, user_id: int) -> None:
    svc = StopCardService(
        StopCardRepository(db),
        StopCardPhotoRepository(db),
        UserRepository(db),
    )
    cards = await svc.link_pending_cards_for_user(user_id)
    user = await UserRepository(db).get_by_id(user_id)
    if user and user.telegram_id:
        for card in cards:
            await notify(
                user.telegram_id,
                f"⚠️ <b>У вас появилась стоп-карта #{card.id}</b>\n\n"
                f"📄 {card.description}\n\n"
                f"Откройте список карт и отправьте исправление.",
            )


@router.get("/users/by-telegram/{telegram_id}", response_model=UserResponse)
async def get_by_telegram(
    telegram_id: int,
    svc: UserService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    user = await svc.repo.get_by_telegram_id(telegram_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user


@router.post("/users/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: BotRegisterRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_bot_token),
):
    svc = UserService(UserRepository(db))
    try:
        user = await svc.register_via_bot(
            telegram_id=body.telegram_id,
            full_name=body.full_name,
            phone=body.phone,
            section_id=body.section_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    # Уведомляем менеджеров участка о новом сотруднике
    managers = await UserRepository(db).get_managers_by_section(body.section_id)
    section = await SectionRepository(db).get_by_id(body.section_id)
    section_name = section.name if section else f"участок {body.section_id}"
    for mgr in managers:
        if mgr.telegram_id:
            await notify(
                mgr.telegram_id,
                f"👤 <b>Новый сотрудник ожидает одобрения</b>\n\n"
                f"ФИО: {body.full_name}\n"
                f"Телефон: {body.phone}\n"
                f"Участок: {section_name}\n\n"
                f"ID пользователя: <code>{user.id}</code>\n"
                f"Отправьте боту: /approve_{user.id} или /reject_{user.id}",
            )

    return user


@router.post("/users/{user_id}/approve", response_model=UserResponse)
async def approve_user(
    user_id: int,
    body: BotUserApprovalRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_bot_token),
):
    repo = UserRepository(db)

    # Проверяем что approver — менеджер
    approver = await repo.get_by_telegram_id(body.manager_telegram_id)
    if approver is None or approver.role.value not in ("manager", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")

    target = await repo.get_by_id(user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    if approver.role.value != "admin" and approver.section_id != target.section_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому пользователю")

    user = await repo.update_status(user_id, UserStatus.active)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    await _link_pending_cards(db, user.id)

    if user.telegram_id:
        await notify(
            user.telegram_id,
            "✅ <b>Вас одобрили!</b>\n\nТеперь вы можете создавать стоп-карты.\n\nНажмите /start",
        )

    return user


@router.post("/users/{user_id}/reject", response_model=UserResponse)
async def reject_user(
    user_id: int,
    body: BotUserApprovalRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_bot_token),
):
    repo = UserRepository(db)

    approver = await repo.get_by_telegram_id(body.manager_telegram_id)
    if approver is None or approver.role.value not in ("manager", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")

    target = await repo.get_by_id(user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    if approver.role.value != "admin" and approver.section_id != target.section_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому пользователю")

    user = await repo.update_status(user_id, UserStatus.blocked)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    if user.telegram_id:
        await notify(
            user.telegram_id,
            "❌ <b>Ваша заявка отклонена.</b>\n\nОбратитесь к менеджеру участка.",
        )

    return user


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    svc: UserService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    from app.repositories.user import UserRepository
    user = await svc.repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user


@router.get("/sections", response_model=list[SectionResponse])
async def list_sections(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_bot_token),
):
    return await SectionRepository(db).get_all()
