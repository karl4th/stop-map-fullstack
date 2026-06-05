from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.stop_card import StopCardStatus
from app.models.user import User
from app.repositories.stop_card import StopCardRepository
from app.repositories.stop_card_photo import StopCardPhotoRepository
from app.repositories.user import UserRepository
from app.routers.deps import require_admin
from app.schemas.stop_card import StopCardResponse
from app.services.stop_card import StopCardService

router = APIRouter(prefix="/stop-cards", tags=["admin-stop-cards"])


def _service(db: AsyncSession = Depends(get_db)) -> StopCardService:
    return StopCardService(
        StopCardRepository(db),
        StopCardPhotoRepository(db),
        UserRepository(db),
    )


@router.get("", response_model=list[StopCardResponse])
async def list_stop_cards(
    section_id: int | None = Query(None),
    card_status: StopCardStatus | None = Query(None, alias="status"),
    year: int | None = Query(None),
    month: int | None = Query(None),
    svc: StopCardService = Depends(_service),
    _: User = Depends(require_admin),
):
    if year and month:
        cards = await svc.get_by_month(year, month)
    elif section_id:
        cards = await svc.get_by_section(section_id)
    else:
        cards = await svc.repo.get_all()

    if year and month and section_id:
        cards = [c for c in cards if c.section_id == section_id]
    if card_status:
        cards = [c for c in cards if c.status == card_status]
    return cards


@router.get("/{stop_card_id}", response_model=StopCardResponse)
async def get_stop_card(
    stop_card_id: int,
    svc: StopCardService = Depends(_service),
    _: User = Depends(require_admin),
):
    try:
        return await svc.get_by_id(stop_card_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{stop_card_id}/close", response_model=StopCardResponse)
async def close_stop_card(
    stop_card_id: int,
    svc: StopCardService = Depends(_service),
    _: User = Depends(require_admin),
):
    try:
        return await svc.close(stop_card_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
