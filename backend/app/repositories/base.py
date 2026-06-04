from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, id: int) -> ModelT | None:
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_all(self) -> list[ModelT]:
        result = await self.db.execute(select(self.model))
        return list(result.scalars().all())

    async def create(self, **kwargs) -> ModelT:
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete(self, id: int) -> bool:
        instance = await self.get_by_id(id)
        if instance is None:
            return False
        await self.db.delete(instance)
        await self.db.flush()
        return True
