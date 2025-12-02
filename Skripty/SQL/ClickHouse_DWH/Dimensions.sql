CREATE TABLE IF NOT EXISTS DimCity (
    CityKey UInt32,
    CityName String
)
ENGINE = ReplacingMergeTree()
ORDER BY CityKey;

CREATE TABLE IF NOT EXISTS DimSensor (
    SensorKey UInt32,
    SensorCode String
)
ENGINE = ReplacingMergeTree()
ORDER BY SensorKey;

CREATE TABLE IF NOT EXISTS DimLP (
    LPKey UInt32,
    LicensePlate String
)
ENGINE = ReplacingMergeTree()
ORDER BY LPKey;

CREATE TABLE IF NOT EXISTS DimDetectionType (
    DetectionTypeKey UInt32,
    DetectionType String
)
ENGINE = ReplacingMergeTree()
ORDER BY DetectionTypeKey;

CREATE TABLE IF NOT EXISTS DimVehicleClass (
    VehicleClassKey UInt32,
    VehicleClass String
)
ENGINE = ReplacingMergeTree()
ORDER BY VehicleClassKey;

CREATE TABLE IF NOT EXISTS DimCountry (
    CountryKey UInt32,
    CountryCode String
)
ENGINE = ReplacingMergeTree()
ORDER BY CountryKey;

CREATE TABLE IF NOT EXISTS DimTime (
    TimeKey UInt32,
    FullDate DateTime,
    Year UInt16,
    Month UInt8,
    Day UInt8,
    Hour UInt8,
    Minute UInt8
)
ENGINE = ReplacingMergeTree()
ORDER BY TimeKey;