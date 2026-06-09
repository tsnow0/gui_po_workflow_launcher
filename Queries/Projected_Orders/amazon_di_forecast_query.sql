SELECT
    cf.oproduct_id,
    CASE WHEN cf.echannel_id IN (27) THEN 'US'
         ELSE 'CA' END AS 'country',
    DATE(cf.ecf_date) AS 'month',
    SUM(cf.ecf_qty * COALESCE(ap.abulk_percentage + ap.adi_percentage, 1)) AS di_demand_quantity
FROM
   analytics.echannel_forecasts cf
   LEFT JOIN analytics.bc_us_items bi ON cf.oproduct_id = bi.product_id
   LEFT JOIN analytics.ainventory_depletions_amazon_percentages ap on cf.oproduct_id = ap.oproduct_id and ap.ochannel_id = cf.echannel_id

WHERE
    bi.go_forward_flag = 1
    AND cf.echannel_id IN (27,31)
    AND cf.ecf_date >=  DATE_FORMAT(NOW() ,'%Y-%m-01')
GROUP BY
    cf.oproduct_id,
    country,
    DATE(cf.ecf_date)
ORDER BY
    cf.oproduct_id,
    country,
    DATE(cf.ecf_date)