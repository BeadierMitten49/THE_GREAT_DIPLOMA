---
type: entity
title: OrderItem
module: orders
layer: domain
tags: [entity, orders]
---

# OrderItem (Позиция заказа)

Сущность, входящая в агрегат [[Order]]. Описывает одну строку заказа — продукт и количество.

## Поля

| Поле | Тип | Описание |
|------|-----|---------|
| id | int \| None | PK |
| order_id | int | FK → `orders` |
| product_id | int | FK → `products` |
| quantity | int | Количество в штуках |

## Жизненный цикл

Создаётся и удаляется только через use case `create_order` / `edit_order`. При редактировании заказа позиции пересоздаются атомарно (удаление старых + вставка новых).

## Связи

- Принадлежит → [[Order]]
- Ссылается на → [[Product]]

## Расположение в коде

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/orders/entities.py` | `OrderItem` |
| Domain | `src/domain/orders/interfaces.py` | `IOrderItemRepository` |
| Infrastructure | `src/infrastructure/db/models/orders.py` | `OrderItemModel` |
| Infrastructure | `src/infrastructure/db/repositories/orders.py` | `OrderItemRepository` |

## DB table: `order_items`
