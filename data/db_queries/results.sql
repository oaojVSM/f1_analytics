SELECT
    r.raceId,
    r.year,
    r.name AS race_name,
    res.driverId,
    d.driverRef AS driver_ref,
    d.number AS driver_number,
    d.code AS driver_code,
    d.forename AS driver_forename,
    d.surname AS driver_surname,
    d.forename || ' ' || d.surname AS driver_full_name,
    res.constructorId,
    c.name AS constructor_name,
    res.grid AS starting_position,
    res.positionOrder AS finishing_position,
    res.points,
    res.laps,
    res.time,
    res.milliseconds,
    res.fastestLap,
    res.rank,
    res.fastestLapTime,
    res.fastestLapSpeed,
    res.statusId
FROM
    results res
JOIN
    races r ON res.raceId = r.raceId
JOIN
    drivers d ON res.driverId = d.driverId
JOIN
    constructors c ON res.constructorId = c.constructorId
ORDER BY
    r.year DESC,
    r.raceId ASC,
    res.positionOrder ASC;
