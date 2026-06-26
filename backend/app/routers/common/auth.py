from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import authenticate, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user = await UserRepository(db).get_by_phone(body.phone)
    try:
        user = await authenticate(body.phone, body.password, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    token = create_access_token(user.id, user.role.value)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="strict",
        max_age=24 * 60 * 60,
        path="/",
    )
    return TokenResponse(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        path="/",
        secure=settings.APP_ENV == "production",
        httponly=True,
        samesite="strict",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
