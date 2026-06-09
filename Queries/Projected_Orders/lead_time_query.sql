SELECT
    v.ovendor_code as vendor_number,
    CASE
        WHEN v.ovendor_id = 1254859 AND pv.oproduct_vendor_production_days IS NULL THEN 40 + 45
        WHEN v.ovendor_id = 78038 AND pv.oproduct_vendor_production_days IS NULL THEN 45 + 57
        WHEN v.ovendor_id = 1254876 AND pv.oproduct_vendor_production_days IS NULL THEN 100 + 14 + 44
        WHEN v.ovendor_id = 1254877 AND pv.oproduct_vendor_production_days IS NULL THEN 100 + 14 + 44
        WHEN v.ovendor_id = 1254878 AND pv.oproduct_vendor_production_days IS NULL THEN 100 + 14 + 44
        WHEN v.ovendor_id = 1254879 AND pv.oproduct_vendor_production_days IS NULL THEN 100 + 14 + 44
        WHEN v.ovendor_id = 440174 THEN 60
        ELSE ROUND(AVG(pv.oproduct_vendor_production_days) + IFNULL(AVG(IFNULL(ld.avg_dwell, 0) + IFNULL(ld.avg_water_transit, 0) + IFNULL(ld.avg_land_transit, 0)), AVG(pv.oproduct_vendor_transit_days)), 0)
        END as 'avg_lead_days'
FROM
    analytics.bc_us_items i
    JOIN hq.ovendors v ON i.vendor_number = v.ovendor_code
    LEFT JOIN hq.oproductsvendors pv ON v.ovendor_id = pv.ovendor_id
    LEFT JOIN hq.oproducts pr ON i.product_id = pr.oproduct_id
    LEFT JOIN analytics.alead_days ld ON v.ovendor_id = ld.avendor_id AND ld.alocation_id IN (12, 44)
WHERE TRUE
    AND i.go_forward_flag = 1
GROUP BY
    v.ovendor_id;