# Git Workflow — АИС «Ярко»

## Ветки

```
main
 └── develop
      ├── feature/auth
      ├── feature/orders
      ├── feature/production
      ├── feature/warehouse
      ├── feature/delivery
      ├── feature/notifications
      ├── feature/reports
      ├── feature/dashboard
      └── feature/references
```

### `main`
Production. Только стабильный, протестированный код. Прямые пуши запрещены — только merge из `develop`. Каждый merge в `main` = релиз (тег версии).

### `develop`
Интеграционная ветка. Сюда сливаются завершённые фичи. Код здесь должен работать, но может быть не полным. Основная ветка для разработки.

### `feature/*`
Ветка под конкретный модуль или задачу. Создаётся от `develop`, вливается обратно в `develop`.

### `hotfix/*`
Критический баг в проде. Создаётся от `main`, вливается в `main` и `develop`.

```bash
git checkout main
git checkout -b hotfix/order-status-bug
# фикс
git checkout main && git merge hotfix/order-status-bug
git checkout develop && git merge hotfix/order-status-bug
git branch -d hotfix/order-status-bug
```

---

## Жизненный цикл фичи

```bash
# 1. Начать работу над модулем
git checkout develop
git pull origin develop
git checkout -b feature/orders

# 2. Разрабатываем, коммитим по ходу
git add src/orders/
git commit -m "feat(orders): add Order entity and status transitions"

# 3. Перед слиянием — подтянуть изменения из develop
git fetch origin
git rebase origin/develop

# 4. Влить в develop
git checkout develop
git merge --no-ff feature/orders -m "merge: feature/orders"
git push origin develop

# 5. Удалить ветку
git branch -d feature/orders
```

`--no-ff` сохраняет историю — в логе видно где начался и закончился каждый модуль.

---

## Конвенция коммитов

Формат: `<тип>(<модуль>): <что сделано>`

| Тип | Когда |
|-----|-------|
| `feat` | новая функциональность |
| `fix` | исправление бага |
| `refactor` | рефакторинг без изменения поведения |
| `test` | добавление/изменение тестов |
| `docs` | документация, wiki |
| `chore` | конфиг, зависимости, CI |
| `wip` | незавершённая работа (не попадает в `develop`) |

Модули: `auth`, `orders`, `production`, `warehouse`, `delivery`, `notifications`, `reports`, `dashboard`, `references`, `shared`

**Примеры:**
```
feat(orders): create order with stock availability check
feat(production): calculate raw material consumption from recipe
fix(warehouse): fix batch number reset on January 1st
refactor(auth): extract rate limiter to shared middleware
test(orders): add integration test for order reservation flow
chore: add alembic migration for auth_log table
docs: update git workflow

# merge feature-ветки в develop — тип отражает содержимое модуля:
feat(references): merge feature/references → develop — реализован модуль справочников
feat(auth): merge feature/auth → develop — реализована авторизация
fix(warehouse): merge hotfix/batch-reset → develop
```

---

## Правила

1. **Никаких прямых пушей в `main`** — только merge из `develop`.
2. **Никаких прямых пушей в `develop`** — только merge из `feature/*`.
3. **Одна ветка — один модуль/задача.** Не смешивать orders и warehouse в одной ветке.
4. **`wip:`-коммиты** — можно использовать внутри feature-ветки, в `develop` не попадают.
5. **Rebase перед merge** — подтянуть `develop` через `rebase`, не `merge`, чтобы не засорять историю.
6. **Тесты перед merge в develop** — `pytest tests/` должен проходить.
7. **Wiki entities** обновляются в той же ветке где добавляется сущность.

---

## Теги и релизы

При каждом merge в `main`:

```bash
git tag -a v1.0.0 -m "release: orders + production modules"
git push origin v1.0.0
```

Версионирование: `v<major>.<minor>.<patch>`
- `major` — большой релиз (новый модуль в проде)
- `minor` — новая функциональность внутри модуля
- `patch` — hotfix

---

## Типичный рабочий день

```bash
# Начало работы — всегда синхронизируемся
git checkout develop
git pull origin develop

# Переходим на свою feature-ветку
git checkout feature/warehouse

# Работаем, коммитим по ходу
git commit -m "feat(warehouse): add raw material arrival use case"
git commit -m "feat(warehouse): add critical stock check"
git commit -m "test(warehouse): add unit tests for stock reservation"

# Конец дня — пушим ветку (бэкап + виден прогресс)
git push origin feature/warehouse
```

