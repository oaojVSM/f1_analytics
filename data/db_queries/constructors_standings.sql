-- SQLite
-- Query para montar versão de reporting da tabela de classificação de construtores

SELECT
    cs.round_id,
    cs.year,
    r.name AS race_name,
    cs.team_id,
    t.name AS constructor_name,
    t.nationality AS constructor_nationality,
    cs.points,
    cs.position,
    cs.win_count AS wins
FROM
    teamchampionship cs
JOIN
    round r ON cs.round_id = r.id
JOIN
    team t ON cs.team_id = t.id
ORDER BY
    cs.year DESC,
    cs.round_id DESC,
    cs.position ASC;
