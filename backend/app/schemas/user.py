from datetime import datetime

from pydantic import BaseModel

from app.models.user import UserRole, UserStatus


class UserResponse(BaseModel):
    id: int
    telegram_id: int | None
    full_name: str
    phone: str | None
    role: UserRole
    status: UserStatus
    section_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignRoleRequest(BaseModel):
    role: UserRole
    password: str | None = None
    section_id: int | None = None
