#
# NOTE: IF ANY CHANGES ARE MADE TO THIS QUERY, COPY THE NEW VERSION TO THE analytics_order_prompt_containerization_gui REPO
#
SELECT
	oproduct_sku AS SKU,
	SUM(IF(Location='California',Qty,0)) AS CA_Inv,
	SUM(IF(Location='South Carolina',Qty,0)) AS SC_Inv
FROM(
		SELECT
			p.oproduct_sku,
			l.olocation_name AS Location,
			SUM(pci.opo_container_item_quantity) AS Qty

		FROM hq.opos po
		JOIN hq.oPOContainers pco ON pco.opo_id = po.opo_id
		JOIN hq.oPOContainerItems pci ON pci.opo_container_id = pco.opo_container_id
		JOIN hq.opoitems poi ON poi.opo_item_id=pci.opo_item_id
		JOIN hq.oproducts p ON p.oproduct_id = poi.oproduct_id
		JOIN hq.olocations l ON l.olocation_id = pco.opo_destination_id
		WHERE
			 pco.opo_container_status_id NOT IN (5,6)
			-- AND p.oproduct_id IN (581)
			AND po.opo_created_date >= '2025-01-01'
			AND pci.opo_container_item_quantity >0
			AND poi.opo_item_amount IS NOT NULL
			AND poi.opo_item_amount >0
			AND pco.opo_container_receipt_date IS NULL
			AND pco.opo_destination_id IN (44,12)

		GROUP BY
			p.oproduct_sku,
			Location

			UNION All

			SELECT
				oproduct_sku,
				l.olocation_name AS Location,
				SUM(oh.on_hand_quantity) AS Qty
			FROM hq.on_hand_inventory oh
			JOIN hq.oproducts p ON p.oproduct_id = oh.oproduct_id
			JOIN hq.fulfillment_centers fc ON fc.id = oh.fulfillment_center_id
			JOIN hq.olocations l ON l.olocation_id = fc.olocation_id
			WHERE l.olocation_id IN(44,12)
		GROUP BY
			p.oproduct_sku,
			Location
		)x
	GROUP BY
		SKU