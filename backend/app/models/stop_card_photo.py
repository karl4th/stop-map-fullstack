from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StopCardPhoto(Base):
    __tablename__ = "stop_card_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    stop_card_id: Mapped[int] = mapped_column(ForeignKey("stop_cards.id"), nullable=False)
    minio_key: Mapped[str] = mapped_column(String(512), nullable=False)
    photo_type: Mapped[str] = mapped_column(String(10), nullable=False, default="before")  # "before" | "after"
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    stop_card: Mapped["StopCard"] = relationship(back_populates="photos")
