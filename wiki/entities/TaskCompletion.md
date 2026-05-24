---
type: entity
title: TaskCompletion
module: tasks
layer: domain
tags: [entity, tasks]
---

# TaskCompletion (Отчёт о выполнении задачи)

Сущность модуля задач. Фиксирует результат выполнения [[ProductionTask|производственной задачи]] — фактическое количество продукции и расход сырья.

## Поля

| Поле | Тип | Описание |
|------|-----|---------|
| id | int \| None | PK |
| task_id | int | FK → `production_tasks`, уникальный (одна задача — один отчёт) |
| actual_quantity | int | Фактическое количество произведённой продукции |
| comment | str \| None | Комментарий исполнителя |
| created_at | datetime \| None | Дата создания отчёта |

## Связи

- Принадлежит → [[ProductionTask]]
- Владеет → [[TaskCompletionConsumption]] (расход по каждому виду сырья)

## Жизненный цикл

Создаётся при завершении задачи (`complete_task`). Используется при закрытии (`close_task`) для определения фактического количества продукции и списания сырья.

## Расположение в коде

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/tasks/entities.py` | `TaskCompletion` |
| Domain | `src/domain/tasks/interfaces.py` | `ITaskCompletionRepository` |
| Infrastructure | `src/infrastructure/db/models/tasks.py` | `TaskCompletionModel` |
| Infrastructure | `src/infrastructure/db/repositories/tasks.py` | `TaskCompletionRepository` |

## DB table: `task_completions`
