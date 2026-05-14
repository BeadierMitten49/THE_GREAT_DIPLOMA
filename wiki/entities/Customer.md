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

- Domain: `src/domain/references/entities.py`
- Repository interface: `src/domain/references/interfaces.py` → `ICustomerRepository`
- SQLAlchemy model: `src/infrastructure/db/models/references.py` → `CustomerModel`
- Repository impl: `src/infrastructure/db/repositories/references.py` → `CustomerRepository`
- DB table: `customers`
