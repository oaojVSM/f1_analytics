-- SQLite
-- Query para montar versão de reporting da tabela de resultados de corridas

WITH fastest_laps_ranked AS (
    SELECT
        l.session_entry_id,
        l.number as fastest_lap_number,
        l.time as fastest_lap_time,
        l.average_speed as fastest_lap_speed,
        ROW_NUMBER() OVER(PARTITION BY l.session_entry_id ORDER BY l.time ASC) as rn
    FROM lap l
),
fastest_laps AS (
    SELECT
        session_entry_id,
        fastest_lap_number,
        fastest_lap_time,
        fastest_lap_speed
    FROM fastest_laps_ranked
    WHERE rn = 1
)
SELECT
    r.name AS race_name,
    r.id AS round_id,
    c.year AS year,
    r.date AS race_date,
    circ.name AS circuit_name,
    circ.country AS circuit_country,
    d.id AS driver_id,
    d.abbreviation AS driver_code,
    d.reference AS driver_ref,
    d.forename AS driver_forename,
    d.surname AS driver_surname,
    d.forename || ' ' || d.surname AS driver_full_name,
    d.nationality AS driver_nationality,
    t.name AS constructor_name,
    t.nationality AS constructor_nationality,
    se.grid AS starting_position,
    se.position AS finishing_position,
    se.points AS points_scored,
    se.laps_completed AS laps_completed,
    se.time AS time_in_race_ms,
    fl.fastest_lap_number,
    se.fastest_lap_rank, -- "Posição" da volta mais rápida do piloto
    fl.fastest_lap_time,
    fl.fastest_lap_speed,
    se.status AS race_status,
    s.type AS session_type
FROM
    sessionentry AS se
JOIN
    session AS s ON se.session_id = s.id
JOIN
    round AS r ON s.round_id = r.id
JOIN
    season AS c ON r.season_id = c.id
JOIN
    circuit AS circ ON r.circuit_id = circ.id
JOIN
    roundentry AS re ON se.round_entry_id = re.id
JOIN
    teamdriver AS td ON re.team_driver_id = td.id
JOIN
    driver AS d ON td.driver_id = d.id
JOIN
    team AS t ON td.team_id = t.id
LEFT JOIN
    fastest_laps fl ON se.id = fl.session_entry_id
WHERE
    s.type IN ('R', 'SR')
ORDER BY
    c.year DESC,
    r.number ASC,
    se.position ASC;