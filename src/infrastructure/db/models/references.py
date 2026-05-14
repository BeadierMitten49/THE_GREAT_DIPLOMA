from decimal import Decimal
from typing import Annotated

from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.models import Base, bool_active, intpk, str_nn


class CustomerModel(Base):
    __tablename__ = "customers"

    id: Mapped[intpk]
    name: Mapped[str_nn]
    default_address: Mapped[str_nn]
    is_active: Mapped[bool_active]


class ProductModel(Base):
    __tablename__ = "products"

    id: Mapped[intpk]
    name: Mapped[str_nn]
    units_per_box: Mapped[int] = mapped_column(Integer, nullable=False)
    shelf_life_days: Mapped[int] = mapped_column(Integer, nullable=False)
    critical_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool_active]

    recipe: Mapped[list["RecipeLineModel"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class RawMaterialCatalogModel(Base):
    __tablename__ = "raw_materials_catalog"

    id: Mapped[intpk]
    name: Mapped[str_nn]
    unit: Mapped[str_nn]
    shelf_life_days: Mapped[int] = mapped_column(Integer, nullable=False)
    critical_stock: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    is_active: Mapped[bool_active]


class PackagingCatalogModel(Base):
    __tablename__ = "packaging_catalog"

    id: Mapped[intpk]
    name: Mapped[str_nn]
    unit: Mapped[str_nn]
    critical_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool_active]


class RecipeLineModel(Base):
    __tablename__ = "recipes"

    id: Mapped[intpk]
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    raw_material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("raw_materials_catalog.id"), nullable=False
    )
    consumption_per_unit: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    waste_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    product: Mapped["ProductModel"] = relationship(back_populates="recipe")
