from app.models.user import User, UserRole, UserStatus
from app.repositories.user import UserRepository
from app.services.auth import hash_password


class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    async def get_all(self) -> list[User]:
        return await self.repo.get_all()

    async def get_by_id(self, user_id: int) -> User:
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise ValueError(f"Пользователь {user_id} не найден")
        return user

    async def get_by_section(self, section_id: int) -> list[User]:
        return await self.repo.get_by_section(section_id)

    async def get_pending_by_section(self, section_id: int) -> list[User]:
        return await self.repo.get_pending_by_section(section_id)

    async def get_pending_all(self) -> list[User]:
        return await self.repo.get_pending_all()

    async def approve(self, user_id: int) -> User:
        user = await self.get_by_id(user_id)
        if user.status != UserStatus.pending:
            raise ValueError("Пользователь уже активирован или заблокирован")
        return await self.repo.update_status(user_id, UserStatus.active)

    async def block(self, user_id: int) -> User:
        await self.get_by_id(user_id)
        return await self.repo.update_status(user_id, UserStatus.blocked)

    async def assign_role(
        self,
        user_id: int,
        role: UserRole,
        password: str | None = None,
        section_id: int | None = None,
    ) -> User:
        user = await self.get_by_id(user_id)
        user.role = role
        if role in (UserRole.manager, UserRole.safety_engineer, UserRole.admin):
            if not password:
                raise ValueError("Для данной роли необходимо задать пароль")
            user.hashed_password = hash_password(password)
        if section_id is not None:
            user.section_id = section_id
        await self.repo.db.flush()
        await self.repo.db.refresh(user)
        return user

    async def register_via_bot(
        self,
        telegram_id: int,
        full_name: str,
        phone: str,
        section_id: int,
    ) -> User:
        existing = await self.repo.get_by_telegram_id(telegram_id)
        if existing is not None:
            raise ValueError("Вы уже зарегистрированы")
        return await self.repo.create(
            telegram_id=telegram_id,
            full_name=full_name,
            phone=phone,
            section_id=section_id,
            role=UserRole.worker,
            status=UserStatus.pending,
        )
