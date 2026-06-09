SELECT
  i.product,
  IFNULL(SUM(oh.on_hand_quantity), 0) AS inventory_quantity
FROM
    hq.on_hand_inventory oh
   LEFT JOIN hq.fulfillment_centers fc on oh.fulfillment_center_id = fc.id
   LEFT JOIN hq.olocations l ON fc.olocation_id=l.olocation_id
   LEFT JOIN analytics.bc_us_items i on oh.oproduct_id = i.product_id
   JOIN analytics.replacement_parts_reorder_points rp on i.product = rp.product # only include and include all products that are in this table (there are some inserts in the table that were being excluded because I was filtering for POP and Replacement Part categories)
WHERE TRUE
GROUP BY
    i.product;
