CREATE TABLE DimLP (
    LPKey INT AUTO_INCREMENT PRIMARY KEY,
    LicensePlate VARCHAR(20) NOT NULL,
    UNIQUE KEY UQ_DimLP_LicensePlate (LicensePlate),
    INDEX IX_DimLP_LicensePlate (LicensePlate)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
