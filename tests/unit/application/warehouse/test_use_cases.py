from datetime import date
from decimal import Decimal

import pytest

from src.application.warehouse.dto import (
    PackagingStockArrivalDTO,
    PackagingStockWriteOffDTO,
    ProductStockArrivalDTO,
    ProductStockWriteOffDTO,
    RawMaterialStockAdjustDTO,
    RawMaterialStockArrivalDTO,
    RawMaterialStockWriteOffDTO,
)
from src.application.warehouse.exceptions import NotFoundError
from src.application.warehouse.use_cases import (
    get_packaging_stock,
    get_packaging_stocks,
    get_packaging_stocks_by_packaging,
    get_product_stock,
    get_product_stocks,
    get_product_stocks_by_product,
    get_raw_material_stock,
    get_raw_material_stocks,
    get_raw_material_stocks_by_material,
    packaging_stock_arrival,
    packaging_stock_write_off,
    product_stock_arrival,
    product_stock_write_off,
    raw_material_stock_adjust,
    raw_material_stock_arrival,
    raw_material_stock_write_off,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# RawMaterialStock
# ---------------------------------------------------------------------------


class TestGetRawMaterialStock:
    async def test_returns_entity_when_found(self, raw_material_stock_repo, saved_raw_material_stock):
        result = await get_raw_material_stock(saved_raw_material_stock.id, raw_material_stock_repo)
        assert result.raw_material_id == 1
        assert result.quantity == Decimal("100.0")

    async def test_raises_not_found_when_missing(self, raw_material_stock_repo):
        with pytest.raises(NotFoundError):
            await get_raw_material_stock(999, raw_material_stock_repo)


class TestGetRawMaterialStocks:
    async def test_returns_all_stocks(self, raw_material_stock_repo, saved_raw_material_stock):
        result = await get_raw_material_stocks(raw_material_stock_repo)
        assert len(result) == 1

    async def test_returns_empty_list_when_none(self, raw_material_stock_repo):
        result = await get_raw_material_stocks(raw_material_stock_repo)
        assert result == []


class TestGetRawMaterialStocksByMaterial:
    async def test_returns_stocks_for_given_material(self, raw_material_stock_repo, saved_raw_material_stock):
        result = await get_raw_material_stocks_by_material(1, raw_material_stock_repo)
        assert len(result) == 1

    async def test_returns_empty_for_unknown_material(self, raw_material_stock_repo, saved_raw_material_stock):
        result = await get_raw_material_stocks_by_material(999, raw_material_stock_repo)
        assert result == []


class TestRawMaterialStockArrival:
    async def test_creates_stock_and_returns_id(self, raw_material_stock_repo):
        dto = RawMaterialStockArrivalDTO(
            raw_material_id=1,
            quantity=Decimal("50.0"),
            arrival_date=date(2026, 5, 1),
            expiry_date=date(2026, 12, 31),
            comment=None,
        )
        id_ = await raw_material_stock_arrival(dto, raw_material_stock_repo)
        assert isinstance(id_, int)
        saved = await raw_material_stock_repo.get_by_id(id_)
        assert saved.quantity == Decimal("50.0")


class TestRawMaterialStockAdjust:
    async def test_sets_new_quantity(self, raw_material_stock_repo, saved_raw_material_stock):
        dto = RawMaterialStockAdjustDTO(
            stock_id=saved_raw_material_stock.id,
            quantity=Decimal("42.0"),
            comment="fixed",
        )
        await raw_material_stock_adjust(dto, raw_material_stock_repo)
        updated = await raw_material_stock_repo.get_by_id(saved_raw_material_stock.id)
        assert updated.quantity == Decimal("42.0")
        assert updated.comment == "fixed"

    async def test_raises_not_found_when_stock_missing(self, raw_material_stock_repo):
        dto = RawMaterialStockAdjustDTO(stock_id=999, quantity=Decimal("1.0"), comment=None)
        with pytest.raises(NotFoundError):
            await raw_material_stock_adjust(dto, raw_material_stock_repo)


class TestRawMaterialStockWriteOff:
    async def test_reduces_quantity(self, raw_material_stock_repo, saved_raw_material_stock):
        dto = RawMaterialStockWriteOffDTO(stock_id=saved_raw_material_stock.id, amount=Decimal("30.0"))
        await raw_material_stock_write_off(dto, raw_material_stock_repo)
        updated = await raw_material_stock_repo.get_by_id(saved_raw_material_stock.id)
        assert updated.quantity == Decimal("70.0")

    async def test_raises_not_found_when_stock_missing(self, raw_material_stock_repo):
        dto = RawMaterialStockWriteOffDTO(stock_id=999, amount=Decimal("1.0"))
        with pytest.raises(NotFoundError):
            await raw_material_stock_write_off(dto, raw_material_stock_repo)


# ---------------------------------------------------------------------------
# PackagingStock
# ---------------------------------------------------------------------------


class TestGetPackagingStock:
    async def test_returns_entity_when_found(self, packaging_stock_repo, saved_packaging_stock):
        result = await get_packaging_stock(saved_packaging_stock.id, packaging_stock_repo)
        assert result.packaging_id == 1
        assert result.quantity == 500

    async def test_raises_not_found_when_missing(self, packaging_stock_repo):
        with pytest.raises(NotFoundError):
            await get_packaging_stock(999, packaging_stock_repo)


class TestGetPackagingStocks:
    async def test_returns_all_stocks(self, packaging_stock_repo, saved_packaging_stock):
        result = await get_packaging_stocks(packaging_stock_repo)
        assert len(result) == 1

    async def test_returns_empty_list_when_none(self, packaging_stock_repo):
        result = await get_packaging_stocks(packaging_stock_repo)
        assert result == []


class TestGetPackagingStocksByPackaging:
    async def test_returns_stocks_for_given_packaging(self, packaging_stock_repo, saved_packaging_stock):
        result = await get_packaging_stocks_by_packaging(1, packaging_stock_repo)
        assert len(result) == 1

    async def test_returns_empty_for_unknown_packaging(self, packaging_stock_repo, saved_packaging_stock):
        result = await get_packaging_stocks_by_packaging(999, packaging_stock_repo)
        assert result == []


class TestPackagingStockArrival:
    async def test_creates_stock_and_returns_id(self, packaging_stock_repo):
        dto = PackagingStockArrivalDTO(packaging_id=2, quantity=200, comment=None)
        id_ = await packaging_stock_arrival(dto, packaging_stock_repo)
        assert isinstance(id_, int)
        saved = await packaging_stock_repo.get_by_id(id_)
        assert saved.quantity == 200


class TestPackagingStockWriteOff:
    async def test_reduces_quantity(self, packaging_stock_repo, saved_packaging_stock):
        dto = PackagingStockWriteOffDTO(stock_id=saved_packaging_stock.id, amount=100)
        await packaging_stock_write_off(dto, packaging_stock_repo)
        updated = await packaging_stock_repo.get_by_id(saved_packaging_stock.id)
        assert updated.quantity == 400

    async def test_raises_not_found_when_stock_missing(self, packaging_stock_repo):
        dto = PackagingStockWriteOffDTO(stock_id=999, amount=1)
        with pytest.raises(NotFoundError):
            await packaging_stock_write_off(dto, packaging_stock_repo)


# ---------------------------------------------------------------------------
# ProductStock
# ---------------------------------------------------------------------------


class TestGetProductStock:
    async def test_returns_entity_when_found(self, product_stock_repo, saved_product_stock):
        result = await get_product_stock(saved_product_stock.id, product_stock_repo)
        assert result.product_id == 1
        assert result.quantity == 100

    async def test_raises_not_found_when_missing(self, product_stock_repo):
        with pytest.raises(NotFoundError):
            await get_product_stock(999, product_stock_repo)


class TestGetProductStocks:
    async def test_returns_all_stocks(self, product_stock_repo, saved_product_stock):
        result = await get_product_stocks(product_stock_repo)
        assert len(result) == 1

    async def test_returns_empty_list_when_none(self, product_stock_repo):
        result = await get_product_stocks(product_stock_repo)
        assert result == []


class TestGetProductStocksByProduct:
    async def test_returns_stocks_for_given_product(self, product_stock_repo, saved_product_stock):
        result = await get_product_stocks_by_product(1, product_stock_repo)
        assert len(result) == 1

    async def test_returns_empty_for_unknown_product(self, product_stock_repo, saved_product_stock):
        result = await get_product_stocks_by_product(999, product_stock_repo)
        assert result == []


class TestProductStockArrival:
    async def test_first_arrival_of_year_gets_batch_number_1(self, product_stock_repo):
        dto = ProductStockArrivalDTO(
            product_id=1,
            quantity=50,
            arrival_date=date(2026, 5, 1),
            expiry_date=date(2026, 11, 1),
            comment=None,
        )
        id_ = await product_stock_arrival(dto, product_stock_repo)
        saved = await product_stock_repo.get_by_id(id_)
        assert saved.batch_number == 1
        assert saved.batch_year == 2026

    async def test_increments_batch_number_within_same_year(self, product_stock_repo, saved_product_stock):
        dto = ProductStockArrivalDTO(
            product_id=2,
            quantity=50,
            arrival_date=date(2026, 5, 1),
            expiry_date=date(2026, 11, 1),
            comment=None,
        )
        id_ = await product_stock_arrival(dto, product_stock_repo)
        saved = await product_stock_repo.get_by_id(id_)
        assert saved.batch_number == 2  # saved_product_stock already has batch_number=1 in 2026


class TestProductStockWriteOff:
    async def test_reduces_quantity(self, product_stock_repo, saved_product_stock):
        dto = ProductStockWriteOffDTO(stock_id=saved_product_stock.id, amount=40)
        await product_stock_write_off(dto, product_stock_repo)
        updated = await product_stock_repo.get_by_id(saved_product_stock.id)
        assert updated.quantity == 60

    async def test_raises_not_found_when_stock_missing(self, product_stock_repo):
        dto = ProductStockWriteOffDTO(stock_id=999, amount=1)
        with pytest.raises(NotFoundError):
            await product_stock_write_off(dto, product_stock_repo)
