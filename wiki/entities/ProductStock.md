---
type: entity
title: ProductStock
module: warehouse
layer: domain
tags: [entity, warehouse]
---

# ProductStock (Партия готовой продукции на складе)

Сущность модуля склада. Представляет одну партию готовой продукции с номером партии, количеством и сроками.

## Поля

| Поле | Тип | Описание |
|------|-----|---------|
| id | int \| None | PK |
| product_id | int | FK → `products` |
| quantity | int | Количество в штуках |
| batch_number | int | Номер партии в рамках года |
| batch_year | int | Год партии |
| arrival_date | date | Дата поступления |
| expiry_date | date | Срок годности |
| comment | str \| None | Комментарий |

## Поведение

- `write_off(amount)` — списание: `amount > 0`, не может превышать `quantity`
- `adjust(new_quantity, comment)` — корректировка: `new_quantity >= 0`

## Нумерация партий

Номер партии = `n+1` от последней партии в текущем году. Сбрасывается 1 января каждого года. Уникальная пара `(product_id, batch_number, batch_year)`.

Метка партии в UI: `П-{batch_year}-{id:03d}` (например, П-2026-001).

## Когда создаётся

При закрытии [[ProductionTask|производственной задачи]] (`close_task`) — для **любого** типа задачи (`stock_task` и `order_task`).

## Резервирование

Продукция резервируется через [[ProductReservation]] для конкретного [[Order|заказа]]. Зарезервированная продукция отображается отдельно и недоступна для других заказов.

## Связи

- Ссылается на → [[Product]]
- Резервируется через → [[ProductReservation]]

## Расположение в коде

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/warehouse/entities.py` | `ProductStock` |
| Domain | `src/domain/warehouse/interfaces.py` | `IProductStockRepository` |
| Infrastructure | `src/infrastructure/db/models/warehouse.py` | `ProductStockModel` |
| Infrastructure | `src/infrastructure/db/repositories/warehouse.py` | `ProductStockRepository` |

## API-эндпоинты

| Метод | Путь | Описание |
|-------|------|---------|
| GET | `/api/v1/product-stock` | Список партий продукции |
| GET | `/api/v1/product-stock/pending-tasks` | Задачи ожидающие приёмки |
| GET | `/api/v1/product-stock/{id}` | Получить партию |
| POST | `/api/v1/product-stock/from-task` | Принять продукцию из задачи (201) |
| POST | `/api/v1/product-stock` | Ручной приход (201) |
| PATCH | `/api/v1/product-stock/{id}` | Корректировка (204) |
| POST | `/api/v1/product-stock/{id}/write-off` | Списание (204, только директор) |

## DB table: `products_stock`
