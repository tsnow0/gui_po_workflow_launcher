SELECT
    i.product,
    SUM(pci.opo_container_item_quantity) AS po_quantity
FROM hq.opoitems poi
    JOIN hq.opos po ON po.opo_id = poi.opo_id
    JOIN hq.oPOContainerItems pci ON pci.opo_item_id = poi.opo_item_id
    JOIN hq.oPOContainers pc ON pci.opo_container_id = pc.opo_container_id
    JOIN hq.olocations l ON pc.opo_destination_id = l.olocation_id
    JOIN hq.ovendors v on po.ovendor_id = v.ovendor_id
    JOIN analytics.bc_us_items i on poi.oproduct_id = i.product_id
    JOIN analytics.replacement_parts_reorder_points rp on i.product = rp.product # only include and include all products that are in this table (there are some inserts in the table that were being excluded because I was filtering for POP and Replacement Part categories)
WHERE TRUE
    AND pc.opo_container_status_id IN (1, 13)
    AND po.opo_status_id IN (1, 13)
    AND po.opo_prefix IN ('EVR')
    AND pc.opo_destination_id NOT IN (1)
    AND IFNULL(pc.opo_container_ssd, pc.opo_container_eta) >= DATE_ADD(CURDATE(), INTERVAL(-WEEKDAY(CURDATE())) DAY)
    AND l.olocation_is_owned = 1
    AND pci.opo_container_item_quantity > 0
GROUP BY i.product