from datetime import date
from decimal import Decimal

import pytest

from src.domain.warehouse.entities import PackagingStock, ProductStock, RawMaterialStock
from src.infrastructure.db.repositories.warehouse import (
    PackagingStockRepository,
    ProductStockRepository,
    RawMaterialStockRepository,
)

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_raw_material_stock(
    raw_material_id: int = 1,
    quantity: str = "50.000",
    arrival_date: date = date(2026, 1, 1),
    expiry_date: date = date(2026, 6, 1),
    comment: str | None = None,
) -> RawMaterialStock:
    return RawMaterialStock(
        raw_material_id=raw_material_id,
        quantity=Decimal(quantity),
        arrival_date=arrival_date,
        expiry_date=expiry_date,
        comment=comment,
    )


def make_packaging_stock(
    packaging_id: int = 1,
    quantity: int = 500,
    comment: str | None = None,
) -> PackagingStock:
    return PackagingStock(packaging_id=packaging_id, quantity=quantity, comment=comment)


def make_product_stock(
    product_id: int = 1,
    quantity: int = 1000,
    batch_number: int = 1,
    batch_year: int = 2026,
    arrival_date: date = date(2026, 1, 1),
    expiry_date: date = date(2026, 7, 1),
    comment: str | None = None,
) -> ProductStock:
    return ProductStock(
        product_id=product_id,
        quantity=quantity,
        batch_number=batch_number,
        batch_year=batch_year,
        arrival_date=arrival_date,
        expiry_date=expiry_date,
        comment=comment,
    )


# ---------------------------------------------------------------------------
# RawMaterialStockRepository
# ---------------------------------------------------------------------------


class TestRawMaterialStockRepository:
    async def test_save_and_get_by_id(self, session):
        repo = RawMaterialStockRepository(session)
        stock = make_raw_material_stock()
        await repo.save(stock)

        found = await repo.get_by_id(stock.id)
        assert found is not None
        assert found.raw_material_id == 1
        assert found.quantity == Decimal("50.000")
        assert found.arrival_date == date(2026, 1, 1)
        assert found.expiry_date == date(2026, 6, 1)

    async def test_save_returns_id(self, session):
        repo = RawMaterialStockRepository(session)
        stock = make_raw_material_stock()
        id_ = await repo.save(stock)
        assert id_ is not None
        assert id_ == stock.id

    async def test_get_by_id_not_found(self, session):
        repo = RawMaterialStockRepository(session)
        assert await repo.get_by_id(999) is None

    async def test_get_all(self, session):
        repo = RawMaterialStockRepository(session)
        await repo.save(make_raw_material_stock(raw_material_id=1))
        await repo.save(make_raw_material_stock(raw_material_id=2))

        all_ = await repo.get_all()
        assert len(all_) == 2

    async def test_get_by_raw_material(self, session):
        repo = RawMaterialStockRepository(session)
        await repo.save(make_raw_material_stock(raw_material_id=1))
        await repo.save(make_raw_material_stock(raw_material_id=1))
        await repo.save(make_raw_material_stock(raw_material_id=2))

        result = await repo.get_by_raw_material(1)
        assert len(result) == 2
        assert all(s.raw_material_id == 1 for s in result)

    async def test_save_updates_existing(self, session):
        repo = RawMaterialStockRepository(session)
        stock = make_raw_material_stock(quantity="100.000")
        await repo.save(stock)

        stock.write_off(Decimal("30.000"))
        await repo.save(stock)

        found = await repo.get_by_id(stock.id)
        assert found.quantity == Decimal("70.000")

    async def test_comment_saved(self, session):
        repo = RawMaterialStockRepository(session)
        stock = make_raw_material_stock(comment="партия А")
        await repo.save(stock)

        found = await repo.get_by_id(stock.id)
        assert found.comment == "партия А"


# ---------------------------------------------------------------------------
# PackagingStockRepository
# ---------------------------------------------------------------------------


