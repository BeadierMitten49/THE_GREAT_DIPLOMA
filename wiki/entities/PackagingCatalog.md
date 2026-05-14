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

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/references/entities.py` | `PackagingCatalog` |
| Domain | `src/domain/references/interfaces.py` | `IPackagingCatalogRepository` |
| Infrastructure | `src/infrastructure/db/models/references.py` | `PackagingCatalogModel` |
| Infrastructure | `src/infrastructure/db/repositories/references.py` | `PackagingCatalogRepository` |
| Application | `src/application/references/use_cases.py` | `get_packaging`, `get_packagings`, `create_packaging`, `update_packaging`, `deactivate_packaging`, `activate_packaging` |
| Application | `src/application/references/dto.py` | `CreatePackagingDTO`, `UpdatePackagingDTO` |
| Presentation | `src/presentation/api/v1/references/service.py` | `PackagingService` |
| Presentation | `src/presentation/api/v1/references/packaging.py` | router |
| Presentation | `src/presentation/api/v1/references/schemas.py` | `CreatePackagingRequest`, `UpdatePackagingRequest`, `PackagingResponse` |

## API-эндпоинты

| Метод | Путь | Описание |
|-------|------|---------|
| GET | `/api/v1/references/packaging` | Список |
| GET | `/api/v1/references/packaging/{id}` | Получить по ID |
| POST | `/api/v1/references/packaging` | Создать (201) |
| PATCH | `/api/v1/references/packaging/{id}` | Обновить (200) |
| POST | `/api/v1/references/packaging/{id}/deactivate` | Деактивировать (204) |
| POST | `/api/v1/references/packaging/{id}/activate` | Активировать (204) |

## DB table: `packaging_catalog`
