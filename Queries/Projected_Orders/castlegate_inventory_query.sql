SELECT p.oproduct_id,
       DATE_FORMAT(NOW() ,'%Y-%m-01') AS 'month',
       i.oinventory_ext_pos_available as cg_inventory_quantity
FROM hq.oInventoryExtPOS i
LEFT JOIN hq.oproducts p ON i.oproduct_id = p.oproduct_id
WHERE TRUE
    AND i.ochannel_id = 15
    AND p.oproduct_designation_id NOT IN (3, 10) -- Inserts, DNIP/OOP
    AND p.obrand_id NOT IN (49, 51) -- 3PL 49,  Becky Owens 51
    AND p.oproduct_id NOT IN (SELECT pcl.oproduct_id
                              FROM hq.oProductCategoryLinks pcl
                              WHERE pcl.oproduct_sub_category1_id IN (213, 217)
                              ) -- Apparel 213, Fireworks 217;
    AND i.oinventory_ext_pos_available > 0;