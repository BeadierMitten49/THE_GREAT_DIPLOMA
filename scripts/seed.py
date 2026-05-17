"""Seed script: populate DB with test data."""
import asyncio
import sys
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, ".")

from src.application.auth.dto import CreateUserDTO, SetUserRolesDTO
from src.application.auth.use_cases import create_user, set_user_roles
from src.application.orders.dto import CreateOrderDTO
from src.application.orders.use_cases import create_order
from src.application.references.dto import (
    CreateCustomerDTO,
    CreatePackagingDTO,
    CreateProductDTO,
    CreateRawMaterialDTO,
    RecipeLineDTO,
)
from src.application.references.use_cases import (
    create_customer,
    create_packaging,
    create_product,
    create_raw_material,
    set_product_recipe,
)
from src.application.tasks.dto import CreateTaskDTO
from src.application.tasks.use_cases import create_task
from src.application.warehouse.dto import (
    PackagingStockArrivalDTO,
    ProductStockArrivalDTO,
    RawMaterialStockArrivalDTO,
)
from src.application.warehouse.use_cases import (
    packaging_stock_arrival,
    product_stock_arrival,
    raw_material_stock_arrival,
)
from src.domain.auth.value_objects import Role
from src.domain.tasks.value_objects import TaskType
from src.infrastructure.db.repositories.auth import UserCredentialRepository, UserRepository
from src.infrastructure.db.repositories.references import (
    CustomerRepository,
    PackagingCatalogRepository,
    ProductRepository,
    RawMaterialCatalogRepository,
)
from src.infrastructure.db.repositories.warehouse import (
    PackagingStockRepository,
    ProductStockRepository,
    RawMaterialStockRepository,
)
from src.infrastructure.db.repositories.orders import OrderItemRepository, OrderRepository, ProductReservationRepository
from src.infrastructure.db.repositories.tasks import ProductionTaskRepository, RawMaterialReservationRepository
from src.infrastructure.db.session import AsyncSessionFactory
from src.infrastructure.security.password_hasher import BcryptPasswordHasher

TODAY = date.today()


