---
type: entity
title: PackagingStock
module: warehouse
layer: domain
tags: [entity, warehouse]
---

# PackagingStock (Запас упаковки на складе)

Сущность модуля склада. Представляет запас одного вида упаковочного материала.

## Поля

| Поле | Тип | Описание |
|------|-----|---------|
| id | int \| None | PK |
| packaging_id | int | FK → `packaging_catalog` |
| quantity | int | Текущее количество (в единицах измерения) |
| comment | str \| None | Комментарий |

## Поведение

- `write_off(amount)` — списание: `amount > 0`, не может превышать `quantity`

## Особенности

- Упаковка **не связана** с отчётами производственных задач — списание только ручное
- Нет дат поступления и годности (в отличие от сырья)
- Нет резервирования

## Связи

- Ссылается на → [[PackagingCatalog]]

## Расположение в коде

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/warehouse/entities.py` | `PackagingStock` |
| Domain | `src/domain/warehouse/interfaces.py` | `IPackagingStockRepository` |
| Infrastructure | `src/infrastructure/db/models/warehouse.py` | `PackagingStockModel` |
| Infrastructure | `src/infrastructure/db/repositories/warehouse.py` | `PackagingStockRepository` |

## API-эндпоинты

| Метод | Путь | Описание |
|-------|------|---------|
| GET | `/api/v1/packaging-stock` | Список запасов упаковки |
| GET | `/api/v1/packaging-stock/{id}` | Получить запись |
| POST | `/api/v1/packaging-stock` | Приход упаковки (201) |
| POST | `/api/v1/packaging-stock/{id}/write-off` | Списание (204) |

## DB table: `packaging_stock`
