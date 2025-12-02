CREATE TABLE DimCity (
    CityKey INT AUTO_INCREMENT PRIMARY KEY,
    CityName VARCHAR(100) NOT NULL,
    IsActive BOOLEAN DEFAULT TRUE,
    UNIQUE KEY UQ_DimCity_CityName (CityName),
    INDEX IX_DimCity_Name (CityName)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
