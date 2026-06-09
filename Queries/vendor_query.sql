#
# NOTE: IF ANY CHANGES ARE MADE TO THIS QUERY, COPY THE NEW VERSION TO THE analytics_order_prompt_containerization_gui REPO
#
SELECT
	p.oproduct_id,
	v.ovendor_id,
	ap.aproducts_type AS Category,
	ap.aproducts_parentsku AS Parent,
	CONCAT(p.oproduct_sku,v.ovendor_code) AS SKUVen,
	p.oproduct_sku,
	opvd_40hc_container_qty,
	oproduct_qty_per_container,
	IF(IFNULL(opvd_case_pack_qty,0)=0,1,opvd_case_pack_qty) AS opvd_case_pack_qty,
	ROUND(70/((opvd_vendor_unit_length * opvd_vendor_unit_height * opvd_vendor_unit_width)/61023.7),0) AS ContQuant,
	(opvd_vendor_unit_length * opvd_vendor_unit_height * opvd_vendor_unit_width)/61023.7 AS CBM,
	IFNULL(oproduct_version_standard_cost,pc.material_cost) AS FOBCost,
	IFNULL(oproduct_version_new_order_landed_cost,pc.standard_cost) AS LandedCost

FROM analytics.bc_us_items bci
LEFT JOIN
	(SELECT
			pvd.oproduct_id,
			pvd.ovendor_id,
			v.ovendor_code,
			pvc.oproduct_version_new_order_landed_cost,
			pvc.oproduct_version_landed_cost,
			pvc.oproduct_version_standard_cost,
			pvd.opvd_40hc_container_qty,
			pvd.opvd_case_pack_qty,
			pvd.opvd_vendor_unit_length,
			pvd.opvd_vendor_unit_height,
			pvd.opvd_vendor_unit_width,
			pvd.opvd_location_MOQ AS U_MOQ,
	      pvd.opvd_location_MOQ_type AS U_MOQ_TYPE,
	      CASE
	          WHEN pvd.opvd_location_MOQ_type = 'SKU' AND pvd.opvd_location_MOQ IS NOT NULL AND pvd.opvd_location_MOQ > 0 THEN pvd.opvd_location_MOQ
	               WHEN pvd.opvd_case_pack_qty IS NOT NULL AND pvd.opvd_case_pack_qty > 0 THEN pvd.opvd_case_pack_qty
	          ELSE 1
	       END AS MinDRPQty
		FROM  hq.oProductVersionDetails pvd
 		JOIN hq.oProductVersionPODefaults pvpo ON pvpo.oversion_detail_id_for_pos = pvd.oversion_detail_id
     LEFT JOIN hq.oProductVersionCosts pvc ON pvc.oversion_detail_id = pvpo.oversion_detail_id_for_pos
      JOIN hq.ovendors v ON v.ovendor_id = pvd.ovendor_id
      )x ON x.oproduct_id = bci.product_id AND x.ovendor_code = bci.vendor_number
JOIN hq.ovendors v ON v.ovendor_code = bci.vendor_number
JOIN hq.oproducts p ON p.oproduct_id = bci.product_id
LEFT JOIN analytics.aproducts ap ON ap.oproduct_id = p.oproduct_id
LEFT JOIN hq.product_costs pc ON pc.oproduct_id = bci.product_id

