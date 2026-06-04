from sqlalchemy import select

from app.models.user import User, UserRole, UserStatus
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.phone == phone)
        )
        return result.scalar_one_or_none()

    async def get_by_section(self, section_id: int) -> list[User]:
        result = await self.db.execute(
            select(User).where(User.section_id == section_id)
        )
        return list(result.scalars().all())

    async def get_managers_by_section(self, section_id: int) -> list[User]:
        result = await self.db.execute(
            select(User).where(
                User.section_id == section_id,
                User.role == UserRole.manager,
                User.status == UserStatus.active,
            )
        )
        return list(result.scalars().all())

    async def get_pending_by_section(self, section_id: int) -> list[User]:
        result = await self.db.execute(
            select(User).where(
                User.section_id == section_id,
                User.status == UserStatus.pending,
            )
        )
        return list(result.scalars().all())

    async def get_pending_all(self) -> list[User]:
        result = await self.db.execute(
            select(User).where(User.status == UserStatus.pending)
        )
        return list(result.scalars().all())

    async def update_status(self, user_id: int, status: UserStatus) -> User | None:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.status = status
        await self.db.flush()
        await self.db.refresh(user)
        return user

