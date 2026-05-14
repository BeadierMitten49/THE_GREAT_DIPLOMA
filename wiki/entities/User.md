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
| Application (use cases) | `src/application/auth/use_cases.py` | `create_user`, `deactivate_user`, `reset_password`, `bind_telegram`, `login`, `refresh_tokens`, `logout` |
| Application (port) | `src/application/ports/auth.py` | `IUserCredentialRepository`, `IRefreshTokenRepository`, `IAuthLogRepository`, `IPasswordHasher`, `IJWTService` |
| Infrastructure (models) | `src/infrastructure/db/models/auth.py` | `UserModel`, `UserCredentialModel`, `UserRoleModel`, `AuthLogModel`, `RefreshTokenModel` |
| Infrastructure (repos) | `src/infrastructure/db/repositories/auth.py` | `UserRepository`, `UserCredentialRepository`, `RefreshTokenRepository`, `AuthLogRepository` |
| Infrastructure (security) | `src/infrastructure/security/password_hasher.py` | `BcryptPasswordHasher` |
| Infrastructure (security) | `src/infrastructure/security/jwt_service.py` | `JWTService` |
| Presentation (schemas) | `src/presentation/api/v1/auth/schemas.py` | `LoginRequest`, `RefreshRequest`, `TokenResponse`, `CreateUserRequest`, `UpdateUserRequest`, `SetRolesRequest`, `BindTelegramRequest`, `ResetPasswordRequest`, `UserResponse` |
| Presentation (service) | `src/presentation/api/v1/auth/service.py` | `AuthService`, `UserService` |
| Presentation (dependencies) | `src/presentation/api/v1/auth/dependencies.py` | `get_current_user`, `require_role`, `get_auth_service`, `get_user_service` |
| Presentation (router) | `src/presentation/api/v1/auth/auth.py` | `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` |
| Presentation (router) | `src/presentation/api/v1/auth/users.py` | `GET /users`, `GET /users/{id}`, `POST /users`, `PATCH /users/{id}`, `POST /users/{id}/roles`, `POST /users/{id}/deactivate`, `POST /users/{id}/activate`, `POST /users/{id}/bind-telegram`, `POST /users/{id}/reset-password` |

## DB tables: `users`, `user_credentials`, `user_roles`, `auth_log`, `refresh_tokens`
