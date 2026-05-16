# CLAUDE.md — АИС «Ярко»

Прочитай этот файл полностью перед началом любой работы.

---

## Проект

**АИС «Ярко»** — веб-система автоматизации производственного предприятия по фасовке пищевого сырья. Разрабатывается как дипломная работа, идёт в production, послужит основой для других систем.

- Стек: **FastAPI + SQLAlchemy + PostgreSQL**
- Прототип UI: **Streamlit** (не production UI)
- Архитектура: **DDD (Domain-Driven Design)**
- Документация: `docs/`
- База требований: `wiki/sources/SRS-Yarko-v3.md`

---

## Архитектура — обязательно к соблюдению

Четыре слоя, зависимости строго в одну сторону:

```
presentation → application → domain
infrastructure → domain
```

**`domain/`** — чистая бизнес-логика. Никаких импортов FastAPI, SQLAlchemy, httpx и любых фреймворков. Только стандартная библиотека Python и `shared/`.

**`application/`** — use cases. Не знает о HTTP, не знает о SQLAlchemy. Работает через интерфейсы (`ports/`).

**`infrastructure/`** — реализует интерфейсы из `domain/` и `application/ports/`. Здесь живут SQLAlchemy-модели, репозитории, Telegram-клиент.

**`presentation/`** — FastAPI-роутеры и Streamlit-страницы. Роутеры вызывают только **service-классы** (живут в `presentation/`), которые инкапсулируют создание репозитория и вызов use cases. Никогда не лезут в репозитории и use cases напрямую из роутера.

Нарушение этих правил — архитектурная ошибка, исправляй сразу.

---

## Git — правила

Полный workflow: `docs/git-workflow.md`. Коротко:

- Ветки: `main` → `develop` → `feature/*` / `hotfix/*`
- Прямые пуши в `main` и `develop` **запрещены**
- Перед merge в `develop` — `pytest tests/` должен проходить
- Rebase при подтягивании `develop` в feature-ветку, не merge
- Merge в `develop` только через `--no-ff`

**Конвенция коммитов:** `<тип>(<модуль>): <что сделано>`

Типы: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `wip`

Модули: `auth`, `orders`, `tasks`, `warehouse`, `delivery`, `notifications`, `reports`, `dashboard`, `references`, `shared`

---

## Wiki

**Что в git:** только `wiki/entities/` — обновляй в той же feature-ветке что и код.

**Что на диске (gitignored):** `wiki/concepts/`, `wiki/sources/`, `wiki/log.md`, `wiki/hot.md`, `wiki/index.md`

При добавлении новой доменной сущности — создавай или обновляй соответствующий файл в `wiki/entities/`.

---

## Кодовые правила

**Бизнес-логика** — в `domain/` или `application/`, никогда в роутерах.

**Роутеры** — только: принять запрос → вызвать метод service-класса → вернуть ответ. Без логики.

**Service-классы** (`presentation/api/v1/<module>/service.py`) — фасад между роутером и application-слоем. Принимают `AsyncSession`, сами создают конкретный репозиторий, вызывают use cases. Это единственное место где конкретный репозиторий создаётся в presentation-слое.

**Репозитории** — интерфейс в `domain/`, реализация в `infrastructure/db/repositories/`. Use cases работают только с интерфейсом. Service-классы создают конкретную реализацию и передают её в use case.

**Уведомления** — только через `INotificationService` из `application/ports/`. Прямых вызовов Telegram из бизнес-логики нет.

**Логи авторизации** — таблица `auth_log` в БД, не файл.

**Сессии** — долгоживущий refresh token, без автовыхода по таймауту.

---

## Порядок разработки модулей

```
references → auth → warehouse → orders → tasks → delivery → notifications → reports → dashboard
```

Не начинай модуль если его зависимости не влиты в `develop`.

---

## Чего не делать

- Не добавляй функциональность сверх текущей задачи
- Не рефакторь код вне текущей задачи
- Не нарушай направление зависимостей между слоями
- Не пиши бизнес-логику в роутерах
- Не делай физическое удаление записей
- Не коммить в `main` или `develop` напрямую
- Не добавляй новые зависимости без явного запроса

---

## Где что найти

| Что | Где |
|-----|-----|
| Обзор требований | `wiki/sources/SRS-Yarko-v3.md` |
| Роли и доступ | `wiki/concepts/rbac-roles.md` |
| Модуль заказов | `wiki/concepts/order-management.md` |
| Производственные задачи | `wiki/concepts/production-tasks.md` |
| Склад | `wiki/concepts/warehouse-management.md` |
| Доставка | `wiki/concepts/delivery-module.md` |
| Уведомления Telegram | `wiki/concepts/telegram-notifications.md` |
| Схема БД (таблицы) | `docs/database-schema.md` |
| ERD диаграмма | `docs/erd.md` |
| Структура проекта | `docs/project-structure.md` |
| Git workflow | `docs/git-workflow.md` |
| Доменные сущности | `wiki/entities/` |
