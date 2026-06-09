SELECT
  a.oproduct_id,
  IFNULL(SUM(a.available_quantity), 0) AS evr_inventory_quantity,
  DATE_FORMAT(NOW() ,'%Y-%m-01') AS 'month'
FROM hq.available_inventory a
   JOIN hq.olocations l on a.olocation_id = l.olocation_id
GROUP BY
    a.oproduct_id
