import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from app.core.api import close_client
from app.core.config import settings
from app.handlers.cards_list import router as cards_list_router
from app.handlers.engineer import router as engineer_router
from app.handlers.manager import router as manager_router
from app.handlers.start import router as start_router
from app.handlers.stop_card import router as stop_card_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logging.getLogger("aiogram").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def main():
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    storage = RedisStorage.from_url(settings.REDIS_URL)
    dp = Dispatcher(storage=storage)

    dp.include_router(start_router)
    dp.include_router(stop_card_router)
    dp.include_router(manager_router)
    dp.include_router(engineer_router)
    dp.include_router(cards_list_router)

    logging.info("Bot started pid=%s", os.getpid())
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await close_client()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
