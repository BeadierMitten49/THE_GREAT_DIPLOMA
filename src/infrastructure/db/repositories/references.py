from decimal import Decimal

from sqlalchemy import delete, select, update
from sqlalchemy.orm import selectinload

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
from src.infrastructure.db.models.references import (
    CustomerModel,
    PackagingCatalogModel,
    ProductModel,
    RawMaterialCatalogModel,
    RecipeLineModel,
)
from src.infrastructure.db.repositories.base import BaseRepository


class BaseCatalogRepository[TEntity, TModel](BaseRepository[TEntity, TModel]):
    async def exists_by_name(self, name: str, exclude_id: int | None = None) -> bool:
        stmt = select(self._model_class.id).where(self._model_class.name == name)
        if exclude_id is not None:
            stmt = stmt.where(self._model_class.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar() is not None


class CustomerRepository(BaseCatalogRepository[Customer, CustomerModel], ICustomerRepository):
    @property
    def _model_class(self) -> type[CustomerModel]:
        return CustomerModel

    def _to_entity(self, model: CustomerModel) -> Customer:
        return Customer(
            name=model.name,
            default_address=model.default_address,
            is_active=model.is_active,
            id=model.id,
        )

    def _to_values(self, entity: Customer) -> dict:
        return {
            "name": entity.name,
            "default_address": entity.default_address,
            "is_active": entity.is_active,
        }


class RawMaterialCatalogRepository(
    BaseCatalogRepository[RawMaterialCatalog, RawMaterialCatalogModel],
    IRawMaterialCatalogRepository,
):
    @property
    def _model_class(self) -> type[RawMaterialCatalogModel]:
        return RawMaterialCatalogModel

    def _to_entity(self, model: RawMaterialCatalogModel) -> RawMaterialCatalog:
        return RawMaterialCatalog(
            name=model.name,
            unit=model.unit,
            shelf_life_days=model.shelf_life_days,
            critical_stock=Decimal(str(model.critical_stock)),
            is_active=model.is_active,
            id=model.id,
        )

    def _to_values(self, entity: RawMaterialCatalog) -> dict:
        return {
            "name": entity.name,
            "unit": entity.unit,
            "shelf_life_days": entity.shelf_life_days,
            "critical_stock": entity.critical_stock,
            "is_active": entity.is_active,
        }


class PackagingCatalogRepository(
    BaseCatalogRepository[PackagingCatalog, PackagingCatalogModel],
    IPackagingCatalogRepository,
):
    @property
    def _model_class(self) -> type[PackagingCatalogModel]:
        return PackagingCatalogModel

    def _to_entity(self, model: PackagingCatalogModel) -> PackagingCatalog:
        return PackagingCatalog(
            name=model.name,
            unit=model.unit,
            critical_stock=model.critical_stock,
            is_active=model.is_active,
            id=model.id,
        )

    def _to_values(self, entity: PackagingCatalog) -> dict:
        return {
            "name": entity.name,
            "unit": entity.unit,
            "critical_stock": entity.critical_stock,
            "is_active": entity.is_active,
        }


class ProductRepository(
    BaseCatalogRepository[Product, ProductModel],
    IProductRepository,
):
    @property
    def _model_class(self) -> type[ProductModel]:
        return ProductModel

    def _to_values(self, entity: Product) -> dict:
        return {
            "name": entity.name,
            "units_per_box": entity.units_per_box,
            "shelf_life_days": entity.shelf_life_days,
            "critical_stock": entity.critical_stock,
            "is_active": entity.is_active,
        }

    async def get_by_id(self, id: int) -> Product | None:
        stmt = (
            select(ProductModel)
            .options(selectinload(ProductModel.recipe))
            .where(ProductModel.id == id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_all(self, include_inactive: bool = False) -> list[Product]:
        stmt = select(ProductModel).options(selectinload(ProductModel.recipe))
        if not include_inactive:
            stmt = stmt.where(ProductModel.is_active.is_(True))
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def save(self, product: Product) -> int:
        await super().save(product)
        await self._sync_recipe(product.id, product.recipe)
        return product.id

    async def _sync_recipe(self, product_id: int, lines: list[RecipeLine]) -> None:
        existing_ids = {line.id for line in lines if line.id is not None}

        stmt = delete(RecipeLineModel).where(RecipeLineModel.product_id == product_id)
        if existing_ids:
            stmt = stmt.where(RecipeLineModel.id.not_in(existing_ids))
        await self._session.execute(stmt)

        for line in lines:
            if line.id is None:
                model = RecipeLineModel(
                    product_id=product_id,
                    raw_material_id=line.raw_material_id,
                    consumption_per_unit=line.consumption_per_unit,
                    waste_percentage=line.waste_percentage,
                )
                self._session.add(model)
                await self._session.flush()
                line.id = model.id
            else:
                await self._session.execute(
                    update(RecipeLineModel)
                    .where(RecipeLineModel.id == line.id)
                    .values(
                        consumption_per_unit=line.consumption_per_unit,
                        waste_percentage=line.waste_percentage,
                    )
                )

    def _to_entity(self, model: ProductModel) -> Product:
        return Product(
            name=model.name,
            units_per_box=model.units_per_box,
            shelf_life_days=model.shelf_life_days,
            critical_stock=model.critical_stock,
            is_active=model.is_active,
            recipe=[
                RecipeLine(
                    raw_material_id=line.raw_material_id,
                    consumption_per_unit=Decimal(str(line.consumption_per_unit)),
                    waste_percentage=Decimal(str(line.waste_percentage)),
                    id=line.id,
                )
                for line in model.recipe
            ],
            id=model.id,
        )
