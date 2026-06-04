from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Section(Base):
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="section")
    stop_cards: Mapped[list["StopCard"]] = relationship(back_populates="section")
