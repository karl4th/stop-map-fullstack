from datetime import datetime, timezone

from app.models.stop_card import StopCard, StopCardStatus
from app.repositories.stop_card import StopCardRepository
from app.repositories.stop_card_photo import StopCardPhotoRepository
from app.repositories.user import UserRepository


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class StopCardService:
    def __init__(
        self,
        repo: StopCardRepository,
        photo_repo: StopCardPhotoRepository,
        user_repo: UserRepository,
    ) -> None:
        self.repo = repo
        self.photo_repo = photo_repo
        self.user_repo = user_repo

    async def create(
        self,
        reporter_id: int,
        violator_name: str,
        section_id: int,
        description: str,
        minio_keys: list[str],
    ) -> StopCard:
        card = await self.repo.create(
            reporter_id=reporter_id,
            violator_name=violator_name,
            section_id=section_id,
            description=description,
            status=StopCardStatus.created,
        )
        if minio_keys:
            await self.photo_repo.create_many(card.id, minio_keys, photo_type="before")
        return await self.repo.get_with_photos(card.id)

    async def get_by_id(self, stop_card_id: int) -> StopCard:
        card = await self.repo.get_with_photos(stop_card_id)
        if card is None:
            raise ValueError(f"Стоп-карта {stop_card_id} не найдена")
        return card

    async def get_by_section(self, section_id: int) -> list[StopCard]:
        return await self.repo.get_by_section(section_id)

    async def get_by_reporter(self, reporter_id: int) -> list[StopCard]:
        return await self.repo.get_by_reporter(reporter_id)

    async def get_by_month(self, year: int, month: int) -> list[StopCard]:
        return await self.repo.get_by_month(year, month)

    async def get_for_safety_check(self) -> list[StopCard]:
        return await self.repo.get_by_status(StopCardStatus.safety_check)

    # ─── Менеджер: принять карту ────────────────────────────────────────────

    async def acknowledge(self, stop_card_id: int, manager_id: int) -> StopCard:
        card = await self.get_by_id(stop_card_id)
        if card.status != StopCardStatus.created:
            raise ValueError("Можно принять только только что созданную карту")
        card.status = StopCardStatus.under_review
        card.acknowledged_by_id = manager_id
        card.acknowledged_at = _now()
        await self.repo.db.flush()
        self.repo.db.expire_all()
        return await self.repo.get_with_photos(stop_card_id)

    # ─── Менеджер: загрузить устранение (фото после + описание) ─────────────

    async def submit_fix(
        self,
        stop_card_id: int,
        manager_id: int,
        fix_description: str,
        after_minio_keys: list[str],
    ) -> StopCard:
        card = await self.get_by_id(stop_card_id)
        if card.status not in (StopCardStatus.under_review, StopCardStatus.in_progress):
            raise ValueError("Нельзя загрузить устранение на данном этапе")
        card.status = StopCardStatus.safety_check
        card.fixed_by_id = manager_id
        card.fixed_at = _now()
        card.fix_description = fix_description
        if after_minio_keys:
            await self.photo_repo.create_many(stop_card_id, after_minio_keys, photo_type="after")
        await self.repo.db.flush()
        self.repo.db.expire_all()
        return await self.repo.get_with_photos(stop_card_id)

    # ─── Инженер ОТ и ТБ: разрешить ─────────────────────────────────────────

    async def safety_approve(
        self,
        stop_card_id: int,
        engineer_id: int,
        note: str | None,
    ) -> StopCard:
        card = await self.get_by_id(stop_card_id)
        if card.status != StopCardStatus.safety_check:
            raise ValueError("Карта не находится на проверке ОТ и ТБ")
        card.status = StopCardStatus.approved
        card.safety_checked_by_id = engineer_id
        card.safety_checked_at = _now()
        card.safety_note = note
        card.closed_at = _now()
        await self.repo.db.flush()
        self.repo.db.expire_all()
        return await self.repo.get_with_photos(stop_card_id)

    # ─── Инженер ОТ и ТБ: запретить ─────────────────────────────────────────

    async def safety_reject(
        self,
        stop_card_id: int,
        engineer_id: int,
        note: str | None,
    ) -> StopCard:
        card = await self.get_by_id(stop_card_id)
        if card.status != StopCardStatus.safety_check:
            raise ValueError("Карта не находится на проверке ОТ и ТБ")
        card.status = StopCardStatus.rejected
        card.safety_checked_by_id = engineer_id
        card.safety_checked_at = _now()
        card.safety_note = note
        await self.repo.db.flush()
        self.repo.db.expire_all()
        return await self.repo.get_with_photos(stop_card_id)

    # ─── Инженер ОТ и ТБ: на доработку ──────────────────────────────────────

    async def safety_revision(
        self,
        stop_card_id: int,
        engineer_id: int,
        note: str | None,
    ) -> StopCard:
        card = await self.get_by_id(stop_card_id)
        if card.status != StopCardStatus.safety_check:
            raise ValueError("Карта не находится на проверке ОТ и ТБ")
        card.status = StopCardStatus.in_progress
        card.safety_checked_by_id = engineer_id
        card.safety_checked_at = _now()
        card.safety_note = note
        # Сбрасываем данные предыдущего устранения для повторной попытки
        card.fixed_by_id = None
        card.fixed_at = None
        card.fix_description = None
        await self.repo.db.flush()
        self.repo.db.expire_all()
        return await self.repo.get_with_photos(stop_card_id)

    # ─── Администратор: закрыть ──────────────────────────────────────────────

    async def close(self, stop_card_id: int) -> StopCard:
        card = await self.get_by_id(stop_card_id)
        if card.status != StopCardStatus.approved:
            raise ValueError("Закрыть можно только одобренную карту")
        card.status = StopCardStatus.closed
        card.closed_at = _now()
        await self.repo.db.flush()
        self.repo.db.expire_all()
        return await self.repo.get_with_photos(stop_card_id)

    # ─── Вспомогательные ─────────────────────────────────────────────────────

    async def get_managers_for_card(self, stop_card_id: int) -> list:
        card = await self.repo.get_with_photos(stop_card_id)
        if card is None:
            return []
        return await self.user_repo.get_managers_by_section(card.section_id)

    async def get_safety_engineers(self) -> list:
        return await self.user_repo.get_safety_engineers()
