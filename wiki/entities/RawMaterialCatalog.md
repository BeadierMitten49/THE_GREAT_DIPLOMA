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

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/references/entities.py` | `RawMaterialCatalog` |
| Domain | `src/domain/references/interfaces.py` | `IRawMaterialCatalogRepository` |
| Infrastructure | `src/infrastructure/db/models/references.py` | `RawMaterialCatalogModel` |
| Infrastructure | `src/infrastructure/db/repositories/references.py` | `RawMaterialCatalogRepository` |
| Application | `src/application/references/use_cases.py` | `get_raw_material`, `get_raw_materials`, `create_raw_material`, `update_raw_material`, `deactivate_raw_material`, `activate_raw_material` |
| Application | `src/application/references/dto.py` | `CreateRawMaterialDTO`, `UpdateRawMaterialDTO` |
| Presentation | `src/presentation/api/v1/references/service.py` | `RawMaterialService` |
| Presentation | `src/presentation/api/v1/references/raw_materials.py` | router |
| Presentation | `src/presentation/api/v1/references/schemas.py` | `CreateRawMaterialRequest`, `UpdateRawMaterialRequest`, `RawMaterialResponse` |

## API-эндпоинты

| Метод | Путь | Описание |
|-------|------|---------|
| GET | `/api/v1/references/raw-materials` | Список |
| GET | `/api/v1/references/raw-materials/{id}` | Получить по ID |
| POST | `/api/v1/references/raw-materials` | Создать (201) |
| PATCH | `/api/v1/references/raw-materials/{id}` | Обновить (200) |
| POST | `/api/v1/references/raw-materials/{id}/deactivate` | Деактивировать (204) |
| POST | `/api/v1/references/raw-materials/{id}/activate` | Активировать (204) |

## DB table: `raw_materials_catalog`
