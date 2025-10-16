CREATE TABLE FactCameraDetection (
    CameraDetectionKey INT AUTO_INCREMENT PRIMARY KEY,
    TimeKey INT NOT NULL,
    SensorKey INT NOT NULL,
    DetectionTypeKey INT NOT NULL,
    LPKey INT NOT NULL,
    CountryKey INT NOT NULL,
    VehicleClassKey INT NOT NULL,
    CityKey INT NOT NULL,
    Velocity FLOAT NOT NULL,
    FOREIGN KEY (TimeKey) REFERENCES DimTime(TimeKey),
    FOREIGN KEY (SensorKey) REFERENCES DimSensor(SensorKey),
    FOREIGN KEY (DetectionTypeKey) REFERENCES DimDetectionType(DetectionTypeKey),
    FOREIGN KEY (LPKey) REFERENCES DimLP(LPKey),
    FOREIGN KEY (CountryKey) REFERENCES DimCountry(CountryKey),
    FOREIGN KEY (VehicleClassKey) REFERENCES DimVehicleClass(VehicleClassKey),
    FOREIGN KEY (CityKey) REFERENCES DimCity(CityKey)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
