-- Отчет A09: Аномальные дни - максимальные разрывы
SELECT
    introduced_date::date AS дата_ввода,
    COUNT(*)              AS всего_кодов,
    ROUND(AVG((introduced_date::date - emission_date::date)::numeric), 1)   AS ср_разрыв_э_в,
    ROUND(AVG((introduced_date::date - application_date::date)::numeric), 1) AS ср_разрыв_н_в,
    MAX((introduced_date::date - application_date::date))                   AS макс_разрыв_н_в
FROM chz_cises
WHERE introduced_date IS NOT NULL
  AND emission_date IS NOT NULL
  AND application_date IS NOT NULL
  AND (introduced_date::date - emission_date::date) >= 0
  AND (introduced_date::date - application_date::date) >= 0
GROUP BY introduced_date::date
HAVING AVG((introduced_date::date - application_date::date)) > 90
    OR AVG((introduced_date::date - emission_date::date)) > 100
ORDER BY ср_разрыв_э_в DESC;
