SELECT
    i.oproduct_id,
    i.ochannel_id,
    IFNULL(i.oinventory_ext_pos_available, 0) AS di_inventory_quantity,
    DATE_FORMAT(NOW() ,'%Y-%m-01') AS 'month'
FROM
    hq.oInventoryExtPOS i
WHERE
    i.ochannel_id IN (27,31)