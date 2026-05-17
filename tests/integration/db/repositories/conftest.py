import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from src.infrastructure.db.models import Base
from src.infrastructure.db.models.auth import (  # noqa: F401 — register models
    AuthLogModel,
    RefreshTokenModel,
    UserCredentialModel,
    UserModel,
    UserRoleModel,
)
from src.infrastructure.db.models.references import (  # noqa: F401 — register models
    CustomerModel,
    PackagingCatalogModel,
    ProductModel,
    RawMaterialCatalogModel,
    RecipeLineModel,
)
from src.infrastructure.db.models.orders import (  # noqa: F401 — register models
    OrderItemModel,
    OrderModel,
    ProductReservationModel,
)
from src.infrastructure.db.models.warehouse import (  # noqa: F401 — register models
    PackagingStockModel,
    ProductStockModel,
    RawMaterialStockModel,
)
from src.infrastructure.db.models.tasks import (  # noqa: F401 — register models
    ProductionTaskModel,
    RawMaterialReservationModel,
    TaskCompletionConsumptionModel,
    TaskCompletionModel,
    TaskStopModel,
)
from src.infrastructure.db.models.delivery import DeliveryModel  # noqa: F401 — register models


@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine):
    async with engine.connect() as conn:
        trans = await conn.begin()
        async with AsyncSession(bind=conn, join_transaction_mode="create_savepoint") as s:
            yield s
        await trans.rollback()
