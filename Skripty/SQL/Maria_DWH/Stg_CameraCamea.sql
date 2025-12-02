CREATE TABLE Stg_CameraCamea (
    StgID INT AUTO_INCREMENT PRIMARY KEY,
    LandingID INT,
    LoadDttm DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    OriginalTime DATETIME(6),
    City VARCHAR(50),
    DetectionType VARCHAR(50),
    Utc DATETIME(6),
    LP VARCHAR(50),
    Sensor VARCHAR(50),
    VehClass INT,
    ILPC VARCHAR(50),
    Velocity INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
