from datetime import datetime

from sqlalchemy import func, select
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

    async def get_filtered(
        self,
        *,
        section_id: int | None = None,
        status: StopCardStatus | None = None,
        statuses: list[StopCardStatus] | None = None,
        reporter_id: int | None = None,
        violator_id: int | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[StopCard]:
        stmt = self._with_all()
        if section_id is not None:
            stmt = stmt.where(StopCard.section_id == section_id)
        if status is not None:
            stmt = stmt.where(StopCard.status == status)
        if statuses:
            stmt = stmt.where(StopCard.status.in_(statuses))
        if reporter_id is not None:
            stmt = stmt.where(StopCard.reporter_id == reporter_id)
        if violator_id is not None:
            stmt = stmt.where(StopCard.violator_id == violator_id)
        if created_from is not None:
            stmt = stmt.where(StopCard.created_at >= created_from)
        if created_to is not None:
            stmt = stmt.where(StopCard.created_at < created_to)
        stmt = stmt.order_by(StopCard.created_at.desc()).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_reporter(self, reporter_id: int) -> list[StopCard]:
        return await self.get_filtered(reporter_id=reporter_id)

    async def get_by_section(self, section_id: int) -> list[StopCard]:
        return await self.get_filtered(section_id=section_id)

    async def get_by_status(self, status: StopCardStatus) -> list[StopCard]:
        return await self.get_filtered(status=status)

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

    async def get_by_month(
        self,
        year: int,
        month: int,
        *,
        section_id: int | None = None,
        status: StopCardStatus | None = None,
    ) -> list[StopCard]:
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        return await self.get_filtered(
            section_id=section_id,
            status=status,
            created_from=start,
            created_to=end,
        )
