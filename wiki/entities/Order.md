---
type: entity
title: Order
module: orders
layer: domain
tags: [entity, orders, aggregate-root]
---

# Order (Заказ)

Агрегат-рут модуля заказов. Представляет заказ клиента на продукцию — от создания до доставки.

## Поля

| Поле | Тип | Описание |
|------|-----|---------|
| id | int \| None | PK |
| number | str | Уникальный номер заказа, генерируется системой |
| customer_id | int | FK → `customers` |
| delivery_address | str | Адрес доставки (копируется из справочника, редактируется) |
| delivery_date | date | Плановая дата доставки |
| status | [[OrderStatus]] | Текущий статус заказа |
| delivery_user_id | int \| None | FK → `users`, исполнитель доставки |
| comment | str \| None | Комментарий |
| is_active | bool | Признак активности (soft delete) |
| created_at | datetime \| None | Дата создания |

## Поведение

- `set_status(new_status)` — переход статуса с валидацией допустимых переходов
- `delete()` — soft delete (is_active = False)

## Допустимые переходы статусов

```
Создан → Производство
Создан → Сборка
Производство → Сборка
Сборка → Доставка
Доставка → Завершён
```

## Инварианты

- Переход `Производство → Сборка` возможен только когда все связанные [[ProductionTask|задачи]] закрыты
- Переход `Сборка → Доставка` возможен только когда резервы покрывают все позиции и создана [[Delivery|доставка]]
- Редактирование невозможно в статусах `delivery` и `completed`

## Связи

- Владеет → [[OrderItem]] (cascade)
- Владеет → [[ProductReservation]] (резервы продукции)
- Ссылается на → [[Customer]], [[User]]
- Связан с → [[ProductionTask]] (через `order_id`), [[Delivery]]

## Расположение в коде

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/orders/entities.py` | `Order` |
| Domain | `src/domain/orders/interfaces.py` | `IOrderRepository` |
| Domain | `src/domain/orders/value_objects.py` | `OrderStatus` |
| Infrastructure | `src/infrastructure/db/models/orders.py` | `OrderModel` |
| Infrastructure | `src/infrastructure/db/repositories/orders.py` | `OrderRepository` |
| Application | `src/application/orders/use_cases.py` | `get_order`, `get_orders`, `create_order`, `edit_order`, `change_order_status`, `delete_order` |
| Application | `src/application/orders/dto.py` | `CreateOrderDTO`, `EditOrderDTO`, `ChangeOrderStatusDTO` |
| Presentation | `src/presentation/api/v1/orders/service.py` | `OrderService` |
| Presentation | `src/presentation/api/v1/orders/router.py` | router |

## API-эндпоинты

| Метод | Путь | Описание |
|-------|------|---------|
| GET | `/api/v1/orders` | Список заказов (фильтры: status, customer_id, delivery_date) |
| GET | `/api/v1/orders/{id}` | Получить заказ |
| GET | `/api/v1/orders/{id}/items` | Позиции заказа |
| GET | `/api/v1/orders/{id}/drawer` | Обогащённые данные для drawer |
| GET | `/api/v1/orders/{id}/reservations` | Резервы продукции |
| POST | `/api/v1/orders` | Создать заказ (201) |
| POST | `/api/v1/orders/{id}/reservations` | Зарезервировать продукцию (201) |
| PATCH | `/api/v1/orders/{id}/status` | Сменить статус (204) |
| PUT | `/api/v1/orders/{id}` | Редактировать заказ (204) |
| DELETE | `/api/v1/orders/{id}` | Удалить (soft delete, 204) |
| DELETE | `/api/v1/orders/{id}/reservations` | Снять все резервы (204) |
| DELETE | `/api/v1/orders/reservation/{reservation_id}` | Снять резерв (204) |

## DB table: `orders`