---

## Сценарии переходов

### 1. Начало нового модуля

```
develop ──────────────────────────●
                                   \
feature/references ─────────────────●──●──●
```

```bash
git checkout develop
git pull origin develop
git checkout -b feature/references

# пишем модуль...

git checkout develop
git merge --no-ff feature/references -m "merge: feature/references"
git push origin develop
git branch -d feature/references
```

---

### 2. Параллельная работа: один модуль зависит от другого

Ситуация: начал `feature/orders`, но нужна функция из `feature/warehouse` которая ещё не в `develop`.

```
develop          ──────────────────────────────────────────●
                  \                                       /
feature/warehouse  ●──●──●──● (merge в develop) ─────────
                                  \
feature/orders   (ждём merge)      ●──●──●──●────────────●
```

```bash
# Вариант А — ждём пока warehouse вольётся в develop, потом начинаем orders
git checkout develop
git pull origin develop
git checkout -b feature/orders

# Вариант Б — срочно нужна конкретная функция из warehouse, не ждём
git checkout feature/orders
git cherry-pick <commit-hash>   # берём только нужный коммит
# когда warehouse вольётся в develop — делаем rebase чтобы убрать дубль
git rebase origin/develop
```

---

### 3. Подтягиваем обновления из develop в свою ветку

Пока ты работал над `feature/orders`, в `develop` влили `feature/warehouse`.
Нужно подтянуть чтобы не было расхождений.

```bash
git checkout feature/orders
git fetch origin
git rebase origin/develop

# если есть конфликты — решаем, потом
git rebase --continue

# принудительно обновляем свою ветку на remote (rebase переписывает историю)
git push --force-with-lease origin feature/orders
```

`--force-with-lease` безопаснее чем `--force` — не перезапишет если кто-то ещё пушил в эту ветку.

---

### 4. Завершение модуля и merge в develop

```bash
# Убеждаемся что тесты проходят
pytest tests/

# Подтягиваем develop
git fetch origin
git rebase origin/develop

# Вливаем
git checkout develop
git merge --no-ff feature/production -m "merge: feature/production"
git push origin develop

# Чистим
git branch -d feature/production
git push origin --delete feature/production
```

---

### 5. Релиз в прод

Когда в `develop` набралось достаточно готовых модулей для релиза.

```bash
git checkout main
git pull origin main
git merge --no-ff develop -m "release: v1.0.0 — references, auth, warehouse"

git tag -a v1.0.0 -m "release: v1.0.0"
git push origin main
git push origin v1.0.0

# Синхронизируем develop с main (на случай если в main были hotfix-ы)
git checkout develop
git merge main
git push origin develop
```

---

### 6. Hotfix — критический баг в проде

```
main     ──────────────────────●──────────────●
                                \             /
hotfix/x                         ●──●─────────
                                          \
develop  ────────────────────────────────●──●
```

```bash
# Создаём от main
git checkout main
git pull origin main
git checkout -b hotfix/auth-rate-limit-bypass

# Чиним
git commit -m "fix(auth): prevent rate limit bypass via null username"

# Вливаем в main
git checkout main
git merge --no-ff hotfix/auth-rate-limit-bypass
git tag -a v1.0.1 -m "hotfix: auth rate limit"
git push origin main
git push origin v1.0.1

# Вливаем в develop чтобы фикс не потерялся
git checkout develop
git merge hotfix/auth-rate-limit-bypass
git push origin develop

git branch -d hotfix/auth-rate-limit-bypass
```

---

### 7. Обновление wiki entities при добавлении сущности

Wiki entities живут в git — обновляем в той же feature-ветке.

```bash
git checkout feature/orders

# написали Order entity в src/domain/orders/entities.py
# сразу обновляем wiki

# создаём/обновляем wiki/entities/Order.md
git add src/domain/orders/entities.py
git add wiki/entities/Order.md
git commit -m "feat(orders): add Order entity + wiki"
```

---

## Порядок разработки модулей

Рекомендуемый порядок с учётом зависимостей:

```
1. references   ← справочники нужны всем модулям
2. auth         ← без авторизации нечего защищать
3. warehouse    ← от него зависят orders и production
4. production   ← зависит от warehouse (сырьё)
5. orders       ← зависит от warehouse (резерв продукции) и production
6. delivery     ← зависит от orders
7. notifications← подключается по ходу к каждому модулю
8. reports      ← последний, читает данные всех модулей
9. dashboard    ← агрегирует данные всех модулей
```
