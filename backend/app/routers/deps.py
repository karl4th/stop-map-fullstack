from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.services.auth import decode_access_token

bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный токен")

    user = await UserRepository(db).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return user


async def require_manager_or_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in (UserRole.manager, UserRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return user


async def require_safety_engineer(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.safety_engineer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return user


async def require_safety_engineer_or_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in (UserRole.safety_engineer, UserRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return user


async def verify_bot_token(x_bot_token: str = Header(...)) -> None:
    if x_bot_token != settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Неверный токен бота")
