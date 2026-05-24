---
type: entity
title: ProductionTask
module: tasks
layer: domain
tags: [entity, tasks, aggregate-root]
---

# ProductionTask (Производственная задача)

Агрегат-рут модуля задач. Представляет задание на производство определённого количества продукции.

## Поля

| Поле | Тип | Описание |
|------|-----|---------|
| id | int \| None | PK |
| product_id | int | FK → `products`, какой продукт производить |
| quantity | int | Плановое количество в штуках |
| executor_id | int | FK → `users`, исполнитель (роль «Производство») |
| start_date | date | Плановая дата начала |
| deadline | date | Дедлайн |
| task_type | [[TaskType]] | Тип: `stock_task` или `order_task` |
| status | [[TaskStatus]] | Текущий статус |
| order_id | int \| None | FK → `orders`, только для `order_task` |
| comment | str \| None | Комментарий |
| is_active | bool | Признак активности (soft delete) |
| created_at | datetime \| None | Дата создания |
| actual_start_at | datetime \| None | Фактическое время начала работы |
| actual_end_at | datetime \| None | Фактическое время завершения |

## Поведение

- `start()` — переход `created → in_progress`, фиксирует `actual_start_at`
- `stop()` — переход `in_progress → stopped`
- `resume()` — переход `stopped → in_progress`
- `complete()` — переход `in_progress → completed`, фиксирует `actual_end_at`
- `close()` — переход `completed → closed`
- `delete()` — soft delete

## Типы задач

| Тип | Описание |
|-----|---------|
| `stock_task` | Задача в запас — пополнение склада без привязки к заказу |
| `order_task` | Задача под заказ — привязана к конкретному [[Order|заказу]] |

## Статусы

```
Создана → В работе ⇄ Остановлена → Завершена → Закрыта
```

## Что происходит при создании

Система автоматически рассчитывает потребность в сырье по рецептуре ([[RecipeLine]]) и резервирует сырьё со склада FIFO по сроку годности. Если сырья недостаточно — предупреждение, но создание не блокируется.

## Что происходит при завершении (`complete`)

1. Сохраняется отчёт [[TaskCompletion]] с фактическим количеством и расходом сырья
2. Снимаются [[RawMaterialReservation|резервы сырья]]

## Что происходит при закрытии (`close`)

1. **Списание сырья** — фактический расход из отчёта списывается со склада сырья FIFO по сроку годности
2. **Добавление продукции** — создаётся [[ProductStock]] на складе готовой продукции
3. **Для `order_task`** — продукция сразу резервируется под заказ ([[ProductReservation]])

## Связи

- Ссылается на → [[Product]], [[User]], [[Order]] (опционально)
- Владеет → [[TaskStop]], [[TaskCompletion]], [[RawMaterialReservation]]

## Расположение в коде

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/tasks/entities.py` | `ProductionTask` |
| Domain | `src/domain/tasks/interfaces.py` | `IProductionTaskRepository` |
| Domain | `src/domain/tasks/value_objects.py` | `TaskStatus`, `TaskType` |
| Infrastructure | `src/infrastructure/db/models/tasks.py` | `ProductionTaskModel` |
| Infrastructure | `src/infrastructure/db/repositories/tasks.py` | `ProductionTaskRepository` |
| Application | `src/application/tasks/use_cases.py` | `create_task`, `start_task`, `stop_task`, `resume_task`, `complete_task`, `close_task`, `reassign_task`, `delete_task` |
| Application | `src/application/tasks/dto.py` | `CreateTaskDTO`, `CompleteTaskDTO`, `ConsumptionInputDTO` |
| Presentation | `src/presentation/api/v1/tasks/service.py` | `ProductionTaskService` |
| Presentation | `src/presentation/api/v1/tasks/router.py` | router |

## API-эндпоинты

| Метод | Путь | Описание |
|-------|------|---------|
| GET | `/api/v1/tasks` | Список задач (фильтры: status, executor_id) |
| GET | `/api/v1/tasks/{id}` | Получить задачу |
| GET | `/api/v1/tasks/{id}/drawer` | Обогащённые данные для drawer |
| POST | `/api/v1/tasks` | Создать задачу (201) |
| POST | `/api/v1/tasks/{id}/start` | Начать (204) |
| POST | `/api/v1/tasks/{id}/stop` | Остановить (204) |
| POST | `/api/v1/tasks/{id}/resume` | Возобновить (204) |
| POST | `/api/v1/tasks/{id}/complete` | Завершить с отчётом (204) |
| POST | `/api/v1/tasks/{id}/close` | Закрыть (204) |
| PATCH | `/api/v1/tasks/{id}/assignee` | Переназначить (204) |
| DELETE | `/api/v1/tasks/{id}` | Удалить (soft delete, 204) |

## DB table: `production_tasks`
