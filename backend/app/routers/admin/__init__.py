from fastapi import APIRouter

from app.routers.admin.auth import router as auth_router
from app.routers.admin.sections import router as sections_router
from app.routers.admin.stop_cards import router as stop_cards_router
from app.routers.admin.users import router as users_router

router = APIRouter(prefix="/admin")

router.include_router(auth_router)
router.include_router(sections_router)
router.include_router(users_router)
router.include_router(stop_cards_router)
