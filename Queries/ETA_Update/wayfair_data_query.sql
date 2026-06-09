SELECT
    pc.opo_container_name AS 'po',
    p.ovendor_id AS 'vendor_id',
    v.ovendor_code AS 'vendor',
    ld.omaersk_dir_locations_id AS 'destination_id',
    l.olocation_name AS 'destination',
    DATE(pc.opo_container_ready_date) AS 'cargo_ready',
    DATE(pc.opo_container_requested_ship_date) AS 'requested_ship',
    IFNULL(ld.awld_avg_dwell, 0) AS 'dwell',
    IFNULL((ld.awld_avg_water_transit + ld.awld_avg_land_transit), pv.oproduct_vendor_transit_days) AS 'transit_time',
    DATE(pc.opo_container_eta) AS 'eta',
    IF(UPPER(v.ovendor_origin_port) = 'DOMESTIC', 1, 0) AS 'domestic_flag',
    0 AS 'amz_flag',
    1 AS 'wayfair_flag'
FROM
    hq.opos p
    JOIN hq.oPOContainers pc ON pc.opo_id = p.opo_id
    JOIN hq.olocations l ON l.olocation_id = pc.opo_destination_id
    JOIN hq.ovendors v ON v.ovendor_id = p.ovendor_id
    LEFT JOIN analytics.awayfair_lead_days ld ON ld.ovendor_id = p.ovendor_id AND ld.omaersk_dir_locations_id = pc.opo_destination_id
    LEFT JOIN hq.oproductsvendors pv ON pv.ovendor_id = p.ovendor_id AND pv.oproduct_vendor_is_active = 1
WHERE
    (pc.opo_container_number = ""
    OR pc.opo_container_number IS NULL)
    AND pc.opo_container_status_id IN (1, 13)
    AND p.opo_prefix = 'WAY'
    AND pc.opo_destination_id = 6
    AND UPPER(v.ovendor_origin_port) <> 'DOMESTIC'
GROUP BY
    pc.opo_container_name