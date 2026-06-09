#
# NOTE: IF ANY CHANGES ARE MADE TO THIS QUERY, COPY THE NEW VERSION TO THE analytics_order_prompt_containerization_gui REPO
#
SELECT
    v.ovendor_id,
	case when v.ovendor_id ='' then 'missing' else ovendor_code end as ovendor_code,
	v.ovendor_name,
	v.ovendor_external_id

FROM hq.ovendors v
WHERE v.ovendor_is_active = 1