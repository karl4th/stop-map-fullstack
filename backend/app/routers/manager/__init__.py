from fastapi import APIRouter

from app.routers.common.auth import router as auth_router
from app.routers.manager.stop_cards import router as stop_cards_router
from app.routers.manager.users import router as users_router

router = APIRouter(prefix="/manager")

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(stop_cards_router)
