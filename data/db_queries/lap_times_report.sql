-- SQLite
-- Query para montar versão de reporting da tabela de tempos de volta (compatível com novo schema)
WITH pit_laps AS (
    -- Identifica as voltas de entrada (in-lap) e saída (out-lap) dos boxes
    SELECT ps.session_entry_id,
        l.number AS in_lap,
        -- A volta em que o piloto entrou no pit
        (l.number + 1) AS out_lap -- A volta seguinte à entrada no pit
    FROM pitstop ps
        JOIN lap l ON ps.lap_id = l.id
)
SELECT r.name AS race_name,
    season.year AS year,
    r.date AS race_date,
    c.name AS circuit_name,
    c.country AS circuit_country,
    d.id AS driver_id,
    d.abbreviation AS driver_code,
    d.forename AS driver_forename,
    d.surname AS driver_surname,
    d.forename || ' ' || d.surname AS driver_full_name,
    d.nationality AS driver_nationality,
    t.name AS constructor_name,
    l.number AS lap_number,
    l.position AS position_on_lap,
    l.time AS lap_time,
    se.status AS race_status,
    -- Status final do piloto na corrida
    -- Stint Number: Increments after each pit stop (In-Lap stays in previous stint)
    (
        SUM(
            CASE
                WHEN ps_stint.id IS NOT NULL THEN 1
                ELSE 0
            END
        ) OVER (
            PARTITION BY se.id
            ORDER BY l.number
        ) - (
            CASE
                WHEN ps_stint.id IS NOT NULL THEN 1
                ELSE 0
            END
        ) + 1
    ) AS stint_number,
    -- Adiciona uma flag para identificar se a volta é de pit stop (entrada ou saída)
    CASE
        WHEN l.number = pl.in_lap
        OR l.number = pl.out_lap THEN 1
        ELSE 0
    END AS is_pit_lap
FROM lap AS l
    LEFT JOIN sessionentry AS se ON l.session_entry_id = se.id
    LEFT JOIN session AS s ON se.session_id = s.id
    LEFT JOIN round AS r ON s.round_id = r.id
    LEFT JOIN season AS season ON r.season_id = season.id
    LEFT JOIN circuit AS c ON r.circuit_id = c.id
    LEFT JOIN roundentry AS re ON se.round_entry_id = re.id
    LEFT JOIN teamdriver AS td ON re.team_driver_id = td.id
    LEFT JOIN driver AS d ON td.driver_id = d.id
    LEFT JOIN team AS t ON td.team_id = t.id
    LEFT JOIN pit_laps pl ON l.session_entry_id = pl.session_entry_id
    AND (
        l.number = pl.in_lap
        OR l.number = pl.out_lap
    )
    LEFT JOIN pitstop ps_stint ON l.id = ps_stint.lap_id
WHERE s.type = 'R' -- Filtra para tempos de volta da corrida principal
ORDER BY season.year DESC,
    r.number DESC,
    l.number ASC,
    l.position ASC;