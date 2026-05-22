from datetime import date
from decimal import Decimal

import pytest

from src.domain.shared.exceptions import InvalidFieldError
from src.domain.warehouse.entities import PackagingStock, ProductStock, RawMaterialStock


# ---------------------------------------------------------------------------
# RawMaterialStock.write_off
# ---------------------------------------------------------------------------


class TestRawMaterialStockAdjust:
    def _make(self, quantity: str = "100.000") -> RawMaterialStock:
        return RawMaterialStock(
            raw_material_id=1,
            quantity=Decimal(quantity),
            arrival_date=date(2026, 1, 1),
            expiry_date=date(2026, 6, 1),
            comment="original",
        )

    def test_adjust_sets_new_quantity(self):
        stock = self._make("100.000")
        stock.adjust(Decimal("75.000"), None)
        assert stock.quantity == Decimal("75.000")

    def test_adjust_updates_comment(self):
        stock = self._make()
        stock.adjust(Decimal("50.000"), "corrected")
        assert stock.comment == "corrected"

    def test_adjust_clears_comment_when_none(self):
        stock = self._make()
        stock.adjust(Decimal("50.000"), None)
        assert stock.comment is None

    def test_adjust_allows_zero_quantity(self):
        stock = self._make()
        stock.adjust(Decimal("0"), None)
        assert stock.quantity == Decimal("0")

    def test_adjust_negative_quantity_raises(self):
        stock = self._make()
        with pytest.raises(InvalidFieldError):
            stock.adjust(Decimal("-1"), None)


class TestRawMaterialStockWriteOff:
    def _make(self, quantity: str = "100.000") -> RawMaterialStock:
        return RawMaterialStock(
            raw_material_id=1,
            quantity=Decimal(quantity),
            arrival_date=date(2026, 1, 1),
            expiry_date=date(2026, 6, 1),
        )

    def test_write_off_reduces_quantity(self):
        stock = self._make("100.000")
        stock.write_off(Decimal("30.500"))
        assert stock.quantity == Decimal("69.500")

    def test_write_off_full_quantity(self):
        stock = self._make("50.000")
        stock.write_off(Decimal("50.000"))
        assert stock.quantity == Decimal("0")

    def test_write_off_exceeds_quantity_raises(self):
        stock = self._make("10.000")
        with pytest.raises(InvalidFieldError):
            stock.write_off(Decimal("10.001"))

    def test_write_off_zero_raises(self):
        stock = self._make()
        with pytest.raises(InvalidFieldError):
            stock.write_off(Decimal("0"))

    def test_write_off_negative_raises(self):
        stock = self._make()
        with pytest.raises(InvalidFieldError):
            stock.write_off(Decimal("-1"))


# ---------------------------------------------------------------------------
# PackagingStock.write_off
# ---------------------------------------------------------------------------


class TestPackagingStockWriteOff:
    def _make(self, quantity: int = 500) -> PackagingStock:
        return PackagingStock(packaging_id=1, quantity=quantity)

    def test_write_off_reduces_quantity(self):
        stock = self._make(500)
        stock.write_off(200)
        assert stock.quantity == 300

    def test_write_off_full_quantity(self):
        stock = self._make(100)
        stock.write_off(100)
        assert stock.quantity == 0

    def test_write_off_exceeds_quantity_raises(self):
        stock = self._make(10)
        with pytest.raises(InvalidFieldError):
            stock.write_off(11)

    def test_write_off_zero_raises(self):
        stock = self._make()
        with pytest.raises(InvalidFieldError):
            stock.write_off(0)

    def test_write_off_negative_raises(self):
        stock = self._make()
        with pytest.raises(InvalidFieldError):
            stock.write_off(-5)


# ---------------------------------------------------------------------------
# ProductStock.write_off
# ---------------------------------------------------------------------------


class TestProductStockAdjust:
    def _make(self, quantity: int = 100) -> ProductStock:
        return ProductStock(
            product_id=1,
            quantity=quantity,
            batch_number=1,
            batch_year=2026,
            arrival_date=date(2026, 1, 1),
            expiry_date=date(2026, 7, 1),
            comment="original",
        )

    def test_adjust_sets_new_quantity(self):
        stock = self._make(100)
        stock.adjust(75, None)
        assert stock.quantity == 75

    def test_adjust_updates_comment(self):
        stock = self._make()
        stock.adjust(50, "corrected")
        assert stock.comment == "corrected"

    def test_adjust_clears_comment_when_none(self):
        stock = self._make()
        stock.adjust(50, None)
        assert stock.comment is None

    def test_adjust_allows_zero_quantity(self):
        stock = self._make()
        stock.adjust(0, None)
        assert stock.quantity == 0

    def test_adjust_negative_quantity_raises(self):
        stock = self._make()
        with pytest.raises(InvalidFieldError):
            stock.adjust(-1, None)


class TestProductStockWriteOff:
    def _make(self, quantity: int = 1000) -> ProductStock:
        return ProductStock(
            product_id=1,
            quantity=quantity,
            batch_number=1,
            batch_year=2026,
            arrival_date=date(2026, 1, 1),
            expiry_date=date(2026, 7, 1),
        )

    def test_write_off_reduces_quantity(self):
        stock = self._make(1000)
        stock.write_off(300)
        assert stock.quantity == 700

    def test_write_off_full_quantity(self):
        stock = self._make(50)
        stock.write_off(50)
        assert stock.quantity == 0

    def test_write_off_exceeds_quantity_raises(self):
        stock = self._make(10)
        with pytest.raises(InvalidFieldError):
            stock.write_off(11)

    def test_write_off_zero_raises(self):
        stock = self._make()
        with pytest.raises(InvalidFieldError):
            stock.write_off(0)

    def test_write_off_negative_raises(self):
        stock = self._make()
        with pytest.raises(InvalidFieldError):
            stock.write_off(-1)
