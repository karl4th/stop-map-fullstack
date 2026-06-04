from app.models.section import Section
from app.repositories.section import SectionRepository


class SectionService:
    def __init__(self, repo: SectionRepository) -> None:
        self.repo = repo

    async def get_all(self) -> list[Section]:
        return await self.repo.get_all()

    async def get_by_id(self, section_id: int) -> Section:
        section = await self.repo.get_by_id(section_id)
        if section is None:
            raise ValueError(f"Участок {section_id} не найден")
        return section

    async def create(self, name: str) -> Section:
        existing = await self.repo.get_by_name(name)
        if existing is not None:
            raise ValueError(f"Участок '{name}' уже существует")
        return await self.repo.create(name=name)

    async def update(self, section_id: int, name: str) -> Section:
        section = await self.get_by_id(section_id)
        existing = await self.repo.get_by_name(name)
        if existing is not None and existing.id != section_id:
            raise ValueError(f"Участок '{name}' уже существует")
        section.name = name
        await self.repo.db.flush()
        await self.repo.db.refresh(section)
        return section

    async def delete(self, section_id: int) -> None:
        deleted = await self.repo.delete(section_id)
        if not deleted:
            raise ValueError(f"Участок {section_id} не найден")
