---
type: entity
title: TaskCompletionConsumption
module: tasks
layer: domain
tags: [entity, tasks]
---

# TaskCompletionConsumption (Расход сырья в отчёте)

Строка отчёта [[TaskCompletion]]. Фиксирует плановый и фактический расход одного вида сырья по задаче.

## Поля

| Поле | Тип | Описание |
|------|-----|---------|
| id | int \| None | PK |
| completion_id | int | FK → `task_completions` |
| raw_material_id | int | FK → `raw_materials_catalog` |
| planned_qty | Decimal | Плановый расход (рассчитан по рецептуре) |
| actual_qty | Decimal | Фактический расход (заполняет исполнитель) |
| waste_qty | Decimal \| None | Брак в кг |

## Связи

- Принадлежит → [[TaskCompletion]]
- Ссылается на → [[RawMaterialCatalog]]

## Расположение в коде

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/tasks/entities.py` | `TaskCompletionConsumption` |
| Infrastructure | `src/infrastructure/db/models/tasks.py` | `TaskCompletionConsumptionModel` |

## DB table: `task_completion_consumptions`
