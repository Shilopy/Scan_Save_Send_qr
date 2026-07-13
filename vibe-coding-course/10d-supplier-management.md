# Проект Г: Система управления поставщиками

**Время**: 1 час
**Цель**: создать инструмент для сравнения и выбора поставщиков

---

## Бизнес-контекст

У снабженца есть несколько поставщиков на один и тот же материал.
Нужно сравнивать цены, сроки, рейтинг и выбирать лучшего.
Также нужно уметь быстро найти контакты поставщика.

## Шаг 1: Поиск поставщика

**Промпт для Cline:**
```
В проекте supply_manager создай файл suppliers_module.py.

Напиши функцию search_suppliers(search_term):
1. Подключается к БД supply_db
2. Ищет поставщиков, у которых name содержит search_term (ILIKE)
3. Выводит таблицу: ID | Название | Контакт | Телефон | Email | Рейтинг
4. Если ничего не найдено — выводит "Поставщики не найдены"

В main.py добавь вызов search_suppliers("Металл") для демонстрации.
```

## Шаг 2: Сравнение цен поставщиков

**Промпт для Cline:**
```
В suppliers_module.py добавь функцию compare_prices(material_name):
1. Принимает название материала
2. Выполняет запрос с JOIN:
   SELECT sp.price, sp.valid_from, sp.valid_until, s.name AS supplier, s.rating
   FROM supplier_prices sp
   JOIN suppliers s ON sp.supplier_id = s.id
   JOIN materials m ON sp.material_id = m.id
   WHERE m.name ILIKE %s AND (sp.valid_until IS NULL OR sp.valid_until >= CURRENT_DATE)
   ORDER BY sp.price ASC
3. Выводит:
   Поставщик | Цена | Рейтинг поставщика | Цена действительна до
4. Подсвечивает лучшую цену (зелёным цветом или звёздочкой)
```

## Шаг 3: Выбор лучшего поставщика (с весами)

В реальной жизни выбор — не всегда по минимальной цене.
Нужно учитывать: цену, срок поставки, рейтинг, надёжность.

**Промпт для Cline:**
```
В suppliers_module.py добавь функцию best_supplier(material_name, weights=None):
1. Принимает название материала и опциональные веса критериев
2. Веса по умолчанию: {"price": 0.4, "rating": 0.3, "lead_time": 0.3}
3. Для каждого поставщика этого материала вычисляет взвешенную оценку:
   - price_score = (min_price / supplier_price) * 100 (чем ниже цена, тем выше балл)
   - rating_score = supplier_rating * 20 (макс. 100)
   - lead_time_score находится из таблицы materials
   - total_score = price_score * weight_price + rating_score * weight_rating + lead_time_score * weight_lead_time
4. Выводит рейтинг поставщиков по убыванию total_score
5. Рекомендует поставщика с максимальным баллом
```

## Шаг 4: История закупок по поставщику

**Промпт для Cline:**
```
В suppliers_module.py добавь функцию supplier_history(supplier_name):
1. Принимает название поставщика
2. Выполняет запрос:
   SELECT p.purchase_date, m.name AS material, p.quantity, p.total_cost, p.status
   FROM purchases p
   JOIN suppliers s ON p.supplier_id = s.id
   JOIN materials m ON p.material_id = m.id
   WHERE s.name ILIKE %s
   ORDER BY p.purchase_date DESC
3. Выводит таблицу с историей закупок
4. Считает и выводит итоги:
   - Всего закупок: N
   - Общая сумма: XXX
   - Средняя сумма закупки: XXX
```

## Шаг 5: Дашборд поставщиков

**Промпт для Cline:**
```
В suppliers_module.py добавь функцию supplier_dashboard():
1. Выполняет запрос с агрегацией:
   SELECT s.name, COUNT(p.id) as purchases_count, 
          SUM(p.total_cost) as total_spent, 
          AVG(p.total_cost) as avg_purchase,
          MAX(p.purchase_date) as last_purchase,
          s.rating
   FROM suppliers s
   LEFT JOIN purchases p ON s.id = p.supplier_id
   GROUP BY s.id
   ORDER BY total_spent DESC NULLS LAST
2. Выводит дашборд:
   Поставщик | Закупок | Потрачено всего | Средний чек | Последняя закупка | Рейтинг
3. В конце выводит итоги: всего поставщиков, общая сумма закупок
```

## Чек-лист ученика

- [ ] Реализован поиск поставщиков
- [ ] Реализовано сравнение цен на материал
- [ ] Реализован алгоритм выбора лучшего поставщика
- [ ] Реализована история закупок по поставщику
- [ ] Реализован дашборд поставщиков
- [ ] Понимает как работают весовые коэффициенты при выборе
