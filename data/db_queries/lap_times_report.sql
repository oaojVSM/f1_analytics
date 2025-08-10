-- SQLite
-- Query para montar versão de reporting da tabela de tempos de volta

SELECT
    r.name AS race_name,
    r.year AS year,
    r.date AS race_date,
    c.name AS circuit_name,
    c.country AS circuit_country,
    d.code AS driver_code,
    d.forename AS driver_forename,
    d.surname AS driver_surname,
    CONCAT(d.forename, ' ', d.surname) AS driver_full_name,
    d.nationality AS driver_nationality,
    lt.lap AS lap_number,
    lt.position AS position_on_lap,
    lt.time AS lap_time,
    lt.milliseconds AS lap_time_ms
FROM
    lap_times AS lt
        LEFT JOIN
            races AS r ON lt.raceId = r.raceId
        LEFT JOIN
            circuits AS c ON r.circuitId = c.circuitId
        LEFT JOIN
            drivers AS d ON lt.driverId = d.driverId
ORDER BY
    r.year, r.date, lap_number, position_on_lap;
