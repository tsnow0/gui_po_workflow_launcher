SELECT
    po.ovendor_id,
    ROUND((DATEDIFF(DATE(pc.opo_container_receipt_date), DATE(po.opo_created_date))), 2) AS target_days
FROM
     hq.opos po
    LEFT JOIN hq.oPOContainers pc ON po.opo_id = pc.opo_id
WHERE
    pc.opo_container_receipt_date >= CURDATE() - INTERVAL 1 YEAR
    AND pc.opo_container_status_id = 4
    AND po.opo_id IS NOT NULL
ORDER BY
    po.ovendor_id