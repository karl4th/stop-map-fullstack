from sqlalchemy import extract, func, select
from sqlalchemy.orm import selectinload

from app.models.stop_card import StopCard, StopCardStatus
from app.models.stop_card_photo import StopCardPhoto
from app.repositories.base import BaseRepository


class StopCardRepository(BaseRepository[StopCard]):
    model = StopCard

    def _with_all(self):
        return select(StopCard).options(
            selectinload(StopCard.photos),
            selectinload(StopCard.reporter),
            selectinload(StopCard.violator),
            selectinload(StopCard.acknowledged_by),
            selectinload(StopCard.fixed_by),
            selectinload(StopCard.manager_checked_by),
            selectinload(StopCard.safety_checked_by),
        )

    async def get_with_photos(self, stop_card_id: int) -> StopCard | None:
        result = await self.db.execute(
            self._with_all().where(StopCard.id == stop_card_id)
        )
        return result.scalar_one_or_none()

    async def get_by_photo_key(self, key: str) -> StopCard | None:
        result = await self.db.execute(
            self._with_all()
            .join(StopCardPhoto, StopCardPhoto.stop_card_id == StopCard.id)
            .where(StopCardPhoto.minio_key == key)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[StopCard]:
        result = await self.db.execute(
            self._with_all().order_by(StopCard.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_reporter(self, reporter_id: int) -> list[StopCard]:
        result = await self.db.execute(
            self._with_all()
            .where(StopCard.reporter_id == reporter_id)
            .order_by(StopCard.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_section(self, section_id: int) -> list[StopCard]:
        result = await self.db.execute(
            self._with_all()
            .where(StopCard.section_id == section_id)
            .order_by(StopCard.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_status(self, status: StopCardStatus) -> list[StopCard]:
        result = await self.db.execute(
            self._with_all()
            .where(StopCard.status == status)
            .order_by(StopCard.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_unassigned_by_violator_name(self, full_name: str) -> list[StopCard]:
        result = await self.db.execute(
            self._with_all()
            .where(
                StopCard.violator_id.is_(None),
                StopCard.status == StopCardStatus.waiting_violator,
                func.lower(StopCard.violator_name) == full_name.lower().strip(),
            )
            .order_by(StopCard.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_month(self, year: int, month: int) -> list[StopCard]:
        result = await self.db.execute(
            self._with_all()
            .where(
                extract("year", StopCard.created_at) == year,
                extract("month", StopCard.created_at) == month,
            )
            .order_by(StopCard.created_at.desc())
        )
        return list(result.scalars().all())
