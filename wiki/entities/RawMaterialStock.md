---
type: entity
title: RawMaterialStock
module: warehouse
layer: domain
tags: [entity, warehouse]
---

# RawMaterialStock (Партия сырья на складе)

Сущность модуля склада. Представляет одну партию сырья с количеством, датами поступления и годности.

## Поля

| Поле | Тип | Описание |
|------|-----|---------|
| id | int \| None | PK |
| raw_material_id | int | FK → `raw_materials_catalog` |
| quantity | Decimal | Текущее количество (в единицах измерения из справочника, обычно кг) |
| arrival_date | date | Дата поступления |
| expiry_date | date | Срок годности |
| comment | str \| None | Комментарий |

## Поведение

- `write_off(amount)` — списание: `amount > 0`, не может превышать `quantity`
- `adjust(new_quantity, comment)` — корректировка: `new_quantity >= 0`

## Резервирование

Сырьё резервируется через [[RawMaterialReservation]]. Доступное количество = `quantity - сумма резервов`. При создании [[ProductionTask|задачи]] резервирование идёт FIFO по сроку годности.

## Списание при закрытии задачи

При закрытии задачи (`close_task`) фактический расход из отчёта [[TaskCompletion]] списывается с партий FIFO по сроку годности.

## Связи

- Ссылается на → [[RawMaterialCatalog]]
- Резервируется через → [[RawMaterialReservation]]

## Расположение в коде

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/warehouse/entities.py` | `RawMaterialStock` |
| Domain | `src/domain/warehouse/interfaces.py` | `IRawMaterialStockRepository` |
| Infrastructure | `src/infrastructure/db/models/warehouse.py` | `RawMaterialStockModel` |
| Infrastructure | `src/infrastructure/db/repositories/warehouse.py` | `RawMaterialStockRepository` |

## API-эндпоинты

| Метод | Путь | Описание |
|-------|------|---------|
| GET | `/api/v1/raw-material-stock` | Список партий сырья |
| GET | `/api/v1/raw-material-stock/{id}` | Получить партию |
| POST | `/api/v1/raw-material-stock` | Приход сырья (201) |
| POST | `/api/v1/raw-material-stock/{id}/write-off` | Списание (204) |
| PATCH | `/api/v1/raw-material-stock/{id}` | Корректировка (204) |

## DB table: `raw_material_stock`
