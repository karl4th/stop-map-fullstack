import enum
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    worker = "worker"
    manager = "manager"
    safety_engineer = "safety_engineer"
    admin = "admin"


class UserStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    blocked = "blocked"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    section_id: Mapped[int | None] = mapped_column(ForeignKey("sections.id"), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        sa.Enum(UserRole, name="userrole"),
        default=UserRole.worker,
        nullable=False,
    )
    status: Mapped[UserStatus] = mapped_column(
        sa.Enum(UserStatus, name="userstatus"),
        default=UserStatus.active,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    section: Mapped["Section"] = relationship(back_populates="users")
    stop_cards: Mapped[list["StopCard"]] = relationship(back_populates="reporter", foreign_keys="StopCard.reporter_id")
