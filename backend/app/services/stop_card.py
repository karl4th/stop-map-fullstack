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
        # Ищем нарушителя по ФИО (точное совпадение без учёта регистра)
        matches = [
            user
            for user in await self.user_repo.find_by_full_name(violator_name)
            if user.status.value == "active"
        ]
        violator_id = matches[0].id if len(matches) == 1 else None
        initial_status = (
            StopCardStatus.violator_fixing
            if violator_id is not None
            else StopCardStatus.waiting_violator
        )

        card = await self.repo.create(
            reporter_id=reporter_id,
            violator_name=violator_name,
            violator_id=violator_id,
            section_id=section_id,
            description=description,
            status=initial_status,
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

    async def link_pending_cards_for_user(self, user_id: int) -> list[StopCard]:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise ValueError("Пользователь не найден")
        cards = await self.repo.get_unassigned_by_violator_name(user.full_name)
        for card in cards:
            card.violator_id = user.id
            card.status = StopCardStatus.violator_fixing
        await self.repo.db.flush()
        self.repo.db.expire_all()
        return [await self.repo.get_with_photos(card.id) for card in cards]

    def _assert_manager_can_handle(self, card: StopCard, actor) -> None:
        if actor is None:
            raise ValueError("Пользователь не найден")
        if actor.role.value == "admin":
            return
        if actor.role.value != "manager":
            raise ValueError("Нет прав для обработки этой карты")
        if actor.section_id != card.section_id:
            raise ValueError("Нет доступа к карте другого участка")

    # ─── Нарушитель: принять карту ──────────────────────────────────────────

    async def acknowledge(self, stop_card_id: int, actor_id: int) -> StopCard:
        card = await self.get_by_id(stop_card_id)
        if card.status not in (StopCardStatus.created, StopCardStatus.violator_fixing):
            raise ValueError("Карта уже обработана или ожидает другого действия")
        actor = await self.user_repo.get_by_id(actor_id)
        if actor is None:
            raise ValueError("Пользователь не найден")
        is_violator = card.violator_id is not None and card.violator_id == actor.id
        if not is_violator:
            raise ValueError("Нет прав для принятия этой карты")
        card.status = StopCardStatus.violator_fixing
        card.acknowledged_by_id = actor_id
        card.acknowledged_at = _now()
        await self.repo.db.flush()
        self.repo.db.expire_all()
        return await self.repo.get_with_photos(stop_card_id)

    # ─── Нарушитель: загрузить устранение (фото после + описание) ───────────

    async def submit_fix(
        self,
        stop_card_id: int,
        actor_id: int,
        fix_description: str,
        after_minio_keys: list[str],
    ) -> StopCard:
        card = await self.get_by_id(stop_card_id)
        if card.status != StopCardStatus.violator_fixing:
            raise ValueError("Нельзя загрузить устранение на данном этапе")
        if card.violator_id != actor_id:
            raise ValueError("Исправление может отправить только нарушитель")
        card.status = StopCardStatus.manager_review
        card.fixed_by_id = actor_id
        card.fixed_at = _now()
        card.fix_description = fix_description
        card.manager_note = None
        card.manager_checked_by_id = None
        card.manager_checked_at = None
        if after_minio_keys:
            await self.photo_repo.create_many(stop_card_id, after_minio_keys, photo_type="after")
        await self.repo.db.flush()
        self.repo.db.expire_all()
        return await self.repo.get_with_photos(stop_card_id)

    # ─── Менеджер: вернуть нарушителю ───────────────────────────────────────

    async def manager_return_to_violator(
        self,
        stop_card_id: int,
        manager_id: int,
        note: str,
    ) -> StopCard:
        card = await self.get_by_id(stop_card_id)
        if card.status != StopCardStatus.manager_review:
            raise ValueError("Вернуть можно только карту на проверке менеджера")
        manager = await self.user_repo.get_by_id(manager_id)
        self._assert_manager_can_handle(card, manager)
        card.status = StopCardStatus.violator_fixing
        card.manager_note = note
        card.manager_checked_by_id = manager_id
        card.manager_checked_at = _now()
        await self.repo.db.flush()
        self.repo.db.expire_all()
        return await self.repo.get_with_photos(stop_card_id)

    # ─── Менеджер: отправить в ОТ и ТБ ──────────────────────────────────────

    async def manager_send_to_safety(
        self,
        stop_card_id: int,
        manager_id: int,
        note: str | None = None,
    ) -> StopCard:
        card = await self.get_by_id(stop_card_id)
        if card.status != StopCardStatus.manager_review:
            raise ValueError("Отправить в ОТ и ТБ можно только после исправления нарушителем")
        manager = await self.user_repo.get_by_id(manager_id)
        self._assert_manager_can_handle(card, manager)
        card.status = StopCardStatus.safety_check
        card.manager_note = note
        card.manager_checked_by_id = manager_id
        card.manager_checked_at = _now()
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
        card.status = StopCardStatus.violator_fixing
        card.safety_checked_by_id = engineer_id
        card.safety_checked_at = _now()
        card.safety_note = note
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
