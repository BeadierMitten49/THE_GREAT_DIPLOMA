from decimal import Decimal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------


class CreateCustomerRequest(BaseModel):
    name: str
    default_address: str


class UpdateCustomerRequest(BaseModel):
    name: str
    default_address: str


class CustomerResponse(BaseModel):
    id: int
    name: str
    default_address: str
    is_active: bool


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------


class CreateProductRequest(BaseModel):
    name: str
    units_per_box: int = Field(gt=0)
    shelf_life_days: int = Field(gt=0)
    critical_stock: int = Field(ge=0)


class UpdateProductRequest(BaseModel):
    name: str
    units_per_box: int = Field(gt=0)
    shelf_life_days: int = Field(gt=0)
    critical_stock: int = Field(ge=0)


class RecipeLineRequest(BaseModel):
    raw_material_id: int
    consumption_per_unit: Decimal = Field(gt=0)
    waste_percentage: Decimal = Field(ge=0, le=100)


class SetRecipeRequest(BaseModel):
    lines: list[RecipeLineRequest]


class RecipeLineResponse(BaseModel):
    id: int
    raw_material_id: int
    consumption_per_unit: Decimal
    waste_percentage: Decimal


class ProductResponse(BaseModel):
    id: int
    name: str
    units_per_box: int
    shelf_life_days: int
    critical_stock: int
    is_active: bool
    recipe: list[RecipeLineResponse]


# ---------------------------------------------------------------------------
# RawMaterialCatalog
# ---------------------------------------------------------------------------


class CreateRawMaterialRequest(BaseModel):
    name: str
    unit: str
    shelf_life_days: int = Field(gt=0)
    critical_stock: Decimal = Field(ge=0)


class UpdateRawMaterialRequest(BaseModel):
    name: str
    unit: str
    shelf_life_days: int = Field(gt=0)
    critical_stock: Decimal = Field(ge=0)


class RawMaterialResponse(BaseModel):
    id: int
    name: str
    unit: str
    shelf_life_days: int
    critical_stock: Decimal
    is_active: bool


# ---------------------------------------------------------------------------
# PackagingCatalog
# ---------------------------------------------------------------------------


class CreatePackagingRequest(BaseModel):
    name: str
    unit: str
    critical_stock: int = Field(ge=0)


class UpdatePackagingRequest(BaseModel):
    name: str
    unit: str
    critical_stock: int = Field(ge=0)


class PackagingResponse(BaseModel):
    id: int
    name: str
    unit: str
    critical_stock: int
    is_active: bool
