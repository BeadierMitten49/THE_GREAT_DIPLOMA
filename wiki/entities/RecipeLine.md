---
type: entity
title: RecipeLine
module: references
layer: domain
tags: [entity, references]
---

# RecipeLine (Строка рецептуры)

Сущность, входящая в агрегат [[Product]]. Описывает норму расхода одного вида сырья на единицу готовой продукции.

## Поля

| Поле | Тип | Описание |
|------|-----|---------|
| id | int \| None | PK, присваивается БД после сохранения |
| raw_material_id | int | FK → `raw_materials_catalog` |
| consumption_per_unit | Decimal | Норма расхода сырья на 1 штуку продукта |
| waste_percentage | Decimal | Процент брака (0..100) |

## Инварианты

- `consumption_per_unit > 0`
- `0 <= waste_percentage <= 100`

## Жизненный цикл

Управляется исключительно через `Product.set_recipe()`. Не создаётся и не удаляется напрямую из use cases.

При сохранении агрегата `ProductRepository._sync_recipe()`:
- Строки с `id=None` → INSERT
- Строки с `id` → UPDATE (`consumption_per_unit`, `waste_percentage`)
- Строки удалённые из списка → DELETE

## Связи

- Принадлежит → [[Product]]
- Ссылается на → [[RawMaterialCatalog]]

## Расположение в коде

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/references/entities.py` | `RecipeLine` |
| Infrastructure | `src/infrastructure/db/models/references.py` | `RecipeLineModel` |
| Infrastructure | `src/infrastructure/db/repositories/references.py` | `ProductRepository._sync_recipe()` |
| Application | `src/application/references/dto.py` | `RecipeLineDTO` |
| Presentation | `src/presentation/api/v1/references/schemas.py` | `RecipeLineRequest`, `RecipeLineResponse` |

## DB table: `recipes`
