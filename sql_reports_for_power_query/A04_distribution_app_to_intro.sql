-- Отчет A04: Распределение разрывов Нанесение -> Ввод в оборот (ВСЕ КОДЫ)
-- ODBC-совместимая версия: без CTE, без OVER(), с подзапросами
-- Категория 'еще не введен' для кодов без introduced_date;
-- категория 'нет нанесения' для кодов без application_date

SELECT
    CASE
        WHEN application_date IS NULL       THEN 'нет нанесения'
        WHEN introduced_date IS NULL        THEN 'есть нанесение, еще не введен'
        WHEN (introduced_date::date - application_date::date) = 0       THEN '0 дн.'
        WHEN (introduced_date::date - application_date::date) = 1       THEN '1 дн.'
        WHEN (introduced_date::date - application_date::date) BETWEEN 2 AND 7    THEN '2-7 дн.'
        WHEN (introduced_date::date - application_date::date) BETWEEN 8 AND 30   THEN '8-30 дн.'
        WHEN (introduced_date::date - application_date::date) BETWEEN 31 AND 90  THEN '31-90 дн.'
        WHEN (introduced_date::date - application_date::date) BETWEEN 91 AND 365 THEN '91-365 дн.'
        WHEN (introduced_date::date - application_date::date) >= 366     THEN '>=366 дн.'
    END AS диапазон,
    COUNT(*) AS количество,
    ROUND(COUNT(*) * 100.0 / (
        SELECT COUNT(*) FROM chz_cises WHERE emission_date IS NOT NULL
    ), 1) AS доля_проц
FROM chz_cises
WHERE emission_date IS NOT NULL
GROUP BY
    CASE
        WHEN application_date IS NULL       THEN -2
        WHEN introduced_date IS NULL        THEN -1
        WHEN (introduced_date::date - application_date::date) = 0       THEN 0
        WHEN (introduced_date::date - application_date::date) = 1       THEN 1
        WHEN (introduced_date::date - application_date::date) BETWEEN 2 AND 7    THEN 2
        WHEN (introduced_date::date - application_date::date) BETWEEN 8 AND 30   THEN 8
        WHEN (introduced_date::date - application_date::date) BETWEEN 31 AND 90  THEN 31
        WHEN (introduced_date::date - application_date::date) BETWEEN 91 AND 365 THEN 91
        WHEN (introduced_date::date - application_date::date) >= 366     THEN 366
    END
ORDER BY
    CASE
        WHEN application_date IS NULL       THEN -2
        WHEN introduced_date IS NULL        THEN -1
        WHEN (introduced_date::date - application_date::date) = 0       THEN 0
        WHEN (introduced_date::date - application_date::date) = 1       THEN 1
        WHEN (introduced_date::date - application_date::date) BETWEEN 2 AND 7    THEN 2
        WHEN (introduced_date::date - application_date::date) BETWEEN 8 AND 30   THEN 8
        WHEN (introduced_date::date - application_date::date) BETWEEN 31 AND 90  THEN 31
        WHEN (introduced_date::date - application_date::date) BETWEEN 91 AND 365 THEN 91
        WHEN (introduced_date::date - application_date::date) >= 366     THEN 366
    END;