async def main() -> None:
    hasher = BcryptPasswordHasher()

    async with AsyncSessionFactory() as session:
        user_repo = UserRepository(session)
        cred_repo = UserCredentialRepository(session)
        customer_repo = CustomerRepository(session)
        product_repo = ProductRepository(session)
        raw_repo = RawMaterialCatalogRepository(session)
        pack_repo = PackagingCatalogRepository(session)
        rm_stock_repo = RawMaterialStockRepository(session)
        pack_stock_repo = PackagingStockRepository(session)
        prod_stock_repo = ProductStockRepository(session)
        order_repo = OrderRepository(session)
        order_item_repo = OrderItemRepository(session)
        reservation_repo = ProductReservationRepository(session)
        task_repo = ProductionTaskRepository(session)
        rm_res_repo = RawMaterialReservationRepository(session)

        # ── Users ──────────────────────────────────────────────────────────────
        print("Creating users...")
        warehouse_id = await create_user(
            CreateUserDTO(full_name="Иванов Сергей", password="warehouse123"),
            user_repo, cred_repo, hasher,
        )
        await set_user_roles(warehouse_id, SetUserRolesDTO(roles=[Role.warehouse]), user_repo)

        production_id = await create_user(
            CreateUserDTO(full_name="Петров Алексей", password="production123"),
            user_repo, cred_repo, hasher,
        )
        await set_user_roles(production_id, SetUserRolesDTO(roles=[Role.production]), user_repo)

        delivery_id = await create_user(
            CreateUserDTO(full_name="Сидоров Михаил", password="delivery123"),
            user_repo, cred_repo, hasher,
        )
        await set_user_roles(delivery_id, SetUserRolesDTO(roles=[Role.delivery]), user_repo)

        # ── Customers ──────────────────────────────────────────────────────────
        print("Creating customers...")
        c1 = await create_customer(CreateCustomerDTO(name="ООО Ромашка", default_address="г. Москва, ул. Ленина, 1"), customer_repo)
        c2 = await create_customer(CreateCustomerDTO(name="ИП Сидоров", default_address="г. Санкт-Петербург, пр. Невский, 25"), customer_repo)
        c3 = await create_customer(CreateCustomerDTO(name="АО Прогресс", default_address="г. Казань, ул. Баумана, 10"), customer_repo)

        # ── Raw materials ──────────────────────────────────────────────────────
        print("Creating raw materials...")
        sugar_id = await create_raw_material(
            CreateRawMaterialDTO(name="Сахар", unit="кг", shelf_life_days=730, critical_stock=Decimal("50")),
            raw_repo,
        )
        flour_id = await create_raw_material(
            CreateRawMaterialDTO(name="Мука пшеничная", unit="кг", shelf_life_days=180, critical_stock=Decimal("100")),
            raw_repo,
        )
        salt_id = await create_raw_material(
            CreateRawMaterialDTO(name="Соль", unit="кг", shelf_life_days=1825, critical_stock=Decimal("20")),
            raw_repo,
        )
        oil_id = await create_raw_material(
            CreateRawMaterialDTO(name="Масло подсолнечное", unit="л", shelf_life_days=365, critical_stock=Decimal("30")),
            raw_repo,
        )

        # ── Packaging ──────────────────────────────────────────────────────────
        print("Creating packaging...")
        box_small_id = await create_packaging(
            CreatePackagingDTO(name="Коробка малая 0.5кг", unit="шт", critical_stock=200),
            pack_repo,
        )
        box_large_id = await create_packaging(
            CreatePackagingDTO(name="Коробка большая 1кг", unit="шт", critical_stock=100),
            pack_repo,
        )
        bag_id = await create_packaging(
            CreatePackagingDTO(name="Пакет полиэтиленовый", unit="шт", critical_stock=500),
            pack_repo,
        )

        # ── Products ───────────────────────────────────────────────────────────
        print("Creating products...")
        prod1_id = await create_product(
            CreateProductDTO(name="Сахар фасованный 0.5кг", units_per_box=20, shelf_life_days=730, critical_stock=50),
            product_repo,
        )
        await set_product_recipe(prod1_id, [
            RecipeLineDTO(raw_material_id=sugar_id, consumption_per_unit=Decimal("0.5"), waste_percentage=Decimal("1")),
        ], product_repo)

        prod2_id = await create_product(
            CreateProductDTO(name="Соль фасованная 1кг", units_per_box=10, shelf_life_days=1825, critical_stock=30),
            product_repo,
        )
        await set_product_recipe(prod2_id, [
            RecipeLineDTO(raw_material_id=salt_id, consumption_per_unit=Decimal("1.0"), waste_percentage=Decimal("0.5")),
        ], product_repo)

        prod3_id = await create_product(
            CreateProductDTO(name="Мука пшеничная 1кг", units_per_box=10, shelf_life_days=180, critical_stock=20),
            product_repo,
        )
        await set_product_recipe(prod3_id, [
            RecipeLineDTO(raw_material_id=flour_id, consumption_per_unit=Decimal("1.0"), waste_percentage=Decimal("2")),
        ], product_repo)

        # ── Raw material stock ─────────────────────────────────────────────────
        print("Creating stock...")
        await raw_material_stock_arrival(
            RawMaterialStockArrivalDTO(
                raw_material_id=sugar_id, quantity=Decimal("500"),
                arrival_date=TODAY - timedelta(days=10),
                expiry_date=TODAY + timedelta(days=720),
                comment="Партия от поставщика",
            ), rm_stock_repo,
        )
        await raw_material_stock_arrival(
            RawMaterialStockArrivalDTO(
                raw_material_id=flour_id, quantity=Decimal("300"),
                arrival_date=TODAY - timedelta(days=5),
                expiry_date=TODAY + timedelta(days=175),
                comment=None,
            ), rm_stock_repo,
        )
        await raw_material_stock_arrival(
            RawMaterialStockArrivalDTO(
                raw_material_id=salt_id, quantity=Decimal("200"),
                arrival_date=TODAY - timedelta(days=30),
                expiry_date=TODAY + timedelta(days=1800),
                comment=None,
            ), rm_stock_repo,
        )
        await raw_material_stock_arrival(
            RawMaterialStockArrivalDTO(
                raw_material_id=oil_id, quantity=Decimal("50"),
                arrival_date=TODAY - timedelta(days=7),
                expiry_date=TODAY + timedelta(days=358),
                comment=None,
            ), rm_stock_repo,
        )

        # ── Packaging stock ────────────────────────────────────────────────────
        await packaging_stock_arrival(
            PackagingStockArrivalDTO(packaging_id=box_small_id, quantity=1000, comment="Начальный остаток"),
            pack_stock_repo,
        )
        await packaging_stock_arrival(
            PackagingStockArrivalDTO(packaging_id=box_large_id, quantity=500, comment=None),
            pack_stock_repo,
        )
        await packaging_stock_arrival(
            PackagingStockArrivalDTO(packaging_id=bag_id, quantity=2000, comment=None),
            pack_stock_repo,
        )

        # ── Product stock ──────────────────────────────────────────────────────
        await product_stock_arrival(
            ProductStockArrivalDTO(
                product_id=prod1_id, quantity=200,
                arrival_date=TODAY - timedelta(days=3),
                expiry_date=TODAY + timedelta(days=727),
                comment="Готовая продукция",
            ), prod_stock_repo,
        )
        await product_stock_arrival(
            ProductStockArrivalDTO(
                product_id=prod2_id, quantity=100,
                arrival_date=TODAY - timedelta(days=1),
                expiry_date=TODAY + timedelta(days=1824),
                comment=None,
            ), prod_stock_repo,
        )

        # ── Orders ─────────────────────────────────────────────────────────────
        print("Creating orders...")
        await create_order(
            CreateOrderDTO(
                customer_id=c1,
                delivery_address="г. Москва, ул. Ленина, 1",
                delivery_date=TODAY + timedelta(days=3),
                items=[(prod1_id, 50), (prod2_id, 20)],
                delivery_user_id=delivery_id,
                comment="Срочный заказ",
            ),
            order_repo, order_item_repo,
        )
        await create_order(
            CreateOrderDTO(
                customer_id=c2,
                delivery_address="г. Санкт-Петербург, пр. Невский, 25",
                delivery_date=TODAY + timedelta(days=7),
                items=[(prod1_id, 30)],
                delivery_user_id=None,
                comment=None,
            ),
            order_repo, order_item_repo,
        )
        await create_order(
            CreateOrderDTO(
                customer_id=c3,
                delivery_address="г. Казань, ул. Баумана, 10",
                delivery_date=TODAY + timedelta(days=14),
                items=[(prod2_id, 40), (prod3_id, 10)],
                delivery_user_id=delivery_id,
                comment="Стандартная поставка",
            ),
            order_repo, order_item_repo,
        )

        # ── Production tasks ───────────────────────────────────────────────────
        print("Creating tasks...")
        await create_task(
            CreateTaskDTO(
                product_id=prod1_id,
                quantity=100,
                executor_id=production_id,
                start_date=TODAY,
                deadline=TODAY + timedelta(days=2),
                task_type=TaskType.stock_task,
                comment="Пополнение склада",
            ),
            task_repo, product_repo, rm_stock_repo, rm_res_repo,
        )
        await create_task(
            CreateTaskDTO(
                product_id=prod3_id,
                quantity=50,
                executor_id=production_id,
                start_date=TODAY + timedelta(days=1),
                deadline=TODAY + timedelta(days=5),
                task_type=TaskType.stock_task,
                comment=None,
            ),
            task_repo, product_repo, rm_stock_repo, rm_res_repo,
        )

        await session.commit()
        print()
        print("Done! Test users:")
        print(f"  Склад:       ivanov_sergey / warehouse123")
        print(f"  Производство: petrov_aleksey / production123")
        print(f"  Доставка:    sidorov_mikhail / delivery123")


asyncio.run(main())
