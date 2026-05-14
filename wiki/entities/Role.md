---
type: value-object
title: Role
module: auth
layer: domain
tags: [value-object, auth, rbac]
---

# Role (Роль пользователя)

Value object модуля авторизации. `StrEnum` — сериализуется в строку без дополнительных конвертаций.

## Значения

| Значение | Описание |
|----------|---------|
| `director` | Директор — полный доступ ко всем функциям |
| `production` | Сотрудник производства — только свои задачи |
| `warehouse` | Сотрудник склада — приход, расход, резерв, отгрузка |
| `delivery` | Сотрудник доставки — выполнение назначенных доставок |

## Особенности

- Один пользователь может иметь несколько ролей одновременно
- Самостоятельная регистрация невозможна — роли назначает только директор
- Подробно о правах доступа: `wiki/concepts/rbac-roles.md`

## Расположение в коде

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/auth/value_objects.py` | `Role(StrEnum)` |
| Infrastructure | `src/infrastructure/db/models/auth.py` | `UserRoleModel` |
| Presentation | `src/presentation/api/v1/auth/dependencies.py` | `require_role(*roles)` — фабрика FastAPI-dependency |
| Presentation | `src/presentation/api/v1/dependencies.py` | `director_only`, `director_or_warehouse`, `director_or_production`, `director_or_delivery` |

## DB table: `user_roles`
