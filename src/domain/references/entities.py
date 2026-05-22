from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal

from src.domain.references.exceptions import InvalidFieldError


@dataclass
class RecipeLine:
    raw_material_id: int
    consumption_per_unit: Decimal
    waste_percentage: Decimal  # 0..100
    id: int | None = None

    def __post_init__(self) -> None:
        if self.consumption_per_unit <= 0:
            raise InvalidFieldError("consumption_per_unit", "must be greater than zero")
        if not (Decimal(0) <= self.waste_percentage <= Decimal(100)):
            raise InvalidFieldError("waste_percentage", "must be between 0 and 100")


def _require_positive_int(value: int, field_name: str) -> None:
    if value <= 0:
        raise InvalidFieldError(field_name, "must be greater than zero")


def _require_non_negative(value: int | Decimal, field_name: str) -> None:
    if value < 0:
        raise InvalidFieldError(field_name, "must be non-negative")


def _require_non_empty(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise InvalidFieldError(field_name, "must not be empty")


@dataclass
class Customer:
    name: str
    default_address: str
    is_active: bool = True
    contact: str = ""
    comment: str = ""
    id: int | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.name, "name")
        _require_non_empty(self.default_address, "default_address")

    def update(self, name: str, default_address: str, contact: str = "", comment: str = "") -> None:
        _require_non_empty(name, "name")
        _require_non_empty(default_address, "default_address")
        self.name = name
        self.default_address = default_address
        self.contact = contact
        self.comment = comment

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True


@dataclass
class Product:
    name: str
    units_per_box: int
    shelf_life_days: int
    critical_stock: int
    is_active: bool = True
    recipe: list[RecipeLine] = field(default_factory=list)
    id: int | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.name, "name")
        _require_positive_int(self.units_per_box, "units_per_box")
        _require_positive_int(self.shelf_life_days, "shelf_life_days")
        _require_non_negative(self.critical_stock, "critical_stock")

    def update(self, name: str, units_per_box: int, shelf_life_days: int, critical_stock: int) -> None:
        _require_non_empty(name, "name")
        _require_positive_int(units_per_box, "units_per_box")
        _require_positive_int(shelf_life_days, "shelf_life_days")
        _require_non_negative(critical_stock, "critical_stock")
        self.name = name
        self.units_per_box = units_per_box
        self.shelf_life_days = shelf_life_days
        self.critical_stock = critical_stock

    def set_recipe(self, lines: Iterable[RecipeLine]) -> None:
        self.recipe = list(lines)

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True


@dataclass
class RawMaterialCatalog:
    name: str
    unit: str
    shelf_life_days: int
    critical_stock: Decimal
    is_active: bool = True
    comment: str = ""
    id: int | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.name, "name")
        _require_non_empty(self.unit, "unit")
        _require_positive_int(self.shelf_life_days, "shelf_life_days")
        _require_non_negative(self.critical_stock, "critical_stock")

    def update(self, name: str, unit: str, shelf_life_days: int, critical_stock: Decimal, comment: str = "") -> None:
        _require_non_empty(name, "name")
        _require_non_empty(unit, "unit")
        _require_positive_int(shelf_life_days, "shelf_life_days")
        _require_non_negative(critical_stock, "critical_stock")
        self.name = name
        self.unit = unit
        self.shelf_life_days = shelf_life_days
        self.critical_stock = critical_stock
        self.comment = comment

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True


@dataclass
class PackagingCatalog:
    name: str
    unit: str
    critical_stock: int
    is_active: bool = True
    comment: str = ""
    id: int | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.name, "name")
        _require_non_empty(self.unit, "unit")
        _require_non_negative(self.critical_stock, "critical_stock")

    def update(self, name: str, unit: str, critical_stock: int, comment: str = "") -> None:
        _require_non_empty(name, "name")
        _require_non_empty(unit, "unit")
        _require_non_negative(critical_stock, "critical_stock")
        self.name = name
        self.unit = unit
        self.critical_stock = critical_stock
        self.comment = comment

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True
