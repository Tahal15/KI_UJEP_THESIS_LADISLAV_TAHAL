CREATE TABLE DimVehicleClass (
    VehicleClassKey INT AUTO_INCREMENT PRIMARY KEY,
    VehicleClass INT NOT NULL,
    UNIQUE KEY UQ_DimVehicleClass_Class (VehicleClass),
    INDEX IX_DimVehicleClass_Class (VehicleClass)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
