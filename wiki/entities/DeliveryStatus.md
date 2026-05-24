---
type: value-object
title: DeliveryStatus
module: delivery
layer: domain
tags: [value-object, delivery]
---

# DeliveryStatus (Статус доставки)

Value object модуля доставки. `StrEnum` — сериализуется в строку.

## Значения

| Значение | Описание | UI-метка |
|----------|---------|----------|
| `pending` | Ожидает, заказ ещё не забран | Ожидает |
| `picked_up` | Водитель забрал заказ | Забран |
| `in_transit` | В пути, начат выезд | В пути |
| `completed` | Доставлено | Доставлено |
| `cancelled` | Отменена (с причиной) | Отменена |

## Диаграмма переходов

```
pending → picked_up → in_transit → completed
                                 → cancelled (из любого статуса кроме completed)
```

## Расположение в коде

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/delivery/value_objects.py` | `DeliveryStatus(StrEnum)` |
