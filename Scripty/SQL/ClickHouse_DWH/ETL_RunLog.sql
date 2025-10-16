CREATE TABLE IF NOT EXISTS ETL_RunLog
(
    RunID        UInt64,
    JobName      String,
    Topic        String,
    Status       String,
    StartTime    DateTime,
    EndTime      Nullable(DateTime),
    RowsInserted UInt64,
    ErrorMessage String
)
ENGINE = MergeTree
ORDER BY (RunID);