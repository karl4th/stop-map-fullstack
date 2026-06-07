from aiogram.types import ReplyKeyboardMarkup

from app.core import api
from app.keyboards.reply import engineer_menu, main_menu, manager_menu, remove


async def role_menu(telegram_id: int) -> ReplyKeyboardMarkup:
    try:
        user = await api.get_user(telegram_id)
        if user and user.get("status") == "active":
            role = user.get("role", "worker")
            if role == "manager":
                return manager_menu()
            if role == "safety_engineer":
                return engineer_menu()
    except Exception:
        pass
    return main_menu()
