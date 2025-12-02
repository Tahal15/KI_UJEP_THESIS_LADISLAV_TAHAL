CREATE TABLE ETL_RunLog (
    RunID INT AUTO_INCREMENT PRIMARY KEY,
    JobName VARCHAR(200),
    Topic VARCHAR(400),
    Status VARCHAR(40),
    StartTime DATETIME(6),
    EndTime DATETIME(6),
    RowsInserted BIGINT,
    RowsUpdated BIGINT,
    ErrorMessage TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
