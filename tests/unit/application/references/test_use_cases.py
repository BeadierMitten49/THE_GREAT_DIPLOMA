from decimal import Decimal

import pytest

from src.application.references.dto import (
    CreateCustomerDTO,
    CreatePackagingDTO,
    CreateProductDTO,
    CreateRawMaterialDTO,
    RecipeLineDTO,
    UpdateCustomerDTO,
    UpdatePackagingDTO,
    UpdateProductDTO,
    UpdateRawMaterialDTO,
)
from src.application.references.exceptions import AlreadyExistsError, NotFoundError
from src.application.references.use_cases import (
    activate_customer,
    activate_packaging,
    activate_product,
    activate_raw_material,
    create_customer,
    create_packaging,
    create_product,
    create_raw_material,
    deactivate_customer,
    deactivate_packaging,
    deactivate_product,
    deactivate_raw_material,
    get_customer,
    get_customers,
    get_packaging,
    get_packagings,
    get_product,
    get_products,
    get_raw_material,
    get_raw_materials,
    set_product_recipe,
    update_customer,
    update_packaging,
    update_product,
    update_raw_material,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------


class TestGetCustomer:
    async def test_returns_entity_when_found(self, customer_repo, saved_customer):
        result = await get_customer(saved_customer.id, customer_repo)
        assert result.name == "ООО Ромашка"

    async def test_raises_not_found_when_missing(self, customer_repo):
        with pytest.raises(NotFoundError):
            await get_customer(999, customer_repo)


class TestGetCustomers:
    async def test_returns_only_active_by_default(self, customer_repo, saved_customer):
        saved_customer.deactivate()
        result = await get_customers(customer_repo)
        assert result == []

    async def test_returns_all_when_include_inactive(self, customer_repo, saved_customer):
        saved_customer.deactivate()
        result = await get_customers(customer_repo, include_inactive=True)
        assert len(result) == 1


class TestCreateCustomer:
    async def test_creates_and_returns_id(self, customer_repo):
        id = await create_customer(CreateCustomerDTO("New Co", "addr"), customer_repo)
        assert id is not None
        assert await customer_repo.get_by_id(id) is not None

    async def test_raises_when_name_already_exists(self, customer_repo, saved_customer):
        with pytest.raises(AlreadyExistsError):
            await create_customer(CreateCustomerDTO(saved_customer.name, "addr"), customer_repo)


class TestUpdateCustomer:
    async def test_updates_fields(self, customer_repo, saved_customer):
        await update_customer(saved_customer.id, UpdateCustomerDTO("New Name", "New addr"), customer_repo)
        updated = await customer_repo.get_by_id(saved_customer.id)
        assert updated.name == "New Name"
        assert updated.default_address == "New addr"

    async def test_raises_not_found_when_missing(self, customer_repo):
        with pytest.raises(NotFoundError):
            await update_customer(999, UpdateCustomerDTO("X", "addr"), customer_repo)

    async def test_raises_when_name_taken_by_another(self, customer_repo, saved_customer):
        other = await create_customer(CreateCustomerDTO("Other Co", "addr"), customer_repo)
        with pytest.raises(AlreadyExistsError):
            await update_customer(saved_customer.id, UpdateCustomerDTO("Other Co", "addr"), customer_repo)

    async def test_allows_keeping_own_name(self, customer_repo, saved_customer):
        await update_customer(
            saved_customer.id,
            UpdateCustomerDTO(saved_customer.name, "New addr"),
            customer_repo,
        )
        updated = await customer_repo.get_by_id(saved_customer.id)
        assert updated.default_address == "New addr"


class TestDeactivateCustomer:
    async def test_deactivates(self, customer_repo, saved_customer):
        await deactivate_customer(saved_customer.id, customer_repo)
        assert (await customer_repo.get_by_id(saved_customer.id)).is_active is False

    async def test_raises_not_found_when_missing(self, customer_repo):
        with pytest.raises(NotFoundError):
            await deactivate_customer(999, customer_repo)


class TestActivateCustomer:
    async def test_activates(self, customer_repo, saved_customer):
        saved_customer.deactivate()
        await activate_customer(saved_customer.id, customer_repo)
        assert (await customer_repo.get_by_id(saved_customer.id)).is_active is True

    async def test_raises_not_found_when_missing(self, customer_repo):
        with pytest.raises(NotFoundError):
            await activate_customer(999, customer_repo)


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------


class TestCreateProduct:
    async def test_creates_and_returns_id(self, product_repo):
        id = await create_product(CreateProductDTO("Продукт", 12, 365, 100), product_repo)
        assert id is not None

    async def test_raises_when_name_already_exists(self, product_repo, saved_product):
        with pytest.raises(AlreadyExistsError):
            await create_product(CreateProductDTO(saved_product.name, 1, 1, 0), product_repo)


class TestUpdateProduct:
    async def test_updates_fields(self, product_repo, saved_product):
        await update_product(saved_product.id, UpdateProductDTO("New", 24, 730, 50), product_repo)
        updated = await product_repo.get_by_id(saved_product.id)
        assert updated.name == "New"
        assert updated.units_per_box == 24

    async def test_raises_not_found_when_missing(self, product_repo):
        with pytest.raises(NotFoundError):
            await update_product(999, UpdateProductDTO("X", 1, 1, 0), product_repo)

    async def test_allows_keeping_own_name(self, product_repo, saved_product):
        await update_product(
            saved_product.id,
            UpdateProductDTO(saved_product.name, 24, 365, 100),
            product_repo,
        )
        updated = await product_repo.get_by_id(saved_product.id)
        assert updated.units_per_box == 24


class TestSetProductRecipe:
    async def test_sets_recipe(self, product_repo, saved_product):
        lines = [RecipeLineDTO(raw_material_id=1, consumption_per_unit=Decimal("1.5"), waste_percentage=Decimal("2"))]
        await set_product_recipe(saved_product.id, lines, product_repo)
        updated = await product_repo.get_by_id(saved_product.id)
        assert len(updated.recipe) == 1
        assert updated.recipe[0].raw_material_id == 1

    async def test_raises_not_found_when_missing(self, product_repo):
        with pytest.raises(NotFoundError):
            await set_product_recipe(999, [], product_repo)


class TestDeactivateProduct:
    async def test_deactivates(self, product_repo, saved_product):
        await deactivate_product(saved_product.id, product_repo)
        assert (await product_repo.get_by_id(saved_product.id)).is_active is False

    async def test_raises_not_found_when_missing(self, product_repo):
        with pytest.raises(NotFoundError):
            await deactivate_product(999, product_repo)


class TestActivateProduct:
    async def test_activates(self, product_repo, saved_product):
        saved_product.deactivate()
        await activate_product(saved_product.id, product_repo)
        assert (await product_repo.get_by_id(saved_product.id)).is_active is True

    async def test_raises_not_found_when_missing(self, product_repo):
        with pytest.raises(NotFoundError):
            await activate_product(999, product_repo)


# ---------------------------------------------------------------------------
# RawMaterialCatalog
# ---------------------------------------------------------------------------


class TestCreateRawMaterial:
    async def test_creates_and_returns_id(self, raw_material_repo):
        id = await create_raw_material(
            CreateRawMaterialDTO("Соль", "кг", 365, Decimal("10")), raw_material_repo
        )
        assert id is not None

    async def test_raises_when_name_already_exists(self, raw_material_repo, saved_raw_material):
        with pytest.raises(AlreadyExistsError):
            await create_raw_material(
                CreateRawMaterialDTO(saved_raw_material.name, "кг", 1, Decimal("0")), raw_material_repo
            )


class TestUpdateRawMaterial:
    async def test_updates_fields(self, raw_material_repo, saved_raw_material):
        await update_raw_material(
            saved_raw_material.id,
            UpdateRawMaterialDTO("New", "л", 365, Decimal("5")),
            raw_material_repo,
        )
        updated = await raw_material_repo.get_by_id(saved_raw_material.id)
        assert updated.name == "New"
        assert updated.unit == "л"

    async def test_raises_not_found_when_missing(self, raw_material_repo):
        with pytest.raises(NotFoundError):
            await update_raw_material(999, UpdateRawMaterialDTO("X", "кг", 1, Decimal("0")), raw_material_repo)

    async def test_allows_keeping_own_name(self, raw_material_repo, saved_raw_material):
        await update_raw_material(
            saved_raw_material.id,
            UpdateRawMaterialDTO(saved_raw_material.name, "л", 365, Decimal("5")),
            raw_material_repo,
        )
        updated = await raw_material_repo.get_by_id(saved_raw_material.id)
        assert updated.unit == "л"


class TestDeactivateRawMaterial:
    async def test_deactivates(self, raw_material_repo, saved_raw_material):
        await deactivate_raw_material(saved_raw_material.id, raw_material_repo)
        assert (await raw_material_repo.get_by_id(saved_raw_material.id)).is_active is False

    async def test_raises_not_found_when_missing(self, raw_material_repo):
        with pytest.raises(NotFoundError):
            await deactivate_raw_material(999, raw_material_repo)


class TestActivateRawMaterial:
    async def test_activates(self, raw_material_repo, saved_raw_material):
        saved_raw_material.deactivate()
        await activate_raw_material(saved_raw_material.id, raw_material_repo)
        assert (await raw_material_repo.get_by_id(saved_raw_material.id)).is_active is True

    async def test_raises_not_found_when_missing(self, raw_material_repo):
        with pytest.raises(NotFoundError):
            await activate_raw_material(999, raw_material_repo)


# ---------------------------------------------------------------------------
# PackagingCatalog
# ---------------------------------------------------------------------------


class TestCreatePackaging:
    async def test_creates_and_returns_id(self, packaging_repo):
        id = await create_packaging(CreatePackagingDTO("Коробка", "шт", 100), packaging_repo)
        assert id is not None

    async def test_raises_when_name_already_exists(self, packaging_repo, saved_packaging):
        with pytest.raises(AlreadyExistsError):
            await create_packaging(CreatePackagingDTO(saved_packaging.name, "шт", 0), packaging_repo)


class TestUpdatePackaging:
    async def test_updates_fields(self, packaging_repo, saved_packaging):
        await update_packaging(saved_packaging.id, UpdatePackagingDTO("New Pkg", "уп", 200), packaging_repo)
        updated = await packaging_repo.get_by_id(saved_packaging.id)
        assert updated.name == "New Pkg"
        assert updated.critical_stock == 200

    async def test_raises_not_found_when_missing(self, packaging_repo):
        with pytest.raises(NotFoundError):
            await update_packaging(999, UpdatePackagingDTO("X", "шт", 0), packaging_repo)

    async def test_allows_keeping_own_name(self, packaging_repo, saved_packaging):
        await update_packaging(
            saved_packaging.id,
            UpdatePackagingDTO(saved_packaging.name, "уп", 200),
            packaging_repo,
        )
        updated = await packaging_repo.get_by_id(saved_packaging.id)
        assert updated.unit == "уп"


class TestDeactivatePackaging:
    async def test_deactivates(self, packaging_repo, saved_packaging):
        await deactivate_packaging(saved_packaging.id, packaging_repo)
        assert (await packaging_repo.get_by_id(saved_packaging.id)).is_active is False

    async def test_raises_not_found_when_missing(self, packaging_repo):
        with pytest.raises(NotFoundError):
            await deactivate_packaging(999, packaging_repo)


class TestActivatePackaging:
    async def test_activates(self, packaging_repo, saved_packaging):
        saved_packaging.deactivate()
        await activate_packaging(saved_packaging.id, packaging_repo)
        assert (await packaging_repo.get_by_id(saved_packaging.id)).is_active is True

    async def test_raises_not_found_when_missing(self, packaging_repo):
        with pytest.raises(NotFoundError):
            await activate_packaging(999, packaging_repo)
