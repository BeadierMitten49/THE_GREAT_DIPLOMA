from decimal import Decimal

import pytest

from src.domain.references.entities import (
    Customer,
    PackagingCatalog,
    Product,
    RawMaterialCatalog,
    RecipeLine,
)


@pytest.fixture
def customer():
    return Customer(name="ООО Ромашка", default_address="ул. Ленина, 1")


@pytest.fixture
def product():
    return Product(name="Сахар фасованный", units_per_box=12, shelf_life_days=365, critical_stock=100)


@pytest.fixture
def raw_material():
    return RawMaterialCatalog(name="Сахар-сырец", unit="кг", shelf_life_days=730, critical_stock=Decimal("50.0"))


@pytest.fixture
def packaging():
    return PackagingCatalog(name="Пакет 1кг", unit="шт", critical_stock=500)


@pytest.fixture
def recipe_line():
    return RecipeLine(
        raw_material_id=1,
        consumption_per_unit=Decimal("1.05"),
        waste_percentage=Decimal("2.0"),
    )


@pytest.fixture
def recipe_line_factory():
    def _make(raw_material_id=1, consumption="1.0", waste="2.0") -> RecipeLine:
        return RecipeLine(
            raw_material_id=raw_material_id,
            consumption_per_unit=Decimal(consumption),
            waste_percentage=Decimal(waste),
        )
    return _make
