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

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/references/entities.py` | `Product` |
| Domain | `src/domain/references/interfaces.py` | `IProductRepository` |
| Infrastructure | `src/infrastructure/db/models/references.py` | `ProductModel` |
| Infrastructure | `src/infrastructure/db/repositories/references.py` | `ProductRepository` |
| Application | `src/application/references/use_cases.py` | `get_product`, `get_products`, `create_product`, `update_product`, `set_product_recipe`, `deactivate_product`, `activate_product` |
| Application | `src/application/references/dto.py` | `CreateProductDTO`, `UpdateProductDTO`, `RecipeLineDTO` |
| Presentation | `src/presentation/api/v1/references/service.py` | `ProductService` |
| Presentation | `src/presentation/api/v1/references/products.py` | router |
| Presentation | `src/presentation/api/v1/references/schemas.py` | `CreateProductRequest`, `UpdateProductRequest`, `ProductResponse`, `RecipeLineRequest`, `RecipeLineResponse`, `SetRecipeRequest` |

## API-эндпоинты

| Метод | Путь | Описание |
|-------|------|---------|
| GET | `/api/v1/references/products` | Список |
| GET | `/api/v1/references/products/{id}` | Получить по ID (включает рецептуру) |
| POST | `/api/v1/references/products` | Создать (201) |
| PATCH | `/api/v1/references/products/{id}` | Обновить (200) |
| PUT | `/api/v1/references/products/{id}/recipe` | Заменить рецептуру целиком (204) |
| POST | `/api/v1/references/products/{id}/deactivate` | Деактивировать (204) |
| POST | `/api/v1/references/products/{id}/activate` | Активировать (204) |

## DB table: `products`
