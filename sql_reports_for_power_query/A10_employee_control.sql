-- Отчет A10: Ежедневный контроль сотрудника
-- Показывает по дням: сколько эмитировано, нанесено, введено в оборот
-- Каждая операция считается в день её фактического выполнения
-- (эмиссия могла быть раньше, нанесение/ввод считаются сегодня)
-- ODBC-совместимая версия: без CTE, без OVER(), без FILTER(WHERE)

-- =============================================================
-- 1. СВОДКА ЗА СЕГОДНЯ
-- =============================================================
SELECT
    CURRENT_DATE::date AS дата,
    COUNT(CASE WHEN emission_date::date = CURRENT_DATE THEN 1 END)     AS эмитировано_сегодня,
    COUNT(CASE WHEN application_date::date = CURRENT_DATE THEN 1 END)  AS нанесено_сегодня,
    COUNT(CASE WHEN introduced_date::date = CURRENT_DATE THEN 1 END)   AS введено_сегодня,
    ROUND(AVG(
        CASE WHEN application_date::date = CURRENT_DATE
             THEN (application_date::date - emission_date::date)::numeric
             ELSE NULL END
    ), 1) AS ср_дней_от_эмиссии_до_нанесения,
    ROUND(AVG(
        CASE WHEN introduced_date::date = CURRENT_DATE
             THEN (introduced_date::date - application_date::date)::numeric
             ELSE NULL END
    ), 1) AS ср_дней_от_нанесения_до_ввода
FROM chz_cises
WHERE emission_date IS NOT NULL
   OR application_date IS NOT NULL
   OR introduced_date IS NOT NULL;

-- =============================================================
-- 2. ДИНАМИКА ЗА ПОСЛЕДНИЕ 60 ДНЕЙ (основной отчёт)
-- =============================================================
SELECT
    d.дата,
    COALESCE(e.cnt, 0)  AS эмитировано,
    COALESCE(a.cnt, 0)  AS нанесено,
    COALESCE(i.cnt, 0)  AS введено,
    ROUND((SELECT AVG((application_date::date - emission_date::date)::numeric)
           FROM chz_cises
           WHERE application_date::date = d.дата
             AND emission_date IS NOT NULL
             AND (application_date::date - emission_date::date) >= 0), 1) AS ср_дней_э_н,
    ROUND((SELECT AVG((introduced_date::date - application_date::date)::numeric)
           FROM chz_cises
           WHERE introduced_date::date = d.дата
             AND application_date IS NOT NULL
             AND (introduced_date::date - application_date::date) >= 0), 1) AS ср_дней_н_в
FROM generate_series(CURRENT_DATE - 60, CURRENT_DATE, '1 day') d(дата)
LEFT JOIN (
    SELECT emission_date::date AS дата, COUNT(*) AS cnt
    FROM chz_cises WHERE emission_date IS NOT NULL
    GROUP BY emission_date::date
) e ON e.дата = d.дата
LEFT JOIN (
    SELECT application_date::date AS дата, COUNT(*) AS cnt
    FROM chz_cises WHERE application_date IS NOT NULL
    GROUP BY application_date::date
) a ON a.дата = d.дата
LEFT JOIN (
    SELECT introduced_date::date AS дата, COUNT(*) AS cnt
    FROM chz_cises WHERE introduced_date IS NOT NULL
    GROUP BY introduced_date::date
) i ON i.дата = d.дата
ORDER BY d.дата DESC;

-- =============================================================
-- 3. АНОМАЛИИ: что пошло не так (проблемные коды)
-- =============================================================
-- Коды, эмитированные >7 дней назад, но не нанесённые
SELECT 'Коды без нанесения >7 дней' AS проблема,
       COUNT(*) AS количество
FROM chz_cises
WHERE emission_date IS NOT NULL
  AND application_date IS NULL
  AND emission_date::date < CURRENT_DATE - 7;

-- Коды, нанесённые >14 дней назад, но не введённые
SELECT 'Коды без ввода >14 дней' AS проблема,
       COUNT(*) AS количество
FROM chz_cises
WHERE application_date IS NOT NULL
  AND introduced_date IS NULL
  AND application_date::date < CURRENT_DATE - 14;

-- Коды, которые попали в серую зону сегодня
SELECT 'Ушло в серую зону за сегодня' AS проблема,
       COUNT(*) AS количество
FROM chz_cises
WHERE gray_zone = TRUE
  AND emission_date::date = CURRENT_DATE;
