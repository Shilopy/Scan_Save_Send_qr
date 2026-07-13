-- ============================================================
-- ФИНАЛЬНАЯ ВЕРСИЯ
-- Только паллеты с максимальным числом
-- Колонка Qty_in_pal — количество из [Package]
-- СУБД: SQL Server
-- ============================================================

SELECT
    *,
    TRY_CAST(
        REPLACE(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE([Package], ' ', ''),
                        CHAR(160), ''
                    ),
                    N'пал(', ''
                ),
                N'шт)', ''
            ),
            ')', ''
        ) AS INT
    ) AS Qty_in_pal
FROM (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY [Material No]
            ORDER BY TRY_CAST(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                REPLACE([Package], ' ', ''),
                                CHAR(160), ''
                            ),
                            N'пал(', ''
                        ),
                        N'шт)', ''
                    ),
                    ')', ''
                ) AS INT
            ) DESC
        ) AS rn
    FROM ASH_ERP_Material_logistic_data_vw
    WHERE [Package] LIKE N'%пал%'
) t
WHERE rn = 1
ORDER BY [Material No];
