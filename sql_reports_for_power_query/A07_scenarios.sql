-- Отчет A08: Типовые сценарии разрывов
WITH base AS (
    SELECT
        (introduced_date::date - application_date::date) AS app_to_intro,
        (introduced_date::date - emission_date::date)   AS em_to_intro
    FROM chz_cises
    WHERE introduced_date IS NOT NULL
      AND emission_date IS NOT NULL
      AND application_date IS NOT NULL
      AND (introduced_date::date - emission_date::date) >= 0
      AND (introduced_date::date - application_date::date) >= 0
)
SELECT
    CASE
        WHEN app_to_intro = 0 AND em_to_intro BETWEEN 8 AND 30   THEN 'Быстрый (Н==В, Э за 8-30 дн.)'
        WHEN app_to_intro = 0                                     THEN 'Быстрый (Н==В)'
        WHEN app_to_intro BETWEEN 1 AND 30                        THEN 'Средний (Н->В 1-30 дн.)'
        WHEN app_to_intro BETWEEN 31 AND 90                       THEN 'Долгий (Н->В 31-90 дн.)'
        WHEN app_to_intro > 90                                    THEN 'Очень долгий (Н->В >90 дн.)'
    END AS сценарий,
    COUNT(*) AS количество
FROM base
GROUP BY сценарий
ORDER BY COUNT(*) DESC;
