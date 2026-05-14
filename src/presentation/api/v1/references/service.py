from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

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
from src.domain.references.entities import (
    Customer,
    PackagingCatalog,
    Product,
    RawMaterialCatalog,
)
from src.infrastructure.db.repositories.references import (
    CustomerRepository,
    PackagingCatalogRepository,
    ProductRepository,
    RawMaterialCatalogRepository,
)


class CustomerService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = CustomerRepository(session)

    async def get(self, id: int) -> Customer:
        return await get_customer(id, self._repo)

    async def get_all(self, include_inactive: bool = False) -> list[Customer]:
        return await get_customers(self._repo, include_inactive)

    async def create(self, name: str, default_address: str) -> int:
        return await create_customer(CreateCustomerDTO(name, default_address), self._repo)

    async def update(self, id: int, name: str, default_address: str) -> None:
        await update_customer(id, UpdateCustomerDTO(name, default_address), self._repo)

    async def deactivate(self, id: int) -> None:
        await deactivate_customer(id, self._repo)

    async def activate(self, id: int) -> None:
        await activate_customer(id, self._repo)


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = ProductRepository(session)

    async def get(self, id: int) -> Product:
        return await get_product(id, self._repo)

    async def get_all(self, include_inactive: bool = False) -> list[Product]:
        return await get_products(self._repo, include_inactive)

    async def create(
        self, name: str, units_per_box: int, shelf_life_days: int, critical_stock: int
    ) -> int:
        return await create_product(
            CreateProductDTO(name, units_per_box, shelf_life_days, critical_stock), self._repo
        )

    async def update(
        self, id: int, name: str, units_per_box: int, shelf_life_days: int, critical_stock: int
    ) -> None:
        await update_product(
            id, UpdateProductDTO(name, units_per_box, shelf_life_days, critical_stock), self._repo
        )

    async def set_recipe(self, id: int, lines: list[tuple[int, Decimal, Decimal]]) -> None:
        dtos = [RecipeLineDTO(rm_id, consumption, waste) for rm_id, consumption, waste in lines]
        await set_product_recipe(id, dtos, self._repo)

    async def deactivate(self, id: int) -> None:
        await deactivate_product(id, self._repo)

    async def activate(self, id: int) -> None:
        await activate_product(id, self._repo)


class RawMaterialService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = RawMaterialCatalogRepository(session)

    async def get(self, id: int) -> RawMaterialCatalog:
        return await get_raw_material(id, self._repo)

    async def get_all(self, include_inactive: bool = False) -> list[RawMaterialCatalog]:
        return await get_raw_materials(self._repo, include_inactive)

    async def create(self, name: str, unit: str, shelf_life_days: int, critical_stock: Decimal) -> int:
        return await create_raw_material(
            CreateRawMaterialDTO(name, unit, shelf_life_days, critical_stock), self._repo
        )

    async def update(
        self, id: int, name: str, unit: str, shelf_life_days: int, critical_stock: Decimal
    ) -> None:
        await update_raw_material(
            id, UpdateRawMaterialDTO(name, unit, shelf_life_days, critical_stock), self._repo
        )

    async def deactivate(self, id: int) -> None:
        await deactivate_raw_material(id, self._repo)

    async def activate(self, id: int) -> None:
        await activate_raw_material(id, self._repo)


class PackagingService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = PackagingCatalogRepository(session)

    async def get(self, id: int) -> PackagingCatalog:
        return await get_packaging(id, self._repo)

    async def get_all(self, include_inactive: bool = False) -> list[PackagingCatalog]:
        return await get_packagings(self._repo, include_inactive)

    async def create(self, name: str, unit: str, critical_stock: int) -> int:
        return await create_packaging(CreatePackagingDTO(name, unit, critical_stock), self._repo)

    async def update(self, id: int, name: str, unit: str, critical_stock: int) -> None:
        await update_packaging(id, UpdatePackagingDTO(name, unit, critical_stock), self._repo)

    async def deactivate(self, id: int) -> None:
        await deactivate_packaging(id, self._repo)

    async def activate(self, id: int) -> None:
        await activate_packaging(id, self._repo)
