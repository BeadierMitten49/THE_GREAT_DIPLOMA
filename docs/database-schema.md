# Схема базы данных — АИС «Ярко»

Выведена из SRS. Источник: `wiki/sources/SRS-Yarko-v3.md`.

**Правила хранения количеств:** везде храним только в **штуках**. Пересчёт в коробки (`units / units_per_box`) — на стороне фронта/API-ответа.

---

## Авторизация и пользователи

### `users`
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| username | str, unique | автогенерируется из ФИО |
| full_name | str | |
| is_active | bool | деактивация вместо удаления |
| telegram_username | str, nullable | вводит директор |
| telegram_id | bigint, nullable | сохраняется после /start |
| created_at | datetime | |

### `user_credentials`
Хранит учётные данные отдельно от бизнес-сущности пользователя. Domain-сущность `User` не знает про пароль.

| Поле | Тип | Примечание |
|------|-----|-----------|
| user_id | FK → users, PK | один к одному |
| hashed_password | str | bcrypt |
| updated_at | datetime | обновляется при смене пароля |

### `user_roles`
Связь many-to-many: один пользователь — несколько ролей.

| Поле | Тип | Примечание |
|------|-----|-----------|
| user_id | FK → users | |
| role | enum | director, production, warehouse, delivery |

### `auth_log`
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| username_attempt | str | что ввёл пользователь |
| user_id | FK → users, nullable | null если пользователь не найден |
| success | bool | |
| created_at | datetime | |

### `refresh_tokens`
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| user_id | FK → users | |
| token | str, unique | |
| expires_at | datetime | |
| created_at | datetime | |

---

## Справочники

### `customers` (заказчики)
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| name | str | |
| default_address | str | автоподставляется в заказ при создании |
| is_active | bool | |

### `products` (готовая продукция)
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| name | str | |
| units_per_box | int | штук в коробке (фасовка) |
| shelf_life_days | int | срок годности |
| critical_stock | int | пороговый остаток (в штуках) |
| is_active | bool | |

### `raw_materials_catalog` (справочник сырья)
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| name | str | |
| unit | str | кг, л и т.д. |
| shelf_life_days | int | |
| critical_stock | decimal | |
| is_active | bool | |

### `packaging_catalog` (справочник упаковки)
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| name | str | |
| unit | str | |
| critical_stock | int | |
| is_active | bool | |

### `recipes` (рецептура)
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| product_id | FK → products | |
| raw_material_id | FK → raw_materials_catalog | |
| consumption_per_unit | decimal | норма расхода на 1 штуку |
| waste_percentage | decimal | % брака |

---

## Заказы

### `orders`
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| number | int, unique | автогенерируется |
| customer_id | FK → customers | |
| delivery_address | str | копируется из customers.default_address при создании; хранится отдельно чтобы сохранить адрес доставки даже если у заказчика он потом изменится |
| status | enum | created, production, assembly, delivery, completed |
| delivery_date | date | |
| delivery_user_id | FK → users | исполнитель доставки |
| comment | str, nullable | |
| created_at | datetime | |
| is_deleted | bool | soft delete |

### `order_items`
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| order_id | FK → orders | |
| product_id | FK → products | |
| quantity | int | в штуках |

---

## Производственные задачи

### `production_tasks`
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| type | enum | order_task, stock_task |
| product_id | FK → products | |
| quantity | int | в штуках |
| executor_id | FK → users | роль: production |
| start_date | date | плановая дата начала |
| deadline | date | |
| status | enum | created, in_progress, stopped, completed, closed |
| order_id | FK → orders, nullable | только для order_task |
| comment | str, nullable | |
| created_at | datetime | |
| actual_start_at | datetime, nullable | |
| actual_end_at | datetime, nullable | |
| is_deleted | bool | soft delete |

### `task_stops` (остановки задачи)
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| task_id | FK → production_tasks | |
| reason | str | обязателен |
| stopped_at | datetime | |
| resumed_at | datetime, nullable | null если ещё не возобновлена |

### `task_completions` (отчёт сотрудника при завершении)
Заполняется сотрудником при переводе задачи в статус «Завершена».

| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| task_id | FK → production_tasks, unique | один отчёт на задачу |
| actual_quantity | int | фактически произведено, в штуках |
| comment | str, nullable | |
| created_at | datetime | |

### `task_completion_consumption` (фактический расход сырья)
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| completion_id | FK → task_completions | |
| raw_material_id | FK → raw_materials_catalog | |
| planned_qty | decimal | рассчитано при создании задачи |
| actual_qty | decimal | введено сотрудником |
| waste_qty | decimal, nullable | брак |

---

## Склад

### `raw_material_stock` (склад сырья)
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| raw_material_id | FK → raw_materials_catalog | |
| quantity | decimal | в единицах из справочника (кг и т.д.) |
| arrival_date | date | |
| expiry_date | date | arrival_date + shelf_life_days |
| comment | str, nullable | |

### `packaging_stock` (склад упаковки)
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| packaging_id | FK → packaging_catalog | |
| quantity | int | |
| comment | str, nullable | |

### `products_stock` (склад готовой продукции)
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| product_id | FK → products | |
| quantity | int | в штуках |
| batch_number | int | n+1; сбрасывается 1 января |
| batch_year | int | год партии |
| arrival_date | date | |
| expiry_date | date | автоматически |
| comment | str, nullable | |

### `raw_material_reservations` (резерв сырья под задачу)
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| stock_id | FK → raw_material_stock | |
| task_id | FK → production_tasks | |
| quantity | decimal | |
| created_at | datetime | |

### `products_reservations` (резерв продукции под заказ)
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| stock_id | FK → products_stock | |
| order_id | FK → orders | |
| quantity | int | в штуках |
| created_at | datetime | |

---

## Доставка

### `deliveries`
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| order_id | FK → orders, unique | |
| executor_id | FK → users | роль: delivery |
| status | enum | pending, picked_up, in_transit, completed, cancelled |
| planned_date | date | |
| started_at | datetime, nullable | «Начать выезд» |
| completed_at | datetime, nullable | |
| cancellation_reason | str, nullable | обязателен при отмене |

---

## Уведомления

### `notifications`
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| user_id | FK → users | |
| message | str | |
| is_read | bool | |
| created_at | datetime | |

---

## Настройки

### `settings`
| Поле | Тип | Примечание |
|------|-----|-----------|
| key | str, PK | |
| value | str | |

Используется для хранения токена Telegram-бота (директор вводит через UI).

---

## Архив (отчёты)

Денормализованные снапшоты. Хранят строки вместо FK — данные остаются читаемыми даже если оперативные таблицы очищены. Заполняются при закрытии задачи / завершении заказа.

### `orders_archive`
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| order_id | int | без FK — ссылка на оригинал если жив |
| order_number | int | |
| customer_name | str | скопировано из customers.name |
| delivery_address | str | адрес по которому реально везли |
| delivery_date_planned | date | |
| delivery_date_actual | date, nullable | |
| delivery_executor_name | str | скопировано из users.full_name |
| status | str | финальный статус |
| comment | str, nullable | |
| items | json | [{product_name, quantity, units_per_box}, ...] |
| archived_at | datetime | |

### `tasks_archive`
| Поле | Тип | Примечание |
|------|-----|-----------|
| id | PK | |
| task_id | int | без FK |
| type | str | order_task / stock_task |
| product_name | str | скопировано из products.name |
| planned_quantity | int | в штуках |
| actual_quantity | int | из отчёта сотрудника |
| executor_name | str | скопировано из users.full_name |
| planned_start_date | date | |
| actual_start_at | datetime, nullable | |
| actual_end_at | datetime, nullable | |
| deadline | date | |
| order_number | int, nullable | если task типа order_task |
| comment | str, nullable | |
| stops | json | [{reason, stopped_at, resumed_at}, ...] |
| consumption | json | [{material_name, unit, planned_qty, actual_qty, waste_qty}, ...] |
| archived_at | datetime | |

---

## Итого

| Группа | Таблиц |
|--------|--------|
| Авторизация и пользователи | 5 |
| Справочники | 5 |
| Заказы | 2 |
| Производственные задачи | 4 |
| Склад | 5 |
| Доставка | 1 |
| Уведомления | 1 |
| Настройки | 1 |
| Архив | 2 |
| **Итого** | **26** |
