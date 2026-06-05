from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.telegram import notify
from app.models.user import User, UserRole, UserStatus
from app.repositories.user import UserRepository
from app.routers.deps import require_admin
from app.schemas.user import AssignRoleRequest, UserResponse
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["admin-users"])


def _service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


@router.get("", response_model=list[UserResponse])
async def list_users(
    section_id: int | None = Query(None),
    role: UserRole | None = Query(None),
    status: UserStatus | None = Query(None),
    search: str | None = Query(None),
    svc: UserService = Depends(_service),
    _: User = Depends(require_admin),
):
    users = await svc.get_all()
    if section_id is not None:
        users = [u for u in users if u.section_id == section_id]
    if role is not None:
        users = [u for u in users if u.role == role]
    if status is not None:
        users = [u for u in users if u.status == status]
    if search:
        q = search.lower()
        users = [
            u for u in users
            if q in u.full_name.lower() or (u.phone and q in u.phone.lower())
        ]
    return users


@router.get("/pending", response_model=list[UserResponse])
async def list_pending(
    svc: UserService = Depends(_service),
    _: User = Depends(require_admin),
):
    return await svc.get_pending_all()


@router.patch("/{user_id}/approve", response_model=UserResponse)
async def approve_user(
    user_id: int,
    svc: UserService = Depends(_service),
    _: User = Depends(require_admin),
):
    try:
        user = await svc.approve(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if user.telegram_id:
        await notify(
            user.telegram_id,
            "✅ <b>Вас одобрили!</b>\n\nТеперь вы можете создавать стоп-карты.\n\nНажмите /start",
        )
    return user


@router.patch("/{user_id}/block", response_model=UserResponse)
async def block_user(
    user_id: int,
    svc: UserService = Depends(_service),
    _: User = Depends(require_admin),
):
    try:
        return await svc.block(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{user_id}/role", response_model=UserResponse)
async def assign_role(
    user_id: int,
    body: AssignRoleRequest,
    svc: UserService = Depends(_service),
    _: User = Depends(require_admin),
):
    try:
        return await svc.assign_role(user_id, body.role, body.password, body.section_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
