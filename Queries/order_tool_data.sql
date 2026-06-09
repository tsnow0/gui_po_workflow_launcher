#
# NOTE: IF ANY CHANGES ARE MADE TO THIS QUERY, COPY THE NEW VERSION TO THE analytics_order_prompt_containerization_gui REPO
#
SELECT
	*
FROM
	(
	SELECT
		x.VendorCode,
		x.Category,
		x.Parent,
		x.Tier,
		x.Blocked AS 'Hold Status',
		x.SKU,
		x.MinOrder,
		x.ContQuant,
		x.CBM,
		SUM(IF(po.location='EVR',po.order_quantity,0)) AS 'EVR OrderQty',
		SUM(IF(po.location='CG',po.order_quantity,0)) AS 'CG OrderQty',
		x.LandedCost,
		po.order_month AS OrderMonth,
		po.order_arrival_month AS OrderArrivalMonth

	FROM analytics.eprojected_orders po
	LEFT JOIN
	(


		SELECT
			v.ovendor_id AS VendorID,
			v.ovendor_code AS VendorCode,
			ap.aproducts_type AS Category,
			ap.aproducts_parentsku AS Parent,
			p.oproduct_id AS ProdID,
			p.oproduct_sku AS SKU,
			IFNULL(IF(opvd_case_pack_qty=0,1,opvd_case_pack_qty),1) AS CasePack,
			ROUND(70/((opvd_vendor_case_pack_length * opvd_vendor_case_pack_width * opvd_vendor_case_pack_height)/61023.7/opvd_case_pack_qty ),0) AS ContQuant,
						(opvd_vendor_case_pack_length * opvd_vendor_case_pack_width * opvd_vendor_case_pack_height)/61023.7/opvd_case_pack_qty AS CBM,
			IFNULL(bcic.unit_cost,IFNULL(oproduct_version_standard_cost,pc.material_cost)) AS FOBCost,
			IF(IFNULL(oproduct_version_new_order_landed_cost,pc.standard_cost)=0,IFNULL(oproduct_version_standard_cost,pc.material_cost),IFNULL(oproduct_version_new_order_landed_cost,pc.standard_cost)) AS LandedCost,
			IFNULL(MinDRPQty,1) AS MinOrder,
			p.oproduct_tier AS Tier,
			bci.status AS Blocked

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
					pvd.opvd_vendor_case_pack_length,
					pvd.opvd_vendor_case_pack_height,
					pvd.opvd_vendor_case_pack_width,
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
--		      WHERE pvd.oproduct_id = 133337
		      )x ON x.oproduct_id = bci.product_id AND x.ovendor_code = bci.vendor_number
		JOIN hq.ovendors v ON v.ovendor_code = bci.vendor_number
		JOIN hq.oproducts p ON p.oproduct_id = bci.product_id
		LEFT JOIN analytics.aproducts ap ON ap.oproduct_id = p.oproduct_id
		LEFT JOIN hq.product_costs pc ON pc.oproduct_id = bci.product_id
	 	LEFT JOIN analytics.bc_us_item_costs bcic ON bcic.product = bci.product
		 													AND bcic.vendor_number = bci.vendor_number
															AND bcic.ending_date IS NULL

		)
		x ON x.ProdID = po.oproduct_id
		WHERE TRUE
--		AND po.order_quantity = 0
		AND po.order_month < CURDATE() + INTERVAL 2 MONTH
		AND po.order_month >= DATE_FORMAT(CURDATE(),'%Y-%m-01')
		AND x.SKU IS NOT NULL

		GROUP BY
			x.SKU,
			OrderMonth
	)y
ORDER BY
	y.VendorCode,
	y.Parent,
	y.OrderMonth,
	y.OrderMonth,
	'EVR OrderQty' DESC;
