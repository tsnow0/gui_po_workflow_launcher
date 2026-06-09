SELECT
    x.oproduct_id,
    DATE_FORMAT(DATE_ADD(x.arrival_date, INTERVAL 1 - DAYOFMONTH(x.arrival_date) DAY), '%Y-%m-01') AS 'month',
    SUM(x.quantity) AS evr_po_quantity
FROM
    (
        SELECT
            po.opo_prefix,
            po.opo_id,
            poi.oproduct_id,
            v.ovendor_code,
            pc.opo_destination_id AS olocation_id,
            pci.opo_container_item_quantity AS quantity,
            DATE(IFNULL(pc.opo_container_ssd, pc.opo_container_eta)) AS arrival_date
        FROM
           hq.opoitems poi
           JOIN hq.oPOContainerItems pci on poi.opo_item_id = pci.opo_item_id
           JOIN hq.opos po ON poi.opo_id = po.opo_id
           JOIN hq.oPOContainers pc ON pci.opo_container_id = pc.opo_container_id
           JOIN hq.olocations l ON pc.opo_destination_id = l.olocation_id
           JOIN hq.ovendors v on po.ovendor_id = v.ovendor_id
           JOIN hq.oproducts p on poi.oproduct_id = p.oproduct_id
        WHERE TRUE
           AND pc.opo_container_status_id IN (1, 13)
           AND po.opo_status_id IN (1, 13)
           AND po.opo_prefix IN ('EVR')
           AND po.opo_id NOT IN (182667,182660,182663,183275)
           AND pc.opo_destination_id NOT IN (1)
           AND IFNULL(pc.opo_container_ssd, pc.opo_container_eta) >= DATE_ADD(CURDATE(), INTERVAL(-WEEKDAY(CURDATE())) DAY)
           AND l.olocation_is_owned = 1
           AND pci.opo_container_item_quantity > 0
    ) x
GROUP BY
    oproduct_id,
    YEAR(month),
    MONTH(month)
ORDER BY
    oproduct_id,
    YEAR(month),
    MONTH(month)