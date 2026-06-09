UPDATE
    hq.oPOContainers
SET
    opo_container_eta = %(new_eta)s
WHERE
    opo_container_name = %(po)s