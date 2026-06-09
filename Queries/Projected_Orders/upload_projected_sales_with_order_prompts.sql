INSERT INTO
    analytics.eprojected_sales_with_order_prompts(product_id,
                                projected_sales_date,
                                non_di_sales,
                                di_sales,
                                total_projected_sales)
VALUES
    (%(oproduct_id)s,
    %(end_date)s,
    %(non_di_sales)s,
    %(di_sales)s,
    %(total_projected_sales)s)
ON DUPLICATE KEY UPDATE
    non_di_sales = VALUES(non_di_sales),
    di_sales = VALUES(di_sales),
    total_projected_sales = VALUES(total_projected_sales)