import logging

from aiogram import Bot
from aiogram.types import BufferedInputFile, InputMediaPhoto

from app.core import api

logger = logging.getLogger(__name__)


async def send_card_photos(bot: Bot, chat_id: int, photos: list[dict], label: str | None = None) -> None:
    if not photos:
        return
    media = []
    for i, p in enumerate(photos[:10]):
        try:
            data = await api.get_photo_bytes(p["minio_key"])
            caption = label if i == 0 and label else None
            media.append(InputMediaPhoto(
                media=BufferedInputFile(data, filename=f"photo_{p['id']}.jpg"),
                caption=caption,
            ))
        except Exception as e:
            logger.warning("Failed to fetch photo %s: %s", p.get("minio_key"), e)

    if media:
        try:
            await bot.send_media_group(chat_id=chat_id, media=media)
        except Exception as e:
            logger.warning("Failed to send media group to %s: %s", chat_id, e)
