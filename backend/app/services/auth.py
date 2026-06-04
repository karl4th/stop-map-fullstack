from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings
from app.models.user import User, UserStatus


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(user_id: int, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])


async def authenticate(phone: str, password: str, user: User | None) -> User:
    if user is None or user.hashed_password is None:
        raise ValueError("Неверный телефон или пароль")
    if user.status != UserStatus.active:
        raise ValueError("Пользователь заблокирован или не активирован")
    if not verify_password(password, user.hashed_password):
        raise ValueError("Неверный телефон или пароль")
    return user
