DELETE [DWH].[dbo].[FactCameraDetection]
DELETE [DWH].[dbo].[ETL_IncrementalControl] WHERE ProcessStep = 1
DELETE [DWH].[dbo].[DimVehicleClass]
DELETE [DWH].[dbo].[DimCountry]
DELETE [DWH].[dbo].[DimDetectionType]
DELETE [DWH].[dbo].[DimLP]
DELETE [DWH].[dbo].[DimSensor]
DELETE [DWH].[dbo].[DimCity]



DBCC CHECKIDENT ('[DWH].[dbo].[DimVehicleClass]', RESEED, 0);
DBCC CHECKIDENT ('[DWH].[dbo].[DimCountry]', RESEED, 0);
DBCC CHECKIDENT ('[DWH].[dbo].[DimDetectionType]', RESEED, 0);
DBCC CHECKIDENT ('[DWH].[dbo].[DimLP]', RESEED, 0);
DBCC CHECKIDENT ('[DWH].[dbo].[DimSensor]', RESEED, 0);
DBCC CHECKIDENT ('[DWH].[dbo].[DimCity]', RESEED, 0);
DBCC CHECKIDENT ('[DWH].[dbo].[FactCameraDetection]', RESEED, 0);

-- DimSensor (pokud SensorCode je IDENTITY)
IF NOT EXISTS (SELECT 1 FROM dbo.DimSensor WHERE SensorCode = 'UNKNOWN')
BEGIN
    SET IDENTITY_INSERT dbo.DimSensor ON;

    INSERT INTO dbo.DimSensor (SensorKey, SensorCode)
    VALUES (-1, 'UNKNOWN');

    SET IDENTITY_INSERT dbo.DimSensor OFF;
END

-- DimLP
IF NOT EXISTS (SELECT 1 FROM dbo.DimLP WHERE LicensePlate = 'UNKNOWN')
BEGIN
    SET IDENTITY_INSERT dbo.DimLP ON;

    INSERT INTO dbo.DimLP (LPKey, LicensePlate)
    VALUES (-1, 'UNKNOWN');

    SET IDENTITY_INSERT dbo.DimLP OFF;
END

-- DimDetectionType
IF NOT EXISTS (SELECT 1 FROM dbo.DimDetectionType WHERE DetectionType = 'UNKNOWN')
BEGIN
    SET IDENTITY_INSERT dbo.DimDetectionType ON;

    INSERT INTO dbo.DimDetectionType (DetectionTypeKey, DetectionType)
    VALUES (-1, 'UNKNOWN');

    SET IDENTITY_INSERT dbo.DimDetectionType OFF;
END

-- DimVehicleClass
IF NOT EXISTS (SELECT 1 FROM dbo.DimVehicleClass WHERE VehicleClass = '-999')
BEGIN
    SET IDENTITY_INSERT dbo.DimVehicleClass ON;

    INSERT INTO dbo.DimVehicleClass (VehicleClassKey, VehicleClass)
    VALUES (-1, '-999');

    SET IDENTITY_INSERT dbo.DimVehicleClass OFF;
END

-- DimCountry
IF NOT EXISTS (SELECT 1 FROM dbo.DimCountry WHERE CountryCode = 'UNK')
BEGIN
    SET IDENTITY_INSERT dbo.DimCountry ON;

    INSERT INTO dbo.DimCountry (CountryKey, CountryCode)
    VALUES (-1, 'UNK');

    SET IDENTITY_INSERT dbo.DimCountry OFF;
END

-- DimCity 
IF NOT EXISTS (SELECT 1 FROM dbo.DimCity WHERE CityName = 'UNKNOWN')
BEGIN
    SET IDENTITY_INSERT dbo.DimCity ON;

    INSERT INTO dbo.DimCity (CityKey, CityName)
    VALUES (-1, 'UNKNOWN');

    SET IDENTITY_INSERT dbo.DimCity OFF;
END

-- DimTime - vložení UNKNOWN øádku s TimeKey = -1
IF NOT EXISTS (SELECT 1 FROM dbo.DimTime WHERE TimeKey = -1)
BEGIN
    SET IDENTITY_INSERT dbo.DimTime ON;

    INSERT INTO dbo.DimTime (
        TimeKey, FullDate, YearNum, MonthNum,
        DayNum, DayOfWeekNum, HourNum, MinuteNum
    )
    VALUES (
        -1, '1900-01-01 00:00:00.000', 1900, 1,
        1, 1, 0, 0
    );

    SET IDENTITY_INSERT dbo.DimTime OFF;
END;