SELECT
    id.oproduct_id,
    id.ainventory_depletions_owned_locations as 'owned_location_flag',
    id.ainventory_depletions_month as 'month',
    id.ainventory_depletions_quantity as 'inventory_quantity'
FROM
    analytics.ainventory_depletions_aggregate id
    LEFT JOIN analytics.ego_forward_skus gfs ON id.oproduct_id = gfs.oproduct_id
WHERE
    gfs.go_forward_flag = 1
ORDER BY
    id.oproduct_id,
    id.ainventory_depletions_owned_locations,
    id.ainventory_depletions_month