# Модуль 9: Python + SQL — соединяем код и базу данных

**Время**: 2 часа
**Цель**: научиться подключаться к PostgreSQL из Python и выполнять запросы

---

## Шаг 1: Установка библиотеки psycopg2

Библиотека `psycopg2` позволяет Python общаться с PostgreSQL.

**В CMD (с активным venv):**
```
pip install psycopg2-binary pandas
```

**Что установили:**
- `psycopg2-binary` — для подключения к PostgreSQL
- `pandas` — для работы с таблицами в Python

## Шаг 2: Подключение к базе

**Промпт для Cline:**
```
В файле utils.py проекта supply_manager напиши функцию connect_db(), которая:
1. Подключается к PostgreSQL базе supply_db
2. Параметры подключения: host=localhost, port=5432, user=postgres, password=твой_пароль, dbname=supply_db
3. Возвращает объект подключения (connection)
4. Если подключение не удалось — выводит ошибку и возвращает None
```

**Важно:** Пароль от PostgreSQL пока можно вписать прямо в код (мы вынесем его позже).

## Шаг 3: Первый запрос из Python

**Промпт для Cline:**
```
В файле main.py проекта supply_manager:
1. Импортируй функцию connect_db из utils
2. Напиши функцию get_all_suppliers(), которая:
   - Подключается к БД
   - Выполняет SELECT id, name, rating FROM suppliers
   - Выводит таблицу в консоль
3. В main() вызови get_all_suppliers()
4. Закрывай соединение после работы
```

**Запусти:** `python main.py`

## Шаг 4: Запрос с параметрами

**Промпт для Cline:**
```
В файл utils.py проекта supply_manager добавь функцию get_purchases_by_supplier(supplier_name), которая:
1. Принимает название поставщика (например "ООО МеталлСнаб")
2. Выполняет SQL запрос с JOIN:
   SELECT p.purchase_date, m.name AS material, p.quantity, p.total_cost
   FROM purchases p
   JOIN suppliers s ON p.supplier_id = s.id
   JOIN materials m ON p.material_id = m.id
   WHERE s.name = %s
3. Возвращает список строк-результатов
4. Используй правильную подстановку параметров (%s), НЕ конкатенацию строк
```

## Шаг 5: Сохранение результатов в CSV/Excel

**Промпт для Cline:**
```
В файл main.py проекта supply_manager добавь функцию export_purchases_to_csv():
1. Выполняет SELECT с JOIN для получения всех закупок
2. Использует pandas для сохранения результата:
   - Сохраняет в файл purchases_report.csv (через pandas to_csv)
   - Сохраняет в файл purchases_report.xlsx (через pandas to_excel, нужен openpyxl)
3. Выводит "Отчёт сохранён: purchases_report.xlsx"
4. Добавь openpyxl в requirements.txt

Также добавь вызов export_purchases_to_csv() в main().
```

Установи openpyxl: `pip install openpyxl`

**Запусти:** `python main.py`
Открой `purchases_report.xlsx` в Excel.

## Шаг 6: Загрузка данных из Excel в БД

Практическая задача: у снабженца есть прайс-лист от поставщика в Excel, нужно загрузить его в базу.

**Промпт для Cline:**
```
В файл utils.py проекта supply_manager добавь функцию import_prices_from_excel(file_path):
1. Принимает путь к Excel-файлу
2. Загружает его через pandas.read_excel()
3. Ожидает колонки: supplier_id, material_id, price, valid_from, valid_until
4. Вставляет данные в таблицу supplier_prices
5. Использует executemany для массовой вставки
6. Выводит сколько строк добавлено
7. Обрабатывает ошибки (если файл не найден, если не те колонки)
```

## Шаг 7: Выносим пароль в .env

Хранить пароль в коде — плохая практика. Используем .env файл.

**Промпт для Cline:**
```
В проекте supply_manager:
1. Установи python-dotenv (добавь в requirements.txt)
2. Создай файл .env:
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=supply_db
   DB_USER=postgres
   DB_PASSWORD=твой_пароль
3. В config.py загрузи эти переменные через load_dotenv()
4. Обнови connect_db() в utils.py: читай настройки из config, а не хардкод
5. Добавь .env в .gitignore

Используй os.getenv("DB_HOST") для чтения.
```

## Шаг 8: Переносим SQL-запросы в отдельный файл

**Промпт для Cline:**
```
Создай файл queries.py в проекте supply_manager.
Перенеси туда все SQL-запросы как строки в функции:
1. get_all_suppliers_query() -> "SELECT * FROM suppliers ORDER BY name"
2. get_purchases_by_supplier_query() -> "SELECT ... WHERE s.name = %s"
3. get_top_materials_query() -> "SELECT m.name, SUM(p.total_cost) as total FROM ... GROUP BY ... ORDER BY total DESC"
4. get_monthly_spending_query() -> "SELECT ... GROUP BY month"

В utils.py импортируй и используй эти функции.
```

## Чек-лист ученика

- [ ] Установлены psycopg2-binary, pandas, openpyxl
- [ ] Написал функцию connect_db()
- [ ] Выполнил SELECT из Python
- [ ] Сделал запрос с параметрами (WHERE name = %s)
- [ ] Сохранил результат в Excel
- [ ] Загрузил данные из Excel в БД
- [ ] Вынес пароль в .env файл
- [ ] SQL-запросы вынесены в отдельный файл queries.py
