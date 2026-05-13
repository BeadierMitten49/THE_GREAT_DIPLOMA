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
│   │   ├── orders/
│   │   │   ├── entities.py            ← Order, OrderItem
│   │   │   ├── value_objects.py       ← OrderStatus
│   │   │   ├── services.py            ← доменные сервисы (проверка остатков при создании)
│   │   │   └── repository.py          ← интерфейс IOrderRepository
│   │   │
│   │   ├── production/
│   │   │   ├── entities.py            ← ProductionTask, TaskReport
│   │   │   ├── value_objects.py       ← TaskStatus, RawMaterialConsumption
│   │   │   ├── services.py            ← расчёт потребности в сырье по рецептуре
│   │   │   └── repository.py
│   │   │
│   │   ├── warehouse/
│   │   │   ├── entities.py            ← RawMaterial, Packaging, FinishedGoods, Batch
│   │   │   ├── value_objects.py       ← StockReservation, BatchNumber
│   │   │   ├── services.py            ← проверка критического остатка
│   │   │   └── repository.py
│   │   │
│   │   ├── delivery/
│   │   │   ├── entities.py            ← Delivery
│   │   │   ├── value_objects.py       ← DeliveryStatus
│   │   │   └── repository.py
│   │   │
│   │   ├── users/
│   │   │   ├── entities.py            ← User, Role
│   │   │   ├── value_objects.py       ← TelegramBinding
│   │   │   └── repository.py
│   │   │
│   │   └── shared/                    ← Общие примитивы домена
│   │       ├── value_objects.py       ← Money, Quantity, DateRange
│   │       └── events.py              ← доменные события (TaskCompleted и т.д.)
│   │
│   ├── application/                   ← Use cases. Оркестрирует домен. Не знает о HTTP/БД.
│   │   │
│   │   ├── orders/
│   │   │   ├── use_cases.py           ← CreateOrder, ChangeOrderStatus, DeleteOrder
│   │   │   └── dto.py
│   │   │
│   │   ├── production/
│   │   │   ├── use_cases.py           ← CreateTask, StartTask, StopTask, CompleteTask, CloseTask
│   │   │   └── dto.py
│   │   │
│   │   ├── warehouse/
│   │   │   ├── use_cases.py           ← StockArrival, WriteOff, Reserve, Release, Ship
│   │   │   └── dto.py
│   │   │
│   │   ├── delivery/
│   │   │   ├── use_cases.py           ← StartDelivery, CompleteDelivery, CancelDelivery
│   │   │   └── dto.py
│   │   │
│   │   ├── users/
│   │   │   ├── use_cases.py           ← CreateUser, DeactivateUser, ResetPassword, BindTelegram
│   │   │   └── dto.py
│   │   │
│   │   └── ports/                     ← Интерфейсы для внешних сервисов
│   │       └── notification_port.py   ← INotificationService (реализация — в infrastructure)
│   │
│   ├── infrastructure/                ← Реализации интерфейсов. Зависит на фреймворки и БД.
│   │   │
│   │   ├── db/
│   │   │   ├── models/                ← SQLAlchemy-модели (ORM)
│   │   │   │   ├── order.py
│   │   │   │   ├── production.py
│   │   │   │   ├── warehouse.py
│   │   │   │   ├── delivery.py
│   │   │   │   ├── user.py
│   │   │   │   └── auth_log.py        ← лог попыток входа (SRS §4.1.1)
│   │   │   ├── repositories/          ← реализации IXxxRepository
│   │   │   │   ├── order_repo.py
│   │   │   │   ├── production_repo.py
│   │   │   │   ├── warehouse_repo.py
│   │   │   │   ├── delivery_repo.py
│   │   │   │   └── user_repo.py
│   │   │   ├── migrations/            ← Alembic
│   │   │   └── session.py
│   │   │
│   │   ├── telegram/
│   │   │   ├── bot.py                 ← инициализация, обработка /start → привязка Telegram ID
│   │   │   └── notification_service.py← реализация INotificationService
│   │   │
│   │   └── config.py                  ← env-переменные (pydantic BaseSettings)
│   │
│   └── presentation/                  ← Точки входа. Зависит только на application/.
│       │
│       ├── api/                       ← FastAPI
│       │   ├── v1/
│       │   │   ├── auth.py
│       │   │   ├── orders.py
│       │   │   ├── production.py
│       │   │   ├── warehouse.py
│       │   │   ├── delivery.py
│       │   │   └── settings.py
│       │   ├── schemas/               ← Pydantic request/response схемы
│       │   └── dependencies.py        ← get_current_user, require_role(...)
│       │
│       └── streamlit/                 ← Прототип UI для демонстрации
│           ├── app.py
│           └── pages/
│
├── tests/
│   ├── unit/                          ← тесты домена (без БД)
│   └── integration/                   ← тесты с реальной БД
│
├── logs/                              ← gitignored
├── docs/
│   └── project-structure.md
├── wiki/
│   └── entities/                      ← в git; остальное gitignored
│
├── main.py                            ← точка входа FastAPI
├── .env.example
├── .gitignore
└── docker-compose.yml
```

## Правила зависимостей (DDD)

```
presentation → application → domain
infrastructure → domain (реализует интерфейсы)
```

`domain/` не импортирует ничего кроме `shared/`. `application/` не знает о SQLAlchemy и FastAPI. `presentation/` не лезет в репозитории напрямую — только через use cases.

## Ключевые решения

**`ports/notification_port.py`** — application-слой знает только об интерфейсе `INotificationService`. Telegram — деталь инфраструктуры. Завтра можно заменить на email без касания бизнес-логики.

**`domain/shared/events.py`** — доменные события (`TaskCompleted`, `StockCritical`, `OrderShipped`) — через них уведомления запускаются без прямых вызовов из домена в инфраструктуру.

**`auth_log`** — таблица в БД, не файл. Нужна для отчётности и фильтрации через интерфейс.

**`streamlit/`** — только для прототипирования и показа. Не production UI.
