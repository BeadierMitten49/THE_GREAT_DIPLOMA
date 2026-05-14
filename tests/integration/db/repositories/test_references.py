from decimal import Decimal

import pytest

from src.domain.references.entities import (
    Customer,
    PackagingCatalog,
    Product,
    RawMaterialCatalog,
    RecipeLine,
)
from src.infrastructure.db.repositories.references import (
    CustomerRepository,
    PackagingCatalogRepository,
    ProductRepository,
    RawMaterialCatalogRepository,
)

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# CustomerRepository
# ---------------------------------------------------------------------------


class TestCustomerRepository:
    async def test_save_creates_record_and_assigns_id(self, session):
        repo = CustomerRepository(session)
        customer = Customer(name="ООО Ромашка", default_address="ул. Ленина, 1")

        returned_id = await repo.save(customer)

        assert returned_id is not None
        assert customer.id == returned_id

    async def test_get_by_id_returns_entity(self, session):
        repo = CustomerRepository(session)
        customer = Customer(name="ООО Ромашка", default_address="ул. Ленина, 1")
        await repo.save(customer)

        found = await repo.get_by_id(customer.id)

        assert found is not None
        assert found.name == "ООО Ромашка"
        assert found.default_address == "ул. Ленина, 1"
        assert found.is_active is True

    async def test_get_by_id_returns_none_for_missing(self, session):
        repo = CustomerRepository(session)
        assert await repo.get_by_id(999) is None

    async def test_get_all_returns_only_active_by_default(self, session):
        repo = CustomerRepository(session)
        active = Customer(name="Active", default_address="addr")
        inactive = Customer(name="Inactive", default_address="addr", is_active=False)
        await repo.save(active)
        await repo.save(inactive)

        result = await repo.get_all()

        names = [c.name for c in result]
        assert "Active" in names
        assert "Inactive" not in names

    async def test_get_all_include_inactive(self, session):
        repo = CustomerRepository(session)
        active = Customer(name="Active2", default_address="addr")
        inactive = Customer(name="Inactive2", default_address="addr", is_active=False)
        await repo.save(active)
        await repo.save(inactive)

        result = await repo.get_all(include_inactive=True)

        names = [c.name for c in result]
        assert "Active2" in names
        assert "Inactive2" in names

    async def test_save_updates_existing_record(self, session):
        repo = CustomerRepository(session)
        customer = Customer(name="Old Name", default_address="Old addr")
        await repo.save(customer)

        customer.update("New Name", "New addr")
        await repo.save(customer)

        found = await repo.get_by_id(customer.id)
        assert found.name == "New Name"
        assert found.default_address == "New addr"

    async def test_exists_by_name_returns_true_when_exists(self, session):
        repo = CustomerRepository(session)
        await repo.save(Customer(name="Unique Co", default_address="addr"))

        assert await repo.exists_by_name("Unique Co") is True

    async def test_exists_by_name_returns_false_when_missing(self, session):
        repo = CustomerRepository(session)
        assert await repo.exists_by_name("Ghost Co") is False

    async def test_exists_by_name_excludes_self(self, session):
        repo = CustomerRepository(session)
        customer = Customer(name="Solo Co", default_address="addr")
        await repo.save(customer)

        assert await repo.exists_by_name("Solo Co", exclude_id=customer.id) is False


# ---------------------------------------------------------------------------
# RawMaterialCatalogRepository
# ---------------------------------------------------------------------------


