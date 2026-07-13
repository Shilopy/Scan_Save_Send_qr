-- Отчет A02: Заполненность дат (сколько строк имеют каждую дату)
SELECT
    COUNT(*)                                                          AS всего_строк,
    COUNT(*) FILTER (WHERE emission_date IS NOT NULL)                 AS дата_эмиссии_заполнена,
    COUNT(*) FILTER (WHERE application_date IS NOT NULL)              AS дата_нанесения_заполнена,
    COUNT(*) FILTER (WHERE introduced_date IS NOT NULL)               AS дата_ввода_заполнена
FROM chz_cises;
