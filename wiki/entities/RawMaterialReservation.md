---
type: entity
title: RawMaterialReservation
module: tasks
layer: domain
tags: [entity, tasks, warehouse]
---

# RawMaterialReservation (Резерв сырья)

Связывает [[ProductionTask|производственную задачу]] с конкретной партией [[RawMaterialStock|сырья]] на складе. Зарезервированное сырьё недоступно для других задач.

## Поля

| Поле | Тип | Описание |
|------|-----|---------|
| id | int \| None | PK |
| stock_id | int | FK → `raw_material_stock` |
| task_id | int | FK → `production_tasks` |
| quantity | Decimal | Зарезервированное количество |
| created_at | datetime \| None | Дата создания резерва |

## Когда создаётся

При создании задачи (`create_task`) система автоматически рассчитывает потребность по рецептуре и резервирует сырьё FIFO по сроку годности. Если сырья недостаточно — задача всё равно создаётся, но возвращается список `insufficient_material_ids`.

## Когда снимается

- При завершении задачи (`complete_task`) — все резервы задачи удаляются
- При удалении задачи (`delete_task`) — все резервы задачи удаляются

## Связи

- Принадлежит → [[ProductionTask]]
- Ссылается на → [[RawMaterialStock]]

## Расположение в коде

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/tasks/entities.py` | `RawMaterialReservation` |
| Domain | `src/domain/tasks/interfaces.py` | `IRawMaterialReservationRepository` |
| Infrastructure | `src/infrastructure/db/models/tasks.py` | `RawMaterialReservationModel` |
| Infrastructure | `src/infrastructure/db/repositories/tasks.py` | `RawMaterialReservationRepository` |

## DB table: `raw_material_reservations`
