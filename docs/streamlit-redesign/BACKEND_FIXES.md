# Backend Fixes — проблемы выявленные при разработке UI

---

## BF-001 — Деактивированный пользователь возвращает 401 вместо 403

**Файл:** `src/presentation/api/v1/auth/auth.py:20`
**Проблема:** `AuthenticationError` всегда маппится на 401, в том числе для случая `"user is deactivated"`. UI ждёт 403 для показа состояния «Учётная запись деактивирована».
**Ожидаемое поведение:** При `AuthenticationError("user is deactivated")` → HTTP 403.
**Текущее поведение:** HTTP 401.

