from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.domain.shared.exceptions import InvalidFieldError


@dataclass
class RawMaterialStock:
    raw_material_id: int
    quantity: Decimal
    arrival_date: date
    expiry_date: date
    id: int | None = None
    comment: str | None = None

    def write_off(self, amount: Decimal) -> None:
        if amount <= 0:
            raise InvalidFieldError("amount", "must be > 0")
        if amount > self.quantity:
            raise InvalidFieldError("amount", "exceeds available quantity")
        self.quantity -= amount

    def adjust(self, new_quantity: Decimal, comment: str | None) -> None:
        if new_quantity < 0:
            raise InvalidFieldError("new_quantity", "must be >= 0")
        self.quantity = new_quantity
        self.comment = comment


@dataclass
class PackagingStock:
    packaging_id: int
    quantity: int
    id: int | None = None
    comment: str | None = None

    def write_off(self, amount: int) -> None:
        if amount <= 0:
            raise InvalidFieldError("amount", "must be > 0")
        if amount > self.quantity:
            raise InvalidFieldError("amount", "exceeds available quantity")
        self.quantity -= amount


@dataclass
class ProductStock:
    product_id: int
    quantity: int
    batch_number: int
    batch_year: int
    arrival_date: date
    expiry_date: date
    id: int | None = None
    comment: str | None = None

    def adjust(self, new_quantity: int, comment: str | None) -> None:
        if new_quantity < 0:
            raise InvalidFieldError("new_quantity", "must be >= 0")
        self.quantity = new_quantity
        self.comment = comment

    def write_off(self, amount: int) -> None:
        if amount <= 0:
            raise InvalidFieldError("amount", "must be > 0")
        if amount > self.quantity:
            raise InvalidFieldError("amount", "exceeds available quantity")
        self.quantity -= amount
