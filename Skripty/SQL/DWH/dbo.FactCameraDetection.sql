CREATE TABLE dbo.FactCameraDetection (
    CameraDetectionKey INT IDENTITY(1,1) PRIMARY KEY,
    TimeKey INT NOT NULL,
    CameraKey INT NOT NULL,
    SensorKey INT NOT NULL,
    DetectionTypeKey INT NOT NULL,
    LPKey INT NOT NULL,
    CountryKey INT NOT NULL,
    VehicleClassKey INT NOT NULL,
    CityKey INT NOT NULL,
    Velocity FLOAT NOT NULL,
    FOREIGN KEY (TimeKey) REFERENCES dbo.DimTime(TimeKey),
    FOREIGN KEY (SensorKey) REFERENCES dbo.DimSensor(SensorKey),
    FOREIGN KEY (DetectionTypeKey) REFERENCES dbo.DimDetectionType(DetectionTypeKey),
    FOREIGN KEY (LPKey) REFERENCES dbo.DimLP(LPKey),
    FOREIGN KEY (CountryKey) REFERENCES dbo.DimCountry(CountryKey),
    FOREIGN KEY (VehicleClassKey) REFERENCES dbo.DimVehicleClass(VehicleClassKey),
    FOREIGN KEY (CityKey) REFERENCES dbo.DimCity(CityKey)
);


