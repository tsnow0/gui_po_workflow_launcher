SELECT
    i.product_id as 'oproduct_id',
    i.product as 'oproduct_sku',
    i.vendor_number,
    i.category,
    DAY(CURDATE()) / DAY(LAST_DAY(months.m)) AS 'month_percent',
    DAY(CURDATE()) AS 'current_date',
    DAY(LAST_DAY(months.m)) AS 'month_date',
    months.m AS 'month'
FROM analytics.bc_us_items i
    LEFT JOIN hq.oproducts p ON i.product_id = p.oproduct_id
    CROSS JOIN
    (
        SELECT
            STR_TO_DATE(CONCAT(d.`year`, '-', d.`month`, '-01'), '%Y-%m-%d') AS m
        FROM
            analytics.adates d
        WHERE
            STR_TO_DATE(CONCAT(d.`year`, '-', d.`month`, '-01'), '%Y-%m-%d') >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
            AND STR_TO_DATE(CONCAT(d.`year`, '-', d.`month`, '-01'), '%Y-%m-%d') <= DATE_FORMAT(CURDATE() + INTERVAL 12 MONTH, '%Y-%m-01')
        GROUP BY
            m
        ORDER BY
            m
    ) AS months
WHERE
    i.go_forward_flag = 1
    AND i.product NOT LIKE 'MENE%' # Remove Menards DI products
ORDER BY
    i.product_id,
    months.m;