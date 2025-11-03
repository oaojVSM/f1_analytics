-- SQLite
-- Query para montar versão de reporting da tabela de classificação de pilotos (compatível com novo schema)

SELECT
    ds.round_id,
    ds.year,
    r.name AS race_name,
    ds.driver_id,
    d.reference AS driver_ref,
    d.permanent_car_number AS driver_number,
    d.abbreviation AS driver_code,
    d.forename AS driver_forename,
    d.surname AS driver_surname,
    ds.points,
    ds.position,
    ds.win_count AS wins
FROM
    driverchampionship ds
JOIN
    round r ON ds.round_id = r.id
JOIN
    driver d ON ds.driver_id = d.id
ORDER BY
    ds.year DESC,
    ds.round_id DESC,
    ds.position ASC;