class TestRawMaterialCatalogRepository:
    async def test_save_creates_and_assigns_id(self, session):
        repo = RawMaterialCatalogRepository(session)
        item = RawMaterialCatalog(name="Сахар", unit="кг", shelf_life_days=365, critical_stock=Decimal("50.0"))

        returned_id = await repo.save(item)

        assert returned_id is not None
        assert item.id == returned_id

    async def test_get_by_id_returns_correct_entity(self, session):
        repo = RawMaterialCatalogRepository(session)
        item = RawMaterialCatalog(name="Мука", unit="кг", shelf_life_days=180, critical_stock=Decimal("30.5"))
        await repo.save(item)

        found = await repo.get_by_id(item.id)

        assert found.name == "Мука"
        assert found.unit == "кг"
        assert found.shelf_life_days == 180
        assert found.critical_stock == Decimal("30.5")

    async def test_get_all_returns_only_active_by_default(self, session):
        repo = RawMaterialCatalogRepository(session)
        await repo.save(RawMaterialCatalog(name="ActiveRM", unit="кг", shelf_life_days=1, critical_stock=Decimal("0")))
        await repo.save(RawMaterialCatalog(name="InactiveRM", unit="кг", shelf_life_days=1, critical_stock=Decimal("0"), is_active=False))

        result = await repo.get_all()

        names = [r.name for r in result]
        assert "ActiveRM" in names
        assert "InactiveRM" not in names

    async def test_save_updates_existing(self, session):
        repo = RawMaterialCatalogRepository(session)
        item = RawMaterialCatalog(name="Old", unit="кг", shelf_life_days=1, critical_stock=Decimal("0"))
        await repo.save(item)

        item.update("New", "л", 365, Decimal("10.0"))
        await repo.save(item)

        found = await repo.get_by_id(item.id)
        assert found.name == "New"
        assert found.unit == "л"
        assert found.critical_stock == Decimal("10.0")

    async def test_exists_by_name_excludes_self(self, session):
        repo = RawMaterialCatalogRepository(session)
        item = RawMaterialCatalog(name="Salt", unit="кг", shelf_life_days=1, critical_stock=Decimal("0"))
        await repo.save(item)

        assert await repo.exists_by_name("Salt", exclude_id=item.id) is False


# ---------------------------------------------------------------------------
# PackagingCatalogRepository
# ---------------------------------------------------------------------------


class TestPackagingCatalogRepository:
    async def test_save_creates_and_assigns_id(self, session):
        repo = PackagingCatalogRepository(session)
        item = PackagingCatalog(name="Пакет 1кг", unit="шт", critical_stock=500)

        returned_id = await repo.save(item)

        assert returned_id is not None
        assert item.id == returned_id

    async def test_get_by_id_returns_correct_entity(self, session):
        repo = PackagingCatalogRepository(session)
        item = PackagingCatalog(name="Коробка", unit="шт", critical_stock=100)
        await repo.save(item)

        found = await repo.get_by_id(item.id)

        assert found.name == "Коробка"
        assert found.critical_stock == 100

    async def test_save_updates_existing(self, session):
        repo = PackagingCatalogRepository(session)
        item = PackagingCatalog(name="Old Pkg", unit="шт", critical_stock=0)
        await repo.save(item)

        item.update("New Pkg", "уп", 200)
        await repo.save(item)

        found = await repo.get_by_id(item.id)
        assert found.name == "New Pkg"
        assert found.critical_stock == 200

    async def test_deactivate_persists(self, session):
        repo = PackagingCatalogRepository(session)
        item = PackagingCatalog(name="ToDeactivate", unit="шт", critical_stock=0)
        await repo.save(item)

        item.deactivate()
        await repo.save(item)

        found = await repo.get_by_id(item.id)
        assert found.is_active is False


# ---------------------------------------------------------------------------
# ProductRepository
# ---------------------------------------------------------------------------


