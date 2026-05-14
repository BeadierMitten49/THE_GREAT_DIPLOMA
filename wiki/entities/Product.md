---
type: entity
title: Product
module: references
layer: domain
tags: [entity, references, aggregate-root]
---

# Product (Готовая продукция)

Агрегат-рут модуля справочников. Описывает единицу готовой продукции, которую предприятие производит и отгружает. Владеет списком строк рецептуры [[RecipeLine]].

## Поля

| Поле | Тип | Описание |
|------|-----|---------|
| id | int \| None | PK, присваивается БД после сохранения |
| name | str | Наименование продукта |
| units_per_box | int | Штук в коробке (для пересчёта на фронте) |
| shelf_life_days | int | Срок годности в днях |
| critical_stock | int | Пороговый остаток в штуках (для предупреждений) |
| is_active | bool | Признак активности (soft delete) |
| recipe | list[RecipeLine] | Строки рецептуры — нормы расхода сырья |

## Поведение

- `update(name, units_per_box, shelf_life_days, critical_stock)` — обновляет поля с валидацией
- `set_recipe(lines)` — атомарно заменяет рецептуру, валидирует все строки перед применением
- `deactivate()` / `activate()` — управление активностью

## Инварианты

- `units_per_box > 0`, `shelf_life_days > 0`
- `critical_stock >= 0`
- В каждой строке рецептуры: `consumption_per_unit > 0`, `0 <= waste_percentage <= 100`

## Связи

- Владеет → [[RecipeLine]] (cascade delete)
- Используется в → `production_tasks`, `order_items`, `products_stock`

## Расположение в коде

- Domain: `src/domain/references/entities.py`
- Repository interface: `src/domain/references/interfaces.py` → `IProductRepository`
- SQLAlchemy model: `src/infrastructure/db/models/references.py` → `ProductModel`
- Repository impl: `src/infrastructure/db/repositories/references.py` → `ProductRepository`
- DB table: `products`
