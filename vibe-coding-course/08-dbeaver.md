# Модуль 8: DBeaver — графический клиент для SQL

**Время**: 1 час
**Цель**: освоить DBeaver для визуальной работы с базой данных

---

## Что такое DBeaver

DBeaver — это программа с окошками, кнопками и таблицами для работы с БД.
Вместо того чтобы печатать команды в чёрном окне psql, ты видишь данные как в Excel.

## Шаг 1: Установка DBeaver (если не установили)

1. Перейти на [dbeaver.io](https://dbeaver.io)
2. Нажать Download, выбрать Windows (Community Edition — бесплатно)
3. Установить (все опции по умолчанию)

## Шаг 2: Подключение к PostgreSQL

1. Открыть DBeaver
2. Нажать иконку **New Database Connection** (молния с +)
3. Выбрать **PostgreSQL**
4. Ввести:
   - Host: `localhost`
   - Port: `5432`
   - Database: `supply_db`
   - Username: `postgres`
   - Password: (пароль, который задавали при установке PostgreSQL)
5. Нажать **Test Connection** — должно показать "Connected"
6. Нажать **Finish**

## Шаг 3: Обзор интерфейса

После подключения слева появится дерево:

```
supply_db
├── Schemas
│   └── public
│       ├── Tables
│       │   ├── suppliers
│       │   ├── materials
│       │   ├── supplier_prices
│       │   ├── purchases
│       │   └── sales_history
│       ├── Views
│       └── ...
```

**Что где:**
- **Tables** — сами таблицы с данными
- **ПКМ на таблице -> View/Edit Data** — посмотреть и редактировать данные
- **ПКМ на таблице -> View Diagram** — увидеть связи между таблицами

## Шаг 4: Визуальный просмотр данных

1. Разверни Tables -> suppliers
2. ПКМ (правая кнопка мыши) по suppliers -> View/Edit Data -> All Rows
3. Откроется таблица, как в Excel
4. Можно редактировать ячейки прямо в DBeaver (изменить, добавить строку)

## Шаг 5: Написание SQL запросов в DBeaver

1. Нажать **SQL Editor** (или ПКМ по БД -> SQL Editor -> New Script)
2. Откроется окно для ввода SQL
3. Напиши запрос:
   ```sql
   SELECT s.name AS supplier, m.name AS material, p.quantity, p.purchase_date
   FROM purchases p
   JOIN suppliers s ON p.supplier_id = s.id
   JOIN materials m ON p.material_id = m.id
   ORDER BY p.purchase_date DESC
   LIMIT 20;
   ```
4. Нажать **Ctrl+Enter** или иконку "Execute" (зелёный треугольник)

## Шаг 6: Экспорт данных в Excel

1. Выполни любой SELECT запрос
2. В результатах (снизу) ПКМ по таблице -> **Export Data**
3. Выбрать формат: **CSV** или **XLSX** (Excel)
4. Выбрать путь сохранения
5. Нажать Finish

Это позволяет выгрузить любой SQL-запрос в Excel одним кликом.

## Шаг 7: Создание ER-диаграммы

1. ПКМ по базе supply_db -> **View Diagram**
2. DBeaver покажет схему: таблицы в виде прямоугольников, связи стрелками
3. Это называется ER-диаграмма (Entity-Relationship)
4. Можно сохранить как картинку (ПКМ -> Save As)

## Шаг 8: Сохранение запросов

1. ПКМ по БД -> SQL Editor -> New Script
2. Напиши запрос
3. Нажми Ctrl+S, сохрани как "ежемесячный_отчёт.sql"
4. Теперь этот запрос можно открыть и выполнить в любое время

## Чек-лист ученика

- [ ] Установлен DBeaver
- [ ] Создано подключение к PostgreSQL supply_db
- [ ] Может открыть таблицу и увидеть данные (View/Edit Data)
- [ ] Написал и выполнил SQL запрос в редакторе
- [ ] Экспортировал данные в Excel
- [ ] Посмотрел ER-диаграмму
- [ ] Сохранил запрос как файл .sql
