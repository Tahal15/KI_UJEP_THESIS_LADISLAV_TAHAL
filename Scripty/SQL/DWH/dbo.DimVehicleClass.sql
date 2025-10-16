CREATE TABLE dbo.DimVehicleClass (
    VehicleClassKey INT IDENTITY(1,1) PRIMARY KEY,
    VehicleClass INT UNIQUE NOT NULL
);
