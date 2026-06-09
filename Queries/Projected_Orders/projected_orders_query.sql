SELECT
    i.product AS Product,
    i.parent AS Parent,
    v.ovendor_code AS Vendor,
    po.order_month AS Order_Month,
    po.order_arrival_month AS Arrival_Month,
	SUM(CASE WHEN po.location = 'EVR' THEN order_quantity ELSE 0 END) AS EVR_Order_Quantity,
    SUM(CASE WHEN po.location = 'CG' THEN order_quantity ELSE 0 END) AS CG_Order_Quantity,
    ic.unit_cost AS FOB_Cost,
    pvc.oproduct_version_new_order_landed_cost AS New_Order_Landed_Cost,
    pc.standard_cost AS Standard_Cost,
    CASE
        WHEN IFNULL(pvd.opvd_40hc_container_qty, p.oproduct_qty_per_container) = 0 THEN 0
        WHEN IFNULL(pvd.opvd_40hc_container_qty, p.oproduct_qty_per_container) IS NULL THEN 0
        ELSE SUM(CASE WHEN po.location = 'EVR' THEN order_quantity ELSE 0 END) / IFNULL(pvd.opvd_40hc_container_qty, p.oproduct_qty_per_container)
        END AS EVR_Container_Fill,
    CASE
        WHEN IFNULL(pvd.opvd_40hc_container_qty, p.oproduct_qty_per_container) = 0 THEN 0
        WHEN IFNULL(pvd.opvd_40hc_container_qty, p.oproduct_qty_per_container) IS NULL THEN 0
        ELSE SUM(CASE WHEN po.location = 'CG' THEN order_quantity ELSE 0 END) / IFNULL(pvd.opvd_40hc_container_qty, p.oproduct_qty_per_container)
        END AS CG_Container_Fill,
    CASE
        WHEN po.order_quantity < IFNULL(pvd.opvd_location_MOQ, 0) THEN 'No'
        ELSE 'Yes'
        END AS 'MOQ_Met?',
    CASE WHEN i.status = 'ON HOLD' THEN 1 ELSE 0 END as On_Hold
FROM
    analytics.eprojected_orders po
    LEFT JOIN hq.oproducts p ON po.oproduct_id = p.oproduct_id
    LEFT JOIN analytics.bc_us_items i ON po.oproduct_id = i.product_id
    LEFT JOIN hq.ovendors v ON i.vendor_number = v.ovendor_code
    LEFT JOIN analytics.bc_us_item_costs ic ON i.product = ic.product
                                                        AND v.ovendor_code = ic.vendor_number
    LEFT JOIN hq.oProductVersionPODefaults pod ON po.oproduct_id = pod.oproduct_id
                                                                AND v.ovendor_id = pod.oproduct_version_po_default_vendor_id
                                                                AND ic.ending_date IS NULL
    LEFT JOIN hq.oProductVersionDetails pvd ON pod.oversion_detail_id_for_pos = pvd.oversion_detail_id
    LEFT JOIN hq.oProductVersionCosts pvc ON pvd.oversion_detail_id = pvc.oversion_detail_id
    LEFT JOIN hq.product_costs pc ON po.oproduct_id = pc.oproduct_id
WHERE
    po.order_quantity > 0
GROUP BY Product, Vendor, Order_Month