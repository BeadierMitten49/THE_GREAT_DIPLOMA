---
type: entity
title: RawMaterialCatalog
module: references
layer: domain
tags: [entity, references, aggregate-root]
---

# RawMaterialCatalog (Справочник сырья)

Агрегат-рут модуля справочников. Описывает вид сырья, используемого в производстве.

## Поля

| Поле | Тип | Описание |
|------|-----|---------|
| id | int \| None | PK, присваивается БД после сохранения |
| name | str | Наименование сырья |
| unit | str | Единица измерения (кг, л и т.д.) |
| shelf_life_days | int | Срок годности в днях |
| critical_stock | Decimal | Пороговый остаток в единицах измерения |
| is_active | bool | Признак активности (soft delete) |

## Поведение

- `update(name, unit, shelf_life_days, critical_stock)` — обновляет поля с валидацией
- `deactivate()` / `activate()` — управление активностью

## Инварианты

- `name` и `unit` не могут быть пустыми
- `shelf_life_days > 0`
- `critical_stock >= 0`

## Связи

- Используется в → [[RecipeLine]], `raw_material_stock`, `raw_material_reservations`

## Расположение в коде

- Domain: `src/domain/references/entities.py`
- Repository interface: `src/domain/references/interfaces.py` → `IRawMaterialCatalogRepository`
- SQLAlchemy model: `src/infrastructure/db/models/references.py` → `RawMaterialCatalogModel`
- Repository impl: `src/infrastructure/db/repositories/references.py` → `RawMaterialCatalogRepository`
- DB table: `raw_materials_catalog`
