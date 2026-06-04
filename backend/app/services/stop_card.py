from app.models.stop_card import StopCard, StopCardStatus
from app.repositories.stop_card import StopCardRepository
from app.repositories.stop_card_photo import StopCardPhotoRepository
from app.repositories.user import UserRepository


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
            status=StopCardStatus.issued,
        )
        if minio_keys:
            await self.photo_repo.create_many(card.id, minio_keys)
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

    async def acknowledge(self, stop_card_id: int) -> StopCard:
        card = await self.get_by_id(stop_card_id)  # 1 fetch with photos
        if card.status != StopCardStatus.issued:
            raise ValueError("Стоп-карта уже обработана")
        card.status = StopCardStatus.acknowledged
        await self.repo.db.flush()
        return await self.repo.get_with_photos(stop_card_id)  # reload with updated_at

    async def close(self, stop_card_id: int) -> StopCard:
        card = await self.get_by_id(stop_card_id)
        card.status = StopCardStatus.closed
        await self.repo.db.flush()
        return await self.repo.get_with_photos(stop_card_id)

    async def dispute(self, stop_card_id: int, reason: str) -> StopCard:
        card = await self.get_by_id(stop_card_id)
        card.status = StopCardStatus.disputed
        card.dispute_reason = reason
        await self.repo.db.flush()
        return await self.repo.get_with_photos(stop_card_id)

    async def get_managers_for_card(self, stop_card_id: int) -> list:
        card = await self.repo.get_by_id(stop_card_id)
        if card is None:
            return []
        return await self.user_repo.get_managers_by_section(card.section_id)
