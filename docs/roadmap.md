# Roadmap — АИС «Ярко»

Порядок разработки соответствует зависимостям между модулями.
Каждый модуль = ветка `feature/<module>` от `develop`.

## Соглашения по слоям

**Application** — use cases как чистые `async`-функции, репозитории передаются явно:
```python
async def create_customer(dto: CreateCustomerDTO, repo: ICustomerRepository) -> int
```
DTO — frozen dataclasses. Исключения: `NotFoundError`, `AlreadyExistsError` в `exceptions.py`.

**Presentation** — service-класс на каждый агрегат скрывает создание репо и DTO от роутера:
```python
class CustomerService:
    def __init__(self, session: AsyncSession) -> None: ...
    async def create(self, name: str, ...) -> int: ...
```
Роутер вызывает только методы сервиса. Exception handlers — в `presentation/api/exception_handlers.py`.

**Tests** — четыре уровня на каждый модуль:
1. Unit domain — чистые сущности, без БД
2. Unit use cases — fake-репозитории в памяти
3. Integration repo — SQLite aiosqlite, savepoint-rollback
4. Integration API — `httpx.AsyncClient` + `dependency_overrides`

---

## Phase 0 — Setup ✅
- [x] Документация проекта (CLAUDE.md, docs/)
- [x] Схема БД и ERD
- [x] Git workflow
- [x] Инициализация проекта (FastAPI, DDD структура, Alembic, логирование)

---

## Phase 1 — References (справочники) ✅
> Ветка: `feature/references` → влита в `develop`

**Domain**
- [x] `customers` — entity
- [x] `products` — entity (units_per_box, shelf_life_days, critical_stock)
- [x] `raw_materials_catalog` — entity
- [x] `packaging_catalog` — entity
- [x] `recipes` — entity (consumption_per_unit, waste_percentage)
- [x] `IRepository[T]` — generic base interface в `domain/shared/`

**Infrastructure**
- [x] SQLAlchemy модели для всех справочников
- [x] `BaseCatalogRepository[TEntity, TModel]` — generic base repo
- [x] Репозитории (CRUD + деактивация)
- [x] Alembic миграция

**Application**
- [x] Use cases: `get_*`, `create_*`, `update_*`, `deactivate_*`, `activate_*` для каждого справочника
- [x] `set_product_recipe` — атомарная замена рецептуры
- [x] DTO, `NotFoundError`, `AlreadyExistsError`

**Presentation**
- [x] Service-классы: `CustomerService`, `ProductService`, `RawMaterialService`, `PackagingService`
- [x] CRUD эндпоинты для каждого справочника (`/api/v1/references/*`)
- [x] Pydantic схемы, dependencies
- [x] Exception handlers в `presentation/api/exception_handlers.py`

**Tests**
- [x] Unit тесты domain (55)
- [x] Unit тесты use cases (43)
- [x] Integration тесты репозиториев (25)
- [x] Integration тесты API (48)

---

## Phase 2 — Auth
> Ветка: `feature/auth`

**Domain**
- [x] `User` entity, `Role` value object
- [x] `IUserRepository` интерфейс

**Infrastructure**
- [x] SQLAlchemy модели: `users`, `user_roles`, `auth_log`, `refresh_tokens`
- [x] Репозитории
- [x] Alembic миграция

**Application**
- [x] Use cases: `create_user`, `deactivate_user`, `reset_password`, `bind_telegram`
- [x] Use cases auth: `login`, `refresh_tokens`, `logout`
- [x] `INotificationService` port (заглушка, реализация — в Phase 7)
- [x] Rate limit логика: блокировка после 5 неудачных попыток на 30 минут

**Presentation**
- [x] `AuthService`, `UserService`
- [x] `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`
- [x] Эндпоинты управления пользователями (только директор)
- [x] `dependencies.py` — `get_current_user`, `require_role(...)`

**Tests**
- [x] Unit тесты domain
- [x] Unit тесты use cases
- [x] Integration тесты репозиториев
- [x] Integration тесты API: login, refresh, блокировка

---

