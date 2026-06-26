from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.stop_card import StopCardStatus
from app.models.user import User
from app.repositories.stop_card import StopCardRepository
from app.repositories.stop_card_photo import StopCardPhotoRepository
from app.repositories.user import UserRepository
from app.routers.deps import require_safety_engineer_or_admin
from app.schemas.stop_card import SafetyDecisionRequest, StopCardPublicResponse
from app.services.stop_card import StopCardService

router = APIRouter(prefix="/stop-cards", tags=["safety-engineer-stop-cards"])


def _service(db: AsyncSession = Depends(get_db)) -> StopCardService:
    return StopCardService(
        StopCardRepository(db),
        StopCardPhotoRepository(db),
        UserRepository(db),
    )


@router.get("", response_model=list[StopCardPublicResponse])
async def list_stop_cards(
    svc: StopCardService = Depends(_service),
    current_user: User = Depends(require_safety_engineer_or_admin),
):
    """Все карты на проверке ОТ и ТБ (+ история)"""
    if current_user.role.value == "admin":
        return await svc.repo.get_all()
    return await svc.get_filtered(
        statuses=[
            StopCardStatus.safety_check,
            StopCardStatus.approved,
            StopCardStatus.rejected,
        ],
    )


@router.get("/{stop_card_id}", response_model=StopCardPublicResponse)
async def get_stop_card(
    stop_card_id: int,
    svc: StopCardService = Depends(_service),
    _: User = Depends(require_safety_engineer_or_admin),
):
    try:
        return await svc.get_by_id(stop_card_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{stop_card_id}/approve", response_model=StopCardPublicResponse)
async def approve(
    stop_card_id: int,
    body: SafetyDecisionRequest,
    svc: StopCardService = Depends(_service),
    current_user: User = Depends(require_safety_engineer_or_admin),
):
    try:
        return await svc.safety_approve(stop_card_id, current_user.id, body.note)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{stop_card_id}/reject", response_model=StopCardPublicResponse)
async def reject(
    stop_card_id: int,
    body: SafetyDecisionRequest,
    svc: StopCardService = Depends(_service),
    current_user: User = Depends(require_safety_engineer_or_admin),
):
    try:
        return await svc.safety_reject(stop_card_id, current_user.id, body.note)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{stop_card_id}/revision", response_model=StopCardPublicResponse)
async def revision(
    stop_card_id: int,
    body: SafetyDecisionRequest,
    svc: StopCardService = Depends(_service),
    current_user: User = Depends(require_safety_engineer_or_admin),
):
    try:
        return await svc.safety_revision(stop_card_id, current_user.id, body.note)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
