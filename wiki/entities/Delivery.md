---
type: entity
title: Delivery
module: delivery
layer: domain
tags: [entity, delivery, aggregate-root]
---

# Delivery (Доставка)

Агрегат-рут модуля доставки. Представляет задачу на доставку конкретного [[Order|заказа]] исполнителем.

## Поля

| Поле | Тип | Описание |
|------|-----|---------|
| id | int \| None | PK |
| order_id | int | FK → `orders`, уникальный (один заказ — одна активная доставка) |
| executor_id | int | FK → `users`, исполнитель (роль «Доставка» или директор) |
| status | [[DeliveryStatus]] | Текущий статус |
| planned_date | date | Плановая дата доставки |
| started_at | datetime \| None | Время начала выезда |
| completed_at | datetime \| None | Время завершения доставки |
| cancellation_reason | str \| None | Причина отмены (обязательна при отмене) |

## Поведение

- `pick_up()` — переход `pending → picked_up`, водитель забрал заказ
- `start()` — переход `picked_up → in_transit`, фиксирует `started_at`
- `complete()` — переход `in_transit → completed`, фиксирует `completed_at`
- `cancel(reason)` — переход в `cancelled` из любого статуса кроме `completed`, фиксирует `cancellation_reason`

## Статусы

```
pending → picked_up → in_transit → completed
                                 → cancelled (из любого, кроме completed)
```

## Связи

- Ссылается на → [[Order]], [[User]]

## Расположение в коде

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/delivery/entities.py` | `Delivery` |
| Domain | `src/domain/delivery/interfaces.py` | `IDeliveryRepository` |
| Domain | `src/domain/delivery/value_objects.py` | `DeliveryStatus` |
| Infrastructure | `src/infrastructure/db/models/delivery.py` | `DeliveryModel` |
| Infrastructure | `src/infrastructure/db/repositories/delivery.py` | `DeliveryRepository` |
| Application | `src/application/delivery/use_cases.py` | `create_delivery`, `pick_up_order`, `start_delivery`, `complete_delivery`, `cancel_delivery` |
| Application | `src/application/delivery/dto.py` | `CreateDeliveryDTO` |
| Presentation | `src/presentation/api/v1/delivery/service.py` | `DeliveryService` |
| Presentation | `src/presentation/api/v1/delivery/router.py` | router |

## API-эндпоинты

| Метод | Путь | Описание |
|-------|------|---------|
| GET | `/api/v1/deliveries` | Список доставок (фильтры: executor_id, status) |
| GET | `/api/v1/deliveries/{id}` | Получить доставку |
| POST | `/api/v1/deliveries` | Создать доставку (201) |
| POST | `/api/v1/deliveries/{id}/pick-up` | Забрал заказ (204) |
| POST | `/api/v1/deliveries/{id}/start` | Начать выезд (204) |
| POST | `/api/v1/deliveries/{id}/complete` | Доставлено (204) |
| POST | `/api/v1/deliveries/{id}/cancel` | Отмена доставки (204) |

## DB table: `deliveries`
