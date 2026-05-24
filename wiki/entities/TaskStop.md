---
type: entity
title: TaskStop
module: tasks
layer: domain
tags: [entity, tasks]
---

# TaskStop (Остановка задачи)

Сущность модуля задач. Фиксирует факт остановки [[ProductionTask|производственной задачи]] с причиной и временными метками.

## Поля

| Поле | Тип | Описание |
|------|-----|---------|
| id | int \| None | PK |
| task_id | int | FK → `production_tasks` |
| reason | str | Причина остановки (обязательна) |
| stopped_at | datetime | Время остановки |
| resumed_at | datetime \| None | Время возобновления (None = ещё остановлена) |

## Жизненный цикл

- Создаётся при вызове `stop_task` — фиксирует `stopped_at` и `reason`
- При вызове `resume_task` — заполняется `resumed_at` у открытой остановки
- Задача может иметь несколько записей остановок (многократные остановки)

## Связи

- Принадлежит → [[ProductionTask]]

## Расположение в коде

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/tasks/entities.py` | `TaskStop` |
| Domain | `src/domain/tasks/interfaces.py` | `ITaskStopRepository` |
| Infrastructure | `src/infrastructure/db/models/tasks.py` | `TaskStopModel` |
| Infrastructure | `src/infrastructure/db/repositories/tasks.py` | `TaskStopRepository` |

## DB table: `task_stops`
