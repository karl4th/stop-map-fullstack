from sqlalchemy import func, select

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

    async def get_filtered(
        self,
        *,
        section_id: int | None = None,
        role: UserRole | None = None,
        status: UserStatus | None = None,
        search: str | None = None,
    ) -> list[User]:
        stmt = select(User)
        if section_id is not None:
            stmt = stmt.where(User.section_id == section_id)
        if role is not None:
            stmt = stmt.where(User.role == role)
        if status is not None:
            stmt = stmt.where(User.status == status)
        if search:
            q = f"%{search.lower().strip()}%"
            stmt = stmt.where(
                (func.lower(User.full_name).like(q))
                | (func.lower(User.phone).like(q))
            )
        result = await self.db.execute(stmt.order_by(User.created_at.desc()))
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

    async def get_safety_engineers(self) -> list[User]:
        result = await self.db.execute(
            select(User).where(
                User.role == UserRole.safety_engineer,
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

    async def find_by_full_name(self, full_name: str) -> list[User]:
        result = await self.db.execute(
            select(User).where(func.lower(User.full_name) == full_name.lower().strip())
        )
        return list(result.scalars().all())

    async def get_admins_with_telegram(self) -> list[User]:
        result = await self.db.execute(
            select(User).where(
                User.role == UserRole.admin,
                User.status == UserStatus.active,
                User.telegram_id.isnot(None),
            )
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
