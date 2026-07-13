-- =============================================================
-- ОТЧЕТ: Анализ разрывов для кодов, эмитированных в заданном периоде
-- База: chz_cises (PostgreSQL)
--
-- ИСПОЛЬЗОВАНИЕ:
--   1. Замените даты '2026-01-01' и '2026-06-30' на нужные вам
--   2. Вставьте весь скрипт в DBeaver, Power Query или PgAdmin и выполните
--
-- ОСОБЕННОСТЬ:
--   Фильтр ТОЛЬКО по emission_date. В статистику попадают
--   только те коды, которые были эмитированы в указанном
--   диапазоне. Коды, эмитированные раньше — исключены.
-- =============================================================

-- >>> УКАЖИТЕ ПЕРИОД ЭМИССИИ <<<
-- Замените '2026-01-01' (ниже) на дату начала периода
-- Замените '2026-06-30' (ниже) на дату конца периода
-- Формат: 'YYYY-MM-DD'

-- =============================================================
-- 0. ПАРАМЕТРЫ
-- =============================================================
SELECT '[0] ПАРАМЕТРЫ ОТЧЕТА' AS section;

SELECT
    '2026-01-01'::text AS период_эмиссии_с,
    '2026-06-30'::text AS период_эмиссии_по;

-- =============================================================
-- 1. СТАТУСЫ КОДОВ, ЭМИТИРОВАННЫХ В ПЕРИОД
-- =============================================================
SELECT '[1] СТАТУСЫ КОДОВ, ЭМИТИРОВАННЫХ В ПЕРИОД' AS section;

SELECT
    COALESCE(NULLIF(status, ''), '(пусто)') AS status,
    COUNT(*) AS cnt
FROM chz_cises
WHERE emission_date::date BETWEEN '2026-01-01'::date AND '2026-06-30'::date
GROUP BY status
ORDER BY cnt DESC;

-- =============================================================
-- 2. ОБЩАЯ СТАТИСТИКА (заполненность дат за период)
-- =============================================================
SELECT '[2] ОБЩАЯ СТАТИСТИКА (заполненность дат)' AS section;

SELECT
    COUNT(*)                                                          AS всего_строк_в_периоде,
    COUNT(*) FILTER (WHERE emission_date IS NOT NULL)                 AS дата_эмиссии_заполнена,
    COUNT(*) FILTER (WHERE application_date IS NOT NULL)              AS дата_нанесения_заполнена,
    COUNT(*) FILTER (WHERE introduced_date IS NOT NULL)               AS дата_ввода_заполнена
FROM chz_cises
WHERE emission_date::date BETWEEN '2026-01-01'::date AND '2026-06-30'::date;

-- =============================================================
-- 3. СРЕДНИЙ РАЗРЫВ МЕЖДУ ЭТАПАМИ (в днях)
-- =============================================================
SELECT '[3] СРЕДНИЙ РАЗРЫВ МЕЖДУ ЭТАПАМИ (в днях)' AS section;

