from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db.models import Base, intpk, str_nn


class DeliveryModel(Base):
    __tablename__ = "deliveries"
    __table_args__ = (UniqueConstraint("order_id"),)

    id: Mapped[intpk]
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    executor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str_nn]
    planned_date: Mapped[date] = mapped_column(Date, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String, nullable=True)
