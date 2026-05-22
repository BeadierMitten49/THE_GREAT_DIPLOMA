from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class RawMaterialStockArrivalDTO:
    raw_material_id: int
    quantity: Decimal
    arrival_date: date
    expiry_date: date
    comment: str | None


@dataclass(frozen=True)
class RawMaterialStockWriteOffDTO:
    stock_id: int
    amount: Decimal


@dataclass(frozen=True)
class RawMaterialStockAdjustDTO:
    stock_id: int
    quantity: Decimal
    comment: str | None


@dataclass(frozen=True)
class PackagingStockArrivalDTO:
    packaging_id: int
    quantity: int
    comment: str | None


@dataclass(frozen=True)
class PackagingStockWriteOffDTO:
    stock_id: int
    amount: int


@dataclass(frozen=True)
class ProductStockArrivalDTO:
    product_id: int
    quantity: int
    arrival_date: date
    expiry_date: date
    comment: str | None


@dataclass(frozen=True)
class ProductStockAdjustDTO:
    stock_id: int
    quantity: int
    comment: str | None


@dataclass(frozen=True)
class ProductStockWriteOffDTO:
    stock_id: int
    amount: int
