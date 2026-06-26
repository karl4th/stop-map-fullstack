import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(8, connect=3),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _client


async def close_telegram_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def notify(chat_id: int, text: str, inline_keyboard: list | None = None) -> None:
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if inline_keyboard:
        payload["reply_markup"] = {"inline_keyboard": inline_keyboard}
    try:
        response = await _get_client().post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        logger.warning("Telegram notify failed for %s: %s", chat_id, e)
