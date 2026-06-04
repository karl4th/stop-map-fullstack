from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import authenticate, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await UserRepository(db).get_by_phone(body.phone)
    try:
        user = await authenticate(body.phone, body.password, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    token = create_access_token(user.id, user.role.value)
    return TokenResponse(access_token=token)
