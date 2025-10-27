-- SQLite
-- Query para montar versão de reporting da tabela de tempos de volta

 WITH pit_laps AS (
    -- Identifica as voltas de entrada (in-lap) e saída (out-lap) dos boxes
    SELECT
        raceId,
        driverId,
        lap AS in_lap,      -- A volta em que o piloto entrou no pit
        (lap + 1) AS out_lap -- A volta seguinte à entrada no pit
    FROM pit_stops
)
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
    lt.milliseconds AS lap_time_ms,
    -- Adiciona uma flag para identificar se a volta é de pit stop (entrada ou saída)
    CASE
        WHEN lt.lap = pl.in_lap OR lt.lap = pl.out_lap THEN 1
        ELSE 0
    END AS is_pit_lap
FROM
    lap_times AS lt
    LEFT JOIN races AS r ON lt.raceId = r.raceId
    LEFT JOIN circuits AS c ON r.circuitId = c.circuitId
    LEFT JOIN drivers AS d ON lt.driverId = d.driverId
    LEFT JOIN pit_laps AS pl ON lt.raceId = pl.raceId AND lt.driverId = pl.driverId AND (lt.lap = pl.in_lap OR lt.lap = pl.out_lap);
