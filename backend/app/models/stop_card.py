import enum
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StopCardStatus(str, enum.Enum):
    created = "created"           # Создана (работник подал)
    under_review = "under_review" # На рассмотрении (менеджер принял)
    in_progress = "in_progress"   # В работе (менеджер устраняет / после доработки)
    safety_check = "safety_check" # Проверка ОТ и ТБ
    approved = "approved"         # Разрешено к работе
    rejected = "rejected"         # Запрещено (инженер отклонил)
    closed = "closed"             # Закрыто (финальное состояние)


class StopCard(Base):
    __tablename__ = "stop_cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    violator_name: Mapped[str] = mapped_column(Text, nullable=False)
    violator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[StopCardStatus] = mapped_column(
        sa.Enum(StopCardStatus, name="stopcard_status"),
        default=StopCardStatus.created,
        nullable=False,
    )

    # Менеджер — принятие
    acknowledged_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Менеджер — устранение
    fix_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    fixed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    fixed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Инженер ОТ и ТБ — решение
    safety_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    safety_checked_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    safety_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    reporter: Mapped["User"] = relationship(back_populates="stop_cards", foreign_keys=[reporter_id])
    violator: Mapped["User | None"] = relationship(foreign_keys=[violator_id])
    section: Mapped["Section"] = relationship(back_populates="stop_cards")
    acknowledged_by: Mapped["User | None"] = relationship(foreign_keys=[acknowledged_by_id])
    fixed_by: Mapped["User | None"] = relationship(foreign_keys=[fixed_by_id])
    safety_checked_by: Mapped["User | None"] = relationship(foreign_keys=[safety_checked_by_id])
    photos: Mapped[list["StopCardPhoto"]] = relationship(back_populates="stop_card")
