-- DELETEs
DELETE FROM FactCameraDetection;
DELETE FROM ETL_IncrementalControl WHERE ProcessStep = 1;
DELETE FROM DimVehicleClass;
DELETE FROM DimCountry;
DELETE FROM DimDetectionType;
DELETE FROM DimLP;
DELETE FROM DimSensor;
DELETE FROM DimCity;

-- Reset AUTO_INCREMENT
ALTER TABLE DimVehicleClass AUTO_INCREMENT = 1;
ALTER TABLE DimCountry AUTO_INCREMENT = 1;
ALTER TABLE DimDetectionType AUTO_INCREMENT = 1;
ALTER TABLE DimLP AUTO_INCREMENT = 1;
ALTER TABLE DimSensor AUTO_INCREMENT = 1;
ALTER TABLE DimCity AUTO_INCREMENT = 1;
ALTER TABLE FactCameraDetection AUTO_INCREMENT = 1;

-- Insert fallback/UNKNOWN values
INSERT IGNORE INTO DimSensor (SensorKey, SensorCode)
VALUES (-1, 'UNKNOWN');

INSERT IGNORE INTO DimLP (LPKey, LicensePlate)
VALUES (-1, 'UNKNOWN');

INSERT IGNORE INTO DimDetectionType (DetectionTypeKey, DetectionType)
VALUES (-1, 'UNKNOWN');

INSERT IGNORE INTO DimVehicleClass (VehicleClassKey, VehicleClass)
VALUES (-1, '-999');

INSERT IGNORE INTO DimCountry (CountryKey, CountryCode)
VALUES (-1, 'UNK');

INSERT IGNORE INTO DimCity (CityKey, CityName)
VALUES (-1, 'UNKNOWN');

INSERT IGNORE INTO DimTime (
    TimeKey, FullDate, YearNum, MonthNum,
    DayNum, DayOfWeekNum, HourNum, MinuteNum
)
VALUES (
    -1, '1900-01-01 00:00:00', 1900, 1,
    1, 1, 0, 0
);
