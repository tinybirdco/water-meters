SELECT
    1 AS meter_id,
    now() - rand() % 86400 AS timestamp,
    rand() % 100 / 10 AS flow_rate,
    1 + rand() % 29 AS temperature
FROM numbers(4)