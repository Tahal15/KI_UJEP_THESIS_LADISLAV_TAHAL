-- DimCity
INSERT IGNORE INTO DimCity (CityKey, CityName, IsActive) VALUES (-1, 'UNKNOWN', TRUE);

-- DimCountry
INSERT IGNORE INTO DimCountry (CountryKey, CountryCode) VALUES (-1, 'UNKNOWN');

-- DimDetectionType
INSERT IGNORE INTO DimDetectionType (DetectionTypeKey, DetectionType) VALUES (-1, 'UNKNOWN');

-- DimLP
INSERT IGNORE INTO DimLP (LPKey, LicensePlate) VALUES (-1, 'UNKNOWN');

-- DimSensor
INSERT IGNORE INTO DimSensor (SensorKey, SensorCode) VALUES (-1, 'UNKNOWN');

-- DimVehicleClass
INSERT IGNORE INTO DimVehicleClass (VehicleClassKey, VehicleClass) VALUES (-1, -1);

-- DimTime (časová dimenze potřebuje smysluplný záznam)
INSERT IGNORE INTO DimTime (
    TimeKey, FullDate, YearNum, MonthNum, DayNum,
    DayOfWeekNum, HourNum, MinuteNum
) VALUES (
    -1, '1900-01-01 00:00:00', 1900, 1, 1, 1, 0, 0
);
