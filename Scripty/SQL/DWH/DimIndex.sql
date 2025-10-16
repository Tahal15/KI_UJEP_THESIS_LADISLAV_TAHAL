-- DimSensor
CREATE UNIQUE NONCLUSTERED INDEX IX_DimSensor_SensorCode
ON dbo.DimSensor (SensorCode);

-- DimLP
CREATE UNIQUE NONCLUSTERED INDEX IX_DimLP_LicensePlate
ON dbo.DimLP (LicensePlate);

-- DimDetectionType
CREATE UNIQUE NONCLUSTERED INDEX IX_DimDetectionType_Type
ON dbo.DimDetectionType (DetectionType);

-- DimVehicleClass
CREATE UNIQUE NONCLUSTERED INDEX IX_DimVehicleClass_Class
ON dbo.DimVehicleClass (VehicleClass);

-- DimCountry
CREATE UNIQUE NONCLUSTERED INDEX IX_DimCountry_Code
ON dbo.DimCountry (CountryCode);

-- DimCity
CREATE UNIQUE NONCLUSTERED INDEX IX_DimCity_Name
ON dbo.DimCity (CityName);