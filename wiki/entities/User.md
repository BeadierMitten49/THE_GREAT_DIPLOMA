---
type: entity
title: User
module: auth
layer: domain
tags: [entity, auth, aggregate-root]
---

# User (Пользователь)

Агрегат-рут модуля авторизации. Представляет сотрудника предприятия с одной или несколькими ролями.

## Поля

| Поле | Тип | Описание |
|------|-----|---------|
| id | int \| None | PK, присваивается БД после сохранения |
| username | str | Логин для входа, уникальный, автогенерируется из ФИО в application-слое |
| full_name | str | Полное имя, отображается в интерфейсе и копируется в архивные таблицы |
| roles | list[Role] | Роли пользователя (мультироль) |
| is_active | bool | Признак активности (soft delete) |
| telegram_username | str \| None | Вводит директор при создании пользователя |
| telegram_id | int \| None | Сохраняется после /start в боте |

> `hashed_password` и `created_at` — не в domain-сущности. Пароль хранится в отдельной таблице `user_credentials`, доступ через `IUserCredentialRepository` (application/ports).

## Поведение

- `has_role(role) -> bool` — проверка наличия роли
- `add_role(role)` — добавить роль (дубликаты игнорируются)
- `remove_role(role)` — убрать роль (если нет — no-op)
- `deactivate()` / `activate()` — управление активностью
- `set_telegram_username(username)` — директор вводит при создании/редактировании
- `set_telegram_id(telegram_id)` — вызывается когда пользователь написал /start боту

## Инварианты

- `username` и `full_name` не могут быть пустыми
- `telegram_id > 0`
- `telegram_username` может быть задан без `telegram_id` (пользователь ещё не нажал /start)

## Жизненный цикл Telegram-привязки

```
None / None          ← Telegram не настроен
username / None      ← директор добавил, пользователь не нажал /start
username / id        ← полностью привязан
```

## Связи

- Владеет → [[Role]] (value object)
- Используется в → `orders`, `production_tasks`, `deliveries`, `notifications`

## Расположение в коде

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/auth/entities.py` | `User` |
| Domain | `src/domain/auth/interfaces.py` | `IUserRepository` |
| Application (port) | `src/application/ports/auth.py` | `IUserCredentialRepository` |
| Infrastructure | `src/infrastructure/db/models/auth.py` | `UserModel`, `UserCredentialModel` |
| Infrastructure | `src/infrastructure/db/repositories/auth.py` | `UserRepository`, `UserCredentialRepository` |

## DB tables: `users`, `user_credentials`, `user_roles`
