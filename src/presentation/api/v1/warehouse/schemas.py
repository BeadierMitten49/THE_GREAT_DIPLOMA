from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# RawMaterialStock
# ---------------------------------------------------------------------------


class RawMaterialStockArrivalRequest(BaseModel):
    raw_material_id: int
    quantity: Decimal = Field(gt=0)
    arrival_date: date
    expiry_date: date
    comment: str | None = None


class RawMaterialStockWriteOffRequest(BaseModel):
    amount: Decimal = Field(gt=0)


class RawMaterialStockAdjustRequest(BaseModel):
    quantity: Decimal = Field(ge=0)
    comment: str | None = None


class RawMaterialStockResponse(BaseModel):
    id: int
    raw_material_id: int
    quantity: Decimal
    reserved: Decimal
    arrival_date: date
    expiry_date: date
    comment: str | None


# ---------------------------------------------------------------------------
# PackagingStock
# ---------------------------------------------------------------------------


class PackagingStockArrivalRequest(BaseModel):
    packaging_id: int
    quantity: int = Field(gt=0)
    comment: str | None = None


class PackagingStockWriteOffRequest(BaseModel):
    amount: int = Field(gt=0)


class PackagingStockResponse(BaseModel):
    id: int
    packaging_id: int
    quantity: int
    comment: str | None


# ---------------------------------------------------------------------------
# ProductStock
# ---------------------------------------------------------------------------


class ProductStockArrivalRequest(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    arrival_date: date
    expiry_date: date
    comment: str | None = None


class ProductStockAcceptFromTaskRequest(BaseModel):
    task_id: int


class ProductStockAdjustRequest(BaseModel):
    quantity: int = Field(ge=0)
    comment: str | None = None


class ProductStockWriteOffRequest(BaseModel):
    amount: int = Field(gt=0)


class ProductStockResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    reserved: int
    reserved_orders: list[int]
    batch_number: int
    batch_year: int
    arrival_date: date
    expiry_date: date
    comment: str | None
