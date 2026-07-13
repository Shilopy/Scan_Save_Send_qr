-- Отчет A01: Статистика по статусам
-- В Power Query: Свой источник -> Вставить этот SQL
SELECT
    COALESCE(NULLIF(status, ''), '(пусто)') AS status,
    COUNT(*) AS cnt
FROM chz_cises
GROUP BY status
ORDER BY cnt DESC;
