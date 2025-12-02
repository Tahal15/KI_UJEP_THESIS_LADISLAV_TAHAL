CREATE TABLE DimCountry (
    CountryKey INT AUTO_INCREMENT PRIMARY KEY,
    CountryCode VARCHAR(10) NOT NULL,
    UNIQUE KEY UQ_DimCountry_Code (CountryCode),
    INDEX IX_DimCountry_Code (CountryCode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
