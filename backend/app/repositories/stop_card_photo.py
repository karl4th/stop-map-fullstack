from sqlalchemy import select

from app.models.stop_card_photo import StopCardPhoto
from app.repositories.base import BaseRepository


class StopCardPhotoRepository(BaseRepository[StopCardPhoto]):
    model = StopCardPhoto

    async def get_by_stop_card(self, stop_card_id: int) -> list[StopCardPhoto]:
        result = await self.db.execute(
            select(StopCardPhoto).where(StopCardPhoto.stop_card_id == stop_card_id)
        )
        return list(result.scalars().all())

    async def create_many(self, stop_card_id: int, minio_keys: list[str]) -> list[StopCardPhoto]:
        photos = [
            StopCardPhoto(stop_card_id=stop_card_id, minio_key=key)
            for key in minio_keys
        ]
        self.db.add_all(photos)
        await self.db.flush()
        for photo in photos:
            await self.db.refresh(photo)
        return photos
