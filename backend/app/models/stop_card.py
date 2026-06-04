import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StopCardStatus(str, enum.Enum):
    issued = "issued"
    acknowledged = "acknowledged"
    closed = "closed"
    disputed = "disputed"


class StopCard(Base):
    __tablename__ = "stop_cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    violator_name: Mapped[str] = mapped_column(Text, nullable=False)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[StopCardStatus] = mapped_column(default=StopCardStatus.issued, nullable=False)
    dispute_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    reporter: Mapped["User"] = relationship(back_populates="stop_cards")
    section: Mapped["Section"] = relationship(back_populates="stop_cards")
    photos: Mapped[list["StopCardPhoto"]] = relationship(back_populates="stop_card")
