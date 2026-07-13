-- Отчет A03: Средний разрыв между этапами (в днях)
WITH gaps AS (
    SELECT
        (introduced_date::date - emission_date::date)      AS emission_to_intro,
        (introduced_date::date - application_date::date)    AS app_to_intro,
        (application_date::date - emission_date::date)      AS emission_to_app
    FROM chz_cises
    WHERE introduced_date IS NOT NULL
      AND emission_date IS NOT NULL
      AND application_date IS NOT NULL
)
SELECT
    'Эмиссия -> Ввод в оборот'        AS этап,
    COUNT(*)                           AS кол_во,
    ROUND(AVG(emission_to_intro), 1)   AS среднее_дн,
    MIN(emission_to_intro)             AS min_дн,
    MAX(emission_to_intro)             AS max_дн
FROM gaps WHERE emission_to_intro >= 0
UNION ALL
SELECT
    'Эмиссия -> Нанесение'             AS этап,
    COUNT(*)                           AS кол_во,
    ROUND(AVG(emission_to_app), 1)     AS среднее_дн,
    MIN(emission_to_app)               AS min_дн,
    MAX(emission_to_app)               AS max_дн
FROM gaps WHERE emission_to_app >= 0
UNION ALL
SELECT
    'Нанесение -> Ввод в оборот'       AS этап,
    COUNT(*)                           AS кол_во,
    ROUND(AVG(app_to_intro), 1)        AS среднее_дн,
    MIN(app_to_intro)                  AS min_дн,
    MAX(app_to_intro)                  AS max_дн
FROM gaps WHERE app_to_intro >= 0;
