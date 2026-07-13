-- =============================================================
-- ОТЧЕТ: Анализ разрывов между эмиссией, нанесением и вводом в оборот
-- База: chz_cises (PostgreSQL)
-- Использование: вставить в DBeaver и выполнить
-- =============================================================

-- Описание колонок:
-- emission_date  - дата эмиссии кода
-- application_date - дата нанесения
-- introduced_date  - дата ввода в оборот
-- status           - статус: EMITTED, APPLIED, INTRODUCED, WAIT_TRANSFER_TO_OWNER

-- =============================================================
-- 1. ОБЩАЯ СТАТИСТИКА ПО СТАТУСАМ
-- =============================================================
SELECT '[1] ОБЩАЯ СТАТИСТИКА ПО СТАТУСАМ' AS section;

SELECT
    COALESCE(NULLIF(status, ''), '(пусто)') AS status,
    COUNT(*) AS cnt
FROM chz_cises
GROUP BY status
ORDER BY cnt DESC;

-- =============================================================
-- 2. ОБЩАЯ СТАТИСТИКА (сколько строк имеют заполненные даты)
-- =============================================================
SELECT '[2] ОБЩАЯ СТАТИСТИКА (заполненность дат)' AS section;

SELECT
    COUNT(*)                                                          AS всего_строк,
    COUNT(*) FILTER (WHERE emission_date IS NOT NULL)                 AS дата_эмиссии_заполнена,
    COUNT(*) FILTER (WHERE application_date IS NOT NULL)              AS дата_нанесения_заполнена,
    COUNT(*) FILTER (WHERE introduced_date IS NOT NULL)               AS дата_ввода_заполнена
FROM chz_cises;

-- =============================================================
-- 3. СРЕДНИЙ РАЗРЫВ МЕЖДУ ЭТАПАМИ (в днях)
-- =============================================================
SELECT '[3] СРЕДНИЙ РАЗРЫВ МЕЖДУ ЭТАПАМИ (в днях)' AS section;

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
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY emission_to_intro)::numeric(10,1) AS медиана_дн,
    MIN(emission_to_intro)             AS min_дн,
    MAX(emission_to_intro)             AS max_дн
FROM gaps WHERE emission_to_intro >= 0
UNION ALL
SELECT
    'Эмиссия -> Нанесение'             AS этап,
    COUNT(*)                           AS кол_во,
    ROUND(AVG(emission_to_app), 1)     AS среднее_дн,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY emission_to_app)::numeric(10,1) AS медиана_дн,
    MIN(emission_to_app)               AS min_дн,
    MAX(emission_to_app)               AS max_дн
FROM gaps WHERE emission_to_app >= 0
UNION ALL
SELECT
    'Нанесение -> Ввод в оборот'       AS этап,
    COUNT(*)                           AS кол_во,
    ROUND(AVG(app_to_intro), 1)        AS среднее_дн,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY app_to_intro)::numeric(10,1) AS медиана_дн,
    MIN(app_to_intro)                  AS min_дн,
    MAX(app_to_intro)                  AS max_дн
FROM gaps WHERE app_to_intro >= 0;

-- =============================================================
-- 4. РАСПРЕДЕЛЕНИЕ РАЗРЫВОВ: ЭМИССИЯ -> ВВОД В ОБОРОТ (ВСЕ КОДЫ)
-- =============================================================
SELECT '[4.1] РАСПРЕДЕЛЕНИЕ: Эмиссия -> Ввод в оборот (все коды)' AS section;

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

-- =============================================================
-- 4. РАСПРЕДЕЛЕНИЕ РАЗРЫВОВ: НАНЕСЕНИЕ -> ВВОД В ОБОРОТ (ВСЕ КОДЫ)
-- =============================================================
SELECT '[4.2] РАСПРЕДЕЛЕНИЕ: Нанесение -> Ввод в оборот (все коды)' AS section;

WITH gaps AS (
    SELECT
        CASE
            WHEN application_date IS NULL THEN -2
            WHEN introduced_date IS NULL THEN -1
            ELSE (introduced_date::date - application_date::date)
        END AS days_diff
    FROM chz_cises
    WHERE emission_date IS NOT NULL
)
SELECT
    CASE
        WHEN days_diff = -2              THEN 'нет нанесения'
        WHEN days_diff = -1              THEN 'есть нанесение, еще не введен'
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
GROUP BY
    CASE
        WHEN days_diff = -2              THEN -2
        WHEN days_diff = -1              THEN -1
        WHEN days_diff = 0               THEN 0
        WHEN days_diff = 1               THEN 1
        WHEN days_diff BETWEEN 2 AND 7   THEN 2
        WHEN days_diff BETWEEN 8 AND 30  THEN 8
        WHEN days_diff BETWEEN 31 AND 90 THEN 31
        WHEN days_diff BETWEEN 91 AND 365 THEN 91
        WHEN days_diff >= 366            THEN 366
    END
ORDER BY MIN(days_diff);

-- =============================================================
-- 5. СОВПАДЕНИЕ ЭТАПОВ В ОДИН ДЕНЬ
-- =============================================================
SELECT '[5] СОВПАДЕНИЕ ЭТАПОВ В ОДИН ДЕНЬ' AS section;

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

-- =============================================================
-- 6. СТАТИСТИКА ПО НЕДЕЛЯМ (группировка по неделям ввода в оборот)
-- =============================================================
SELECT '[6] СТАТИСТИКА ПО НЕДЕЛЯМ (ввод в оборот)' AS section;

WITH weeks AS (
    SELECT
        date_trunc('week', introduced_date::date) AS week_start,
        COUNT(*)                                                           AS всего,
        ROUND(AVG((introduced_date::date - emission_date::date)::numeric), 1)   AS ср_разрыв_э_в,
        ROUND(AVG((introduced_date::date - application_date::date)::numeric), 1) AS ср_разрыв_н_в,
        COUNT(*) FILTER (WHERE (introduced_date::date - application_date::date) = 0) AS н_равно_в,
        COUNT(*) FILTER (WHERE (introduced_date::date - emission_date::date) = 0)   AS э_равно_в
    FROM chz_cises
    WHERE introduced_date IS NOT NULL
      AND emission_date IS NOT NULL
      AND application_date IS NOT NULL
      AND (introduced_date::date - emission_date::date) >= 0
      AND (introduced_date::date - application_date::date) >= 0
    GROUP BY date_trunc('week', introduced_date::date)
)
SELECT
    week_start::date AS неделя_пн,
    всего,
    ср_разрыв_э_в,
    ср_разрыв_н_в,
    э_равно_в,
    н_равно_в
FROM weeks
ORDER BY week_start;

-- =============================================================
-- 7. ИТОГОВАЯ СВОДКА (типовые сценарии)
-- =============================================================
SELECT '[7] ИТОГОВАЯ СВОДКА - ТИПОВЫЕ СЦЕНАРИИ' AS section;

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
    COUNT(*) AS количество,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS доля_проц
FROM base
GROUP BY сценарий
ORDER BY COUNT(*) DESC;

-- =============================================================
-- 8. АНОМАЛЬНЫЕ ДАТЫ (пиковые значения разрывов)
-- =============================================================
SELECT '[8] АНОМАЛЬНЫЕ ДНИ - МАКСИМАЛЬНЫЕ РАЗРЫВЫ' AS section;

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
