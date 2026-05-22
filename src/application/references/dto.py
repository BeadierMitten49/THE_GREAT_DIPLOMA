from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CreateCustomerDTO:
    name: str
    default_address: str
    contact: str = ""
    comment: str = ""


@dataclass(frozen=True)
class UpdateCustomerDTO:
    name: str
    default_address: str
    contact: str = ""
    comment: str = ""


@dataclass(frozen=True)
class CreateProductDTO:
    name: str
    units_per_box: int
    shelf_life_days: int
    critical_stock: int


@dataclass(frozen=True)
class UpdateProductDTO:
    name: str
    units_per_box: int
    shelf_life_days: int
    critical_stock: int


@dataclass(frozen=True)
class RecipeLineDTO:
    raw_material_id: int
    consumption_per_unit: Decimal
    waste_percentage: Decimal


@dataclass(frozen=True)
class CreateRawMaterialDTO:
    name: str
    unit: str
    shelf_life_days: int
    critical_stock: Decimal
    comment: str = ""


@dataclass(frozen=True)
class UpdateRawMaterialDTO:
    name: str
    unit: str
    shelf_life_days: int
    critical_stock: Decimal
    comment: str = ""


@dataclass(frozen=True)
class CreatePackagingDTO:
    name: str
    unit: str
    critical_stock: int
    comment: str = ""


@dataclass(frozen=True)
class UpdatePackagingDTO:
    name: str
    unit: str
    critical_stock: int
    comment: str = ""
