SELECT i.product,
       rp.min,
       rp.max,
       i.vendor_number,
       i.status as item_status
FROM analytics.replacement_parts_reorder_points rp
JOIN analytics.bc_us_items i on rp.product = i.product