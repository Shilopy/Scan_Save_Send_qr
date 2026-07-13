-- Отчет A07: Статистика по неделям ввода в оборот
WITH weeks AS (
    SELECT
        date_trunc('week', introduced_date::date) AS week_start,
        (introduced_date::date - emission_date::date)   AS em_to_intro,
        (introduced_date::date - application_date::date) AS app_to_intro
    FROM chz_cises
    WHERE introduced_date IS NOT NULL
      AND emission_date IS NOT NULL
      AND application_date IS NOT NULL
      AND (introduced_date::date - emission_date::date) >= 0
      AND (introduced_date::date - application_date::date) >= 0
)
SELECT
    week_start::date AS неделя_пн,
    COUNT(*)         AS всего,
    ROUND(AVG(em_to_intro), 1)  AS ср_разрыв_э_в_дн,
    ROUND(AVG(app_to_intro), 1) AS ср_разрыв_н_в_дн,
    COUNT(*) FILTER (WHERE app_to_intro = 0) AS н_равно_в,
    COUNT(*) FILTER (WHERE em_to_intro = 0)  AS э_равно_в
FROM weeks
GROUP BY week_start
ORDER BY week_start;
