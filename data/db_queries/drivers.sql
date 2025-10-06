-- SQLite
-- Query para montar versão de reporting da tabela de resultados de corridas

SELECT
    driverId AS driver_id,
    code AS driver_code,
    forename AS driver_forename,
    surname AS driver_surname,
    CONCAT(forename, ' ', surname) AS driver_full_name, -- Alguns pilotos tem dois sobrenomes (Schumacher, Villeneuve, etc e isso mistura os dados)
    dob AS dob -- Data de Nascimento
FROM
    drivers