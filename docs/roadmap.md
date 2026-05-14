# Roadmap — АИС «Ярко»

Порядок разработки соответствует зависимостям между модулями.
Каждый модуль = ветка `feature/<module>` от `develop`.

---

## Phase 0 — Setup ✅
- [x] Документация проекта (CLAUDE.md, docs/)
- [x] Схема БД и ERD
- [x] Git workflow
- [x] Инициализация проекта (FastAPI, DDD структура, Alembic, логирование)

---

## Phase 1 — References (справочники)
> Ветка: `feature/references`

**Domain**
- [x] `customers` — entity, value objects
- [x] `products` — entity (units_per_box, shelf_life_days, critical_stock)
- [x] `raw_materials_catalog` — entity
- [x] `packaging_catalog` — entity
- [x] `recipes` — entity (consumption_per_unit, waste_percentage)

**Infrastructure**
- [x] SQLAlchemy модели для всех справочников
- [x] Репозитории (CRUD + деактивация)
- [x] Alembic миграция

**Application**
- [x] Use cases: создание, редактирование, деактивация записей справочников

**Presentation**
- [x] CRUD эндпоинты для каждого справочника
- [x] Pydantic схемы

**Tests**
- [x] Unit тесты domain
- [x] Integration тесты репозиториев

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
- [ ] Use cases: `CreateUser`, `DeactivateUser`, `ResetPassword`, `BindTelegram`
- [ ] `INotificationService` port (заглушка, реализация — в Phase 7)

**Presentation**
- [ ] `POST /auth/login` — выдача access + refresh токенов
- [ ] `POST /auth/refresh` — обновление access токена
- [ ] `POST /auth/logout`
- [ ] Эндпоинты управления пользователями (только директор)
- [ ] `dependencies.py` — `get_current_user`, `require_role(...)`
- [ ] Rate limiting: блокировка после 5 неудачных попыток на 30 минут

**Tests**
- [ ] Unit тесты: rate limit логика, JWT
- [ ] Integration тесты: login, refresh, блокировка

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
- [ ] Use cases сырья: `RawMaterialArrival`, `RawMaterialWriteOff`, `ReserveRawMaterial`, `ReleaseRawMaterialReservation`
- [ ] Use cases упаковки: `PackagingArrival`, `PackagingWriteOff`
- [ ] Use cases продукции: `FinishedGoodsArrival`, `ReserveFinishedGoods`, `ReleaseFinishedGoodsReservation`, `ShipFinishedGoods`

**Presentation**
- [ ] Эндпоинты склада сырья, упаковки, продукции
- [ ] Эндпоинты отгрузок (список заказов в статусе «Сборка», кнопка «Выдано»)

**Tests**
- [ ] Unit тесты: резервирование, критический остаток, batch_number reset
- [ ] Integration тесты

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
- [ ] Use cases: `CreateTask`, `StartTask`, `StopTask`, `ResumeTask`, `CompleteTask` (отчёт сотрудника), `CloseTask` (директор)
- [ ] Use case: `ReassignTask`, `DeleteTask`
- [ ] Логика связи с заказом (order_task)

**Presentation**
- [ ] Эндпоинты задач (по ролям: производство видит только свои)
- [ ] Эндпоинт завершения с формой отчёта

**Tests**
- [ ] Unit тесты: расчёт сырья, state machine задачи
- [ ] Integration тесты

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
- [ ] Use cases: `CreateOrder`, `ChangeOrderStatus`, `EditOrder`, `DeleteOrder`
- [ ] Логика резервирования продукции при переходе в «Сборка»
- [ ] Аварийное снятие резерва директором

**Presentation**
- [ ] Эндпоинты заказов
- [ ] Эндпоинт аварийного снятия резерва

**Tests**
- [ ] Unit тесты: логика начального статуса, переходы состояний
- [ ] Integration тесты: полный цикл заказа

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
- [ ] Use cases: `PickUpOrder`, `StartDelivery`, `CompleteDelivery`, `CancelDelivery`

**Presentation**
- [ ] Эндпоинты доставки (водитель видит только свои)

**Tests**
- [ ] Unit тесты: state machine доставки
- [ ] Integration тесты

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
- [ ] Unit тесты с mock INotificationService
- [ ] Integration тест привязки Telegram

---

## Phase 8 — Reports + Dashboard
> Ветка: `feature/reports`

**Infrastructure**
- [ ] SQLAlchemy модели: `orders_archive`, `tasks_archive`
- [ ] Alembic миграция
- [ ] Логика архивации при закрытии задачи / завершении заказа

**Application**
- [ ] Use case: `ArchiveOrder`, `ArchiveTask`
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
