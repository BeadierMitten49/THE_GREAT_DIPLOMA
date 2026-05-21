# Backend Fixes — проблемы выявленные при разработке UI

---

## ~~BF-002~~ ✅ FIXED — auth_log не сохраняется при неудачном входе → rate limiting не работает

**Файл:** `src/presentation/api/v1/auth/auth.py` (обработка исключений), session middleware
**Проблема:** `log_attempt(success=False)` вызывается до `raise AuthenticationError()`, но исключение откатывает DB-сессию — запись в `auth_log` не сохраняется. Из-за этого `count_failed_recent` всегда возвращает 0 и `RateLimitError` никогда не срабатывает.
**Ожидаемое поведение:** Запись о неудачной попытке должна коммититься в БД до того как исключение выбрасывается наверх.
**Решение:** Сделать явный `await session.commit()` (или `flush`) после `log_attempt` внутри use case, до `raise`.

---

## ~~BF-001~~ ✅ FIXED — Деактивированный пользователь возвращает 401 вместо 403

**Файл:** `src/presentation/api/v1/auth/auth.py:20`
**Проблема:** `AuthenticationError` всегда маппится на 401, в том числе для случая `"user is deactivated"`. UI ждёт 403 для показа состояния «Учётная запись деактивирована».
**Ожидаемое поведение:** При `AuthenticationError("user is deactivated")` → HTTP 403.
**Текущее поведение:** HTTP 401.

