from fastapi import APIRouter

from app.routers.bot.stop_cards import router as stop_cards_router
from app.routers.bot.users import router as users_router

router = APIRouter(prefix="/bot")

router.include_router(users_router)
router.include_router(stop_cards_router)