WITH filtered AS (
    SELECT *
    FROM chz_cises
    WHERE emission_date::date BETWEEN '2026-01-01'::date AND '2026-06-30'::date
),
gaps AS (
    SELECT
        (introduced_date::date - emission_date::date)      AS emission_to_intro,
        (introduced_date::date - application_date::date)    AS app_to_intro,
        (application_date::date - emission_date::date)      AS emission_to_app
    FROM filtered
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
-- 4. РАСПРЕДЕЛЕНИЕ РАЗРЫВОВ (ВСЕ КОДЫ)
-- =============================================================
SELECT '[4.1] РАСПРЕДЕЛЕНИЕ: Эмиссия -> Ввод в оборот (все коды)' AS section;

WITH filtered AS (
    SELECT
        CASE
            WHEN introduced_date IS NULL THEN NULL
            ELSE (introduced_date::date - emission_date::date)
        END AS days_diff
    FROM chz_cises
    WHERE emission_date::date BETWEEN '2026-01-01'::date AND '2026-06-30'::date
      AND emission_date IS NOT NULL
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
FROM filtered
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

SELECT '[4.2] РАСПРЕДЕЛЕНИЕ: Нанесение -> Ввод в оборот (все коды)' AS section;

WITH filtered AS (
    SELECT
        CASE
            WHEN application_date IS NULL THEN -2
            WHEN introduced_date IS NULL THEN -1
            ELSE (introduced_date::date - application_date::date)
        END AS days_diff
    FROM chz_cises
    WHERE emission_date::date BETWEEN '2026-01-01'::date AND '2026-06-30'::date
      AND emission_date IS NOT NULL
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
FROM filtered
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

WITH filtered AS (
    SELECT *
    FROM chz_cises
    WHERE emission_date::date BETWEEN '2026-01-01'::date AND '2026-06-30'::date
),
base AS (
    SELECT
        (introduced_date::date = emission_date::date)       AS em_eq_intro,
        (introduced_date::date = application_date::date)    AS app_eq_intro,
        (emission_date::date = application_date::date
         AND application_date::date = introduced_date::date) AS all_three
    FROM filtered
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
-- 6. СТАТИСТИКА ПО НЕДЕЛЯМ ЭМИССИИ
-- =============================================================
SELECT '[6] СТАТИСТИКА ПО НЕДЕЛЯМ ЭМИССИИ' AS section;

WITH filtered AS (
    SELECT *
    FROM chz_cises
    WHERE emission_date::date BETWEEN '2026-01-01'::date AND '2026-06-30'::date
),
weeks AS (
    SELECT
        date_trunc('week', emission_date::date) AS week_emission,
        COUNT(*)                                                           AS всего_эмитировано,
        COUNT(*) FILTER (WHERE introduced_date IS NOT NULL)                AS введено_в_оборот,
        ROUND(AVG(
            CASE WHEN introduced_date IS NOT NULL AND emission_date IS NOT NULL
                 THEN (introduced_date::date - emission_date::date)::numeric
                 ELSE NULL
            END
        ), 1) AS ср_разрыв_э_в_дн,
        ROUND(AVG(
            CASE WHEN introduced_date IS NOT NULL AND application_date IS NOT NULL
                 THEN (introduced_date::date - application_date::date)::numeric
                 ELSE NULL
            END
        ), 1) AS ср_разрыв_н_в_дн
    FROM filtered
    GROUP BY date_trunc('week', emission_date::date)
)
SELECT
    week_emission::date AS неделя_эмиссии,
    всего_эмитировано,
    введено_в_оборот,
    ROUND(введено_в_оборот * 100.0 / NULLIF(всего_эмитировано, 0), 1) AS процент_введенных,
    ср_разрыв_э_в_дн,
    ср_разрыв_н_в_дн
FROM weeks
ORDER BY week_emission;

-- =============================================================
-- 7. СТАТИСТИКА ПО ДНЯМ ЭМИССИИ (топ-20 по количеству)
-- =============================================================
SELECT '[7] ТОП-20 ДНЕЙ ЭМИССИИ ПО КОЛИЧЕСТВУ КОДОВ' AS section;

WITH filtered AS (
    SELECT *
    FROM chz_cises
    WHERE emission_date::date BETWEEN '2026-01-01'::date AND '2026-06-30'::date
)
SELECT
    emission_date::date AS дата_эмиссии,
    COUNT(*)            AS эмитировано,
    COUNT(*) FILTER (WHERE introduced_date IS NOT NULL) AS введено_в_оборот,
    ROUND(AVG(
        CASE WHEN introduced_date IS NOT NULL AND emission_date IS NOT NULL
             THEN (introduced_date::date - emission_date::date)::numeric
             ELSE NULL
        END
    ), 1) AS ср_разрыв_э_в_дн
FROM filtered
GROUP BY emission_date::date
ORDER BY COUNT(*) DESC
LIMIT 20;

-- =============================================================
-- 8. ИТОГОВАЯ СВОДКА (типовые сценарии)
-- =============================================================
SELECT '[8] ИТОГОВАЯ СВОДКА - ТИПОВЫЕ СЦЕНАРИИ' AS section;

WITH filtered AS (
    SELECT *
    FROM chz_cises
    WHERE emission_date::date BETWEEN '2026-01-01'::date AND '2026-06-30'::date
),
base AS (
    SELECT
        (introduced_date::date - application_date::date) AS app_to_intro,
        (introduced_date::date - emission_date::date)   AS em_to_intro
    FROM filtered
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
-- 9. СТАТИСТИКА ПО ТИПУ ЭМИССИИ (emission_type)
-- =============================================================
SELECT '[9] СТАТИСТИКА ПО ТИПУ ЭМИССИИ' AS section;

SELECT
    COALESCE(NULLIF(emission_type::text, ''), '(пусто)') AS тип_эмиссии,
    COUNT(*)                                             AS всего_кодов,
    COUNT(*) FILTER (WHERE introduced_date IS NOT NULL)  AS введено_в_оборот,
    ROUND(AVG(
        CASE WHEN introduced_date IS NOT NULL AND emission_date IS NOT NULL
             THEN (introduced_date::date - emission_date::date)::numeric
             ELSE NULL
        END
    ), 1) AS ср_разрыв_э_в_дн
FROM chz_cises
WHERE emission_date::date BETWEEN '2026-01-01'::date AND '2026-06-30'::date
GROUP BY emission_type
ORDER BY COUNT(*) DESC;

-- =============================================================
-- 10. СТАТИСТИКА ПО ТИПУ УПАКОВКИ (package_type)
-- =============================================================
SELECT '[10] СТАТИСТИКА ПО ТИПУ УПАКОВКИ' AS section;

SELECT
    COALESCE(NULLIF(package_type::text, ''), '(пусто)') AS тип_упаковки,
    COUNT(*)                                            AS всего_кодов,
    COUNT(*) FILTER (WHERE introduced_date IS NOT NULL) AS введено_в_оборот,
    ROUND(AVG(
        CASE WHEN introduced_date IS NOT NULL AND emission_date IS NOT NULL
             THEN (introduced_date::date - emission_date::date)::numeric
             ELSE NULL
        END
    ), 1) AS ср_разрыв_э_в_дн
FROM chz_cises
WHERE emission_date::date BETWEEN '2026-01-01'::date AND '2026-06-30'::date
GROUP BY package_type
ORDER BY COUNT(*) DESC;

-- =============================================================
-- 11. СТАТИСТИКА ПО ГРУППОВЫМ УПАКОВКАМ (general_package_type)
--     0 = не групповая, 1 = групповая упаковка
-- =============================================================
SELECT '[11] СТАТИСТИКА ПО ТИПУ ОБЩЕЙ УПАКОВКИ (general_package_type)' AS section;

SELECT
    CASE
        WHEN general_package_type = 0 THEN '0 - не групповая'
        WHEN general_package_type = 1 THEN '1 - групповая упаковка'
        ELSE COALESCE(general_package_type::text, '(пусто)')
    END AS тип_общей_упаковки,
    COUNT(*)                                            AS всего_кодов,
    COUNT(*) FILTER (WHERE introduced_date IS NOT NULL) AS введено_в_оборот,
    ROUND(AVG(
        CASE WHEN introduced_date IS NOT NULL AND emission_date IS NOT NULL
             THEN (introduced_date::date - emission_date::date)::numeric
             ELSE NULL
        END
    ), 1) AS ср_разрыв_э_в_дн
FROM chz_cises
WHERE emission_date::date BETWEEN '2026-01-01'::date AND '2026-06-30'::date
GROUP BY general_package_type
ORDER BY general_package_type;

-- =============================================================
-- 12. СТАТИСТИКА ПО ТИПУ АГРЕГАЦИИ (aggregation_type)
-- =============================================================
SELECT '[12] СТАТИСТИКА ПО ТИПУ АГРЕГАЦИИ' AS section;

SELECT
    COALESCE(NULLIF(aggregation_type::text, ''), '(пусто)') AS тип_агрегации,
    COUNT(*)                                             AS всего_кодов,
    COUNT(*) FILTER (WHERE introduced_date IS NOT NULL)  AS введено_в_оборот,
    ROUND(AVG(
        CASE WHEN introduced_date IS NOT NULL AND emission_date IS NOT NULL
             THEN (introduced_date::date - emission_date::date)::numeric
             ELSE NULL
        END
    ), 1) AS ср_разрыв_э_в_дн
FROM chz_cises
WHERE emission_date::date BETWEEN '2026-01-01'::date AND '2026-06-30'::date
GROUP BY aggregation_type
ORDER BY COUNT(*) DESC;
