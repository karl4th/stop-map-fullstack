import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def notify(chat_id: int, text: str, inline_keyboard: list | None = None) -> None:
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if inline_keyboard:
        payload["reply_markup"] = {"inline_keyboard": inline_keyboard}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            await client.post(url, json=payload)
    except Exception as e:
        logger.warning("Telegram notify failed for %s: %s", chat_id, e)
