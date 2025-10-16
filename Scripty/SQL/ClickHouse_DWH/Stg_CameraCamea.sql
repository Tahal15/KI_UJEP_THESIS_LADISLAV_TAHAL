CREATE TABLE IF NOT EXISTS Stg_CameraCamea
(
    LandingID     UInt64,
    OriginalTime  DateTime,
    City          String,
    DetectionType String,
    Utc           Nullable(DateTime),
    LP            String,
    Sensor        String,
    VehClass      Nullable(Int32),
    ILPC          String,
    Velocity      Nullable(Int32),
    LoadDttm      DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (LandingID);