## Phase 3 — Warehouse (склад) ✅
> Ветка: `feature/warehouse` → влита в `develop`

**Domain**
- [x] `RawMaterialStock` entity (quantity: Decimal, arrival_date, expiry_date, write_off)
- [x] `PackagingStock` entity (quantity: int, write_off)
- [x] `ProductStock` entity (quantity: int, batch_number, batch_year, expiry_date, write_off)
- [x] `IRawMaterialStockRepository`, `IPackagingStockRepository`, `IProductStockRepository`

> `RawMaterialReservation` → `domain/production`, `ProductReservation` → `domain/orders`

**Infrastructure**
- [x] SQLAlchemy модели: `raw_material_stock`, `packaging_stock`, `products_stock`
- [x] Репозитории
- [x] Alembic миграция

**Application**
- [x] Use cases сырья: `get_raw_material_stock`, `get_raw_material_stocks`, `get_raw_material_stocks_by_material`, `raw_material_stock_arrival`, `raw_material_stock_write_off`
- [x] Use cases упаковки: `get_packaging_stock`, `get_packaging_stocks`, `get_packaging_stocks_by_packaging`, `packaging_stock_arrival`, `packaging_stock_write_off`
- [x] Use cases продукции: `get_product_stock`, `get_product_stocks`, `get_product_stocks_by_product`, `product_stock_arrival`, `product_stock_write_off` (ручное списание директором)

> `ship_product_stock` → Phase 5 (orders, при смене статуса «Сборка → Доставка»)
> `reserve_raw_material_stock` / `release_raw_material_stock` → Phase 4 (production)
> `reserve_product_stock` / `release_product_stock` → Phase 5 (orders)

**Presentation**
- [x] Service-классы: `RawMaterialStockService`, `PackagingStockService`, `ProductStockService`
- [x] Эндпоинты: `/raw-material-stock`, `/packaging-stock`, `/product-stock`
- [x] RBAC: `director_or_warehouse` на всех, `director_only` на `product-stock/{id}/write-off`

**Refactoring**
- [x] `NotFoundError` вынесен в `application/shared/exceptions.py` (единый для всех модулей)

**Tests**
- [x] Unit тесты domain: write_off (граничные случаи), batch_number
- [x] Unit тесты use cases (28)
- [x] Integration тесты репозиториев (20)
- [x] Integration тесты API (27)

---

## Phase 4 — Orders (заказы)
> Ветка: `feature/orders`

**Domain**
- [ ] `Order` entity, `OrderStatus` value object
- [ ] `OrderItem` entity
- [ ] `ProductReservation` entity (stock_id, order_id, quantity) — из warehouse
- [ ] `IOrderRepository`, `IOrderItemRepository`, `IProductReservationRepository`

**Infrastructure**
- [ ] SQLAlchemy модели: `orders`, `order_items`
- [ ] Репозитории
- [ ] Alembic миграция

**Application**
- [ ] Use cases: `create_order`, `change_order_status`, `edit_order`, `delete_order`
- [ ] Логика резервирования продукции при переходе в «Сборка»
- [ ] Аварийное снятие резерва директором

**Presentation**
- [ ] `OrderService`
- [ ] Эндпоинты заказов
- [ ] Эндпоинт аварийного снятия резерва

**Tests**
- [ ] Unit тесты domain: логика начального статуса, переходы состояний
- [ ] Unit тесты use cases
- [ ] Integration тесты репозиториев
- [ ] Integration тесты API: полный цикл заказа

---

## Phase 5 — Tasks (производственные задачи)
> Ветка: `feature/tasks`

**Domain**
- [ ] `ProductionTask` entity, `TaskStatus` value object
- [ ] `TaskStop` entity
- [ ] `TaskCompletion` entity
- [ ] `TaskCompletionConsumption` entity
- [ ] `RawMaterialReservation` entity (stock_id, task_id, quantity) — из warehouse
- [ ] `IRawMaterialReservationRepository`
- [ ] Domain service: расчёт потребности в сырье по рецептуре (с % брака)

