from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.section import SectionRepository
from app.repositories.user import UserRepository
from app.routers.deps import verify_bot_token
from app.schemas.bot import BotRegisterRequest
from app.schemas.section import SectionResponse
from app.schemas.user import UserResponse
from app.services.user import UserService

router = APIRouter(tags=["bot-users"])


def _service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


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
    svc: UserService = Depends(_service),
    _: None = Depends(verify_bot_token),
):
    try:
        return await svc.register_via_bot(
            telegram_id=body.telegram_id,
            full_name=body.full_name,
            phone=body.phone,
            section_id=body.section_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/sections", response_model=list[SectionResponse])
async def list_sections(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_bot_token),
):
    return await SectionRepository(db).get_all()
