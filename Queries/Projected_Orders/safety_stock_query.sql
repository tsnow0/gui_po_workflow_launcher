SELECT
    ss.oproduct_id,
    -- ROUND(ss.safety_stock) AS safety_stock_quantity
    0 AS safety_stock_quantity
FROM
    analytics.esafety_stock ss