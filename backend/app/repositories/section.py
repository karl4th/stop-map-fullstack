from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.section import Section
from app.repositories.base import BaseRepository


class SectionRepository(BaseRepository[Section]):
    model = Section

    async def get_by_name(self, name: str) -> Section | None:
        result = await self.db.execute(
            select(Section).where(Section.name == name)
        )
        return result.scalar_one_or_none()

    async def get_with_managers(self, section_id: int) -> Section | None:
        from app.models.user import User, UserRole
        result = await self.db.execute(
            select(Section)
            .where(Section.id == section_id)
            .options(
                selectinload(Section.users.and_(User.role == UserRole.manager))
            )
        )
        return result.scalar_one_or_none()
