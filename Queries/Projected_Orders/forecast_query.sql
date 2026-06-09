SELECT
    cf.oproduct_id,
    'other' as 'channel',
    cf.ecf_date AS 'month',
    SUM(cf.ecf_qty) AS demand_quantity
FROM
    analytics.echannel_forecasts cf
    LEFT JOIN analytics.bc_us_items bi ON cf.oproduct_id = bi.product_id
    #LEFT JOIN analytics.ego_forward_skus gfs ON cf.oproduct_id = gfs.oproduct_id
WHERE
    bi.go_forward_flag = 1
    AND cf.echannel_id NOT IN (15, 27, 31, 85, 73, 132, 179, 185, 204, 910, 911, 912, 913) # Exclude DI channels and amazon and wayfair
    AND cf.ecf_date >=  DATE_FORMAT(NOW() ,'%Y-%m-01')
GROUP BY
    cf.oproduct_id,
    channel,
    cf.ecf_date

UNION

# just for amazon us and ca because we need to get just the dropship percent
SELECT
    cf.oproduct_id,
    'amazon' AS 'channel',
    cf.ecf_date AS 'month',
    SUM(cf.ecf_qty * COALESCE(ap.adropship_percentage, 0)) AS demand_quantity # if null, multiply by 0. basically we are saying that if there is a forecast for 27 or 31 we are going to assume it's di if there isn't a dropship percent. the di forecast query multiplies by 1 if null
FROM
    analytics.echannel_forecasts cf
    LEFT JOIN analytics.bc_us_items bi ON cf.oproduct_id = bi.product_id
    #LEFT JOIN analytics.ego_forward_skus gfs ON cf.oproduct_id = gfs.oproduct_id
    LEFT JOIN analytics.ainventory_depletions_amazon_percentages ap on cf.oproduct_id = ap.oproduct_id and cf.echannel_id = ap.ochannel_id

WHERE
    bi.go_forward_flag = 1
    AND cf.echannel_id IN (27,31)
    AND cf.ecf_date >=  DATE_FORMAT(NOW() ,'%Y-%m-01')
GROUP BY
    cf.oproduct_id,
    channel,
    cf.ecf_date

UNION
# just wayfair
SELECT
    cf.oproduct_id,
    'wayfair' as 'channel',
    cf.ecf_date AS 'month',
    SUM(cf.ecf_qty) AS demand_quantity
FROM
    analytics.echannel_forecasts cf
    LEFT JOIN analytics.bc_us_items bi ON cf.oproduct_id = bi.product_id
    #LEFT JOIN analytics.ego_forward_skus gfs ON cf.oproduct_id = gfs.oproduct_id
WHERE
    bi.go_forward_flag = 1
    AND cf.echannel_id = 15
    AND cf.ecf_date >=  DATE_FORMAT(NOW() ,'%Y-%m-01')
GROUP BY
    cf.oproduct_id,
    channel,
    cf.ecf_date

ORDER BY
    oproduct_id,
    channel,
    month