# Модуль 12: Профессиональный уровень

**Время**: 2 часа
**Цель**: поднять качество кода до продакшн-уровня

---

## Шаг 1: Type Hints (подсказки типов)

Type hints делают код понятнее и помогают ловить ошибки.

**Промпт для Cline:**
```
Добавь type hints во все функции проекта supply_manager.
Пример:
def connect_db() -> Optional[connection]:
def search_suppliers(search_term: str) -> list[dict]:
def calculate_requirements(products: dict, production_plan: dict, inventory: dict) -> dict:

Установи mypy и проверь типы:
pip install mypy
mypy .
```

## Шаг 2: Тесты с pytest

**Промпт для Cline:**
```
В проекте supply_manager создай папку tests/ и файл test_mrp.py.

Напиши тесты для mrp.py:
1. test_calculate_requirements_basic():
   - Создай тестовые данные (products, plan, inventory)
   - Вызови calculate_requirements()
   - Проверь что результат — словарь
   - Проверь что для материала с достаточным запасом to_order = 0

2. test_calculate_requirements_zero_inventory():
   - inventory = {1: 0}
   - Проверь что to_order > 0

3. test_calculate_requirements_negative_inventory():
   - Проверь что если на складе больше чем нужно, заказ = 0

Установи pytest:
pip install pytest
Запусти: pytest tests/ -v
```

## Шаг 3: Логирование вместо print

**Промпт для Cline:**
```
Замени все print() в проекте supply_manager на logging.

1. В config.py добавь настройку логгера:
   import logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('supply_manager.log'),
           logging.StreamHandler()
       ]
   )
   logger = logging.getLogger(__name__)

2. Замени print() на logger.info(), logger.warning(), logger.error()

3. Уровни логирования:
   - logger.info() — обычная информация
   - logger.warning() — что-то пошло не так, но не критично
   - logger.error() — ошибка
   - logger.debug() — детали для отладки
```

## Шаг 4: Docker-контейнеризация

**Промпт для Cline:**
```
Создай Dockerfile в корне проекта supply_manager:
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]

И docker-compose.yml:
version: '3.8'
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: supply_db
      POSTGRES_PASSWORD: your_password
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  app:
    build: .
    depends_on:
      - db
    environment:
      DB_HOST: db

volumes:
  pgdata:
```

**Запуск:** `docker-compose up`

## Шаг 5: CI/CD через GitHub Actions

**Промпт для Cline:**
```
Создай файл .github/workflows/ci.yml в проекте supply_manager:

name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest mypy
      - name: Run tests
        run: pytest tests/ -v
      - name: Type check
        run: mypy src/ || true
```

## Шаг 6: Код-ревью чеклист

Перед тем как считать код готовым, проверь:

- [ ] Нет хардкоженных паролей (используй .env)
- [ ] Все функции имеют type hints
- [ ] Нет дублирования кода
- [ ] Обработаны возможные ошибки (try/except)
- [ ] Есть комментарии к сложным участкам
- [ ] requirements.txt обновлён
- [ ] Есть README с инструкцией по запуску
- [ ] Тесты проходят (pytest)
- [ ] Код закоммичен и запушен в GitHub

## Чек-лист ученика

- [ ] Добавлены type hints во все функции
- [ ] Написаны тесты для mrp.py
- [ ] pytest проходит успешно
- [ ] print() заменены на logging
- [ ] Создан Dockerfile
- [ ] Создан .github/workflows/ci.yml
- [ ] Знает чеклист код-ревью
