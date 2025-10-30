SELECT
    ds.raceId,
    r.year,
    r.name AS race_name,
    ds.driverId,
    d.driverRef AS driver_ref,
    d.number AS driver_number,
    d.code AS driver_code,
    d.forename AS driver_forename,
    d.surname AS driver_surname,
    ds.points,
    ds.position,
    ds.wins
FROM
    driver_standings ds
JOIN
    races r ON ds.raceId = r.raceId
JOIN
    drivers d ON ds.driverId = d.driverId
ORDER BY
    r.year DESC,
    ds.raceId ASC,
    ds.position ASC;