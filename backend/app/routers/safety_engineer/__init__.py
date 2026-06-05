from fastapi import APIRouter

from app.routers.common.auth import router as auth_router
from app.routers.safety_engineer.stop_cards import router as stop_cards_router

router = APIRouter(prefix="/safety-engineer")

router.include_router(auth_router)
router.include_router(stop_cards_router)
