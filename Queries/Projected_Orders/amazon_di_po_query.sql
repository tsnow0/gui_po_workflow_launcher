SELECT
    x.oproduct_id,
    SUM(x.quantity) AS amazon_projected_sales_po_quantity,
    DATE_FORMAT(DATE_ADD(GREATEST(x.etd, x.container_ready_date), INTERVAL 1 - DAYOFMONTH(GREATEST(x.etd, x.container_ready_date)) DAY), '%Y-%m-01') AS month
FROM
(
    SELECT
        poi.oproduct_id,
        pci.opo_container_item_quantity AS quantity,
        IFNULL(DATE_ADD(DATE(pc.opo_container_etd), INTERVAL(-WEEKDAY(DATE(pc.opo_container_etd))) DAY), DATE('1900-01-01')) AS etd,
        IFNULL(DATE_ADD((DATE(pc.opo_container_ready_date) + INTERVAL 6 DAY), INTERVAL(-WEEKDAY((DATE(pc.opo_container_ready_date) + INTERVAL 6 DAY))) DAY), DATE('1900-01-01')) AS container_ready_date
    FROM
        hq.opoitems poi
        JOIN hq.opos po ON po.opo_id = poi.opo_id
        JOIN hq.oPOContainers pc ON pc.opo_id = po.opo_id
        JOIN hq.oPOContainerItems pci ON pci.opo_item_id = poi.opo_item_id
        JOIN hq.olocations l ON pc.opo_destination_id = l.olocation_id
    WHERE
        pc.opo_container_status_id IN (1, 13)
        AND po.opo_status_id IN (1, 13)
        AND po.opo_prefix IN ('AMZ')
        AND DATE(pc.opo_container_atd) IS NULL
        AND l.olocation_id = 6
) x
WHERE
    GREATEST(x.etd, x.container_ready_date) != DATE('1900-01-01')
GROUP BY
    x.oproduct_id,
   `month`
ORDER BY
    x.oproduct_id,
    `month`