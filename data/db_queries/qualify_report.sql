-- SQLite
-- Construir versão de análise para dados de qualificação

SELECT
    r.name AS race_name,
    r.year AS year,
    r.date AS race_date,
    c.name AS circuit_name,
    c.country AS circuit_country,
    d.code AS driver_code,
    d.forename AS driver_forename,
    d.surname AS driver_surname,
    d.nationality AS driver_nationality,
    cons.name AS constructor_name,
    cons.nationality AS constructor_nationality,
    q.position AS position,
    q.q1 AS q1_time,
    q.q2 AS q2_time,
    q.q3 AS q3_time
FROM
    qualifying AS q 
        LEFT JOIN races AS r
            ON q.raceId = r.raceId
        LEFT JOIN circuits AS c
            ON r.circuitId = c.circuitId
        LEFT JOIN drivers AS d
            ON q.driverId = d.driverId
        LEFT JOIN constructors AS cons
            ON q.constructorId = cons.constructorId