class TestProductRepository:
    async def test_save_creates_and_assigns_id(self, session):
        repo = ProductRepository(session)
        product = Product(name="Сахар фасованный", units_per_box=12, shelf_life_days=365, critical_stock=100)

        returned_id = await repo.save(product)

        assert returned_id is not None
        assert product.id == returned_id

    async def test_get_by_id_returns_correct_entity(self, session):
        repo = ProductRepository(session)
        product = Product(name="Соль", units_per_box=24, shelf_life_days=730, critical_stock=50)
        await repo.save(product)

        found = await repo.get_by_id(product.id)

        assert found.name == "Соль"
        assert found.units_per_box == 24
        assert found.shelf_life_days == 730
        assert found.critical_stock == 50

    async def test_get_by_id_loads_recipe(self, session):
        rm_repo = RawMaterialCatalogRepository(session)
        rm = RawMaterialCatalog(name="СырьёПР", unit="кг", shelf_life_days=1, critical_stock=Decimal("0"))
        await rm_repo.save(rm)

        repo = ProductRepository(session)
        product = Product(name="Продукт с рецептом", units_per_box=1, shelf_life_days=1, critical_stock=0)
        product.set_recipe([RecipeLine(raw_material_id=rm.id, consumption_per_unit=Decimal("1.5"), waste_percentage=Decimal("2.0"))])
        await repo.save(product)

        found = await repo.get_by_id(product.id)

        assert len(found.recipe) == 1
        assert found.recipe[0].raw_material_id == rm.id
        assert found.recipe[0].consumption_per_unit == Decimal("1.5")
        assert found.recipe[0].waste_percentage == Decimal("2.0")
        assert found.recipe[0].id is not None

    async def test_save_inserts_new_recipe_lines(self, session):
        rm_repo = RawMaterialCatalogRepository(session)
        rm1 = RawMaterialCatalog(name="РМ1", unit="кг", shelf_life_days=1, critical_stock=Decimal("0"))
        rm2 = RawMaterialCatalog(name="РМ2", unit="кг", shelf_life_days=1, critical_stock=Decimal("0"))
        await rm_repo.save(rm1)
        await rm_repo.save(rm2)

        repo = ProductRepository(session)
        product = Product(name="Продукт2", units_per_box=1, shelf_life_days=1, critical_stock=0)
        product.set_recipe([
            RecipeLine(raw_material_id=rm1.id, consumption_per_unit=Decimal("1.0"), waste_percentage=Decimal("0")),
            RecipeLine(raw_material_id=rm2.id, consumption_per_unit=Decimal("2.0"), waste_percentage=Decimal("5")),
        ])
        await repo.save(product)

        found = await repo.get_by_id(product.id)
        assert len(found.recipe) == 2

    async def test_sync_recipe_updates_existing_line(self, session):
        rm_repo = RawMaterialCatalogRepository(session)
        rm = RawMaterialCatalog(name="РМ_upd", unit="кг", shelf_life_days=1, critical_stock=Decimal("0"))
        await rm_repo.save(rm)

        repo = ProductRepository(session)
        product = Product(name="Продукт3", units_per_box=1, shelf_life_days=1, critical_stock=0)
        product.set_recipe([RecipeLine(raw_material_id=rm.id, consumption_per_unit=Decimal("1.0"), waste_percentage=Decimal("0"))])
        await repo.save(product)

        found = await repo.get_by_id(product.id)
        line = found.recipe[0]
        line.consumption_per_unit = Decimal("3.0")
        found.set_recipe([line])
        await repo.save(found)

        updated = await repo.get_by_id(product.id)
        assert len(updated.recipe) == 1
        assert updated.recipe[0].consumption_per_unit == Decimal("3.0")

    async def test_sync_recipe_deletes_removed_lines(self, session):
        rm_repo = RawMaterialCatalogRepository(session)
        rm1 = RawMaterialCatalog(name="РМ_del1", unit="кг", shelf_life_days=1, critical_stock=Decimal("0"))
        rm2 = RawMaterialCatalog(name="РМ_del2", unit="кг", shelf_life_days=1, critical_stock=Decimal("0"))
        await rm_repo.save(rm1)
        await rm_repo.save(rm2)

        repo = ProductRepository(session)
        product = Product(name="Продукт4", units_per_box=1, shelf_life_days=1, critical_stock=0)
        product.set_recipe([
            RecipeLine(raw_material_id=rm1.id, consumption_per_unit=Decimal("1.0"), waste_percentage=Decimal("0")),
            RecipeLine(raw_material_id=rm2.id, consumption_per_unit=Decimal("1.0"), waste_percentage=Decimal("0")),
        ])
        await repo.save(product)

        found = await repo.get_by_id(product.id)
        found.set_recipe([found.recipe[0]])
        await repo.save(found)

        updated = await repo.get_by_id(product.id)
        assert len(updated.recipe) == 1

    async def test_save_updates_product_fields(self, session):
        repo = ProductRepository(session)
        product = Product(name="Old Product", units_per_box=1, shelf_life_days=1, critical_stock=0)
        await repo.save(product)

        product.update("New Product", 24, 365, 100)
        await repo.save(product)

        found = await repo.get_by_id(product.id)
        assert found.name == "New Product"
        assert found.units_per_box == 24
