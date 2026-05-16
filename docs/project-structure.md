# Структура проекта АИС «Ярко»

Стек: **FastAPI** + **SQLAlchemy** + **PostgreSQL**. Прототип UI — **Streamlit**.
Архитектурный подход: **Domain-Driven Design (DDD)**.

```
yarko/
│
├── src/
│   │
│   ├── domain/                        ← Чистая бизнес-логика. Нет зависимостей на фреймворки.
│   │   │
│   │   ├── references/                ← ✅ реализован
│   │   │   ├── entities.py            ← Customer, Product, RecipeLine, RawMaterialCatalog, PackagingCatalog
│   │   │   ├── interfaces.py          ← ICustomerRepository, IProductRepository, ...
│   │   │   └── exceptions.py         ← InvalidFieldError, DomainError
│   │   │
│   │   ├── orders/
│   │   │   ├── entities.py            ← Order, OrderItem
│   │   │   ├── value_objects.py       ← OrderStatus
│   │   │   ├── services.py            ← доменные сервисы (проверка остатков при создании)
│   │   │   └── interfaces.py
│   │   │
│   │   ├── tasks/
│   │   │   ├── entities.py            ← ProductionTask, TaskReport
│   │   │   ├── value_objects.py       ← TaskStatus, RawMaterialConsumption
│   │   │   ├── services.py            ← расчёт потребности в сырье по рецептуре
│   │   │   └── interfaces.py
│   │   │
│   │   ├── warehouse/
│   │   │   ├── entities.py            ← RawMaterial, Packaging, FinishedGoods, Batch
│   │   │   ├── value_objects.py       ← StockReservation, BatchNumber
│   │   │   ├── services.py            ← проверка критического остатка
│   │   │   └── interfaces.py
│   │   │
│   │   ├── delivery/
│   │   │   ├── entities.py            ← Delivery
│   │   │   ├── value_objects.py       ← DeliveryStatus
│   │   │   └── interfaces.py
│   │   │
│   │   ├── auth/                      ← ✅ реализован
│   │   │   ├── entities.py            ← User
│   │   │   ├── value_objects.py       ← Role (StrEnum)
│   │   │   ├── interfaces.py          ← IUserRepository
│   │   │   └── exceptions.py
│   │   │
│   │   └── shared/                    ← Общие примитивы домена
│   │       ├── repository.py          ← IRepository[T] — generic base interface
│   │       └── events.py              ← доменные события (TaskCompleted и т.д.)
│   │
│   ├── application/                   ← Use cases. Оркестрирует домен. Не знает о HTTP/БД.
│   │   │
│   │   ├── references/                ← ✅ реализован
│   │   │   ├── use_cases.py           ← чистые async-функции: get_customer, create_customer, ...
│   │   │   ├── dto.py                 ← frozen dataclasses: CreateCustomerDTO, UpdateCustomerDTO, ...
│   │   │   └── exceptions.py         ← NotFoundError, AlreadyExistsError
│   │   │
│   │   ├── orders/
│   │   │   ├── use_cases.py           ← create_order, change_order_status, ...
│   │   │   ├── dto.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── tasks/
│   │   │   ├── use_cases.py           ← create_task, start_task, stop_task, complete_task, close_task
│   │   │   ├── dto.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── warehouse/
│   │   │   ├── use_cases.py           ← stock_arrival, write_off, reserve, release, ship
│   │   │   ├── dto.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── delivery/
│   │   │   ├── use_cases.py           ← start_delivery, complete_delivery, cancel_delivery
│   │   │   ├── dto.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── auth/                      ← ✅ реализован
│   │   │   ├── use_cases.py           ← create_user, deactivate_user, reset_password, bind_telegram, login, refresh_tokens, logout
│   │   │   ├── dto.py                 ← CreateUserDTO, LoginDTO, TokenPairDTO, ...
│   │   │   └── exceptions.py         ← AuthenticationError, RateLimitError, InvalidTokenError
│   │   │
│   │   └── ports/                     ← Интерфейсы для внешних сервисов
│   │       ├── auth.py                ← IUserCredentialRepository, IRefreshTokenRepository, IAuthLogRepository, IPasswordHasher, IJWTService
│   │       └── notification_port.py   ← INotificationService (реализация — в infrastructure)
│   │
│   ├── infrastructure/                ← Реализации интерфейсов. Зависит на фреймворки и БД.
│   │   │
│   │   ├── db/
│   │   │   ├── models/                ← SQLAlchemy-модели (ORM)
│   │   │   │   ├── __init__.py        ← Annotated-типы: intpk, str_nn, bool_active
│   │   │   │   ├── references.py      ← ✅ CustomerModel, ProductModel, RecipeLineModel, ...
│   │   │   │   ├── auth.py            ← ✅ UserModel, UserCredentialModel, UserRoleModel, AuthLogModel, RefreshTokenModel
│   │   │   │   ├── order.py
│   │   │   │   ├── production.py
│   │   │   │   ├── warehouse.py
│   │   │   │   └── delivery.py
│   │   │   ├── repositories/          ← реализации IXxxRepository
│   │   │   │   ├── base.py            ← BaseRepository, BaseCatalogRepository
│   │   │   │   ├── references.py      ← ✅ CustomerRepository, ProductRepository, ...
│   │   │   │   ├── auth.py            ← ✅ UserRepository, UserCredentialRepository, RefreshTokenRepository, AuthLogRepository
│   │   │   │   ├── order_repo.py
│   │   │   │   ├── production_repo.py
│   │   │   │   ├── warehouse_repo.py
│   │   │   │   └── delivery_repo.py
│   │   │   ├── migrations/            ← Alembic
│   │   │   └── session.py
│   │   │
│   │   ├── security/                  ← ✅ реализован
│   │   │   ├── password_hasher.py     ← BcryptPasswordHasher (реализация IPasswordHasher)
│   │   │   └── jwt_service.py         ← JWTService (реализация IJWTService)
│   │   │
│   │   ├── telegram/
│   │   │   ├── bot.py                 ← инициализация, обработка /start → привязка Telegram ID
│   │   │   └── notification_service.py← реализация INotificationService
│   │   │
│   │   └── config.py                  ← env-переменные (pydantic BaseSettings)
│   │
│   └── presentation/                  ← Точки входа. Зависит только на application/.
│       │
│       ├── api/
│       │   ├── exception_handlers.py  ← глобальный маппинг исключений → HTTP-статусы
│       │   └── v1/
│       │       ├── __init__.py        ← корневой APIRouter
│       │       ├── references/        ← ✅ реализован
│       │       │   ├── __init__.py    ← router с prefix /references
│       │       │   ├── customers.py   ← роутер /customers
│       │       │   ├── products.py    ← роутер /products
│       │       │   ├── raw_materials.py
│       │       │   ├── packaging.py
│       │       │   ├── service.py     ← CustomerService, ProductService, ... (фасад над use cases)
│       │       │   ├── schemas.py     ← Pydantic request/response схемы
│       │       │   └── dependencies.py← get_customer_service, ...
│       │       ├── auth/
│       │       ├── orders/
│       │       └── ...
│       │
│       └── streamlit/                 ← Прототип UI для демонстрации
│           ├── app.py
│           └── pages/
│
├── tests/
│   ├── conftest.py                    ← регистрация маркеров: unit, integration, smoke
│   ├── unit/
│   │   ├── domain/                    ← тесты сущностей (без БД, без фреймворков)
│   │   ├── application/               ← тесты use cases (fake-репозитории в памяти)
│   │   └── infrastructure/            ← тесты инфраструктурных сервисов (security и др.)
│   └── integration/
│       ├── db/repositories/           ← тесты репозиториев (SQLite aiosqlite, savepoint-rollback)
│       └── api/                       ← тесты API (httpx.AsyncClient + dependency_overrides)
│
├── logs/                              ← gitignored
├── docs/
├── wiki/
│   └── entities/                      ← в git; остальное gitignored
│
├── main.py                            ← точка входа: собирает app, подключает роутеры и handlers
├── .env.example
├── .gitignore
└── docker-compose.yml
```

