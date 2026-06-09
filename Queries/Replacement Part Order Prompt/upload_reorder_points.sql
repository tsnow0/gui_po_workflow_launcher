INSERT INTO
    analytics.replacement_parts_reorder_points(product,
              `min`,
              `max`
              )
VALUES (%(product)s,
        %(min)s,
        %(max)s
        )
ON DUPLICATE KEY UPDATE
    `min` = VALUES(`min`),
    `max` = VALUES(`max`)
;