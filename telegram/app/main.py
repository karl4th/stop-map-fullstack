import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from app.core.config import settings
from app.handlers.start import router as start_router
from app.handlers.stop_card import router as stop_card_router

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    storage = RedisStorage.from_url(settings.REDIS_URL)
    dp = Dispatcher(storage=storage)

    dp.include_router(start_router)
    dp.include_router(stop_card_router)

    logging.info("Bot started")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
