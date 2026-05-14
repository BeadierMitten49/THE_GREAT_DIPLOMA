---
type: entity
title: PackagingCatalog
module: references
layer: domain
tags: [entity, references, aggregate-root]
---

# PackagingCatalog (Справочник упаковки)

Агрегат-рут модуля справочников. Описывает вид упаковочного материала.

## Поля

| Поле | Тип | Описание |
|------|-----|---------|
| id | int \| None | PK, присваивается БД после сохранения |
| name | str | Наименование упаковки |
| unit | str | Единица измерения |
| critical_stock | int | Пороговый остаток в единицах измерения |
| is_active | bool | Признак активности (soft delete) |

## Поведение

- `update(name, unit, critical_stock)` — обновляет поля с валидацией
- `deactivate()` / `activate()` — управление активностью

## Инварианты

- `name` и `unit` не могут быть пустыми
- `critical_stock >= 0`

## Связи

- Используется в → `packaging_stock`

## Расположение в коде

- Domain: `src/domain/references/entities.py`
- Repository interface: `src/domain/references/interfaces.py` → `IPackagingCatalogRepository`
- SQLAlchemy model: `src/infrastructure/db/models/references.py` → `PackagingCatalogModel`
- Repository impl: `src/infrastructure/db/repositories/references.py` → `PackagingCatalogRepository`
- DB table: `packaging_catalog`
