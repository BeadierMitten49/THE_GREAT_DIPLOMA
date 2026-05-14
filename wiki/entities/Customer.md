---
type: entity
title: Customer
module: references
layer: domain
tags: [entity, references, aggregate-root]
---

# Customer (Заказчик)

Агрегат-рут модуля справочников. Представляет юридическое или физическое лицо, которому отгружается продукция.

## Поля

| Поле | Тип | Описание |
|------|-----|---------|
| id | int \| None | PK, присваивается БД после сохранения |
| name | str | Наименование заказчика |
| default_address | str | Адрес доставки по умолчанию, копируется в заказ при создании |
| is_active | bool | Признак активности (soft delete) |

## Поведение

- `update(name, default_address)` — обновляет поля с валидацией
- `deactivate()` — переводит в неактивное состояние
- `activate()` — возвращает в активное состояние

## Инварианты

- `name` и `default_address` не могут быть пустыми или состоять только из пробелов

## Расположение в коде

| Слой | Файл | Символ |
|------|------|--------|
| Domain | `src/domain/references/entities.py` | `Customer` |
| Domain | `src/domain/references/interfaces.py` | `ICustomerRepository` |
| Domain | `src/domain/references/exceptions.py` | `InvalidFieldError` |
| Infrastructure | `src/infrastructure/db/models/references.py` | `CustomerModel` |
| Infrastructure | `src/infrastructure/db/repositories/references.py` | `CustomerRepository` |
| Application | `src/application/references/use_cases.py` | `get_customer`, `get_customers`, `create_customer`, `update_customer`, `deactivate_customer`, `activate_customer` |
| Application | `src/application/references/exceptions.py` | `NotFoundError`, `AlreadyExistsError` |
| Application | `src/application/references/dto.py` | `CreateCustomerDTO`, `UpdateCustomerDTO` |
| Presentation | `src/presentation/api/v1/references/service.py` | `CustomerService` |
| Presentation | `src/presentation/api/v1/references/customers.py` | router |
| Presentation | `src/presentation/api/v1/references/schemas.py` | `CreateCustomerRequest`, `UpdateCustomerRequest`, `CustomerResponse` |

## API-эндпоинты

| Метод | Путь | Описание |
|-------|------|---------|
| GET | `/api/v1/references/customers` | Список (по умолчанию только активные) |
| GET | `/api/v1/references/customers/{id}` | Получить по ID |
| POST | `/api/v1/references/customers` | Создать (201) |
| PATCH | `/api/v1/references/customers/{id}` | Обновить (200) |
| POST | `/api/v1/references/customers/{id}/deactivate` | Деактивировать (204) |
| POST | `/api/v1/references/customers/{id}/activate` | Активировать (204) |

## DB table: `customers`
