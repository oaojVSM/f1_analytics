-- SQLite
-- Construir versão de análise para dados de qualificação (compatível com novo schema)
-- OBS: O novo schema não parece ter colunas distintas para q1, q2 e q3.
-- Esta query busca o melhor tempo de volta de cada piloto na sessão de qualificação.

WITH BestLapPerDriver AS (
    SELECT
        l.session_entry_id,
        MIN(l.time) as best_lap_time
    FROM
        lap l
    GROUP BY
        l.session_entry_id
)
SELECT
    r.name AS race_name,
    season.year AS year,
    r.date AS race_date,
    r.name AS circuit_name,
    c.locality AS circuit_locality,
    c.country AS circuit_country,
    d.id AS driver_id,
    d.forename AS driver_forename,
    d.surname AS driver_surname,
    d.forename || ' ' || d.surname AS driver_full_name,
    d.nationality AS driver_nationality,
    t.name AS constructor_name,
    t.nationality AS constructor_nationality,
    se.position AS position,
    bl.best_lap_time,
    s.type AS session_type
FROM
    sessionentry se
JOIN
    session s ON se.session_id = s.id
JOIN
    round r ON s.round_id = r.id
JOIN
    season season ON r.season_id = season.id
JOIN
    circuit c ON r.circuit_id = c.id
JOIN
    roundentry re ON se.round_entry_id = re.id
JOIN
    teamdriver td ON re.team_driver_id = td.id
JOIN
    driver d ON td.driver_id = d.id
JOIN
    team t ON td.team_id = t.id
LEFT JOIN
    BestLapPerDriver bl ON se.id = bl.session_entry_id
WHERE
    s.type LIKE 'Q%' -- Filtra para sessões de qualificação (Q1, Q2, Q3, etc.)
ORDER BY
    season.year DESC,
    r.number DESC,
    s.type ASC,
    se.position ASC;