CREATE TABLE IF NOT EXISTS ETL_IncrementalControl
(
    Topic         String,
    LastLoadedID  UInt64,
    LastUpdate    DateTime,
    FullLoadDone  UInt8
)
ENGINE = ReplacingMergeTree
ORDER BY (Topic);