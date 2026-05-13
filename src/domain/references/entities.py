from dataclasses import dataclass, field
from decimal import Decimal

from src.domain.references.exceptions import InvalidFieldError
from src.domain.references.value_objects import RecipeLine


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
    id: int | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.name, "name")
        _require_non_empty(self.default_address, "default_address")

    def update(self, name: str, default_address: str) -> None:
        _require_non_empty(name, "name")
        _require_non_empty(default_address, "default_address")
        self.name = name
        self.default_address = default_address

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

    def set_recipe(self, lines: list[RecipeLine]) -> None:
        for line in lines:
            if line.consumption_per_unit <= 0:
                raise InvalidFieldError("consumption_per_unit", "must be greater than zero")
            if not (Decimal(0) <= line.waste_percentage <= Decimal(100)):
                raise InvalidFieldError("waste_percentage", "must be between 0 and 100")
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
    id: int | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.name, "name")
        _require_non_empty(self.unit, "unit")
        _require_positive_int(self.shelf_life_days, "shelf_life_days")
        _require_non_negative(self.critical_stock, "critical_stock")

    def update(self, name: str, unit: str, shelf_life_days: int, critical_stock: Decimal) -> None:
        _require_non_empty(name, "name")
        _require_non_empty(unit, "unit")
        _require_positive_int(shelf_life_days, "shelf_life_days")
        _require_non_negative(critical_stock, "critical_stock")
        self.name = name
        self.unit = unit
        self.shelf_life_days = shelf_life_days
        self.critical_stock = critical_stock

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
    id: int | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.name, "name")
        _require_non_empty(self.unit, "unit")
        _require_non_negative(self.critical_stock, "critical_stock")

    def update(self, name: str, unit: str, critical_stock: int) -> None:
        _require_non_empty(name, "name")
        _require_non_empty(unit, "unit")
        _require_non_negative(critical_stock, "critical_stock")
        self.name = name
        self.unit = unit
        self.critical_stock = critical_stock

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True