class TestPackagingStockRepository:
    async def test_save_and_get_by_id(self, session):
        repo = PackagingStockRepository(session)
        stock = make_packaging_stock()
        await repo.save(stock)

        found = await repo.get_by_id(stock.id)
        assert found is not None
        assert found.packaging_id == 1
        assert found.quantity == 500

    async def test_get_by_id_not_found(self, session):
        repo = PackagingStockRepository(session)
        assert await repo.get_by_id(999) is None

    async def test_get_all(self, session):
        repo = PackagingStockRepository(session)
        await repo.save(make_packaging_stock(packaging_id=1))
        await repo.save(make_packaging_stock(packaging_id=2))

        all_ = await repo.get_all()
        assert len(all_) == 2

    async def test_get_by_packaging(self, session):
        repo = PackagingStockRepository(session)
        await repo.save(make_packaging_stock(packaging_id=1))
        await repo.save(make_packaging_stock(packaging_id=1))
        await repo.save(make_packaging_stock(packaging_id=2))

        result = await repo.get_by_packaging(1)
        assert len(result) == 2
        assert all(s.packaging_id == 1 for s in result)

    async def test_save_updates_existing(self, session):
        repo = PackagingStockRepository(session)
        stock = make_packaging_stock(quantity=500)
        await repo.save(stock)

        stock.write_off(200)
        await repo.save(stock)

        found = await repo.get_by_id(stock.id)
        assert found.quantity == 300


# ---------------------------------------------------------------------------
# ProductStockRepository
# ---------------------------------------------------------------------------


class TestProductStockRepository:
    async def test_save_and_get_by_id(self, session):
        repo = ProductStockRepository(session)
        stock = make_product_stock()
        await repo.save(stock)

        found = await repo.get_by_id(stock.id)
        assert found is not None
        assert found.product_id == 1
        assert found.quantity == 1000
        assert found.batch_number == 1
        assert found.batch_year == 2026

    async def test_get_by_id_not_found(self, session):
        repo = ProductStockRepository(session)
        assert await repo.get_by_id(999) is None

    async def test_get_all(self, session):
        repo = ProductStockRepository(session)
        await repo.save(make_product_stock(product_id=1, batch_number=1))
        await repo.save(make_product_stock(product_id=2, batch_number=1))

        all_ = await repo.get_all()
        assert len(all_) == 2

    async def test_get_by_product(self, session):
        repo = ProductStockRepository(session)
        await repo.save(make_product_stock(product_id=1, batch_number=1))
        await repo.save(make_product_stock(product_id=1, batch_number=2))
        await repo.save(make_product_stock(product_id=2, batch_number=1))

        result = await repo.get_by_product(1)
        assert len(result) == 2
        assert all(s.product_id == 1 for s in result)

    async def test_get_last_batch_number_returns_max(self, session):
        repo = ProductStockRepository(session)
        await repo.save(make_product_stock(product_id=1, batch_number=1, batch_year=2026))
        await repo.save(make_product_stock(product_id=1, batch_number=2, batch_year=2026))
        await repo.save(make_product_stock(product_id=2, batch_number=3, batch_year=2026))

        last = await repo.get_last_batch_number(2026)
        assert last == 3

    async def test_get_last_batch_number_no_batches_returns_zero(self, session):
        repo = ProductStockRepository(session)
        last = await repo.get_last_batch_number(2026)
        assert last == 0

    async def test_get_last_batch_number_ignores_other_year(self, session):
        repo = ProductStockRepository(session)
        await repo.save(make_product_stock(product_id=1, batch_number=5, batch_year=2025))

        last = await repo.get_last_batch_number(2026)
        assert last == 0

    async def test_save_updates_existing(self, session):
        repo = ProductStockRepository(session)
        stock = make_product_stock(quantity=1000)
        await repo.save(stock)

        stock.write_off(400)
        await repo.save(stock)

        found = await repo.get_by_id(stock.id)
        assert found.quantity == 600
