SELECT
    x.oproduct_id,
    x.opo_prefix,
    DATE_FORMAT(DATE_ADD(x.arrival_date, INTERVAL 1 - DAYOFMONTH(x.arrival_date) DAY), '%Y-%m-01') AS 'month',
    SUM(x.quantity) AS di_po_quantity
FROM
    (
        SELECT
           poi.oproduct_id,
           po.opo_prefix,
           v.ovendor_code,
           pc.opo_destination_id AS olocation_id,
           pci.opo_container_item_quantity AS quantity,
           DATE(IFNULL(pc.opo_container_ssd, pc.opo_container_eta)) AS arrival_date
        FROM
           hq.opoitems poi
           JOIN hq.opos po ON po.opo_id = poi.opo_id
           JOIN hq.oPOContainerItems pci ON pci.opo_item_id = poi.opo_item_id
           JOIN hq.oPOContainers pc ON pci.opo_container_id = pc.opo_container_id
           JOIN hq.olocations l ON pc.opo_destination_id = l.olocation_id
           JOIN hq.ovendors v on po.ovendor_id = v.ovendor_id
           JOIN hq.oproducts p on poi.oproduct_id = p.oproduct_id
        WHERE TRUE
           AND pc.opo_container_status_id IN (1, 13)
           AND po.opo_status_id IN (1, 13)
           AND po.opo_prefix IN ('AMZ', 'AMC', 'WAY')
           AND IFNULL(pc.opo_container_ssd, pc.opo_container_eta) >= DATE_ADD(CURDATE(), INTERVAL(-WEEKDAY(CURDATE())) DAY)
           AND l.olocation_id = 6
           AND pci.opo_container_item_quantity > 0
    ) x
GROUP BY
    oproduct_id,
    opo_prefix,
    YEAR(month),
    MONTH(month)
ORDER BY
    oproduct_id,
    opo_prefix,
    YEAR(month),
    MONTH(month)