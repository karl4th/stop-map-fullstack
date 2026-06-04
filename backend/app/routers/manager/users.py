from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.repositories.user import UserRepository
from app.routers.deps import require_manager_or_admin
from app.schemas.user import UserResponse
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["manager-users"])


def _service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


@router.get("/pending", response_model=list[UserResponse])
async def list_pending(
    svc: UserService = Depends(_service),
    current_user: User = Depends(require_manager_or_admin),
):
    return await svc.get_pending_by_section(current_user.section_id)


@router.get("", response_model=list[UserResponse])
async def list_users(
    svc: UserService = Depends(_service),
    current_user: User = Depends(require_manager_or_admin),
):
    return await svc.get_by_section(current_user.section_id)


@router.patch("/{user_id}/approve", response_model=UserResponse)
async def approve_user(
    user_id: int,
    svc: UserService = Depends(_service),
    current_user: User = Depends(require_manager_or_admin),
):
    user = await svc.get_by_id(user_id)
    if user.section_id != current_user.section_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому пользователю")
    try:
        return await svc.approve(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{user_id}/block", response_model=UserResponse)
async def block_user(
    user_id: int,
    svc: UserService = Depends(_service),
    current_user: User = Depends(require_manager_or_admin),
):
    user = await svc.get_by_id(user_id)
    if user.section_id != current_user.section_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому пользователю")
    try:
        return await svc.block(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
