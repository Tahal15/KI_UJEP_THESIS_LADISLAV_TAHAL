DROP TABLE IF EXISTS DimCity;

CREATE TABLE DimCity
(
    CityKey UInt32 DEFAULT CAST(rand64(), 'UInt32'),
    CityName String
)
ENGINE = MergeTree
ORDER BY CityKey;

DROP TABLE IF EXISTS DimSensor;

CREATE TABLE DimSensor
(
    SensorKey UInt32 DEFAULT CAST(rand64(), 'UInt32'),
    SensorCode String
)
ENGINE = MergeTree
ORDER BY SensorKey;

DROP TABLE IF EXISTS DimLP;

CREATE TABLE DimLP
(
    LPKey UInt32 DEFAULT CAST(rand64(), 'UInt32'),
    LicensePlate String
)
ENGINE = MergeTree
ORDER BY LPKey;

DROP TABLE IF EXISTS DimDetectionType;

CREATE TABLE DimDetectionType
(
    DetectionTypeKey UInt32 DEFAULT CAST(rand64(), 'UInt32'),
    DetectionType String
)
ENGINE = MergeTree
ORDER BY DetectionTypeKey;

DROP TABLE IF EXISTS DimVehicleClass;

CREATE TABLE DimVehicleClass
(
    VehicleClassKey UInt32 DEFAULT CAST(rand64(), 'UInt32'),
    VehicleClass String
)
ENGINE = MergeTree
ORDER BY VehicleClassKey;

DROP TABLE IF EXISTS DimCountry;

CREATE TABLE DimCountry
(
    CountryKey UInt32 DEFAULT CAST(rand64(), 'UInt32'),
    CountryCode String
)
ENGINE = MergeTree
ORDER BY CountryKey;

DROP TABLE IF EXISTS FactCameraDetection;

DROP TABLE IF EXISTS DimTime;

CREATE TABLE DimTime
(
    TimeKey UInt32,
    FullDate DateTime,
    YearNum UInt16,
    MonthNum UInt8,
    DayNum UInt8,
    DayOfWeekNum UInt8,
    HourNum UInt8,
    MinuteNum UInt8
)
ENGINE = MergeTree
ORDER BY TimeKey;


CREATE TABLE FactCameraDetection
(
    TimeKey UInt32,              
    SensorKey UInt32,
    DetectionTypeKey UInt32,
    LPKey UInt32,
    CountryKey UInt32,
    VehicleClassKey UInt32,
    CityKey UInt32,
    Velocity Float32
)
ENGINE = MergeTree
ORDER BY (TimeKey, SensorKey);