**Infrastructure**
- [ ] SQLAlchemy модели: `production_tasks`, `task_stops`, `task_completions`, `task_completion_consumption`
- [ ] Репозитории
- [ ] Alembic миграция

**Application**
- [ ] Use cases: `create_task`, `start_task`, `stop_task`, `resume_task`, `complete_task`, `close_task`
- [ ] Use cases: `reassign_task`, `delete_task`
- [ ] Логика связи с заказом: `order_id` в задаче, проверка обеспеченности при закрытии

**Presentation**
- [ ] `ProductionTaskService`
- [ ] Эндпоинты задач (по ролям: производство видит только свои)
- [ ] Эндпоинт завершения с формой отчёта

**Tests**
- [ ] Unit тесты domain: расчёт сырья, state machine задачи
- [ ] Unit тесты use cases
- [ ] Integration тесты репозиториев
- [ ] Integration тесты API

---

## Phase 6 — Delivery (доставки)
> Ветка: `feature/delivery`

**Domain**
- [ ] `Delivery` entity, `DeliveryStatus` value object

**Infrastructure**
- [ ] SQLAlchemy модель: `deliveries`
- [ ] Репозиторий
- [ ] Alembic миграция

**Application**
- [ ] Use cases: `pick_up_order`, `start_delivery`, `complete_delivery`, `cancel_delivery`

**Presentation**
- [ ] `DeliveryService`
- [ ] Эндпоинты доставки (водитель видит только свои)

**Tests**
- [ ] Unit тесты domain: state machine доставки
- [ ] Unit тесты use cases
- [ ] Integration тесты репозиториев
- [ ] Integration тесты API

---

## Phase 7 — Notifications (уведомления)
> Ветка: `feature/notifications`

**Infrastructure**
- [ ] `TelegramNotificationService` — реализация `INotificationService`
- [ ] Telegram bot: обработка `/start` → сохранение `telegram_id`
- [ ] SQLAlchemy модели: `notifications`, `settings`
- [ ] Alembic миграция

**Application**
- [ ] Подключение уведомлений ко всем use cases где они нужны (по реестру SRS §4.7.3)

**Presentation**
- [ ] Эндпоинты: настройка токена бота, статус подключения
- [ ] Webhook / polling для бота

**Tests**
- [ ] Unit тесты use cases с mock `INotificationService`
- [ ] Integration тест привязки Telegram

---

## Phase 8 — Reports + Dashboard
> Ветка: `feature/reports`

**Infrastructure**
- [ ] SQLAlchemy модели: `orders_archive`, `tasks_archive`
- [ ] Alembic миграция
- [ ] Логика архивации при закрытии задачи / завершении заказа

**Application**
- [ ] Use cases: `archive_order`, `archive_task`
- [ ] Use cases отчётов: фильтрация, поиск

**Presentation**
- [ ] Эндпоинты отчётов (только директор): заказы, задачи
- [ ] Эндпоинты дашборда по ролям:
  - Директор: резервы, критические остатки, просроченные задачи, ближайшие доставки
  - Склад: активные резервы, отгрузки сегодня
  - Производство: текущая задача, задачи на сегодня
  - Доставка: доставки сегодня, все мои доставки
- [ ] Эндпоинты уведомлений: список, отметить прочитанными, очистить прочитанные

**Tests**
- [ ] Integration тесты архивации и отчётов

---

## Phase 9 — Streamlit prototype
> Ветка: `feature/streamlit`

- [ ] Авторизация (login форма)
- [ ] Страница справочников
- [ ] Страница заказов
- [ ] Страница производственных задач
- [ ] Страница склада
- [ ] Страница доставок
- [ ] Дашборд директора

---

## Phase 10 — Deploy
> Ветка: `feature/deploy`

- [ ] `Dockerfile` для backend
- [ ] `docker-compose.yml` — добавить сервис приложения
- [ ] Nginx конфиг (reverse proxy + HTTPS)
- [ ] `alembic upgrade head` при старте контейнера
- [ ] Настройка переменных окружения на сервере
- [ ] Smoke test после деплоя
