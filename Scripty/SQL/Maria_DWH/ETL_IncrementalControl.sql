CREATE TABLE ETL_IncrementalControl (
    ControlID INT AUTO_INCREMENT PRIMARY KEY,
    Topic VARCHAR(400) NOT NULL UNIQUE,
    LastLoadedID BIGINT,
    FullLoadDone BOOLEAN,
    LastUpdate DATETIME(6),
    ProcessStep TINYINT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
