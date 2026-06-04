from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.models.user import User
from app.repositories.stop_card import StopCardRepository
from app.repositories.stop_card_photo import StopCardPhotoRepository
from app.repositories.user import UserRepository
from app.routers.deps import require_manager_or_admin
from app.schemas.stop_card import DisputeRequest, StopCardResponse
from app.services.stop_card import StopCardService

router = APIRouter(prefix="/stop-cards", tags=["manager-stop-cards"])


def _service(db: AsyncSession = Depends(get_db)) -> StopCardService:
    return StopCardService(
        StopCardRepository(db),
        StopCardPhotoRepository(db),
        UserRepository(db),
    )


def _assert_section(card, current_user: User) -> None:
    if card.section_id != current_user.section_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этой стоп-карте")


@router.get("", response_model=list[StopCardResponse])
async def list_stop_cards(
    svc: StopCardService = Depends(_service),
    current_user: User = Depends(require_manager_or_admin),
):
    return await svc.get_by_section(current_user.section_id)


@router.get("/{stop_card_id}", response_model=StopCardResponse)
async def get_stop_card(
    stop_card_id: int,
    svc: StopCardService = Depends(_service),
    current_user: User = Depends(require_manager_or_admin),
):
    try:
        card = await svc.get_by_id(stop_card_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    _assert_section(card, current_user)
    return card


@router.patch("/{stop_card_id}/acknowledge", response_model=StopCardResponse)
async def acknowledge(
    stop_card_id: int,
    svc: StopCardService = Depends(_service),
    current_user: User = Depends(require_manager_or_admin),
):
    try:
        card = await svc.get_by_id(stop_card_id)
        _assert_section(card, current_user)
        return await svc.acknowledge(stop_card_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{stop_card_id}/close", response_model=StopCardResponse)
async def close(
    stop_card_id: int,
    svc: StopCardService = Depends(_service),
    current_user: User = Depends(require_manager_or_admin),
):
    try:
        card = await svc.get_by_id(stop_card_id)
        _assert_section(card, current_user)
        return await svc.close(stop_card_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{stop_card_id}/dispute", response_model=StopCardResponse)
async def dispute(
    stop_card_id: int,
    body: DisputeRequest,
    svc: StopCardService = Depends(_service),
    current_user: User = Depends(require_manager_or_admin),
):
    try:
        card = await svc.get_by_id(stop_card_id)
        _assert_section(card, current_user)
        return await svc.dispute(stop_card_id, body.reason)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


