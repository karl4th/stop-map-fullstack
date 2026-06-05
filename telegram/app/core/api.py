import httpx

from app.core.config import settings

_headers = {"X-Bot-Token": settings.TELEGRAM_BOT_TOKEN}


async def get_user(telegram_id: int) -> dict | None:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.BACKEND_URL}/bot/users/by-telegram/{telegram_id}", headers=_headers)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()


async def register_user(telegram_id: int, full_name: str, phone: str, section_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{settings.BACKEND_URL}/bot/users/register", headers=_headers, json={
            "telegram_id": telegram_id,
            "full_name": full_name,
            "phone": phone,
            "section_id": section_id,
        })
        r.raise_for_status()
        return r.json()


async def get_sections() -> list[dict]:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.BACKEND_URL}/bot/sections", headers=_headers)
        r.raise_for_status()
        return r.json()


async def create_stop_card(reporter_telegram_id: int, violator_name: str, section_id: int, description: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{settings.BACKEND_URL}/bot/stop-cards", headers=_headers, json={
            "reporter_telegram_id": reporter_telegram_id,
            "violator_name": violator_name,
            "section_id": section_id,
            "description": description,
        })
        r.raise_for_status()
        return r.json()


async def upload_photos(stop_card_id: int, photos: list[tuple[str, bytes, str]]) -> dict:
    async with httpx.AsyncClient() as client:
        files = [("photos", (name, data, content_type)) for name, data, content_type in photos]
        r = await client.post(
            f"{settings.BACKEND_URL}/bot/stop-cards/{stop_card_id}/photos",
            headers=_headers,
            files=files,
        )
        r.raise_for_status()
        return r.json()


async def get_my_cards(telegram_id: int) -> list[dict]:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.BACKEND_URL}/bot/stop-cards/my/{telegram_id}", headers=_headers)
        r.raise_for_status()
        return r.json()


async def get_managers(section_id: int) -> list[dict]:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.BACKEND_URL}/bot/sections/{section_id}/managers", headers=_headers)
        r.raise_for_status()
        return r.json()


async def get_safety_engineers() -> list[dict]:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.BACKEND_URL}/bot/safety-engineers", headers=_headers)
        r.raise_for_status()
        return r.json()
