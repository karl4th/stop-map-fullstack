from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User, UserRole, UserStatus
from app.services.auth import hash_password as _hash_password


async def create_first_admin(db: AsyncSession) -> None:
    if (
        settings.APP_ENV == "production"
        and settings.FIRST_ADMIN_PASSWORD == "change_me_in_production"
    ):
        raise RuntimeError("FIRST_ADMIN_PASSWORD must be changed in production")

    result = await db.execute(
        select(User).where(User.role == UserRole.admin).limit(1)
    )
    if result.scalar_one_or_none() is not None:
        return

    admin = User(
        full_name=settings.FIRST_ADMIN_NAME,
        phone=settings.FIRST_ADMIN_PHONE,
        hashed_password=_hash_password(settings.FIRST_ADMIN_PASSWORD),
        role=UserRole.admin,
        status=UserStatus.active,
    )
    db.add(admin)
    await db.commit()
