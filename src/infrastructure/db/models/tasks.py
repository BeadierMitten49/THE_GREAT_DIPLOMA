from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db.models import Base, intpk, str_nn


class ProductionTaskModel(Base):
    __tablename__ = "production_tasks"

    id: Mapped[intpk]
    task_type: Mapped[str_nn]
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    executor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str_nn]
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    actual_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TaskStopModel(Base):
    __tablename__ = "task_stops"

    id: Mapped[intpk]
    task_id: Mapped[int] = mapped_column(ForeignKey("production_tasks.id"), nullable=False)
    reason: Mapped[str_nn]
    stopped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TaskCompletionModel(Base):
    __tablename__ = "task_completions"

    __table_args__ = (UniqueConstraint("task_id", name="uq_task_completions_task_id"),)

    id: Mapped[intpk]
    task_id: Mapped[int] = mapped_column(ForeignKey("production_tasks.id"), nullable=False)
    actual_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TaskCompletionConsumptionModel(Base):
    __tablename__ = "task_completion_consumption"

    id: Mapped[intpk]
    completion_id: Mapped[int] = mapped_column(ForeignKey("task_completions.id"), nullable=False)
    raw_material_id: Mapped[int] = mapped_column(
        ForeignKey("raw_materials_catalog.id"), nullable=False
    )
    planned_qty: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    actual_qty: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    waste_qty: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)


class RawMaterialReservationModel(Base):
    __tablename__ = "raw_material_reservations"

    id: Mapped[intpk]
    stock_id: Mapped[int] = mapped_column(ForeignKey("raw_material_stock.id"), nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("production_tasks.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
