-- Отчет A04: Распределение разрывов Эмиссия -> Ввод в оборот (ВСЕ КОДЫ)
-- Категория 'еще не введен' для кодов без introduced_date
WITH gaps AS (
    SELECT
        CASE
            WHEN introduced_date IS NULL THEN NULL
            ELSE (introduced_date::date - emission_date::date)
        END AS days_diff
    FROM chz_cises
    WHERE emission_date IS NOT NULL
)
SELECT
    CASE
        WHEN days_diff IS NULL           THEN 'еще не введен'
        WHEN days_diff = 0               THEN '0 дн.'
        WHEN days_diff = 1               THEN '1 дн.'
        WHEN days_diff BETWEEN 2 AND 7   THEN '2-7 дн.'
        WHEN days_diff BETWEEN 8 AND 30  THEN '8-30 дн.'
        WHEN days_diff BETWEEN 31 AND 90 THEN '31-90 дн.'
        WHEN days_diff BETWEEN 91 AND 365 THEN '91-365 дн.'
        WHEN days_diff >= 366            THEN '>=366 дн.'
    END AS диапазон,
    COUNT(*) AS количество,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS доля_проц
FROM gaps
WHERE days_diff IS NULL OR days_diff >= 0
GROUP BY
    CASE
        WHEN days_diff IS NULL           THEN -1
        WHEN days_diff = 0               THEN 0
        WHEN days_diff = 1               THEN 1
        WHEN days_diff BETWEEN 2 AND 7   THEN 2
        WHEN days_diff BETWEEN 8 AND 30  THEN 8
        WHEN days_diff BETWEEN 31 AND 90 THEN 31
        WHEN days_diff BETWEEN 91 AND 365 THEN 91
        WHEN days_diff >= 366            THEN 366
    END
ORDER BY MIN(
    CASE WHEN days_diff IS NULL THEN -1 ELSE days_diff END
);
