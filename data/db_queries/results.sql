WITH fastest_laps_ranked AS (
    SELECT
        l.session_entry_id,
        l.number as fastest_lap_number,
        l.time as fastest_lap_time,
        ROW_NUMBER() OVER(PARTITION BY l.session_entry_id ORDER BY l.time ASC) as rn
    FROM lap l
),
fastest_laps AS (
    SELECT
        session_entry_id,
        fastest_lap_number,
        fastest_lap_time
    FROM fastest_laps_ranked
    WHERE rn = 1
)
SELECT
    s.id AS session_id,
    c.year,
    r.name AS race_name,
    d.id AS driverId,
    d.reference AS driver_ref,
    re.car_number AS driver_number,
    d.abbreviation AS driver_code,
    d.forename AS driver_forename,
    d.surname AS driver_surname,
    d.forename || ' ' || d.surname AS driver_full_name,
    t.id AS constructorId,
    t.name AS constructor_name,
    se.grid AS starting_position,
    se.position AS finishing_position,
    se.points,
    se.laps_completed AS laps,
    se.time AS milliseconds,
    fl.fastest_lap_number AS fastestLap,
    se.fastest_lap_rank AS rank,
    fl.fastest_lap_time AS fastestLapTime,
    se.status AS statusId
FROM
    sessionentry AS se
JOIN
    session AS s ON se.session_id = s.id
JOIN
    round AS r ON s.round_id = r.id
JOIN
    season AS c ON r.season_id = c.id
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
    s.type = 'R' -- Filtra APENAS para a corrida principal
ORDER BY
    c.year DESC,
    r.number ASC,
    se.position ASC;
