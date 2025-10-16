
CREATE TABLE IF NOT EXISTS FactCameraDetection (
    TimeKey UInt32,
    SensorKey UInt32,
    DetectionTypeKey UInt32,
    LPKey UInt32,
    CountryKey UInt32,
    VehicleClassKey UInt32,
    CityKey UInt32,
    Velocity Float32
)
ENGINE = MergeTree()
ORDER BY (TimeKey, SensorKey);