CREATE TABLE dbo.DimDetectionType (
    DetectionTypeKey INT IDENTITY(1,1) PRIMARY KEY,
    DetectionType NVARCHAR(50) UNIQUE NOT NULL
);
