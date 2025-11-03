-- SQLite
-- Query para montar versão de reporting da tabela de pilotos (compatível com novo schema)

SELECT
    id AS driver_id,
    abbreviation AS driver_code,
    forename AS driver_forename,
    surname AS driver_surname,
    forename || ' ' || surname AS driver_full_name,
    date_of_birth AS dob
FROM
    driver;