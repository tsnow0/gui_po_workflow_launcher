SELECT i.product_id as oproduct_id,
       CASE WHEN wds.location = 'CASTLEGATE' THEN 'CG' ELSE 'DS' END as fulfillment,
       SUM(wds.demand_split) as demand_split
FROM analytics.awayfair_demand_split wds
JOIN analytics.bc_us_items i on wds.product = i.product
GROUP BY i.product_id, fulfillment