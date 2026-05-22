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
from src.domain.references.entities import (
    Customer,
    PackagingCatalog,
    Product,
    RawMaterialCatalog,
    RecipeLine,
)
from src.domain.references.interfaces import (
    ICustomerRepository,
    IPackagingCatalogRepository,
    IProductRepository,
    IRawMaterialCatalogRepository,
)


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------


async def get_customer(id: int, repo: ICustomerRepository) -> Customer:
    customer = await repo.get_by_id(id)
    if customer is None:
        raise NotFoundError("Customer", id)
    return customer


async def get_customers(repo: ICustomerRepository, include_inactive: bool = False) -> list[Customer]:
    return await repo.get_all(include_inactive=include_inactive)


async def create_customer(dto: CreateCustomerDTO, repo: ICustomerRepository) -> int:
    if await repo.exists_by_name(dto.name):
        raise AlreadyExistsError("Customer", "name", dto.name)
    customer = Customer(name=dto.name, default_address=dto.default_address, contact=dto.contact, comment=dto.comment)
    return await repo.save(customer)


async def update_customer(id: int, dto: UpdateCustomerDTO, repo: ICustomerRepository) -> None:
    customer = await get_customer(id, repo)
    if await repo.exists_by_name(dto.name, exclude_id=id):
        raise AlreadyExistsError("Customer", "name", dto.name)
    customer.update(dto.name, dto.default_address, dto.contact, dto.comment)
    await repo.save(customer)


async def deactivate_customer(id: int, repo: ICustomerRepository) -> None:
    customer = await get_customer(id, repo)
    customer.deactivate()
    await repo.save(customer)


async def activate_customer(id: int, repo: ICustomerRepository) -> None:
    customer = await get_customer(id, repo)
    customer.activate()
    await repo.save(customer)


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------


async def get_product(id: int, repo: IProductRepository) -> Product:
    product = await repo.get_by_id(id)
    if product is None:
        raise NotFoundError("Product", id)
    return product


async def get_products(repo: IProductRepository, include_inactive: bool = False) -> list[Product]:
    return await repo.get_all(include_inactive=include_inactive)


async def create_product(dto: CreateProductDTO, repo: IProductRepository) -> int:
    if await repo.exists_by_name(dto.name):
        raise AlreadyExistsError("Product", "name", dto.name)
    product = Product(
        name=dto.name,
        units_per_box=dto.units_per_box,
        shelf_life_days=dto.shelf_life_days,
        critical_stock=dto.critical_stock,
    )
    return await repo.save(product)


async def update_product(id: int, dto: UpdateProductDTO, repo: IProductRepository) -> None:
    product = await get_product(id, repo)
    if await repo.exists_by_name(dto.name, exclude_id=id):
        raise AlreadyExistsError("Product", "name", dto.name)
    product.update(dto.name, dto.units_per_box, dto.shelf_life_days, dto.critical_stock)
    await repo.save(product)


async def set_product_recipe(id: int, lines: list[RecipeLineDTO], repo: IProductRepository) -> None:
    product = await get_product(id, repo)
    product.set_recipe(
        RecipeLine(
            raw_material_id=line.raw_material_id,
            consumption_per_unit=line.consumption_per_unit,
            waste_percentage=line.waste_percentage,
        )
        for line in lines
    )
    await repo.save(product)


async def deactivate_product(id: int, repo: IProductRepository) -> None:
    product = await get_product(id, repo)
    product.deactivate()
    await repo.save(product)


async def activate_product(id: int, repo: IProductRepository) -> None:
    product = await get_product(id, repo)
    product.activate()
    await repo.save(product)


# ---------------------------------------------------------------------------
# RawMaterialCatalog
# ---------------------------------------------------------------------------


async def get_raw_material(id: int, repo: IRawMaterialCatalogRepository) -> RawMaterialCatalog:
    item = await repo.get_by_id(id)
    if item is None:
        raise NotFoundError("RawMaterialCatalog", id)
    return item


async def get_raw_materials(
    repo: IRawMaterialCatalogRepository, include_inactive: bool = False
) -> list[RawMaterialCatalog]:
    return await repo.get_all(include_inactive=include_inactive)


async def create_raw_material(dto: CreateRawMaterialDTO, repo: IRawMaterialCatalogRepository) -> int:
    if await repo.exists_by_name(dto.name):
        raise AlreadyExistsError("RawMaterialCatalog", "name", dto.name)
    item = RawMaterialCatalog(
        name=dto.name,
        unit=dto.unit,
        shelf_life_days=dto.shelf_life_days,
        critical_stock=dto.critical_stock,
        comment=dto.comment,
    )
    return await repo.save(item)


async def update_raw_material(
    id: int, dto: UpdateRawMaterialDTO, repo: IRawMaterialCatalogRepository
) -> None:
    item = await get_raw_material(id, repo)
    if await repo.exists_by_name(dto.name, exclude_id=id):
        raise AlreadyExistsError("RawMaterialCatalog", "name", dto.name)
    item.update(dto.name, dto.unit, dto.shelf_life_days, dto.critical_stock, dto.comment)
    await repo.save(item)


async def deactivate_raw_material(id: int, repo: IRawMaterialCatalogRepository) -> None:
    item = await get_raw_material(id, repo)
    item.deactivate()
    await repo.save(item)


async def activate_raw_material(id: int, repo: IRawMaterialCatalogRepository) -> None:
    item = await get_raw_material(id, repo)
    item.activate()
    await repo.save(item)


# ---------------------------------------------------------------------------
# PackagingCatalog
# ---------------------------------------------------------------------------


async def get_packaging(id: int, repo: IPackagingCatalogRepository) -> PackagingCatalog:
    item = await repo.get_by_id(id)
    if item is None:
        raise NotFoundError("PackagingCatalog", id)
    return item


async def get_packagings(
    repo: IPackagingCatalogRepository, include_inactive: bool = False
) -> list[PackagingCatalog]:
    return await repo.get_all(include_inactive=include_inactive)


async def create_packaging(dto: CreatePackagingDTO, repo: IPackagingCatalogRepository) -> int:
    if await repo.exists_by_name(dto.name):
        raise AlreadyExistsError("PackagingCatalog", "name", dto.name)
    item = PackagingCatalog(name=dto.name, unit=dto.unit, critical_stock=dto.critical_stock, comment=dto.comment)
    return await repo.save(item)


async def update_packaging(
    id: int, dto: UpdatePackagingDTO, repo: IPackagingCatalogRepository
) -> None:
    item = await get_packaging(id, repo)
    if await repo.exists_by_name(dto.name, exclude_id=id):
        raise AlreadyExistsError("PackagingCatalog", "name", dto.name)
    item.update(dto.name, dto.unit, dto.critical_stock, dto.comment)
    await repo.save(item)


async def deactivate_packaging(id: int, repo: IPackagingCatalogRepository) -> None:
    item = await get_packaging(id, repo)
    item.deactivate()
    await repo.save(item)


async def activate_packaging(id: int, repo: IPackagingCatalogRepository) -> None:
    item = await get_packaging(id, repo)
    item.activate()
    await repo.save(item)
