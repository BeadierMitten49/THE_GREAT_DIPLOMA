from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db.models import Base, intpk, str_nn


class NotificationModel(Base):
    __tablename__ = "notifications"

    id: Mapped[intpk]
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    event_type: Mapped[str_nn]
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str_nn]
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    related_entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    related_entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
