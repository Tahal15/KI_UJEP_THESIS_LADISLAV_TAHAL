CREATE TABLE DimDetectionType (
    DetectionTypeKey INT AUTO_INCREMENT PRIMARY KEY,
    DetectionType VARCHAR(50) NOT NULL,
    UNIQUE KEY UQ_DimDetectionType_Type (DetectionType),
    INDEX IX_DimDetectionType_Type (DetectionType)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
