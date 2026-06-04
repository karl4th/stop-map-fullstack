from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.repositories.section import SectionRepository
from app.routers.deps import require_admin
from app.schemas.section import SectionCreate, SectionResponse, SectionUpdate
from app.services.section import SectionService

router = APIRouter(prefix="/sections", tags=["admin-sections"])


def _service(db: AsyncSession = Depends(get_db)) -> SectionService:
    return SectionService(SectionRepository(db))


@router.get("", response_model=list[SectionResponse])
async def list_sections(
    svc: SectionService = Depends(_service),
    _: User = Depends(require_admin),
):
    return await svc.get_all()


@router.post("", response_model=SectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section(
    body: SectionCreate,
    svc: SectionService = Depends(_service),
    _: User = Depends(require_admin),
):
    try:
        return await svc.create(body.name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.put("/{section_id}", response_model=SectionResponse)
async def update_section(
    section_id: int,
    body: SectionUpdate,
    svc: SectionService = Depends(_service),
    _: User = Depends(require_admin),
):
    try:
        return await svc.update(section_id, body.name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(
    section_id: int,
    svc: SectionService = Depends(_service),
    _: User = Depends(require_admin),
):
    try:
        await svc.delete(section_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
