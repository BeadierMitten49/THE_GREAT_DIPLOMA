from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db.models import Base, intpk, str_nn


class RawMaterialStockModel(Base):
    __tablename__ = "raw_material_stock"

    id: Mapped[intpk]
    raw_material_id: Mapped[int] = mapped_column(
        ForeignKey("raw_materials_catalog.id"), nullable=False
    )
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    arrival_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)


class PackagingStockModel(Base):
    __tablename__ = "packaging_stock"

    id: Mapped[intpk]
    packaging_id: Mapped[int] = mapped_column(
        ForeignKey("packaging_catalog.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)


class ProductStockModel(Base):
    __tablename__ = "products_stock"

    id: Mapped[intpk]
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    batch_number: Mapped[int] = mapped_column(Integer, nullable=False)
    batch_year: Mapped[int] = mapped_column(Integer, nullable=False)
    arrival_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("product_id", "batch_number", "batch_year", name="uq_product_batch"),
    )
