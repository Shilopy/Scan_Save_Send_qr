-- Новый запрос: агрегация заказов без детализации по артикулам
-- Использует FOR XML PATH для отображения ВСЕХ дат платежа (STRING_AGG не подошел)

WITH OrderAgg AS (
    SELECT
        [Document date],
        [Purchasing document],
        [Supplier No],
        [Supplier],
        SUM(ISNULL([Still to be delivered], 0)) AS [Still to be delivered],
        SUM(ISNULL([Order amount RUB], 0)) AS [Order amount RUB],
        SUM(ISNULL([Order VAT RUB], 0)) AS [Order VAT RUB],
        SUM(ISNULL([Order amount], 0) + ISNULL([Order VAT], 0)) AS [Order amount inc VAT]
    FROM
        ASH_ERP_PurchaseOrders_vw
    GROUP BY
        [Document date], [Purchasing document], [Supplier No], [Supplier]
),
Payments AS (
    SELECT
        [Purchasing date], 
        [Purchasing document], 
        SUM([Amount inc VAT]) AS [Amount inc VAT],
        SUM([Amount inc VAT RUB]) AS [Amount inc VAT RUB]
    FROM
        ERP_PurchaseOrders_payment_vw
    WHERE
        [Posted] = 1
    GROUP BY 
        [Purchasing date], [Purchasing document]
)
SELECT
    oa.[Purchasing document]                    AS [Номер заказа],
    CONVERT(VARCHAR, oa.[Document date], 104)   AS [Дата создания заказа],
    oa.[Still to be delivered]                  AS [Осталось поставить],
    ISNULL(
        STUFF((
            SELECT CHAR(10) + CONVERT(VARCHAR, pp.[Payment date], 104)
            FROM ERP_PurchaseOrders_payment_vw pp
            WHERE pp.[Purchasing document] = oa.[Purchasing document]
              AND pp.[Purchasing date] = oa.[Document date]
              AND pp.[Posted] = 1
            ORDER BY pp.[Payment date]
            FOR XML PATH(''), TYPE
        ).value('.', 'NVARCHAR(MAX)'), 1, 1, ''),
        N''
    ) AS [Даты платежа],
    ISNULL(p.[Amount inc VAT RUB], 0)           AS [Оплачено в RUB],
    (oa.[Order amount RUB] + oa.[Order VAT RUB])
        - ISNULL(p.[Amount inc VAT RUB], 0)     AS [To be paid inc VAT RUB]
FROM
    OrderAgg oa
LEFT JOIN
    Payments p
    ON  oa.[Purchasing document] = p.[Purchasing document]
    AND oa.[Document date] = p.[Purchasing date]
WHERE
    YEAR(oa.[Document date]) IN (2024, 2025, 2026)
    AND (
        oa.[Still to be delivered] > 0
        OR EXISTS (
            SELECT 1
            FROM ASH_ERP_PurchaseOrders_vw po2
            WHERE po2.[Purchasing document] = oa.[Purchasing document]
            AND po2.[Document date] = oa.[Document date]
            AND po2.[Order delivered] IS NOT NULL
            AND po2.[Order delivered] < po2.[Order quantity]
        )
    )
ORDER BY
    oa.[Document date],
    oa.[Purchasing document];
