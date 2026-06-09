INSERT INTO
    analytics.eprojected_orders(oproduct_id,
                            location,
                            order_month,
                            order_arrival_month,
                            safety_stock_quantity,
                            demand_quantity,
                            order_quantity)
VALUES
    (%(oproduct_id)s,
    %(location)s,
    %(order_date)s,
    %(month)s,
    %(safety_stock_order_quantity)s,
    %(demand_order_quantity)s,
    %(order_quantity)s)
ON DUPLICATE KEY UPDATE
    safety_stock_quantity = VALUES(safety_stock_quantity),
    demand_quantity = VALUES(demand_quantity),
    order_quantity = VALUES(order_quantity)
