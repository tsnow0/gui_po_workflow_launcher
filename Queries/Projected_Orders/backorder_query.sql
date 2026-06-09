SELECT
    backorder.FulfilledProductID as oproduct_id,
    SUM(backorder.BackorderQty) AS backorder_quantity
FROM
(
    SELECT IFNULL(p4.oproduct_id, IFNULL(p3.oproduct_id, IFNULL(pr.oproduct_id, p.oproduct_id))) AS FulfilledProductID,
           IF(o.flow_state_id = 28, (CAST(oi.oorder_item_quantity as SIGNED) - CAST(oi.oorder_item_quantity_canceled as SIGNED)) , oi.oorder_item_quantity_backordered) AS BackorderQty
      FROM hq.oorderitems oi
        JOIN hq.oorders o ON oi.oorder_id = o.oorder_id
        LEFT JOIN hq.oproducts p ON oi.oproduct_id = p.oproduct_id
        LEFT JOIN hq.oproducts pr ON pr.oproduct_id = p.oproduct_master_id
        LEFT JOIN (SELECT DISTINCT s.oproduct_id_ordered, s.oproduct_id_fulfilled FROM hq.oSubstitutions s WHERE s.osubstitution_is_active = 1) AS sub ON sub.oproduct_id_ordered = p.oproduct_id #ADDED 11.06.2023
        LEFT JOIN hq.oproducts p3 ON sub.oproduct_id_fulfilled = p3.oproduct_id #ADDED 11.06.2023 - For Fulfilled SKU
        LEFT JOIN hq.obundles bd on IFNULL(p3.oproduct_id, IFNULL(pr.oproduct_id, p.oproduct_id)) = bd.obundle_parent_id
        LEFT JOIN hq.oproducts p4 on bd.oproduct_id = p4.oproduct_id # added 5.20.25 - for bundle fulfilled skus
      WHERE TRUE
        AND p.oproduct_sku NOT IN ('DROP SHIP FEE')
        AND o.oorder_status_id NOT IN (1, 9)
        AND YEAR(o.oorder_date) >= (YEAR(CURDATE()) - 1)
        AND (CAST(oi.oorder_item_quantity as SIGNED) - CAST(oi.oorder_item_quantity_canceled as SIGNED)) != 0
        AND (oi.oorder_item_quantity_backordered > 0
            OR o.flow_state_id = 28
            OR oi.oorder_item_id IN (SELECT oip.oorder_item_id
                                      FROM hq.order_item_parents oip
                                      JOIN hq.oorderitems oi ON oi.oorder_item_id = oip.oorder_item_id
                                      JOIN hq.oorders o ON oi.oorder_id = o.oorder_id
                                      WHERE o.flow_state_id = 28
                                     )
            )
) AS backorder
GROUP BY
    oproduct_id