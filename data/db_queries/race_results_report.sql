-- SQLite
-- Query para montar versão de reporting da tabela de resultados de corridas

SELECT
    r.name AS race_name,
    r.year AS year,
    r.date AS race_date,
    c.name AS circuit_name,
    c.country AS circuit_country,
    d.code AS driver_code,
    d.forename AS driver_forename,
    d.surname AS driver_surname,
    CONCAT(d.forename, ' ', d.surname) AS driver_full_name, -- Faço isso, porque tem pilotos que tem dois sobrenomes (Schumacher, Villeneuve, etc e isso mistura os dados)
    d.nationality AS driver_nationality,
    cons.name AS constructor_name,
    cons.nationality AS constructor_nationality,
    res.grid AS starting_position,
    res.positionOrder AS finishing_position,
    res.points AS points_scored,
    res.laps AS laps_completed,
    res.time AS time_in_race,
    res.milliseconds AS time_in_race_ms,
    res.fastestLap AS fastest_lap_number, -- Em que volta o piloto fez a sua volta mais rápida
    res.rank AS fastest_lap_rank, -- Rank da volta mais rápida do piloto
    res.fastestLapTime AS fastest_lap_time, -- Tempo da volta mais rápida do piloto
    res.fastestLapSpeed AS fastest_lap_speed, -- Velocidade da volta mais rápida do piloto
    status.status AS race_status -- Status do piloto na corrida (e.g., Finished, Retired, etc.)
FROM
    results AS res
        LEFT JOIN
            races AS r ON res.raceId = r.raceId
        LEFT JOIN
            circuits AS c ON r.circuitId = c.circuitId
        LEFT JOIN
            drivers AS d ON res.driverId = d.driverId
        LEFT JOIN
            constructors AS cons ON res.constructorId = cons.constructorId
        LEFT JOIN
            status AS status ON res.statusId = status.statusId