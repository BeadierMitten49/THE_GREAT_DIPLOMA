---
type: entity
title: ProductReservation
module: orders
layer: domain
tags: [entity, orders, warehouse]
---

# ProductReservation (Резерв продукции)

Связывает [[Order|заказ]] с конкретной партией [[ProductStock|готовой продукции]] на складе. Зарезервированная продукция недоступна для других заказов.

## Поля

| Поле | Тип | Описание |
|------|-----|---------|
| id | int \| None | PK |
| order_id | int | FK → `orders` |
| stock_id | int | FK → `products_stock` |
| quantity | int | Зарезервированное количество в штуках |

## Когда создаётся

1. **Вручную** — директор резервирует конкретную партию через UI заказа
2. **Автоматически** — при закрытии [[ProductionTask|задачи под заказ]] (`close_task`) продукция поступает на склад и сразу резервируется

## Когда снимается

- При отгрузке (переход заказа `Сборка → Доставка`) — списывается со склада
- При ручном снятии директором
- При удалении заказа

## Связи

- Принадлежит → [[Order]]
- Ссылается на → [[ProductStock]]

## Расположение в коде

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/orders/entities.py` | `ProductReservation` |
| Domain | `src/domain/orders/interfaces.py` | `IProductReservationRepository` |
| Infrastructure | `src/infrastructure/db/models/orders.py` | `ProductReservationModel` |
| Infrastructure | `src/infrastructure/db/repositories/orders.py` | `ProductReservationRepository` |

## DB table: `product_reservations`