## Правила зависимостей (DDD)

```
presentation → application → domain
infrastructure → domain (реализует интерфейсы)
```

`domain/` не импортирует ничего кроме `shared/`. `application/` не знает о SQLAlchemy и FastAPI. `presentation/` не лезет в репозитории напрямую — только через сервисы.

## Ключевые решения

### Application layer: функции, не классы

Use cases реализованы как чистые `async`-функции. Репозитории передаются явно как аргументы:

```python
async def create_customer(dto: CreateCustomerDTO, repo: ICustomerRepository) -> int:
    ...
```

Не используются классы-обёртки (`class CreateCustomerUseCase`). Причины:
- Нет скрытого состояния — всё видно из сигнатуры
- Легко тестировать: просто передай fake-репозиторий
- Легко комбинировать: один use case может вызвать другой без создания объектов

DTO — frozen dataclasses (не Pydantic). Application-слой не зависит на Pydantic.

### Presentation: service-класс как фасад

Роутер не знает про репозитории и DTO. Вместо этого — service-класс на каждый агрегат:

```python
class CustomerService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = CustomerRepository(session)  # создаёт репо сам

    async def create(self, name: str, default_address: str) -> int:
        return await create_customer(CreateCustomerDTO(name, default_address), self._repo)
```

Роутер видит только `service.create(name, address)` — без DTO, без репозиториев. Причины:
- Роутер отвечает только за HTTP: принять запрос → вызвать → вернуть ответ
- Смена репозитория или DTO не затрагивает роутер
- Сервис можно переиспользовать из разных роутеров или Streamlit

### Exception handlers: единое место в presentation

Маппинг исключений → HTTP-статусы живёт в `presentation/api/exception_handlers.py`, регистрируется в `main.py` одной строкой:

```
NotFoundError      → 404
AlreadyExistsError → 409
InvalidFieldError  → 422
```

Не в роутерах (дублирование по всем ручкам) и не в `main.py` напрямую (не его ответственность). Новые исключения будущих модулей добавляются в тот же файл.

### Infrastructure: generic base repository

`BaseCatalogRepository[TEntity, TModel]` реализует общую логику `get_by_id`, `get_all`, `save`, `exists_by_name`. Конкретный репозиторий определяет только `_model_class`, `_to_entity`, `_to_values`. Это устраняет дублирование без нарушения DDD: интерфейс остаётся в `domain/`, реализация в `infrastructure/`.

### Прочее

**`IRepository[T]`** в `domain/shared/` — generic base interface (Python 3.12+, без `TypeVar`). Все репозитории наследуются от него.

**`ports/notification_port.py`** — application-слой знает только об интерфейсе `INotificationService`. Telegram — деталь инфраструктуры.

**`auth_log`** — таблица в БД, не файл. Нужна для отчётности и фильтрации через интерфейс.

**`streamlit/`** — только для прототипирования и показа. Не production UI.
