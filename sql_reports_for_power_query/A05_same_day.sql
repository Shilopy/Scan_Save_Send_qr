-- Отчет A06: Совпадение этапов в один день
WITH base AS (
    SELECT
        (introduced_date::date = emission_date::date)       AS em_eq_intro,
        (introduced_date::date = application_date::date)    AS app_eq_intro,
        (emission_date::date = application_date::date
         AND application_date::date = introduced_date::date) AS all_three
    FROM chz_cises
    WHERE introduced_date IS NOT NULL
      AND emission_date IS NOT NULL
      AND application_date IS NOT NULL
)
SELECT
    'Эмиссия == Ввод в оборот'           AS ситуация,
    COUNT(*) FILTER (WHERE em_eq_intro)  AS количество
FROM base
UNION ALL
SELECT
    'Нанесение == Ввод в оборот'         AS ситуация,
    COUNT(*) FILTER (WHERE app_eq_intro) AS количество
FROM base
UNION ALL
SELECT
    'Все три этапа в один день'          AS ситуация,
    COUNT(*) FILTER (WHERE all_three)    AS количество
FROM base;
