CREATE TABLE DimSensor (
    SensorKey INT AUTO_INCREMENT PRIMARY KEY,
    SensorCode VARCHAR(50) NOT NULL,
    UNIQUE KEY UQ_DimSensor_SensorCode (SensorCode),
    INDEX IX_DimSensor_SensorCode (SensorCode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
