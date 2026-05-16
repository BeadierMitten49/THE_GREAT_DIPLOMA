from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db.models import Base, intpk, str_nn


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[intpk]
    number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    delivery_address: Mapped[str_nn]
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str_nn]
    delivery_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[intpk]
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)


class ProductReservationModel(Base):
    __tablename__ = "product_reservations"

    id: Mapped[intpk]
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    stock_id: Mapped[int] = mapped_column(ForeignKey("products_stock.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
