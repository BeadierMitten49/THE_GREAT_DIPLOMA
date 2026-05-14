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
- [ ] `User` entity, `Role` value object
- [ ] `IUserRepository` интерфейс

**Infrastructure**
- [ ] SQLAlchemy модели: `users`, `user_roles`, `auth_log`, `refresh_tokens`
- [ ] Репозитории
- [ ] Alembic миграция

**Application**
- [ ] Use cases: `create_user`, `deactivate_user`, `reset_password`, `bind_telegram`
- [ ] Use cases auth: `login`, `refresh_token`, `logout`
- [ ] `INotificationService` port (заглушка, реализация — в Phase 7)
- [ ] Rate limit логика: блокировка после 5 неудачных попыток на 30 минут

**Presentation**
- [ ] `AuthService`, `UserService`
- [ ] `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`
- [ ] Эндпоинты управления пользователями (только директор)
- [ ] `dependencies.py` — `get_current_user`, `require_role(...)`

**Tests**
- [ ] Unit тесты domain
- [ ] Unit тесты use cases
- [ ] Integration тесты репозиториев
- [ ] Integration тесты API: login, refresh, блокировка

---

## Phase 3 — Warehouse (склад)
> Ветка: `feature/warehouse`

**Domain**
- [ ] `RawMaterialStock` entity
- [ ] `PackagingStock` entity
- [ ] `ProductsStock` entity (batch_number, batch_year)
- [ ] `StockReservation` value object
- [ ] Domain service: проверка критического остатка

**Infrastructure**
- [ ] SQLAlchemy модели: `raw_material_stock`, `packaging_stock`, `products_stock`, `raw_material_reservations`, `products_reservations`
- [ ] Репозитории
- [ ] Alembic миграция

**Application**
- [ ] Use cases сырья: `raw_material_arrival`, `raw_material_write_off`, `reserve_raw_material`, `release_raw_material_reservation`
- [ ] Use cases упаковки: `packaging_arrival`, `packaging_write_off`
- [ ] Use cases продукции: `finished_goods_arrival`, `reserve_finished_goods`, `release_finished_goods_reservation`, `ship_finished_goods`

**Presentation**
- [ ] Service-классы по агрегатам
- [ ] Эндпоинты склада сырья, упаковки, продукции
- [ ] Эндпоинты отгрузок (список заказов в статусе «Сборка», кнопка «Выдано»)

**Tests**
- [ ] Unit тесты domain: резервирование, критический остаток, batch_number reset
- [ ] Unit тесты use cases
- [ ] Integration тесты репозиториев
- [ ] Integration тесты API

---

## Phase 4 — Production (производственные задачи)
> Ветка: `feature/production`

**Domain**
- [ ] `ProductionTask` entity, `TaskStatus` value object
- [ ] `TaskStop` entity
- [ ] `TaskCompletion` entity
- [ ] Domain service: расчёт потребности в сырье по рецептуре (с % брака)

**Infrastructure**
- [ ] SQLAlchemy модели: `production_tasks`, `task_stops`, `task_completions`, `task_completion_consumption`
- [ ] Репозитории
- [ ] Alembic миграция

**Application**
- [ ] Use cases: `create_task`, `start_task`, `stop_task`, `resume_task`, `complete_task`, `close_task`
- [ ] Use cases: `reassign_task`, `delete_task`
- [ ] Логика связи с заказом (order_task)

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

## Phase 5 — Orders (заказы)
> Ветка: `feature/orders`

**Domain**
- [ ] `Order` entity, `OrderItem` value object, `OrderStatus` value object
- [ ] Domain service: проверка остатков при создании заказа, логика начального статуса

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
