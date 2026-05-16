# Реестр имён — АИС «Ярко»

Единый источник истины для названий сущностей, таблиц, use cases и API-маршрутов.
**Перед добавлением нового имени в любой слой — сначала внести сюда.**

---

## Phase 1 — References (справочники)

| Концепт | Entity | DB table | Use case prefix | API prefix |
|---------|--------|----------|-----------------|------------|
| Заказчик | `Customer` | `customers` | `*_customer` | `/customers` |
| Продукция | `Product` | `products` | `*_product` | `/products` |
| Строка рецептуры | `RecipeLine` | `recipes` | `set_product_recipe` | `/products/{id}/recipe` |
| Сырьё (справочник) | `RawMaterialCatalog` | `raw_materials_catalog` | `*_raw_material` | `/raw-materials` |
| Упаковка (справочник) | `PackagingCatalog` | `packaging_catalog` | `*_packaging` | `/packaging` |

---

## Phase 2 — Auth (авторизация)

| Концепт | Entity / VO | DB table | Use case prefix | API prefix |
|---------|-------------|----------|-----------------|------------|
| Пользователь | `User` | `users` | `*_user` | `/users` |
| Роль | `Role` (StrEnum) | `user_roles` | — | — |
| Учётные данные | — | `user_credentials` | — | — |
| Лог авторизации | — | `auth_log` | `login`, `logout` | `/auth/login`, `/auth/logout` |
| Refresh-токен | — | `refresh_tokens` | `refresh_tokens` | `/auth/refresh` |

---

## Phase 3 — Warehouse (склад)

| Концепт | Entity | DB table | Use case prefix | API prefix |
|---------|--------|----------|-----------------|------------|
| Партия сырья | `RawMaterialStock` | `raw_material_stock` | `raw_material_stock_*` | `/raw-material-stock` |
| Остаток упаковки | `PackagingStock` | `packaging_stock` | `packaging_stock_*` | `/packaging-stock` |
| Партия продукции | `ProductStock` | `products_stock` | `product_stock_*` | `/product-stock` |
| Резерв сырья | `RawMaterialReservation` | `raw_material_reservations` | `reserve_raw_material_stock` / `release_raw_material_stock` | — | → **domain/production** |
| Резерв продукции | `ProductReservation` | `products_reservations` | `reserve_product_stock` / `release_product_stock` | — | → **domain/orders** |

---

## Phase 4 — Tasks (производственные задачи)

| Концепт | Entity / VO | DB table | Use case prefix | API prefix |
|---------|-------------|----------|-----------------|------------|
| Производственная задача | `ProductionTask` | `production_tasks` | `*_task` | `/tasks` |
| Статус задачи | `TaskStatus` (StrEnum) | — | — | — |
| Остановка задачи | `TaskStop` | `task_stops` | `stop_task` / `resume_task` | `/tasks/{id}/stop`, `/tasks/{id}/resume` |
| Отчёт завершения | `TaskCompletion` | `task_completions` | `complete_task` | `/tasks/{id}/complete` |
| Расход сырья (отчёт) | `TaskCompletionConsumption` | `task_completion_consumption` | — | — |

---

## Phase 5 — Orders (заказы)

| Концепт | Entity / VO | DB table | Use case prefix | API prefix |
|---------|-------------|----------|-----------------|------------|
| Заказ | `Order` | `orders` | `*_order` | `/orders` |
| Позиция заказа | `OrderItem` | `order_items` | — | — |
| Статус заказа | `OrderStatus` (StrEnum) | — | — | — |

---

## Phase 6 — Delivery (доставки)

| Концепт | Entity / VO | DB table | Use case prefix | API prefix |
|---------|-------------|----------|-----------------|------------|
| Доставка | `Delivery` | `deliveries` | `*_delivery` | `/deliveries` |
| Статус доставки | `DeliveryStatus` (StrEnum) | — | — | — |

---

## Phase 7 — Notifications (уведомления)

| Концепт | Entity | DB table | Use case prefix | API prefix |
|---------|--------|----------|-----------------|------------|
| Уведомление | `Notification` | `notifications` | — | `/notifications` |
| Настройки | — | `settings` | — | `/settings` |

---

## Phase 8 — Reports + Archive (отчёты)

| Концепт | Entity | DB table | Use case prefix | API prefix |
|---------|--------|----------|-----------------|------------|
| Архив заказа | `OrderArchive` | `orders_archive` | `archive_order` | `/reports/orders` |
| Архив задачи | `TaskArchive` | `tasks_archive` | `archive_task` | `/reports/tasks` |

---

## Правила

- Имя entity = PascalCase, строго по таблице выше
- Имя таблицы = snake_case, строго по таблице выше
- Use case = `глагол_существительное` в snake_case
- API prefix = kebab-case, множественное число
- При расхождении между слоями — таблица выше главнее roadmap и старого кода
