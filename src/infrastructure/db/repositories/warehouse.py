from sqlalchemy import func, select

from src.domain.warehouse.entities import PackagingStock, ProductStock, RawMaterialStock
from src.domain.warehouse.interfaces import (
    IPackagingStockRepository,
    IProductStockRepository,
    IRawMaterialStockRepository,
)
from src.infrastructure.db.models.warehouse import (
    PackagingStockModel,
    ProductStockModel,
    RawMaterialStockModel,
)
from src.infrastructure.db.repositories.base import BasePlainRepository


class RawMaterialStockRepository(
    BasePlainRepository[RawMaterialStock, RawMaterialStockModel],
    IRawMaterialStockRepository,
):
    @property
    def _model_class(self) -> type[RawMaterialStockModel]:
        return RawMaterialStockModel

    def _to_entity(self, model: RawMaterialStockModel) -> RawMaterialStock:
        return RawMaterialStock(
            id=model.id,
            raw_material_id=model.raw_material_id,
            quantity=model.quantity,
            arrival_date=model.arrival_date,
            expiry_date=model.expiry_date,
            comment=model.comment,
        )

    def _to_values(self, entity: RawMaterialStock) -> dict:
        return {
            "raw_material_id": entity.raw_material_id,
            "quantity": entity.quantity,
            "arrival_date": entity.arrival_date,
            "expiry_date": entity.expiry_date,
            "comment": entity.comment,
        }

    async def get_by_raw_material(self, raw_material_id: int) -> list[RawMaterialStock]:
        stmt = select(RawMaterialStockModel).where(
            RawMaterialStockModel.raw_material_id == raw_material_id
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]


class PackagingStockRepository(
    BasePlainRepository[PackagingStock, PackagingStockModel],
    IPackagingStockRepository,
):
    @property
    def _model_class(self) -> type[PackagingStockModel]:
        return PackagingStockModel

    def _to_entity(self, model: PackagingStockModel) -> PackagingStock:
        return PackagingStock(
            id=model.id,
            packaging_id=model.packaging_id,
            quantity=model.quantity,
            comment=model.comment,
        )

    def _to_values(self, entity: PackagingStock) -> dict:
        return {
            "packaging_id": entity.packaging_id,
            "quantity": entity.quantity,
            "comment": entity.comment,
        }

    async def get_by_packaging(self, packaging_id: int) -> list[PackagingStock]:
        stmt = select(PackagingStockModel).where(
            PackagingStockModel.packaging_id == packaging_id
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]


class ProductStockRepository(
    BasePlainRepository[ProductStock, ProductStockModel],
    IProductStockRepository,
):
    @property
    def _model_class(self) -> type[ProductStockModel]:
        return ProductStockModel

    def _to_entity(self, model: ProductStockModel) -> ProductStock:
        return ProductStock(
            id=model.id,
            product_id=model.product_id,
            quantity=model.quantity,
            batch_number=model.batch_number,
            batch_year=model.batch_year,
            arrival_date=model.arrival_date,
            expiry_date=model.expiry_date,
            comment=model.comment,
        )

    def _to_values(self, entity: ProductStock) -> dict:
        return {
            "product_id": entity.product_id,
            "quantity": entity.quantity,
            "batch_number": entity.batch_number,
            "batch_year": entity.batch_year,
            "arrival_date": entity.arrival_date,
            "expiry_date": entity.expiry_date,
            "comment": entity.comment,
        }

    async def get_by_product(self, product_id: int) -> list[ProductStock]:
        stmt = select(ProductStockModel).where(ProductStockModel.product_id == product_id)
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_last_batch_number(self, year: int) -> int:
        stmt = select(func.max(ProductStockModel.batch_number)).where(
            ProductStockModel.batch_year == year
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0
